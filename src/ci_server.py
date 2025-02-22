from flask import Flask, request, jsonify, render_template
import venv
import requests
import subprocess
from dotenv import load_dotenv
import os
import shutil
from threading import Thread
import sys

import sqlite3

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from db import *
import datetime

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

app = Flask(__name__)

CLONE_DIR = "/tmp/"  # Temporary directory to clone the repo into


@app.route("/documentation")
def documentation_view():
    return render_template("../docs/html/index.html")


@app.route("/builds")
def builds_view():
    db = get_db()
    builds = get_builds(db)
    close_db()
    return render_template("builds.html", builds=builds)


@app.route("/build/<int:build_id>", methods=["GET"])
def build_view(build_id):
    db = get_db()
    build = get_build(db, build_id)
    close_db()
    if build is None:
        return {"error": "Build not found"}, 404
    return render_template("build.html", build=build)


@app.route("/webhook", methods=["POST"])
def handle_webhook():
    """
    Recieves webhook requests and handles pings and invalid requests.
    Valid requests are proceessed in a separate thread.

    :return: Dictionary with a message responding to the request
    :return: Status code of the request
    :rtype: (dict, int)
    """

    event = request.headers.get("X-GitHub-Event", "")
    content_type = request.headers.get("Content-Type", "")

    # Respond to pings
    if event == "ping":
        return {"message": "Server running"}, 200

    # Handle push events
    if event != "push":
        return {"error": "Invalid event type"}, 400
    if content_type != "application/json":
        return {"error": "Invalid content type"}, 400
    payload = request.get_json()

    # Format the response url
    repo_owner = payload["repository"]["owner"]["login"]
    repo_name = payload["repository"]["name"]
    commit_sha = payload["after"]
    status_url = (
        f"https://api.github.com/repos/{repo_owner}/{repo_name}/statuses/{commit_sha}"
    )

    # Set as pending while processing
    update_github_status(status_url, "pending", GITHUB_TOKEN)
    thread = Thread(target=process_request, args=(payload,))
    thread.start()
    return {"message": "Processing started"}, 202


def process_request(payload: dict) -> int:
    """
    Processes webhook push event request.

    :param payload: The json payload of the request
    :type payload: dict

    :return: Status code of the request, 200 on success, 500 on fail
    :rtype: int
    """
    clone_url = payload["repository"]["clone_url"]
    repo_owner = payload["repository"]["owner"]["login"]
    repo_name = payload["repository"]["name"]
    commit_sha = payload["after"]
    status_url = (
        f"https://api.github.com/repos/{repo_owner}/{repo_name}/statuses/{commit_sha}"
    )
    print("\n\n\n", status_url, "\n\n\n")
    try:
        # Try cloning the repo
        cloned, repo_path = clone_repo(clone_url, commit_sha, repo_name)
        if not cloned:
            update_github_status(status_url, "error", GITHUB_TOKEN)
            print("error", "Cloning failed")
            return 500

        # Try building and testing the repo
        tests, testsOutput = run_tests(repo_path)

        if build_project(repo_path) and tests:
            # Success if cloned and successfully built and tested
            update_github_status(status_url, "success", GITHUB_TOKEN)
            try:
                with app.app_context():
                    db_conn = get_db()
                    insert_build(
                        db_conn,
                        commit_sha,
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "success",
                        testsOutput,
                    )
            except sqlite3.Error as e:
                print("Database error:", e)
            print("message", "Build and tests successful")
            return 200
        else:
            # Failure if cloned but unsuccessfully built or tested
            update_github_status(status_url, "failure", GITHUB_TOKEN)
            try:
                with app.app_context():
                    db_conn = get_db()
                    insert_build(
                        db_conn,
                        commit_sha,
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "failure",
                        testsOutput,
                    )
            except sqlite3.Error as e:
                print("Database error:", e)
            print("message", "Build/tests failed")
            return 200

    except Exception as e:
        # Error if exception is raised during processing
        update_github_status(status_url, "error", GITHUB_TOKEN)
        print("error", e)
        return 500


def clone_repo(git_url: str, sha: str, repo_name: str) -> (bool, str):
    """
    Clone the GitHub repository into the CLONE_DIR directory

    :param git_url: The URL of the GitHub repository to clone
    :type git_url: str
    :param sha: The commit SHA to checkout after cloning
    :type sha: str
    :param repo_name: The name of the repository
    :type repo_name: str

    :return: True if the repository was cloned successfully, False otherwise
    :return: The path to the cloned repository
    :rtype: (bool, str)
    """
    # Ensure that the clone directory does not exist already
    repo_path = os.path.join(CLONE_DIR, f"{repo_name}-{sha}")

    # Try removing existing repo
    if os.path.exists(repo_path):
        try:
            shutil.rmtree(repo_path)
            print(f"Deleted existing repo: {repo_path}")
        except PermissionError:
            print(f"Permission denied: Could not delete {repo_path}")
            return False, repo_path

    try:
        # Run the git clone command
        subprocess.run(["git", "clone", git_url, repo_path], check=True)
        subprocess.run(["git", "checkout", sha], cwd=repo_path, check=True)
        print(f"Repo cloned successfully into {repo_path}")
        return True, repo_path
    except subprocess.CalledProcessError as e:
        print(f"Could not clone repo: {e}")
        return False, repo_path


def build_project(path: str) -> bool:
    """
    Fetches all python files in the directory given by path and runs a compile check on it. Return true if the check succeeds.

    :param path: String representing the path to the directory to be compiled.
                An empty directory is considered a valid path and program (returns True)
    :type path: str
    :returns: True if all python files within the path compile without errors.
              False if any file compile with an error, path is not directory or the path does not exist.
    """

    files = []
    if not os.path.exists(path):
        return False

    if not os.path.isdir(path):
        return False

    if not os.listdir(path):
        # Directory is Empty
        return True

    if os.path.isdir(path):
        for dirpath, _, filenames in os.walk(path):
            for file in filenames:
                if file.endswith(".py"):
                    files.append(dirpath + "/" + file)

    # Create a virtual environment in the directory
    try:
        venv_dir = os.path.join(path, ".venv")
        venv.create(venv_dir)
    except subprocess.CalledProcessError as e:
        print(f"Creating venv failed: {e.stdout}")
        return False

    # Choose the correct python executable based on the OS
    if os.name == "nt":
        python_executable = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        python_executable = os.path.join(venv_dir, "bin", "python")

    # Ensure pip is installed in the virtual environment, install pip otherwise
    subprocess.run(
        [python_executable, "-m", "ensurepip"],
        cwd=path,
        check=True,
    )

    # Install the requirements.txt file if it exists
    if os.path.exists("requirements.txt"):
        try:
            subprocess.run(
                [python_executable, "-m", "pip", "install", "-r", "requirements.txt"],
                cwd=path,  # Make sure the command runs in the directory containing requirements.txt
                check=True,
            )
            print("Requirements installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install requirements: {e}")

    # Run the compile check on all python files
    command = [python_executable, "-m", "py_compile"]
    command.extend(files)
    try:
        subprocess.run(command, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Syntax Check Failed: {e.stderr}")
        return False


def run_tests(path: str) -> tuple[bool, str]:
    """
    Runs all tests in the given repository path.

    - Using pytest

    :param path: Path to the cloned repository.
    :type path: str

    :returns: True if all tests pass, False otherwise.
    :rtype: bool
    """
    # Check if the path exists
    if not os.path.exists(path):
        return False, "Path does not exist."

    # Determine the virtual environment directory path
    venv_dir = os.path.join(path, ".venv")
    if not os.path.exists(venv_dir):
        venv.create(venv_dir)

    # Activate the virtual environment according to the OS
    if os.name == "nt":
        python_executable = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        python_executable = os.path.join(venv_dir, "bin", "python")

    # Check if the python executable exists
    if not os.path.exists(python_executable):
        print(f"Error: Python executable not found at {python_executable}")
        return False, "Python executable not found."

    # Ensure pip is installed in the virtual environment
    subprocess.run(
        [python_executable, "-m", "ensurepip"],
        cwd=path,
        check=True,
    )

    # Install the requirements.txt file if it exists
    try:
        subprocess.run(
            [python_executable, "-m", "pip", "install", "-r", "requirements.txt"],
            cwd=path,  # Make sure the command runs in the directory containing requirements.txt
            check=True,
        )
        print("Requirements installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install requirements: {e}")

    # Check if pytest is installed in the environment
    try:
        subprocess.run(
            [python_executable, "-m", "pytest", "--version"],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"pytest not found in the environment: {e.stderr}")
        try:
            subprocess.run(
                [python_executable, "-m", "pip", "install", "pytest"],
                check=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"Failed to install pytest:\n{e.stderr}")
            return False, "Failed to install pytest."

    # Run the tests using pytest
    test_command = [python_executable, "-m", "pytest"]
    try:
        result = subprocess.run(
            test_command, cwd=path, check=True, capture_output=True, text=True
        )
        print(f"Tests passed!\n{result.stdout}")
        return (True, result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Tests failed:\n{e.stdout}\n{e.stderr}")
        error = e.stdout + e.stderr
        return (False, error)


def update_github_status(url: str, state: str, github_token: str) -> int:
    """
    Updates the status of a commit on github.

    This function sends a commit status update to github using the Statuses API.
    The status can be one of the following: "success", "failure", "pending", or "error".

    :param url: The github API endpoint for updating commit statuses.
    :type url: str
    :param state: The status to be sent to github. Must be one of: "success", "failure", "pending", or "error".
    :type state: str
    :param github_token: The authentication token used to access the github API.
    :type github_token: str

    :return: The HTTP status code returned by github.
    :rtype: int
    """
    headers = {"Authorization": f"token {github_token}"}
    payload = {"state": state, "description": "CI test results", "context": "CI/Test"}

    response = requests.post(url, json=payload, headers=headers)

    return response.status_code


if __name__ == "__main__":
    initialise_db()
    app.run(host="127.0.0.1", port=5000)
