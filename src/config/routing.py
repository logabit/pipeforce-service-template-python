#
# Place all your route key to service mappings here.
# Note: Any match will be executed. Also multiple matches. Matches are checked from top to down.
#
import service.hello

mappings = {
    "pipeforce.webhook.foo.*": service.hello.greeting,
    "pipeforce.webhook.foo.bar": service.hello.greeting2
}
