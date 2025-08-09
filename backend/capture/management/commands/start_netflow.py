import os
import socket
from scapy.all import sniff, UDP
from scapy.layers.netflow import NetflowSession, NetflowDataflowsetV9
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from datetime import datetime
from capture.models import NetflowEntry

flow_id_counter = 1

class Command(BaseCommand):
    help = 'Starts the Netflow/IPFIX listener server using Scapy.'

    def handle(self, *args, **kwargs):
        global flow_id_counter
        PORT = int(os.getenv('NETFLOW_PORT', 2055))
        
        self.stdout.write(self.style.SUCCESS(f'Starting Scapy Netflow/IPFIX listener on port {PORT}'))
        
        def process_packet(packet):
            global flow_id_counter
            if not packet.haslayer(NetflowDataflowsetV9):
                return

            try:
                channel_layer = get_channel_layer()
                
                for flow in packet[NetflowDataflowsetV9].records:
                    source_ip = getattr(flow, 'sourceIPv4Address', getattr(flow, 'srcaddr', 'N/A'))
                    dest_ip = getattr(flow, 'destinationIPv4Address', getattr(flow, 'dstaddr', 'N/A'))
                    source_port = getattr(flow, 'sourceTransportPort', getattr(flow, 'srcport', 'N/A'))
                    dest_port = getattr(flow, 'destinationTransportPort', getattr(flow, 'dstport', 'N/A'))
                    in_bytes = getattr(flow, 'octetDeltaCount', getattr(flow, 'dOctets', 0))
                    in_pkts = getattr(flow, 'packetDeltaCount', getattr(flow, 'dPkts', 0))

                    NetflowEntry.objects.create(
                        source_ip=f"{source_ip}:{source_port}",
                        destination_ip=f"{dest_ip}:{dest_port}",
                        protocol='NETFLOW/IPFIX',
                        info=f"Bytes: {in_bytes} | Packets: {in_pkts}"
                    )

                    packet_for_frontend = {
                        'id': flow_id_counter,
                        'timestamp': datetime.fromtimestamp(packet.time).isoformat(),
                        'source': f"{source_ip}:{source_port}",
                        'destination': f"{dest_ip}:{dest_port}",
                        'protocol': 'NETFLOW/IPFIX',
                        'info': f"Bytes: {in_bytes} | Packets: {in_pkts}"
                    }
                    
                    async_to_sync(channel_layer.group_send)(
                        'netflow_stream',
                        {'type': 'stream.message', 'message': packet_for_frontend}
                    )
                    async_to_sync(channel_layer.group_send)(
                        'service_status',
                        {'type': 'status.update', 'message': {'service': 'netflow', 'status': 'running'}}
                    )
                    flow_id_counter += 1
                
                self.stdout.write(self.style.SUCCESS(f"Processed and saved {len(packet[NetflowDataflowsetV9].records)} flows"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing decoded flow: {e}"))

        sniff(
            filter=f"udp and port {PORT}", 
            prn=process_packet, 
            session=NetflowSession,
            store=False
        )
