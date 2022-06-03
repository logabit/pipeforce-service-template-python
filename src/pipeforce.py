# pylint: disable=E0401
import hashlib
import inspect
import pkgutil
import random
import re
import string
import time
from importlib import import_module

import pika
import requests

from src.config import Config


class PipeforceClient:
    """
        Messaging client to communicate with hub and other microservices inside PIPEFORCE.
        It supports async and sync message processing.
    """

    def __init__(self, config: Config):

        self.config = config

        if not self.config.PIPEFORCE_NAMESPACE and not config.PIPEFORCE_INSTANCE:
            raise ValueError("Config PIPEFORCE_NAMESPACE or PIPEFORCE_INSTANCE is required!")

        if not self.config.PIPEFORCE_SERVICE:
            raise ValueError("Config PIPEFORCE_SERVICE is required!")

        if not self.config.PIPEFORCE_DOMAIN:
            config.PIPEFORCE_DOMAIN = "svc.cluster.local"

        # Extract namespace from domain if given
        if not self.config.PIPEFORCE_NAMESPACE and self.config.PIPEFORCE_DOMAIN:
            self.config.PIPEFORCE_NAMESPACE = self.config.PIPEFORCE_DOMAIN.split(".")[0]

        # Create instance name from service and domain if given
        if not self.config.PIPEFORCE_INSTANCE and self.config.PIPEFORCE_NAMESPACE:
            self.config.PIPEFORCE_INSTANCE = self.config.PIPEFORCE_SERVICE + "." + self.config.PIPEFORCE_DOMAIN

        if not self.config.PIPEFORCE_HUB_URL:
            if self.config.PIPEFORCE_DOMAIN and self.config.PIPEFORCE_DOMAIN.endswith("svc.cluster.local"):
                # Inside cluster
                self.config.PIPEFORCE_HUB_URL = "http://hub." + self.config.PIPEFORCE_NAMESPACE + ".svc.cluster.local"
            else:
                # Outside cluster
                self.config.PIPEFORCE_HUB_URL = "https://hub-" + self.config.PIPEFORCE_INSTANCE

        # List configuration values (except sensitive info)
        attrs = dir(config)
        for name in attrs:
            if not name.startswith("__"):
                value = getattr(config, name)

                if value and any(x in name.lower() for x in ("secret", "pass", "token", "cred", "key")):
                    v = str(hashlib.md5(str(value).encode('utf-8')).hexdigest())[0:5]
                    value = "[MD5:" + v + "...]"

                print(name + ": " + str(value))

        # If in sync mode blocks all messages until it gets a response from the server
        self.sync_mode = False

        self.response = None
        self.correlation_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for i in range(10))
        self.connection = None
        self.channel = None
        self.mappings = None

        # The timestamp in seconds when the last token was requested
        self.last_token_timestamp: int = None

        # The last response from a refresh request
        self.last_token_response = None

    def start_consuming(self):
        """
        Starts the client and consumes for new incoming messages.
        Blocks while consuming.
        :return:
        """
        self.mappings = self.find_event_mappings()
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.config.PIPEFORCE_MESSAGING_HOST))
        self.channel = self.connection.channel()
        self.setup_queues(self.channel)
        self.setup_consumers(self.channel)
        print("Receiving messages...")
        self.channel.start_consuming()

    def stop_consuming(self):
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
        channel.exchange_declare(exchange=self.config.PIPEFORCE_MESSAGING_DEFAULT_TOPIC, exchange_type='topic')
        channel.queue_declare(queue=self.self.config.PIPEFORCE_MESSAGING_QUEUE, durable=True, exclusive=False,
                              auto_delete=True)

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
                exchange=self.config.PIPEFORCE_MESSAGING_DEFAULT_TOPIC, queue=self.config.PIPEFORCE_MESSAGING_QUEUE,
                routing_key=key)

        # Listen to all messages on the service queue
        channel.basic_consume(
            queue=self.config.PIPEFORCE_MESSAGING_QUEUE,
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
            exchange=self.config.default_exchange_topic,
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
                exchange=self.config.default_exchange_topic,
                routing_key=key,
                properties=pika.BasicProperties(content_type='text/plain',
                                                reply_to=self.config.PIPEFORCE_MESSAGING_QUEUE,
                                                correlation_id=self.correlation_id),
                body=payload)

            # Block until we get the response
            print(f"Waiting for server response to queue:{self.config.PIPEFORCE_MESSAGING_QUEUE} with "
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

    def run_pipeline(self, pipeline):
        """
        Executes the given pipeline on PIPEFORCE and returns the body result.
        :param pipeline: The pipeline as YAML string
        :return:
        """

        access_token = self.get_pipeforce_access_token()
        headers = {'Content-type': 'application/yaml', 'Authorization': 'Bearer ' + access_token}
        return self.do_post(self.config.PIPEFORCE_HUB_URL + f"/api/v3/pipeline", data=pipeline, headers=headers)

    def run_command(self, name, params):
        """
        Executes a single command on PIPEFORCE and returns the body result.
        :param name: The name of the command.
        :return: params: The params of the command.
        """

        access_token = self.get_pipeforce_access_token()
        headers = {'Content-type': 'application/json', 'Authorization': 'Bearer ' + access_token}
        return self.do_post(self.config.PIPEFORCE_HUB_URL + f"/api/v3/command/{name}", json=params,
                            headers=headers)

    def get_pipeforce_access_token(self):
        """
        Returns the current access token to login to PIPEFORCE.
        In case the current access token was invalidated because of timeout or doesn't exist yet,
        exchanges a new one using the PIPEFORCE_SECRET env and caches the result.
        :return:
        """

        # If current token is still valid -> Return it
        if self.last_token_response:
            current = int(time.time())
            if (current - self.last_token_timestamp) < self.last_token_response['expires_in']:
                return self.last_token_response['access_token']

        token = None

        # Is it Basic secret?
        if self.config.PIPEFORCE_SECRET.startswith("Basic "):
            value = self.config.PIPEFORCE_SECRET[len("Basic "):]
            split = value.split(":")
            username = split[0]
            password = split[1]

            json = self.do_post(self.config.PIPEFORCE_HUB_URL + "/api/v3/command/iam.token",
                                json={"username": username, "password": password})

            token = json['refresh_token']

        # Is it Apitoken secret?
        elif self.config.PIPEFORCE_SECRET.startswith("Apitoken "):
            token = self.config.PIPEFORCE_SECRET[len("Apitoken "):]

        # Exchange offline token for new refresh token and store it
        self.last_token_response = self.do_post(self.config.PIPEFORCE_HUB_URL + "/api/v3/command/iam.token.refresh",
                                                json={"refreshToken": token})

        self.last_token_timestamp = int(time.time())
        return self.last_token_response['access_token']

    def do_post(self, url, json, headers={}):
        response = requests.post(url, json=json, headers=headers)

        if response.status_code != 200:
            raise Exception(f"Error response [code: {response.status_code}] from POST to [{url}]: {response.text}")

        return self.extract_content(response)

    def do_get(self, url, params={}, headers={}):
        response = requests.get(url, params=params, headers=headers)

        if response.status_code != 200:
            raise Exception(f"Error response [code: {response.status_code}] from GET to [{url}]: {response.text}")

        return self.extract_content(response)

    def extract_content(self, response):
        data = response.text

        if not data:
            return None

        if data.startswith("[") or data.startswith("{"):
            return response.json()

        return data


class BaseService:
    """
        Base class for all message services. Use it like this:

        class MyService(BaseService):
            def my_service_action(self, body):
                pass

        And then map your service methods in the routing.py.
    """

    def __init__(self, client):
        self.client: PipeforceClient = client


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
