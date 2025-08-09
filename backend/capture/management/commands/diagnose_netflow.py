# C:\Users\colby\Desktop\String\backend\capture\management\commands\diagnose_netflow.py

import os
import socket
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Runs a barebones UDP listener to diagnose Netflow traffic.'

    def handle(self, *args, **kwargs):
        HOST = os.getenv('NETFLOW_HOST', '0.0.0.0')
        PORT = int(os.getenv('NETFLOW_PORT', 2055))

        # Create a standard UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            sock.bind((HOST, PORT))
            self.stdout.write(self.style.SUCCESS(f'Barebones listener started on {HOST}:{PORT}. Waiting for data...'))

            while True:
                # Wait for a packet
                data, addr = sock.recvfrom(4096)

                # Get the raw data as a hexadecimal string
                hex_data = data.hex()

                # Print the results
                self.stdout.write(f"--- Packet Received from {addr[0]}:{addr[1]} ---")
                self.stdout.write(f"Size: {len(data)} bytes")
                self.stdout.write(f"Hex Data: {hex_data}")
                self.stdout.write("-" * 40)

        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('\nListener stopped.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
        finally:
            sock.close()