# C:\Users\colby\Desktop\String\backend\capture\management\commands\start_syslog.py

import os
import socketserver
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from capture.syslog_parser import parse_message
from capture.models import SyslogEntry # Import the database model

# A global packet ID to keep track of the order for the live view
packet_id_counter = 1

class SyslogUDPHandler(socketserver.BaseRequestHandler):
    """
    The handler for incoming syslog messages.
    An instance of this class is created for each message.
    """
    def handle(self):
        global packet_id_counter
        data = self.request[0].strip()
        client_address = self.client_address[0]

        try:
            message_str = data.decode('utf-8')
            parsed_data = parse_message(message_str)

            if parsed_data:
                # --- THIS IS THE NEW BLOCK TO SAVE TO THE DATABASE ---
                try:
                    SyslogEntry.objects.create(
                        hostname=parsed_data.get('hostname', 'N/A'),
                        app_name=parsed_data.get('app_name'),
                        message=parsed_data.get('message', ''),
                        raw_message=message_str # Save the original message for auditing
                    )
                except Exception as e:
                    print(f"DATABASE ERROR: Could not save log to database: {e}")
                # --- END OF NEW BLOCK ---

                # Format the parsed data for the live frontend view
                packet_for_frontend = {
                    'id': packet_id_counter,
                    'timestamp': parsed_data['timestamp'],
                    'source': client_address, # The IP where the syslog came from
                    'protocol': 'SYSLOG',
                    'info': parsed_data['message']
                }

                # Get the channel layer and send the data to the group
                channel_layer = get_channel_layer()
                
                # Send to the syslog page
                async_to_sync(channel_layer.group_send)(
                    'syslog_stream',
                    {
                        'type': 'stream.message',
                        'message': packet_for_frontend
                    }
                )

                # Send a heartbeat to the status page
                async_to_sync(channel_layer.group_send)(
                    'service_status',
                    {
                        'type': 'status.update',
                        'message': {'service': 'syslog', 'status': 'running'}
                    }
                )

                print(f"Received, saved, and sent packet #{packet_id_counter} from {client_address}")
                packet_id_counter += 1
            else:
                print(f"Could not parse syslog message: {message_str}")

        except UnicodeDecodeError:
            print("Could not decode message.")


class Command(BaseCommand):
    help = 'Starts the Syslog listener server.'

    def handle(self, *args, **kwargs):
        # Read configuration from the .env file
        HOST = os.getenv('SYSLOG_HOST', '0.0.0.0')
        PORT = int(os.getenv('SYSLOG_PORT', 514))

        self.stdout.write(self.style.SUCCESS(f'Starting syslog listener on {HOST}:{PORT}'))

        try:
            with socketserver.UDPServer((HOST, PORT), SyslogUDPHandler) as server:
                # The server will run forever until you press Ctrl+C
                server.serve_forever()
        except PermissionError:
            self.stdout.write(self.style.ERROR(
                f"Permission denied to bind to port {PORT}. "
                "Try running as administrator or use a port number greater than 1024."
            ))
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('\nSyslog listener stopped.'))
