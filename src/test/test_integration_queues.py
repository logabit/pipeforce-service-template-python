import requests
from requests.auth import HTTPBasicAuth
BASE_URL = "http://172.24.160.1:15672"
API = BASE_URL + "/api/queues"

def test_status_of_rabbitmq():
    response = requests.get(
        "http://localhost:15672",
        auth=HTTPBasicAuth('guest', 'guest')
    )    
    assert response.status_code == 200    

def test_exists():
    response  = requests.get(
        API + '/foo/2nd Key',
        auth=HTTPBasicAuth('guest', 'guest')
    )    
    assert response.status_code == 200

def test_status_of_queue():
    response = requests.get(
        API + '/foo/2nd Key',
        auth=HTTPBasicAuth('guest', 'guest')
    )   
    resp = response.json()    
    assert resp['state'] == "running"
