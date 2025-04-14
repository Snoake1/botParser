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

class OzonConsumer:
    """consumer для обработки поиска похожих товаров на страницах озон"""
    
    def __init__(self):
        self.max_retries = 3
        self.driver = None
        self.port = 9222
        self._ensure_driver()
        self.connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue="ozon_answer")
        logger.info("Connected to RabbitMQ")

    def _init_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        # options.add_argument(
        #     "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)\
        #         AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        # )
        # options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)\
        # AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Safari/605.1.15")
        options.add_argument("user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 6_0 like Mac OS X)\
            AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25")
        try:
            driver = uc.Chrome(
                options=options, version_main=135, delay=random.randint(1, 3)
            )
            logger.info("Ozon driver initialized successfully on port %s", self.port)
            return driver
        except Exception as e:
            logger.error("Failed to initialize Ozon driver on port %s: %s", self.port, e)
            return None

    def _ensure_driver(self):
        if self.driver is None or not self._is_driver_alive():
            if self.driver:
                self.driver.quit()
            self.driver = self._init_driver()

    def _is_driver_alive(self):
        try:
            self.driver.current_url
            return True
        except (
            WebDriverException,
            MaxRetryError,
            NewConnectionError,
            RemoteDisconnected,
        ):
            logger.warning("Driver is not responding")
            return False

    def get_pages_ozon(self, product, cost_range: str, exact_match: bool) -> dict:
        for attempt in range(self.max_retries):
            try:
                self._ensure_driver()
                name = product.name if exact_match else product.get_cleared_name()

                formatted_range = ""
                if cost_range != "Не установлен":
                    borders = cost_range.split()
                    formatted_range = f"currency_price={borders[0]}.000%3B{borders[1]}.000&"

                url = f"https://www.ozon.ru/search/?{formatted_range}from_global=true&sorting=score&text={name.replace(' ', '+')}"
                logger.info("Fetching URL (attempt %s/%s): %s", attempt + 1, self.max_retries, url)

                self.driver.get(url)
                time.sleep(random.uniform(3, 6))

                page_source = self.driver.page_source
                if not page_source or len(page_source) < 100:
                    logger.warning("Page source is empty or too short (length: %s)", len(page_source))
                    raise WebDriverException("Empty page source")

                soup = BeautifulSoup(page_source, "html.parser")
                if soup.find(string="Доступ ограничен") is not None:
                    logger.warning("Access restricted, refreshing page")
                    self.driver.refresh()
                    time.sleep(2)
                    soup = BeautifulSoup(self.driver.page_source, "html.parser")

                if soup.find("div", class_="aa0g_33") is not None:
                    logger.info("No results found on page")
                    return {}

                tiles = soup.find_all("div", class_=re.compile(".*tile-root.*"))
                if not tiles:
                    logger.warning("No tiles found on page")
                    return {}

                pages_with_price = {}
                for tile in tiles:
                    link = tile.find("a")
                    if link and "href" in link.attrs:
                        price = tile.find("span", class_=re.compile(".*tsHeadline500Medium.*"))
                        if price:
                            pages_with_price["https://www.ozon.ru" + link["href"]] = price.text.replace("\u2009", "")
                        else:
                            logger.debug("No price found for tile: %s", tile)

                logger.info("Found %s items", len(pages_with_price))
                return pages_with_price

            except (
                MaxRetryError,
                NewConnectionError,
                WebDriverException,
                RemoteDisconnected,
            ) as e:
                logger.error("WebDriver connection error on attempt %s: %s", attempt, e)
                if attempt < self.max_retries - 1:
                    logger.info("Retrying...")
                    self.driver.quit()
                    self.driver = self._init_driver()
                    time.sleep(1)
                else:
                    logger.error("Max retries exceeded. Returning empty result.")
                    return {}
            except Exception as e:
                logger.error("Unexpected error during parsing on attempt %s: %s", attempt, e)
                if attempt < self.max_retries - 1:
                    logger.info("Retrying due to unexpected error...")
                    self.driver.quit()
                    self.driver = self._init_driver()
                    time.sleep(1)
                else:
                    logger.error("Max retries exceeded for unexpected error. Returning empty result.")
                    return {}

    def on_message(self, ch, method, properties, body):
        try:
            data_json = json.loads(body)
            logger.info("Received data: %s", data_json)
            product = Product.from_json(data_json["product"])
            cost_range, exact_match  = data_json["cost_range"], data_json["exact_match"]

            response = self.get_pages_ozon(product, cost_range, exact_match)

            ch.basic_publish(
                exchange="",
                routing_key=properties.reply_to,
                properties=pika.BasicProperties(
                    correlation_id=properties.correlation_id
                ),
                body=json.dumps(response).encode()
            )
            logger.info("Sent response with correlation_id %s", properties.correlation_id)
        except Exception as e:
            logger.error("Error processing message: %s", e)
            ch.basic_publish(
                exchange="",
                routing_key=properties.reply_to,
                properties=pika.BasicProperties(
                    correlation_id=properties.correlation_id
                ),
                body=json.dumps({}).encode()
            )

    def run(self):
        try:
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(queue="ozon_answer", on_message_callback=self.on_message, auto_ack=True)
            logger.info("Awaiting RPC requests for ozon_answer")
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received. Shutting down...")
        finally:
            if self.driver:
                self.driver.quit()
            self.connection.close()


if __name__ == "__main__":
    display = Display(visible=False)
    display.start()
    try:
        consumer = OzonConsumer()
        consumer.run()
    except KeyboardInterrupt:
        if display:
            display.stop()
        if consumer.driver:
            consumer.driver.quit()
        logger.info("Interrupted")
