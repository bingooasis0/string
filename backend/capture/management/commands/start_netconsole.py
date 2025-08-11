import os
import socketserver
import threading
import time
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from capture.models import NetconsoleEntry

class NetconsoleUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        client_address = self.client_address[0]
        message_str = data.decode('utf-8', errors='ignore')
        db_entry = NetconsoleEntry.objects.create(
            source_ip=client_address,
            message=message_str,
            raw_message=message_str
        )
        channel_layer = get_channel_layer()
        packet_for_frontend = {
            'id': db_entry.id,
            'timestamp': db_entry.received_at.isoformat(),
            'source': db_entry.source_ip,
            'protocol': 'NETCONSOLE',
            'info': db_entry.message
        }
        async_to_sync(channel_layer.group_send)('netconsole_stream', {'type': 'stream.message', 'message': packet_for_frontend})

class Command(BaseCommand):
    help = 'Starts the Netconsole listener server.'

    def handle(self, *args, **kwargs):
        host = os.getenv('NETCONSOLE_HOST', '0.0.0.0')
        port = int(os.getenv('NETCONSOLE_PORT', 6666))
        cache_key = 'service:netconsole:last_seen'
        channel_layer = get_channel_layer()
        cache.set(cache_key, time.time(), timeout=30)

        def heartbeat():
            while True:
                cache.set(cache_key, time.time(), timeout=30)
                async_to_sync(channel_layer.group_send)(
                    'service_status',
                    {'type': 'status.update', 'message': {'service': 'netconsole', 'status': 'running', 'pid': os.getpid(), 'port': port, 'ts': timezone.now().isoformat()}}
                )
                time.sleep(2)

        threading.Thread(target=heartbeat, daemon=True).start()

        try:
            with socketserver.UDPServer((host, port), NetconsoleUDPHandler) as server:
                server.serve_forever()
        except PermissionError:
            self.stdout.write(self.style.ERROR(f'Permission denied to bind to port {port}.'))
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('\nNetconsole listener stopped.'))
