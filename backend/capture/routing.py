from django.urls import re_path
from .consumers import (
    SyslogConsumer,
    NetflowConsumer,
    NetconsoleConsumer,
    StatusConsumer,
    SnmpConsumer,
)

websocket_urlpatterns = [
    re_path(r"^ws/syslog/$", SyslogConsumer.as_asgi()),
    re_path(r"^ws/netflow/$", NetflowConsumer.as_asgi()),
    re_path(r"^ws/netconsole/$", NetconsoleConsumer.as_asgi()),
    re_path(r"^ws/status/$", StatusConsumer.as_asgi()),
    re_path(r"^ws/snmp/$", SnmpConsumer.as_asgi()),
]