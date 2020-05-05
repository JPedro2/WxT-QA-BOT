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
        result = cursor.fetchall()
        # Check that the entry exists
        if not result:
            err_questionID = False
            raise(err_questionID)
        answer, location = result[0][0], result[0][1]
        #cursor.execute("UPDATE qanda SET count=count+1 WHERE id=%s", (questionID,))
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
        if "err_questionID" in locals():
            print("Error, Question ID does not exist")
            return err_questionID
        else:
            print("No answer matching that question could be found")
            return("Failure")

# Get an question, answer, alternatives and locatioon given a question ID
def getKnowledge(questionID):
    try:
        cursor, db = connectToDB()
        cursor.execute("SELECT question, answer, alternatives, location FROM qanda WHERE id=%s", (questionID,))
        result = cursor.fetchall()[0]
        question, answer, alternatives, location = result[0], result[1], result[2], result[3]
        closeConnectionToDB(db, cursor)
        #convert the response into a dictionary to then be easily jsonfied
        answer_resp = ["question", "answer", "alternatives", "location"]
        answer_resp = dict.fromkeys(answer_resp)
        answer_resp["question"]=question
        answer_resp["answer"]=answer
        answer_resp["alternatives"]=[]
        #Check if alternatives and/or location are empty. If so, they will be null/none
        if alternatives != "" and location != "":
            strOfAlternatives = alternatives
            listOfAlternatives=strOfAlternatives.split(" ; ")
            answer_resp["alternatives"]=listOfAlternatives
            answer_resp["location"]=location
        elif alternatives != "":
            strOfAlternatives = alternatives
            listOfAlternatives=strOfAlternatives.split(" ; ")
            answer_resp["alternatives"]=listOfAlternatives
        elif location != "":
            answer_resp["location"]=location
        
        return(answer_resp)
    
    except:
        print("No entries matching that ID could be found.")
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
            #check if alternatives is empty, which is only used when there are alternatives to a given question. If empty return an empty list
            if result[index][5] != "":
                strOfAlternatives=values[5]
                listOfAlternatives=strOfAlternatives.split(" ; ")
                item[index]["alternatives"]=listOfAlternatives
            else:
                item[index]["alternatives"]=[]    
        return(item)
    
    except:
        print("Failure")
        return("Failure")

# Add an entry given a tag, question, answer, and (optionally) a location and question alternatives
def addEntry(tag, question, answer, location, alternatives):
    try:
        cursor, db = connectToDB()
        cursor.execute("INSERT INTO qanda (tag, question, answer, location, count, alternatives) VALUES (%s, %s, %s, %s, %s, %s)", (tag, question, answer, location, 0, alternatives))
        closeConnectionToDB(db, cursor)
        print("Successfully inserted to the database; please do not refresh the page")
        return("Success")
    
    except:
        print("Error inserting into database")
        return("Failure")

def appendAlternative(questionID, alternative):
    try:
        cursor, db = connectToDB()
        
        #Check if questionID exists in the DB
        cursor.execute("SELECT question, alternatives FROM qanda WHERE id=%s", (questionID,))
        result = cursor.fetchall()
        if not result:
            err_questionID = False
            raise(err_questionID)
        
        #Check if alternatives is already populated: This avoids initially appending a white space if alternatives is empty
        alternatives = result[0][1]
        if alternatives == "":
            cursor.execute("UPDATE qanda SET alternatives=%s WHERE id=%s", (alternative, questionID,))
        else:
            cursor.execute("UPDATE qanda SET alternatives=CONCAT(IFNULL(alternatives,''),' ; ',%s) WHERE id=%s", (alternative, questionID,))
        
        closeConnectionToDB(db, cursor)
        print("Successfully added question alternative to Question ID:", questionID)
        return("Success")
    
    except:
        if "err_questionID" in locals():
            print("Error, Question ID does not exist")
            return err_questionID
        else:
            print("Error addding question alternative to Question ID:", questionID)
            return("Failure")

def updateEntries(id, tag, question, answer, location, alternatives, count):
    try:
        cursor, db = connectToDB()
        if id == "":
            return("id required")
        
        #Check if questionID exists in the DB
        cursor.execute("SELECT * FROM qanda WHERE id=%s", (id,))
        result = cursor.fetchall()
        if not result:
            err_questionID = False
            raise(err_questionID)
        # Update entire row if all fields are populated
        elif tag != "" and question != "" and answer != "" and alternatives != "" and count != "" and location != "":
            cursor.execute("UPDATE qanda SET tag=%s, question=%s, answer=%s, alternatives=%s, location=%s, count=%s WHERE id=%s", (tag, question, answer, alternatives, location, count, id,))
            print("Successfully updated the entire row on the database, ID: "+str(id))
        else:
            if tag != "" and question != "" and answer != "" and alternatives != "" and location != "":
                cursor.execute("UPDATE qanda SET tag=%s, question=%s, answer=%s, alternatives=%s, location=%s WHERE id=%s", (tag, question, answer, alternatives, location, id,))
                print("Successfully updated the tag, the question, the answer, the alternatives and the location fields on the database")
            elif tag != "" and question != "" and answer != "" and alternatives != "":
                cursor.execute("UPDATE qanda SET tag=%s, question=%s, answer=%s, alternatives=%s WHERE id=%s", (tag, question, answer, alternatives, id,))
                print("Successfully updated the tag, the question, the answer and the alternatives fields on the database")
            elif tag != "" and question != "" and answer != "":
                cursor.execute("UPDATE qanda SET question=%s, answer=%s WHERE id=%s", (question, answer, id,))
                print("Successfully updated the tag, the question and the answer fields on the database")
            elif question != "":
                cursor.execute("UPDATE qanda SET question=%s WHERE id=%s", (question, id,))
                print("Successfully updated the question field on the database")
            elif answer != "":
                cursor.execute("UPDATE qanda SET answer=%s WHERE id=%s", (answer, id,))
                print("Successfully updated the answer field on the database")
            elif alternatives != "":
                cursor.execute("UPDATE qanda SET alternatives=%s WHERE id=%s", (alternatives, id,))
                print("Successfully updated the alternatives field on the database")
            elif count != "": #update the count
                cursor.execute("UPDATE qanda SET count=%s WHERE id=%s", (count, id,))
                print("Successfully updated the count field on the database")
        closeConnectionToDB(db, cursor)
        print("Successfully updated the database")
        return("Success")
    
    except:
        if "err_questionID" in locals():
            print("Error, Question ID does not exist")
            return err_questionID
        else:
            print("Error addding question alternative to Question ID:", questionID)
            return("Failure")