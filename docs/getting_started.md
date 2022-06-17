## Getting Started


### Installation

You can install the package using `pip`

```
pip install git+https://github.com/FrancescoSaverioZuppichini/any-inference.git
```

#### Rabbitmq

You will also need `rabbitmq` you can run locally it using docker

```
docker run --rm -it -p 15672:15672 -p 5672:5672 rabbitmq:management
```

## Simple Example

!!! warning

    So far only the mode advance `WaitAndPopConsumer` consumer is implement. Once it receives a message, it will wait a little bit, batch and send batch the message's replies.

Let's create one producer and one consumer

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

Now, it two different terminal, let's start the `consumer` first and the `publisher later`

<div class="termy">

```console
$ python consumer.py
[12:48:14] INFO     ✅ Connected to                      Consumer.py:52
                    amqp://guest:guest@localhost//  
```

</div>

And the consumer

<div class="termy">

```console
$ python producer.py
[12:48:14] INFO     ✅ Connected to                      Consumer.py:52
                    amqp://guest:guest@localhost//  
```

</div>

As soon as we start the publisher we will see the messages replies, in our case we are just sending back the messages we received

<div class="termy">

```console
$ python producer.py
[12:48:14] INFO     ✅ Connected to                      Consumer.py:52
                    amqp://guest:guest@localhost//  
Sending data={'foo': 'baa'}
           INFO     [60812] received e0b7db7d-ee2b-11ec- Producer.py:97
                    95b2-309c23a77245, waiting for                     
                    e0b7db7d-ee2b-11ec-95b2-309c23a77245               
           INFO     [60812] ack                          Producer.py:99
                    e0b7db7d-ee2b-11ec-95b2-309c23a77245               
Received {'foo': 'baa', 'pid': '60812', 'uid': 'e0b7db7d-ee2b-11ec-95b2-309c23a77245'})
Sending data={'foo': 'baa'}
           INFO     [60812] received e0e489a1-ee2b-11ec- Producer.py:97
                    961f-309c23a77245, waiting for                     
                    e0e489a1-ee2b-11ec-961f-309c23a77245               
           INFO     [60812] ack                          Producer.py:99
                    e0e489a1-ee2b-11ec-961f-309c23a77245               
Received {'foo': 'baa', 'pid': '60812', 'uid': 'e0e489a1-ee2b-11ec-961f-309c23a77245'})
```

</div>

While, from the consumer side we will see all the loggings



<div class="termy">

```console
$ python consumer.py
[12:48:14] INFO     ✅ Connected to                      Consumer.py:52
                    amqp://guest:guest@localhost//  
[12:54:34] INFO     ✅ Connected to                      Consumer.py:52
                    amqp://guest:guest@localhost//                     
[12:54:36] INFO     [60773] 🔔 60812->e0b7db7d-ee2b-11e Consumer.py:177
                    c-95b2-309c23a77245                                
           INFO     [ThreadPoolExecutor-0_0] 🏃 ...     Consumer.py:144
           INFO     [ThreadPoolExecutor-0_0] 📦         Consumer.py:150
                    Batching 1.                                        
           INFO     [ThreadPoolExecutor-0_0] 📦 message Consumer.py:159
                    s=e0b7db7d-ee2b-11ec-95b2-309c23a77                
                    245                                                
Seen e0b7db7d-ee2b-11ec-95b2-309c23a77245
           INFO     [ThreadPoolExecutor-0_0] Done!      Consumer.py:174
           INFO     [ThreadPoolExecutor-1_0] e0b7db7d-e Consumer.py:139
                    e2b-11ec-95b2-309c23a77245 -> 60812                
           INFO     [60773] 🔔 60812->e0e489a1-ee2b-11e Consumer.py:177
                    c-961f-309c23a77245                                
           INFO     [ThreadPoolExecutor-0_0] 🏃 ...     Consumer.py:144
           INFO     [ThreadPoolExecutor-0_0] 📦         Consumer.py:150
                    Batching 1.                                        
           INFO     [ThreadPoolExecutor-0_0] 📦 message Consumer.py:159
                    s=e0e489a1-ee2b-11ec-961f-309c23a77                
                    245                                                
Seen e0e489a1-ee2b-11ec-961f-309c23a77245
           INFO     [ThreadPoolExecutor-0_0] Done!      Consumer.py:174
           INFO     [ThreadPoolExecutor-1_0] e0e489a1-e Consumer.py:139
                    e2b-11ec-961f-309c23a77245 -> 60812                
           INFO     [60773] 🔔 60812->e10e5a76-ee2b-11e Consumer.py:177
                    c-828e-309c23a77245                                
           INFO     [ThreadPoolExecutor-0_0] 🏃 ...     Consumer.py:144
[12:54:37] INFO     [ThreadPoolExecutor-0_0] 📦         Consumer.py:150
                    Batching 1.                                        
           INFO     [ThreadPoolExecutor-0_0] 📦 message Consumer.py:159
                    s=e10e5a76-ee2b-11ec-828e-309c23a77                
                    245                                                
Seen e10e5a76-ee2b-11ec-828e-309c23a77245
           INFO     [ThreadPoolExecutor-0_0] Done!      Consumer.py:174
           INFO     [ThreadPoolExecutor-1_0] e10e5a76-e Consumer.py:139
                    e2b-11ec-828e-309c23a77245 -> 60812                
           INFO     [60773] 🔔 60812->e13825bd-ee2b-11e Consumer.py:177
                    c-a590-309c23a77245                                
           INFO     [ThreadPoolExecutor-0_0] 🏃 ...     Consumer.py:144
           INFO     [ThreadPoolExecutor-0_0] 📦         Consumer.py:150
                    Batching 1.                                        
           INFO     [ThreadPoolExecutor-0_0] 📦 message Consumer.py:159
                    s=e13825bd-ee2b-11ec-a590-309c23a77                
                    245                                                
Seen e13825bd-ee2b-11ec-a590-309c23a77245
           INFO     [ThreadPoolExecutor-0_0] Done!      Consumer.py:174
           INFO     [ThreadPoolExecutor-1_0] e13825bd-e Consumer.py:139
                    e2b-11ec-a590-309c23a77245 -> 60812 
```

</div>
