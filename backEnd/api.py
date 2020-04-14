import queries
import flask
from flask import request
from flask import abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
app = flask.Flask(__name__)

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per day","10 per hour"]
)

@app.route('/')
def default():
    return

@app.route('/getAnswer', methods=['POST', 'GET'])
@limiter.limit("1 per minute", override_defaults=False)
def getAnswer():
    question = request.form['question']
    try:
        queries.getAnswer(question)
        return flask.Response(status=200)
    except:
        abort(status=400)

@app.route('/getAnswer/<question>')
@limiter.limit("1 per minute", override_defaults=False)
def _getAnswer(question):
    return queries.getAnswer(question)

@app.route('/addEntry', methods=['POST', 'GET'])
@limiter.exempt
def addEntry():
    question = request.form['question']
    answer = request.form['answer']
    try: 
        queries.addEntry(question, answer)
        return flask.Response(status=200)
    except:
        abort(status=400)