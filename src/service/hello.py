from pipeforce import BaseService, event


class HelloService(BaseService):
    """
        Example service. Feel free to delete.
    """

    @event("pipeforce.webhook.foo.*")
    def greeting(self, body):
        """
        Example 1
        :param body:
        :return:
        """
        print("GREETING CALLED. BODY: " + str(body))

    def greeting_with_wait(self, body):
        """
        Example 2
        :param body:
        :return:
        """
        print("GREETING WITH WAIT CALLED. BODY: " + str(body))
        result = self.client.message_send_and_wait("command.http.post", "post message")
        print("RESPONSE IS: " + str(result))
