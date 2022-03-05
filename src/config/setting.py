import os
from service import hello

# Replace this by your final microservice name
service_name = os.environ['PIPEFORCE_SERVICE']

# This usually comes from the container startup params
namespace = os.environ['PIPEFORCE_NAMESPACE']

# Internal microservice hosts
svc_host_suffix = namespace + ".svc.cluster.local"
svc_host_messaging = "localhost"
svc_host_hub = "hub." + svc_host_suffix

# Messaging queues
queue_name_self = "pipeforce.service." + service_name
queue_name_pipeline = "pipeforce.service.hub"
queue_name_pipeline_response = "pipeforce.service.hub.response"

default_exchange_topic = "pipeforce.topic.default"