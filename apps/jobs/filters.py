import django_filters
from .models import Job


class JobFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name="status", lookup_expr="iexact")
    priority = django_filters.CharFilter(field_name="priority", lookup_expr="iexact")
    job_type = django_filters.CharFilter(field_name="job_type", lookup_expr="iexact")
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Job
        fields = ["status", "priority", "job_type", "created_after", "created_before"]
