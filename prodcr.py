import pika
import uuid
import json
from  product import Product
from data import Data


class FindRpcClient(object):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='find_queue')
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            )

        self.response = None
        self.corr_id = None

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body
            self.channel.basic_ack(delivery_tag=method.delivery_tag)

    def call(self, url):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='find_answer',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=url)
        while self.response is None:
            self.connection.process_data_events(time_limit=None)
        return self.response
    
class OzonRpcClient(object):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='ozon_queue')
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            #auto_ack=True
            )

        self.response = None
        self.corr_id = None

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body
            self.channel.basic_ack(delivery_tag=method.delivery_tag)

    def call(self, data):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='ozon_answer',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=data)
        while self.response is None:
            self.connection.process_data_events(time_limit=None)
        return self.response
    

class WbRpcClient(object):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='wb_queue')
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            #auto_ack=True
            )

        self.response = None
        self.corr_id = None

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body
            self.channel.basic_ack(delivery_tag=method.delivery_tag)

    def call(self, data):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='wb_answer',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=data)
        while self.response is None:
            self.connection.process_data_events(time_limit=None)
        return self.response
        

def find_cheaper_products(url: str, cost_range: str, exact_match: bool) -> dict | str:
    
    find_rpc = FindRpcClient()
    ozon_rpc = OzonRpcClient()
    wb_rpc = WbRpcClient()
    
    print(f" [x] Requesting {url};\n {cost_range};\n {exact_match};\n")
    response = find_rpc.call(url).decode()
    product = Product.from_json(response)
    print(f" [.] Got {product}")

    data = Data(product, cost_range, exact_match)
    print(f" [.] Got {product}")
    if type(product) is Product:
        ozon_response = ozon_rpc.call(data.to_json())
        print(f" [.] Got ozon {ozon_response}\n\n")
        wb_response = wb_rpc.call(data.to_json())
        print(f" [.] Got wb {wb_response}\n\n")
        
    ret_dict = json.loads(ozon_response) | json.loads(wb_response)
    ret_dict = dict(sorted(ret_dict.items(), key=lambda x: int(x[1][:-1])))
      
    return ret_dict if ret_dict != {} else "Товар не найден"


def main():
    print(find_cheaper_products("https://www.ozon.ru/product/nabor-nozhey-kuhonnyh-samura-golf-sg-0240-nabor-ih-4-h-nozhey-1576657502/?campaignId=527", "1000 3000", True))

   
if __name__ == "__main__":
    main()