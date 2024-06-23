# import library
import tkinter as tk
from tkinter import scrolledtext
import customtkinter as ctk
from customtkinter import *
import threading
import socket

# setting port dan host
PORT = 5000
HOST = "LOCALHOST"
ADDR = (HOST, PORT)

# connect client ke server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

isAuthenticated = False

# global var
lobby_window = None
chat_text_widget = None
message_entry = None

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# function untuk menerima message dari server
def recv_msg():
    global isAuthenticated, lobby_window, chat_text_widget

    while True:
        try:
            message = client.recv(2048).decode("utf-8")
            print("recv msg : ", message)
            if message:
                msgPart = message.split(";")
                if msgPart[0] == "LOGIN_SUCCESS" or msgPart[0] == "REGISTER_SUCCESS":
                    isAuthenticated = True
                elif msgPart[0] == "ROOMS_DATA":
                    if lobby_window:
                        display_rooms(msgPart[1:])
                elif msgPart[0] == "JOINED":
                    if lobby_window:
                        for widget in lobby_window.winfo_children():
                            widget.destroy()
                        ctk.CTkLabel(lobby_window, text="Welcome").pack(pady=10)
                        chat_text_widget = scrolledtext.ScrolledText(lobby_window, width=40, height=10, state=tk.DISABLED)
                        chat_text_widget.configure(bg="black", fg="white")
                        chat_text_widget.pack(pady=10)

                        chat_text_widget.tag_configure("left", justify="left")
                        chat_text_widget.tag_configure("right", justify="right")
                        chat_text_widget.tag_configure("center", justify="center")

                        global message_entry
                        frame = ctk.CTkFrame(lobby_window, fg_color=lobby_window.cget("fg_color"))
                        frame.pack()
                        message_entry = ctk.CTkEntry(frame)
                        message_entry.pack(side=LEFT, padx=10, fill="x")
                        send_button = ctk.CTkButton(frame, text="SEND", command=handleSendMessage)
                        send_button.pack(side=LEFT)

                        leave_button = ctk.CTkButton(frame, text="Leave Room", command=leave_room)
                        leave_button.pack(padx=10)
                elif msgPart[0] == "MESSAGE":
                    if chat_text_widget:
                        chat_text_widget.config(state=tk.NORMAL)
                        if msgPart[1].endswith("joined the room") or msgPart[1].endswith("left the room") or msgPart[1].endswith("has been kicked"):
                            chat_text_widget.insert(tk.END, msgPart[1] + "\n", "center")
                        elif msgPart[1].startswith("You"):
                            chat_text_widget.insert(tk.END, msgPart[1] + "\n", "right")
                        else:
                            chat_text_widget.insert(tk.END, msgPart[1] + "\n", "left")
                        chat_text_widget.config(state=tk.DISABLED)
                        chat_text_widget.yview(tk.END)  # untuk auto scroll
                elif msgPart[0].startswith("PARTICIPANTS"):
                    rid = msgPart[0].split("-")[1]
                    show_participants_popup(msgPart[1:], rid)
                elif msgPart[0] == "LEFT":
                    show_left_popup(msgPart[1])
                    lobby_window.destroy()
                    lobby_page()
                elif msgPart[0] == "KICKED":
                    show_kicked_popup("You have been kicked by the owner")
                    show_kick_popup()
                    lobby_window.destroy()
                    lobby_page()
                elif msgPart[0] == "DELETED":
                    show_kicked_popup("Room has been deleted by the owner")
                    show_delete_popup()
                    lobby_window.destroy()
                    lobby_page()
                elif msgPart[0] != "SUCCESS": 
                    error_page(message)
        except Exception as e:
            print(e)
            client.close()
            break

# function untuk menampilkan room yang ada
def display_rooms(rooms_data): 
    for widget in lobby_window.winfo_children():
        widget.destroy()

    ctk.CTkLabel(lobby_window, text="Available Rooms").pack(pady=10)
    
    for room in rooms_data:
        room_id, room_name = room.split('-', 1)
        room_frame = ctk.CTkFrame(lobby_window, fg_color=lobby_window.cget("fg_color"))
        room_frame.pack(pady=5)
        room_button = ctk.CTkButton(room_frame, text=f"{room_name} (ID: {room_id})",
                                command=lambda rid=room_id: join_handler(rid))
        room_button.pack(side=LEFT, padx=5, pady=5)

        participants_button = ctk.CTkButton(room_frame, text=f"Room details (ID: {room_id})",
                                        command=lambda rid=room_id: show_participants(rid))
        participants_button.pack(side=LEFT, padx=5, pady=5)

    create_room_button = ctk.CTkButton(lobby_window, text="Create Room", command=show_create_room_popup)
    create_room_button.pack(pady=10)

    refresh_button = ctk.CTkButton(lobby_window, text="Refresh", command=refresh_room_list)
    refresh_button.pack(pady=10)

# popup untuk membuat room
def show_create_room_popup(): 
    popup = ctk.CTkToplevel()
    popup.title("Create Room")

    window_width = 300
    window_height = 150

    screen_width = popup.winfo_screenwidth()
    screen_height = popup.winfo_screenheight()

    position_x = (screen_width // 2) - (window_width // 2)
    position_y = (screen_height // 2) - (window_height // 2)

    popup.geometry(f'{window_width}x{window_height}+{position_x}+{position_y}')

    ctk.CTkLabel(popup, text="Enter room name:").pack(pady=10)
    room_name_entry = ctk.CTkEntry(popup)
    room_name_entry.pack(padx=10, pady=5, fill="x")

    create_button = ctk.CTkButton(popup, text="Create", command=lambda: handleCreateRoom(popup, room_name_entry.get()))
    create_button.pack(pady=10)

# popup success sesudah berhasil kick
def show_kick_popup(): 
    popup = ctk.CTkToplevel()
    popup.title("kicked")

    window_width = 300
    window_height = 100

    screen_width = popup.winfo_screenwidth()
    screen_height = popup.winfo_screenheight()

    position_x = (screen_width // 2) - (window_width // 2)
    position_y = (screen_height // 2) - (window_height // 2)

    popup.geometry(f'{window_width}x{window_height}+{position_x}+{position_y}')

    ctk.CTkLabel(popup, text="Kicked successfully", text_color="light green").pack(pady=10)

    close_button = ctk.CTkButton(popup, text="Close", command=popup.destroy)
    close_button.pack(pady=10)

# popup success sesudah berhasil delete room
def show_delete_popup(): 
    popup = ctk.CTkToplevel()
    popup.title("room deleted")

    window_width = 300
    window_height = 100

    screen_width = popup.winfo_screenwidth()
    screen_height = popup.winfo_screenheight()

    position_x = (screen_width // 2) - (window_width // 2)
    position_y = (screen_height // 2) - (window_height // 2)

    popup.geometry(f'{window_width}x{window_height}+{position_x}+{position_y}')

    ctk.CTkLabel(popup, text="Deleted successfully", text_color="light green").pack(pady=10)

    close_button = ctk.CTkButton(popup, text="Close", command=popup.destroy)
    close_button.pack(pady=10)

# untuk menghandle create room dan send message ke server
def handleCreateRoom(popup, room_name): 
    if room_name:
        send_message(f"CREATE_ROOM;{room_name}")
        popup.destroy()

# merefresh room yang ada
def refresh_room_list(): 
    send_message("GET_ROOMS")

# meminta data semua participants pada satu room ke server
def show_participants(room_id): 
    send_message(f"GET_PARTICIPANTS;{room_id}")

# popup untuk menampilkan participants yang ada pada suatu room
def show_participants_popup(participants_data, rid): 
    popup = ctk.CTkToplevel()
    popup.title("Room Participants")

    window_width = 400
    window_height = 200

    screen_width = popup.winfo_screenwidth()
    screen_height = popup.winfo_screenheight()

    position_x = (screen_width // 2) - (window_width // 2)
    position_y = (screen_height // 2) - (window_height // 2)

    popup.geometry(f'{window_width}x{window_height}+{position_x}+{position_y}')

    ctk.CTkLabel(popup, text="Participants").pack(pady=10)
    
    for participant in participants_data:
        ctk.CTkLabel(popup, text=participant).pack(pady=5)
        kick_button = ctk.CTkButton(popup, text="Kick", command=lambda: handleKick(participant.split("-")[0], rid))
        kick_button.pack(pady=10)
        
    delete_button = ctk.CTkButton(popup, text="Delete room", command=lambda: handleDeleteRoom(rid))
    delete_button.pack(pady=10)
    close_button = ctk.CTkButton(popup, text="Close", command=popup.destroy)
    close_button.pack(pady=10)

# mengirim message kick ke server
def handleKick(userId, rid): 
    send_message(f"KICK;{userId};{rid}")

# mengirim message delete room ke server
def handleDeleteRoom(rid):
    send_message(f"DELETE_ROOM;{rid}")

# popup ketika sudah leave room
def show_left_popup(message): 
    popup = ctk.CTkToplevel()
    popup.title("Left Room")

    window_width = 300
    window_height = 100

    screen_width = popup.winfo_screenwidth()
    screen_height = popup.winfo_screenheight()

    position_x = (screen_width // 2) - (window_width // 2)
    position_y = (screen_height // 2) - (window_height // 2)

    popup.geometry(f'{window_width}x{window_height}+{position_x}+{position_y}')

    ctk.CTkLabel(popup, text=message, text_color="light green").pack(pady=10)

    close_button = ctk.CTkButton(popup, text="Close", command=popup.destroy)
    close_button.pack(pady=10)

# popup ketika user di kick
def show_kicked_popup(message): 
    popup = ctk.CTkToplevel()
    popup.title("kicked")

    window_width = 300
    window_height = 100

    screen_width = popup.winfo_screenwidth()
    screen_height = popup.winfo_screenheight()

    position_x = (screen_width // 2) - (window_width // 2)
    position_y = (screen_height // 2) - (window_height // 2)

    popup.geometry(f'{window_width}x{window_height}+{position_x}+{position_y}')

    ctk.CTkLabel(popup, text=message, text_color="red").pack(pady=10)

    close_button = ctk.CTkButton(popup, text="Close", command=popup.destroy)
    close_button.pack(pady=10)

# untuk mengirim message join room ke server
def join_handler(room_id): 
    send_message(f"JOIN_ROOM;{room_id}")

# untuk mengirim message leave room ke server
def leave_room(): 
    send_message("LEAVE_ROOM")

# untuk mengirim pesan chat ke server
def handleSendMessage(): 
    global message_entry
    message = message_entry.get()
    if message:
        send_message(f"SEND_MESSAGE;{message}")
        message_entry.delete(0, ctk.END)

# page untuk menghandle jika terjadi error
def error_page(msg): 
    error_window = ctk.CTk()
    error_window.title("Error Page")

    window_width = 300
    window_height = 100

    screen_width = error_window.winfo_screenwidth()
    screen_height = error_window.winfo_screenheight()

    position_x = (screen_width // 2) - (window_width // 2)
    position_y = (screen_height // 2) - (window_height // 2)

    error_window.geometry(f'{window_width}x{window_height}+{position_x}+{position_y}')

    error_label = ctk.CTkLabel(error_window, text=msg, text_color="red")
    error_label.pack(pady=10)

    close_button = ctk.CTkButton(error_window, text="Close", command=error_window.destroy)
    close_button.pack(pady=10)

    error_window.mainloop()

# protokol pengiriman message
# kirim lengthnya dulu -> kirim messagenya

# function untuk memformat panjang message
def format_number(num): 
    padded_str = f"{num: <4}"
    return padded_str 

# function untuk mengirim pesan chat ke server
def send_message(msg): 
    msg_length = len(msg)
    formatted_length = format_number(msg_length)

    print("sending msg")
    client.send(formatted_length.encode("utf-8"))
    client.send(msg.encode("utf-8"))
    print("here msg sent", msg)

# halaman lobby
def lobby_page(): 
    global lobby_window 
    lobby_window = ctk.CTk()
    lobby_window.title("Lobby Page")

    window_width = 600
    window_height = 400

    screen_width = lobby_window.winfo_screenwidth()
    screen_height = lobby_window.winfo_screenheight()

    position_x = (screen_width // 2) - (window_width // 2)
    position_y = (screen_height // 2) - (window_height // 2)

    lobby_window.geometry(f'{window_width}x{window_height}+{position_x}+{position_y}')

    send_message("GET_ROOMS")

    receive_thread = threading.Thread(target=recv_msg)
    receive_thread.start()

    lobby_window.mainloop()

# page untuk autentikasi (login / register)
def auth_page(): 
    global window
    window = ctk.CTk()
    window.title("Main Page")

    window_width = 400
    window_height = 300

    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    position_x = (screen_width // 2) - (window_width // 2)
    position_y = (screen_height // 2) - (window_height // 2)

    window.geometry(f'{window_width}x{window_height}+{position_x}+{position_y}')

    frame = ctk.CTkFrame(window, fg_color=window.cget("fg_color"))
    frame.pack(expand=True)  

    ctk.CTkLabel(frame, text="Multiple Chat Rooms").pack(pady=5)

    username_frame = ctk.CTkFrame(frame, fg_color=frame.cget("fg_color"))
    username_frame.pack(padx=5, pady=5, expand=True)
    username_label = ctk.CTkLabel(username_frame, text="Username:")
    username_label.pack(padx=5, pady=5, side=LEFT)
    username_entry = ctk.CTkEntry(username_frame)
    username_entry.pack(padx=5, pady=5, side=LEFT)

    password_frame = ctk.CTkFrame(frame, fg_color=frame.cget("fg_color"))
    password_frame.pack(padx=5, pady=5, expand=True)
    password_label = ctk.CTkLabel(password_frame, text="Password:")
    password_label.pack(padx=5, pady=5, side=LEFT)
    password_entry = ctk.CTkEntry(password_frame, show='*')
    password_entry.pack(padx=5, pady=5, side=LEFT)

    checkBox = ctk.BooleanVar()
    showPasswordCB = ctk.CTkCheckBox(frame, text="Show password", variable=checkBox, command=lambda: showPassword(checkBox, password_entry))
    showPasswordCB.pack(padx=10, pady=10)

    button_frame = ctk.CTkFrame(frame, fg_color=frame.cget("fg_color"))
    button_frame.pack(padx=5, pady=5, expand=True)
    login_button = ctk.CTkButton(button_frame, text="Login", command=lambda: register_login(window, "LOGIN", username_entry, password_entry))
    login_button.pack(padx=5, pady=5, side=LEFT)  
    register_button = ctk.CTkButton(button_frame, text="Register", command=lambda: register_login(window, "REGISTER", username_entry, password_entry))
    register_button.pack(padx=5, pady=5, side=LEFT)  

    window.mainloop()

# function untuk mengirim message untuk login / register
def register_login(window, msg, usernameEntry, passwordEntry): 
    username = usernameEntry.get()
    password = passwordEntry.get()
    if username and password:
        send_message(f"{msg};{username};{password}")
    else:
        send_message(f"{msg}")

    response = client.recv(2048).decode("utf-8")
    print("recv msg : ", response)
    if response:
        msgPart = response.split(";")
        if msgPart[0] == "LOGIN_SUCCESS" or msgPart[0] == "REGISTER_SUCCESS":               
            window.withdraw()
            lobby_page()
        else:
            error_page(response)

# function untuk show password
def showPassword(checkBox, password_entry):
        checked = checkBox.get()
        if checked:
            password_entry.configure(show="")
        else:
            password_entry.configure(show="*")


# Thread untuk GUI
auth_page_thread = threading.Thread(target=auth_page)
auth_page_thread.start()