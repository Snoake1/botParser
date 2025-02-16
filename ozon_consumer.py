import json
import random
import re
import time
import undetected_chromedriver as uc 
from bs4 import BeautifulSoup
from selenium import webdriver
from pyvirtualdisplay import Display
import time
from product import Product
from data import Data
import pika


def get_pages_ozon(product: Product, cost_range: str, exact_match: bool, driver) -> dict:

    if not exact_match:
        name = product.get_cleared_name()  
    else:  
        name = product.name
    
    if cost_range == "Не установлен":
        formatted_range = ""
    else:
        borders = cost_range.split()
        formatted_range = f"currency_price={borders[0]}.000%3B{borders[1]}.000&"
    driver.get(url=f"https://www.ozon.ru/search/?{formatted_range}from_global=true&sorting=score&text="+name.replace(" ", "+"))

    time.sleep(1.0)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    if soup.find(string="Доступ ограничен") is not None:
        driver.refresh()
        soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    if soup.find('div', class_="aa0g_33") is not None:
        return {}

    tiles = soup.find_all('div', class_=re.compile(".*tile-root.*"))

    pages_with_price = {}
    for tile in tiles:
        link = tile.find('a')
        link = link['href']
        price = tile.find('span', class_=re.compile(".*tsHeadline500Medium.*")).text
        pages_with_price["https://www.ozon.ru" + link] = price.replace("\u2009", "")

    return pages_with_price


def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = uc.Chrome(options=options, version_main=133, delay=random.randint(1, 3))

    return driver

def on_request(ch, method, props, body):
    data = body
    driver = get_driver()

    print(f" [.] get url: ({data})")
    product, cost_range, exact_match = Data.from_json(data)
    response = get_pages_ozon(product, cost_range, exact_match, driver)

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                         props.correlation_id),
                     body=json.dumps(response))
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))

    channel = connection.channel()

    channel.queue_declare(queue='ozon_answer')
    
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='ozon_answer', on_message_callback=on_request)

    print(" [x] Awaiting RPC requests")
    channel.start_consuming()
    

if __name__ == '__main__':
    try:
        display = Display(visible=True) # to comment for windows
        display.start() # to comment for windows
        main()
    except KeyboardInterrupt:
        display.stop() # to comment for windows
        print('Interrupted')