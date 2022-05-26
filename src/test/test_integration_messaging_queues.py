import requests
import pytest
from requests.auth import HTTPBasicAuth
import os
host = os.environ.get('PIPEFORCE_MESSAGING_HOST')
port = os.environ.get('PIPEFORCE_MESSAGING_PORT')
username = os.environ.get('PIPEFORCE_MESSAGING_USERNAME')
password = os.environ.get('PIPEFORCE_MESSAGING_PASSWORD')

@pytest.fixture
def name():
    return ["test-queue"]

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

class TestMessagingQueues(object):
    def test_integration_messaging_queues(self, name, host, port, username, password):
        for n in name:  
            response = requests.get(
                'http://'+host+':'+port+'/api/queues/%2F/'+n,                
                auth=HTTPBasicAuth(username, password)
            )    
            resp = response.json()            
            assert response.status_code == 200
            assert resp['consumers'] == 0
            assert resp['durable'] == True
            assert resp['exclusive'] == False
            assert resp['type'] == "classic"


    

