import queries
from collections import OrderedDict 
from flask import Flask, jsonify, request, abort
import flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS, cross_origin

from pprint import pprint

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
            answer = queries.getAnswer(questionID)
            if answer == "Failure":
                f_message = "No entry found. Question ID is not valid."
                raise(f_message)

            return jsonify(answer)
        
        except:
            if "f_message" in locals():
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
        location = ""
        #location = request.form.get('location')
        alternatives = ""
        #alternatives = request.form.get('alternatives')
        try:
            addEntry = queries.addEntry(tag,question, answer, location, alternatives)
            if addEntry == "Failure":
                f_message = "Failed to add Entry to DB"
                raise(f_message)
            return(flask.Response(status=200))
        
        except:
            if "f_message" in locals():
                abort(500, f_message)
            abort(400)

    # getAllQuestions
    @API_app.route('/getAllQuestions', methods=['GET'])
    @limiter.limit("200 per hour", override_defaults=False)
    def getAllQuestions():
        try:
            allQuestions = queries.getAllQuestions()
            #Check if there's a DB failure, if so, raise a HTTP 500 error code with DB Failure message
            if allQuestions == "Failure":
                f_message = "Database Failure"
                raise(f_message)
            
            return jsonify(allQuestions)
            
        except:
            if "f_message" in locals():
                abort(500, f_message)
            else:
                abort(400)
    
    # Get all entries from the DB
    @API_app.route('/getAll', methods=['GET'])
    @limiter.limit("200 per hour", override_defaults=False)
    def getAll():
        try:
            allDB = queries.getAll()
            #Check if there's a DB failure, if so, raise a HTTP 500 error code with DB Failure message
            if allDB == "Failure":
                f_message = "Database Failure"
                raise(f_message)
            
            allDBdict = {}
            allDBdict["items"]=[None] * len(allDB) 
            #Convert list output from SQL into a Dictionary to be returned as JSON via jsonfy
            for index,values in enumerate(allDB):
                allDBdict["items"][index] = values

            return jsonify(allDBdict)
        
        except:
            if "f_message" in locals():
                abort(500, f_message)
            else:
                abort(400)

    # Add alternatives to a question 
    @API_app.route('/appendAlternative/<questionID>', methods=['POST'])
    @cross_origin() #Potentially add alternatives field to FrontEnd
    @limiter.limit("200 per hour", override_defaults=False)
    def appendAlternative(questionID):
        try:
            if request.is_json:
                #Consume JSON payload {"question": "Here is an additional question"}
                jsonPayload = request.get_json()
                alternative = jsonPayload["question"]
                
                appendAlternative = queries.appendAlternative(questionID, alternative)
                
                if appendAlternative == False:
                    err_questionID = "Error! Question ID: "+str(questionID)+" does not exist!"
                    raise(err_questionID)
                
                if appendAlternative == "Failure":
                    f_message = "Error appending alternative to Question ID: "+str(questionID)
                    raise(f_message)
                
                print("Successfully added question alternative to Question ID:", questionID)
                return("Successfully added question alternative to Question ID: "+str(questionID))
            else:
                request_isNotJSON = "Error appending alternative to Question ID: "+str(questionID)+". The request POSTed is NOT in JSON format."
                raise(request_isNotJSON)
        
        except:
            if "err_questionID" in locals():
                abort(404, err_questionID)
            if "f_message" in locals():
                print(f_message)
                abort(500, f_message)
            if "request_isNotJSON" in locals():
                print(request_isNotJSON)
                abort(415, request_isNotJSON)
            else:
                abort(400)

    # Add alternatives to a question 
    @API_app.route('/newEscalationAnswer', methods=['POST'])
    @cross_origin() #Potentially add alternatives field to FrontEnd
    @limiter.limit("200 per hour", override_defaults=False)
    def newEscalationAnswer():
        try:
            if request.is_json:
                #Consume JSON payload {"question": "Here is an additional question"}
                jsonPayload = request.get_json()
                question = jsonPayload["question"]
                answer = jsonPayload["answer"]
                #This API endpoint is only handled by the BOT when the Question gets escalated and it's added by the Webex Warriors
                tag = "Escalation: Webex Warriors"
                #alternatives are empty as it is not possible to populate these via the escalation workflow
                alternatives = ""
                #location is empty as it is not possible to attach files via the escalation workflow
                location = ""
                addNewQandA = queries.addEntry(tag, question, answer, location, alternatives)
                
                if addNewQandA == "Failure":
                    f_message = "Failed to add a new question and answer from the Escalation Webex Warriors workflow"
                    raise(f_message)
                
                print("Successfully added a question and answer from the Escalation Webex Warriors workflow")
                return("Successfully added a question and answer from the Escalation Webex Warriors workflow")
            else:
                request_isNotJSON = "Error adding a new question and answer from the Escalation Webex Warriors workflow. The request POSTed is NOT in JSON format."
                raise(request_isNotJSON)
        except:
            if "f_message" in locals():
                print(f_message)
                abort(500, f_message)
            if "request_isNotJSON" in locals():
                print(request_isNotJSON)
                abort(415, request_isNotJSON)
            else:
                abort(400)
    
    @API_app.route('/updateCount', methods=['POST'])
    @cross_origin()
    @limiter.limit("200 per hour", override_defaults=False)
    def updateCount():
        try:
            if request.is_json:
                #Consume JSON payload {'items': [{'id': 1, 'count': 2}, {'id': 2, 'count': 3}]}
                jsonPayload = request.get_json()
                for item in jsonPayload["items"]:
                    questionID = item["id"]
                    count = item["count"]
                    # updateEntry(id, tag, question, answer, location, alternatives, count):
                    updateCount = queries.updateEntry(questionID, "", "", "", "", "", count)
                    
                    if updateCount == "id required":
                        err_IDrequired = "Error! Question ID was not provided. Please provide Question ID"
                        raise(err_IDrequired)
                    
                    if updateCount == False:
                        err_questionID = "Error! Question ID: "+str(questionID)+" does not exist!"
                        raise(err_questionID)
                    
                    if updateCount == "Failure":
                        f_message = "Error updating count on Question ID: "+str(questionID)
                        raise(f_message)
                
                print("Successfully updated the count field on the database")
                return("Successfully updated the count field on the database")
            
            else:
                request_isNotJSON = "Error adding a new question and answer from the Escalation Webex Warriors workflow. The request POSTed is NOT in JSON format."
                raise(request_isNotJSON)
        
        except:
            if "err_IDrequired" in locals():
                abort(404, err_IDrequired)
            if "err_questionID" in locals():
                abort(404, err_questionID)
            if "f_message" in locals():
                print(f_message)
                abort(500, f_message)
            if "request_isNotJSON" in locals():
                print(request_isNotJSON)
                abort(415, request_isNotJSON)
            else:
                abort(400)


    # ************************************************ WORK IN PROGRESS ************************************************
    # Update Entry on the DB **WORK IN PROGRESS**
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
    
    # ************************************************ WORK IN PROGRESS ************************************************
    
    return API_app

# Main
if __name__ == "__main__":
    API_app = create_app()
    #API_app.run(host=credentials.FLASK["Flask_HOST"], port=credentials.FLASK["Flask_PORT"], debug=False)
    #With Debug Capabilities
    #API_app.run(host=credentials.FLASK["Flask_HOST"], port=credentials.FLASK["Flask_PORT"], debug=True)

    #For DEV Testing purposes ONLY
    API_app.run(host=credentials.FLASK_devTest["Flask_HOST"], port=credentials.FLASK_devTest["Flask_PORT"], debug=True)