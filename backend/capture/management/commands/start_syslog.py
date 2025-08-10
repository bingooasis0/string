# C:\Users\colby\Desktop\String\backend\capture\management\commands\start_syslog.py

import os
import socketserver
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from capture.syslog_parser import parse_message
from capture.models import SyslogEntry

class SyslogUDPHandler(socketserver.BaseRequestHandler):
    """
    The handler for incoming syslog messages.
    """
    def handle(self):
        data = self.request[0].strip()
        client_address = self.client_address[0]

        try:
            message_str = data.decode('utf-8')
            parsed_data = parse_message(message_str)

            if parsed_data:
                try:
                    # Save the entry to the database first. The database will automatically
                    # assign a new, unique, auto-incrementing ID.
                    db_entry = SyslogEntry.objects.create(
                        hostname=parsed_data.get('hostname', 'N/A'),
                        app_name=parsed_data.get('app_name'),
                        message=parsed_data.get('message', ''),
                        raw_message=message_str
                    )
                except Exception as e:
                    print(f"DATABASE ERROR: Could not save log to database: {e}")
                    return # Stop if we can't save

                # For the live view, we now use the real, persistent ID from the database record.
                packet_for_frontend = {
                    'id': db_entry.id,
                    'timestamp': db_entry.received_at.isoformat(),
                    'source': client_address,
                    'protocol': 'SYSLOG',
                    'info': db_entry.message
                }

                channel_layer = get_channel_layer()
                
                # Send to the syslog page
                async_to_sync(channel_layer.group_send)(
                    'syslog_stream',
                    {'type': 'stream.message', 'message': packet_for_frontend}
                )

                # Send a heartbeat
                async_to_sync(channel_layer.group_send)(
                    'service_status',
                    {'type': 'status.update', 'message': {'service': 'syslog', 'status': 'running'}}
                )

                print(f"Received, saved (ID: {db_entry.id}), and sent packet from {client_address}")
            else:
                print(f"Could not parse syslog message: {message_str}")

        except UnicodeDecodeError:
            print("Could not decode message.")


class Command(BaseCommand):
    help = 'Starts the Syslog listener server.'

    def handle(self, *args, **kwargs):
        # The faulty startup logic has been removed. The script is now stateless
        # and relies on the database's auto-incrementing primary key.
        HOST = os.getenv('SYSLOG_HOST', '0.0.0.0')
        PORT = int(os.getenv('SYSLOG_PORT', 514))

        self.stdout.write(self.style.SUCCESS(f'Starting syslog listener on {HOST}:{PORT}'))

        try:
            with socketserver.UDPServer((HOST, PORT), SyslogUDPHandler) as server:
                server.serve_forever()
        except PermissionError:
            self.stdout.write(self.style.ERROR(
                f"Permission denied to bind to port {PORT}. Try running as administrator."
            ))
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('\nSyslog listener stopped.'))
