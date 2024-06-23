import pyodbc
from connectDB import conn;

def createRoom(room_name, owner_user_id):
    cursor = conn.cursor()
    query = "INSERT INTO Rooms (room_name, owner_user_id) OUTPUT INSERTED.room_id VALUES (?, ?)"

    try : 
        queryResult = cursor.execute(query, (room_name, owner_user_id))
    except pyodbc.IntegrityError as e:
        raise Exception("room name already exist")

    roomId = queryResult.fetchone()[0]

    cursor.commit()
    cursor.close()

    return {
        "roomId" : roomId,
        "roomName" : room_name,
        "ownerUserId" : owner_user_id,
    }

def getAllRooms():
    cursor = conn.cursor()

    query = "SELECT room_id, room_name, owner_user_id FROM rooms"

    queryResult = cursor.execute(query)

    rows = queryResult.fetchall()

    rooms = []

    for row in rows:
        rooms.append({
            "roomId" : row[0],
            "roomName" : row[1],
            "ownerUserId" : row[2]
        })

    cursor.commit()
    cursor.close()
    return rooms

def deleteRoom(room_id):
    cursor = conn.cursor()

    query = "DELETE FROM Rooms WHERE room_id = ?"

    queryResult = cursor.execute(query, (room_id,))

    if(cursor.rowcount == 0):
        raise Exception("room is not available")
    
    cursor.commit()
    cursor.close()
