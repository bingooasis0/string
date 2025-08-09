from django.contrib import admin
from .models import SyslogEntry, NetflowEntry

admin.site.register(SyslogEntry)
admin.site.register(NetflowEntry)