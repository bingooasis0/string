import json
from channels.generic.websocket import AsyncWebsocketConsumer

class StatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('service_status', self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('service_status', self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        return

    async def status_update(self, event):
        await self.send(text_data=json.dumps(event['message']))
