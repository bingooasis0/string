import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NetconsoleConsumer(AsyncWebsocketConsumer):
    """
    This consumer handles the WebSocket connection for the live Netconsole stream.
    """
    GROUP_NAME = 'netconsole_stream'

    async def connect(self):
        # Join the dedicated group for Netconsole messages
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()
        print(f"Netconsole client added to {self.GROUP_NAME} group.")

    async def disconnect(self, close_code):
        # Leave the group when the client disconnects
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)
        print(f"Netconsole client removed from {self.GROUP_NAME} group.")

    async def stream_message(self, event):
        """
        Receives messages from the channel layer (sent by the collector)
        and forwards them to the client's WebSocket.
        """
        message = event['message']
        await self.send(text_data=json.dumps(message))
