from flask import Flask, request, jsonify
import subprocess
import os
import shutil


app = Flask(__name__)

CLONE_DIR = "/tmp/"  # Temporary directory to clone the repo into


@app.route("/webhook", methods=["POST"])
def handle_webhook():
    pass


def clone_repo(git_url: str):
    """
    Clone the GitHub repository into the CLONE_DIR directory

    Parameters:
        git_url (str): The URL of the GitHub repository to clone
    Returns:
        bool: True if the repository was cloned successfully, False otherwise
    """
    # Ensure that the clone directory does not exist already
    repo_name = git_url.split("/")[-1].replace(".git", "")
    repo_path = os.path.join(CLONE_DIR, repo_name)

    # Try removing existing repo
    if os.path.exists(repo_path):
        try:
            shutil.rmtree(repo_path)
            print(f"✅ Deleted existing repo: {repo_path}")
        except PermissionError:
            print(f"⚠️ Permission denied: Could not delete {repo_path}")
            return False

    try:
        # Run the git clone command
        subprocess.run(["git", "clone", git_url], cwd=CLONE_DIR, check=True)
        print(f"✅ Repo cloned successfully into {repo_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Could not clone repo: {e}")
        return False


def build_project():
    pass


def run_tests():
    pass


def update_github_status():
    pass


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
