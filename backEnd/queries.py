import mysql.connector
import sys

# Set working directory
sys.path.append('/home/WxT-QA-BOT')
import credentials

# Connect to MySQL database
db = mysql.connector.connect(
    host=credentials.DB["host"],
    user=credentials.DB["user"],
    passwd=credentials.DB["passwd"],
    database=credentials.DB["database"]
)

# Instantiate cursor
cursor = db.cursor()

# Get an answer given a question
def getAnswer(questionID):
    try:
        cursor.execute("SELECT answer, location FROM qanda WHERE id=%s", (questionID,))
        result = cursor.fetchall()[0]
        answer, location = result[0], result[1]
        cursor.execute("UPDATE qanda SET count=count+1 WHERE id=%s", (questionID,))
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
        cursor.execute("SELECT question FROM qanda")
        result = cursor.fetchall()
        print(result)
        return(result)
    except:
        print("Failure")
        return("Failure")

# Add an entry given a tag, question, answer, and (optionally) a location
def addEntry(tag, question, answer, location=None):
    try:
        if location is not None:
            cursor.execute("INSERT INTO qanda (tag, question, answer, location, count) VALUES (%s, %s, %s, %s, %s)", (tag, question, answer, "Location", 0))
        else:
            cursor.execute("INSERT INTO qanda (tag, question, answer, location, count) VALUES (%s, %s, %s, %s, %s)", (tag, question, answer, "", 0))
        db.commit()
        print("Successfully inserted to the database; please do not refresh the page")
        return("Success")
    except:
        print("Error inserting into database")
        return("Failure")

# cursor.close()
# db.close()
