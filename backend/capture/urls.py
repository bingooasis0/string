from django.urls import path
from . import views

urlpatterns = [
    path('syslog/recent/', views.get_recent_syslog_entries, name='get_recent_syslog_entries'),
    path('netflow/recent/', views.get_recent_netflow_entries, name='get_recent_netflow_entries'),
    path('service/start/', views.start_service, name='start_service'),
    path('service/stop/', views.stop_service, name='stop_service'),
    path('service/stop_all/', views.stop_all_services, name='stop_all_services'),
    path('service/purge_all/', views.purge_all_data, name='purge_all_data'),
    path('graph/volume/', views.get_historical_volume, name='get_historical_volume'),
]
