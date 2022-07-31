import json
import threading
from flask import Flask, request, Response
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
import shelve
import util

app = Flask(__name__)
CORS(app)
auth = HTTPBasicAuth()
db_write_lock = threading.Lock()


@auth.verify_password
def verify_password(username, password) -> bool:
    with shelve.open('data/user', "c") as data:
        try:
            return data[username] == password
        except:
            return False

@app.route('/user', methods=['GET'])
@auth.login_required
def get_user():
    return auth.get_auth().get('username')

@app.route('/software/<name>', methods=['POST'])
@auth.login_required
def add(name):
    db_write_lock.acquire()
    with shelve.open('data/software', "c", writeback=True) as data:
        if name in data:
            db_write_lock.release()
            return Response('already exists', 400)
        text = request.data
        if util.check(text):
            data[name] = text
            db_write_lock.release()
            return 'ok'
        else:
            db_write_lock.release()
            return Response('format error', 400)

@auth.login_required
@app.route('/software/<name>', methods=['DELETE'])
def remove(name):
    db_write_lock.acquire()
    with shelve.open('data/software', "c", writeback=True) as data:
        try:
            data.pop(name)
        except KeyError:
            db_write_lock.release()
            return Response('not found {}', 400)
    db_write_lock.release()
    return 'ok'

@auth.login_required
@app.route('/software/<name>', methods=['PUT'])
def update(name):
    return add(name)

@app.route('/software/<name>', methods=['GET'])
def select(name):
    with shelve.open('data/software', "c") as data:
        try:
            return data[name]
        except KeyError:
            return Response('not found', 400)

@app.route('/list/software', methods=['GET'])
def listall():
    with shelve.open('data/software', "c") as data:
        return json.dumps(list(map(str, data.keys())))