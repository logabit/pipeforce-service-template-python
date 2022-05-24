#This unittest is created to just get idea before implementing the integration test to check all tests are running or not

BASE_URL = "http://localhost:15672/api/"
API = BASE_URL + "queues"
import requests
from requests.auth import HTTPBasicAuth
import HtmlTestRunner

import unittest

def statuscheck():
    response = requests.get(
        "http://localhost:15672",
        auth=HTTPBasicAuth('guest', 'guest')
    )
    return response.status_code

def existcheck():
    response  = requests.get(
        API + '/foo/2nd Key',
        auth=HTTPBasicAuth('guest', 'guest')
    )
    return response.status_code

def statusofqueue():
    response = requests.get(
        API + '/foo/2nd Key',
        auth=HTTPBasicAuth('guest', 'guest')
    )   
    resp = response.json()
    return resp['state']

class TestCalc(unittest.TestCase):
    def test_status_of_rabbitme(self):
        self.assertEqual(statuscheck(),200)
    def test_queue_exist(self):
        self.assertEqual(existcheck(),200)
    def test_status_of_queue(self):
        self.assertEqual(statusofqueue(),'running')

if __name__ == '__main__':
    unittest.main(testRunner=HtmlTestRunner.HTMLTestRunner(output='D:/Logabit/pipeforce-service-template-python-1/src/test'))

