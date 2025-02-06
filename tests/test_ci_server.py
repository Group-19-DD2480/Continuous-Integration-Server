import pytest
import subprocess
from unittest.mock import patch
import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from ci_server import *


@pytest.fixture
def client():
    app.testing = True
    return app.test_client()


@patch("ci_server.clone_repo")
@patch("ci_server.build_project")
@patch("ci_server.run_tests")
@patch("ci_server.update_github_status")
def test_handle_webhook(
    mock_update_status, mock_run_tests, mock_build, mock_clone, client
):
    # Passing commit
    mock_clone.return_value = (True, "/repo/path")
    mock_build.return_value = True
    mock_run_tests.return_value = True

    payload = {
        "repository": {
            "clone_url": "https://github.com/example/repo.git",
            "owner": {"login": "example"},
            "name": "repo",
        },
        "after": "abcd1234",
    }

    headers = {"X-GitHub-Event": "push", "Content-Type": "application/json"}

    response = client.post("/webhook", data=json.dumps(payload), headers=headers)

    mock_update_status.assert_any_call(
        "https://api.github.com/repos/example/repo/statuses/abcd1234",
        "pending",
        GITHUB_TOKEN,
    )
    mock_clone.assert_any_call(
        "https://github.com/example/repo.git", "abcd1234", "repo"
    )
    mock_build.assert_any_call("/repo/path")
    mock_run_tests.assert_any_call("/repo/path")
    mock_update_status.assert_any_call(
        "https://api.github.com/repos/example/repo/statuses/abcd1234",
        "success",
        GITHUB_TOKEN,
    )

    assert response.status_code == 200

    # Test failing commit
    mock_run_tests.return_value = False
    response = client.post("/webhook", data=json.dumps(payload), headers=headers)

    mock_update_status.assert_any_call(
        "https://api.github.com/repos/example/repo/statuses/abcd1234",
        "pending",
        GITHUB_TOKEN,
    )
    mock_clone.assert_any_call(
        "https://github.com/example/repo.git", "abcd1234", "repo"
    )
    mock_build.assert_any_call("/repo/path")
    mock_run_tests.assert_any_call("/repo/path")
    mock_update_status.assert_any_call(
        "https://api.github.com/repos/example/repo/statuses/abcd1234",
        "failure",
        GITHUB_TOKEN,
    )

    assert response.status_code == 200

    # Build failing commit
    mock_build.return_value = False
    mock_run_tests.return_value = True
    response = client.post("/webhook", data=json.dumps(payload), headers=headers)

    mock_update_status.assert_any_call(
        "https://api.github.com/repos/example/repo/statuses/abcd1234",
        "pending",
        GITHUB_TOKEN,
    )
    mock_clone.assert_any_call(
        "https://github.com/example/repo.git", "abcd1234", "repo"
    )
    mock_build.assert_any_call("/repo/path")
    mock_update_status.assert_any_call(
        "https://api.github.com/repos/example/repo/statuses/abcd1234",
        "failure",
        GITHUB_TOKEN,
    )

    assert response.status_code == 200

    # Clone failing commit
    mock_clone.return_value = (False, None)
    mock_build.return_value = True
    mock_run_tests.return_value = True
    response = client.post("/webhook", data=json.dumps(payload), headers=headers)

    mock_update_status.assert_any_call(
        "https://api.github.com/repos/example/repo/statuses/abcd1234",
        "pending",
        GITHUB_TOKEN,
    )
    mock_clone.assert_any_call(
        "https://github.com/example/repo.git", "abcd1234", "repo"
    )
    mock_update_status.assert_any_call(
        "https://api.github.com/repos/example/repo/statuses/abcd1234",
        "error",
        GITHUB_TOKEN,
    )

    assert response.status_code == 500

    # Invalid request commit
    headers = {"X-GitHub-Event": "pull_request", "Content-Type": "application/json"}
    response = client.post("/webhook", data=json.dumps(payload), headers=headers)

    assert response.status_code == 400


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


@pytest.mark.skip(reason="Feature not implemented yet")
@patch("requests.post")
def test_update_github_status(mock_post):
    pass
