import requests
import pytest
from requests.auth import HTTPBasicAuth
import os

host = os.environ.get('PIPEFORCE_MESSAGING_HOST')
port = os.environ.get('PIPEFORCE_MESSAGING_PORT')
username = os.environ.get('PIPEFORCE_MESSAGING_USERNAME')
password = os.environ.get('PIPEFORCE_MESSAGING_PASSWORD')


@pytest.fixture
def queries():
    return [
        "device_status_routing_pipeline_eu_routing",
        "device_status_routing_pipeline_monitoring_status_filtering",
        "device_status_routing_pipeline_us_routing",
        "opsgenie_alert_updates_q", "opsgenie_pipeline_update_alert",
        "pipeforce_default_dlq", "salesforce_new_device_monitoring_results_q",
        "salesforce_new_device_status_q"
    ]


@pytest.fixture
def host():
    return (os.environ.get('PIPEFORCE_MESSAGING_HOST'))


@pytest.fixture
def port():
    return (os.environ.get('PIPEFORCE_MESSAGING_PORT'))


@pytest.fixture
def username():
    return (os.environ.get('PIPEFORCE_MESSAGING_USERNAME'))


@pytest.fixture
def password():
    return (os.environ.get('PIPEFORCE_MESSAGING_PASSWORD'))


def test_integration_messaging_queues(queries, host, port, username, password):
    for n in queries:
        response = requests.get('http://' + host + ":" + port + '/api/queues/%2F/' + n,
                                auth=HTTPBasicAuth(username, password))
        resp = response.json()
        assert response.status_code == 200
        assert resp['consumers'] == 0
        assert resp['durable'] == True
        assert resp['exclusive'] == False
        assert resp['type'] == "classic"
