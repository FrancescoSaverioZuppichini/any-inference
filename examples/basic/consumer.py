from any_inference import WaitAndPopConsumer
from typing import List, Dict, Any
import time

def inference(messages: List[Dict[str, Any]]):
    # here you can have your thicc model
    print(f"Seen {','.join([m['uid'] for m in messages])}")
    time.sleep(0.05)
    return messages

WaitAndPopConsumer(inference_strategy=inference).spin()