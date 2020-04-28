from collections import OrderedDict 
import mysql.connector
import sys

# Set working directory
sys.path.append('/home/WxT-QA-BOT')
import credentials

# Connect to MySQL database
def connectToDB():
    try:
        db = mysql.connector.connect(
            host=credentials.DB["host"],
            user=credentials.DB["user"],
            passwd=credentials.DB["passwd"],
            database=credentials.DB["database"]
        )
        # Instantiate cursor
        cursor = db.cursor()
        print("Sucessfully connected to DB")
        return cursor, db
        
    except:
        print("Failed to connect to DB. MySQL Connection not available.")

# Close cursor and connection to DB
def closeConnectionToDB(db, cursor):
    try:
        db.commit()
        cursor.close()
        db.close()
    except:
        print("Failed to close connection to DB")

# Get an answer given a question
def getAnswer(questionID):
    try:
        cursor, db = connectToDB()
        cursor.execute("SELECT answer, location FROM qanda WHERE id=%s", (questionID,))
        result = cursor.fetchall()[0]
        answer, location = result[0], result[1]
        cursor.execute("UPDATE qanda SET count=count+1 WHERE id=%s", (questionID,))
        closeConnectionToDB(db, cursor)
        #convert the response into a dictionary to then be easily jsonfied
        answer_resp = ["answer", "location"]
        answer_resp = dict.fromkeys(answer_resp)
        #check if location is empty, which is only used when files are submited with answers
        if location != "":
            answer_resp["answer"]=answer
            answer_resp["location"]=location
        else:
            answer_resp["answer"]=answer
        return(answer_resp)
    except:
        print("No answer matching that question could be found")
        return("Failure")

# Get all questions
def getAllQuestions():
    try:
        cursor, db = connectToDB()
        cursor.execute("SELECT id, question FROM qanda")
        #cursor.execute("SELECT question FROM aqanda")
        result = cursor.fetchall()
        closeConnectionToDB(db, cursor)
        questions = [None] * len(result)
        for index, values in enumerate(result): 
            resp = ["id","question"]
            resp = dict.fromkeys(resp)
            questions[index]=resp
            questions[index]["id"]=values[0]
            questions[index]["question"]=values[1]

        return(questions)
    except:
        print("Failure")
        return("Failure")

def getAll():
    try:
        cursor, db = connectToDB()
        cursor.execute("SELECT id, question, answer, location, count, alternatives FROM qanda")
        result = cursor.fetchall()
        closeConnectionToDB(db, cursor)
        item = [None] * len(result)
        for index, values in enumerate(result): 
            resp = ["id","question","answer", "location", "count", "alternatives"]
            resp = dict.fromkeys(resp)
            item[index]=resp
            item[index]["id"]=values[0]
            item[index]["question"]=values[1]
            item[index]["answer"]=values[2]
            #check if location is empty, which is only used when files are submited with answers
            if result[index][3] != "":
                item[index]["location"]=values[3]

            item[index]["count"]=values[4]
            #check if alternatives is empty, which is only used when there are alternatives to a given question
            if result[index][5] != "":
                item[index]["alternatives"]=values[5]
            
        return(item)
    except:
        print("Failure")
        return("Failure")

# Add an entry given a tag, question, answer, and (optionally) a location
def addEntry(tag, question, answer, location=None, alternatives=""):
    try:
        cursor, db = connectToDB()
        if location is not None:
            cursor.execute("INSERT INTO qanda (tag, question, answer, location, count, alternatives) VALUES (%s, %s, %s, %s, %s, %s)", (tag, question, answer, "Location", 0, ""))
        else:
            cursor.execute("INSERT INTO qanda (tag, question, answer, location, count, alternatives) VALUES (%s, %s, %s, %s, %s, %s)", (tag, question, answer, "", 0, ""))
        closeConnectionToDB(db, cursor)
        print("Successfully inserted to the database; please do not refresh the page")
        return("Success")
    except:
        print("Error inserting into database")
        return("Failure")

def updateEntry(id, tag, question, answer, location):
    try:
        cursor, db = connectToDB()
        if id is None:
            return("id required")
        else:
            cursor.execute("UPDATE qanda SET tag=%s, question=%s, answer=%s, location=%S WHERE id=%s)", (tag, question, answer, location, id))
        closeConnectionToDB(db, cursor)
        print("Successfully updated the database")
        return("Success")
    except:
        print("Error updating the database")
        return("Failure")