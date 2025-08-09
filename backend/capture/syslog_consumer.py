import json
from channels.generic.websocket import AsyncWebsocketConsumer

class PacketConsumer(AsyncWebsocketConsumer):
    # The name of the group that this consumer will join.
    # All consumers in this group will receive messages sent to the group.
    GROUP_NAME = 'syslog_stream'

    async def connect(self):
        # Join the group
        await self.channel_layer.group_add(
            self.GROUP_NAME,
            self.channel_name
        )
        await self.accept()
        print(f"Added to {self.GROUP_NAME} group.")

    async def disconnect(self, close_code):
        # Leave the group
        await self.channel_layer.group_discard(
            self.GROUP_NAME,
            self.channel_name
        )
        print(f"Removed from {self.GROUP_NAME} group.")

    # This method is the handler for messages sent to the group.
    # The name of the method corresponds to the "type" of the message.
    async def stream_message(self, event):
        message = event['message']

        # Send the message to the WebSocket client
        await self.send(text_data=json.dumps(message))