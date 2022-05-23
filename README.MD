# pipeforce-service-template-python

This repo can be used as a base template to write a microservice (= service) in PIPEFORCE using the Python programming language. It
contains a ready-to-use AMQP messaging setup with a mapping from message keys to service methods using the `@event`
decorator to simplify development and testing.

# Quick Start Guide

## Development

### Step 1

Fork or import this repo to your private or public microservice repo and clone it to your local workstation.

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
> export PIPEFORCE_NAMESPACE=local; export PIPEFORCE_SERVICE=myservice; export PIPEFORCE_MESSAGE_BROKER=localhost; python service.py
```

When deploying a microservice using the `service.start` or `service.job.start`command, these environment variables will be provided
automatically for you.

In order to trigger webhooks or other messages to the broker, you can use the scripts inside the `test` folder. Example:

```
> python test/trigger_webhook.py
```

## Build your image

After you're finished with development, create a Docker image of your service:

```docker build -t <yourimage> .```

## Publish your image to the registry

Before you can use the generated image inside the cluster, you need to publish it to your PIPEFORCE image repository.
For example:

```
docker tag <yourimage> us-east1-docker.pkg.dev/pipeforce/<namespace>/<yourimage>
docker push us-east1-docker.pkg.dev/pipeforce/<namespace>/<yourimage>
```

Replace `<yourimage>` by the name of your image and `<namespace>` by the name of your PIPEFORCE namespace.

**Note:** Usually this step is only possible to be executed from your CI/CD system like Jenkins or CircleCI for example, since the credentials to access the registry is usually already provided there. It's not a good practice doing it from your local workspace.

## Deploy your image as service

A service in PIPEFORCE is a long running application which interacts with other services in the cluster.

After your image is available in the registry, you can deploy it into PIPEFORCE as service using the
command [service.start](https://pipeforce.github.io/docs/api/commands#servicestart) inside your online workbench:

``` 
pipeline:  
  - service.start:  
      name: <myservice>
      image: us-east1-docker.pkg.dev/pipeforce/<namespace>/<yourimage>
      port: <port>  
      ingress: <myservice>  
      imagePullSecret: <value> 
```

Or use the [PIPEFORCE CLI](https://github.com/logabit/pipeforce-cli) for this:

```
> pi command service.start name=<myservice> image=us-east1-docker.pkg.dev/pipeforce/<namespace>/<yourimage> port=<port> ingress=<myservice> imagePullSecret=<value> 
```

It will be automatically downloaded and then installed + started inside your PIPEFORCE namespace. If an ingress name is
given, you can access the service finally under ``https://<ingressname>-<namespace>.pipeforce.dev``.

**Note: It's highly recommended automating the build and deployment steps using a CD/CI tool!**

## Deploy your image as job

Differently to a service, a job in PIPEFORCE runs only once and then exits after this.

Jobs are useful for batch processing tasks or running tests for example.

After your image is available in the registry, you can deploy your image into your PIPEFORCE namespace as job using the
command [service.job.start](https://pipeforce.github.io/docs/api/commands#service.job.start) inside your online
workbench:

``` 
pipeline:  
  - service.job.start:  
      name: <myjobname>
      image: us-east1-docker.pkg.dev/pipeforce/<namespace>/<yourimage>
      imagePullSecret: <value> 
      wait: true
```

Or use the [PIPEFORCE CLI](https://github.com/logabit/pipeforce-cli) for this:

```
> pi command service.job.start name=<myjob> image=us-east1-docker.pkg.dev/pipeforce/<namespace>/<yourimage> imagePullSecret=<value> wait=true
```

Your job image will be automatically downloaded and then installed + started inside your PIPEFORCE namespace.

If `wait:true` the command will wait until the job is finished (max. 30 min) and will return the resulting output of the
job. No other job can be started during that time.

In case a longer running job is required, start it in async mode using `wait:false` (default) and check the finish
status of the job using the command `service.job.status` later. You can download the output of the job using the
command `service.job.logs`.

Note: Each job must have a new unique name in order to be able to refer to its logs and status later. So its good
practice to use a counter or date tag for the job name. For example:

```
myjob-run1
myjob-run2
myjob-run3
...
```

## Unit Testing

Make sure you have installed all libs from requirements.txt:

```
> pip3 install -r requirements.txt
```

Place your test scripts inside `src/test` and name the files with suffix `_test.py` and all test methods with
prefix `test_`. Example:

```
src/test/test_hello.py
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

The test additionally contains a linter check to make sure you code complies with best practice Python code styles. See
the `codestyle_test.py` for further details about test integration. In case you would like to run the linter manually,
execute this command:

```
> cd pipeforce-service-template-python
> pylint src
```

Adjust the linter settings in the `.pylintrc` configuration file.

## Integration Testing

While Unit Testing tests single components of the microservice as independent as possible, an Integration Test is the
opposite: It tests the microservice integrated into the environment.

Since Integration Test depend on the microservice to be installed, the integration must also run inside the cluster.

### Creating an Integration Test

Creating an integration test is similar to writing a Unit Test:

Create a new file inside the `src/test` folder but with prefix `test_integration_.py`.

```
src/test/test_integration_hello.py
```

Also any single integration test method must start with prefix `test_integration_`:

```python
def test_integration_greeting():
    # Your integration test goes here...
    ...
```

### Execute the Integration Test

Since the integration test needs to run inside the microservice cluster, you have to create a container image from it
first, deploy it to the cluster and then execute it.

To do so, you can use the existing `Dockerfile` to build and deploy the image as shown above.

This creates a new image and adds the `run-*.sh` scripts to it, so they can be used as entrypoints to execute the tests.

Depending on which entrypoint you define as command, you can run different test types then.

This example runs all integration tests in the cluster and stops after finished:

```yaml
pipeline:
  - service.job.start:
      name: myintegrationtest-run1
      image: pipeforce-registry/myintegrationtest
      command: "./run-tests-integration.sh"
      wait: true
```

Note: Make sure, you have published your image to the registry before as explained above.

Depending on how you wrote your tests, you can run them also locally with your Docker command (outside the cluster):

Example 1: Run integration tests only

```
docker run myintegrationtests ./run-tests-integration.sh
```

Example 2: Run all tests

```
docker run myintegrationtests ./run-tests-all.sh
```

Example 3: Run unit tests only

```
docker run myintegrationtests ./run-tests-unit.sh
```

#### Steps in a nutshell

These are steps required to develop and run integration tests:

##### 1. Create a docker image

```
docker build -t <yourimage> .
```

##### 2. Run your tests inside the docker image (optional and if possible)

```
docker run <yourimage> ./run-tests-**.sh
```

This outputs the JUnit result xml.

##### 3. Publish your docker image to the registry

```
docker tag <yourimage> us-east1-docker.pkg.dev/pipeforce/<namespace>/<yourimage>
docker push us-east1-docker.pkg.dev/pipeforce/<namespace>/<yourimage>
```
This is usually done by your CI/CD tool.

##### 4. Run your test as job inside PIPEFORCE:

```yaml
pipeline:
  - service.job.start:
      name: myintegrationtest-run1
      image: pipeforce-registry/myintegrationtest
      command: "./run-tests-integration.sh"
      wait: true
```

Note the `pipeforce-registry/` prefix in order to indicate to load the image from your PIPEFORCE registry. It's a
shorthand for `us-east1-docker.pkg.dev/pipeforce/`.
