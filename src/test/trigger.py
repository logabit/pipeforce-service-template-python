import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='pipeforce.topic.default', exchange_type='topic')

# Send Webhook trigger
channel.basic_publish(
    exchange='pipeforce.topic.default', routing_key='pipeforce.webhook.foo.bar', body="bodyOfWebhook")

connection.close()
