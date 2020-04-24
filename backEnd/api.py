import queries
from collections import OrderedDict 
from flask import Flask, jsonify, request, abort
import flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS, cross_origin

import sys
# Set working directory
sys.path.append('/home/WxT-QA-BOT')
import credentials

def create_app():
    # Instantiate Flask app
    API_app = flask.Flask(__name__)
    #CORS(API_app)

    # Instantiate limiter
    limiter = Limiter(
        API_app,
        key_func=get_remote_address,
        default_limits=["10000 per day","1000 per hour"]
    )

    # Root
    @API_app.route('/')
    def default():
        return("Welcome. This is April's API Service")

    # getAnswer by GET
    @API_app.route('/getAnswer/<questionID>', methods=['GET'])
    @cross_origin()
    @limiter.limit("200 per hour", override_defaults=False)
    def _getAnswer(questionID):
        try:
            if queries.getAnswer(questionID) == "Failure":
                f_message = "No entry found"
                raise(f_message)

            answer = queries.getAnswer(questionID)
            return jsonify(answer)
        except:
            if f_message != "":
                abort(404, f_message)
            else:
                abort(400)

    # addEntry by POST form
    @API_app.route('/addEntry', methods=['POST'])
    @cross_origin(supports_credentials=True)
    # Exempt from rate limit
    @limiter.exempt

    def addEntry():
        tag = request.form.get('select')
        question = request.form.get('question')
        answer = request.form.get('answer')
        try:
            queries.addEntry(tag,question, answer)
            return(flask.Response(status=200))
        except:
            abort(400)

    # getAllQuestions
    @API_app.route('/getAllQuestions', methods=['GET'])
    @limiter.limit("200 per hour", override_defaults=False)
    def getAllQuestions():
        try:
            #Check if there's a DB failure, if so, raise a HTTP 500 error code with DB Failure message
            if queries.getAllQuestions() == "Failure":
                f_message = "Database Failure"
                raise(f_message)
            
            allQuestions = queries.getAllQuestions()
            allQuestionsDict = {}
            #Convert list of tuples output from SQL into a Dictionary to be returned as JSON via jsonfy
            for index,tuple in enumerate(allQuestions):
                for questions in tuple:
                    id = index+1        #match the id from the sql table, otherwise it starts from 0
                    allQuestionsDict[id]=questions
            return jsonify(allQuestionsDict)
        except:
            if f_message != "":
                abort(500, f_message)
            else:
                abort(400)
    
    # Get all entries from the DB
    @API_app.route('/getAll', methods=['GET'])
    @limiter.limit("200 per hour", override_defaults=False)
    def getAll():
        try:
            #Check if there's a DB failure, if so, raise a HTTP 500 error code with DB Failure message
            if queries.getAll() == "Failure":
                f_message = "Database Failure"
                raise(f_message)
            
            allDB = queries.getAll()
            allDBdict = {}
            allDBdict["items"]=[None] * len(allDB) 
            #Convert list output from SQL into a Dictionary to be returned as JSON via jsonfy
            for index,values in enumerate(allDB):
                allDBdict["items"][index] = values

            return jsonify(allDBdict)
        except:
            if f_message != "":
                abort(500, f_message)
            else:
                abort(400)

    # Update Entry on the DB W.I.P.
    @API_app.route('/updateEntries', methods=['POST'])
    @limiter.limit("200 per hour", override_defaults=False)
    def updateEntries():
        try:
            id = request.form.get('id')
            tag = request.form.get('tag')
            question = request.form.get('question')
            answer = request.form.get('answer')
            
            allQuestions = queries.getAllQuestions()
            allQuestionsDict = {}
            #Convert list of tuples output from SQL into a Dictionary to be returned as JSON via jsonfy
            for index,tuple in enumerate(allQuestions):
                for questions in tuple:
                    id = index+1        #match the id from the sql table, otherwise it starts from 0
                    allQuestionsDict[id]=questions
            return jsonify(allQuestionsDict)
        except:
            abort(status=400)
    
    return API_app

# Main
if __name__ == "__main__":
    API_app = create_app()
    API_app.run(host=credentials.FLASK["Flask_HOST"], port=credentials.FLASK["Flask_PORT"], debug=False)
