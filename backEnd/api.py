import os
import sys
import time
import queries
import queries_user
from flask import Flask, jsonify, request, abort, g, url_for
import flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS, cross_origin
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

# Set working directory
sys.path.append('/home/WxT-QA-BOT')
import credentials

def create_app():
    
    # Instantiate Flask app
    API_app = flask.Flask(__name__)
    API_app.config['SECRET_KEY'] = credentials.FLASK["Flask_SECRET_KEY"]
    auth = HTTPBasicAuth()
    authToken = HTTPTokenAuth('Bearer')
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

#======================================================= API AUTH =======================================================

    #For each user a username and a password_hash will be stored.
    def hash_password(password):
        try: 
            new_password_hash = generate_password_hash(password)
            return new_password_hash
        
        except:
            abort(500, "Error hashing the password")
    
    def verify_password_hash(user, password):
        try:
            password_hash = queries_user.getPasswordHash(user)
            if not password_hash: #user doesnt exist
                return False
            return check_password_hash(password_hash, password)
        
        except:
            abort(500, "Error verifying the password")

    #AUTH Token to expire in 24h / 86400 seconds
    def generate_auth_token(user, expires_in):
        try:
            authToken = jwt.encode(
                {'id': user, 'exp': time.time() + expires_in},
                API_app.config['SECRET_KEY'], algorithm='HS256')
            return authToken
        
        except:
            abort(500, "Error generating the Auth Token")

    def verify_auth_token(token):
        try:
            # Make sure you query the DB with the user id that gets decoded from the token. 
            # If user exists then it's authenticated
            user = jwt.decode(token, API_app.config['SECRET_KEY'],algorithms=['HS256'])
            # If the token auth is sucessful, return the user
            return queries_user.getUser(user["id"])
        
        except:
            user = None
            return user
    
    @auth.verify_password
    def verify_password(username, password):
        # first try to authenticate by token
        try:
            user = queries_user.getUser(username)
            checkPassword = verify_password_hash(username, password)
            if not user or not checkPassword:
                return False
            #Set Global variable on flask to be used by other @routes
            g.user = user
            print("Sucessfully validated the user: "+str(user))
            return True

        except:
            abort(400, "Error validating the user credentials")

    @authToken.verify_token
    def verify_token(token):
        # first try to authenticate by token
        try:
            user = verify_auth_token(token)
            if not user:
                return False
            #Set Global variable on flask to be used by other @routes
            g.user = user
            print("Sucessfully validated the user: "+str(user))
            return True

        except:
            abort(400, "Error validating the token")

    @API_app.route('/api/newUsers', methods=['POST'])
    def new_user():
        try:
            username = request.json.get('username')
            password = request.json.get('password')
            if username is None or password is None: # missing arguments
                err_missingInfo = "Information Missing! Please fill use both the username and the password fields."
                raise(err_missingInfo)
            if username == "" or password == "": # empty arguments
                err_empty = "Empty credentials! Please fill in both the username and the password fields."
                raise(err_empty)
            if queries_user.getUser(username) is not None: # existing user
                err_userExists = "Username: "+str(username)+" already exists. Please use a different username."
                raise(err_userExists)    
            
            #hash the password
            hashedPassword = hash_password(password)
            #Add both user and hashed password to the DB
            newUser_ID, newUser = queries_user.addUser(username, hashedPassword)
            #Generate the token for the new user - this will last 24h, then it will need to be renewed
            token = generate_auth_token(newUser,86400)

            return (jsonify([{'username': queries_user.getUser(username)},
                            {'token': token.decode('ascii'), 'duration': 86400}]), 201)
        
        except:
            if "err_missingInfo" in locals():
                abort(400, err_missingInfo)
            if "err_empty" in locals():
                abort(400, err_empty)
            if "err_userExists" in locals():
                abort(400, err_userExists)
            else:
                abort(400)
    
    @API_app.route('/api/token')
    @auth.login_required
    def get_auth_token():
        try:
            token = generate_auth_token(g.user,86400)
            print("Sucessfully generated a token for the user: "+str(g.user)+" and it is valid for 24h.")
            return jsonify({'token': token.decode('ascii'), 'duration': 86400})
        
        except:
            abort(400, "Error generating Token")

    @API_app.route('/api/resource')
    @authToken.login_required
    def get_resource():
        return jsonify({'data': 'Hello, %s!' % g.user})

#======================================================= API AUTH =======================================================

    # getAnswer by GET
    @API_app.route('/getAnswer/<questionID>', methods=['GET'])
    @cross_origin()
    @limiter.limit("200 per hour", override_defaults=False)
    @authToken.login_required
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
    #@authToken.login_required #Need to explore how to implement token login via the frontEnd
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
    @authToken.login_required
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
    @authToken.login_required
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
    @authToken.login_required
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
    @authToken.login_required
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
    @authToken.login_required
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
    @authToken.login_required
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