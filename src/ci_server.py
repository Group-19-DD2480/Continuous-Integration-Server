from flask import Flask, request, jsonify
import venv
import requests
import subprocess
from dotenv import load_dotenv
import os
import shutil
import sys
from threading import Thread


load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

app = Flask(__name__)

CLONE_DIR = "/tmp/"  # Temporary directory to clone the repo into


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
        if build_project(repo_path) and run_tests(repo_path):
            # Success if cloned and successfully built and tested
            update_github_status(status_url, "success", GITHUB_TOKEN)
            print("message", "Build and tests successful")
            return 200
        else:
            # Failure if cloned but unsuccessfully built or tested
            update_github_status(status_url, "failure", GITHUB_TOKEN)
            print("message", "Build/tests failed")
            return 200

    except Exception:
        # Error if exception is raised during processing
        update_github_status(status_url, "error", GITHUB_TOKEN)
        return 500


def clone_repo(git_url: str, sha: str, repo_name: str) -> (bool, str):
    """
    Clone the GitHub repository into the CLONE_DIR directory

    Parameters:
        git_url (str): The URL of the GitHub repository to clone
        sha (str): The commit SHA to checkout after cloning
        repo_name (str): The name of the repository
    Returns:
        bool: True if the repository was cloned successfully, False otherwise
        str: The path to the cloned repository
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
        print(f"Repo cloned successfully into {repo_path}")
        return True, repo_path
    except subprocess.CalledProcessError as e:
        print(f"Could not clone repo: {e}")
        return False, repo_path


def build_project(path) -> bool:
    """
    Fetches all python files in the directory given by path and runs a compile check on it. Return true if the check succeeds.
    Parameters:
        path: String representing the path to the directory to be compiled.
              An empty directory is considered a valid path and program (returns True)
    Returns:
        bool: True if all python files within the path compile without errors.
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


def run_tests(path: str) -> bool:
    """
    Runs all tests in the given repository path.

    - Using pytest

    Parameters:
        path (str): Path to the cloned repository.

    Returns:
        bool: True if all tests pass, False otherwise.
    """
    # Check if the path exists
    if not os.path.exists(path):
        return False

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
        return False

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
            return False

    # Run the tests using pytest
    test_command = [python_executable, "-m", "pytest"]
    try:
        result = subprocess.run(
            test_command, cwd=path, check=True, capture_output=True, text=True
        )
        print(f"Tests passed!\n{result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Tests failed:\n{e.stdout}\n{e.stderr}")
        return False


def update_github_status(url: str, state: str, github_token: str) -> int:
    headers = {"Authorization": f"token {github_token}"}
    payload = {"state": state, "description": "CI test results", "context": "CI/Test"}

    response = requests.post(url, json=payload, headers=headers)

    return response.status_code


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
