import socket
import threading
import tkinter as tk
from tkinter import messagebox

clients = []
user_db = {}

def load_users():
    with open("users.txt", "r") as file:
        for line in file:
            username, password = line.strip().split(":")
            user_db[username] = password

def broadcast(message, sender_conn):
    for client in clients:
        conn, _ = client
        if conn != sender_conn:
            try:
                conn.send(message)
            except:
                clients.remove(client)
                conn.close()

def handle_client(conn, addr):
    username = None
    try:
        log_area.insert(tk.END, f"[NEW CONNECTION] {addr}\n")

        creds = conn.recv(1024).decode()
        username, password = creds.split(":")

        log_area.insert(tk.END, f"[LOGIN ATTEMPT] {username} from {addr}\n")

        if username not in user_db or user_db[username] != password:
            conn.send("AUTH_FAILED".encode())
            log_area.insert(tk.END, f"[AUTH FAILED] {username} from {addr}\n")
            return  # Не добавляем в clients

        conn.send("AUTH_OK".encode())
        log_area.insert(tk.END, f"[AUTH OK] {username} connected.\n")
        clients.append((conn, username))
        broadcast(f"{username} joined the chat.".encode(), conn)

        while True:
            msg = conn.recv(1024)
            if not msg:
                break
            log_area.insert(tk.END, f"[MESSAGE] {username}: {msg.decode()}\n")
            broadcast(f"{username}: {msg.decode()}".encode(), conn)

    except Exception as e:
        if isinstance(e, ConnectionResetError) and e.errno == 10054:
            pass  # просто не выводим в лог. Скорее всего закрыли окно или вернулись в главное меню
        else:
            print(f"[ERROR] Connection with {addr} caused error: {e}")
            log_area.insert(tk.END, f"[ERROR] Connection with {addr}: {e}\n")

    finally:
        # Удаляем только если клиент был добавлен
        if (conn, username) in clients:
            clients.remove((conn, username))
            broadcast(f"{username} left the chat.".encode(), conn)
            log_area.insert(tk.END, f"[DISCONNECTED] {username} disconnected.\n")
        conn.close()


def start_server():
    try:
        ip = ip_entry.get()
        port = int(port_entry.get())
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((ip, port))
        server.listen()

        log_area.insert(tk.END, f"[STARTED] Server running at {ip}:{port}\n")

        def accept_clients():
            while True:
                conn, addr = server.accept()
                threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

        threading.Thread(target=accept_clients, daemon=True).start()

    except Exception as e:
        messagebox.showerror("Error", str(e))

load_users()

root = tk.Tk()
root.title("Server Control Panel")
root.geometry("400x300")

tk.Label(root, text="Server IP:").pack()
ip_entry = tk.Entry(root)
ip_entry.insert(0, "127.0.0.1")
ip_entry.pack()

tk.Label(root, text="Port:").pack()
port_entry = tk.Entry(root)
port_entry.insert(0, "12345")
port_entry.pack()

tk.Button(root, text="Start Server", command=start_server).pack(pady=10)

log_area = tk.Text(root, height=10, state='normal')
log_area.pack(fill='both', expand=True)

root.mainloop()
