import os
import socketserver
import threading
import time
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from capture.syslog_parser import parse_message
from capture.models import SyslogEntry

class SyslogUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        client_address = self.client_address[0]
        try:
            message_str = data.decode('utf-8')
            parsed_data = parse_message(message_str)
            if parsed_data:
                db_entry = SyslogEntry.objects.create(
                    hostname=parsed_data.get('hostname', 'N/A'),
                    app_name=parsed_data.get('app_name'),
                    message=parsed_data.get('message', ''),
                    raw_message=message_str
                )
                packet_for_frontend = {
                    'id': db_entry.id,
                    'timestamp': db_entry.received_at.isoformat(),
                    'source': client_address,
                    'protocol': 'SYSLOG',
                    'info': db_entry.message
                }
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)('syslog_stream', {'type': 'stream.message', 'message': packet_for_frontend})
        except UnicodeDecodeError:
            pass

class Command(BaseCommand):
    help = 'Starts the Syslog listener server.'

    def handle(self, *args, **kwargs):
        host = os.getenv('SYSLOG_HOST', '0.0.0.0')
        port = int(os.getenv('SYSLOG_PORT', 514))
        cache_key = 'service:syslog:last_seen'
        channel_layer = get_channel_layer()
        cache.set(cache_key, time.time(), timeout=30)

        def heartbeat():
            while True:
                cache.set(cache_key, time.time(), timeout=30)
                async_to_sync(channel_layer.group_send)(
                    'service_status',
                    {'type': 'status.update', 'message': {'service': 'syslog', 'status': 'running', 'pid': os.getpid(), 'port': port, 'ts': timezone.now().isoformat()}}
                )
                time.sleep(2)

        threading.Thread(target=heartbeat, daemon=True).start()

        try:
            with socketserver.UDPServer((host, port), SyslogUDPHandler) as server:
                server.serve_forever()
        except PermissionError:
            self.stdout.write(self.style.ERROR(f'Permission denied to bind to port {port}.'))
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('\nSyslog listener stopped.'))
