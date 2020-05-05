import os
import sys
import time
import queries
import queries_user
from flask import Flask, jsonify, request, abort, g, url_for, flash, redirect
import flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS, cross_origin
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Set working directory
sys.path.append('/home/WxT-QA-BOT')
import credentials

def create_app():
    
    # Instantiate Flask app
    API_app = flask.Flask(__name__)
    
    # Instantiate API config for uploads
    ALLOWED_EXTENSIONS = credentials.FLASK["ALLOWED_EXTENSIONS"]
    API_app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 #16MB maximum allowed file size to be uploaded                    
    API_app.config['UPLOAD_FOLDER'] = credentials.FLASK["UPLOAD_FOLDER"]

    # Instantiate API config for Auth
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

    # @API_app.route('/api/newUsers', methods=['POST'])
    # def new_user():
    #     try:
    #         username = request.json.get('username')
    #         password = request.json.get('password')
    #         if username is None or password is None: # missing arguments
    #             err_missingInfo = "Information Missing! Please fill use both the username and the password fields."
    #             raise(err_missingInfo)
    #         if username == "" or password == "": # empty arguments
    #             err_empty = "Empty credentials! Please fill in both the username and the password fields."
    #             raise(err_empty)
    #         if queries_user.getUser(username) is not None: # existing user
    #             err_userExists = "Username: "+str(username)+" already exists. Please use a different username."
    #             raise(err_userExists)    
            
    #         #hash the password
    #         hashedPassword = hash_password(password)
    #         #Add both user and hashed password to the DB
    #         newUser_ID, newUser = queries_user.addUser(username, hashedPassword)
    #         #Generate the token for the new user - this will last 24h, then it will need to be renewed
    #         token = generate_auth_token(newUser,86400)

    #         return (jsonify([{'username': queries_user.getUser(username)},
    #                         {'token': token.decode('ascii'), 'duration': 86400}]), 201)
        
    #     except:
    #         if "err_missingInfo" in locals():
    #             abort(400, err_missingInfo)
    #         if "err_empty" in locals():
    #             abort(400, err_empty)
    #         if "err_userExists" in locals():
    #             abort(400, err_userExists)
    #         else:
    #             abort(400)
    
    @API_app.route('/api/token')
    @auth.login_required
    def get_auth_token():
        try:
            token = generate_auth_token(g.user,86400)
            print("Sucessfully generated a token for the user: "+str(g.user)+" and it is valid for 24h.")
            return jsonify({'token': token.decode('ascii'), 'duration': 86400})
        
        except:
            abort(400, "Error generating Token")

#======================================================= API AUTH =======================================================

#=================================================== API File Upload ====================================================
    def allowed_file(filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    #URL needs to contain the questionID that the file needs to be associated with 
    # /uploads/<path:filename>/?questionID=
    @API_app.route('/uploads/<path:filename>/', methods=['POST'])
    def upload_file(filename):
        try:
            if not request.args.get('questionID'):
                err_IDrequired = "No question ID provided. Please provide a questionID"
                raise(err_IDrequired)

            if queries.getAnswer(questionID) == False:
                err_questionID = "Error! Question ID: "+str(questionID)+" does not exist!"
                raise(err_questionID)

            # check if the post request has the file part
            if 'file' not in request.files:
                err_noFile = "No file submitted"
                raise(err_noFile)
                #flash('No file part')
                #return redirect(request.url)
            file = request.files['file']
            # if user does not select file, browser also
            # submit an empty part without filename
            #if file.filename == '':
            #    flash('No selected file')
            #    return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(API_app.config['UPLOAD_FOLDER'], filename))
                filePath = url_for('uploaded_file',filename=filename)
                #add filePath to the location column on the DB

                return ("File Sucefully Uploaded to Knowledge Base", 201)
                #return redirect(url_for('uploaded_file',filename=filename))

            else:
                err_fileExtension = "File extentions is not allowed. Please only submit allowed file extensions."
                raise(err_fileExtension)
        
        except:
            if "err_IDrequired" in locals():
                abort(404, err_IDrequired)
            if "err_questionID" in locals():
                abort(404, err_questionID)
            if "err_noFile" in locals():
                abort(400, err_noFile)
            if "err_fileExtension" in locals():
                abort(400, err_fileExtension)
            else:
                abort(400)
#=================================================== API File Upload ====================================================

#==================================================== API Endpoints =====================================================
    # getAnswer for the Bot to grab answers based on Question ID
    @API_app.route('/getAnswer/<int:questionID>', methods=['GET'])
    @cross_origin(supports_credentials=True)
    @limiter.limit("200 per hour", override_defaults=False)
    #@authToken.login_required
    def _getAnswer(questionID):
        try:
            answer = queries.getAnswer(questionID)
            if answer == False:
                err_questionID = "Error! Question ID: "+str(questionID)+" does not exist!"
                raise(err_questionID)
            if answer == "Failure":
                f_message = "Error, database failure whilst retrieving the answer."
                raise(f_message)
            return jsonify(answer)
        
        except:
            if "err_questionID" in locals():
                abort(404, err_questionID)
            if "f_message" in locals():
                abort(500, f_message)
            else:
                abort(400)
    
    # get question, answer, alternatives and location for the FrontEnd to use this knowledge: Query and Update tabs
    @API_app.route('/getKnowledge/<int:questionID>', methods=['GET'])
    @cross_origin(supports_credentials=True)
    @limiter.limit("200 per hour", override_defaults=False)
    #@authToken.login_required
    def getKnowledge(questionID):
        try:
            knowledge = queries.getKnowledge(questionID)
            if knowledge == "Failure":
                f_message = "No entries have been found. Question ID is not valid."
                raise(f_message)
            return jsonify(knowledge)
        
        except:
            if "f_message" in locals():
                abort(404, f_message)
            else:
                abort(400)

    # addEntry to add Questions, Answers and Alternative Questions from the FrontEnd: Submit tab
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

    # getAllQuestions to be used by the Bot and the FE: Update and Query Tabs
    @API_app.route('/getAllQuestions', methods=['GET'])
    @cross_origin(supports_credentials=True)
    @limiter.limit("200 per hour", override_defaults=False)
    #@authToken.login_required
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
    
    # Get all entries from the Knowledge Base
    @API_app.route('/getAll', methods=['GET'])
    @cross_origin(supports_credentials=True)
    @limiter.limit("200 per hour", override_defaults=False)
    #@authToken.login_required
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

    # Allows the Boot (via escalation) to add alternatives to an existing question. Used as a feedback mechanism for NLP. 
    # Adds valid questions that people ask the BOT (and the bot wrongly classifies) as alternativate questions. 
    @API_app.route('/appendAlternative/<int:questionID>', methods=['POST'])
    @limiter.limit("200 per hour", override_defaults=False)
    #@authToken.login_required
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

    # Allows the BOT (via escalation) to add new Questions and Answers to the Knowledge Base 
    @API_app.route('/newEscalationAnswer', methods=['POST'])
    @limiter.limit("200 per hour", override_defaults=False)
    #@authToken.login_required
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
    
    # Allows the BOT to update the count on which Q&As have been handled every 12h
    @API_app.route('/updateCount', methods=['POST'])
    @limiter.limit("200 per hour", override_defaults=False)
    #@authToken.login_required
    def updateCount():
        try:
            if request.is_json:
                #Consume JSON payload {'items': [{'id': 1, 'count': 2}, {'id': 2, 'count': 3}]}
                jsonPayload = request.get_json()
                for item in jsonPayload["items"]:
                    questionID = item["id"]
                    count = item["count"]
                    # updateEntry(id, tag, question, answer, location, alternatives, count):
                    updateCount = queries.updateEntries(questionID, "", "", "", "", "", count)
                    
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

    # Update entries on the DB, to be used by the FrontEnd - Update Tab
    @API_app.route('/updateEntries/<int:questionID>', methods=['POST'])
    @cross_origin(supports_credentials=True)
    @limiter.limit("200 per hour", override_defaults=False)
    #@authToken.login_required
    def updateEntries(questionID):
        try:
            id = questionID
            tag = request.form.get('tag')
            question = request.form.get('question')
            answer = request.form.get('answer')
            location = request.form.get('location')
            alternatives = request.form.get('alternatives')
            count = request.form.get('count')
            if location is None:
                location = ""
            if count is None:
                count = ""
            if alternatives is None:
                alternatives = ""

            addEntries = queries.updateEntries(id, tag, question, answer, location, alternatives, count)     
            #Check questionID is valid
            if addEntries == False:
                err_questionID = "Error! Question ID: "+str(questionID)+" does not exist!"
                raise(err_questionID)
            #Check if there was a DB failure when updating entries
            if addEntries == "Failure":
                f_message = "Failed to update entries on the DB"
                raise(f_message)
            return("Sucessfully updated the entries on the DB, ID: "+str(id))
        
        except:
            if "err_questionID" in locals():
                abort(404, err_questionID)
            if "f_message" in locals():
                abort(500, f_message)
            else:
                abort(400)
#==================================================== API Endpoints =====================================================

    return API_app

# Main
if __name__ == "__main__":
    API_app = create_app()
    #Production
    #API_app.run(host=credentials.FLASK["Flask_HOST"], port=credentials.FLASK["Flask_PORT"], debug=True)

    #For DEV Testing purposes ONLY
    API_app.run(host=credentials.FLASK_devTest["Flask_HOST"], port=credentials.FLASK_devTest["Flask_PORT"], debug=True)