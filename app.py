import os
import datetime
import logging
import base64
import requests
import jwt
from pymongo import MongoClient
from flask import Flask, jsonify, request, json
from passlib.hash import pbkdf2_sha256

app = Flask(__name__)

# Set up debug file and choose its logging level
logging.basicConfig(filename="Debug.log", level=logging.INFO)

class InMemoryDatabase(object):
    """
    To save you setting up a database, create a
    class to hold any information in memory while the
    app is running
    """
    def __init__(self):
        self.users = []
    
    def add_user(self,username,password):
        for user in self.users:
            if user["Details"]["Username"] == username:
                return False
        self.users.append({
            "Details": {
                "Username": username,
                "Password": password
            },
            "Data": {

            }
        })
        return True
    
    def create_token(self,username,password):
        for user in self.users:
            if user["Details"]["Username"] == username:
                if pbkdf2_sha256.verify(password,user["Details"]["Password"]):
                    try:
                        # Create session token
                        payload = {
                            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, hours=1),
                            'iat': datetime.datetime.utcnow(),
                            'sub': username
                        }
                        token = jwt.encode(
                            payload,
                            user["Details"]["Password"],
                            algorithm='HS256'
                        )
                        # Create or replace a session object
                        db.sessions.replace_one(
                            {"UID":user["_id"]},
                            {
                                "UID": user["_id"],
                                "SessionToken": token,
                                "Created": payload["iat"],
                                "Expires": payload["exp"]
                            },
                            upsert=True
                            })
                        return token
                    except Exception as e:
                        return e
                else:
                    return None
    
    def is_authorised(self,token):
        """
        Decodes the auth token
        :param auth_token:
        :return: integer|string
        """
        try:
            if db.sessions.find_one({"SessionToken":token}) is None:
                return False
            for user in self.users:
                if user["Details"]["Username"] == username:
                    password = user["Details"]["Password"]
                    break
            payload = jwt.decode(auth_token, password)
            return True
        except jwt.ExpiredSignatureError:
            return 'Signature expired. Please log in again.'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again.'

def startup():
    help_string = """
        The API is available at:
        http://localhost:5000/api/todo/

        Example use:

        A GET request to http://localhost:5000/api/todo/1234 would return
        the details of the item with id = 1234 (if it exists) in JSON format

        User credentials:

        A user has been created on startup with the following credentials:
            Username: Testuser
            Password: Secretcode
        """
    print(help_string)
    # Generate starting data if it does not already exist
    client = MongoClient()
    db = client.Novastone
    users = db.Users
    firstUser = users.find_one({"Username":"Testuser"})
    if (firstUser is None):
        result = users.insert_one({
            "Username": "Testuser",
            "Password": pbkdf2_sha256.hash("Secretcode")
        })
    

    #DB = InMemoryDatabase()
    #DB.add_user("Testuser",pbkdf2_sha256.hash("Secretcode"))
    return db

def create_token(username,password):
    user = db.user.find_one({"Username":username})
    if user is not None and pbkdf2_sha256.verify(password,user["Details"]["Password"]):
        try:
            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, seconds=5),
                'iat': datetime.datetime.utcnow(),
                'sub': username
            }
            token = jwt.encode(
                payload,
                user["Details"]["Password"],
                algorithm='HS256'
            )
            # Create or replace a session object
            db.sessions.replace_one(
                {"UID":user["_id"]},
                {
                    "UID": user["_id"],
                    "SessionToken": token,
                    "Created": payload["iat"],
                    "Expires": payload["exp"]
                },
                upsert=True
                })
            return btoken
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
            if db.sessions.find_one({"SessionToken":token}) is None:
                return 'Invalid token. Please log in again.'
            username,auth_token = base64.b64decode(token).split(",")
            user = db.users.find_one({"Username":username})
            if user is not None:
                payload = jwt.decode(auth_token, user["Password"])
                return True
        except jwt.ExpiredSignatureError:
            return 'Signature expired. Please log in again.'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again.'

db = startup()

@app.route('/login', methods=["POST"])
def login():
    token = create_token(request.json["Username"],request.json["Password"])
    if token is not None: 
        return jsonify({"SessionToken": token})
    else:
        return jsonify({"Message":"Invalid username or password"})

@app.route('/api/todo/<id>', methods=["GET"])
def get_item(id):
    if "SessionToken" in request.cookies:
        auth = is_authorised(request.cookies["SessionToken"])
        if (auth is True):
            chosen_item={}
            return jsonify({"Items":chosen_item})
        else:
            return jsonify({"Error":auth})
    else:
        return jsonify({"Error":"Please provide a valid session token"})

@app.route('/api/todo/', methods=["GET"])
def get_items():
    return jsonify({"Items":{},"Message":"Please provide a valid id"})

@app.route('/api/todo/', methods=['POST'])
def post_item(json_data):
    return json_data
