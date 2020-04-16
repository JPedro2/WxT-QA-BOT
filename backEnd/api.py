import queries
from flask import jsonify
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

# getAnswer by GET
@API_app.route('/getAnswer/<questionID>', methods=['GET'])
@limiter.limit("200 per hour", override_defaults=False)
def _getAnswer(questionID):
    try:
        answer = queries.getAnswer(questionID)
        return(answer)
    except:
        flask.abort(status=400)

# addEntry by POST form
@API_app.route('/addEntry', methods=['POST'])
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

# getAllQuestions
@API_app.route('/getAllQuestions', methods=['GET'])
@limiter.limit("200 per hour", override_defaults=False)
def getAllQuestions():
    try:
        allQuestions = queries.getAllQuestions()
        allQuestionsDict = {}
        #Convert list of tuples output from SQL into a Dictionary to be returned as JSON via jsonfy
        for index,tuple in enumerate(allQuestions):
            for questions in tuple:
                id = index+1        #match the id from the sql table, otherwise it starts from 0
                allQuestionsDict[id]=questions
        return jsonify(allQuestionsDict)
    except:
        flask.abort(status=400)

# Main
if __name__ == "__main__":
    API_app.run(host=credentials.FLASK["Flask_HOST"], port=credentials.FLASK["Flask_PORT"], debug=True)
