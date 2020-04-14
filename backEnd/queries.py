import mysql.connector
import sys
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
def getAnswer(question):
	stmt = ("SELECT answer, location FROM qanda WHERE question=%s")
	data = (question)
	cursor.execute(stmt, data)
	result = cursor.fetchall()[0]
	answer, location = result[0], result[1]
	return answer, location

# Add an entry given a question, answer, and (optionally) a location
def addEntry(question, answer, location=None):
	try:
		if location is not None:
			cursor.execute("INSERT INTO qanda (question, answer, location) VALUES (%s %s %s)", (question, answer, location))
		else:
			cursor.execute("INSERT INTO qanda (question, answer) VALUES (%s %s)", (question, answer))
		db.commit()
	except:
		print("Error inserting into database")

# cursor.close()
# db.close()
