import random
import re
import time
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium import webdriver
from pyvirtualdisplay import Display
import pika
from product import Product


def get_driver():
    """Получние драйвера"""
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # options.add_argument(
    #    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)\
    #        AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.165 Safari/537.36")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)\
        AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Safari/605.1.15")

    driver = uc.Chrome(options=options, version_main=135, delay=random.randint(1, 3))
    # driver.get("https://www.browserscan.net/ru/bot-detection")
    # time.sleep(10)
    # driver.get("https://nowsecure.nl")
    # time.sleep(10)
    return driver


def parse(url, driver) -> Product | str:
    """Выбор парсера"""
    if re.search(r".*ozon.ru.*", url):
        return parse_page_ozon(url, driver)

    if re.search(r".*wildberries.*", url):
        return parse_page_wildberries(url, driver)

    return "Страницу не удалось распознать"


def parse_page_ozon(url: str, driver) -> Product:
    """Парсинг страницы ozon"""
    driver.get(url=url)
    time.sleep(random.randint(1, 3))

    soup = BeautifulSoup(driver.page_source, "html.parser")

    if soup.find(string="Доступ ограничен") is not None:
        time.sleep(10)
        driver.refresh()
        soup = BeautifulSoup(driver.page_source, "html.parser")

    name = soup.find("h1", class_=re.compile(".*tsHeadline550Medium"))
    if name is None:
        return None

    name = name.text
    name = name.replace("\n", "")
    name = name.replace("  ", "")

    specifications = soup.find_all("span", class_="tsBodyM")
    values = soup.find_all(
        "span", class_=re.compile(".*tsBody400Small"), style="color:rgba(7, 7, 7, 1);"
    )
    new_values = []
    for value in values:
        if value.parent.name != "div":
            values.remove(value)
            continue
        if value.parent.text not in new_values:
            new_values.append(value.parent.text)

    brand = soup.find("a", class_="tsCompactControl500Medium")
    if brand is None:
        brand = "Бренд отсутствует"
    else:
        brand = brand.text

    price_with_card = soup.find(string=re.compile("c Ozon Картой"))
    if price_with_card is None:
        price_with_card = "Цена с картой отсутствует"
        price_without_card = soup.find(
            "span",
            class_=re.compile("^[a-zA-Z0-9_]{6} [a-zA-Z0-9_]{6} [a-zA-Z0-9_]{6}$"),
        ).text
        price_without_card = price_without_card.replace("\u2009", "")
        price_without_card = float(re.findall(r"\b\d+\b", price_without_card)[0])
    else:
        price_with_card = price_with_card.parent.parent.text
        price_with_card = price_with_card.replace("\u2009", "")
        price_with_card = float(re.findall(r"\b\d+\b", price_with_card)[0])

        price_without_card = (
            soup.find(string="без Ozon Карты").parent.parent.parent.find("span").text
        )
        price_without_card = price_without_card.replace("\u2009", "")
        price_without_card = float(re.findall(r"\b\d+\b", price_without_card)[0])

    specifications = dict((x.text, y) for x, y in zip(specifications, new_values))

    return Product(
        name, price_without_card, brand, price_with_card, specifications, url=url
    )


def parse_page_wildberries(url: str, driver) -> Product:
    """Парсинг страницы wb"""
    driver.get(url=url)
    time.sleep(random.randint(3, 5))
    soup = BeautifulSoup(driver.page_source, "html.parser")

    name = soup.find("h1", class_=re.compile(".*product-page__title.*"))
    if name is None:
        return None
    name = name.text

    price = soup.find("ins", class_=re.compile(".*price-block__final-price.*"))
    if price is None:
        return None
    price = price.text.replace("\xa0", "")
    price = float(re.findall(r"\b\d+\b", price)[0])

    price_with_card = soup.find(
        "span", class_=re.compile(".*price-block__wallet-price.*")
    )
    if price_with_card is None:
        price_with_card = "Цена с картой отсутствует"
    else:
        price_with_card = price_with_card.text.replace("\xa0", "")
        price_with_card = float(re.findall(r"\b\d+\b", price_with_card)[0])

    brand = soup.find("a", class_=re.compile(".*product-page__header-brand.*"))
    if brand is None:
        brand = "Бренд отсутствует"
    else:
        brand = brand.text

    specifications_table = soup.find(
        "table", class_=re.compile(".*product-params__table*")
    )
    if specifications_table is None:
        specifications = "Характеристики отсутствуют"
    else:
        specifications_table = specifications_table.find_all("tr")
        specifications = {}
        for row in specifications_table:
            key = (
                row.find("th")
                .find("span", class_="product-params__cell-decor")
                .text.strip()
            )
            value = row.find("td").text.strip()
            specifications[key] = value

    return Product(
        name,
        price,
        price_with_card=price_with_card,
        brand=brand,
        specifications=specifications,
        url=url,
    )


def get_product_info(url: str, driver) -> Product | str:
    """Получение информации о товаре"""
    product = parse(url, driver)
    if isinstance(product, str):
        return product
    return product.to_json() if product != None else None


def on_request(ch, method, props, body):
    """Обработчки запроса"""
    url = body.decode()
    driver = get_driver()

    print(f" [.] get url: ({url})")
    response = get_product_info(url, driver)
    if not response:
        response = 1
        
    ch.basic_publish(
        exchange="",
        routing_key=props.reply_to,
        properties=pika.BasicProperties(correlation_id=props.correlation_id),
        body=str(response),
    )
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))

    channel = connection.channel()

    channel.queue_declare(queue="find_answer")

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue="find_answer", on_message_callback=on_request)

    print(" [x] Awaiting RPC requests")
    channel.start_consuming()


if __name__ == "__main__":
    try:
        display = Display(visible=False)  # to comment for windows
        display.start()  # to comment for windows
        main()
    except KeyboardInterrupt:
        display.stop()  # to comment for windows
        print("Interrupted")
