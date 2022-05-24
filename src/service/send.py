#This File will create a new queue and routing key to the rabbitmq and send the message
# The agenda of this file to create is to get data on management side API
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost',virtual_host='foo'))
channel = connection.channel()

channel.queue_declare(queue='2nd Key')

channel.basic_publish(exchange='',                    
                      routing_key='2nd Key',
                      body='Hello from 2nd key!')
print(" [x] Sent 'Hello from 2nd key!'")
connection.close()
