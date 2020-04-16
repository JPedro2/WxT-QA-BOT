import queries
import flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import sys
# Set working directory
sys.path.append('/home/WxT-QA-BOT')
import credentials

# Instantiate Flask app
API_app = flask.Flask(__name__)

# Instantiate limiter
limiter = Limiter(
    API_app,
    key_func=get_remote_address,
    default_limits=["10000 per day","1000 per hour"]
)

# Root
@API_app.route('/')
def default():
    return

# getAnswer by POST form
@API_app.route('/getAnswer', methods=['POST', 'GET'])
@limiter.limit("200 per hour", override_defaults=False)
def getAnswer():
    question = flask.request.form['question']
    try:
        queries.getAnswer(question)
        return(flask.Response(status=200))
    except:
        flask.abort(status=400)

# getAnswer by GET
@API_app.route('/getAnswer/<question>', methods=['GET'])
@limiter.limit("200 per hour", override_defaults=False)
def _getAnswer(question):
    try:
        out = queries.getAnswer(question)
        return(flask.Response(status=200))
    except:
        flask.abort(status=400)

# addEntry by POST form
@API_app.route('/addEntry', methods=['POST', 'GET'])
# Exempt from rate limit
@limiter.exempt
def addEntry():
    question = flask.request.form['question']
    answer = flask.request.form['answer']
    try: 
        queries.addEntry("General", question, answer)
        return(flask.Response(status=200))
    except:
        flask.abort(status=400)

# Main
if __name__ == "__main__":
    API_app.run(host=credentials.FLASK["Flask_HOST"], port=credentials.FLASK["Flask_PORT"], debug=True)
