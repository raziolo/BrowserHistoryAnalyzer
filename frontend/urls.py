
from django.urls import path
from . import views
from .views import HistoryEventListView

urlpatterns = [
    path('', views.home, name='home'),
    path('make_backup', views.make_backup, name='make_backup'),
    path('classification', views.classification, name='classification'),
    path('start_classification', views.start_classification, name='start_classification'),
    path('get_classification_status', views.get_classification_status, name='get_classification_status'),
    path('reset_classification_status', views.reset_classification_status, name='reset_classification_status'),
    path('settings/', views.settings_view, name='settings'),

    path('history/', HistoryEventListView.as_view(), name='history_list'),

]