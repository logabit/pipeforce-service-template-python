import random
import re
import string
import time
from importlib import import_module

import pika

import config
import routing


class Client(object):
    """
        Messaging client to communicate with hub and other microservices inside PIPEFORCE.
        It supports async and sync message processing.
    """

    def __init__(self):

        print("Starting service: " + config.service_name)
        print("Namespace: " + config.namespace)
        print("Service exclusive queue: " + config.queue_name_self)
        print("Default exchange: " + config.default_exchange_topic)
        print("Broker: " + config.svc_host_messaging)

        # If in sync mode blocks all messages until it gets a response from the server
        self.sync_mode = False

        self.response = None
        self.correlation_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for i in range(10))
        self.connection = None
        self.channel = None

    def start(self):
        """
        Starts the client and consumes for new incoming messages.
        Blocks while consuming.
        :return:
        """
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=config.svc_host_messaging))
        self.channel = self.connection.channel()
        self.setup_queues(self.channel)
        self.setup_consumers(self.channel)
        print("Receiving messages...")
        self.channel.start_consuming()

    def stop(self):
        self.connection.close()

    def dispatch_message(self, ch, method, props, body):
        """
        Callback which dispatches all incoming messages.
        If the client is in sync_mode, the correlation_id of the current message is checked. If it matches,
        the current message is treated as a response of a (blocking) request call and is set as response.
        Otherwise the incoming message is forwarded to a mapped service function.
        Any receiving message during a blocking sync call which is not the response message is re-queued
        by rejecting it. So it will be delivered again.
        :param ch:
        :param method:
        :param props:
        :param body:
        :return:
        """

        # RPC response -> no service mapping
        if self.sync_mode:
            if props.correlation_id == self.correlation_id:
                self.channel.basic_ack(method.delivery_tag)
                self.response = body
                print("Dispatcher: Response message received: correlation_id=" + self.correlation_id +
                      ", routing_key=" + method.routing_key)
                return
            else:
                # Put message back to queue since we're waiting for the response message
                self.channel.basic_reject(method.delivery_tag)
                print("Dispatcher: Message rejected to queue (waiting for response message): " + method.routing_key)
                return

        # Map message to service
        found = False
        for key, value in routing.mappings.items():
            if self.amqp_match(method.routing_key, key):
                found = True
                self.channel.basic_ack(method.delivery_tag)
                print(f"Dispatcher: Message accepted:{method.routing_key} -> {key} -> {value}()")

                class_path, method_name = value.rsplit('.', 1)
                module_path, class_name = class_path.rsplit('.', 1)

                module = import_module(module_path)

                clazz = getattr(module, class_name)
                service_instance = clazz(self)

                service_meth = getattr(service_instance, method_name)
                service_meth(body)  # Execute service function

        if not found:
            print("Dispatcher: Warning: Incoming message did not match any service: " + method.routing_key)

    def setup_queues(self, channel):
        """
        Sets up all default queues to listen on the default exchange.
        :param channel:
        :return:
        """
        channel.exchange_declare(exchange=config.default_exchange_topic, exchange_type='topic')
        channel.queue_declare(queue=config.queue_name_self, durable=True, exclusive=False, auto_delete=True)

    def setup_consumers(self, channel):
        """
        Sets up the default consumers required for this service.
        Adds a binding for each mapping so we get only messages we're really interested in.
        :param channel:
        :return:
        """
        for key, value in routing.mappings.items():
            print(f'Creating Binding: {key} -> {value}() ')

            # Set the routing rules at the broker
            channel.queue_bind(
                exchange=config.default_exchange_topic, queue=config.queue_name_self, routing_key=key)

        # Listen to all messages on the service queue
        channel.basic_consume(
            queue=config.queue_name_self,
            on_message_callback=self.dispatch_message,
            auto_ack=False)

    def message_send(self, key, payload):
        """
        Sends the message to given routing key and returns immediately.
        :param key:
        :param payload:
        :return:
        """
        self.channel.basic_publish(
            exchange=config.default_exchange_topic,
            routing_key=key,
            body=payload)

    def message_send_and_wait(self, key, payload):
        """
        Sends the message to given routing key and waits for response.
        :param key:
        :param payload:
        :return:
        """
        self.sync_mode = True

        try:
            self.channel.basic_publish(
                exchange=config.default_exchange_topic,
                routing_key=key,
                properties=pika.BasicProperties(content_type='text/plain', reply_to=config.queue_name_self,
                                                correlation_id=self.correlation_id),
                body=payload)

            # Block until we get the response
            print(f"Waiting for server response to queue:{config.queue_name_self} with "
                  f"correlation_id:{self.correlation_id}...")
            while self.response is None:
                self.connection.process_data_events()
                time.sleep(0.5)  # Do not do potential re-queueing too frequently -> Give server time to respond

        finally:
            self.sync_mode = False

        resp = self.response
        self.response = None
        return resp

    def amqp_match(self, key: str, pattern: str) -> bool:
        """
        Checks if given key matches the given AMQP pattern.
        :param key:
        :param pattern:
        :return:
        """
        if key == pattern:
            return True
        replaced = pattern.replace(r'*', r'([^.]+)').replace(r'#', r'([^.]+.?)+')
        regex_string = f"^{replaced}$"
        match = re.search(regex_string, key)
        return match is not None
