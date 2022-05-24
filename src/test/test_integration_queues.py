#This is the integration test file which i'm working on it now

import sys
sys.path.insert(1, 'D:/Logabit/pipeforce-service-template-python-1/src/service')
sys.path.append("../service/")
import main


def test_statuscheck():
    assert main.statuscheck() == 200
    assert main.existcheck() == 200
    assert main.statusofqueue == 'running'

