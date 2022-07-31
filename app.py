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


@app.errorhandler(util.LackJSONParameter)
def lack_json_parameter(e):
    db_write_lock.release()
    return Response(str(e), 400)

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
            return Response('Already exists', 400)
        description = util.get_from_json(request.json, 'description')
        content = util.get_from_json(request.json, 'content')
        if util.check(content):
            data[name] = {
                'description': description,
                'content': content
            }
            db_write_lock.release()
            return 'Ok'
        else:
            db_write_lock.release()
            return Response('Format error', 400)

@auth.login_required
@app.route('/software/<name>', methods=['DELETE'])
def remove(name):
    db_write_lock.acquire()
    with shelve.open('data/software', "c", writeback=True) as data:
        try:
            data.pop(name)
        except KeyError:
            db_write_lock.release()
            return Response('Not found {}', 400)
    db_write_lock.release()
    return 'Ok'

@auth.login_required
@app.route('/software/<name>', methods=['PUT'])
def update(name):
    db_write_lock.acquire()
    with shelve.open('data/software', "c", writeback=True) as data:
        if name not in data:
            db_write_lock.release()
            return Response('Not found', 400)
        description = util.get_from_json(request.json, 'description')
        content = util.get_from_json(request.json, 'content')
        if util.check(content):
            data[name] = {
                'description': description,
                'content': content
            }
            db_write_lock.release()
            return 'Ok'
        else:
            db_write_lock.release()
            return Response('Format error', 400)

@app.route('/software/<name>', methods=['GET'])
def select(name):
    with shelve.open('data/software', "c") as data:
        try:
            return data[name]['content']
        except KeyError:
            return Response('Not found', 400)

@app.route('/software/<name>/info', methods=['GET'])
def info(name):
    with shelve.open('data/software', "c") as data:
        try:
            res = data[name]
            del res['content']
            return json.dumps(res)
        except KeyError:
            return Response('Not found', 400)

@app.route('/list/software', methods=['GET'])
def listall():
    with shelve.open('data/software', "c") as data:
        return json.dumps(list(map(str, data.keys())))