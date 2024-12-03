import json
class Product():
    def __init__(self, name, price, brand=None, price_with_card=None, specifications=None, url=None):
        self.name = name
        self.price = price
        self.price_with_card = price_with_card
        self.brand = brand
        self.specifications = specifications
        self.url = url

    def __str__(self):
        return f"Название: {self.name}\nЦена: {self.price}\nЦена с картой: {self.price_with_card}\nБренд: {self.brand}\nХарактеристики: {self.specifications.__str__()}\nСсылка: {self.url}"
        