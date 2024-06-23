from connectDB import conn
from services import room as roomServices, user as userServices

import socket
import threading

activeUsers = {}
rooms = {}

# ambil dlu rooms yang sebelumnya ada di db
initRooms = roomServices.getAllRooms()
for room in initRooms:
    rooms[room["roomId"]] = {
                        "roomName" : room["roomName"],
                        "ownerUserId" : room["ownerUserId"],
                        "participants" : set()
                    }

# broadcast message ke semua orang yang ada di room
def broadcastMessage(roomId:int, message:str, senderId):
    targetRoom = rooms[roomId]

    if targetRoom is None : 
        raise Exception("room not found")
    
    participants = targetRoom["participants"]

    for participantId in participants:
        broadcastMessage = "MESSAGE;"
        if participantId != senderId: 
            broadcastMessage += activeUsers[senderId]["username"] + " :\n"
            
        else : 
            broadcastMessage += "You :\n"

        broadcastMessage += message
        participantConn = activeUsers[participantId]["conn"]
        participantConn.send(broadcastMessage.encode("utf-8"))

# broadcast jika ada yang join
def joinRoomBroadcast(roomId, senderId):
    targetRoom = rooms[roomId]

    if targetRoom is None : 
        raise Exception("room not found")
    
    participants = targetRoom["participants"]

    for participantId in participants:
        broadcastMessage = "MESSAGE;"

        print("participant : ", participantId)
        if participantId != senderId: 
            broadcastMessage += activeUsers[senderId]["username"] + " "
            
        else : 
            broadcastMessage += "You "

        broadcastMessage += "joined the room"
        participantConn = activeUsers[participantId]["conn"]
        participantConn.send(broadcastMessage.encode("utf-8"))

# broadcast jika ada yang leave
def leaveRoomBroadcast(roomId, leftUserId):
    targetRoom = rooms[roomId]

    if targetRoom is None : 
        raise Exception("room not found")
    
    participants = targetRoom["participants"]
    leftUsername = activeUsers[leftUserId]["username"]

    for participantId in participants:
        broadcastMessage = f"MESSAGE;{leftUsername} left the room"
        participantConn = activeUsers[participantId]["conn"]
        participantConn.send(broadcastMessage.encode("utf-8"))

# broadcast jika ada yang di kick
def kickBroadcast(roomId, kickedUserId):
    targetRoom = rooms[roomId]

    if targetRoom is None : 
        raise Exception("room not found")
    
    participants = targetRoom["participants"]
    leftUsername = activeUsers[kickedUserId]["username"]

    for participantId in participants:
        broadcastMessage = f"MESSAGE;{leftUsername} has been kicked"
        participantConn = activeUsers[participantId]["conn"]
        participantConn.send(broadcastMessage.encode("utf-8"))

# broadcast jika roomnya dihapus
def deleteRoomBroadcast(roomId):
    targetRoom = rooms[roomId]
    ownerUserId = rooms[roomId]["ownerUserId"]

    if targetRoom is None:
        raise Exception("room not found")
    
    participants = targetRoom["participants"]
    for participantId in participants:
        broadcastMessage = f"DELETED;room has been deleted"
        participantConn = activeUsers[participantId]["conn"]
        participantConn.send(broadcastMessage.encode("utf-8"))
    
# thread untuk menghandle client
def handleClient(connectionSocket, clientAddress):
    loggedInUserData = None

    while True:
        try:
            # terima dulu, nanti messagenya mau ngirim berapa lengthnya
            upcomingMsgLength = connectionSocket.recv(4).decode("UTF-8")
            # terima messagenya
            upcomingMsgLength = int(upcomingMsgLength)

            if(upcomingMsgLength) : 
                msg = connectionSocket.recv(upcomingMsgLength).decode("UTF-8")
                msgParts = msg.split(";")

                if len(msgParts) == 0 :
                    raise Exception("invalid command format")

                command = msgParts[0]
                
                if command == "REGISTER" : 
                    if len(msgParts) != 3:
                        raise Exception("invalid register format")
                    
                    username = msgParts[1]
                    password = msgParts[2]

                    userId = userServices.register(username, password)

                    loggedInUserData = {"userId":userId, "username":username}

                    activeUsers[userId] = {
                        "username":username,
                        "conn" : connectionSocket,
                        "joinedRoomId" : None,
                    }

                    connectionSocket.send("REGISTER_SUCCESS;user is registered".encode("utf-8"))

                elif command == "LOGIN" : 
                    if len(msgParts) != 3:
                        raise Exception("invalid login format")
                    username = msgParts[1]
                    password = msgParts[2]

                    userData = userServices.login(username, password)
                    loggedInUserData = {"userId":userData["user_id"], "username":userData["username"]}

                    activeUsers[userData["user_id"]] = {
                        "username" : username,
                        "conn" : connectionSocket,
                        "joinedRoomId" : None,
                    }

                    connectionSocket.send("LOGIN_SUCCESS;user is logged in".encode("utf-8"))

                elif command == "CREATE_ROOM" : 
                    print("creating room")

                    if(loggedInUserData is None):
                        raise Exception("please login first")

                    if len(msgParts) != 2:
                        raise Exception("invalid create room format")
                    
                    roomName = msgParts[1]

                    insertedRoomData = roomServices.createRoom(roomName, loggedInUserData["userId"])

                    # masukkan room baru
                    rooms[insertedRoomData["roomId"]] = {
                        "roomName" : insertedRoomData["roomName"],
                        "ownerUserId" : insertedRoomData["ownerUserId"],
                        "participants" : {loggedInUserData["userId"]}
                    }


                    connectionSocket.send("SUCCESS;room is created".encode("utf-8"))
                elif command == "JOIN_ROOM" : 
                    if(len(msgParts) != 2):
                        raise Exception("invalid join room format")
                    
                    if(loggedInUserData is None):
                        raise Exception("please login first")
                    
                    roomId = int(msgParts[1])

                    userId = loggedInUserData["userId"]
                    joinedRoomId = activeUsers[userId]["joinedRoomId"]
                    if(joinedRoomId is not None):
                        raise Exception("you are already in another room")
                    
                    print(roomId)
                    room = rooms.get(roomId)
                    if (room is None):
                        raise Exception("room does not exist")
                    
                    room["participants"].add(loggedInUserData["userId"])

                    print("here", room["participants"])

                    # set penanda dia sekarang di room mana
                    activeUsers[userId]["joinedRoomId"] = roomId
                    
                    roomName = room["roomName"]
                    connectionSocket.send(f"JOINED;{roomName}".encode("utf-8"))

                    # broadcast klo ad yg join
                    joinRoomBroadcast(roomId, userId)

                elif command == "SEND_MESSAGE" : 
                    if(len(msgParts) != 2):
                        raise Exception("invalid join room format")
                    
                    if(loggedInUserData is None):
                        raise Exception("please login first")
                    
                    joinedRoomId = activeUsers[loggedInUserData["userId"]]["joinedRoomId"]
                    if(joinedRoomId is None):
                        raise Exception("you are not joined in any room")
                    
                    message = msgParts[1]

                    broadcastMessage(joinedRoomId, message, loggedInUserData["userId"])

                elif command == "GET_ROOMS":
                    roomsStr = "ROOMS_DATA;"

                    for roomId, roomData in rooms.items() : 
                        roomsStr += str(roomId)
                        roomsStr += "-"
                        roomsStr += roomData["roomName"]
                        roomsStr += ";"

                    roomsStr = roomsStr[:-1]

                    connectionSocket.send(roomsStr.encode("utf-8"))

                elif command == "GET_PARTICIPANTS":
                    if(len(msgParts) != 2):
                        raise Exception("invalid get participants format")
                    
                    if(loggedInUserData is None):
                        raise Exception("please login first")
                    
                    roomId = int(msgParts[1])

                    roomData = rooms[roomId]

                    if(roomData is None):
                        raise Exception("room does not exist")
                
                    participants = roomData["participants"]

                    respMessage = f"PARTICIPANTS-{roomId};"
                    for participantId in participants :
                        userData = activeUsers[participantId]
                        respMessage += str(participantId)
                        respMessage += "-"
                        respMessage += userData["username"]
                        respMessage += ";"

                    respMessage = respMessage[:-1]

                    connectionSocket.send(respMessage.encode("utf-8"))

                elif command == "LEAVE_ROOM":
                    if(loggedInUserData is None):
                        raise Exception("please login first")
                    
                    userId = loggedInUserData["userId"]
                    roomId = activeUsers[userId]["joinedRoomId"]
                    if (roomId is None):
                        raise Exception("you are not in any room")

                    rooms[roomId]["participants"].remove(userId)
                    activeUsers[userId]["joinedRoomId"] = None

                    leaveRoomBroadcast(roomId, userId)

                    connectionSocket.send("LEFT;you left the room".encode("utf-8"))

                elif command == "KICK" : 
                    if(loggedInUserData is None):
                        raise Exception("please login first")
                    
                    if(len(msgParts) != 3):
                        raise Exception("invalid kick format")
                    
                    kickUserId = int(msgParts[1])
                    roomId = int(msgParts[2])
                    
                    roomData = rooms[roomId]
                    if(roomData is None):
                        raise Exception("room does not exist")
                    
                    ownerUserId = roomData["ownerUserId"]

                    if(loggedInUserData["userId"] != ownerUserId):
                        raise Exception("you are not the owner of the room")
                    
                    participants = roomData["participants"]

                    if kickUserId not in participants:
                        raise Exception("user not in the room")
                    
                    rooms[roomId]["participants"].remove(kickUserId)
                    
                    activeUsers[kickUserId]["joinedRoomId"] = None
                    kickBroadcast(roomId, kickUserId)

                    kickedConnectionSocket = activeUsers[kickUserId]["conn"]
                    kickedConnectionSocket.send("KICKED;you have been kicked".encode("utf-8"))

                elif command == "DELETE_ROOM":
                    if(loggedInUserData is None):
                        raise Exception("please login first")
                    
                    if(len(msgParts) != 2):
                        raise Exception("invalid delete room format")
                    
                    roomId = int(msgParts[1])

                    roomData = rooms[roomId]
                    if(roomData is None):
                        raise Exception("room does not exist")
                    
                    ownerUserId = roomData["ownerUserId"]

                    if(loggedInUserData["userId"] != ownerUserId):
                        raise Exception("you are not the owner of the room")
                    
                    participants = roomData["participants"]

                    for participantId in participants : 
                        activeUsers[participantId]["joinedRoomId"] = None

                    deleteRoomBroadcast(roomId)
                    roomServices.deleteRoom(roomId)
                    del rooms[roomId]
                else : 
                    raise Exception("ERROR;command not found")

        except ConnectionResetError as e:
            print("user disconnected")
            break
        except Exception as e : 
            errMsg = "ERROR;" + str(e)
            connectionSocket.send(errMsg.encode("utf-8"))
    
# setting port
serverPort = 5000
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind(("",serverPort))
serverSocket.listen(1)
print(f"Server is listening on port {serverPort}")

cursor = conn.cursor()

while 1:
    connectionSocket, clientAddress = serverSocket.accept()
    client_thread = threading.Thread(target=handleClient, args=(connectionSocket, clientAddress))
    client_thread.start()