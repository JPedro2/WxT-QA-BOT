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

# Add a user and the hashed Password to the DB
def addUser(user, hashedPassword):
    try:
        cursor, db = connectToDB()
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (user, hashedPassword))
        cursor.execute("SELECT id FROM users WHERE username=%s", (user,))
        userID = cursor.fetchall()[0][0]
        closeConnectionToDB(db, cursor)
        print("Successfully added user to the database")
        return userID, user
    except:
        print("Error adding user into the database")
        return("Failure")

def getUser(user):
    try:
        cursor, db = connectToDB()
        cursor.execute("SELECT username FROM users WHERE username=%s", (user,))
        result = cursor.fetchall()
        if not result:
            err_userNotFound = True
            closeConnectionToDB(db, cursor)
            raise(err_user)
        
        user = result[0][0]
        closeConnectionToDB(db, cursor)
        return(user)
    
    except:
        if "err_userNotFound" in locals():
            print("Error! Username: "+str(user)+" does not exist.")
            return None
        else:
            print("Error getting Username:"+str(user)+" from the database.")
            return("Failure")

def getUserbyID(id):
    try:
        cursor, db = connectToDB()
        cursor.execute("SELECT username FROM users WHERE id=%s", (id,))
        result = cursor.fetchall()
        if not result:
            err_userNotFound = True
            closeConnectionToDB(db, cursor)
            raise(err_user)
        
        user = result[0][0]
        closeConnectionToDB(db, cursor)
        return(user)
    
    except:
        if "err_userNotFound" in locals():
            print("Error! User ID: "+str(id)+" does not exist.")
            return None
        else:
            print("Error getting username with ID: "+str(id)+" from the database.")
            return("Failure")

def getPasswordHash(user):
    try:
        cursor, db = connectToDB()
        cursor.execute("SELECT password FROM users WHERE username=%s", (user,))
        result = cursor.fetchall()
        if not result:
            err_userNotFound = True
            closeConnectionToDB(db, cursor)
            raise(err_user)
        
        passwordHash = result[0][0]
        closeConnectionToDB(db, cursor)
        return(passwordHash)
    
    except:
        if "err_userNotFound" in locals():
            print("Error! Failed to get hashed password as username: "+str(user)+" does not exist.")
            return None
        else:
            print("Error getting hashed password from Username: "+str(id)+" from the database.")
            return("Failure")