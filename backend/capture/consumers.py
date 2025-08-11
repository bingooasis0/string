from channels.generic.websocket import AsyncWebsocketConsumer

# each consumer joins a group; your management commands group_send() into these names

class BaseGroupConsumer(AsyncWebsocketConsumer):
    group_name = None  # override

    async def connect(self):
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # event handler called by group_send({"type": "<name>.message", "text": ...})
    async def forward(self, event):
        await self.send(text_data=event["text"])

class SyslogConsumer(BaseGroupConsumer):
    group_name = "syslog"
    async def syslog_message(self, event):  # type name must match
        await self.forward(event)

class NetflowConsumer(BaseGroupConsumer):
    group_name = "netflow"
    async def netflow_message(self, event):
        await self.forward(event)

class NetconsoleConsumer(BaseGroupConsumer):
    group_name = "netconsole"
    async def netconsole_message(self, event):
        await self.forward(event)

class StatusConsumer(BaseGroupConsumer):
    group_name = "status"
    async def status_message(self, event):
        await self.forward(event)

class SnmpConsumer(BaseGroupConsumer):
    group_name = "snmp"
    async def snmp_message(self, event):
        await self.forward(event)
