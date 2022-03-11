import inspect
import pkgutil
import random
import re
import string
import time
from importlib import import_module

import pika

import config


class Client:
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
        self.mappings = None

    def start(self):
        """
        Starts the client and consumes for new incoming messages.
        Blocks while consuming.
        :return:
        """
        self.mappings = self.find_event_mappings()
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=config.svc_host_messaging))
        self.channel = self.connection.channel()
        self.setup_queues(self.channel)
        self.setup_consumers(self.channel)
        print("Receiving messages...")
        self.channel.start_consuming()

    def stop(self):
        """
        Stops the client and closes any connection to the message broker.
        :return:
        """
        self.connection.close()

    # Adding this to disabled config .pylintrc W0613 didnt work so adding the ignore marker here:
    # pylint: disable=unused-argument
    def dispatch_message(self, channel, method, props, body):
        """
        Callback which dispatches all incoming messages.
        If the client is in sync_mode, the correlation_id of the current message is checked. If it matches,
        the current message is treated as a response of a (blocking) request call and is set as response.
        Otherwise the incoming message is forwarded to a mapped service function.
        Any receiving message during a blocking sync call which is not the response message is re-queued
        by rejecting it. So it will be delivered again.
        :param channel:
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
                print("Dispatching: Response message received: correlation_id=" + self.correlation_id +
                      ", routing_key=" + method.routing_key)
                return

            # Put message back to queue since we're waiting for the response message
            self.channel.basic_reject(method.delivery_tag)
            print("Dispatching: Message rejected to queue (waiting for response message): " + method.routing_key)
            return

        # Map message to service
        found = False
        for key, value in self.mappings.items():
            if self.amqp_match(method.routing_key, key):
                found = True
                self.channel.basic_ack(method.delivery_tag)
                print(f"Dispatching message: {method.routing_key} -> {key} -> {value}()")

                class_path, method_name = value.rsplit('#', 1)
                module_path, class_name = class_path.rsplit('.', 1)

                module = import_module(module_path)

                clazz = getattr(module, class_name)
                service_instance = clazz(self)

                service_meth = getattr(service_instance, method_name)
                service_meth(body)  # Execute service function

        if not found:
            print("Dispatching: Warning: Incoming message did not match any service: " + method.routing_key)

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

        for key, value in self.mappings.items():
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

    def find_event_mappings(self):
        """
        Collects all event mappings from all service classes.
        :return:
        """
        decorator_name = "event"
        mapping = {}

        for _, service_module, _ in pkgutil.iter_modules(['service']):

            module = import_module("service." + service_module)

            for name, cls in inspect.getmembers(module):
                if not inspect.isclass(cls):
                    continue

                sourcelines = inspect.getsourcelines(cls)[0]

                for i, line in enumerate(sourcelines):
                    line = line.strip()
                    if line.split('(')[0].strip() == '@' + decorator_name:  # leaving a bit out
                        key = line.split('"')[1]
                        method_line = sourcelines[i + 1]
                        method_name = method_line.split('def')[1].split('(')[0].strip()
                        mapping[key] = cls.__module__ + "." + cls.__name__ + "#" + method_name

        return mapping


class BaseService:
    """
        Base class for all message services. Use it like this:

        class MyService(BaseService):
            def my_service_action(self, body):
                pass

        And then map your service methods in the routing.py.
    """

    def __init__(self, client):
        self.client: Client = client


# pylint: disable=unused-argument
def event(key):
    """
    The @event decorator.
    :param key:
    :return:
    """

    def decorator(func):
        def func_wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        return func_wrapper

    return decorator
