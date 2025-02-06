from flask import Flask, request, jsonify
import venv
import os
import subprocess

GITHUB_TOKEN = None

app = Flask(__name__)


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
        cloned, repo_path = clone_repo(clone_url)
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


def clone_repo():
    pass


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

    try:
        venv_dir = os.path.join(path, ".venv")
        venv.create(venv_dir)
        if os.path.exists("requirements.txt"):
            subprocess.run(["pip", "install", "-r", "requirements.txt"])

    except subprocess.CalledProcessError as e:
        print(f"Setting up venv failed: {e.stdout}")
        return False

    command = ["python3", "-m", "py_compile"]
    command.extend(files)
    try:
        subprocess.run(command, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Syntax Check Failed: {e.stderr}")
        return False


def run_tests():
    pass


def update_github_status():
    pass


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
