import pytest
import subprocess
from unittest.mock import patch
import sys
import os
import shutil


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


@patch("subprocess.run")
def test_clone_repo(mock_subprocess):
    mock_subprocess.return_value = None

    # Ensure that the clone directory does not exist already
    if os.path.exists(CLONE_DIR):
        shutil.rmtree(CLONE_DIR)

    success = clone_repo()

    assert success is True, "Cloning repo failed"
    mock_subprocess.assert_called_once_with(
        ["git", "clone", GITHUB_REPO_URL, CLONE_DIR], check=True
    )

    # Cleanup
    if os.path.exists(CLONE_DIR):
        shutil.rmtree(CLONE_DIR)


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
