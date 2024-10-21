import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import socket
import threading
import json
from datetime import datetime
import hashlib
import urllib.request
import io
import os
import base64

COLORS = {
    'bg_dark': '#36393f',
    'bg_medium': '#2f3136',
    'bg_light': '#40444b',
    'text': '#dcddde',
    'highlight': '#7289da',
    'success': '#43b581',
    'error': '#f04747'
}

class CustomStyle:
    def __init__(self):
        style = ttk.Style()
        style.configure('Discord.TFrame', background=COLORS['bg_dark'])
        style.configure('Discord.TLabel', 
                        background=COLORS['bg_dark'],
                        foreground=COLORS['text'],
                        font=('Nunito Sans', 12))
        style.configure('Discord.TButton',
                        background='#5b6eae',
                        foreground='black',
                        borderwidth=1,
                        focusthickness=3,
                        focuscolor='none',
                        font=('Nunito Sans', 12))
        style.map('Discord.TButton', 
                  background=[('active', '#7289da')])
        style.configure('Discord.TEntry',
                        fieldbackground=COLORS['bg_light'],
                        foreground='black',
                        font=('Nunito Sans', 12))

class LoginWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("..?")
        self.root.configure(bg=COLORS['bg_dark'])
        self.root.geometry("300x320")
        CustomStyle()
        self.frame = ttk.Frame(self.root, style='Discord.TFrame')
        self.frame.pack(pady=20, padx=20, fill='both', expand=True)
        self.title_label = ttk.Label(self.frame, text="@",
                                      font=('Nunito Sans', 20, 'bold'),
                                      style='Discord.TLabel')
        self.title_label.pack(pady=20)
        self.username_label = ttk.Label(self.frame, text="Username:", style='Discord.TLabel')
        self.username_label.pack(pady=(20,5))
        self.username_entry = ttk.Entry(self.frame, style='Discord.TEntry')
        self.username_entry.pack(pady=(0,10), fill='x')
        self.password_label = ttk.Label(self.frame, text="Password:", style='Discord.TLabel')
        self.password_label.pack(pady=(10,5))
        self.password_entry = ttk.Entry(self.frame, show="●", style='Discord.TEntry')
        self.password_entry.pack(pady=(0,20), fill='x')
        self.login_button = ttk.Button(self.frame,
                                        text="click to login.",
                                        command=self.login,
                                        style='Discord.TButton')
        self.login_button.pack(pady=10, fill='x')
        self.login_attempts = 0
        self.max_attempts = 3
        self.username = None
        self.logged_in = False

    def login(self):
        if self.login_attempts >= self.max_attempts:
            messagebox.showerror("Error", "Too many failed attempts. Please try again later.")
            self.root.destroy()
            return
            
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        self.username = username
        self.logged_in = True
        self.root.destroy()

    def run(self):
        self.root.mainloop()
        return self.username if self.logged_in else None

class ChatClient:
    def __init__(self, root, username):
        self.root = root
        self.username = username
        self.root.title(f"incognito. - @{username}")
        self.root.geometry("800x600")
        self.root.configure(bg=COLORS['bg_dark'])
        CustomStyle()
        self.main_frame = ttk.Frame(self.root, style='Discord.TFrame')
        self.main_frame.pack(pady=10, padx=10, fill='both', expand=True)
        self.chat_frame = ttk.Frame(self.main_frame, style='Discord.TFrame')
        self.chat_frame.pack(fill='both', expand=True)
        self.chat_display = tk.Text(
            self.chat_frame,
            wrap=tk.WORD,
            state='disabled',
            height=20,
            bg=COLORS['bg_medium'],
            fg=COLORS['text'],
            insertbackground=COLORS['text'],
            selectbackground=COLORS['highlight'],
            font=('Nunito Sans', 10)
        )
        self.chat_display.pack(fill='both', expand=True)
        self.scrollbar = ttk.Scrollbar(self.chat_frame, command=self.chat_display.yview)
        self.scrollbar.pack(side='right', fill='y')
        self.chat_display['yscrollcommand'] = self.scrollbar.set
        self.input_frame = ttk.Frame(self.main_frame, style='Discord.TFrame')
        self.input_frame.pack(fill='x', pady=(10,0))
        self.upload_button = ttk.Button(
            self.input_frame,
            text="📎",
            command=self.upload_file,
            style='Discord.TButton',
            width=3
        )
        self.upload_button.pack(side='left', padx=(0,5))
        self.message_entry = ttk.Entry(self.input_frame, style='Discord.TEntry')
        self.message_entry.pack(side='left', fill='x', expand=True)
        self.send_button = ttk.Button(
            self.input_frame,
            text="Send",
            command=self.send_message,
            style='Discord.TButton'
        )
        self.send_button.pack(side='right', padx=(10,0))
        self.status_label = ttk.Label(self.main_frame, text="Status: Connecting...",
                                       style='Discord.TLabel')
        self.status_label.pack(pady=5)
        self.message_entry.bind('<Return>', lambda e: self.send_message())
        self.setup_network()
        
    def upload_file(self):
        file_path = filedialog.askopenfilename(
            title="Select a file",
            filetypes=[
                ("Text files", "*.txt"),
                ("Images", "*.png *.jpg *.jpeg *.gif"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'rb') as file:
                    file_data = file.read()
                file_data_b64 = base64.b64encode(file_data).decode('utf-8')
                filename = os.path.basename(file_path)
                self.client_socket.send(json.dumps({
                    'type': 'file',
                    'username': self.username,
                    'filename': filename,
                    'data': file_data_b64,
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                }).encode())
            except Exception as e:
                self.display_message({
                    'type': 'system',
                    'content': f"Error uploading file: {str(e)}"
                })

    def setup_network(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect(('localhost', 5555))
            self.status_label.config(text="Status: Connected")
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            self.client_socket.send(json.dumps({
                'type': 'connect',
                'username': self.username
            }).encode())
        except Exception as e:
            self.status_label.config(text=f"Status: Connection failed - {str(e)}")
            messagebox.showwarning("Connection Error", 
                "Could not connect to server. Running in offline mode.")

    def send_message(self):
        message = self.message_entry.get().strip()
        if message:
            try:
                self.client_socket.send(json.dumps({
                    'type': 'message',
                    'username': self.username,
                    'content': message,
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                }).encode())
                self.message_entry.delete(0, tk.END)
            except Exception as e:
                self.display_message({
                    'type': 'system',
                    'content': f"Error sending message: {str(e)}"
                })

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(4096).decode()
                if message:
                    data = json.loads(message)
                    self.display_message(data)
            except Exception as e:
                print(f"Error receiving message: {str(e)}")
                break

    def display_message(self, data):
        self.chat_display.configure(state='normal')
        timestamp = data.get('timestamp', datetime.now().strftime("%H:%M:%S"))
        
        if data['type'] == 'message':
            message = f"[{timestamp}] {data['username']}: {data['content']}\n"
        elif data['type'] == 'file':
            message = f"[{timestamp}] {data['username']} shared a file: {data['filename']}\n"
            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            file_path = os.path.join(downloads_dir, data['filename'])
            try:
                file_data = base64.b64decode(data['data'])
                with open(file_path, 'wb') as f:
                    f.write(file_data)
                message += f"File saved to: {file_path}\n"
            except Exception as e:
                message += f"Error saving file: {str(e)}\n"
        else:
            message = f"System: {data['content']}\n"
            
        self.chat_display.insert(tk.END, message)
        self.chat_display.configure(state='disabled')
        self.chat_display.see(tk.END)

class ChatServer:
    def __init__(self):
        print("Starting server...")
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server_socket.bind(('localhost', 5555))
            self.server_socket.listen(5)
            print("Server started on localhost:5555")
            self.clients = {}
            self.accept_connections()
        except Exception as e:
            print(f"Server error: {str(e)}")

    def accept_connections(self):
        while True:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"New connection from {address}")
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket,)
                )
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                print(f"Error accepting connection: {str(e)}")

    def handle_client(self, client_socket):
        try:
            data = json.loads(client_socket.recv(4096).decode())
            if data['type'] == 'connect':
                username = data['username']
                self.clients[client_socket] = username
                print(f"User {username} connected")
                self.broadcast({
                    'type': 'system',
                    'content': f"{username} joined the chat"
                })
            while True:
                message = client_socket.recv(4096).decode()
                if message:
                    self.broadcast(json.loads(message))
        except Exception as e:
            print(f"Client error: {str(e)}")
            if client_socket in self.clients:
                username = self.clients[client_socket]
                del self.clients[client_socket]
                self.broadcast({
                    'type': 'system',
                    'content': f"{username} left the chat"
                })
            client_socket.close()

    def broadcast(self, message):
        for client in self.clients:
            try:
                client.send(json.dumps(message).encode())
            except Exception as e:
                print(f"Broadcast error: {str(e)}")

def main():
    print("Starting chat application...")
    server_thread = threading.Thread(target=lambda: ChatServer())
    server_thread.daemon = True
    server_thread.start()
    print("Starting login window...")
    login_window = LoginWindow()
    username = login_window.run()
    if username:
        print(f"Login successful for user: {username}")
        root = tk.Tk()
        ChatClient(root, username)
        root.mainloop()
    else:
        print("Login failed or cancelled")

if __name__ == "__main__":
    main()
