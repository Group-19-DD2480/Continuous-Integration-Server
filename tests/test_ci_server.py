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
    """Test that clone_repo correctly calls git clone"""
    git_url = "https://github.com/Group-19-DD2480/Continuous-Integration-Server.git"
    mock_subprocess.return_value = None

    repo_name = git_url.split("/")[-1].replace(".git", "")
    repo_path = os.path.join(
        CLONE_DIR, repo_name
    )  # This is "/tmp/Continuous-Integration-Server"

    if os.path.exists(repo_path):
        shutil.rmtree(repo_path, ignore_errors=True)

    success = clone_repo(git_url=git_url)

    assert success is True, "Cloning repo failed"
    mock_subprocess.assert_called_once_with(
        ["git", "clone", git_url], cwd=CLONE_DIR, check=True
    )

    if os.path.exists(repo_path):
        shutil.rmtree(repo_path, ignore_errors=True)


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
