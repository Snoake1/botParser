import pytest
from seeker import parse_page_ozon, parse_page_wildberries, get_driver
from product import Product
import undetected_chromedriver as uc 


def driver_inj(func):
    def wrapper(*args, **kwargs):
        driver = get_driver()
        result = func(*args, driver=driver, **kwargs)
        driver.quit()
        return result
    return wrapper

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
@driver_inj
def test_parse_page_ozon_valid_page(driver):
    result = parse_page_ozon('file:///home/snoake/vkr/botSeeker/tests/pages/%D0%A2%D0%BE%D0%B2%D0%B0%D1%80%20%D1%81%20%D0%BA%D0%B0%D1%80%D1%82%D0%BE%D0%B9%20OZON.html', driver)
    assert result.brand == "KARATOV"
    assert result.name == "Кольцо женское c фианитами, золото 375 пробы, KARATOV"
    assert result.price_with_card == "3299₽  c Ozon Картой"
    assert result.price == "3399₽"
    assert result.get_cleared_name() == "Кольцо женское c фианитами золото 375 пробы KARATOV"
    assert isinstance(result.specifications, dict)


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
@driver_inj
def test_parse_page_ozon_one_price(driver):
    result = parse_page_ozon('file:///home/snoake/vkr/botSeeker/tests/pages/%D0%A1%D0%BC%D0%B0%D1%80%D1%82%D1%84%D0%BE%D0%BD%20Xiaomi%2013T%20%20%D0%B1%D0%B5%D0%B7%20%D0%BA%D0%B0%D1%80%D1%82%D1%8B%20OZON.html', driver)
    assert result.brand == "Бренд отсутствует"
    assert result.name == "Xiaomi Смартфон 13T 5G Глобальная версия Абсолютно новый мобильный телефон европейской версии, заклеенный наклейкой (экологически чистый). 8/256 ГБ, черный"
    assert result.price_with_card  == "Цена с картой отсутствует"
    assert result.price == "33593₽"
    assert result.get_cleared_name() == "Xiaomi Смартфон 13T 5G Глобальная версия Абсолютно новый мобильный телефон европейской версии заклеенный наклейкой экологически чистый 8/256 ГБ"
    assert isinstance(result.specifications, dict)
   
  
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
@driver_inj
def test_parse_page_ozon_invalid(driver):
    result = parse_page_ozon('file:///home/snoake/vkr/botSeeker/tests/pages/invalid%20apg.html', driver)
    assert result is None
    
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
@driver_inj
def test_parse_page_wildberries_valid(driver):
    result = parse_page_wildberries('file:///home/snoake/vkr/botSeeker/tests/pages/%D0%A1%D1%82%D0%B5%D0%BB%D1%8C%D0%BA%D0%B8.%20%D1%86%D0%B5%D0%BD%D0%B0%20%D1%81%20%D0%BA%D0%BE%D1%88%D0%B5%D0%BB%D1%8C%D0%BA%D0%BE%D0%BC%20%D0%B8%20%D0%B1%D0%B5%D0%B7%20Wildberries.html', driver)
    assert result.price == "454₽"
    assert result.price_with_card == "444₽"
    assert result.brand == "ЗДОРОВЬЕ И КОМФОРТ !!!"
    assert result.name == "Стельки для зимней обуви меховые греющие мужские женские"
    assert result.get_cleared_name() == "Стельки для зимней обуви меховые греющие мужские женские"
    assert isinstance(result.specifications, dict)
    

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
@driver_inj
def test_parse_page_wildberries_one_price(driver):
    result = parse_page_wildberries('file:///home/snoake/vkr/botSeeker/tests/pages/prod_with_one_price_wb.html', driver)
    assert result.price == "59605₽"
    assert result.price_with_card == "Цена с картой отсутствует"
    assert result.brand == "Xiaomi"
    assert result.name == "Смартфон 13T Pro 12/512Gb, Черный"
    assert result.get_cleared_name() == "Смартфон 13T Pro 12/512Gb"
    assert isinstance(result.specifications, dict)
    
    
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
@driver_inj
def test_parse_page_wildberries_invalid(driver):
    result = parse_page_wildberries('file:///home/snoake/vkr/botSeeker/tests/pages/invalid%20apg.html', driver)
    assert result is None   