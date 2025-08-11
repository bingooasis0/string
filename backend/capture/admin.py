from django.contrib import admin
from .models import SyslogEntry, NetflowEntry, NetconsoleEntry

@admin.register(SyslogEntry)
class SyslogAdmin(admin.ModelAdmin):
    list_display = ("id","received_at","hostname","app_name","facility","severity")

@admin.register(NetflowEntry)
class NetflowAdmin(admin.ModelAdmin):
    list_display = ("id","received_at","exporter_ip","src_ip","dst_ip","src_port","dst_port","protocol","packets","bytes")

@admin.register(NetconsoleEntry)
class NetconsoleAdmin(admin.ModelAdmin):
    list_display = ("id","received_at","source_ip")
