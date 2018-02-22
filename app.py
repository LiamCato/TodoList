import os
import datetime
import logging
import requests
import jwt
from pymongo import MongoClient, ReturnDocument
from bson.objectid import ObjectId
from flask import Flask, jsonify, request, json, abort
from passlib.hash import pbkdf2_sha256

app = Flask(__name__)

# Set up debug file for the application and choose its logging level
logging.basicConfig(filename="Debug.log", level=logging.DEBUG)

# Define a function to be called at startup to initialise sample data
def startup():
    help_string = """
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
        """
    print(help_string)
    # Generate starting data
    client = MongoClient()
    db = client.Novastone
    db.users.replace_one(
        {"Username":"Testuser"},
        {
            "Username": "Testuser",
            "Password": pbkdf2_sha256.hash("Secretcode")
        },
        upsert=True
    )
    return db

# Returns a session token given a username and password
def create_token(username,password):
    user = db.users.find_one({"Username":username})
    if user is not None and pbkdf2_sha256.verify(password,user["Password"]):
        try:
            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, hours=1),
                'iat': datetime.datetime.utcnow(),
                'sub': username
            }
            token = jwt.encode(
                payload,
                user["Password"],
                algorithm='HS256'
            )
            # Create or replace a session object
            db.sessions.replace_one(
                {"UID":user["_id"]},
                {
                    "UID": user["_id"],
                    "SessionToken": token.decode(),
                    "Created": payload["iat"],
                    "Expires": payload["exp"]
                },
                upsert=True
                )
            return token.decode()
        except Exception as e:
            return e
    else:
        return None

# Checks a provided session token is valid
def is_authorised(token):
    try:
        session = db.sessions.find_one({"SessionToken":token})
        if  session is None:
            return 'Invalid token. Please log in again.'
        else:
            user = db.users.find_one({"_id":session["UID"]})
            if user is not None:
                jwt.decode(token, user["Password"])
                return True
            else:
                return 'Invalid token. Please log in again.'

    except jwt.ExpiredSignatureError:
        return 'Signature expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'


# Call startup function when app launches
db = startup()


@app.route('/api/sessiontoken', methods=["POST","PUT"])
def sessiontoken():
    # Login
    if request.method == "POST":
        try:
            token = create_token(request.json["Username"],request.json["Password"])
            if token is not None: 
                response = jsonify({"SessionToken": token})
                response.set_cookie("SessionToken", token)
                return response
            else:
                response = jsonify({"Error":"Invalid username or password"})
                return response, 401
        except KeyError:
            return jsonify({"Error": "Please provide both a Username and Password key"}), 400
    # Logout
    elif request.method == "PUT":
        if "SessionToken" in request.cookies:
            auth = is_authorised(request.cookies["SessionToken"])
            if (auth is True):
                db.sessions.delete_one({"SessionToken":request.cookies["SessionToken"]})
                response = jsonify({"Logged_out":True})
                response.set_cookie("SessionToken","")
                return response
            else:
                return jsonify({"Error": auth}), 401
        else:
            return jsonify({"Error":"Please provide a session token cookie with your request."}), 401
    else:
        abort(404)

@app.route('/api/todo/<id>', methods=["PUT","DELETE"])
def get_item(id):
    if "SessionToken" in request.cookies:
        auth = is_authorised(request.cookies["SessionToken"])
        if (auth is True):
            UID = db.sessions.find_one({"SessionToken":request.cookies["SessionToken"]})["UID"]
            # Update a to do list item
            if request.method == "PUT" and request.json is not None:
                update = {}
                if "Description" in request.json and isinstance(request.json["Description"],str):
                    update["Description"] = request.json["Description"]
                if "Completed" in request.json and isinstance(request.json["Completed"],bool):
                    update["Completed"] = request.json["Completed"]
                item = db.todo.find_one_and_update(
                    {"UID":UID,"_id":ObjectId(id)},
                    {'$set':update},
                    return_document=ReturnDocument.AFTER
                    )
                if item is not None:
                    return jsonify({
                        "Id": str(item["_id"]),
                        "Description": item["Description"],
                        "Completed": item["Completed"]
                    }),200
                else:
                    return jsonify({"Error":"Please provide a valid id"}),400
            # Remove a to do list item
            elif request.method == "DELETE":
                item = db.todo.find_one_and_delete({"UID":UID,"_id":ObjectId(id)})
                if item is not None:
                    return jsonify({"Id":str(item["_id"])}),203
                else:
                    return jsonify({"Error":"Please provide a valid id"}),400
            else:
                abort(404)
        else:
            return jsonify({"Error": auth}), 401
    else:
        return jsonify({"Error":"Please provide a session token cookie with your request."}), 401

@app.route('/api/todo', methods=['GET','POST'])
def get_items():
    if "SessionToken" in request.cookies:
        auth = is_authorised(request.cookies["SessionToken"])
        if (auth is True):
            UID = db.sessions.find_one({"SessionToken":request.cookies["SessionToken"]})["UID"]
            # Get all to do list items for the given user
            if request.method == "GET":
                result = db.todo.find({"UID":UID})
                return jsonify(
                    [
                        {
                            "Id": str(item["_id"]),
                            "Description": item["Description"],
                            "Completed": item["Completed"]
                        } for item in result]
                )
            # Create a new to do list item for the given user
            elif request.method == "POST":
                try:
                    if( isinstance(request.json["Description"], str) and isinstance(request.json["Completed"],bool)):
                        result = db.todo.insert_one({
                            "UID": UID,
                            "Description": request.json["Description"],
                            "Completed": request.json["Completed"]
                        })
                        return jsonify({"Id": str(result.inserted_id)}), 201
                    else:
                        return jsonify({"Error": "Invalid data provided"}), 400
                except KeyError:
                    return jsonify({"Error": "Please provide both a Description and Completed key"}), 400
            else:
                abort(404)
        else:
            return jsonify({"Error": auth}), 401
    else:
        return jsonify({"Error":"Please provide a session token cookie with your request."}), 401
