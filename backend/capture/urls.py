from django.urls import path
from . import views

urlpatterns = [
    # Service control
    path('api/service/start/', views.start_service, name='start_service'),
    path('api/service/stop/', views.stop_service, name='stop_service'),
    path('api/service/stop_all/', views.stop_all_services, name='stop_all_services'),
    path('api/service/purge_all/', views.purge_all_data, name='purge_all_data'),
    path('api/service/status/', views.service_status, name='service_status'),

    # Recent data endpoints
    path('api/syslog/recent/', views.get_recent_syslog_entries, name='recent_syslog'),
    path('api/netflow/recent/', views.get_recent_netflow_entries, name='recent_netflow'),
    path('api/netconsole/recent/', views.get_recent_netconsole_entries, name='recent_netconsole'),
    path('api/snmp/recent/', views.recent_snmp, name='recent_snmp'),

    # Chart data (single route only)
    path('api/graph/volume/', views.graph_volume, name='graph_volume'),
]
