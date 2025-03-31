import uuid
import json
import asyncio
from typing import Dict, Union
import aio_pika
from product import Product
from data import Data


async def rabbitmq_connection():
    """Создание асинхронного подключения к RabbitMQ."""
    return await aio_pika.connect_robust("amqp://guest:guest@localhost/")


class AsyncFindRpcClient:
    """Обмен данными с find consumer"""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def setup(self):
        """Настройка соединения и очередей"""
        self.connection = await rabbitmq_connection()
        self.channel = await self.connection.channel()
        self.callback_queue = await self.channel.declare_queue(exclusive=True)
        self.responses = {}
        # Используем очередь для потребления сообщений
        await self.callback_queue.consume(self.on_response)

    async def on_response(self, message: aio_pika.IncomingMessage):
        """Обработка ответа от RabbitMQ"""
        async with message.process():
            correlation_id = message.correlation_id
            self.responses[correlation_id] = message.body

    async def call(self, url: str) -> bytes:
        """Асинхронный RPC-вызов"""
        if not hasattr(self, "channel"):
            await self.setup()

        correlation_id = str(uuid.uuid4())
        self.responses[correlation_id] = None

        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=url.encode(),
                correlation_id=correlation_id,
                reply_to=self.callback_queue.name,
            ),
            routing_key="find_answer",
        )

        # Ожидание ответа
        while self.responses[correlation_id] is None:
            await asyncio.sleep(0.1)
        response = self.responses.pop(correlation_id)
        return response


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


class AsyncWbRpcClient:
    """Обмен данными с wb consumer"""

    _instance = None

    def __new__(cls):
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
        """Асинхронный RPC-вызов"""
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
            routing_key="wb_answer",
        )

        while self.responses[correlation_id] is None:
            await asyncio.sleep(0.1)
        response = self.responses.pop(correlation_id)
        return response


async def find_cheaper_products(
    url: str, cost_range: str, exact_match: bool
) -> Union[Dict[str, str], str]:
    """Асинхронная функция поиска более дешевых товаров."""
    find_rpc = AsyncFindRpcClient()
    ozon_rpc = AsyncOzonRpcClient()
    wb_rpc = AsyncWbRpcClient()

    print(f" [x] Requesting {url};\n {cost_range};\n {exact_match};\n")
    response = await find_rpc.call(url)
    product = Product.from_json(response.decode())
    print(f" [.] Got {product}")

    data = Data(product, cost_range, exact_match)
    print(f" [.] Data prepared: {data}")

    if isinstance(product, Product):
        ozon_task = ozon_rpc.call(data.to_json())
        wb_task = wb_rpc.call(data.to_json())
        ozon_response, wb_response = await asyncio.gather(ozon_task, wb_task)

        print(f" [.] Got ozon {ozon_response}")
        print(f" [.] Got wb {wb_response}")

        ret_dict = json.loads(ozon_response) | json.loads(wb_response)
        ret_dict = dict(sorted(ret_dict.items(), key=lambda x: int(x[1][:-1])))
        return product.name, ret_dict if ret_dict else "Товар не найден"
    return "Ошибка при получении данных о товаре"


async def get_prod(url):
    """
    Получение данных о товаре
    без поиска похожих товаров
    """
    find_rpc = AsyncFindRpcClient()
    print(f" [x] Requesting just parse: {url};\n")
    response = await find_rpc.call(url)
    product = Product.from_json(response.decode())
    return product


async def main():
    """Отладочны запуск"""
    result = await find_cheaper_products(
        "https://www.ozon.ru/product/nabor-nozhey-\
        kuhonnyh-samura-golf-sg-0240-nabor-ih-4-h-nozhey-1576657502/?campaignId=527",
        "1000 3000",
        True,
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
