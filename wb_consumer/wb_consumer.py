import asyncio
import json
import random
import re
import time
import logging
from http.client import RemoteDisconnected
from urllib3.exceptions import MaxRetryError, NewConnectionError
import pika
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from pyvirtualdisplay import Display
from product import Product

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

class WbConsumer:
    def __init__(self):
        self.driver = None
        self.port = 9223
        self.max_init_retries = 3
        self._ensure_driver()
        self._setup_connection()

    def _setup_connection(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue="wb_answer")
        self.channel.basic_qos(prefetch_count=1)
        logger.info("Connected to RabbitMQ and queue declared")

    def _init_driver(self):
        for attempt in range(self.max_init_retries):
            try:
                options = webdriver.ChromeOptions()
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument("--user-agent=Mozilla/5.0 ...")
                options.add_argument(f"--remote-debugging-port={self.port}")
                options.add_argument("--headless")
                options.add_argument("--disable-gpu")
                driver = uc.Chrome(options=options, version_main=135, delay=random.randint(1, 3))
                logger.info("Driver initialized successfully")
                return driver
            except Exception as e:
                logger.error("Driver init failed (attempt %s/%s): %s", attempt+1, self.max_init_retries, e)
                if attempt < self.max_init_retries - 1:
                    time.sleep(5)
                else:
                    raise

    def _ensure_driver(self):
        if self.driver is None or not self._is_driver_alive():
            if self.driver:
                self.driver.quit()
            self.driver = self._init_driver()

    def _is_driver_alive(self):
        try:
            _ = self.driver.current_url
            return True
        except (WebDriverException, MaxRetryError, NewConnectionError, RemoteDisconnected):
            return False

    def get_pages_wb(self, product: Product, cost_range: str, exact_match: bool) -> dict:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self._ensure_driver()
                name = product.name if exact_match else product.get_cleared_name()
                if name == "":
                    return {}
                formatted_range = ""
                if cost_range != "Не установлен":
                    borders = cost_range.split()
                    formatted_range = f"&priceU={borders[0]}00%3B{borders[1]}00"

                url = f"https://www.wildberries.ru/catalog/0/search.aspx?sort=popular&search={name.replace(' ', '+')}{formatted_range}"
                logger.info("Fetching: %s", url)
                self.driver.get(url)
                time.sleep(random.uniform(4, 7))

                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                tiles = soup.find_all("div", class_=re.compile(".*product-card__wrapper*"))
                if not tiles:
                    return {}

                pages_with_price = {}
                for tile in tiles[:10]:
                    link = tile.find("a")
                    if not link or "href" not in link.attrs:
                        continue
                    href = link["href"]
                    price = tile.find("ins", class_=re.compile(".*price__lower-price.*"))
                    if not price:
                        continue
                    price_text = price.text.replace("\xa0", "").replace("₽", "")
                    try:
                        price_int = int(price_text)
                    except ValueError:
                        continue

                    if cost_range == "Не установлен":
                        pages_with_price[href] = f"{price_int} ₽"
                    else:
                        bounds = list(map(int, cost_range.split()))
                        if bounds[0] <= price_int <= bounds[1]:
                            pages_with_price[href] = f"{price_int} ₽"
                return pages_with_price
            except Exception as e:
                logger.error("Error while parsing (attempt %s/%s): %s", attempt+1, max_retries, e)
                if attempt < max_retries - 1:
                    time.sleep(2)
                    self.driver.quit()
                    self.driver = self._init_driver()
                else:
                    return {}

    def _on_request(self, ch, method, props, body):
        try:
            data = json.loads(body)
            logger.info("Get data:  %s", data)
            print(data["product"])
            product = Product.from_json(data["product"])
            cost_range = data.get("cost_range", "Не установлен")
            exact_match = data.get("exact_match", False)
            print("extraction success")

            response = self.get_pages_wb(product, cost_range, exact_match)
            response_json = json.dumps(response)

            ch.basic_publish(
                exchange="",
                routing_key=props.reply_to,
                properties=pika.BasicProperties(
                    correlation_id=props.correlation_id
                ),
                body=response_json,
            )
            logger.info("Sent response for correlation_id %s", props.correlation_id)
        except Exception as e:
            logger.error("Failed to process message: %s", e)
            ch.basic_publish(
                exchange="",
                routing_key=props.reply_to,
                properties=pika.BasicProperties(
                    correlation_id=props.correlation_id
                ),
                body=json.dumps({}),
            )
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def run(self):
        logger.info("Starting WB consumer with pika")
        self.channel.basic_consume(queue="wb_answer", on_message_callback=self._on_request)
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Gracefully stopping...")
            self.channel.stop_consuming()
            if self.driver:
                self.driver.quit()
            self.connection.close()


if __name__ == "__main__":
    # Инициализация виртуального дисплея (закомментировать для Windows)
    display = Display(visible=False)
    display.start()
    try:
        consumer = WbConsumer()
        asyncio.run(consumer.run())
    except KeyboardInterrupt:
        if display:
            display.stop()
        if consumer.driver:
            consumer.driver.quit()
        logger.info("Interrupted")
