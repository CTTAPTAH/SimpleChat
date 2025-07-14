import socket
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
from PIL import Image, ImageTk
from collections import deque

message_queue = deque()
animating = False

def connect_to_server():
    global client_socket, username
    username = username_entry.get()
    password = password_entry.get()
    server_ip = ip_entry.get()
    port = int(port_entry.get())

    if not username or not password:
        messagebox.showwarning("Login Failed", "Enter username and password.")
        return

    try:
        client_socket = socket.socket()
        client_socket.connect((server_ip, port))
        client_socket.send(f"{username}:{password}".encode())

        response = client_socket.recv(1024).decode()
        if response == "AUTH_FAILED":
            messagebox.showerror("Login Failed", "Invalid credentials.")
            return
        elif response == "AUTH_OK":
            login_frame.pack_forget()
            chat_frame.pack(fill='both', expand=True)
            threading.Thread(target=receive_messages, daemon=True).start()
    except Exception as e:
        messagebox.showerror("Connection Error", str(e))

def receive_messages():
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            animate_message(data.decode())
        except:
            break

def send_message(event=None):
    msg = message_entry.get()
    if msg:
        client_socket.send(msg.encode())
        animate_message(f"{username}: {msg}")
        message_entry.delete(0, tk.END)

def animate_message(message):
    message_queue.append(message)
    process_next_message()

# синхронизация вывода
def process_next_message():
    global animating
    if animating or not message_queue:
        return
    animating = True
    msg = message_queue.popleft()

    chat_area.config(state='normal')

    def step(i=0):
        nonlocal msg
        if i < len(msg):
            chat_area.insert(tk.END, msg[i])
            chat_area.yview(tk.END)
            root.after(10, step, i+1)
        else:
            chat_area.insert(tk.END, "\n")
            chat_area.config(state='disabled')
            global animating
            animating = False
            process_next_message()  # обработать следующее сообщение

    step()

# выход обратно в главное меню
def logout():
    global client_socket
    try:
        client_socket.close()
    except:
        pass
    chat_frame.pack_forget()
    login_frame.pack(fill='both', expand=True)

# GUI Setup
root = tk.Tk()
root.title("Client Chat")
root.geometry("500x500")

# Login Frame
login_frame = tk.Frame(root)
login_frame.pack()

tk.Label(login_frame, text="Username:").pack()
username_entry = tk.Entry(login_frame)
username_entry.pack()

tk.Label(login_frame, text="Password:").pack()
password_entry = tk.Entry(login_frame, show="*")
password_entry.pack()

tk.Label(login_frame, text="Server IP:").pack()
ip_entry = tk.Entry(login_frame)
ip_entry.insert(0, "127.0.0.1")
ip_entry.pack()

tk.Label(login_frame, text="Port:").pack()
port_entry = tk.Entry(login_frame)
port_entry.insert(0, "12345")
port_entry.pack()

tk.Button(login_frame, text="Connect", command=connect_to_server).pack(pady=10)

# Chat Frame
chat_frame = tk.Frame(root)

bg_image = Image.open("wallpaper.jpg")
bg_photo = ImageTk.PhotoImage(bg_image.resize((500, 500)))
canvas = tk.Canvas(chat_frame, width=500, height=500)
canvas.pack(fill="both", expand=True)
canvas.create_image(0, 0, image=bg_photo, anchor="nw")

chat_area = scrolledtext.ScrolledText(chat_frame, state='disabled', width=50, height=20, font=("Segoe UI", 11))
chat_area.place(x=10, y=10)

message_entry = tk.Entry(chat_frame, width=50, font=("Segoe UI", 11))
message_entry.place(x=10, y=420)
message_entry.bind("<Return>", send_message)

send_button = tk.Button(chat_frame, text="Send", command=send_message, font=("Segoe UI", 10))
send_button.place(x=420, y=417)

logout_button = tk.Button(chat_frame, text="Logout", command=logout, font=("Segoe UI", 10))
logout_button.place(x=420, y=460)

root.mainloop()
