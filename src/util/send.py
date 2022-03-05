import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()


channel.exchange_declare(exchange='pipeforce.topic.default', exchange_type='topic')

channel.basic_publish(
    exchange='pipeforce.topic.default', routing_key='pipeforce.webhook.weclapp.order.created', body="SOME MESSAGE!")

print(" [x] Sent %r:%r" % ("pipeforce.service.myservice!", "SOME MESSAGE!"))

connection.close()
