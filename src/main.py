import random
import re
import string

import pika

import context
from config import setting, routing


class PipeforceClient(object):

    def __init__(self):
        self.response = None
        self.correlation_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for i in range(10))
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=setting.svc_host_messaging))
        self.channel = self.connection.channel()
        self.setup_queues(self.channel)
        self.setup_consumers(self.channel)

    def dispatch_message(self, ch, method, props, body):

        # RPC response -> no service mapping
        if props.correlation_id == self.correlation_id:
            self.response = body
            return

        found = False
        for key, value in routing.mappings.items():
            if self.amqp_match(method.routing_key, key):
                found = True
                print("Message matches: " + method.routing_key + " -> " + key + " -> " + ".".join(
                    [value.__module__, value.__name__]) + "()")
                value(body)  # Execute service function

        if not found:
            print("Warning: Message did not match any service: " + method.routing_key)

    def setup_queues(self, channel):
        # Setup the default queue for this service
        channel.exchange_declare(exchange='pipeforce.topic.default', exchange_type='topic')
        channel.queue_declare(queue=setting.queue_name_self, durable=True, exclusive=False, auto_delete=True)

    def setup_consumers(self, channel):

        # Setup all mapped services (for ASYNC calls)
        for key, value in routing.mappings.items():
            print(f'Creating Binding: {key} -> {".".join([value.__module__, value.__name__])}() ')

            # Set the routing rules at the broker
            channel.queue_bind(
                exchange=setting.default_exchange_topic, queue=setting.queue_name_self, routing_key=key)

        # Listen to all messages on the service queue
        channel.basic_consume(
            queue=setting.queue_name_self,
            on_message_callback=self.dispatch_message,
            auto_ack=True)

    def message_send_async(self, key, payload):
        """
            Sends the message to given routing key and returns immediately.
        """
        self.channel.basic_publish(
            exchange=setting.default_exchange_topic,
            routing_key=key,

            body=payload)

    def message_send_sync(self, key, payload):
        """
            Sends the message to given routing key and waits for response.
        """
        self.response = None
        self.channel.basic_publish(
            exchange=setting.default_exchange_topic,
            routing_key=key,
            properties=pika.BasicProperties(content_type='text/plain', reply_to=setting.queue_name_self,
                                            correlation_id=self.correlation_id), body=payload)

        # Block until we get the response
        while self.response is None:
            self.connection.process_data_events()

        return self.response

    def amqp_match(self, key: str, pattern: str) -> bool:
        if key == pattern:
            return True
        replaced = pattern.replace(r'*', r'([^.]+)').replace(r'#', r'([^.]+.?)+')
        regex_string = f"^{replaced}$"
        match = re.search(regex_string, key)
        return match is not None


print("Starting service: " + setting.service_name + " in namespace " + setting.namespace)
print("Service queue: " + setting.queue_name_self)
print("Default exchange: " + setting.default_exchange_topic)
print("Connecting to broker: " + setting.svc_host_messaging)

pipeforce = PipeforceClient()
context.client = pipeforce

print("Receiving messages...")

pipeforce.channel.start_consuming()
