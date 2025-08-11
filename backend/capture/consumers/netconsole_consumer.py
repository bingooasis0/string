import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NetconsoleConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('netconsole_stream', self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('netconsole_stream', self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        return

    async def stream_message(self, event):
        await self.send(text_data=json.dumps(event['message']))

    async def status_update(self, event):
        await self.send(text_data=json.dumps({'status': event['message']}))
