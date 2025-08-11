from django.db import models

class SyslogEntry(models.Model):
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    hostname = models.CharField(max_length=255, db_index=True)
    app_name = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    facility = models.IntegerField(null=True, blank=True, db_index=True)
    severity = models.IntegerField(null=True, blank=True, db_index=True)
    message = models.TextField()
    raw_message = models.TextField()

class NetflowEntry(models.Model):
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    exporter_ip = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    observation_domain_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    template_id = models.IntegerField(null=True, blank=True, db_index=True)
    flow_start = models.DateTimeField(null=True, blank=True, db_index=True)
    flow_end = models.DateTimeField(null=True, blank=True, db_index=True)
    src_ip = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    dst_ip = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    src_port = models.IntegerField(null=True, blank=True, db_index=True)
    dst_port = models.IntegerField(null=True, blank=True, db_index=True)
    protocol = models.IntegerField(null=True, blank=True, db_index=True)
    tos = models.IntegerField(null=True, blank=True)
    tcp_flags = models.IntegerField(null=True, blank=True)
    packets = models.BigIntegerField(null=True, blank=True)
    bytes = models.BigIntegerField(null=True, blank=True)
    input_if = models.IntegerField(null=True, blank=True)
    output_if = models.IntegerField(null=True, blank=True)
    vlan_id_in = models.IntegerField(null=True, blank=True)
    vlan_id_out = models.IntegerField(null=True, blank=True)
    next_hop = models.GenericIPAddressField(null=True, blank=True)
    src_as = models.IntegerField(null=True, blank=True)
    dst_as = models.IntegerField(null=True, blank=True)
    info = models.TextField(null=True, blank=True)
    raw = models.BinaryField(null=True, blank=True)

class NetconsoleEntry(models.Model):
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    source_ip = models.GenericIPAddressField(db_index=True)
    message = models.TextField()
    raw_message = models.TextField()

class SnmpTrap(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    source_ip = models.GenericIPAddressField(null=True, blank=True, db_index=True)

    version = models.CharField(max_length=8, db_index=True)  # v1/v2c/v3
    community = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    user = models.CharField(max_length=64, null=True, blank=True, db_index=True)

    context_engine_id = models.CharField(max_length=128, null=True, blank=True)
    context_name = models.CharField(max_length=128, null=True, blank=True)

    trap_oid = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    enterprise_oid = models.CharField(max_length=255, null=True, blank=True)
    generic_trap = models.IntegerField(null=True, blank=True)
    specific_trap = models.IntegerField(null=True, blank=True)

    uptime = models.BigIntegerField(null=True, blank=True)  # timeticks
    severity = models.CharField(max_length=32, null=True, blank=True, db_index=True)

    security_level = models.CharField(max_length=16, null=True, blank=True)       # noAuthNoPriv/authNoPriv/authPriv
    auth_protocol = models.CharField(max_length=16, null=True, blank=True)        # MD5/SHA/...
    priv_protocol = models.CharField(max_length=16, null=True, blank=True)        # DES/AES128/...

    engine_boots = models.IntegerField(null=True, blank=True)
    engine_time = models.IntegerField(null=True, blank=True)

    var_binds = models.JSONField(null=True, blank=True)
    info = models.TextField(blank=True)

    class Meta:
        ordering = ('-id',)