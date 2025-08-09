# C:\Users\colby\Desktop\String\backend\capture\netflow_consumer.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NetflowConsumer(AsyncWebsocketConsumer):
    GROUP_NAME = 'netflow_stream'

    async def connect(self):
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()
        print(f"Netflow client added to {self.GROUP_NAME} group.")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)
        print(f"Netflow client removed from {self.GROUP_NAME} group.")

    async def stream_message(self, event):
        await self.send(text_data=json.dumps(event['message']))