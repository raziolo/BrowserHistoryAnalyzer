from datetime import timedelta, datetime

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from HistoryApp import app_settings
from frontend.analytics import calculate_dashboard_analytics
from frontend.models import HistoryEvent
from frontend.utils.dashboard import make_backup_card, dashboard_context, make_lm_studio_ping


# Create your views here.
def home(request):
    """Renders the home page."""

    context = {
        "backup_card_data": make_backup_card(),
        "backup_dir": app_settings.BACKUP_DIR,
        'dashboard_data': dashboard_context(),
        'generation_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'lm_studio': make_lm_studio_ping(),
    }

    return render(request, 'frontend/home.html', context)


def detailed_dashboard_view(request: HttpRequest) -> HttpResponse:
    """
    View for the detailed analytics dashboard.
    Handles filtering based on query parameters.
    """
    today = datetime.now().date()
    start_date_str = request.GET.get('start_date', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', today.strftime('%Y-%m-%d'))

    try:
        # Add time component for filtering (inclusive of end date)
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').strftime('%Y-%m-%d')

        # Filter the base queryset
        # IMPORTANT: Assumes 'last_visit' is stored as text like 'YYYY-MM-DD HH:MM:SS...'
        # If it's a proper DateTimeField, use __range directly on the field.
        # If format varies, filtering might need adjustment or pre-processing.
        base_queryset = HistoryEvent.objects.filter(
            last_visit__gte=start_date,
            last_visit__lte=end_date
        )
    except ValueError:
        # Handle invalid date format input, fallback to default
        start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d 00:00:00')
        end_date = today.strftime('%Y-%m-%d 23:59:59')
        base_queryset = HistoryEvent.objects.filter(
            last_visit__gte=start_date,
            last_visit__lte=end_date
        )
        # Optionally add a message to the user about the date format error

    # Calculate analytics using the filtered data
    analytics_results = calculate_dashboard_analytics(base_queryset)
    day_of_week_data = sorted(analytics_results['activity_by_day_of_week'],
                              key=lambda x: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].index(x['day']))

    # Prepare data directly as a Python dictionary for json_script
    chart_data_dict = {
        'category_labels': list(analytics_results['category_distribution'].keys()),
        'category_values': list(analytics_results['category_distribution'].values()),
        'browser_labels': list(analytics_results['browser_distribution'].keys()),
        'browser_values': list(analytics_results['browser_distribution'].values()),
        'visit_trend_labels': [item['date'] for item in analytics_results['visit_trend']],
        'visit_trend_values': [item['count'] for item in analytics_results['visit_trend']],
        'activity_hour_labels': [f"{item['hour']:02d}:00" for item in
                                 sorted(analytics_results['activity_by_hour'], key=lambda x: x['hour'])],
        'activity_hour_values': [item['count'] for item in
                                 sorted(analytics_results['activity_by_hour'], key=lambda x: x['hour'])],
        # NEW chart data
        'day_of_week_labels': [item['day'] for item in day_of_week_data],
        'day_of_week_values': [item['count'] for item in day_of_week_data],
    }

    context = {
        'analytics': analytics_results,
        'start_date': start_date_str,
        'end_date': end_date_str,
        # Pass the dictionary directly
        'chart_data_dict': chart_data_dict,  # Use a different name or the same, just ensure it's the dict
        'title': 'Detailed Dashboard'
    }

    if request.headers.get('HX-Request') == 'true':
        return render(request, 'components/dashboard/detailed_dashboard_content.html', context)
    else:
        return render(request, 'frontend/detailed_dashboard.html', context)
