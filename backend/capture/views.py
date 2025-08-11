# backend/capture/views.py

import os
import sys
import json
import time
import signal
import subprocess
from datetime import datetime, timedelta

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.db.models import Count
from django.db.models.functions import TruncMinute
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import SyslogEntry, NetflowEntry, NetconsoleEntry, SnmpTrap


PID_DIR = os.path.join(settings.BASE_DIR, 'running_pids')
os.makedirs(PID_DIR, exist_ok=True)


def is_process_running(pid: int) -> bool:
    if not pid:
        return False
    try:
        if os.name == 'nt':
            # Check with tasklist on Windows
            res = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}'],
                capture_output=True,
                text=True
            )
            return str(pid) in res.stdout
        else:
            # POSIX check
            os.kill(pid, 0)
            return True
    except Exception:
        return False


@csrf_exempt
def start_service(request):
    """POST {"service":"syslog|netflow|netconsole|snmp"} -> start background mgmt command."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

    try:
        data = json.loads(request.body or '{}')
        service_name = data.get('service')
        valid_services = ['syslog', 'netflow', 'netconsole', 'snmp']
        if service_name not in valid_services:
            return JsonResponse({'status': 'error', 'message': 'Invalid service name'}, status=400)

        pid_file = os.path.join(PID_DIR, f'{service_name}.pid')

        # already running?
        if os.path.exists(pid_file):
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                if is_process_running(pid):
                    return JsonResponse(
                        {'status': 'error', 'message': f'{service_name.capitalize()} service is already running.'},
                        status=400
                    )
            except Exception:
                # stale or bad pid file; fall through to start new
                pass

        # launch management command in background
        py = sys.executable
        if os.name == 'nt':
            # use pythonw to avoid console popping
            py = py.replace('python.exe', 'pythonw.exe')

        cmd = [py, 'manage.py', f'start_{service_name}']

        creation_flags = 0
        if os.name == 'nt':
            creation_flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW

        proc = subprocess.Popen(cmd, creationflags=creation_flags, close_fds=True)

        with open(pid_file, 'w') as f:
            f.write(str(proc.pid))

        return JsonResponse({
            'status': 'success',
            'message': f'{service_name.capitalize()} service started successfully with PID {proc.pid}.'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def stop_service(request):
    """POST {"service":"syslog|netflow|netconsole|snmp"} -> stop by PID file."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

    try:
        data = json.loads(request.body or '{}')
        service_name = data.get('service')
        valid_services = ['syslog', 'netflow', 'netconsole', 'snmp']
        if service_name not in valid_services:
            return JsonResponse({'status': 'error', 'message': 'Invalid service name'}, status=400)

        pid_file = os.path.join(PID_DIR, f'{service_name}.pid')

        if not os.path.exists(pid_file):
            return JsonResponse({'status': 'error', 'message': f'{service_name.capitalize()} service is not running.'}, status=400)

        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
        except Exception:
            pid = None

        if pid and is_process_running(pid):
            try:
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True)
                else:
                    os.kill(pid, signal.SIGTERM)
            except Exception:
                pass

        # remove pid file regardless
        try:
            os.remove(pid_file)
        except Exception:
            pass

        return JsonResponse({'status': 'success', 'message': f'{service_name.capitalize()} service stopped.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def stop_all_services(request):
    """Stop any service that has a pid file in running_pids."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

    stopped = 0
    errors = []

    try:
        for fname in os.listdir(PID_DIR):
            if not fname.endswith('.pid'):
                continue
            path = os.path.join(PID_DIR, fname)
            try:
                with open(path, 'r') as f:
                    pid = int(f.read().strip())
                if is_process_running(pid):
                    if os.name == 'nt':
                        subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True)
                    else:
                        os.kill(pid, signal.SIGTERM)
                    stopped += 1
            except Exception:
                pass
            finally:
                try:
                    os.remove(path)
                except Exception:
                    pass
    except Exception as e:
        errors.append(str(e))

    if errors:
        return JsonResponse({'status': 'error', 'message': ' '.join(errors)}, status=500)

    return JsonResponse({'status': 'success', 'message': f'Successfully stopped {stopped} services.'})


@csrf_exempt
def purge_all_data(request):
    """Delete all records across collectors and reset SQLite autoincrement."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

    try:
        syslog_deleted_count, _ = SyslogEntry.objects.all().delete()
        netflow_deleted_count, _ = NetflowEntry.objects.all().delete()
        netconsole_deleted_count, _ = NetconsoleEntry.objects.all().delete()
        snmp_deleted_count, _ = SnmpTrap.objects.all().delete()

        # Reset autoincrement for SQLite (safe to ignore errors elsewhere)
        try:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='capture_syslogentry';")
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='capture_netflowentry';")
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='capture_netconsoleentry';")
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='capture_snmptrap';")
        except Exception:
            pass

        total = syslog_deleted_count + netflow_deleted_count + netconsole_deleted_count + snmp_deleted_count
        return JsonResponse({'status': 'success', 'message': f'Successfully purged {total} records and reset counters.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def get_recent_syslog_entries(request):
    recent = SyslogEntry.objects.order_by('-received_at')[:200]
    data = [{
        'id': r.id,
        'timestamp': r.received_at.isoformat(),
        'source': r.hostname,
        'protocol': 'SYSLOG',
        'info': r.message
    } for r in recent]
    return JsonResponse(data, safe=False)


def get_recent_netflow_entries(request):
    q = NetflowEntry.objects.order_by('-received_at')[:200]
    data = []
    for e in q:
        duration = None
        if e.flow_start and e.flow_end:
            duration = (e.flow_end - e.flow_start).total_seconds()
        data.append({
            'id': e.id,
            'timestamp': e.received_at.isoformat(),
            'exporter_ip': e.exporter_ip,
            'odid': e.observation_domain_id,
            'template_id': e.template_id,
            'src_ip': e.src_ip,
            'src_port': e.src_port,
            'dst_ip': e.dst_ip,
            'dst_port': e.dst_port,
            'protocol': e.protocol,
            'packets': e.packets or 0,
            'bytes': e.bytes or 0,
            'flow_start': e.flow_start.isoformat() if e.flow_start else None,
            'flow_end': e.flow_end.isoformat() if e.flow_end else None,
            'duration': duration,
            'tos': e.tos,
            'tcp_flags': e.tcp_flags,
            'input_if': e.input_if,
            'output_if': e.output_if,
            'vlan_id_in': e.vlan_id_in,
            'vlan_id_out': e.vlan_id_out,
            'src_as': e.src_as,
            'dst_as': e.dst_as,
        })
    return JsonResponse(data, safe=False)


def get_recent_netconsole_entries(request):
    recent = NetconsoleEntry.objects.order_by('-received_at')[:200]
    data = [{
        'id': r.id,
        'timestamp': r.received_at.isoformat(),
        'source': r.source_ip,
        'protocol': 'NETCONSOLE',
        'info': r.message
    } for r in recent]
    return JsonResponse(data, safe=False)


def recent_snmp(request):
    qs = SnmpTrap.objects.order_by('-id')[:200]
    data = []
    for t in qs:
        data.append({
            "id": t.id,
            "timestamp": t.timestamp.isoformat(),
            "source_ip": t.source_ip,
            "version": t.version,
            "community": t.community,
            "user": t.user,
            "trap_oid": t.trap_oid,
            "enterprise_oid": t.enterprise_oid,
            "generic_trap": t.generic_trap,
            "specific_trap": t.specific_trap,
            "uptime": t.uptime,
            "severity": t.severity,
            "context_engine_id": t.context_engine_id,
            "context_name": t.context_name,
            "security_level": t.security_level,
            "auth_protocol": t.auth_protocol,
            "priv_protocol": t.priv_protocol,
            "engine_boots": t.engine_boots,
            "engine_time": t.engine_time,
            "var_binds": t.var_binds,
            "info": t.info or "",
        })
    return JsonResponse(data, safe=False)


def _graph_volume_payload():
    """
    24h per-minute counts for syslog / netflow / netconsole / snmp
    using the correct datetime fields on each model.
    """
    now = timezone.now()
    start = now - timezone.timedelta(hours=24)

    # Prefill minute buckets
    buckets = {}
    t = start.replace(second=0, microsecond=0)
    while t <= now:
        label = t.strftime('%H:%M')
        buckets[label] = {'time': label, 'syslog': 0, 'netflow': 0, 'netconsole': 0, 'snmp': 0}
        t += timezone.timedelta(minutes=1)

    def add(model, dt_field: str, key: str):
        qs = (model.objects
              .filter(**{f'{dt_field}__gte': start, f'{dt_field}__lte': now})
              .annotate(m=TruncMinute(dt_field))
              .values('m').annotate(c=Count('id')))
        for row in qs:
            label = row['m'].strftime('%H:%M')
            if label in buckets:
                buckets[label][key] += row['c']

    add(SyslogEntry,     'received_at', 'syslog')
    add(NetflowEntry,    'received_at', 'netflow')
    add(NetconsoleEntry, 'received_at', 'netconsole')
    add(SnmpTrap,        'timestamp',   'snmp')

    # Return list sorted by time label
    return list(buckets.values())


def graph_volume(request):
    return JsonResponse(_graph_volume_payload(), safe=False)


# Keep this so whichever URL you wired up still works
def get_historical_volume(request):
    return JsonResponse(_graph_volume_payload(), safe=False)


def service_status(request):
    """Report 'running'/'down' for each service (syslog/netflow/netconsole/snmp)."""
    services = ['syslog', 'netflow', 'netconsole', 'snmp']
    out = {}

    for s in services:
        # heartbeat from workers (set elsewhere) keeps this hot
        last = cache.get(f'service:{s}:last_seen')
        alive = False
        if last is not None:
            try:
                alive = (time.time() - float(last)) < 8
            except Exception:
                alive = False

        # pid file fallback
        pid_file = os.path.join(PID_DIR, f'{s}.pid')
        pid_alive = False
        if os.path.exists(pid_file):
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                pid_alive = is_process_running(pid)
            except Exception:
                pid_alive = False

        out[s] = 'running' if (alive or pid_alive) else 'down'

    return JsonResponse(out)
