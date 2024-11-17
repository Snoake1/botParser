import re
import time
import undetected_chromedriver as uc 
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC 
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from fake_useragent import UserAgent
from pyvirtualdisplay import Display


def parse_page_ozon(url):
    future_class = {}
    display = Display(visible=False, size=(800, 600)) # to comment for windows
    display.start() # to comment for windows
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    driver = uc.Chrome(options=options, version_main=130)

    driver.implicitly_wait(5)

    driver.get(url=url)

    time.sleep(2)

    html = driver.page_source
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    html = driver.page_source
    driver.quit()
    display.stop() # to comment for windows
    soup = BeautifulSoup(html, "html.parser")
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
    print(new_values)

    brand = soup.find('a', class_="tsCompactControl500Medium")
    if brand is None:
        brand = "Бренд отсутствует"
    else:
        brand = brand.text

    price_with_card = soup.find(string=re.compile("c Ozon Картой"))
    if price_with_card is None:
        price_with_card = soup.find('span', class_=re.compile("^[a-zA-Z0-9_]{6} [a-zA-Z0-9_]{6} [a-zA-Z0-9_]{6}$"))
        price_without_card = None
    else:
        price_with_card = price_with_card.parent.parent.text
        price_with_card = price_with_card.replace("\u2009", "")

        price_without_card = soup.find(string="без Ozon Карты").parent.parent.parent.find("span").text
        # print(price_without_card)
        price_without_card = price_without_card.replace("\u2009", "")

    future_class["Название"] = name
    future_class["Бренд"] = brand
    future_class["Цена с картой"] = price_with_card
    future_class["Цена без карты"] = price_without_card

    future_class["Характеристики"] = dict([(x.text, y) for x, y in zip(specifications, new_values)])
    return future_class


def get_pages(text=""): #TODO

    if text == "":
        return []

    driver = uc.Chrome()
    driver.implicitly_wait(5)

    driver.get(url="https://www.ozon.ru/search/?q=" + text)

    time.sleep(2)

    html = driver.page_source
    driver.quit()
    soup = BeautifulSoup(html, "html.parser")
    urls = []

    urls.append()
    return urls


if __name__ == '__main__':
    # print(parse_page_ozon(url='https://www.whatismybrowser.com'))
    print(parse_page_ozon(url='https://www.ozon.ru/product/vibrosa-hand-brush-1-pcs-1685165481/?advert=APMAptoZS3gnCCNE-SkReavgYRPZ9mwAu_mhzFXgAwGNXOOKtsq6AE3il0nhERXRJWr3i-6tCuGagTAM-TZZ0vuJfMtRTD-HGTP7ocAENxgUkO9V91B1va_WiYGogTGdeZOHdfy74_4XzAm_WXHtuVZHPQUec5Vf3_F2hzz9zkF6lKOi0Y_Jndb_PLVQ2zGGoPtNU_Eg0_4TujjE18Ooe2XyTu_-XTjkOks_1tqt9_nfCIjYWejAo6DTsMdmxj0HsXzqNDPjPq2UC62kV5hXJlaP2-mFRfViEdemAJJADA&avtc=1&avte=4&avts=1731842910'))
    print(parse_page_ozon(url='https://www.ozon.ru/product/krossovki-moocie-1611940316/?advert=APMATHIne-yv7EMEHEjc5lcF5h4n_2NevDf5k0FNlcbvYR9fuFtweySm0y4G-RiMJC1Ro0tPIYXHCT1u2nDcjhVj5jGWk9exEOZWEjcCBP3_DDfuPjO2hcC0sIUj5HHQk7VNlBwar8SZ45_YwWXlIdfCYkzqn1VhXFVy&avtc=1&avte=4&avts=1731837984'))
    print(parse_page_ozon(url='https://www.ozon.ru/product/nabor-skovorod-polaris-easykeep-3dss-3-predmeta-co-semnoy-ruchkoy-iz-nerzhaveyushchey-stali-1652871074/?campaignId=439'))
