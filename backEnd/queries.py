import mysql.connector
import credentials

db = mysql.connector.connect(
	host=credentials.DB["host"],
	user=credentials.DB["user"],
	passwd=credentials.DB["passwd"],
	database=credentials.DB["qanda"]
)

cursor = db.cursor()

def getAnswer(question):
	stmt = ("SELECT answer, location FROM qanda WHERE question=%s")
	data = (question)
	cursor.execute(stmt, data)
	result = cursor.fetchall()[0]
	answer, location = result[0], result[1]
	return answer, location

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