import os
import sys
import time
import logging
import queries
import queries_user
from flask import Flask, jsonify, request, abort, g
import flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS, cross_origin
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from google.cloud import storage

def create_app():
    
    # Instantiate Flask app
    API_app = flask.Flask(__name__)
    
    # Instantiate Flask-CORS middleware
    CORS(API_app)

    # Instantiate API config for uploads
    ALLOWED_EXTENSIONS = os.environ['Flask_AllowedExtensions']
    API_app.config['MAX_CONTENT_LENGTH'] = 300 * 1024 * 1024 #300MB maximum allowed file size to be uploaded                    
    API_app.config['UPLOAD_FOLDER'] = os.environ['Flask_UploadFolder']

    # Instantiate API config for Auth
    API_app.config['SECRET_KEY'] = os.environ['Flask_SecretKey']
    auth = HTTPBasicAuth()
    authToken = HTTPTokenAuth('Bearer')

    # Instantiate GCP Storage Credentials
    bucket_name = os.environ['GCP_bucketName']
    GCP_Service_Acct = os.environ['GCP_ServiceAcct']

    # Instantiate default rate limit of 10000 per day, and 1000 per hour applied to all routes for API service
    limiter = Limiter(
        API_app,
        key_func=get_remote_address,
        default_limits=["10000 per day","1000 per hour"]
    )

    # Gunicorn has its own loggers and handlers. 
    # Sync the Flask application to use those handlers and set --log-level=info (or other level) when invoking Gunicorn
    if __name__ != "__main__":
        gunicorn_logger = logging.getLogger("gunicorn.error")
        API_app.logger.handlers = gunicorn_logger.handlers
        API_app.logger.setLevel(gunicorn_logger.level)

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

    @auth.get_user_roles
    def get_user_roles(user):
        try:
            user=user.username
            userRole = queries_user.getRole(user)
            if userRole == "Failure":
                f_message = "Error getting role from the DB with Username: "+str(user)
                raise(f_message)
            return userRole
        
        except:
            if "f_message" in locals():
                abort(500, f_message)

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
            API_app.logger.info("Sucessfully validated the user: "+str(user))
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
            API_app.logger.info("Sucessfully validated the user: "+str(user))
            return True

        except:
            abort(400, "Error validating the token")

    @API_app.route('/auth/token')
    @auth.login_required
    def get_auth_token():
        try:
            token = generate_auth_token(g.user,86400)
            API_app.logger.info("Sucessfully generated a token for the user: "+str(g.user)+" and it is valid for 24h.")
            return jsonify({'token': token.decode('ascii'), 'duration': 86400})
        
        except:
            abort(400, "Error generating Token")

    @API_app.route('/auth/checkPosture')
    @authToken.login_required
    def checkPosture():
        try:
            return ("Token is valid", 200)
        
        except:
            abort(500, "Error checking  if token is valid")

    @API_app.route('/newUsers', methods=['POST'])
    @auth.login_required(role='admin')
    def new_user():
        try:
            username = request.json.get('username')
            password = request.json.get('password')
            role = request.json.get('role')
            if username is None or password is None or role is None: # missing arguments
                err_missingInfo = "Information Missing! Please fill use both the username and the password fields."
                raise(err_missingInfo)
            if username == "" or password == "" or role =="": # empty arguments
                err_empty = "Empty credentials! Please fill in both the username and the password fields."
                raise(err_empty)
            if queries_user.getUser(username) is not None: # existing user
                err_userExists = "Username: "+str(username)+" already exists. Please use a different username."
                raise(err_userExists)    
            
            #hash the password
            hashedPassword = hash_password(password)
            #Add both user and hashed password to the DB
            newUser_ID, newUser = queries_user.addUser(username, hashedPassword, role)
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
    
#======================================================= API AUTH =======================================================

#=================================================== API File Upload ====================================================
    def allowed_file(filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def upload_blob(source_file_name, destination_blob_name):
        try:
            # destination_blob_name is "/atttachmentDoc-for-<questionID>.<file_extension>"
            # source_file_name is "/tmp-uploadFiles/<file>"
            storage_client = storage.Client.from_service_account_json(GCP_Service_Acct)
            bucket = storage_client.bucket(bucket_name)
            
            blob = bucket.blob(destination_blob_name)
            blob.upload_from_filename(source_file_name)

            location = "https://storage.googleapis.com/"+bucket_name+"/"+destination_blob_name

            API_app.logger.info("Sucessfully uploaded a file to GCP Cloud Storage, URL: "+location)
            return location
        
        except:
            API_app.logger.info("Error uploading file to GCP Cloud Storage")
            return None
    
    def rename_blob(blob_name):
        try:
            #Renames the object/attachment-file stored on GCP Storage, used when changing the current attached file on the DB
            #At any given time the maximum GCP will old per question is 2 items: "old_UploadedFile" and the up-to-date file 
            storage_client = storage.Client.from_service_account_json(GCP_Service_Acct)
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            #stats = storage.Blob(bucket=bucket, name=blob_name).exists(storage_client)
            new_name=blob_name.split('/')[-2]+"/"+"old_UploadedFile"
            new_blob = bucket.rename_blob(blob, new_name)
            return True

        except:
            API_app.logger.debug("Error renaming file from GCP Cloud Storage")
            return None

    def delete_blob(blob_name):
        try:
            # Deletes the object/attachment-file stored on GCP Storage, used when deleting a question from the DB
            storage_client = storage.Client.from_service_account_json(GCP_Service_Acct)
            bucket = storage_client.bucket(bucket_name)
            #iterate over the folder to delete all files. There will never be more than 2 files in a question folder
            blobs = bucket.list_blobs(prefix=blob_name)
            for blob in blobs:
                blob.delete()
            return True

        except:
            API_app.logger.error("Error deleting file from GCP Cloud Storage")
            return None

    def add_fileToDB(file, questionID):
        try:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_extension = filename.rsplit('.', 1)[1].lower()
                source_file_name = os.path.join(API_app.config['UPLOAD_FOLDER'], filename)
                file.save(source_file_name)
                API_app.logger.info("File temporarily Uploaded from the FrontEnd to the BackEnd")
            else:
                err_fileExtension = True
                raise(err_fileExtension)
            
            #Before submiting the file to GCP Storage check if a question-attachment file already exists
            #If so, change the name of the current file stored to "old_UploadedFile" and store the new file
            checkUrl = queries.getKnowledge(questionID)
            location = checkUrl["location"]
            if location:
                #grab the part of the URL that specifies the path to the file on GCP
                renameFilePath=location.split('/')[-2]+"/"+location.split('/')[-1]
                if rename_blob(renameFilePath):
                    API_app.logger.info("Attached file for question ID: "+str(questionID)+" has been renamed on GCP.")
                else:
                    #delete temporarily uploaded file
                    delete_tmpFile = os.remove(source_file_name)
                    ErrReNameGCPfile = True
                    raise(ErrReNameGCPfile)
            
            destination_blob_name = "QuestionID-"+str(questionID)+"/"+filename
            #Submit file to GCP Cloud Storage to be used by the BOT
            location = upload_blob(source_file_name, destination_blob_name)
            if location:
                #add the file's URL for download to the location on the database base
                addLocation = queries.updateEntries(questionID, "", "", "", location, "", "")
                #delete temporarily uploaded file
                delete_tmpFile = os.remove(source_file_name)
                API_app.logger.info("Sucessfully uploaded a file to GCP Cloud Storage. URL: "+str(location))
                return("",201)
            else:
                delete_tmpFile = os.remove(source_file_name)
                ErrUploadGCPfile = True
                raise(ErrUploadGCPfile)
            
        except:
            if "err_fileExtension" in locals():
                return "err_fileExtension"
            if "ErrReNameGCPfile" in locals():
                return "ErrReNameGCPfile"
            if "ErrUploadGCPfile" in locals():
                return "ErrUploadGCPfile"
            else:
                return None

    #URL needs to contain the questionID that the file needs to be associated with 
    @API_app.route('/uploadFile/<int:questionID>', methods=['POST'])
    @authToken.login_required
    def upload_file(questionID):
        try:
            checkQuestionID = queries.getAnswer(questionID)
            if checkQuestionID == False:
                err_questionID = "Error! Question ID: "+str(questionID)+" does not exist!"
                raise(err_questionID)

            # check if the post request has the file part
            if 'file' not in request.files:
                err_noFile = "No file submitted"
                raise(err_noFile)
            file = request.files['file']

            addFile=add_fileToDB(file, questionID)
            if addFile == "err_fileExtension":
                err_fileExtension = "This file extention is not allowed. Please only submit allowed file extensions."
                raise(err_fileExtension)
            if addFile == "ErrReNameGCPfile":
                ErrReNameGCPfile = "Error renaming file from GCP on Question ID: "+str(questionID)
                raise(ErrReNameGCPfile)
            if addFile == "ErrUploadGCPfile":
                ErrUploadGCPfile = "Error uploading file to GCP for Question ID: "+str(questionID)
                raise(ErrUploadGCPfile)
            if addFile is None:
                raise

            return("",200)
            
        except:
            if "err_questionID" in locals():
                abort(404, err_questionID)
            if "err_noFile" in locals():
                abort(400, err_noFile)
            if "err_fileExtension" in locals():
                abort(400, err_fileExtension)
            if "ErrReNameGCPfile" in locals():
                abort(500, ErrReNameGCPfile)
            if "ErrUploadGCPfile" in locals():
                abort(500, ErrUploadGCPfile)
            else:
                abort(500)

#=================================================== API File Upload ====================================================

#==================================================== API Endpoints =====================================================
    # getAnswer for the Bot to grab answers based on Question ID
    @API_app.route('/getAnswer/<int:questionID>', methods=['GET'])
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
    def getKnowledge(questionID):
        try:
            knowledge = queries.getKnowledge(questionID)
            if knowledge == False:
                err_questionID = "Error! Question ID: "+str(questionID)+" does not exist!"
                raise(err_questionID)
            if knowledge == "Failure":
                f_message = "Error! Failure whilst retrieving the information from the database"
                raise(f_message)
            return jsonify(knowledge)
        
        except:
            if "err_questionID" in locals():
                abort(404, err_questionID)
            if "f_message" in locals():
                abort(500, f_message)
            else:
                abort(400)

    # addEntry to add Questions, Answers and Alternative Questions from the FrontEnd: Submit tab
    @API_app.route('/addEntry', methods=['POST'])
    @authToken.login_required
    def addEntry():
        try:
            tag = request.form.get('tag')
            question = request.form.get('question')
            answer = request.form.get('answer')
            alternatives = request.form.get('alternatives')
        
            newQuestionID = queries.addEntry(tag, question, answer, alternatives)
            if newQuestionID == "Failure":
                f_message = "Failed to add Entry to DB"
                raise(f_message)
            
            #Check if a file is part of the request to be updated or added to the question
            if 'file' in request.files:
                file = request.files['file']
                addFile=add_fileToDB(file, newQuestionID)
                if addFile == "err_fileExtension":
                    #if there's an error uploading the file when adding a completely new questioon, 
                    #we need to delete the newly added question otherwise the question still gets created
                    queries.deleteQuestion(newQuestionID)
                    err_fileExtension = "File extentions is not allowed. Please only submit allowed file extensions."
                    raise(err_fileExtension)
                if addFile == "ErrReNameGCPfile":
                    queries.deleteQuestion(newQuestionID)
                    ErrReNameGCPfile = "Error renaming file from GCP on Question ID: "+str(newQuestionID)
                    raise(ErrReNameGCPfile)
                if addFile == "ErrUploadGCPfile":
                    queries.deleteQuestion(newQuestionID)
                    ErrUploadGCPfile = "Error uploading file to GCP for Question ID: "+str(newQuestionID)
                    raise(ErrUploadGCPfile)
                if addFile is None:
                    raise
                API_app.logger.info("File sucessfully attached to Question ID: "+str(newQuestionID))
            
            return (newQuestionID, 201)
        
        except:
            if "f_message" in locals():
                abort(500, f_message)
            if "err_fileExtension" in locals():
                abort(400, err_fileExtension)
            if "ErrReNameGCPfile" in locals():
                abort(500, ErrReNameGCPfile)
            if "ErrUploadGCPfile" in locals():
                abort(500, ErrUploadGCPfile)
            else:
                abort(400)

    @API_app.route('/deleteQuestion/<int:questionID>', methods=['DELETE'])
    @authToken.login_required
    def deleteQuestion(questionID):
        try:
            deleteQuestion = queries.getKnowledge(questionID)
            if not deleteQuestion:
                err_questionID = "Error! Question ID: "+str(questionID)+" does not exist!"
                raise(err_questionID)

            #Before deleting the question from the DB check if there is a file attached to that question and delete it from GCP
            location = deleteQuestion["location"]
            if location:
                #grab the part of the URL that specifies the path to the file on GCP
                FilePath=location.split('/')[-2]
                if delete_blob(FilePath):
                    API_app.logger.info("Attached file for question ID: "+str(questionID)+" has been removed from GCP.")
                else:
                    API_app.logger.error("Error deleting file from GCP for Question ID: "+str(questionID))
            
            _deleteQuestion = queries.deleteQuestion(questionID)
            if not _deleteQuestion:
                API_app.logger.error("Error deleting entries of Question ID: "+str(questionID)+" from the database.")
                f_message = "Error deleting entries of Question ID: "+str(questionID)+" from the database."
                raise(f_message)
            API_app.logger.info("Successfully deleted all entries of Question ID: "+str(questionID)+" from the database.")
            return("",204)
        
        except:
            if "err_questionID" in locals():
                abort(404, err_questionID)
            if "f_message" in locals():
                abort(500, f_message)
            else:
                abort(400)

    # getAllQuestions to be used by the Bot and the FE: Update and Query Tabs
    @API_app.route('/getAllQuestions', methods=['GET'])
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
    @authToken.login_required
    def appendAlternative(questionID):
        try:
            if request.is_json:
                #Consume JSON payload {"question": "Here is an additional question"}
                jsonPayload = request.get_json()
                alternative = jsonPayload["question"]
                if alternative == "":
                    err_alternativeRequired = "Error! The alternative question field is empty."
                    raise(err_alternativeRequired)
                appendAlternative = queries.appendAlternative(questionID, alternative)
                
                #if appendAlternative == "Duplicate":
                #    err_duplicate = "Error! Question alternative already exists"
                #    raise(err_duplicate)

                if appendAlternative == False:
                    err_questionID = "Error! Question ID: "+str(questionID)+" does not exist!"
                    raise(err_questionID)
                
                if appendAlternative == "Failure":
                    f_message = "Error appending alternative to Question ID: "+str(questionID)
                    raise(f_message)
                
                API_app.logger.info("Successfully added question alternative to Question ID:", questionID)
                return("",201)
            else:
                request_isNotJSON = "Error appending alternative to Question ID: "+str(questionID)+". The request POSTed is NOT in JSON format."
                raise(request_isNotJSON)
        
        except:
            #if "err_duplicate" in locals():
            #    abort(400, err_duplicate)
            if "err_alternativeRequired" in locals():
                abort(400, err_alternativeRequired)
            if "err_questionID" in locals():
                abort(404, err_questionID)
            if "f_message" in locals():
                abort(500, f_message)
            if "request_isNotJSON" in locals():
                abort(415, request_isNotJSON)
            else:
                abort(400)

    # Allows the BOT (via escalation) to add new Questions and Answers to the Knowledge Base 
    @API_app.route('/newEscalationAnswer', methods=['POST'])
    @authToken.login_required
    def newEscalationAnswer():
        try:
            if request.is_json:
                #Consume JSON payload {"question": "Here is an additional question"}
                jsonPayload = request.get_json()
                question = jsonPayload["question"]
                answer = jsonPayload["answer"]
                
                if question == "" or answer == "":
                    err_emptyParameters = "Error! 'question' AND 'answer' parameters cannot be empty"
                    raise(err_emptyParameters)
                elif type(question) != str or type(answer) != str:
                    err_notString = "Error! 'question' AND 'answer' parameters MUST be strings"
                    raise(err_notString)
                
                #This API endpoint is only handled by the BOT when the Question gets escalated and it's added by the Webex Warriors
                tag = "Escalation: Webex Warriors"
                #alternatives are empty as it is not possible to populate these via the escalation workflow
                alternatives = ""
                NewEscalationQAid = queries.addEntry(tag, question, answer, alternatives)
                
                if NewEscalationQAid == "Failure":
                    f_message = "Failed to add a new question and answer from the Escalation Webex Warriors workflow"
                    raise(f_message)
                
                API_app.logger.info("Successfully added a question and answer from the Escalation Webex Warriors workflow, ID: "+NewEscalationQAid)
                return(NewEscalationQAid, 201)
            else:
                request_isNotJSON = "Error adding a new question and answer from the Escalation Webex Warriors workflow. The request POSTed is NOT in JSON format."
                raise(request_isNotJSON)
        except:
            if "err_emptyParameters" in locals():
                abort(400, err_emptyParameters)
            if "err_notString" in locals():
                abort(400, err_notString)
            if "f_message" in locals():
                abort(500, f_message)
            if "request_isNotJSON" in locals():
                abort(415, request_isNotJSON)
            else:
                abort(400)
    
    # Allows the BOT to update the count on which Q&As have been handled every 12h
    @API_app.route('/updateCount', methods=['PUT'])
    @authToken.login_required
    def updateCount():
        try:
            if request.is_json:
                #Consume JSON payload {'items': [{'id': 1, 'count': 2}, {'id': 2, 'count': 3}]}
                jsonPayload = request.get_json()
                for item in jsonPayload["items"]:
                    questionID = item["id"]
                    count = item["count"]
                    
                    if type(questionID) != int or type(count) != int:
                        err_type = "Error! The 'questionID' AND 'count' MUST be integers."
                        raise(err_type)
                    if count == "":
                        err_COUNTrequired = "Error! Both the 'questionID' AND 'count' fields need to be populated."
                        raise(err_COUNTrequired)

                    # updateEntry(id, tag, question, answer, location, alternatives, count):
                    updateCount = queries.incrementCount(questionID, count)
                    
                    if updateCount == "id required":
                        err_IDrequired = "Error! 'questionID' was not provided."
                        raise(err_IDrequired)
                    
                    if updateCount == False:
                        err_questionID = "Error! Question ID: "+str(questionID)+" does not exist!"
                        raise(err_questionID)
                    
                    if updateCount == "Failure":
                        f_message = "Error updating count on Question ID: "+str(questionID)
                        raise(f_message)
                
                API_app.logger.info("Successfully incremented the count field on the database")
                return("",204)
            
            else:
                request_isNotJSON = "Error incrementing the count. The request is NOT in JSON format."
                raise(request_isNotJSON)
        
        except:
            if "err_type" in locals():
                abort(400, err_type)
            if "err_COUNTrequired" in locals():
                abort(404, err_COUNTrequired)
            if "err_IDrequired" in locals():
                abort(404, err_IDrequired)
            if "err_questionID" in locals():
                abort(404, err_questionID)
            if "f_message" in locals():
                abort(500, f_message)
            if "request_isNotJSON" in locals():
                abort(415, request_isNotJSON)
            else:
                abort(400)

    # Update entries on the DB, to be used by the FrontEnd - Update Tab
    @API_app.route('/updateEntries/<int:questionID>', methods=['PUT'])
    @authToken.login_required
    def updateEntries(questionID):
        try:
            id = questionID
            tag = request.form.get('tag')
            question = request.form.get('question')
            answer = request.form.get('answer')
            location = request.form.get('location')
            alternatives = request.form.get('alternatives')
            deleteFile = request.form.get('deleteFile')

            #Make sure count is an int 
            #count will be 'None' if the field is not present in the form OR if it cannot be converted to an integer
            count = request.form.get('count', type=int)
            if location is None:
                location = ""
            if alternatives is None:
                alternatives = ""
            if count is None:
                count = ""
            deleteFile = deleteFile.lower()
            if deleteFile == "true":
                deleteFile = True
            else:
                deleteFile = False

            updateEntries = queries.updateEntries(id, tag, question, answer, location, alternatives, count)     
            #Check questionID is valid
            if updateEntries == False:
                err_questionID = "Error! Question ID: "+str(questionID)+" does not exist!"
                raise(err_questionID)
            #Check if there was a DB failure when updating entries
            if updateEntries == "Failure":
                f_message = "Failed to update entries on the DB"
                raise(f_message)
            
            #Check if a file is part of the request to be updated or added to the question
            if 'file' in request.files:
                file = request.files['file']
                addFile=add_fileToDB(file, questionID)
                if addFile == "err_fileExtension":
                    err_fileExtension = "This file extention is not allowed. Please only submit allowed file extensions."
                    raise(err_fileExtension)
                if addFile == "ErrReNameGCPfile":
                    ErrReNameGCPfile = "Error renaming file from GCP on Question ID: "+str(questionID)
                    raise(ErrReNameGCPfile)
                if addFile == "ErrUploadGCPfile":
                    ErrUploadGCPfile = "Error uploading file to GCP for Question ID: "+str(questionID)
                    raise(ErrUploadGCPfile)
                if addFile is None:
                    raise
                API_app.logger.info("File sucessfully attached to Question ID: "+str(id))
            
            #Check if we just need to delete the file attached to the answer from the DB
            if deleteFile:
                #Make sure check there is a file attached to that question (to avoid errors) and delete it from GCP
                questionToDeleteFile = queries.getKnowledge(questionID)
                fileToDelete = questionToDeleteFile["location"]
                if fileToDelete:
                    #grab the part of the URL that specifies the path to the file on GCP
                    FilePath=fileToDelete.split('/')[-2]
                    if delete_blob(FilePath):
                        API_app.logger.info("Attached file for question ID: "+str(questionID)+" has been removed from GCP.")
                    else:
                        API_app.logger.error("Error deleting file from GCP for Question ID: "+str(questionID))
                #Delete file location entry from the DB
                deletefile_DB = queries.deleteFileLocation(questionID)
                if deletefile_DB:
                    API_app.logger.info("File location for question ID: "+str(questionID)+" has been removed from Database.")
                else:
                    API_app.logger.error("Error deleting file location from Database for Question ID: "+str(questionID))

            API_app.logger.info("Sucessfully updated the entries on the DB, ID: "+str(id))
            return(str(id), 200)
        
        except:
            if "err_questionID" in locals():
                abort(404, err_questionID)
            if "f_message" in locals():
                abort(500, f_message)
            if "err_fileExtension" in locals():
                abort(400, err_fileExtension)
            if "ErrReNameGCPfile" in locals():
                abort(500, ErrReNameGCPfile)
            if "ErrUploadGCPfile" in locals():
                abort(500, ErrUploadGCPfile)
            else:
                abort(400)
#==================================================== API Endpoints =====================================================

    return API_app

# Main
if __name__ == "__main__":
    API_app = create_app()

    #For DEV Testing purposes ONLY
    API_app.run(host=os.environ['Flask_host'], port=os.environ['Flask_port'], debug=True)