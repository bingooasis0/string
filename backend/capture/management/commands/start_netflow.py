import os
import socket
import threading
import time
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from capture.models import NetflowEntry
from capture.netflow_decoder import TemplateCache, parse_packet

class Command(BaseCommand):
    help = 'Starts a NetFlow v9/IPFIX listener on UDP'

    def handle(self, *args, **kwargs):
        host = os.getenv('NETFLOW_HOST', '0.0.0.0')
        port = int(os.getenv('NETFLOW_PORT', '2055'))
        cache_key = 'service:netflow:last_seen'
        channel_layer = get_channel_layer()
        cache.set(cache_key, time.time(), timeout=30)

        def heartbeat():
            while True:
                cache.set(cache_key, time.time(), timeout=30)
                async_to_sync(channel_layer.group_send)(
                    'service_status',
                    {'type': 'status.update', 'message': {'service': 'netflow', 'status': 'running', 'pid': os.getpid(), 'port': port, 'ts': timezone.now().isoformat()}}
                )
                time.sleep(2)

        threading.Thread(target=heartbeat, daemon=True).start()

        cache_templates = TemplateCache()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8 * 1024 * 1024)
        s.bind((host, port))

        while True:
            data, addr = s.recvfrom(65535)
            exporter_ip = addr[0]
            pkt = parse_packet(data, exporter_ip, cache_templates)
            for f in pkt["flows"]:
                db = NetflowEntry.objects.create(
                    exporter_ip=f.get("exporter_ip"),
                    observation_domain_id=f.get("observation_domain_id"),
                    template_id=f.get("template_id"),
                    flow_start=f.get("flow_start"),
                    flow_end=f.get("flow_end"),
                    src_ip=f.get("src_ip"),
                    dst_ip=f.get("dst_ip"),
                    src_port=f.get("src_port"),
                    dst_port=f.get("dst_port"),
                    protocol=f.get("protocol"),
                    tos=f.get("tos"),
                    tcp_flags=f.get("tcp_flags"),
                    packets=f.get("packets"),
                    bytes=f.get("bytes"),
                    input_if=f.get("input_if"),
                    output_if=f.get("output_if"),
                    vlan_id_in=f.get("vlan_id_in"),
                    vlan_id_out=f.get("vlan_id_out"),
                    next_hop=f.get("next_hop"),
                    src_as=f.get("src_as"),
                    dst_as=f.get("dst_as"),
                    info=None,
                    raw=data
                )
                msg = {
                    'id': db.id,
                    'timestamp': db.received_at.isoformat(),
                    'source': f"{db.src_ip}:{db.src_port}" if db.src_ip and db.src_port else db.exporter_ip,
                    'destination': f"{db.dst_ip}:{db.dst_port}" if db.dst_ip and db.dst_port else '',
                    'protocol': 'NETFLOW',
                    'info': f"bytes={db.bytes or 0} packets={db.packets or 0} proto={db.protocol or 0}"
                }
                async_to_sync(channel_layer.group_send)('netflow_stream', {'type': 'stream.message', 'message': msg})
