
from django.urls import path
from .views import (
    dashboard,
    classification,
    settings,
    history,
    action
)

urlpatterns = [
    path('', dashboard.home, name='home'),
    path('detailed-dashboard/', dashboard.detailed_dashboard_view, name='detailed_dashboard'),

    path('classification/', classification.classification, name='classification'),
    path('get_classification_status/', classification.get_classification_status,
         name='get_classification_status'),
    path('reset-classification/', classification.reset_classification_status, name='reset_classification_status'),

    path('settings/', settings.settings_view, name='settings'),

    # Ensure HistoryEventListView is imported correctly if using .as_view()
    path('history/', history.HistoryEventListView.as_view(), name='history_list'),
    path('delete-history-event/<int:pk>/', history.delete_history_event, name='delete_history_event'),

    path('flush-db/', action.flush_db, name='flush_db'),  # Example URL for the action

    path('make-backup/', action.make_backup, name='make_backup'),  # Example URL for the action

]