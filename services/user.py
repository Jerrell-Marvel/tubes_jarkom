from connectDB import conn
import pyodbc

def register(username, password):
    cursor = conn.cursor()
    query = "INSERT INTO Users (username, password) OUTPUT INSERTED.user_id  VALUES (?, ?)"

    try : 
        queryResult = cursor.execute(query, (username, password))
    except pyodbc.IntegrityError as e:
        raise Exception("username already exist")

    userId = queryResult.fetchone()[0]

    cursor.commit()
    cursor.close()

    return userId

def login(usernameInput, passwordInput):
    cursor = conn.cursor()

    query = "SELECT user_id, username, password FROM users WHERE username = ?"

    queryResult = cursor.execute(query, (usernameInput,))

    userData = queryResult.fetchone()

    if userData is None :
        raise Exception("user not found")
    
    username = userData[1]
    userPassword = userData[2]

    if passwordInput != userPassword:
        raise Exception("wrong password")
    
    cursor.close()
    return {
        "user_id" : userData[0],
        "username" : username
    }