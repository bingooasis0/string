from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # All API routes live in the capture app:
    path('', include('capture.urls')),
]
