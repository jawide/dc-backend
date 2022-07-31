from datetime import timedelta
import json
import os
import threading
from uuid import uuid1
from flask import Flask, request, Response
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
import shelve
import redis
import util


REDIS_HOST = os.environ.get('REDIS_HOST') or 'localhost'
REDIS_PORT = os.environ.get('REDIS_PORT') or 6379
REDIS_DB = os.environ.get('REDIS_DB') or 0


app = Flask(__name__)
CORS(app)
auth = HTTPBasicAuth()
db_write_lock = threading.Lock()
r = redis.StrictRedis(REDIS_HOST, REDIS_PORT, REDIS_DB)


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
            info = data.get(name) or json.loads(r.get(name))
            return info['content']
        except KeyError:
            return Response('Not found', 400)

@app.route('/software/<name>/info', methods=['GET'])
def info(name):
    with shelve.open('data/software', "c") as data:
        try:
            res = data.get(name) or json.loads(r.get(name))
            del res['content']
            return json.dumps(res)
        except KeyError:
            return Response('Not found', 400)

@app.route('/list/software', methods=['GET'])
def listall():
    with shelve.open('data/software', "c") as data:
        return json.dumps(list(map(str, data.keys())))

@app.route('/software/temp', methods=['POST'])
def temp():
    name = str(uuid1())
    description = util.get_from_json(request.json, 'description')
    content = util.get_from_json(request.json, 'content')
    r.set(name, json.dumps({
        'description': description,
        'content': content
    }), timedelta(minutes=5))
    return json.dumps({
        'name': name
    })