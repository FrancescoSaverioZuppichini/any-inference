import os
from functools import partial
from typing import Any, Dict, Optional
from uuid import uuid1

from kombu import Connection, Exchange, Message, Queue

from .logger import logger


class Producer:
    def __init__(
        self,
        hostname: str = "amqp://guest:guest@localhost//",
        inputs_message_ttl: Optional[int] = 4,
        inputs_max_length: Optional[int] = 32,
        ouputs_message_ttl: Optional[int] = 4,
        ouputs_max_length: Optional[int] = 32,
        uid: Optional[str] = None,
        wait_timeout: Optional[int] = 2,
    ):
        """The producer, his job is to receive messages, put the in the `inputs` queue and wait a `wait_timeout` to receive an answer.

        We add a field `'uid'` inside the `send` method to identify the message we have send.


        ```python
        producer = Producer()
        body = {
            "baa": "foo",
        }

        try:
            response = producer.send(body)
            print(response)
        except TimeoutError:
            print("Timeout")
        ```

        Args:
            hostname (_type_, optional): The rabbitmq hostname. Defaults to "amqp://guest:guest@localhost//".
            inputs_message_ttl (Optional[int], optional):  The time to live (ttl) of inputs messages. Defaults to 4.
            inputs_max_length (Optional[int], optional): Max number of messages in the inputs queue. Defaults to 32.
            ouputs_message_ttl (Optional[int], optional):  The time to live (ttl) of outputs messages. Defaults to 4.
            ouputs_max_length (Optional[int], optional): Max number of messages in the outputs queue. Defaults to 32.
            uid (Optional[str], optional): Unique identifier of this producer, if not passed we will use `os.getpid()`. Defaults to None.
            wait_timeout (Optional[int], optional): Maximum amount of time(in seconds) we will wait for an answer. Defaults to 2.
        """
        if not uid:
            uid = str(os.getpid())
        self.uid = uid
        self.wait_timeout = wait_timeout
        self._connection = Connection(hostname)
        self._producer = self._connection.Producer(serializer="json")
        self._inputs_exchange = Exchange(
            type="direct", durable=False, delivery_mode="transient"
        )
        self._inputs_queue = Queue(
            "inputs",
            exchange=self._inputs_exchange,
            routing_key="inputs",
            durable=False,
            message_ttl=inputs_message_ttl,
            max_length=inputs_max_length,
        )
        self._outputs_exchange = Exchange(
            "outputs", type="direct", durable=False, delivery_mode="transient"
        )
        self._outputs_queue = Queue(
            self.uid,
            exchange=self._outputs_exchange,
            routing_key=self.uid,
            durable=False,
            exclusive=True,
            message_ttl=ouputs_message_ttl,
            max_length=ouputs_max_length,
        )

    def send(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        output = [None]
        uid = uuid1()
        # add the message identifier, we will use it later to know if we have receive an answer
        data["uid"] = str(uid)

        self._producer.publish(
            data,
            routing_key="inputs",
            exchange=self._inputs_exchange,
            declare=[self._inputs_queue],
        )

        def consume(body: Dict[str, Any], message: Message, uid: str):
            logger.info(f'[{self.uid}] received {body["uid"]}, waiting for {uid}')
            if body["uid"] == uid:
                logger.info(f"[{self.uid}] ack {uid}")
                output[0] = body
                # this the answer for my request, we need to ack
                message.ack()

        with self._connection.Consumer(
            self._outputs_queue,
            callbacks=[partial(consume, uid=data["uid"])],
            accept=["json"],
        ):
            try:
                self._connection.drain_events(timeout=self.wait_timeout)
            except Exception as e:
                print(e)
                pass

        if not output[0]:
            raise TimeoutError(f"Output(uid={uid}) not received in time.")

        return output[0]
