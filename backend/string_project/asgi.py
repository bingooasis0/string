# C:\Users\colby\Desktop\String\backend\string_project\asgi.py

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import capture.routing  # This is the only custom import needed here

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'string_project.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            capture.routing.websocket_urlpatterns
        )
    ),
})