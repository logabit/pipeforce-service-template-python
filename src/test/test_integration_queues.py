import requests
import pytest
from requests.auth import HTTPBasicAuth
import os
host = os.environ.get('PIPEFORCE_MESSAGING_HOST')
port = os.environ.get('PIPEFORCE_MESSAGING_PORT')
username = os.environ.get('PIPEFORCE_MESSAGING_USERNAME')
password = os.environ.get('PIPEFORCE_MESSAGING_PASSWORD')

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

def test_status_of_rabbitmq(host, port, username, password):    
    response = requests.get(
         'http://'+host+':'+port,        
        auth=HTTPBasicAuth(username, password)
    )    
    assert response.status_code == 200

def test_exists(host, port, username, password):
    response  = requests.get(
        'http://'+host+':'+port+'/api/queues/%2F/2ndKey',
        auth=HTTPBasicAuth(username, password)
    )    
    assert response.status_code == 200
 
def test_status_of_queue(host, port, username, password):
    response = requests.get(
        'http://'+host+':'+port+'/api/queues/%2F/2ndKey',       
        auth=HTTPBasicAuth(username, password)
    )   
    resp = response.json()    
    assert resp['state'] == "running"
