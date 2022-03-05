import json

import pika

from config import setting, routing


class PipeforceClient(object):

    def __init__(self):
        self.response = None
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=setting.svc_host_messaging))
        self.channel = self.connection.channel()
        self.props = pika.BasicProperties(content_type='text/plain', reply_to=setting.queue_name_pipeline_response)
        self.setup_queues(self.channel)
        self.setup_consumers(self.channel)

    def on_pipeline_response(self, ch, method, props, body):
        self.response = body

    def on_service_message(self, ch, method, props, body):
        print(str(body))

    # Executes a given pipeline in the hub service and waits for the result.
    def pipeline(self, msg):
        body = json.dumps(msg)
        self.channel.basic_publish(
            exchange='',
            routing_key=setting.queue_name_pipeline,
            properties=self.props,
            body=body)

        while self.response is None:
            self.connection.process_data_events()

        return self.response

    def setup_queues(self, channel):
        # Default queue for this service

        channel.exchange_declare(exchange='pipeforce.topic.default', exchange_type='topic')
        channel.queue_declare(queue=setting.queue_name_self, durable=True, exclusive=False, auto_delete=True)

    def setup_consumers(self, channel):
        # # Queue for pipeline responses from hub service
        # channel.basic_consume(
        #     queue=config.queue_name_pipeline_response,
        #     on_message_callback=self.on_pipeline_response,
        #     auto_ack=True)

        # Setup all mapped services
        for key, value in routing.mappings.items():
            print(
                f'Creating mapping: {key} -> {".".join([value.__module__, value.__name__])}() '
                f'[Exchange: {setting.default_exchange_topic}, Queue: {setting.queue_name_self}]')

            channel.queue_bind(
                exchange=setting.default_exchange_topic, queue=setting.queue_name_self, routing_key=key)

            channel.basic_consume(
                queue=setting.queue_name_self,
                on_message_callback=value,
                auto_ack=True)


message = {
    "pipeline":
        [
            {
                "iam.authorize": {
                    "username": "developer1",
                    "password": "developer1pwd"
                }
            },
            {
                "log": {
                    "message": "HELLO WORLD!"
                }
            },
            {
                "datetime": {
                    "message": "HELLO WORLD!"
                }
            }
        ]
}

print("Starting service: " + setting.service_name)
print("Connecting to broker: " + setting.svc_host_messaging)
client = PipeforceClient()
print("Receiving messages...")
client.channel.start_consuming()

# response = client.pipeline(message)
# print(" [.] Got %r" % response)
