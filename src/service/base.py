from pipeforce import Client


class BaseService(object):
    """
        Base class for all message services. Use it like this:

        class MyService(BaseService):
            def my_service_action(self, body):
                pass

        And then map your service methods in the routing.py.
    """

    def __init__(self, client):
        self.client: Client = client
