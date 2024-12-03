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
    driver = uc.Chrome(options=options, version_main=130)

    return driver

def parse(url, driver):
    if "ozon" in url:
        return parse_page_ozon(url, driver)

    elif "wildberries" in url:
        return parse_page_wildberries(url, driver)

    else:
        return "Нельзя парсить эту страницу"


def parse_page_ozon(url: str, driver) -> Product:
    driver.get(url=url)
    time.sleep(1.0)

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    if soup.find(text="Доступ ограничен") is not None:
        driver.refresh()
        soup = BeautifulSoup(driver.page_source, 'html.parser')

    name = soup.find('h1', class_=re.compile(".*tsHeadline550Medium"))
    if name is None:
        name = "Название отсутствует"
        return
    else:
        name = name.text
        name = name.replace("\n", "")
        name = name.replace("  ", "")

    specifications = soup.find_all('span', class_="tsBodyM")
    # print(specifications)
    values = soup.find_all('span', class_=re.compile(".*tsBody400Small"), style="color:rgba(7, 7, 7, 1);")
    new_values = []
    for value in values:
        if value.parent.name != "div":
            values.remove(value)
            continue
        if value.parent.text not in new_values:
            new_values.append(value.parent.text)
    # print(values)
    # print(new_values)

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
        name = "Название отсутствует"
    else:
        name = name.text

    price = soup.find('ins', class_=re.compile(".*price-block__final-price.*"))
    if price is None:
        price = "Цена отсутствует"
    else:
        price = price.text

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

    return Product(name, price, brand=brand, specifications=specifications, url=url)


def get_pages_ozon(product, driver):

    name = product.name.replace(" ", "+")
    driver.get(url="https://www.ozon.ru/search/?from_global=true&sorting=price&text="+name)

    time.sleep(1.0)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    tiles = soup.find_all('div', class_=re.compile(".*sj7_23.*"))

    pages_with_price = {}
    for tile in tiles:
        link = tile.find('a')
        link = link['href']
        price = tile.find('span', class_=re.compile(".*tsHeadline500Medium.*")).text
        pages_with_price["https://www.ozon.ru" + link] = price.replace("\u2009", "")

    return pages_with_price


def get_pages_wildberries(product, driver):
    name = product.name.replace(" ", "+")
    
    driver.get(url="https://www.wildberries.ru/catalog/0/search.aspx?sort=popular&search="+name)
    time.sleep(1.0)

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    tiles = soup.find_all('a', class_=re.compile(".*product-card__wrapper*"))

    pages_with_price = {}
    for tile in tiles:
        link = tile.find('a')
        link = link['href']
        price = tile.find('ins', class_=re.compile(".*price__lower-price.*")).text
        pages_with_price["https://www.ozon.ru" + link] = price.replace("\u2009", "")

    return

if __name__ == '__main__':
    
    start = time.time()

    display = Display(visible=True, size=(800, 600)) # to comment for windows
    display.start() # to comment for windows
    driver = get_driver()

    # print(parse('https://www.ozon.ru/product/krossovki-moocie-1611940316/?advert=APMATHIne-yv7EMEHEjc5lcF5h4n_2NevDf5k0FNlcbvYR9fuFtweySm0y4G-RiMJC1Ro0tPIYXHCT1u2nDcjhVj5jGWk9exEOZWEjcCBP3_DDfuPjO2hcC0sIUj5HHQk7VNlBwar8SZ45_YwWXlIdfCYkzqn1VhXFVy&avtc=1&avte=4&avts=1731837984', driver).__str__())
    # print(parse('https://www.ozon.ru/product/krossovki-moocie-1611940316/?advert=APMATHIne-yv7EMEHEjc5lcF5h4n_2NevDf5k0FNlcbvYR9fuFtweySm0y4G-RiMJC1Ro0tPIYXHCT1u2nDcjhVj5jGWk9exEOZWEjcCBP3_DDfuPjO2hcC0sIUj5HHQk7VNlBwar8SZ45_YwWXlIdfCYkzqn1VhXFVy&avtc=1&avte=4&avts=1731837984', driver).__str__())
    # print(parse('https://www.ozon.ru/product/nabor-skovorod-polaris-easykeep-3dss-3-predmeta-co-semnoy-ruchkoy-iz-nerzhaveyushchey-stali-1652871074/?campaignId=439', driver).__str__())
    # print(parse("https://www.wildberries.ru/catalog/8352731/detail.aspx", driver).__str__())
    # print(parse("https://www.wildberries.ru/catalog/198244792/detail.aspx", driver).__str__())

    # prod = parse('https://www.ozon.ru/product/xiaomi-smartfon-xiaomi-13t-rostest-eac-12-256-gb-siniy-1196411082/?asb=Ok83xkgiCzoY%252FY%252FjiVEivt%252BBvp90WMATlqvJynJ%252FNUs%253D&asb2=NNaZkI_jcBDQwRfmhd4x-oJleJGX5oyHHf7kNFRmyJpEtzQl7SHtfvlBwY4nKeUxH211z5LWbKYTWYFXxhIj0g&avtc=1&avte=4&avts=1733047697&keywords=xiaomi+13t', driver)
    # print(prod.__str__())
    # print(get_pages_ozon(prod, driver).__str__())

    prod = parse("https://www.wildberries.ru/catalog/8352731/detail.aspx", driver)
    print(prod.__str__())
    print(get_pages_wildberries(prod, driver).__str__())


    driver.quit()
    display.stop() # to comment for windows
    print(time.time() - start)