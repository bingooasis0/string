# C:\Users\colby\Desktop\String\backend\capture\status_consumer.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class StatusConsumer(AsyncWebsocketConsumer):
    GROUP_NAME = 'service_status'
    async def connect(self):
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)
    async def status_update(self, event): # Note the handler name matches the 'type'
        await self.send(text_data=json.dumps(event['message']))