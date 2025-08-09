import sys
import json
import subprocess
from django.http import JsonResponse
from .models import SyslogEntry, NetflowEntry

# A simple in-memory dictionary to keep track of our running service processes.
# In a real production app, a more robust system like Celery or a system service would be used.
running_services = {}

def start_service(request):
    """
    Starts a collector service (syslog or netflow) as a background process.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

    try:
        data = json.loads(request.body)
        service_name = data.get('service')

        # Security check: Only allow specific, known services to be started
        if service_name not in ['syslog', 'netflow']:
            return JsonResponse({'status': 'error', 'message': 'Invalid service name'}, status=400)

        if service_name in running_services and running_services[service_name].poll() is None:
            return JsonResponse({'status': 'error', 'message': f'{service_name.capitalize()} service is already running.'}, status=400)

        # Construct the command to run the appropriate management script
        command = [sys.executable, 'manage.py', f'start_{service_name}']
        
        # Start the process in the background
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        running_services[service_name] = process
        
        return JsonResponse({'status': 'success', 'message': f'{service_name.capitalize()} service started successfully.'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def stop_service(request):
    """
    Stops a running collector service process.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

    try:
        data = json.loads(request.body)
        service_name = data.get('service')

        if service_name not in ['syslog', 'netflow']:
            return JsonResponse({'status': 'error', 'message': 'Invalid service name'}, status=400)

        process = running_services.get(service_name)
        if process and process.poll() is None:
            process.terminate() # Send the termination signal
            del running_services[service_name]
            return JsonResponse({'status': 'success', 'message': f'{service_name.capitalize()} service stopped successfully.'})
        else:
            return JsonResponse({'status': 'error', 'message': f'{service_name.capitalize()} service is not running.'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def get_recent_syslog_entries(request):
    """
    Queries the database for the 200 most recent syslog entries.
    """
    recent_entries = SyslogEntry.objects.order_by('-received_at')[:200]
    data = [
        {
            'id': entry.id,
            'timestamp': entry.received_at.isoformat(),
            'source': entry.hostname,
            'protocol': 'SYSLOG',
            'info': entry.message
        }
        for entry in recent_entries
    ]
    return JsonResponse(data, safe=False)


def get_recent_netflow_entries(request):
    """
    Queries the database for the 200 most recent netflow entries.
    """
    recent_entries = NetflowEntry.objects.order_by('-received_at')[:200]
    data = [
        {
            'id': entry.id,
            'timestamp': entry.received_at.isoformat(),
            'source': entry.source_ip,
            'protocol': entry.protocol,
            'info': entry.info
        }
        for entry in recent_entries
    ]
    return JsonResponse(data, safe=False)
