# Production AWS Deployment Architecture

This document describes how to deploy the **Distributed Job Queue & Task Processing System** on AWS using enterprise cloud best practices.

---

## 1. AWS Cloud Architecture Diagram

```mermaid
flowchart TD
    Internet([Internet / Clients])
    
    subgraph VPC ["AWS VPC (Virtual Private Cloud - 10.0.0.0/16)"]
        subgraph PublicSubnets ["Public Subnets (Multi-AZ)"]
            ALB["Application Load Balancer (ALB)\n(SSL Termination / ACM Certificate)"]
            NAT["NAT Gateways (Multi-AZ)"]
        end

        subgraph AppSubnets ["Private Application Subnets (Multi-AZ)"]
            subgraph ECSCluster ["AWS ECS Fargate Cluster"]
                APIService["Django API Service\n(Auto-Scaled: 2 - 10 Tasks)"]
                WorkerService["Celery Worker Service\n(Auto-Scaled on Queue Depth)"]
            end
        end

        subgraph DataSubnets ["Private Isolated Data Subnets (Multi-AZ)"]
            RDS[("AWS RDS PostgreSQL (Multi-AZ)\n- Automated Snapshots\n- Connection Pooling via RDS Proxy")]
            ElastiCache[("AWS ElastiCache for Redis\n- Replication Group (Primary + Replica)\n- Multi-AZ Auto-Failover")]
        end

        subgraph MonitoringPlane ["Observability & Secrets"]
            CloudWatch["Amazon CloudWatch Logs & Alarms"]
            SecretsManager["AWS Secrets Manager\n(Database passwords, JWT secrets)"]
            S3Reports["Amazon S3 Bucket\n(Generated Report Storage)"]
        end
    end

    Internet -->|HTTPS (443)| ALB
    ALB -->|HTTP (8000)| APIService
    APIService -->|SQL Queries| RDS
    APIService -->|Publish Tasks & Locks| ElastiCache
    WorkerService -->|BRPOP Queues & Locks| ElastiCache
    WorkerService -->|Read/Write Jobs & Results| RDS
    WorkerService -->|Upload PDFs/Artifacts| S3Reports
    
    APIService -.->|Fetch Secrets| SecretsManager
    APIService -.->|Logs & Metrics| CloudWatch
    WorkerService -.->|Logs & Metrics| CloudWatch
```

---

## 2. Infrastructure Components

| Component | AWS Service | Sizing & Configuration |
| :--- | :--- | :--- |
| **Compute (API)** | AWS ECS Fargate | `0.5 vCPU, 1 GB RAM` per task (Autoscaling based on CPU > 70% or Request Count) |
| **Compute (Workers)** | AWS ECS Fargate | `1.0 vCPU, 2 GB RAM` per task (Autoscaling based on Redis Queue depth CloudWatch metric) |
| **Database** | AWS RDS PostgreSQL | `db.t4g.medium` Multi-AZ with automated backups and RDS Proxy connection pooling |
| **Message Broker & Cache** | AWS ElastiCache for Redis | `cache.t4g.small` Replication Group (1 Primary + 1 Read Replica in different AZs) |
| **Secrets Management** | AWS Secrets Manager | Secure rotation of `SECRET_KEY`, database passwords, and JWT credentials |
| **Load Balancer** | AWS Application Load Balancer | HTTPS listener with AWS Certificate Manager (ACM) free managed SSL |
| **Storage** | Amazon S3 | Server-side encrypted S3 bucket for task artifacts, PDF reports, and exported data |

---

## 3. Worker Auto-Scaling on Queue Depth

In production, scaling workers solely on CPU utilization is suboptimal because I/O-bound workers (e.g. waiting on external APIs) will not saturate CPU even if millions of tasks are backing up in the queue.

### Custom CloudWatch Metric Auto-Scaling
1. A lightweight Lambda function polls Redis every 30 seconds: `LLEN queue:high_priority + LLEN queue:default_priority + LLEN queue:low_priority`.
2. Emits a custom metric to CloudWatch: `JobQueueDepth`.
3. An ECS Target Tracking Scaling Policy adjusts the number of Celery worker tasks:
   - Target: `20 unprocessed messages per worker`.
   - If queue depth reaches 200, ECS scales up to 10 worker tasks automatically.
