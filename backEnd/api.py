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
    default_limits=["100 per day","10 per hour"]
)

# Root
@API_app.route('/')
def default():
    return

# getAnswer by POST form
@API_app.route('/getAnswer', methods=['POST', 'GET'])
@limiter.limit("1 per minute", override_defaults=False)
def getAnswer():
    question = request.form['question']
    try:
        queries.getAnswer(question)
        return flask.Response(status=200)
    except:
        abort(status=400)

# getAnswer by GET
@API_app.route('/getAnswer/<question>')
@limiter.limit("1 per minute", override_defaults=False)
def _getAnswer(question):
    return queries.getAnswer(question)

# addEntry by POST form
@API_app.route('/addEntry', methods=['POST', 'GET'])
# Exempt from rate limit
@limiter.exempt
def addEntry():
    question = request.form['question']
    answer = request.form['answer']
    try: 
        queries.addEntry(question, answer)
        return flask.Response(status=200)
    except:
        abort(status=400)

# Main
if __name__ == "__main__":
    API_app.run(host=credentials.FLASK["Flask_HOST"], port=credentials.FLASK["Flask_PORT"], debug=False)
