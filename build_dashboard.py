import json

with open('qa_data.json', 'r', encoding='utf-8') as f:
    qa = json.load(f)

categorized = []
for i, (q, a) in enumerate(qa, 1):
    ql = (q + ' ' + a).lower()
    cat = 'Architecture & Fundamentals'
    if 'lock' in ql or 'redis' in ql or 'lua' in ql or 'ttl' in ql:
        cat = 'Redis & Distributed Locking'
    elif 'idempotenc' in ql or 'tamper' in ql or 'sha-256' in ql or 'hash' in ql:
        cat = 'Idempotency & Deduplication'
    elif 'celery' in ql or 'worker' in ql or 'retry' in ql or 'jitter' in ql or 'prefetch' in ql or 'ack' in ql or 'dlq' in ql:
        cat = 'Celery Workers & Failure Semantics'
    elif 'postgres' in ql or 'index' in ql or 'transaction' in ql or 'outbox' in ql or 'model' in ql or 'fsm' in ql or 'uuid' in ql:
        cat = 'PostgreSQL & Database Design'
    elif 'jwt' in ql or 'token' in ql or 'auth' in ql or 'permission' in ql or 'rate limit' in ql or 'throttle' in ql:
        cat = 'Auth, Security & Rate Limiting'
    elif 'prometheus' in ql or 'grafana' in ql or 'metric' in ql or 'health' in ql or 'latency' in ql or 'correlation' in ql:
        cat = 'Observability & Monitoring'
    elif 'docker' in ql or 'aws' in ql or 'fargate' in ql or 'ecs' in ql or 'deploy' in ql:
        cat = 'Docker & Cloud Deployment'
    elif 'test' in ql or 'locust' in ql or 'pytest' in ql:
        cat = 'Testing & Load Simulation'
        
    categorized.append({
        'id': i,
        'category': cat,
        'question': q,
        'answer': a
    })

data_json = json.dumps(categorized)

html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Distributed Job Queue — Architecture & Master Interview Dashboard</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <!-- Mermaid.js for Architecture Diagrams -->
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({
            startOnLoad: true,
            theme: 'dark',
            themeVariables: {
                darkMode: true,
                background: '#090d16',
                primaryColor: '#0ea5e9',
                primaryTextColor: '#f8fafc',
                primaryBorderColor: '#38bdf8',
                lineColor: '#38bdf8',
                secondaryColor: '#1e293b',
                tertiaryColor: '#0f172a'
            }
        });
    </script>
    <style>
        body { font-family: 'Plus Jakarta Sans', sans-serif; }
        code, pre { font-family: 'JetBrains Mono', monospace; }
        .perspective-1000 { perspective: 1000px; }
        .transform-style-3d { transform-style: preserve-3d; }
        .backface-hidden { backface-visibility: hidden; }
        .rotate-y-180 { transform: rotateY(180deg); }
        .card-flip { transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1); }
        .flipped { transform: rotateY(180deg); }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 9999px; }
        ::-webkit-scrollbar-thumb:hover { background: #475569; }
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col">

    <!-- Top Sticky Header -->
    <header class="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50 px-6 py-4">
        <div class="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 text-white font-bold text-xl">
                    ⚡
                </div>
                <div>
                    <h1 class="text-lg font-bold text-white tracking-tight flex items-center gap-2">
                        Distributed Job Queue <span class="text-xs px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-semibold">Master Platform</span>
                    </h1>
                    <p class="text-xs text-slate-400">System Architecture, Deep-Dive Explanation & Anki Viva Simulator</p>
                </div>
            </div>

            <!-- Global Action Bar -->
            <div class="flex items-center gap-2 flex-wrap">
                <a href="anki_deck_distributed_job_queue.csv" download class="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 transition shadow-sm">
                    <span>📥 Download Anki Deck (.csv)</span>
                </a>
                <a href="Distributed_Job_Queue_Viva_and_Project_Guide.pdf" download class="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 transition shadow-sm">
                    <span>📄 Download Master PDF</span>
                </a>
                <button onclick="resetProgress()" class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition">
                    🔄 Reset Stats
                </button>
            </div>
        </div>
    </header>

    <!-- Main Workspace Container -->
    <main class="max-w-7xl mx-auto px-6 py-6 flex-1 w-full flex flex-col gap-6">

        <!-- Top Navigation Mode Switcher -->
        <div class="flex items-center justify-between border-b border-slate-800 pb-3 flex-wrap gap-4">
            <div class="flex items-center gap-2 bg-slate-900 p-1 rounded-xl border border-slate-800">
                <button id="tab-arch" onclick="switchMode('arch')" class="px-4 py-2 text-xs font-bold rounded-lg transition bg-cyan-500 text-slate-950 shadow">
                    📐 Architecture & Pipeline
                </button>
                <button id="tab-explain" onclick="switchMode('explain')" class="px-4 py-2 text-xs font-bold rounded-lg transition text-slate-400 hover:text-white">
                    📖 Deep Project Explanation
                </button>
                <button id="tab-flashcard" onclick="switchMode('flashcard')" class="px-4 py-2 text-xs font-bold rounded-lg transition text-slate-400 hover:text-white">
                    🎴 Anki Flashcard Simulator
                </button>
                <button id="tab-table" onclick="switchMode('table')" class="px-4 py-2 text-xs font-bold rounded-lg transition text-slate-400 hover:text-white">
                    📑 200 Questions Bank
                </button>
            </div>

            <!-- Stats Badge -->
            <div class="flex items-center gap-3 text-xs font-mono">
                <span class="text-slate-400">Readiness Score:</span>
                <span id="nav-mastery-score" class="text-emerald-400 font-bold text-sm bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">0% Mastered</span>
            </div>
        </div>

        <!-- ======================================================== -->
        <!-- SECTION 1: ARCHITECTURE & PIPELINE DIAGRAMS              -->
        <!-- ======================================================== -->
        <section id="section-arch" class="flex flex-col gap-8">
            
            <!-- Hero Architecture Card -->
            <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col gap-4">
                <div class="flex items-center justify-between border-b border-slate-800 pb-4">
                    <div>
                        <h2 class="text-lg font-bold text-white flex items-center gap-2">
                            <span>📐</span> End-to-End Distributed Architecture
                        </h2>
                        <p class="text-xs text-slate-400">Complete asynchronous task lifecycle from HTTP request to worker completion and monitoring.</p>
                    </div>
                    <span class="text-xs px-2.5 py-1 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono">Interactive Topology</span>
                </div>

                <!-- Mermaid Diagram Container -->
                <div class="bg-slate-950 border border-slate-800 rounded-xl p-4 overflow-x-auto flex justify-center">
                    <pre class="mermaid">
flowchart TD
    Client(["HTTP Client / Frontend / Webhook"])
    
    subgraph API_Layer ["1. API & Security Layer (Django REST Framework)"]
        API["Django API Gateway"]
        JWT["JWT Authenticator & Token Blacklist"]
        Throttle["Redis Rate Limiter (100 req/min, 10 jobs/min)"]
        Idem["Idempotency Guard (SHA-256 + Unique DB Constraint)"]
        Outbox["Transactional Outbox Writer"]
    end

    subgraph Storage_Layer ["2. Persistent & Coordination Layer"]
        PG[("PostgreSQL 15 Database\n- Jobs (Macro State)\n- JobExecutions (Audit Attempts)\n- JobResults (Outputs)\n- OutboxMessages (Guaranteed Delivery)")]
        RedisBroker[("Redis 7.0 In-Memory Engine\n- Priority Message Queues\n- Distributed Locks (SETNX + Lua)\n- Throttling Sliding-Window Buckets")]
    end

    subgraph Worker_Pool ["3. Celery Distributed Worker Cluster"]
        WH["High-Priority Worker Node(s)"]
        WD["Default & Low-Priority Worker Node(s)"]
        Reaper["Stalled Job Reaper (Celery Beat Sweeper)"]
    end

    subgraph Observability ["4. Telemetry & Metrics"]
        Prom["Prometheus Engine (5s Scrape Interval)"]
        Grafana["Grafana Dashboards (Throughput, p95 Latency)"]
    end

    Client -->|"POST /api/jobs/ (with Idempotency-Key)"| API
    API --> JWT
    JWT --> Throttle
    Throttle --> Idem
    Idem -->|"ACID Insert Job + Outbox"| PG
    API -->|"Direct Dispatch (on_commit)"| RedisBroker
    API -->|"HTTP 202 Accepted {job_id}"| Client

    RedisBroker -->|"BRPOP high_priority"| WH
    RedisBroker -->|"BRPOP default_priority"| WD
    Reaper -.->|"Auto-recover stuck PROCESSING jobs"| RedisBroker

    WH -->|"Atomic Lock (SETNX lock:job:uuid)"| RedisBroker
    WH -->|"Transition state to PROCESSING"| PG
    WH -->|"Execute Handler (GenerateReport, SendEmail)"| WH
    WH -->|"Update state to COMPLETED / FAILED"| PG
    WH -->|"Safe Release Lock (Lua Script)"| RedisBroker

    API -.->|"Scrape /metrics"| Prom
    Prom --> Grafana
                    </pre>
                </div>
            </div>

            <!-- Pipeline Breakdown Cards -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <!-- Step 1 -->
                <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
                    <div>
                        <div class="text-xs font-mono text-cyan-400 font-bold mb-1">STAGE 01</div>
                        <h3 class="text-sm font-bold text-white mb-2">Ingestion & Idempotency</h3>
                        <p class="text-xs text-slate-400 leading-relaxed">
                            Client issues <code>POST /api/jobs/</code>. The API checks JWT validity, evaluates sliding-window rate limits (10 submissions/min), hashes the request payload with <b>SHA-256</b>, and checks PostgreSQL for cached responses. Duplicate requests return cached responses instantly without creating duplicate background tasks.
                        </p>
                    </div>
                    <div class="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-500 font-mono">
                        Guarantees: Zero duplicate execution
                    </div>
                </div>

                <!-- Step 2 -->
                <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
                    <div>
                        <div class="text-xs font-mono text-cyan-400 font-bold mb-1">STAGE 02</div>
                        <h3 class="text-sm font-bold text-white mb-2">Dual-Write Safety & Outbox</h3>
                        <p class="text-xs text-slate-400 leading-relaxed">
                            Inside an ACID transaction, the <code>Job</code> and an <code>OutboxMessage</code> are saved simultaneously. Django's <code>transaction.on_commit()</code> hook dispatches the job to Redis <i>only after</i> PostgreSQL commits to disk, eliminating the post-commit race condition where workers query uncommitted rows.
                        </p>
                    </div>
                    <div class="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-500 font-mono">
                        Pattern: Transactional Outbox + on_commit
                    </div>
                </div>

                <!-- Step 3 -->
                <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
                    <div>
                        <div class="text-xs font-mono text-cyan-400 font-bold mb-1">STAGE 03</div>
                        <h3 class="text-sm font-bold text-white mb-2">Worker Lock & Execution</h3>
                        <p class="text-xs text-slate-400 leading-relaxed">
                            Celery workers perform priority blocking pops (<code>BRPOP</code>). Before execution, workers acquire a Redis distributed lock (<code>SETNX</code> with TTL). Handlers execute business logic, record immutable audit rows in <code>JobExecution</code>, handle retries with jitter, and release the lock via atomic Lua script.
                        </p>
                    </div>
                    <div class="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-500 font-mono">
                        Safety: Atomic Lua Lock Release
                    </div>
                </div>
            </div>

            <!-- State Machine Diagram Card -->
            <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col gap-4">
                <div class="flex items-center justify-between border-b border-slate-800 pb-4">
                    <div>
                        <h2 class="text-lg font-bold text-white flex items-center gap-2">
                            <span>🔄</span> Finite State Machine (FSM) Lifecycle
                        </h2>
                        <p class="text-xs text-slate-400">Strict state transition validation preventing illegal mutations or corrupt status jumps.</p>
                    </div>
                    <span class="text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">Enforced in Model</span>
                </div>

                <div class="bg-slate-950 border border-slate-800 rounded-xl p-4 overflow-x-auto flex justify-center">
                    <pre class="mermaid">
stateDiagram-v2
    [*] --> QUEUED: Job Created via API
    QUEUED --> PROCESSING: Worker pops & acquires Redis lock
    QUEUED --> CANCELLED: User requests cancellation
    
    PROCESSING --> COMPLETED: Handler returns success
    PROCESSING --> RETRYING: Failure & retry_count < max_retries
    PROCESSING --> FAILED: Retries exhausted
    PROCESSING --> CANCELLED: Cancellation detected mid-execution
    
    RETRYING --> PROCESSING: Exponential backoff delay expires
    RETRYING --> CANCELLED: Cancelled during backoff window
    
    COMPLETED --> [*]: Terminal State
    FAILED --> [*]: Terminal State
    CANCELLED --> [*]: Terminal State
                    </pre>
                </div>
            </div>
        </section>

        <!-- ======================================================== -->
        <!-- SECTION 2: DEEP PROJECT EXPLANATION                      -->
        <!-- ======================================================== -->
        <section id="section-explain" class="hidden flex-col gap-6">
            
            <div class="bg-slate-900 border border-slate-800 rounded-2xl p-8 flex flex-col gap-6 shadow-xl">
                <div class="border-b border-slate-800 pb-4">
                    <span class="text-xs font-mono text-cyan-400 font-bold uppercase tracking-wider">Executive Engineering Summary</span>
                    <h2 class="text-2xl font-bold text-white mt-1">What is this project and what problem does it solve?</h2>
                </div>

                <div class="text-sm text-slate-300 leading-relaxed space-y-4">
                    <p>
                        In conventional synchronous web applications, when an end-user triggers a computationally heavy operation (such as compiling an annual PDF tax report, processing bulk datasets, or dispatching 10,000 marketing emails), the web server thread executes that task directly within the HTTP request-response cycle.
                    </p>
                    <p>
                        This synchronous design introduces severe production vulnerabilities:
                    </p>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 my-2">
                        <div class="p-4 bg-slate-950 border border-slate-800 rounded-xl">
                            <span class="text-rose-400 font-bold text-xs uppercase font-mono">1. HTTP Gateway Timeouts (504)</span>
                            <p class="text-xs text-slate-400 mt-1">AWS Application Load Balancers, NGINX reverse proxies, and browsers terminate connections that exceed 30–60 seconds, dropping the user's connection while the server continues working in vain.</p>
                        </div>
                        <div class="p-4 bg-slate-950 border border-slate-800 rounded-xl">
                            <span class="text-rose-400 font-bold text-xs uppercase font-mono">2. Web Worker Thread Starvation</span>
                            <p class="text-xs text-slate-400 mt-1">Gunicorn or Uvicorn worker threads blocked on long-running tasks cannot accept incoming requests from other users, causing complete application unresponsiveness.</p>
                        </div>
                        <div class="p-4 bg-slate-950 border border-slate-800 rounded-xl">
                            <span class="text-rose-400 font-bold text-xs uppercase font-mono">3. Accidental Duplicate Execution</span>
                            <p class="text-xs text-slate-400 mt-1">When network packets drop, frontend apps or automated webhooks retry the HTTP request, causing non-idempotent operations (such as charging credit cards) to run twice.</p>
                        </div>
                        <div class="p-4 bg-slate-950 border border-slate-800 rounded-xl">
                            <span class="text-rose-400 font-bold text-xs uppercase font-mono">4. Worker Crash Message Loss</span>
                            <p class="text-xs text-slate-400 mt-1">Standard task queues that acknowledge messages before execution immediately lose jobs forever if the worker process suffers an Out-Of-Memory (OOM) kill or power loss.</p>
                        </div>
                    </div>
                    <p>
                        <b>The Solution:</b> This project implements an enterprise-grade <b>Distributed Task Queue & Background Processing Platform</b>. It decouples synchronous ingestion from execution. Incoming requests receive an immediate <code>HTTP 202 Accepted</code> response with a <code>job_id</code> in <b>under 10 milliseconds</b>, delegating background execution to horizontally scalable Celery workers coordinated by Redis and PostgreSQL.
                    </p>
                </div>

                <!-- 5 Core Engineering Pillars -->
                <div class="border-t border-slate-800 pt-6">
                    <h3 class="text-base font-bold text-white mb-4">5 Key Distributed Systems Challenges Solved</h3>
                    
                    <div class="space-y-4 text-xs text-slate-300">
                        <div class="p-4 bg-slate-950 border border-slate-800 rounded-xl">
                            <h4 class="font-bold text-cyan-400 text-sm mb-1">1. The Post-Commit Message Dispatch Race Condition</h4>
                            <p class="text-slate-400 leading-relaxed">
                                <b>The Bug:</b> If an API dispatches a task to Celery inside an uncommitted database transaction, message transmission over Redis takes &lt;1ms. A fast worker pops the task from Redis and queries PostgreSQL (<code>Job.objects.get(id=job_id)</code>) before the web server's transaction has committed, immediately crashing with <code>Job.DoesNotExist</code>.
                            </p>
                            <p class="text-slate-400 mt-1">
                                <b>The Fix:</b> We wrapped Celery publishing inside Django's <code>transaction.on_commit()</code> hook combined with a persistent <code>OutboxMessage</code> table. The task enters Redis strictly after PostgreSQL confirms the commit has hit disk.
                            </p>
                        </div>

                        <div class="p-4 bg-slate-950 border border-slate-800 rounded-xl">
                            <h4 class="font-bold text-cyan-400 text-sm mb-1">2. Mutual Exclusion via Redis Distributed Locking</h4>
                            <p class="text-slate-400 leading-relaxed">
                                <b>The Bug:</b> Network retries or duplicate message deliveries can cause two workers to execute the same job simultaneously. Furthermore, if a worker's lock expires while it is still working, another worker grabs the lock. If the first worker finishes and blindly executes <code>DEL lock:job:uuid</code>, it deletes the second worker's active lock!
                            </p>
                            <p class="text-slate-400 mt-1">
                                <b>The Fix:</b> We acquire locks via <code>SET key token NX PX 120000</code> and release locks via an atomic Lua script verifying that the token in Redis matches the worker's unique UUID token before deletion.
                            </p>
                        </div>

                        <div class="p-4 bg-slate-950 border border-slate-800 rounded-xl">
                            <h4 class="font-bold text-cyan-400 text-sm mb-1">3. Thundering Herd Storms & Exponential Backoff with Jitter</h4>
                            <p class="text-slate-400 leading-relaxed">
                                <b>The Bug:</b> If an external service or database suffers a temporary network glitch, hundreds of failing tasks retrying at identical exponential intervals (e.g. exactly 2s, 4s, 8s) will hit the recovering service at the exact same second, crashing it repeatedly.
                            </p>
                            <p class="text-slate-400 mt-1">
                                <b>The Fix:</b> We calculate retries using Full Random Jitter: <code>delay = random.uniform(0, min(300, 2^retry_count * base_delay))</code>, dispersing retry traffic uniformly across the timeline.
                            </p>
                        </div>

                        <div class="p-4 bg-slate-950 border border-slate-800 rounded-xl">
                            <h4 class="font-bold text-cyan-400 text-sm mb-1">4. Worker Crash Recovery (At-Least-Once Delivery)</h4>
                            <p class="text-slate-400 leading-relaxed">
                                <b>The Bug:</b> Default Celery acknowledges messages when received (<code>acks_late=False</code>). If a container is terminated mid-task, the job disappears without a trace.
                            </p>
                            <p class="text-slate-400 mt-1">
                                <b>The Fix:</b> We configure <code>task_acks_late = True</code> and <code>task_reject_on_worker_lost = True</code>. If a worker process dies, Redis re-queues the message to another healthy worker, and a periodic Celery Beat reaper sweeps jobs stuck in <code>PROCESSING</code>.
                            </p>
                        </div>

                        <div class="p-4 bg-slate-950 border border-slate-800 rounded-xl">
                            <h4 class="font-bold text-cyan-400 text-sm mb-1">5. Multi-Tenant Row-Level Isolation</h4>
                            <p class="text-slate-400 leading-relaxed">
                                <b>The Bug:</b> In multi-tenant platforms, attackers attempt ID enumeration attacks (guessing <code>/api/jobs/1</code>, <code>/api/jobs/2</code>) to view other tenants' sensitive task outputs.
                            </p>
                            <p class="text-slate-400 mt-1">
                                <b>The Fix:</b> We enforce UUIDv4 primary keys and override DRF's <code>get_queryset()</code> with <code>Job.objects.filter(user=request.user)</code>. Guessing another user's UUID returns <code>HTTP 404 Not Found</code> instead of <code>403 Forbidden</code>, hiding resource existence entirely.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- ======================================================== -->
        <!-- SECTION 3: ANKI FLASHCARD SIMULATOR                      -->
        <!-- ======================================================== -->
        <section id="section-flashcard" class="hidden flex-col items-center justify-center py-4 gap-6">
            
            <!-- Filter Bar for Cards -->
            <div class="w-full max-w-3xl flex items-center justify-between text-xs text-slate-400 font-mono flex-wrap gap-3">
                <div>Card <span id="current-index-label" class="text-cyan-400 font-bold text-sm">1</span> of <span id="total-filtered-label" class="text-white font-bold text-sm">200</span></div>
                <div id="current-category-pill" class="px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300 font-sans">Architecture</div>
                <div class="flex items-center gap-2">
                    <span>Keyboard: <b>Space</b> (Flip), <b>1/2/3</b> (Rate)</span>
                </div>
            </div>

            <!-- Flashcard Frame (Perspective Container) -->
            <div class="w-full max-w-3xl h-[400px] perspective-1000 cursor-pointer" onclick="toggleCardFlip()">
                <div id="card-inner" class="card-flip relative w-full h-full transform-style-3d">
                    
                    <!-- FRONT SIDE -->
                    <div class="absolute inset-0 w-full h-full bg-gradient-to-b from-slate-900 to-slate-950 border-2 border-slate-800 hover:border-cyan-500/50 rounded-2xl p-8 flex flex-col justify-between backface-hidden shadow-2xl transition">
                        <div class="flex items-center justify-between">
                            <span id="card-q-number" class="px-3 py-1 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono font-bold text-xs">Question #1</span>
                            <span class="text-xs text-slate-500 flex items-center gap-1.5">
                                <span class="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span> Click or Press Spacebar to Reveal Answer
                            </span>
                        </div>

                        <div class="my-auto">
                            <h2 id="card-question-text" class="text-xl md:text-2xl font-bold text-white tracking-tight leading-snug">
                                Loading question...
                            </h2>
                        </div>

                        <div class="flex items-center justify-between text-xs text-slate-500 border-t border-slate-800/80 pt-4">
                            <span>Topic: <span id="card-topic-text" class="text-slate-300 font-medium">General</span></span>
                            <span>Prompt: Try answering aloud before flipping</span>
                        </div>
                    </div>

                    <!-- BACK SIDE (ANSWER) -->
                    <div class="absolute inset-0 w-full h-full bg-gradient-to-b from-slate-900 to-slate-950 border-2 border-indigo-500/40 rounded-2xl p-8 flex flex-col justify-between backface-hidden rotate-y-180 shadow-2xl overflow-y-auto">
                        <div class="flex items-center justify-between">
                            <span id="card-ans-number" class="px-3 py-1 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-mono font-bold text-xs">Examiner Answer</span>
                            <span class="text-xs text-slate-400">Click or Space to flip back</span>
                        </div>

                        <div class="my-auto py-2">
                            <div id="card-answer-text" class="text-sm md:text-base text-slate-200 leading-relaxed font-normal">
                                Loading answer...
                            </div>
                        </div>

                        <div class="flex items-center justify-between text-xs text-slate-500 border-t border-slate-800/80 pt-4">
                            <span class="text-emerald-400 font-mono">✓ Verified Production Answer</span>
                            <span>Rate your recall below to advance</span>
                        </div>
                    </div>

                </div>
            </div>

            <!-- Anki-Style Confidence Buttons -->
            <div class="flex items-center gap-3 w-full max-w-3xl justify-center flex-wrap">
                <button onclick="prevCard(event)" class="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 text-xs font-bold transition flex items-center gap-1.5">
                    ⬅ Previous
                </button>
                <button onclick="rateCard('again', event)" class="px-5 py-2.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-bold transition flex items-center gap-1.5 shadow-sm">
                    🔴 Hard / Again (Key: 1)
                </button>
                <button onclick="rateCard('good', event)" class="px-5 py-2.5 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 text-xs font-bold transition flex items-center gap-1.5 shadow-sm">
                    🟡 Good / Review (Key: 2)
                </button>
                <button onclick="rateCard('easy', event)" class="px-5 py-2.5 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-bold transition flex items-center gap-1.5 shadow-sm">
                    🟢 Mastered / Easy (Key: 3)
                </button>
                <button onclick="nextCard(event)" class="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 text-xs font-bold transition flex items-center gap-1.5">
                    Next ➡
                </button>
            </div>
        </section>

        <!-- ======================================================== -->
        <!-- SECTION 4: 200 QUESTION TABLE EXPLORER                   -->
        <!-- ======================================================== -->
        <section id="section-table" class="hidden flex-col gap-4">
            
            <div class="flex items-center justify-between gap-4 flex-wrap text-xs">
                <div class="flex items-center gap-3 flex-wrap">
                    <select id="filter-category" onchange="filterCards()" class="bg-slate-900 border border-slate-800 text-slate-200 px-3 py-2 rounded-lg outline-none focus:border-cyan-500">
                        <option value="ALL">All 8 Topics (200 Questions)</option>
                        <option value="Architecture & Fundamentals">Architecture & Fundamentals</option>
                        <option value="PostgreSQL & Database Design">PostgreSQL & Database Design</option>
                        <option value="Redis & Distributed Locking">Redis & Distributed Locking</option>
                        <option value="Celery Workers & Failure Semantics">Celery Workers & Failure Semantics</option>
                        <option value="Idempotency & Deduplication">Idempotency & Deduplication</option>
                        <option value="Auth, Security & Rate Limiting">Auth, Security & Rate Limiting</option>
                        <option value="Observability & Monitoring">Observability & Monitoring</option>
                        <option value="Docker & Cloud Deployment">Docker & Cloud Deployment</option>
                        <option value="Testing & Load Simulation">Testing & Load Simulation</option>
                    </select>

                    <select id="filter-status" onchange="filterCards()" class="bg-slate-900 border border-slate-800 text-slate-200 px-3 py-2 rounded-lg outline-none focus:border-cyan-500">
                        <option value="ALL">All Statuses</option>
                        <option value="FLAGGED">Hard / Flagged Only</option>
                        <option value="UNVIEWED">Unreviewed Only</option>
                        <option value="MASTERED">Mastered Only</option>
                    </select>

                    <input type="text" id="search-input" oninput="filterCards()" placeholder="Search keywords, Q#, Lua, FSM..." class="bg-slate-900 border border-slate-800 text-slate-200 px-3 py-2 rounded-lg outline-none focus:border-cyan-500 w-56">
                </div>
            </div>

            <div class="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow">
                <div class="max-h-[600px] overflow-y-auto">
                    <table class="w-full text-left text-xs text-slate-300">
                        <thead class="bg-slate-950 text-slate-400 sticky top-0 uppercase tracking-wider font-mono border-b border-slate-800 z-10">
                            <tr>
                                <th class="p-3.5 w-16 text-center">Q#</th>
                                <th class="p-3.5 w-44">Category</th>
                                <th class="p-3.5">Interview Question</th>
                                <th class="p-3.5 w-24 text-center">Status</th>
                                <th class="p-3.5 w-20 text-center">Practice</th>
                            </tr>
                        </thead>
                        <tbody id="table-body" class="divide-y divide-slate-800/60 font-sans">
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

    </main>

    <!-- Embedded Engine & State Management -->
    <script>
        const QUESTIONS_DATA = ''' + data_json + ''';

        let state = {
            currentIndex: 0,
            filteredCards: [...QUESTIONS_DATA],
            cardStatuses: JSON.parse(localStorage.getItem('djq_card_statuses') || '{}'),
            currentMode: 'arch',
            isFlipped: false
        };

        function init() {
            updateStats();
            filterCards();
            renderTable();
            setupKeyboardShortcuts();
        }

        function switchMode(mode) {
            state.currentMode = mode;
            document.getElementById('section-arch').classList.toggle('hidden', mode !== 'arch');
            document.getElementById('section-explain').classList.toggle('hidden', mode !== 'explain');
            document.getElementById('section-flashcard').classList.toggle('hidden', mode !== 'flashcard');
            document.getElementById('section-table').classList.toggle('hidden', mode !== 'table');

            // Tab button styles
            const tabs = ['arch', 'explain', 'flashcard', 'table'];
            tabs.forEach(t => {
                const btn = document.getElementById(`tab-${t}`);
                if (btn) {
                    btn.className = (t === mode) 
                        ? 'px-4 py-2 text-xs font-bold rounded-lg transition bg-cyan-500 text-slate-950 shadow' 
                        : 'px-4 py-2 text-xs font-bold rounded-lg transition text-slate-400 hover:text-white';
                }
            });

            if (mode === 'table') renderTable();
        }

        function filterCards() {
            const cat = document.getElementById('filter-category').value;
            const status = document.getElementById('filter-status').value;
            const search = document.getElementById('search-input').value.toLowerCase().trim();

            state.filteredCards = QUESTIONS_DATA.filter(item => {
                if (cat !== 'ALL' && item.category !== cat) return false;
                
                const itemStatus = state.cardStatuses[item.id] || 'UNVIEWED';
                if (status === 'FLAGGED' && itemStatus !== 'FLAGGED') return false;
                if (status === 'MASTERED' && itemStatus !== 'MASTERED') return false;
                if (status === 'UNVIEWED' && itemStatus !== 'UNVIEWED') return false;

                if (search) {
                    const matchQ = item.question.toLowerCase().includes(search);
                    const matchA = item.answer.toLowerCase().includes(search);
                    const matchId = `q${item.id}` === search || `${item.id}` === search;
                    if (!matchQ && !matchA && !matchId) return false;
                }

                return true;
            });

            state.currentIndex = 0;
            updateCardDisplay();
            if (state.currentMode === 'table') renderTable();
        }

        function updateCardDisplay() {
            const inner = document.getElementById('card-inner');
            inner.classList.remove('flipped');
            state.isFlipped = false;

            const total = state.filteredCards.length;
            document.getElementById('total-filtered-label').innerText = total;

            if (total === 0) {
                document.getElementById('current-index-label').innerText = '0';
                document.getElementById('card-q-number').innerText = 'No Cards Found';
                document.getElementById('card-question-text').innerText = 'No questions match your current filter criteria.';
                document.getElementById('card-answer-text').innerText = 'Try changing category or clearing your search term.';
                document.getElementById('current-category-pill').innerText = 'Empty';
                return;
            }

            const card = state.filteredCards[state.currentIndex];
            document.getElementById('current-index-label').innerText = (state.currentIndex + 1);
            document.getElementById('card-q-number').innerText = `Question #${card.id}`;
            document.getElementById('card-ans-number').innerText = `Answer #${card.id}`;
            document.getElementById('card-question-text').innerText = card.question;
            document.getElementById('card-answer-text').innerHTML = card.answer.replace(/\\n/g, '<br>');
            document.getElementById('card-topic-text').innerText = card.category;
            document.getElementById('current-category-pill').innerText = card.category;
        }

        function toggleCardFlip() {
            const inner = document.getElementById('card-inner');
            state.isFlipped = !state.isFlipped;
            inner.classList.toggle('flipped', state.isFlipped);
        }

        function rateCard(rating, e) {
            if (e) e.stopPropagation();
            if (state.filteredCards.length === 0) return;

            const card = state.filteredCards[state.currentIndex];
            if (rating === 'easy') {
                state.cardStatuses[card.id] = 'MASTERED';
            } else if (rating === 'again') {
                state.cardStatuses[card.id] = 'FLAGGED';
            } else {
                state.cardStatuses[card.id] = 'REVIEW';
            }

            saveStatuses();
            nextCard();
        }

        function nextCard(e) {
            if (e) e.stopPropagation();
            if (state.filteredCards.length === 0) return;
            state.currentIndex = (state.currentIndex + 1) % state.filteredCards.length;
            updateCardDisplay();
        }

        function prevCard(e) {
            if (e) e.stopPropagation();
            if (state.filteredCards.length === 0) return;
            state.currentIndex = (state.currentIndex - 1 + state.filteredCards.length) % state.filteredCards.length;
            updateCardDisplay();
        }

        function jumpToCard(id) {
            const idx = state.filteredCards.findIndex(c => c.id === id);
            if (idx !== -1) {
                state.currentIndex = idx;
                switchMode('flashcard');
                updateCardDisplay();
            }
        }

        function renderTable() {
            const tbody = document.getElementById('table-body');
            tbody.innerHTML = '';

            state.filteredCards.forEach(item => {
                const status = state.cardStatuses[item.id] || 'UNVIEWED';
                let badge = '<span class="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400">Unviewed</span>';
                if (status === 'MASTERED') badge = '<span class="px-2 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-bold">Mastered</span>';
                if (status === 'FLAGGED') badge = '<span class="px-2 py-0.5 rounded text-[10px] bg-rose-500/20 text-rose-400 border border-rose-500/30 font-bold">Hard</span>';
                if (status === 'REVIEW') badge = '<span class="px-2 py-0.5 rounded text-[10px] bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 font-bold">Review</span>';

                const tr = document.createElement('tr');
                tr.className = 'hover:bg-slate-800/40 transition';
                tr.innerHTML = `
                    <td class="p-3.5 text-center font-mono font-bold text-slate-400">Q${item.id}</td>
                    <td class="p-3.5 text-slate-300 font-medium"><span class="text-[11px] px-2 py-1 bg-slate-800/80 rounded-md border border-slate-700/60">${item.category}</span></td>
                    <td class="p-3.5 text-slate-200 font-medium">${item.question}</td>
                    <td class="p-3.5 text-center">${badge}</td>
                    <td class="p-3.5 text-center">
                        <button onclick="jumpToCard(${item.id})" class="px-2.5 py-1 text-[11px] rounded bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 font-semibold">
                            Practice
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        function updateStats() {
            let mastered = 0;
            QUESTIONS_DATA.forEach(item => {
                if (state.cardStatuses[item.id] === 'MASTERED') mastered++;
            });
            const masteryPercent = Math.round((mastered / 200) * 100);
            const badge = document.getElementById('nav-mastery-score');
            if (badge) badge.innerText = `${masteryPercent}% Mastered (${mastered}/200)`;
        }

        function saveStatuses() {
            localStorage.setItem('djq_card_statuses', JSON.stringify(state.cardStatuses));
            updateStats();
        }

        function resetProgress() {
            if (confirm('Reset all card mastery stats and revision progress?')) {
                state.cardStatuses = {};
                saveStatuses();
                filterCards();
            }
        }

        function setupKeyboardShortcuts() {
            window.addEventListener('keydown', (e) => {
                if (document.activeElement === document.getElementById('search-input')) return;

                if (state.currentMode === 'flashcard') {
                    if (e.code === 'Space') {
                        e.preventDefault();
                        toggleCardFlip();
                    } else if (e.key === '1') {
                        rateCard('again');
                    } else if (e.key === '2') {
                        rateCard('good');
                    } else if (e.key === '3') {
                        rateCard('easy');
                    } else if (e.code === 'ArrowRight') {
                        nextCard();
                    } else if (e.code === 'ArrowLeft') {
                        prevCard();
                    }
                }
            });
        }

        document.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>
'''

with open('interview_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html_template)

print('Updated interview_dashboard.html with Architecture and Explanations!')
