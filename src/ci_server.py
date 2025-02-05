from flask import Flask, request, jsonify
import requests
import subprocess


app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
def handle_webhook():
    pass


def clone_repo():
    pass


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
