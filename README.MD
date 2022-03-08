# pipeforce-service-template-python

This repo can be used as a base template to write a new microservice in PIPEFORCE. It contains a ready-to-use AMQP
messaging setup with a mapping from message keys to service methods to simplify development and testing.

## Quick Start Guide

### Step 1

Fork this repo to your private or public microservice repo

### Step 2

Create your service modules which can for example contain your process automation logics inside the `src/service/`
folder. See `src/service/hello.py` as an example.

### Step 3

Create a mapping from a message key to your service method in `src/config/routing.py`

In case you would like to start the microservice locally, outside of the cluster, make sure, you set these environment
variables accordingly:

- `PIPEFORCE_SERVICE` - The name of the microservice.
- `PIPEFORCE_NAMESPACE` - The namespace, this microservice runs inside.
- `PIPEFORCE_MESSAGE_BROKER` - The hostname of the message broker to connect to.

When deploying a microservice using the `service.deploy` command, these environment variables will be provided
automatically for you.

### Step 4

After you're finished with development, create a Docker image of your service

```docker build -t <yourimage> .```

### Step 5

Publish your image to your PIPEFORCE image repository. For example:

```
docker tag <yourimage> us-east1-docker.pkg.dev/pipeforce/<namespace>/<yourimage>
docker push us-east1-docker.pkg.dev/pipeforce/<namespace>/<yourimage>
```

Replace `<yourimage>` by the name of your image and `<namespace>` by the name of your PIPEFORCE namespace.

### Step 6

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

**Note: Its highly recommended to automate the steps 4 - 6 using continous deployment toolings!**

## Testing

Make sure you have installed all libs from requirements.txt:

```
> pip3 install -r requirements.txt
```

Place your test scripts inside `src/test` and name the files with suffix `_test.py` and all test methods with
prefix `test_`.

Execute all tests using:

```
> pytest
```