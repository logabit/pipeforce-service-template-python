#
# Place all your route key to service mappings here.
#

from service import hello

mappings = {
    "pipeforce.webhook.weclapp.order.*": hello.greeting
}
