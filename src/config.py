import os


# pylint: disable=invalid-name

class Config:
    """
    Default settings for this microservice. Do not change unless you know what you're doing.
    """

    # Core settings
    PIPEFORCE_SERVICE = os.getenv("PIPEFORCE_SERVICE")
    PIPEFORCE_NAMESPACE = os.getenv("PIPEFORCE_NAMESPACE")
    PIPEFORCE_HUB_URL = os.getenv("PIPEFORCE_HUB_URL")
    PIPEFORCE_INSTANCE = os.getenv("PIPEFORCE_INSTANCE")
    PIPEFORCE_DOMAIN = os.getenv("PIPEFORCE_DOMAIN")

    # The secret to execute PIPEFORCE commands and pipelines.
    # Can be Apitoken <token> or Basic <username:password>
    PIPEFORCE_SECRET = os.getenv("PIPEFORCE_SECRET")

    # Messaging settings
    PIPEFORCE_MESSAGING_HOST = os.getenv("PIPEFORCE_MESSAGING_HOST", "host.docker.internal")
    PIPEFORCE_MESSAGING_PORT = os.getenv("PIPEFORCE_MESSAGING_PORT", "5672")
    PIPEFORCE_MESSAGING_API_PORT = os.getenv("PIPEFORCE_MESSAGING_API_PORT", "15672")
    PIPEFORCE_MESSAGING_USERNAME = os.getenv("PIPEFORCE_MESSAGING_USERNAME", "guest")
    PIPEFORCE_MESSAGING_PASSWORD = os.getenv("PIPEFORCE_MESSAGING_PASSWORD", "guest")
    PIPEFORCE_MESSAGING_DEFAULT_TOPIC = "pipeforce.topic.default"
    PIPEFORCE_MESSAGING_DEFAULT_DLQ = "pipeforce_default_dlq"
    PIPEFORCE_MESSAGING_QUEUE = "pipeforce.service." + str(PIPEFORCE_SERVICE)

    # Internal microservice hosts
    PIPEFORCE_SVC_PREFIX = "." + str(PIPEFORCE_NAMESPACE) + ".svc.cluster.local"
    PIPEFORCE_SVC_HOST_HUB = "hub" + str(PIPEFORCE_SVC_PREFIX)

    # Custom settings here...
