import json
from product import Product

class Data:
    def __init__(self, product: Product, cost_range: str, exact_match: bool):
        self.product = product
        self.cost_range = cost_range
        self.exact_match = exact_match
        
        
    def to_json(self):
        data = {
            "product": self.product.to_json(),
            "cost_range": self.cost_range,
            "exact_match": self.exact_match
        }
        return json.dumps(data)
    
    @staticmethod
    def from_json(json_str):
        data = json.loads(json_str)
        return (Product(**json.loads(data["product"])), data["cost_range"], data["exact_match"])