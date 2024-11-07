import json
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
    # display = Display(visible=True, size=(800, 600))
    # display.start()
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    # options.add_argument("user-agent=" + UserAgent().chrome)
    # options.add_argument("--headless")
    driver = uc.Chrome(options=options)
    # driver = uc.Chrome()

    driver.implicitly_wait(5)

    driver.get(url=url)

    time.sleep(2)

    html = driver.page_source
    driver.save_screenshot("ozon.png")
    soup = BeautifulSoup(html, "html.parser")
    print(soup)
    while soup.find('h1', class_="tm6_27 tsHeadline550Medium", style="max-height:60px;") is None:
        print(soup.find('h1', class_="tm6_27 tsHeadline550Medium", style="max-height:60px;"))
        driver.refresh()
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
    else:
        name = soup.find('h1', class_="tm6_27 tsHeadline550Medium", style="max-height:60px;").text
        name = name.replace("\n", "")
        name = name.replace("  ", "")

        driver.quit()
        # display.stop()

        specifications = soup.find_all('span', class_="tsBodyM")
        values = soup.find_all('span', class_="m8y_27 tsBody400Small")

        brand = soup.find('a', class_="tsCompactControl500Medium").text
        price = soup.find('span', class_="s5m_27 ms4_27").text
        price = price.replace("\u2009", "")

        future_class["Название"] = name
        future_class["Бренд"] = brand
        future_class["Цена"] = price

        future_class["Характеристики"] = dict([(x.text, y.text) for x, y in zip(specifications, values)])
    return future_class


def get_pages(text=""):

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
    print(parse_page_ozon(url='https://www.ozon.ru/product/nabor-skovorod-polaris-easykeep-3dss-3-predmeta-co-semnoy-ruchkoy-iz-nerzhaveyushchey-stali-1652871074/?campaignId=439'))
