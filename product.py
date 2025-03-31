import re
import string
import json

colors = {
    "красный",
    "красная",
    "красное",
    "красные",
    "синий",
    "синяя",
    "синее",
    "синие",
    "зеленый",
    "зеленая",
    "зеленое",
    "зеленые",
    "черный",
    "черная",
    "черное",
    "черные",
    "белый",
    "белая",
    "белое",
    "белые",
    "желтый",
    "желтая",
    "желтое",
    "желтые",
    "фиолетовый",
    "фиолетовая",
    "фиолетовое",
    "фиолетовые",
    "серый",
    "серая",
    "серое",
    "серые",
    "оранжевый",
    "оранжевая",
    "оранжевое",
    "оранжевые",
    "розовый",
    "розовая",
    "розовое",
    "розовые",
    "коричневый",
    "коричневая",
    "коричневое",
    "коричневые",
    "голубой",
    "голубая",
    "голубое",
    "голубые",
    "бежевый",
    "бежевая",
    "бежевое",
    "бежевые",
    "берюзовый",
    "берюзовая",
    "берюзовое",
    "берюзовые",
    "золотистый",
    "золотистая",
    "золотистое",
    "золотистые",
    "серебряный",
    "серебряная",
    "серебряное",
    "серебряные",
    "золотой",
    "золотая",
    "золотое",
    "золотые",
    "бронзовый",
    "бронзовая",
    "бронзовое",
    "бронзовые",
}


class Product:
    """
    Представление товара
    """

    def __init__(
        self,
        name,
        price,
        brand=None,
        price_with_card=None,
        specifications=None,
        url=None,
    ):
        self.name = name
        self.price = price
        self.price_with_card = price_with_card
        self.brand = brand
        self.specifications = specifications
        self.url = url

    def __str__(self):
        return f"Название: {self.name}\nЦена: {self.price}\n\
            Цена с картой: {self.price_with_card}\nБренд: {self.brand}\n\
            Характеристики: {self.specifications.__str__()}\nСсылка: {self.url}"

    def get_cleared_name(self):
        """Функция очистки названия"""
        cleaned_name = re.sub(
            r"\b(" + "|".join(colors) + r")\b", "", self.name, flags=re.IGNORECASE
        )
        return " ".join(
            word.strip(string.punctuation)
            for word in re.sub(r"\s+", " ", cleaned_name).strip().split()
        )

    def to_json(self):
        """Перевод в JSON формат"""
        return json.dumps(self.__dict__)

    @staticmethod
    def from_json(json_str):
        """Перевод из JSON формата"""
        data = json.loads(json_str)
        return Product(**data)
