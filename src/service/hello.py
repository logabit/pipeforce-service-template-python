from service.base import BaseService


class HelloService(BaseService):
    """
        Example service. Feel free to delete.
    """

    def greeting(self, body):
        print("GREETING CALLED. BODY: " + str(body))

    def greeting_with_wait(self, body):
        print("GREETING WITH WAIT CALLED. BODY: " + str(body))
        result = self.client.message_send_and_wait("command.http.post", "post message")
        print("RESPONSE IS: " + str(result))
