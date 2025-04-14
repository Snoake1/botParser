import json
import asyncio
from typing import Dict, Union
from product import Product
from clients.find_client import AsyncFindRpcClient
from clients.ozon_client import AsyncOzonRpcClient
from clients.wb_client import AsyncWbRpcClient


async def find_cheaper_products(
    url: str, cost_range: str, exact_match: bool
) -> Union[Dict[str, str], str]:
    """Асинхронная функция поиска более дешевых товаров."""
    find_rpc = AsyncFindRpcClient()
    ozon_rpc = AsyncOzonRpcClient()
    wb_rpc = AsyncWbRpcClient()

    print(f" [x] Requesting {url};\n {cost_range};\n {exact_match};\n")
    response = await find_rpc.call(url)
    print(response.decode())
    if response.decode() == "1":
        return "1", "Ошибка при получении данных о товаре"
        
    product = Product.from_json(response.decode())
    print(f" [.] Got {product}")
    
    data = {
        "product": product.to_json(),
        "cost_range": cost_range,
        "exact_match": exact_match
    }
    data = json.dumps(data)
    if isinstance(product, Product):
        ozon_task = ozon_rpc.call(data)
        wb_task = wb_rpc.call(data)
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
