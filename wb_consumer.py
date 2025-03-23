import aio_pika
import asyncio
import json
import random
import re
import time
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from pyvirtualdisplay import Display
from product import Product
from data import Data
import logging
from urllib3.exceptions import MaxRetryError, NewConnectionError
from http.client import RemoteDisconnected

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Инициализация виртуального дисплея (закомментировать для Windows)
try:
    display = Display(visible=False)
    display.start()
except ImportError:
    display = None

class WbConsumer:
    def __init__(self):
        self.driver = None
        self.port = 9223
        self.max_init_retries = 3
        self._ensure_driver()

    def _init_driver(self):
        """Инициализация драйвера с уникальным портом и повторными попытками."""
        for attempt in range(self.max_init_retries):
            try:
                options = webdriver.ChromeOptions()
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument(
                    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                )
                options.add_argument(f"--remote-debugging-port={self.port}")
                options.add_argument("--headless")
                options.add_argument("--disable-gpu")  # Уменьшение нагрузки
                driver = uc.Chrome(options=options, version_main=133, delay=random.randint(1, 3))
                logger.info(f"WB driver initialized successfully on port {self.port}")
                return driver
            except Exception as e:
                logger.error(f"Failed to initialize WB driver on port {self.port}, attempt {attempt + 1}/{self.max_init_retries}: {e}")
                if attempt < self.max_init_retries - 1:
                    time.sleep(5)  # Пауза перед повторной попыткой
                else:
                    logger.critical("Max retries exceeded for driver initialization. Exiting.")
                    raise

    def _ensure_driver(self):
        """Проверка и перезапуск драйвера, если он не работает."""
        if self.driver is None or not self._is_driver_alive():
            if self.driver:
                self.driver.quit()
            self.driver = self._init_driver()

    def _is_driver_alive(self):
        """Проверка, работает ли драйвер."""
        try:
            self.driver.current_url
            return True
        except (WebDriverException, MaxRetryError, NewConnectionError, RemoteDisconnected):
            logger.warning("Driver is not responding")
            return False

    def get_pages_wb(self, product: Product, cost_range: str, exact_match: bool) -> dict:
        """Синхронная функция парсинга Wildberries с переиспользуемым драйвером."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self._ensure_driver()
                if not exact_match:
                    name = product.get_cleared_name()
                else:
                    name = product.name

                if name == "":
                    logger.info("Product name is empty")
                    return {}

                if cost_range == "Не установлен":
                    formatted_range = ""
                else:
                    borders = cost_range.split()
                    formatted_range = f"&priceU={borders[0]}00%3B{borders[1]}00"

                url = f"https://www.wildberries.ru/catalog/0/search.aspx?sort=popular&search={name.replace(' ', '+')}{formatted_range}"
                logger.info(f"Fetching URL (attempt {attempt + 1}/{max_retries}): {url}")
                self.driver.get(url)
                time.sleep(random.uniform(3, 6))  # Увеличенное время ожидания

                page_source = self.driver.page_source
                if not page_source or len(page_source) < 100:
                    logger.warning(f"Page source is empty or too short (length: {len(page_source)})")
                    raise WebDriverException("Empty page source")

                logger.debug(f"Page source length: {len(page_source)}")
                soup = BeautifulSoup(page_source, 'html.parser')
                tiles = soup.find_all('div', class_=re.compile(".*product-card__wrapper*"))
                if not tiles:
                    logger.warning("No tiles found on page")
                    return {}

                pages_with_price = {}
                for tile in tiles[:10]:
                    link = tile.find('a')
                    if link and 'href' in link.attrs:
                        link = link['href']
                        price = tile.find('ins', class_=re.compile(".*price__lower-price.*"))
                        if price:
                            if cost_range == "Не установлен":
                                pages_with_price[link] = price.text.replace("\xa0", "")
                                continue
                            cost_as_list = list(map(int, cost_range.split()))
                            print(cost_as_list)
                            if int(price.text.replace("\xa0", "")[:-1]) in range(
                                cost_as_list[0], cost_as_list[1]
                            ):
                                pages_with_price[link] = price.text.replace("\xa0", "")
                        else:
                            logger.debug(f"No price found for tile: {tile}")

                logger.info(f"Found {len(pages_with_price)} items")
                return pages_with_price

            except (MaxRetryError, NewConnectionError, WebDriverException, RemoteDisconnected) as e:
                logger.error(f"WebDriver connection error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    logger.info("Retrying...")
                    self.driver.quit()
                    self.driver = self._init_driver()
                    time.sleep(2)
                else:
                    logger.error("Max retries exceeded. Returning empty result.")
                    return {}
            except Exception as e:
                logger.error(f"Unexpected error during parsing on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    logger.info("Retrying due to unexpected error...")
                    self.driver.quit()
                    self.driver = self._init_driver()
                    time.sleep(2)
                else:
                    logger.error("Max retries exceeded for unexpected error. Returning empty result.")
                    return {}

    async def process_message(self, message: aio_pika.IncomingMessage, channel: aio_pika.Channel):
        """Обработка сообщения асинхронно."""
        async with message.process():
            try:
                data_json = message.body.decode()
                logger.info(f"Received data: {data_json}")
                product, cost_range, exact_match = Data.from_json(data_json)

                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, self.get_pages_wb, product, cost_range, exact_match
                )

                await channel.default_exchange.publish(
                    aio_pika.Message(
                        body=json.dumps(response).encode(),
                        correlation_id=message.correlation_id,
                        reply_to=message.reply_to
                    ),
                    routing_key=message.reply_to
                )
                logger.info(f"Sent response: {response}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await channel.default_exchange.publish(
                    aio_pika.Message(
                        body=json.dumps({}).encode(),
                        correlation_id=message.correlation_id,
                        reply_to=message.reply_to
                    ),
                    routing_key=message.reply_to
                )

    async def run(self):
        """Запуск консьюмера."""
        while True:
            try:
                connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
                async with connection:
                    channel = await connection.channel()
                    queue = await channel.declare_queue("wb_answer")
                    await channel.set_qos(prefetch_count=1)

                    logger.info("Awaiting RPC requests for wb_answer")
                    await queue.consume(lambda msg: self.process_message(msg, channel))
                    await asyncio.Future()
            except Exception as e:
                logger.error(f"Wb_consumer crashed: {e}. Reconnecting in 5 seconds...")
                await asyncio.sleep(5)
            finally:
                if self.driver:
                    self.driver.quit()

if __name__ == "__main__":
    try:
        consumer = WbConsumer()
        asyncio.run(consumer.run())
    except KeyboardInterrupt:
        if display:
            display.stop()
        if consumer.driver:
            consumer.driver.quit()
        logger.info("Interrupted")
