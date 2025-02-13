import pytest
import requests
from unittest.mock import patch
import sys
import os
import shutil

import json
import tempfile

from src.ci_server import build_project

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

    assert response.status_code != 200

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

    # Invalid event
    headers = {"X-GitHub-Event": "pull_request", "Content-Type": "application/json"}
    response = client.post("/webhook", data=json.dumps(payload), headers=headers)

    assert response.status_code == 400

    # Ping event
    headers = {"X-GitHub-Event": "ping", "Content-Type": "application/json"}
    response = client.post("/webhook", data=json.dumps(payload), headers=headers)

    assert response.status_code == 200


@patch("subprocess.run")
def test_clone_repo(mock_subprocess):
    """Test that clone_repo correctly calls git clone"""
    git_url = "https://github.com/Group-19-DD2480/Continuous-Integration-Server.git"
    sha = "abcd1234"
    repo_name = "Continuous-Integration-Server"
    mock_subprocess.return_value = None

    repo_name = git_url.split("/")[-1].replace(".git", "")
    repo_path = os.path.join(
        CLONE_DIR, f"{repo_name}-{sha}"
    )  # This is "/tmp/Continuous-Integration-Server"

    if os.path.exists(repo_path):
        shutil.rmtree(repo_path, ignore_errors=True)

    success, _ = clone_repo(git_url=git_url, sha=sha, repo_name=repo_name)

    assert success is True, "Cloning repo failed"
    mock_subprocess.assert_called_once_with(
        ["git", "clone", git_url, f"/tmp/{repo_name}-{sha}"], check=True
    )

    if os.path.exists(repo_path):
        shutil.rmtree(repo_path, ignore_errors=True)


# @pytest.fixture
# @patch("subprocess.run")
# def test_build_project(mock_subprocess):
def test_build_project():
    valid_python_program = 'print("Hello World")'
    invalid_python_program = "printHello World)"
    files = {"valid": [], "invalid": []}
    valid_dir = tempfile.TemporaryDirectory()
    invalid_dir = tempfile.TemporaryDirectory()

    # valid file in valid directory
    fd, valid_file1 = tempfile.mkstemp(suffix=".py", dir=valid_dir.name, text=True)
    files["valid"].append({"fd": fd, "path": valid_file1})

    # invalid file in invalid dir
    fd, invalid_file1 = tempfile.mkstemp(suffix=".py", dir=invalid_dir.name, text=True)
    files["invalid"].append({"fd": fd, "path": invalid_file1})

    # valid file in invalid dir
    fd, valid_file2 = tempfile.mkstemp(suffix=".py", dir=invalid_dir.name, text=True)
    files["valid"].append({"fd": fd, "path": valid_file2})

    for file in files["valid"] + files["invalid"]:
        os.close(file["fd"])

    for file in files["valid"]:
        with open(file["path"], "w") as f:
            f.write(valid_python_program + "\n")

    for file in files["invalid"]:
        with open(file["path"], "w") as f:
            f.write(invalid_python_program)

    # Path to directory with valid files
    assert build_project(valid_dir.name)

    # Path to directory with some invalid and valid files
    assert not build_project(invalid_dir.name)

    # Pass path to valid file as argument
    assert not build_project(files["valid"][0]["path"])

    # Pass path to invalid file as argument
    assert not build_project(files["invalid"][0]["path"])

    # Pass empty directory as argument
    empty_dir = tempfile.TemporaryDirectory()
    assert build_project(empty_dir.name)


@pytest.fixture
def setup_test_repo_success():
    """Fixture to create a success test repo with test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file_path = os.path.join(temp_dir, "test_sample.py")

        # Create a test file with both passing and failing tests
        test_file_content = """
import pytest

def test_pass1():
    assert True

def test_pass2():
    assert True
"""
        with open(test_file_path, "w") as f:
            f.write(test_file_content)

        yield temp_dir  # Provide the temporary directory path to the test function


@pytest.fixture
def setup_test_repo_failure():
    """Fixture to create a failure test repo with test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file_path = os.path.join(temp_dir, "test_sample.py")

        # Create a test file with both passing and failing tests
        test_file_content = """
import pytest

def test_pass():
    assert True

def test_fail():
    assert False
"""
        with open(test_file_path, "w") as f:
            f.write(test_file_content)

        yield temp_dir  # Provide the temporary directory path to the test function


def test_run_tests(setup_test_repo_success, setup_test_repo_failure):
    """Test run_tests()"""
    repo_path = setup_test_repo_success
    result = run_tests(repo_path)
    assert result, "Expected run_tests() to return True when all tests pass"

    repo_path = setup_test_repo_failure
    result = run_tests(repo_path)
    assert not result, "Expected run_tests() to return False due to a failing test"


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
