import requests
import pytest
from requests.auth import HTTPBasicAuth
import os

host = os.environ.get("PIPEFORCE_MESSAGING_HOST")
port = os.environ.get("PIPEFORCE_MESSAGING_PORT")
username = os.environ.get("PIPEFORCE_MESSAGING_USERNAME")
password = os.environ.get("PIPEFORCE_MESSAGING_PASSWORD")


@pytest.fixture
def queries():
    return {
        "": {
            "durable": True,
            "type": "direct"
        },
        "amq.direct": {
            "durable": True,
            "type": "direct"
        },
        "amq.fanout": {
            "durable": True,
            "type": "fanout"
        },
        "amq.headers": {
            "durable": True,
            "type": "headers"
        },
        "amq.match": {
            "durable": True,
            "type": "headers"
        },
        "amq.rabbitmq.trace": {
            "durable": True,
            "type": "topic"
        },
        "pipeforce.default.topic": {
            "durable": True,
            "type": "topic"
        }
    }


@pytest.fixture
def host():
    return os.environ.get("PIPEFORCE_MESSAGING_HOST")


@pytest.fixture
def port():
    return os.environ.get("PIPEFORCE_MESSAGING_PORT")


@pytest.fixture
def username():
    return os.environ.get("PIPEFORCE_MESSAGING_USERNAME")


@pytest.fixture
def password():
    return os.environ.get("PIPEFORCE_MESSAGING_PASSWORD")


def test_integration_messaging_exchange(host, port, username, password, queries):
    response = requests.get('http://' + host + ':' + port + '/api/exchanges',
                            auth=HTTPBasicAuth(username, password))
    resp = response.json()
    if len(resp) <= 9:
        for data in resp:
            name = data["name"]
            print("name ", name)
            if (name in [
                    "", "amq.direct", "amq.fanout", "amq.headers", "amq.match",
                    "amq.rabbitmq.trace", "pipeforce.default.topic"
            ] and data["vhost"] == "/"):
                print("came inside")
                assert name in queries.keys()
                assert data["durable"] == queries[data["name"]]["durable"]
                assert data["type"] == queries[data["name"]]["type"]
            else:
                print("name == ", name)
                assert False
    else:
        raise ValueError("Length issue")
