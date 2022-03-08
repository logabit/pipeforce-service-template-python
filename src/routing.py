"""
    Place all your route key to service mappings here.
    Note: Any match will be executed. Also multiple matches are supported. They will be executed by top-down order.
"""

mappings = {
    "pipeforce.webhook.foo.*": "service.hello.HelloService.greeting",
    "pipeforce.webhook.foo.bar": "service.hello.HelloService.greeting2"
}
