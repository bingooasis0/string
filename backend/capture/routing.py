# C:\Users\colby\Desktop\String\backend\capture\routing.py
from django.urls import re_path
from . import syslog_consumer, netflow_consumer, status_consumer # Add status_consumer

websocket_urlpatterns = [
    re_path(r'ws/syslog/$', syslog_consumer.PacketConsumer.as_asgi()),
    re_path(r'ws/netflow/$', netflow_consumer.NetflowConsumer.as_asgi()),
    re_path(r'ws/status/$', status_consumer.StatusConsumer.as_asgi()), # Add this line
]