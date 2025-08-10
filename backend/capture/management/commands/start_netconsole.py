import os
import socketserver
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from capture.models import NetconsoleEntry

class NetconsoleUDPHandler(socketserver.BaseRequestHandler):
    """
    The handler for incoming Netconsole messages.
    """
    def handle(self):
        data = self.request[0].strip()
        client_address = self.client_address[0]

        try:
            message_str = data.decode('utf-8', errors='ignore')

            # For Netconsole, we often just want the raw kernel message.
            # We will save it directly without complex parsing for now.
            try:
                db_entry = NetconsoleEntry.objects.create(
                    source_ip=client_address,
                    message=message_str,
                    raw_message=message_str
                )
            except Exception as e:
                print(f"DATABASE ERROR: Could not save Netconsole log: {e}")
                return

            packet_for_frontend = {
                'id': db_entry.id,
                'timestamp': db_entry.received_at.isoformat(),
                'source': db_entry.source_ip,
                'protocol': 'NETCONSOLE',
                'info': db_entry.message
            }

            channel_layer = get_channel_layer()
            
            # Send to the new 'netconsole_stream' group
            async_to_sync(channel_layer.group_send)(
                'netconsole_stream',
                {'type': 'stream.message', 'message': packet_for_frontend}
            )

            # Send a heartbeat for the new service
            async_to_sync(channel_layer.group_send)(
                'service_status',
                {'type': 'status.update', 'message': {'service': 'netconsole', 'status': 'running'}}
            )

            print(f"Received, saved (ID: {db_entry.id}), and sent Netconsole packet from {client_address}")

        except Exception as e:
            print(f"Error processing Netconsole packet: {e}")


class Command(BaseCommand):
    help = 'Starts the Netconsole listener server.'

    def handle(self, *args, **kwargs):
        HOST = os.getenv('NETCONSOLE_HOST', '0.0.0.0')
        PORT = int(os.getenv('NETCONSOLE_PORT', 6666))

        self.stdout.write(self.style.SUCCESS(f'Starting Netconsole listener on {HOST}:{PORT}'))

        try:
            with socketserver.UDPServer((HOST, PORT), NetconsoleUDPHandler) as server:
                server.serve_forever()
        except PermissionError:
            self.stdout.write(self.style.ERROR(
                f"Permission denied to bind to port {PORT}. Try running as administrator."
            ))
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('\nNetconsole listener stopped.'))
