Installation
============

Clone the Repo
---------------

Clone the repo to your local machine::

   git clone https://github.com/Group-19-DD2480/Continuous-Integration-Server.git


Set up virtual environment
---------------------------
Create and activate a python virtual environmen::
   
   python3 -m venv .venv 
   source .venv/bin/activate

Install Dependencies 
-----------------------
::

   pip install -r requirements.txt

Add Authtoken
----------------
To update github statuses you need an authtoken, you can create a github personal access token at https://github.com/settings/tokens.

Once you have an authtoken, create the following .env file in the Continuous-Integration-Server directory. ::

   GITHUB_TOKEN=$YOUR_AUTHTOKEN

Install and Authenticate ngrok
--------------------------------
The server is run locally, to make it accessible  to the internet you can use a tool like Ngrok.  
Download and install Ngrok from: https://ngrok.com/ or use following command: ::


   curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
     | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
     && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
     | sudo tee /etc/apt/sources.list.d/ngrok.list \
     && sudo apt update \
     && sudo apt install ngrok

Without an account, the session expires after two hours. To keep the server running, make a free Ngrok account at https://ngrok.com/  
Once you have an account, get your authtoken from the https://dashboard.ngrok.com/get-started/your-authtoken.  


Authenticate Ngrok with the following command: ::

   ngrok config add-authtoken $YOUR_AUTHTOKEN

Ngrok generates a unique URL each time it is run, with an Ngrok account you can get a static domain from the https://dashboard.ngrok.com/domains.

Running the Server
==================
Start the CI server by running ci_server.py ::

   python3 src/ci_server.py

The server uses the default Flask port 5000.
Run Ngrok on port 5000: ::

   ngrok http --url=$YOUR_DOMAIN 5000

For easier startup and shutdown, the server can be run using the following startup script: ::

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

.. note::
   Remember to replace $YOUR_DOMAIN with you actual domain 

Run the startup script: ::

   chmod +x start.sh
   ./start.sh 

Press Ctrl+C to exit.

The server can be tested by running `pytest` from the Continous-Integration-Server directory. ::

   pytest

