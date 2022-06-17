from any_inference import Producer
import time
from pprint import pformat

producer = Producer()

def send():
    data = {
        "foo": "baa",
    }
    try:
        print(f"Sending data={pformat(data)}")
        res =  producer.send(data)
        print(f"Received {pformat(res['prediction'])})")
    except TimeoutError:
        print("Timeout")
    
for i in range(36):
    send()
