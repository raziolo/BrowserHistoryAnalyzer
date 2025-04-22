
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('make_backup', views.make_backup, name='make_backup'),
]