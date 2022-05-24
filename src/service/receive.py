#This File will receive the message from the virtual host and queue and display the message
# The agenda of this file to create is to get data on management side API
import pika, sys, os

def main():

    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost',virtual_host='foo'))
    channel = connection.channel()

    channel.queue_declare(queue='2nd Key')

    def callback(ch, method, properties, body):
        print(" [x] Received %r" % body)

    channel.basic_consume(queue='2nd Key',
                        auto_ack=True,
                        on_message_callback=callback)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)