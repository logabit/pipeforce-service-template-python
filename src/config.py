import os

# pylint: disable=invalid-name
"""
    Default settings for this microservice. Do not change unless you know what you're doing.
"""

# This usually comes from the container/pod startup params
service_name = os.environ['PIPEFORCE_SERVICE']

# This usually comes from the container/pod startup params
namespace = os.environ['PIPEFORCE_NAMESPACE']

# Internal microservice hosts
svc_host_messaging = os.environ['PIPEFORCE_MESSAGE_BROKER']
svc_host_suffix = "." + namespace + ".svc.cluster.local"
svc_host_hub = "hub" + svc_host_suffix

# Messaging settings
queue_name_self = "pipeforce.service." + service_name
default_exchange_topic = "pipeforce.topic.default"
