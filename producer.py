import json
import asyncio
import logging
from typing import Dict, Union
from product import Product
from clients.find_client import AsyncFindRpcClient
from clients.ozon_client import AsyncOzonRpcClient
from clients.wb_client import AsyncWbRpcClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


async def find_cheaper_products(
    url: str, cost_range: str, exact_match: bool
) -> Union[Dict[str, str], str]:
    """Асинхронная функция поиска более дешевых товаров."""
    find_rpc = AsyncFindRpcClient()  # Инициализация протоколов клиентов
    ozon_rpc = AsyncOzonRpcClient()
    wb_rpc = AsyncWbRpcClient()

    logger.info(" [x] Requesting %s;\n %s;\n %s;", url, cost_range, exact_match)
    response = await find_rpc.call(url)
    logger.info(" [x] Got data: %s", response.decode())
    if response.decode() == "1":
        return "1", "Ошибка при получении данных о товаре"

    product = Product.from_json(response.decode())
    logger.info(" [x] Got %s", product)

    data = {
        "product": product.to_json(),
        "cost_range": cost_range,
        "exact_match": exact_match,
    }
    data = json.dumps(data)
    if isinstance(product, Product):
        ozon_task = ozon_rpc.call(data)
        wb_task = wb_rpc.call(data)
        ozon_response, wb_response = await asyncio.gather(ozon_task, wb_task)

        logger.info(" [x] Got ozon: %s", ozon_response)
        logger.info(" [x] Got wb: %s", wb_response)

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
    logger.info(" [x] Requesting just parse: %s;\n", url)
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
