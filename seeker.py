import random
import re
import time
import undetected_chromedriver as uc 
from bs4 import BeautifulSoup
from selenium import webdriver
from pyvirtualdisplay import Display
import time
from product import Product


def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = uc.Chrome(options=options, version_main=133, delay=random.randint(1, 3))

    return driver


def find_cheaper_products(url: str, cost_range: str, exact_match: bool) -> dict | str:

    display = Display(visible=False) # to comment for windows
    display.start() # to comment for windows

    driver  = get_driver()
    product = parse(url, driver)

    if type(product) is str:
        return product
    
    ret_ozon = get_pages_ozon(product, driver, cost_range, exact_match)
    ret_wb = get_pages_wb(product, driver, cost_range, exact_match)
    

    driver.quit()
    display.stop() # to comment for windows
    
    ret_dict = ret_ozon | ret_wb
    
    ret_dict = dict(sorted(ret_dict.items(), key=lambda x: int(x[1][:-1])))
      
    return ret_dict if ret_dict != {} else "Товар не найден"


def parse(url, driver) -> Product | str: 
    if re.search(r".*ozon.ru.*", url):
        return parse_page_ozon(url, driver)

    elif re.search(r".*wildberries.*", url):
        return parse_page_wildberries(url, driver)

    else:
        return "Страницу не удалось распознать"


def parse_page_ozon(url: str, driver) -> Product:
    driver.get(url=url)
    time.sleep(random.randint(1, 3))

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    if soup.find(string="Доступ ограничен") is not None:
        driver.refresh()
        soup = BeautifulSoup(driver.page_source, 'html.parser')

    name = soup.find('h1', class_=re.compile(".*tsHeadline550Medium"))
    if name is None:
        return None
    else:
        name = name.text
        name = name.replace("\n", "")
        name = name.replace("  ", "")

    specifications = soup.find_all('span', class_="tsBodyM")
    values = soup.find_all('span', class_=re.compile(".*tsBody400Small"), style="color:rgba(7, 7, 7, 1);")
    new_values = []
    for value in values:
        if value.parent.name != "div":
            values.remove(value)
            continue
        if value.parent.text not in new_values:
            new_values.append(value.parent.text)

    brand = soup.find('a', class_="tsCompactControl500Medium")
    if brand is None:
        brand = "Бренд отсутствует"
    else:
        brand = brand.text

    price_with_card = soup.find(string=re.compile("c Ozon Картой"))
    if price_with_card is None:
        price_with_card = "Цена с картой отсутствует"
        price_without_card = soup.find('span', class_=re.compile("^[a-zA-Z0-9_]{6} [a-zA-Z0-9_]{6} [a-zA-Z0-9_]{6}$")).text
        price_without_card = price_without_card.replace("\u2009", "")
    else:
        price_with_card = price_with_card.parent.parent.text
        price_with_card = price_with_card.replace("\u2009", "")

        price_without_card = soup.find(string="без Ozon Карты").parent.parent.parent.find("span").text
        price_without_card = price_without_card.replace("\u2009", "")

    specifications = dict([(x.text, y) for x, y in zip(specifications, new_values)])

    return Product(name, price_without_card, brand, price_with_card, specifications, url=url)

def parse_page_wildberries(url: str, driver) -> Product:
    driver.get(url=url)

    time.sleep(5.0)
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    name = soup.find('h1', class_=re.compile(".*product-page__title.*"))
    if name is None:
        return  None
    else:
        name = name.text

    price = soup.find('ins', class_=re.compile(".*price-block__final-price.*"))
    if price is None:
        return None
    else:
        price = price.text.replace("\xa0", "")
    
    price_with_card = soup.find('span', class_=re.compile(".*price-block__wallet-price.*"))
    if price_with_card is None:
        price_with_card = "Цена с картой отсутствует"
    else:
        price_with_card = price_with_card.text.replace("\xa0", "")

    brand = soup.find('a', class_=re.compile(".*product-page__header-brand.*"))
    if brand is None:
        brand = "Бренд отсутствует"
    else:
        brand = brand.text
    
    specifications_table = soup.find('table', class_=re.compile(".*product-params__table*"))
    if specifications_table is None:
        specifications = "Характеристики отсутствуют"
    else:
        specifications_table = specifications_table.find_all('tr')
        specifications = {}
        for row in specifications_table:
            key = row.find('th').find('span', class_='product-params__cell-decor').text.strip()
            value = row.find('td').text.strip()
            specifications[key] = value

    return Product(name, price, price_with_card=price_with_card, brand=brand, specifications=specifications, url=url)


def get_pages_ozon(product, driver, cost_range: str, exact_match: bool) -> dict:

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


def get_pages_wb(product, driver, cost_range, exact_match) -> dict:
    
    if not exact_match:
        name = product.get_cleared_name()
    else:
        name = product.name
    
    if name == "":
        return {}
    
    borders = cost_range.split()
    if cost_range == "Не установлен":
        formatted_range = ""
    else:
        borders = cost_range.split()
        formatted_range = f"&priceU={borders[0]}00%3B{borders[1]}00"
    
    driver.get(url="https://www.wildberries.ru/catalog/0/search.aspx?sort=popular&search="+name.replace(" ", "+")+formatted_range)
    time.sleep(5.0)

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    tiles = soup.find_all('div', class_=re.compile(".*product-card__wrapper*"))

    pages_with_price = {}
    for tile in tiles[:10]:
        link = tile.find('a')
        link = link['href']
        price = tile.find('ins', class_=re.compile(".*price__lower-price.*")).text
        pages_with_price[link] = price.replace("\xa0", "")

    return pages_with_price