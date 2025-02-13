# Continuous Integration Server

This is a lightweight Continuous Integration (CI) server built using Flask. It listens for GitHub webhook events, clones repositories on push events, runs build and test processes, and updates the commit status on GitHub accordingly.

# Table of Contents

1. [Continuous Integration Server](#continuous-integration-server)
2. [Installation](#installation)
3. [Running the Server](#running-the-server)
4. [SEMAT](#semat)
5. [Contributions](#contributions)

# Installation

### Clone the Repository

```bash
git clone https://github.com/Group-19-DD2480/Continuous-Integration-Server.git
```

### Set up a Virtual Environment

The project was built and tested with python3 version 3.13.1, lower versions may work aswell but are untested.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install Dependencies

The project was built and tested with pip version 24.3.1 lower versions may work aswell but are untested.

```bash
pip install -r requirements.txt
```

### Add authtoken

To update github statuses you need an authtoken, you can create a github personal access token at [github.com/settings/tokens](https://github.com/settings/tokens).

Once you have an authtoken, create the following .env file in the Continuous-Integration-Server directory.

```
GITHUB_TOKEN=$YOUR_AUTHTOKEN
```

### Install and Authenticate Ngrok

The server is run locally, to make it accessible to the internet you can use a tool like Ngrok.  
Download and install Ngrok from [ngrok.com](https://ngrok.com/) or use following command:

```bash
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
  | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
  && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
  | sudo tee /etc/apt/sources.list.d/ngrok.list \
  && sudo apt update \
  && sudo apt install ngrok
```

Without an account, the session expires after two hours. To keep the server running, make a free Ngrok account at [ngrok.com](https://ngrok.com/)  
Once you have an account, get your authtoken from the [dashboard](https://dashboard.ngrok.com/get-started/your-authtoken).  
Authenticate Ngrok with the following command:

```bash
ngrok config add-authtoken $YOUR_AUTHTOKEN
```

Ngrok generates a unique URL each time it is run, with an Ngrok account you can get a static domain from the [dashboard](https://dashboard.ngrok.com/domains).

# Running the Server<a name='running-the-server'></a>

Start the CI server by running ci_server.py

```bash
python3 src/ci_server.py
```

The server uses the default Flask port 5000.
Run Ngrok on port 5000:

```bash
ngrok http --url=$YOUR_DOMAIN 5000
```

For easier startup and shutdown, the server can be run using the following startup script:

```bash
#!/bin/bash

# Activate the virtual environment
source .venv/bin/activate

# Run Python server
python3 src/ci_server.py &
SERVER_PID=$!

# Start ngrok in the background
nohup ngrok http --url=$YOUR_DOMAIN 5000 >/dev/null 2>&1 &
NGROK_PID=$!

# Function to kill both processes on exit
cleanup() {
    echo "Stopping processes..."
    kill $SERVER_PID $NGROK_PID
    deactivate  # Deactivate virtual environment
    exit 0
}

# Trap SIGINT (Ctrl+C) and SIGTERM signals to call cleanup
trap cleanup SIGINT SIGTERM

# Wait for both processes to finish
wait
```

Run the startup script:

```bash
chmod +x start.sh
./start.sh
```

Press Ctrl+C to exit.

### Connecting the Webhook

To connect the webhook open your repo settings and go to the webhook section, click add webhook.  
Set the payload URL to your domain slash webhook: https://example.com/webhook.  
Set the content type to application/json.

### Testing the Server

The server can be tested by running `pytest` from the Continous-Integration-Server directory.

```bash
pytest
```

# SEMAT

At the moment we are in the “Collaborating” state since we have not met all of the requirements listed in the “Performing” state. The following is an overview of our updated checklist for the “Performing” state:

- [x] The team consistently meets its commitments.
- [x] The team continuously adapts to the changing context
- [x] The team identifies and addresses problems without outside help.
- [x] Effective progress is being achieved with minimal avoidable backtracking and reworking.
- [ ] Wasted work and the potential for wasted work are continuously identified and eliminated.
  - At the moment the team does not explicitly and continuously identify wasted work. Instead wasted work is identified in hindsight.

One obstacle to reach the next state is for the team to try to actively and explicitly identify wasted work. To overcome this obstacle the team should establish a framework which describes what wasted work is. Furthermore the team members should also more clearly discuss their current work status in order to prevent two or more people working on the same thing.

# Contributions

**Tore Stenberg ([HermanKassler](https://github.com/HermanKassler)):** Wrote functionality to compile and check the syntax of the code, and wrote the html documentation (while duplicating some stuff from the README)

**Zarko Sesto ([ErzaDuNord](https://github.com/ErzaDuNord)):** Wrote the handle_webhook and process_request functions and corresponding tests

**Erik Smit ([erikgsmit](https://github.com/erikgsmit)):** Wrote clone_repo function and corresponding tests, worked on README.

**Muhammad Usman ([bitGatito](https://github.com/bitGatito)):** Wrote the run_tests function, build history functionality, and corresponding tests.

**Ruben Socha ([RubenSocha](https://github.com/RubenSocha)):** Worked on code skeleton, update_github_status, server hosting, installation and usage docs.
