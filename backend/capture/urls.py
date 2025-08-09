from django.urls import path
from . import views

urlpatterns = [
    path('syslog/recent/', views.get_recent_syslog_entries, name='get_recent_syslog_entries'),
    path('netflow/recent/', views.get_recent_netflow_entries, name='get_recent_netflow_entries'),
]
