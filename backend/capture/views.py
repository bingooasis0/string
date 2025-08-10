import sys
import json
import subprocess
import os
import signal
from datetime import datetime, timedelta
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.db.models.functions import TruncMinute
from django.db.models import Count
from .models import SyslogEntry, NetflowEntry, NetconsoleEntry # Import the new model

PID_DIR = os.path.join(settings.BASE_DIR, 'running_pids')
os.makedirs(PID_DIR, exist_ok=True)

def is_process_running(pid):
    if pid is None: return False
    try:
        if os.name == 'nt':
            result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], capture_output=True, text=True, check=True)
            return str(pid) in result.stdout
        else:
            os.kill(pid, 0)
            return True
    except (OSError, subprocess.CalledProcessError):
        return False

@csrf_exempt
def start_service(request):
    if request.method != 'POST': return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
    try:
        data = json.loads(request.body)
        service_name = data.get('service')
        pid_file = os.path.join(PID_DIR, f'{service_name}.pid')
        
        # THIS IS UPDATED: Add 'netconsole' to the list of valid services
        if service_name not in ['syslog', 'netflow', 'netconsole']: 
            return JsonResponse({'status': 'error', 'message': 'Invalid service name'}, status=400)

        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                try:
                    pid = int(f.read())
                    if is_process_running(pid): return JsonResponse({'status': 'error', 'message': f'{service_name.capitalize()} service is already running.'}, status=400)
                except (ValueError, FileNotFoundError): pass
        
        python_executable = sys.executable
        if os.name == 'nt': python_executable = python_executable.replace('python.exe', 'pythonw.exe')
        command = [python_executable, 'manage.py', f'start_{service_name}']
        creation_flags = 0
        if os.name == 'nt': creation_flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
        process = subprocess.Popen(command, creationflags=creation_flags, close_fds=True)
        with open(pid_file, 'w') as f: f.write(str(process.pid))
        return JsonResponse({'status': 'success', 'message': f'{service_name.capitalize()} service started successfully with PID {process.pid}.'})
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def stop_service(request):
    if request.method != 'POST': return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
    try:
        data = json.loads(request.body)
        service_name = data.get('service')
        pid_file = os.path.join(PID_DIR, f'{service_name}.pid')

        # THIS IS UPDATED: Add 'netconsole' to the list of valid services
        if service_name not in ['syslog', 'netflow', 'netconsole']: 
            return JsonResponse({'status': 'error', 'message': 'Invalid service name'}, status=400)

        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f: pid = int(f.read())
            if is_process_running(pid):
                subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True)
                os.remove(pid_file)
                return JsonResponse({'status': 'success', 'message': f'{service_name.capitalize()} service (PID {pid}) stopped successfully.'})
            else:
                os.remove(pid_file)
                return JsonResponse({'status': 'error', 'message': 'Service was not running, but stale PID file was cleaned up.'}, status=400)
        else: return JsonResponse({'status': 'error', 'message': f'{service_name.capitalize()} service is not running.'}, status=400)
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def stop_all_services(request):
    # ... (This function remains correct)
    if request.method != 'POST': return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
    stopped_count = 0
    errors = []
    for filename in os.listdir(PID_DIR):
        if filename.endswith(".pid"):
            service_name = filename.split('.')[0]
            pid_file = os.path.join(PID_DIR, filename)
            try:
                with open(pid_file, 'r') as f: pid = int(f.read())
                if is_process_running(pid):
                    subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True)
                    stopped_count += 1
                os.remove(pid_file)
            except (ValueError, FileNotFoundError): os.remove(pid_file)
            except Exception as e: errors.append(f"Could not stop {service_name}: {e}")
    if errors: return JsonResponse({'status': 'error', 'message': ' '.join(errors)}, status=500)
    return JsonResponse({'status': 'success', 'message': f'Successfully stopped {stopped_count} services.'})

@csrf_exempt
def purge_all_data(request):
    # THIS IS UPDATED: Add NetconsoleEntry to the purge logic
    if request.method != 'POST': return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
    try:
        syslog_deleted_count, _ = SyslogEntry.objects.all().delete()
        netflow_deleted_count, _ = NetflowEntry.objects.all().delete()
        netconsole_deleted_count, _ = NetconsoleEntry.objects.all().delete()
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='capture_syslogentry';")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='capture_netflowentry';")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='capture_netconsoleentry';")
        total = syslog_deleted_count + netflow_deleted_count + netconsole_deleted_count
        return JsonResponse({'status': 'success', 'message': f'Successfully purged {total} records and reset counters.'})
    except Exception as e: return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def get_recent_syslog_entries(request):
    recent_entries = SyslogEntry.objects.order_by('-received_at')[:200]
    data = [{'id': entry.id, 'timestamp': entry.received_at.isoformat(), 'source': entry.hostname, 'protocol': 'SYSLOG', 'info': entry.message} for entry in recent_entries]
    return JsonResponse(data, safe=False)

def get_recent_netflow_entries(request):
    recent_entries = NetflowEntry.objects.order_by('-received_at')[:200]
    data = [{'id': entry.id, 'timestamp': entry.received_at.isoformat(), 'source': entry.source_ip, 'protocol': entry.protocol, 'info': entry.info} for entry in recent_entries]
    return JsonResponse(data, safe=False)

# --- NEW FUNCTION ---
def get_recent_netconsole_entries(request):
    """
    Queries the database for the 200 most recent netconsole entries.
    """
    recent_entries = NetconsoleEntry.objects.order_by('-received_at')[:200]
    data = [
        {
            'id': entry.id,
            'timestamp': entry.received_at.isoformat(),
            'source': entry.source_ip,
            'protocol': 'NETCONSOLE',
            'info': entry.message
        }
        for entry in recent_entries
    ]
    return JsonResponse(data, safe=False)

def get_historical_volume(request):
    # ... (This function remains correct)
    now = datetime.now()
    start_time = now - timedelta(hours=24)
    syslog_data = (SyslogEntry.objects.filter(received_at__gte=start_time).annotate(minute=TruncMinute('received_at')).values('minute').annotate(count=Count('id')).order_by('minute'))
    netflow_data = (NetflowEntry.objects.filter(received_at__gte=start_time).annotate(minute=TruncMinute('received_at')).values('minute').annotate(count=Count('id')).order_by('minute'))
    chart_data = {}
    for entry in syslog_data:
        timestamp = entry['minute'].strftime('%H:%M')
        if timestamp not in chart_data: chart_data[timestamp] = {'time': timestamp, 'syslog': 0, 'netflow': 0}
        chart_data[timestamp]['syslog'] += entry['count']
    for entry in netflow_data:
        timestamp = entry['minute'].strftime('%H:%M')
        if timestamp not in chart_data: chart_data[timestamp] = {'time': timestamp, 'syslog': 0, 'netflow': 0}
        chart_data[timestamp]['netflow'] += entry['count']
    return JsonResponse(sorted(chart_data.values(), key=lambda x: x['time']), safe=False)
