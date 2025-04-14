import uuid
import asyncio
import aio_pika
from clients.find_client import rabbitmq_connection

class AsyncOzonRpcClient:
    """Обмен данными с ozon consumer"""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def setup(self):
        self.connection = await rabbitmq_connection()
        self.channel = await self.connection.channel()
        self.callback_queue = await self.channel.declare_queue(exclusive=True)
        self.responses = {}
        await self.callback_queue.consume(self.on_response)

    async def on_response(self, message: aio_pika.IncomingMessage):
        """Обработка ответа от RabbitMQ"""
        async with message.process():
            correlation_id = message.correlation_id
            self.responses[correlation_id] = message.body

    async def call(self, data: str) -> bytes:
        """Асинхронный RPC-вызов."""
        if not hasattr(self, "channel"):
            await self.setup()

        correlation_id = str(uuid.uuid4())
        self.responses[correlation_id] = None

        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=data.encode(),
                correlation_id=correlation_id,
                reply_to=self.callback_queue.name,
            ),
            routing_key="ozon_answer",
        )

        while self.responses[correlation_id] is None:
            await asyncio.sleep(0.1)
        response = self.responses.pop(correlation_id)
        return response