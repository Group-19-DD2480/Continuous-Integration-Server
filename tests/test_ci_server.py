import pytest
import subprocess
import requests
from unittest.mock import patch
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from ci_server import *


@pytest.fixture
def client():
    app.testing = True
    return app.test_client()


@pytest.mark.skip(reason="Feature not implemented yet")
@patch("ci.clone_repo")
@patch("ci.build_project")
@patch("ci.run_tests")
@patch("ci.update_github_status")
def test_handle_webhook(
    mock_update_status, mock_run_tests, mock_build, mock_clone, client
):
    pass


@pytest.mark.skip(reason="Feature not implemented yet")
@patch("subprocess.run")
def test_clone_repo(mock_subprocess):
    pass


@pytest.mark.skip(reason="Feature not implemented yet")
@patch("subprocess.run")
def test_build_project(mock_subprocess):
    pass


@pytest.mark.skip(reason="Feature not implemented yet")
@patch("subprocess.run")
def test_run_tests(mock_subprocess):
    pass


@patch("requests.post")
@patch("requests.Response")
def test_update_github_status(mock_response, mock_post):
    mock_response.status_code = 201
    mock_post.return_value = mock_response

    status_code = update_github_status(
        url="https://api.github.com/repos/user/repo",
        state="success",
        github_token="token",
    )

    mock_post.assert_called_once_with(
        "https://api.github.com/repos/user/repo",
        json={
            "state": "success",
            "description": "CI test results",
            "context": "CI/Test",
        },
        headers={"Authorization": "token token"},
    )

    assert status_code == mock_response.status_code
