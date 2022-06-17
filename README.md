# Any Inference 🚀

🚧 This project is in WIP

## Doc
Head over the doc to learn more!

## Example

```python
# producer.py
from any_inference import Producer
import time

producer = Producer()

def send():
    data = {
        "foo": "baa",
    }
    try:
        res =  producer.send(data)
        print(res)
    except TimeoutError:
        print("Timeout")
    
for i in range(36):
    send()
    time.sleep(0.05)
```


```python
# consumer.py
from any_inference import WaitAndPopConsumer
from typing import List, Dict, Any

def inference(messages: List[Dict[str, Any]]):
    # here you can have your thicc model
    print(f"Seen {','.join([m['uid'] for m in messages])}")
    return messages

WaitAndPopConsumer(inference_strategy=inference).spin()
```




