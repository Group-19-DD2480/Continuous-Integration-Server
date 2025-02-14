API
===

The program hooks onto a webhook on github and acts as a CI-server.

The function :py:func:`ci_server.handle_webhook` listens to the webhook for 'ping' and 'push' events

In the event of a push-event, the payload is expected to be in the format of ::
   
   {
      "repository":{
         "owner":{
            "login": the repo owner
         }
         "name": the repo name
      }
      "after": the commit sha of the latest pushed commit
   }

It will then start a build-environment in a separate thread, and return a *202* http code.

The server will then try to run a static syntax check on the repo in order to check for syntax-errors, aswell as run pytest on the home directory. If both pass, the status on github is set to sucess.

The post event will have the following format: ::

   headers = {
      "Authorization": "token <the authentication token used to access the github API>"
   } 

   payload =
   {
      "state": the status to be sent to github
      "description": "CI test results"
      "context": "CI/Test"
   }



