from flask import Flask, request, jsonify
import requests
import subprocess
import os
import shutil

GITHUB_TOKEN = None

app = Flask(__name__)

CLONE_DIR = "/tmp/"  # Temporary directory to clone the repo into


@app.route("/webhook", methods=["POST"])
def handle_webhook():

    # Only handle push events
    event = request.headers.get("X-GitHub-Event", "")
    content_type = request.headers.get("Content-Type", "")
    if event != "push":
        return {"error": "Invalid event type"}, 400
    if content_type != "application/json":
        return {"error": "Invalid content type"}, 400
    payload = request.get_json()

    # Format the response url
    clone_url = payload["repository"]["clone_url"]
    repo_owner = payload["repository"]["owner"]["login"]
    repo_name = payload["repository"]["name"]
    commit_sha = payload["after"]
    status_url = (
        f"https://api.github.com/repos/{repo_owner}/{repo_name}/statuses/{commit_sha}"
    )

    # Set as pending while processing
    update_github_status(status_url, "pending", GITHUB_TOKEN)

    try:
        # Try cloning the repo
        cloned, repo_path = clone_repo(clone_url, commit_sha, repo_name)
        if not cloned:
            update_github_status(status_url, "error", GITHUB_TOKEN)
            return {"error": "Cloning failed"}, 500

        # Try building and testing the repo
        if build_project(repo_path) and run_tests(repo_path):
            # Success if cloned and successfully built and tested
            update_github_status(status_url, "success", GITHUB_TOKEN)
            return {"message": "Build and tests successful"}, 200
        else:
            # Failure if cloned but unsuccessfully built or tested
            update_github_status(status_url, "failure", GITHUB_TOKEN)
            return {"message": "Build and tests successful"}, 200

    except Exception as e:
        # Error if exception is raised during processing
        update_github_status(status_url, "error", GITHUB_TOKEN)
        return {"error": f"Building/Testing error: {str(e)}"}, 500


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
        subprocess.run(["git", "clone", git_url], cwd=CLONE_DIR, check=True)
        print(f"Repo cloned successfully into {repo_path}")
        return True, repo_path
    except subprocess.CalledProcessError as e:
        print(f"Could not clone repo: {e}")
        return False, repo_path


def build_project():
    pass


def run_tests():
    pass


def update_github_status(url: str, state: str, github_token: str) -> int:
    headers = {"Authorization": f"token {github_token}"}
    payload = {"state": state, "description": "CI test results", "context": "CI/Test"}

    response = requests.post(url, json=payload, headers=headers)

    return response.status_code


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
