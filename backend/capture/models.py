from django.db import models

class SyslogEntry(models.Model):
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    hostname = models.CharField(max_length=255)
    app_name = models.CharField(max_length=255, null=True, blank=True)
    message = models.TextField()
    raw_message = models.TextField()

    def __str__(self):
        return f"{self.received_at.strftime('%Y-%m-%d %H:%M:%S')} - {self.hostname} - {self.message[:50]}"

    class Meta:
        ordering = ['-received_at']
        verbose_name_plural = "Syslog Entries"

class NetflowEntry(models.Model):
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    source_ip = models.CharField(max_length=255)
    destination_ip = models.CharField(max_length=255)
    protocol = models.CharField(max_length=50)
    info = models.TextField()

    def __str__(self):
        return f"{self.received_at.strftime('%Y-%m-%d %H:%M:%S')} - {self.source_ip} -> {self.destination_ip}"

    class Meta:
        ordering = ['-received_at']
        verbose_name_plural = "Netflow Entries"

class NetconsoleEntry(models.Model):
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    source_ip = models.CharField(max_length=255)
    message = models.TextField()
    raw_message = models.TextField()

    def __str__(self):
        return f"{self.received_at.strftime('%Y-%m-%d %H:%M:%S')} - {self.source_ip} - {self.message[:50]}"

    class Meta:
        ordering = ['-received_at']
        verbose_name_plural = "Netconsole Entries"
