# backend/capture/management/commands/start_snmp.py
import os
import json
import socket
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from capture.models import SnmpTrap

# pysnmp (lextudio / upstream both expose these paths)
from pysnmp.entity import engine, config
from pysnmp.entity.rfc3413 import ntfrcv
from pysnmp.carrier.asyncio.dgram import udp


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.lower() in ("1", "true", "yes", "on")


class Command(BaseCommand):
    help = "Start SNMP trap receiver"

    def handle(self, *args, **options):
        # --- Defaults that work even when launched from UI (no shell env) ---
        # Community defaults to 'string' as requested; supports CSV override.
        communities_csv = os.getenv("SNMP_COMMUNITIES", "string")
        communities = [c.strip() for c in communities_csv.split(",") if c.strip()]
        if not communities:
            communities = ["string"]

        # Port: try env (default 162); if binding fails (WSAECONNREFUSED/ACCESS), fall back to 1162.
        try:
            listen_port = int(os.getenv("SNMP_TRAP_PORT", "162"))
        except ValueError:
            listen_port = 162

        v3_enabled = _env_bool("SNMP_V3_ENABLED", False)
        v3_user = os.getenv("SNMP_V3_USER", "")
        v3_auth_key = os.getenv("SNMP_V3_AUTH_KEY", "")
        v3_auth_proto = os.getenv("SNMP_V3_AUTH_PROTO", "SHA")  # SHA|MD5|SHA224|SHA256|SHA384|SHA512
        v3_priv_key = os.getenv("SNMP_V3_PRIV_KEY", "")
        v3_priv_proto = os.getenv("SNMP_V3_PRIV_PROTO", "AES128")  # AES128|AES192|AES256|DES

        snmpEngine = engine.SnmpEngine()

        # v1/v2c communities
        for idx, comm in enumerate(communities, start=1):
            # userName acts as a tag; use a stable label
            config.addV1System(snmpEngine, f"v2c-{idx}", comm)

        # optional v3
        if v3_enabled and v3_user:
            from pysnmp.hlapi.auth import (
                usmHMACMD5AuthProtocol,
                usmHMACSHAAuthProtocol,
                usmHMAC128SHA224AuthProtocol,
                usmHMAC192SHA256AuthProtocol,
                usmHMAC256SHA384AuthProtocol,
                usmHMAC384SHA512AuthProtocol,
                usmNoAuthProtocol,
            )
            from pysnmp.hlapi.priv import (
                usmDESPrivProtocol,
                usmAesCfb128Protocol,
                usmAesCfb192Protocol,
                usmAesCfb256Protocol,
                usmNoPrivProtocol,
            )

            auth_map = {
                "MD5": usmHMACMD5AuthProtocol,
                "SHA": usmHMACSHAAuthProtocol,
                "SHA224": usmHMAC128SHA224AuthProtocol,
                "SHA256": usmHMAC192SHA256AuthProtocol,
                "SHA384": usmHMAC256SHA384AuthProtocol,
                "SHA512": usmHMAC384SHA512AuthProtocol,
                "NONE": usmNoAuthProtocol,
            }
            priv_map = {
                "DES": usmDESPrivProtocol,
                "AES128": usmAesCfb128Protocol,
                "AES192": usmAesCfb192Protocol,
                "AES256": usmAesCfb256Protocol,
                "NONE": usmNoPrivProtocol,
            }

            auth_proto = auth_map.get(v3_auth_proto.upper(), auth_map["SHA"])
            priv_proto = priv_map.get(v3_priv_proto.upper(), priv_map["AES128"])

            config.addV3User(
                snmpEngine,
                v3_user,
                auth_proto if v3_auth_key else auth_map["NONE"],
                v3_auth_key or None,
                priv_proto if v3_priv_key else priv_map["NONE"],
                v3_priv_key or None,
            )

        # transport
        def open_transport(port: int):
            config.addTransport(
                snmpEngine,
                udp.domainName,
                udp.UdpTransport().openServerMode(("0.0.0.0", port)),
            )

        try:
            open_transport(listen_port)
            bound_port = listen_port
        except OSError as e:
            # Common on Windows when port is already taken or blocked; fall back to 1162
            fallback = 1162
            self.stderr.write(
                self.style.WARNING(
                    f"Could not bind UDP/{listen_port} ({e}); falling back to UDP/{fallback}"
                )
            )
            open_transport(fallback)
            bound_port = fallback

        # callback
        channel_layer = get_channel_layer()

        def _on_trap(snmpEngine, stateReference, contextEngineId, contextName, varBinds, cbCtx):
            # peer info
            transportDomain, transportAddress = snmpEngine.msgAndPduDsp.getTransportInfo(
                stateReference
            )
            src_ip = transportAddress[0] if isinstance(transportAddress, tuple) else str(transportAddress)

            # unwrap var-binds
            vb = {str(name): str(val) for name, val in varBinds}
            trap_oid = vb.get("1.3.6.1.6.3.1.1.4.1.0") or vb.get("SNMPv2-MIB::snmpTrapOID.0")

            # save to DB
            obj = SnmpTrap.objects.create(
                timestamp=timezone.now(),
                source_ip=src_ip,
                version="v2c",  # most likely; pysnmp does not pass version directly here
                community=communities[0],  # best-effort / principal community
                user=v3_user if v3_enabled else None,
                trap_oid=str(trap_oid) if trap_oid else None,
                var_binds=json.dumps(vb, ensure_ascii=False),
                info=None,
            )

            # push to websocket group "snmp"
            payload = {
                "id": obj.id,
                "timestamp": obj.timestamp.isoformat(),
                "source_ip": obj.source_ip,
                "version": obj.version,
                "community": obj.community,
                "trap_oid": obj.trap_oid,
                "var_binds": vb,
            }
            try:
                async_to_sync(channel_layer.group_send)(
                    "snmp",
                    {"type": "snmp.message", "text": json.dumps(payload)},
                )
            except Exception:
                # websocket is best-effort; don't crash the collector
                pass

        ntfrcv.NotificationReceiver(snmpEngine, _on_trap)

        # log what we're doing
        comm_list = ", ".join(communities)
        self.stdout.write(self.style.SUCCESS(f"SNMP trap receiver listening on 0.0.0.0:{bound_port}"))
        self.stdout.write(f"Communities: {comm_list}")
        if v3_enabled and v3_user:
            self.stdout.write(f"SNMPv3: user '{v3_user}' enabled")
        else:
            self.stdout.write("SNMPv3: disabled")

        # run forever
        snmpEngine.transportDispatcher.jobStarted(1)
        try:
            snmpEngine.transportDispatcher.runDispatcher()
        finally:
            snmpEngine.transportDispatcher.closeDispatcher()
