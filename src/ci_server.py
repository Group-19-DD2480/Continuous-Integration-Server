from flask import Flask, request, jsonify
import subprocess
import os
import shutil


app = Flask(__name__)

GITHUB_REPO_URL = "https://github.com/Group-19-DD2480/Continuous-Integration-Server.git"
CLONE_DIR = os.path.expanduser("~") + "/tmp/"


@app.route("/webhook", methods=["POST"])
def handle_webhook():
    pass


def clone_repo():
    # Ensure that the clone directory does not exist already
    if os.path.exists(CLONE_DIR):
        shutil.rmtree(CLONE_DIR)

    try:
        # Run the git clone command
        subprocess.run(["git", "clone", GITHUB_REPO_URL, CLONE_DIR], check=True)
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
