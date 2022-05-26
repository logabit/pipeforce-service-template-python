BASE_URL = "http://localhost:15672/api/"
API = BASE_URL + "queues"
import requests
from requests.auth import HTTPBasicAuth


#It will check the status of the rabbitMQ, is it running or not!
def statuscheck():
    response = requests.get(
        "http://localhost:15672",
        auth=HTTPBasicAuth('guest', 'guest')
    )
    return response.status_code


#This will check that the queue is exist or not!
def existcheck():
    response  = requests.get(
        API + '/foo/2nd Key',
        auth=HTTPBasicAuth('guest', 'guest')
    )
    return response.status_code

# This will check the status of the queue
def statusofqueue():
    response = requests.get(
        API + '/foo/2nd Key',
        auth=HTTPBasicAuth('guest', 'guest')
    )   
    resp = response.json()
    return resp['state']




