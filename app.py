import os
import datetime
import logging
import base64
import requests
import jwt
from pymongo import MongoClient
from flask import Flask, jsonify, request, json, abort
from passlib.hash import pbkdf2_sha256

app = Flask(__name__)

# Set up debug file and choose its logging level
logging.basicConfig(filename="Debug.log", level=logging.DEBUG)

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

        [POST]
        /login
        
        Takes login details as json with keys "Username" and "Password".
        Returns a json object showing the session token that should be sent as a
        cookie for all subsequent requests with the key of "SessionToken".

        [GET, POST]
        /todo

        For a GET request, returns all todo list items for the user provided
        in the session token.

        For a POST request, takes json in the form:

        {
            "Description": string,
            "Completed": boolean
        }
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

def is_authorised(token):
        """
        Decodes the auth token
        :param auth_token:
        :return: integer|string
        """
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
                    print("User is none")

        except jwt.ExpiredSignatureError:
            return 'Signature expired. Please log in again.'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again.'

db = startup()

@app.route('/api/login', methods=["POST"])
def login():
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

@app.route('/api/todo/<id>', methods=["PUT","DELETE"])
def get_item(id):
    if "SessionToken" in request.cookies:
        auth = is_authorised(request.cookies["SessionToken"])
        if (auth is True):
            UID = db.sessions.find_one({"SessionToken":request.cookies["SessionToken"]})["UID"]
            if request.method == "PUT":
                item = db.todo.find_one_and_update({"UID":UID,"_id":id})
                if item is not None:
                    return jsonify(item),200
                else:
                    return jsonify({"Error":"Please provide a valid id"}),400
            elif request.method == "DELETE":
                item = db.todo.find_one_and_delete({"UID":UID,"_id":id})
                if item is not None:
                    return jsonify({"Id":item["_id"]}),203
                else:
                    return jsonify({"Error":"Please provide a valid id"}),400
            else:
                abort(404)
        else:
            return jsonify({"Error": auth}), 401
    else:
        return jsonify({"Error":"Please provide a session token cookie with your request."}), 401

@app.route('/api/todo', methods=["GET"])
def get_items():
    if "SessionToken" in request.cookies:
        auth = is_authorised(request.cookies["SessionToken"])
        if (auth is True):
            UID = db.sessions.find_one({"SessionToken":request.cookies["SessionToken"]})["UID"]
            result = db.todo.find({"UID":UID})
            return jsonify(
                [
                    {
                        "Id": str(item["_id"]),
                        "Description": item["Description"],
                        "Completed": item["Completed"]
                    } for item in result]
            )

        else:
            return jsonify({"Error": auth}), 401
    else:
        return jsonify({"Error":"Please provide a session token cookie with your request."}), 401

@app.route('/api/todo', methods=['POST'])
def post_item():
    if "SessionToken" in request.cookies:
        auth = is_authorised(request.cookies["SessionToken"])
        if (auth is True):
            UID = db.sessions.find_one({"SessionToken":request.cookies["SessionToken"]})["UID"]
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
            return jsonify({"Error": auth}), 401
    else:
        return jsonify({"Error":"Please provide a session token cookie with your request."}), 401
