# frontend/views/history_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView # Use ListView for more control than SingleTableView
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django_tables2 import SingleTableMixin, RequestConfig # Import RequestConfig explicitly

from frontend.models import HistoryEvent
from frontend.tables import HistoryEventTable
from frontend.filters import HistoryEventFilter # Import the filter

class HistoryEventListView(SingleTableMixin, ListView): # Inherit from both
    model = HistoryEvent
    table_class = HistoryEventTable
    template_name = 'frontend/history_list.html'
    context_object_name = 'history_events' # Default is object_list, be explicit
    paginate_by = 15 # Define pagination directly

    # Define filterset class
    filterset_class = HistoryEventFilter

    def get_queryset(self):
        queryset = super().get_queryset() # This gets HistoryEvent.objects.all() initially

        self.filterset = self.filterset_class(self.request.GET, queryset=queryset)

        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # The filterset is usually already created by get_queryset or earlier dispatch
        # but assigning it here ensures it's present if get_queryset wasn't called yet.
        if not hasattr(self, 'filterset'):
             # If get_queryset wasn't called (e.g., empty results), initialize filterset for the form
             # Need to get the base queryset again in this edge case
             base_queryset = super().get_queryset()
             self.filterset = self.filterset_class(self.request.GET, queryset=base_queryset)

        context['filter'] = self.filterset
        # The table object itself is added by SingleTableMixin automatically
        return context

    def get_template_names(self):
        if self.request.htmx:
            # If it's an HTMX request (filtering, sorting, pagination),
            # return only the partial template containing the table.
            return ['components/history_table/history_table_partial.html']
        # Otherwise, return the full page template.
        return [self.template_name]


@csrf_exempt # CSRF exemption for HTMX requests
@require_http_methods(["DELETE"]) # Ensure only DELETE requests are allowed
def delete_history_event(request, pk):
    # Permission check could be added here if needed
    try:
        event = get_object_or_404(HistoryEvent, pk=pk)
        event_title = event.title # Get title before deleting for message
        event.delete()
        # messages.success(request, f"Deleted entry: {event_title}") # Doesn't work well with HTMX swap
        # For HTMX row removal, just return an empty response or status 200
        return HttpResponse(status=200) # OK status indicates success
    except Exception as e:
        # Log the error
        # logger.error(f"Error deleting history event {pk}: {e}")
        # Return an error response that HTMX can potentially handle
        return HttpResponse(f"Error deleting entry: {e}", status=500)