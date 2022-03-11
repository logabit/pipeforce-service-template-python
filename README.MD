# pipeforce-service-template-python

This repo can be used as a base template to write a microservice in PIPEFORCE using the Python programming language. It
contains a ready-to-use AMQP messaging setup with a mapping from message keys to service methods using the `@event`
decorator to simplify development and testing.

# Quick Start Guide

## Development

### Step 1

Fork this repo to your private or public microservice repo and clone it to your local workstation.

### Step 2

Create a service class which can for example contain your process automation logics inside the `src/service/`
folder. See `src/service/hello.py` as an example:

```python
from pipeforce import BaseService, event


class HelloService(BaseService):

    @event("some.event.key.*")
    def greeting(self, body):
        print("GREETING CALLED. BODY: " + str(body))

```

Note here the `@event` decorator which creates a mapping from a message event key to the service method. Whenever a
message is sent to the topic `pipeforce.topic.default` matching this key, this service method will be executed. The
payload of the message is given as body argument. In the event key you can use any wildcard pattern like * and #
supported by RabbitMQ:
https://www.rabbitmq.com/tutorials/tutorial-five-python.html

### Step 3

For development, you can start a local RabbitMQ broker as Docker container like this example shows:

```
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.9-management
```

The management web-ui can be accessed via http://localhost:15672/ (guest/guest)

In case you would like to start the microservice locally, outside the cluster, make sure, you set these environment
variables accordingly:

- `PIPEFORCE_SERVICE` - The name of the microservice. Can be anything when running outside of the cluster.
- `PIPEFORCE_NAMESPACE` - The namespace, this microservice runs inside. Can be anything when running outside of the
  cluster.
- `PIPEFORCE_MESSAGE_BROKER` - The hostname of the message broker to connect to. Should be usually `localhost` when
  running outside of the cluster.

To start the microservice locally and let it listen to messages, use this command on Mac/Linux:

```
> export PIPEFORCE_NAMESPACE=local; export PIPEFORCE_SERVICE=myservice; export PIPEFORCE_MESSAGE_BROKER=localhost; python start.py
```

When deploying a microservice using the `service.deploy` command, these environment variables will be provided
automatically for you.

In order to trigger webhooks or other messages to the broker, you can use the scripts inside the `test` folder. Example:

```
> python test/trigger_webhook.py
```

## Build + Deployment

### Step 1

After you're finished with development, create a Docker image of your service

```docker build -t <yourimage> .```

### Step 2

Publish your image to your PIPEFORCE image repository. For example:

```
docker tag <yourimage> us-east1-docker.pkg.dev/pipeforce/<namespace>/<yourimage>
docker push us-east1-docker.pkg.dev/pipeforce/<namespace>/<yourimage>
```

Replace `<yourimage>` by the name of your image and `<namespace>` by the name of your PIPEFORCE namespace.

### Step 3

Deploy your service into your PIPEFORCE namespace using the
command [service.deploy](https://pipeforce.github.io/docs/api/commands#servicedeploy) inside your online workbench:

``` 
pipeline:  
  - service.deploy:  
      name: <myservice>
      image: us-east1-docker.pkg.dev/pipeforce/<namespace>/<yourimage>
      port: <port>  
      ingress: <myservice>  
      imagePullSecret: <value> 
```

Or use the [PIPEFORCE CLI](https://github.com/logabit/pipeforce-cli) for this:

```
> pi command service.deploy name=<myservice> image=us-east1-docker.pkg.dev/pipeforce/<namespace>/<yourimage> port=<port> ingress=<myservice> imagePullSecret=<value> 
```

It will be automatically downloaded and then installed + started inside your PIPEFORCE namespace. If an ingress name is
given, you can access the service finally under ``https://<ingressname>-<namespace>.pipeforce.dev``.

**Note: Its highly recommended to automate the build and deployment steps using a CD/CI tool!**

## Testing

Make sure you have installed all libs from requirements.txt:

```
> pip3 install -r requirements.txt
```

Place your test scripts inside `src/test` and name the files with suffix `_test.py` and all test methods with
prefix `test_`. Example:

```
src/test/hello_test.py
```

```python
def test_greeting():
    # Your test goes here...
    ...
```

Its good practise that for every service method there exists at least one test, whenever possible.

Execute all tests using:

```
> cd pipeforce-service-template-python
> pytest
```

The tool `pytest` will collect all tests and executes them.

**Note**: The test additionally contains a linter check to make sure you code complies with best practice Python code
styles. See the `codestyle_test.py` for further details about test integration. In case you would like to run the linter
manually, execute this command:

```
> cd pipeforce-service-template-python
> pylint src
```

Adjust the linter settings in the `.pylintrc` configuration file.