# frontend/tables.py
import django_tables2 as tables
from .models import HistoryEvent

# Assuming your daisyui.html template adds the main table classes
# Remove conflicting Bootstrap-like classes from attrs if daisyui.html handles it
class HistoryEventTable(tables.Table):
    # Explicitly define columns for better control if needed, or rely on fields
    title = tables.Column(linkify=lambda record: record.url, attrs={"a": {"target": "_blank"}}) # Link title to URL
    url = tables.Column(verbose_name="URL", visible=False) # Keep URL data but hide column if title is linked
    visit_count = tables.Column() # No special order_by needed here for default toggling
    category = tables.Column() # No special order_by needed here for default toggling
    last_visit = tables.DateTimeColumn(format='Y-m-d H:i') # Format datetime

    # Add a delete button column
    delete = tables.TemplateColumn(
        template_name='components/history_table/delete_column_template.html',
        verbose_name="", # No header text needed
        orderable=False, # This column shouldn't be sortable
        attrs={'td': {'class': 'text-center w-px'}} # Center button, minimal width
    )

    class Meta:
        model = HistoryEvent
        template_name = "django_tables2/daisyui.html" # Use your DaisyUI template
        # Define the fields AND the order, including the new 'delete' column
        fields = ("title", "visit_count", "category", "browser", "last_visit", "delete", "url")
        # sequence determines column order if fields doesn't include all needed
        sequence = ("title", "visit_count", "category", "browser", "last_visit", "delete")
        # Use attrs primarily for table-level classes if not handled by template_name
        attrs = {
            'class': 'table w-full', # DaisyUI base table class + full width
            'id': 'history-table' # Add ID for potential JS targeting
            # Remove the old Bootstrap-like attrs like thead class etc.
        }
        row_attrs = {
            # Add hover effect from DaisyUI
            "class": lambda record: "hover"
        }