#
# Place all your route key to service mappings here.
#
import service

mappings = {
    "pipeforce.webhook.weclapp.order.*": service.hello.greeting
}
