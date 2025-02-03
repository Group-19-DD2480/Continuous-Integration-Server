from flask import Flask, request, jsonify
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


def update_github_status():
    pass


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
