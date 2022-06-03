import pytest

from src.config import Config
from src.pipeforce import PipeforceClient


def test_client_config_empty():
    """
    Test that setting no namespace or instance causes an error.
    :return:
    """

    with pytest.raises(ValueError, match="Config PIPEFORCE_NAMESPACE or PIPEFORCE_INSTANCE is required!"):
        config = Config()
        PipeforceClient(config)


def test_client_config_minimal():
    """
    Test with minimal settings and makre sure all other required values are calculated correctly.
    :return:
    """
    config = Config()
    config.PIPEFORCE_NAMESPACE = "somens"
    config.PIPEFORCE_SERVICE = "myservice"
    client = PipeforceClient(config)

    assert client.config.PIPEFORCE_INSTANCE == "myservice.svc.cluster.local"
    assert client.config.PIPEFORCE_HUB_URL == "http://hub.somens.svc.cluster.local"


def test_client_access_token_from_basic(mocker):
    """
    Create access token from given secret.
    :param mocker:
    :return:
    """
    config = Config()
    config.PIPEFORCE_NAMESPACE = "somens"
    config.PIPEFORCE_SERVICE = "myservice"
    config.PIPEFORCE_SECRET = "Basic someUsername:somePass"

    client = PipeforceClient(config)

    def do_post_mocked(self, url, json, headers={}):
        if url.endswith("iam.token"):
            assert json["username"] == "someUsername"
            assert json["password"] == "somePass"
            return {"refresh_token": "someRefreshToken"}
        return {"access_token": "someAccessToken", "expires_in": 300}

    mocker.patch("src.pipeforce.PipeforceClient.do_post", do_post_mocked)

    token = client.get_pipeforce_access_token()
    assert token == "someAccessToken"


def test_client_access_token_from_apitoken(mocker):
    """
    Create access token from given secret.
    :param mocker:
    :return:
    """
    config = Config()
    config.PIPEFORCE_NAMESPACE = "somens"
    config.PIPEFORCE_SERVICE = "myservice"
    config.PIPEFORCE_SECRET = "Apitoken someApitoken"

    client = PipeforceClient(config)

    def do_post_mocked(self, url, json, headers={}):
        assert url.endswith("iam.token.refresh")
        return {"access_token": "someAccessToken", "expires_in": 300}

    mocker.patch("src.pipeforce.PipeforceClient.do_post", do_post_mocked)

    token = client.get_pipeforce_access_token()
    assert token == "someAccessToken"
