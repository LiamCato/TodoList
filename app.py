import os
import logging
import requests
from flask import Flask, jsonify

app = Flask(__name__)

# Set up debug file and choose its logging level
logging.basicConfig(filename="Debug.log", level=logging.INFO)
    
def startup():
    help_string = """
        The API is available at:
        http://localhost:5000/api/todo/

        Example use:

        A GET request to http://localhost:5000/api/todo/1234 would return
        the details of the item with id = 1234 (if it exists) in JSON format
        """
    print(help_string)
    


@app.route('/api/todo/<id>')
def get_item(id):
    chosen_item={}
    return jsonify({"Items":chosen_item})

@app.route('/api/todo/')
def get_items():
    return jsonify({"Items":{},"Message":"Please provide a valid id"})

