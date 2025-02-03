import pytest
from seeker import get_driver, parse, get_pages_ozon, get_pages_wb, find_cheaper_products
from product import Product
from pyvirtualdisplay import Display
import time


def env_inj(func):
    def wrapper(*args, **kwargs):
        display = Display(visible=True, size=(800, 600)) # to comment for windows
        display.start() # to comment for windows
        driver = get_driver()
        result = func(*args, driver=driver, **kwargs)
        driver.quit()
        display.stop()
        return result
    return wrapper

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
@env_inj
def test_parse_page_ozon_main(driver):
    result = parse("https://www.ozon.ru/", driver)
    assert result is None
    
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
@env_inj
def test_parse_page_wb_main(driver):
    result = parse("https://www.wildberries.ru/", driver)
    assert result is None
    
    
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
@env_inj
def test_get_pages_ozon_empty_name(driver):
    prod = Product("", "123")
    result = get_pages_ozon(prod, driver, cost_range="Не установлен", exact_match=False)
    assert result == {}
    

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
@env_inj
def test_get_pages_wb_empty_name(driver):
    prod = Product("", "123")
    result = get_pages_wb(prod, driver, cost_range="Не установлен", exact_match=False)
    assert result == {}

    

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
@env_inj
def test_get_pages_wb_valid(driver):
    prod = Product("Смартфон Xiaomi 13T 12/256, черный", price="47288₽")
    result = get_pages_wb(prod, driver, cost_range="Не установлен", exact_match=False)
    assert len(result) > 0
    for i in range(len(result)):
        assert "http" in list(result.keys())[i]
        assert "₽" in list(result.values())[i]


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
@env_inj
def test_get_pages_ozon_valid(driver):
    prod = Product("Смартфон Xiaomi 13T 12/256, черный", price="47288₽")
    result = get_pages_ozon(prod, driver, cost_range="Не установлен", exact_match=False)
    assert len(result) > 0
    keys = list(result.keys())
    values = list(result.values())
    for i in range(len(result)):
        assert "http" in keys[i]
        assert "₽" in values[i]

        
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_find_cheaper_products_valid_start_wb():
    result = find_cheaper_products("https://www.wildberries.ru/catalog/180601137/detail.aspx", "Не установлен", False)
    assert len(result) > 0
    keys = list(result.keys())
    values = list(result.values())
    for i in range(len(result)):
        assert "http" in keys[i]
        assert "₽" in values[i]


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_find_cheaper_products_valid_start_ozon():
    result = find_cheaper_products("https://www.ozon.ru/product/io-by-red-square-naushniki-provodnye-s-mikrofonom-io-graphite-se-3-5-mm-temno-siniy-1758244283/?campaignId=514", "Не установлен", False)
    assert len(result) > 0
    keys = list(result.keys())
    values = list(result.values())
    for i in range(len(result)):
        assert "http" in keys[i]
        assert "₽" in values[i]
        
 
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_find_cheaper_products_invalid():
    result = find_cheaper_products("https://ru.stackoverflow.com/questions/1438418/aiogram-%D0%BD%D0%B0-inline-%D0%BA%D0%BD%D0%BE%D0%BF%D0%BA%D1%83-%D0%BF%D0%BE%D0%B2%D0%B5%D1%81%D0%B8%D1%82%D1%8C-url-%D0%B8-%D0%BE%D0%B1%D1%80%D0%B0%D0%B1%D0%BE%D1%82%D1%87%D0%B8%D0%BA-%D0%B4%D0%BB%D1%8F-%D1%81%D1%82%D0%B0%D1%82%D0%B8%D1%81%D1%82%D0%B8%D0%BA%D0%B8", "Не установлен", False)
    assert result == "Страницу не удалось распознать" 
    
        
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_find_cheaper_products_empty_str():
    result = find_cheaper_products("", "Не установлен", False)
    assert result == "Страницу не удалось распознать"
    
