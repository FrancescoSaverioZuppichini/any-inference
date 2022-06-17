import os
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from threading import Lock, current_thread
from typing import Any, Callable, Dict, List, Optional

from kombu import Connection, Exchange, Message, Queue

from .logger import logger


class Consumer:
    def __init__(
        self,
        inference_strategy: Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]],
        hostname: str = "amqp://guest:guest@localhost//",
        message_ttl: Optional[int] = 4,
        max_length: Optional[int] = 32,
        uid: Optional[str] = None,
    ):
        """The Consumer, it's job is to consume messages and send them back. You need to implement two methods, `consume` and `send`. `consume` is called for every message received in the queue, `send` can be used to send back the result to the `inputs` queue.


        Args:
            inference_strategy (Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]]): A callable to which we pass the received messages.
            hostname (_type_, optional): The rabbitmq hostname. Defaults to "amqp://guest:guest@localhost//".
            message_ttl (Optional[int], optional): The time to live (ttl) of inputs messages. Defaults to 4.
            max_length (Optional[int], optional): Max number of messages in the inputs queue. Defaults to 32.
            uid (Optional[str], optional): Unique identifier of this consumer, if not passed we will use `os.getpid()`. Defaults to None.
        """
        if not uid:
            uid = str(os.getpid())
        self.inference_strategy = inference_strategy
        self.uid = uid
        self.hostname = hostname

        self._connection = Connection(self.hostname)
        self._inputs_exchange = Exchange(
            type="direct", durable=False, delivery_mode="transient"
        )
        self._inputs_queue = Queue(
            "inputs",
            exchange=self._inputs_exchange,
            routing_key="inputs",
            durable=False,
            message_ttl=message_ttl,
            max_length=max_length,
        )

        logger.info(f"✅ Connected to {self.hostname}")

    def send(self, body: Dict):
        raise NotImplemented

    def consume(self, body: Dict, message: Message):
        raise NotImplemented

    def spin(self):
        with self._connection.Consumer(
            self._inputs_queue, callbacks=[self.consume], accept=["json"]
        ):
            while True:
                try:
                    self._connection.drain_events()
                except KeyboardInterrupt:
                    self.shutdown()
                    break
                except Exception as e:
                    logger.exception(str(e))
                    traceback.print_exc()
                    continue

    def shutdown(self):
        pass


class WaitAndPopConsumer(Consumer):
    def __init__(
        self,
        max_batch: int = 8,
        consume_num_workers: int = 4,
        send_num_workers: int = 4,
        wait_ms: int = 200,
        *args,
        **kwargs,
    ):
        """A consumer that will receive messages, store them in an internal stack, wait a bit and then process a max amount of `max_batch` messages. This is handy since it allows to batch messages together.

        Internally two thread pools are used, one to consume messages and one to send them back to the `inputs` queue.

        A lock is used to ensure threads cannot access the internal stack and run inference at the same time.


        ```python
            def inference(messages):
                print(messages)
                return messages

            WaitAndPopConsumer(inference_strategy=inference).spin()
        ```
        Args:
            max_batch (int, optional): The maximum amount of massages we will batch together. Defaults to 8.
            consume_num_workers (int, optional): Number of workers used in the consume thread pool. Defaults to 4.
            send_num_workers (int, optional): Number of workers used in the send thread pool. Defaults to 4.
            wait_ms (int, optional): _description_. Defaults to 200.
        """
        super().__init__(*args, **kwargs)
        self.max_batch = max_batch
        self.consume_num_workers = consume_num_workers
        self.wait_ms = wait_ms
        self._outputs_exchange = Exchange(
            "outputs", type="direct", durable=False, delivery_mode="transient"
        )
        self._consume_pool = ThreadPoolExecutor(max_workers=consume_num_workers)
        self._publish_pool = ThreadPoolExecutor(
            max_workers=send_num_workers, initializer=self.initializer_for_publish_pool
        )
        self.stack = []
        self._lock = Lock()

    def initializer_for_publish_pool(self):
        thread = current_thread()
        thread.connection = Connection(self.hostname)
        thread.producer = thread.connection.Producer(serializer="json")

    def shutdown(self):
        self._consume_pool.shutdown()
        self._publish_pool.shutdown()

    def send(self, body: Dict):
        thread = current_thread()
        thread_name = thread.name

        thread.producer.publish(
            body, routing_key=body["pid"], exchange=self._outputs_exchange
        )
        logger.info(f"[{thread_name}] {body['uid']} -> {body['pid']}")

    def consume_in_thread(self):
        thread = current_thread()
        thread_name = thread.name
        logger.info(f"[{thread_name}] 🏃 ... ")

        if self.wait_ms > 0:
            time.sleep(self.wait_ms / 1000)
        self._lock.acquire()
        batch_size = min(self.max_batch, len(self.stack))
        logger.info(f"[{thread_name}] 📦 Batching {batch_size}.")
        messages = []
        for _ in range(batch_size):
            try:
                message = self.stack.pop()
                messages.append(message)
            except IndexError:
                logger.error(f"[{thread_name}] 📦 Stack empty!")

        logger.info(
            f"[{thread_name}] 📦 messages={','.join([str(m['uid']) for m in messages])}"
        )
        # run inference and create the outputs
        predictions = self.inference_strategy(messages)
        self._lock.release()
        # create the outptus
        outputs = []
        for message, prediction in zip(messages, predictions):
            output = {"prediction": prediction, **message}
            outputs.append(output)
        # send each output in its correct queue
        for output in outputs:
            self._publish_pool.submit(partial(self.send, output))

        logger.info(f"[{thread_name}] Done!")

    def consume(self, body: Dict, message: Message):
        logger.info(f"[{self.uid}] 🔔 {body['pid']}->{body['uid']}")
        # place the message's body in our stack
        self.stack.extend([body])
        # ack it
        message.ack()
        num_tasks = self._consume_pool._work_queue.qsize()
        if num_tasks < self.consume_num_workers:
            # submit the process task to the threadpool
            self._consume_pool.submit(self.consume_in_thread)
