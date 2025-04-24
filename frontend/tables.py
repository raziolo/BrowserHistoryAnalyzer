# frontend/tables.py
import django_tables2 as tables
from django_tables2 import RequestConfig

from .models import HistoryEvent


class HistoryEventTable(tables.Table):
    url = tables.Column(verbose_name="URL")
    last_visit = tables.DateTimeColumn()

    class Meta:
        model = HistoryEvent
        template_name = "django_tables2/daisyui.html"
        fields = ("title", "visit_count", "category", "browser", "last_visit", "url", )
        attrs = {
            'class': 'table table-striped table-bordered table-hover',
            'thead': {
                'class': 'thead-dark'
            },
        }
