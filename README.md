# TodoList
A simple flask API for managing a to do list

## Requirements

* Python 3.x (written in 3.6)
* Mongodb - [Install the free community version from here](https://docs.mongodb.com/manual/administration/install-community/)
* Python's mongo connector - pip install pymongo
* Python's flask module - pip install flask
* Python's requests module - pip install requests
* Python's passlib module - pip install passlib
* Python's PyJWT module - pip install PyJWT


## Run the app:

* Download the repository
* Open a command line / powershell / terminal
* Add FLASK_APP environment variable to your terminal pointing to the app.py file
* Use command "flask run" to start the app

Once the app is running you can run "python flasktests.py" which runs unit tests for each part of the apps functionality
(Login / Logout / Create / Read / Update / Delete )



The API is available at:
        http://localhost:5000/api/

        Example use:

        A GET request to http://localhost:5000/api/todo/1234 would return
        the details of the item with id = 1234 (if it exists) in JSON format

        User credentials:

        A user has been created on startup with the following credentials:
            Username: Testuser
            Password: Secretcode

        API end points:


        [POST, PUT]
        /sessiontoken
        
        (login)
        A POST request takes login details as json with keys "Username" and "Password".
        Returns a json object showing the session token that should be sent as a
        cookie for all subsequent requests with the key of "SessionToken".

        (logout)
        Sent a PUT request with a valid sessiontoken as a cookie to end the session


        [GET, POST]
        /todo

        For a GET request, returns all todo list items for the user provided
        in the session token.

        For a POST request, creates a new task given json in the form:

        {
            "Description": string,
            "Completed": boolean
        }

        [PUT, DELETE]
        /todo/id

        For a PUT requests updates the task with the given id if it exists and the user has access.
        Takes JSON data with keys of either "Description" as a string, "Completed" as a boolean or
        both to update the whole task.


        For a DELETE request, deletes the task with the given id (assuming that it exists and the user provided in
        the session token has access to it).
