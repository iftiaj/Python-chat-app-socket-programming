import socket
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import pickle
from datetime import datetime
import os
import threading
import struct
import customtkinter

customtkinter.set_appearance_mode("System")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass


class FirstScreen(tk.Tk):
    def __init__(self):
        super().__init__()

        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()

        self.x_co = int((screen_width / 2) - (550 / 2))
        self.y_co = int((screen_height / 2) - (400 / 2)) - 80
        self.geometry(f"550x400+{self.x_co}+{self.y_co}")
        self.title("Chat Room")
        self.resizable(False, False)

        self.user = None
        self.image_extension = None
        self.image_path = None

        self.attributes('-transparentcolor', 'blue')

        self.first_frame = tk.Frame(self, bg="blue")
        self.first_frame.pack(fill="both", expand=True)

        app_icon = Image.open('images/chat_ca.png')
        app_icon = ImageTk.PhotoImage(app_icon)

        self.iconphoto(False, app_icon)

        background = Image.open("images/login_bg_ca.jpg")
        background = background.resize((550, 400), Image.ANTIALIAS)
        background = ImageTk.PhotoImage(background)

        upload_image = Image.open('images/upload_ca.png')
        upload_image = upload_image.resize((25, 25), Image.ANTIALIAS)
        upload_image = ImageTk.PhotoImage(upload_image)

        # Default picture used if user did not choose an image
        self.user_image = 'images/user.png'

        tk.Label(self.first_frame, image=background).place(x=0, y=0)

        head = tk.Label(self.first_frame, text="Sign Up", font="lucida 17 bold", bg="grey")
        head.place(relwidth=1, y=24)

        self.profile_label = tk.Label(self.first_frame, bg="grey")
        self.profile_label.place(x=350, y=75, width=150, height=140)

        # upload_button = tk.Button(self.first_frame, image=upload_image, compound="left", text="Upload Image",
        #                           cursor="hand2", font="lucida 12 bold", padx=2, command=self.add_photo)
        # upload_button.place(x=345, y=220)

        upload_button = customtkinter.CTkButton(master=self.first_frame, image=upload_image, compound="left",
                                                text="Upload Image", padx=2, hover_color="grey", corner_radius=8,
                                                command=self.add_photo)
        upload_button.place(x=270, y=180)

        # self.username = tk.Label(self.first_frame, text="Username", font="lucida 12 bold", bg="grey")
        # self.username.place(x=80, y=150)

        # self.username_entry = tk.Entry(self.first_frame,  font="lucida 12 bold", width=10,
        #                                highlightcolor="blue", highlightthickness=1)
        # self.username_entry.place(x=195, y=150)
        #
        # self.username_entry.focus_set()

        self.username_entry = customtkinter.CTkEntry(master=self.first_frame, width=160,
                                                     placeholder_text="Enter username")
        self.username_entry.place(x=80, y=120)

        self.username_entry.focus_set()

        submit_button = customtkinter.CTkButton(master=self.first_frame, text="Connect", corner_radius=8,
                                                command=self.process_data)

        submit_button.place(x=80, y=180)

        self.mainloop()

    def add_photo(self):
        self.image_path = filedialog.askopenfilename()
        image_name = os.path.basename(self.image_path)
        self.image_extension = image_name[image_name.rfind('.')+1:]

        if self.image_path:
            user_image = Image.open(self.image_path)
            user_image = user_image.resize((150, 140), Image.ANTIALIAS)
            user_image.save('resized'+image_name)
            user_image.close()

            self.image_path = 'resized'+image_name
            user_image = Image.open(self.image_path)

            user_image = ImageTk.PhotoImage(user_image)
            self.profile_label.image = user_image
            self.profile_label.config(image=user_image)

    def process_data(self):
        if self.username_entry.get():
            self.profile_label.config(image="")

            # If username's character is >6, it will be replaced with a '.' in the end
            if len((self.username_entry.get()).strip()) > 6:
                self.user = self.username_entry.get()[:6]+"."
            else:
                self.user = self.username_entry.get()

            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                client_socket.connect(("192.168.1.14", 9998))
                status = client_socket.recv(1024).decode()
                if status == 'not_allowed':
                    client_socket.close()
                    messagebox.showinfo(title="Can't connect !", message='Sorry, server is completely occupied.'
                                                                         'Try again later')
                    return

            except ConnectionRefusedError:
                messagebox.showinfo(title="Can't connect !", message="Server is offline , try again later.")
                print("Server is offline , try again later.")
                return

            client_socket.send(self.user.encode('utf-8'))

            if not self.image_path:
                self.image_path = self.user_image
            with open(self.image_path, 'rb') as image_data:
                image_bytes = image_data.read()

            image_len = len(image_bytes)
            image_len_bytes = struct.pack('i', image_len)
            client_socket.send(image_len_bytes)

            if client_socket.recv(1024).decode() == 'received':
                client_socket.send(str(self.image_extension).strip().encode())

            client_socket.send(image_bytes)

            clients_data_size_bytes = client_socket.recv(1024)
            clients_data_size_int = struct.unpack('i', clients_data_size_bytes)[0]
            b = b''
            while True:
                clients_data_bytes = client_socket.recv(1024)
                b += clients_data_bytes
                if len(b) == clients_data_size_int:
                    break

            clients_connected = pickle.loads(b)

            client_socket.send('image_received'.encode())

            user_id = struct.unpack('i', client_socket.recv(1024))[0]
            print(f"{self.user} is the {user_id} user")
            ChatScreen(self, self.first_frame, client_socket, clients_connected, user_id)


class ChatScreen(tk.Canvas):
    WIDTH = 1000
    HEIGHT = 850

    def __init__(self, parent, first_frame, client_socket, clients_connected, user_id):
        super().__init__(parent, bg="#2b2b2b")

        self.window = 'ChatScreen'

        self.first_frame = first_frame
        self.first_frame.pack_forget()

        self.parent = parent
        self.parent.bind('<Return>', lambda e: self.sent_message_format(e))

        self.all_user_image = {}

        self.user_id = user_id

        self.clients_connected = clients_connected

        # Run on_closing function when user close the window
        self.parent.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.client_socket = client_socket

        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()

        x_co = int((screen_width / 2) - (1000 / 2))
        y_co = int((screen_height / 2) - (850 / 2)) - 80
        self.parent.geometry(f"1000x850+{x_co}+{y_co}")
        self.parent.resizable(False, False)

        user_image = Image.open(self.parent.image_path)
        user_image = user_image.resize((40, 40), Image.ANTIALIAS)
        self.user_image = ImageTk.PhotoImage(user_image)

        # global background
        # background = Image.open("images/chat_bg_ca.jpg")
        # background = background.resize((1600, 1500), Image.ANTIALIAS)
        # background = ImageTk.PhotoImage(background)

        global group_photo
        group_photo = Image.open('images/group_ca.png')
        group_photo = group_photo.resize((60, 60), Image.ANTIALIAS)
        group_photo = ImageTk.PhotoImage(group_photo)

        self.y = 140
        self.clients_online_labels = {}

        # Show online users on the right side
        self.create_text(800, 120, text="Online", font="lucida 12 bold", fill="#40C961")
        # Settings for the title of the group chat
        tk.Label(self, text="   ", font="lucida 15 bold", bg="#b5b3b3").place(x=4, y=29)

        tk.Label(self, text="Group Chat", font="lucida 15 bold", padx=20, fg="green",
                 bg="#b5b3b3", anchor="w", justify="left").place(x=88, y=29, relwidth=1)

        self.create_image(60, 40, image=group_photo)

        container = tk.Frame(self)
        # settings for the chat box
        container.place(x=40, y=120, width=600, height=580)
        self.canvas = tk.Canvas(container, bg="#595656")
        self.scrollable_frame = tk.Frame(self.canvas, bg="#595656")

        scrollable_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        def configure_scroll_region(e):
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))

        def resize_frame(e):
            self.canvas.itemconfig(scrollable_window, width=e.width)

        self.scrollable_frame.bind("<Configure>", configure_scroll_region)

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.yview_moveto(1.0)

        scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", resize_frame)
        self.canvas.pack(fill="both", expand=True)

        # Settings for the "Send" button
        send_button = tk.Button(self, text="Send", fg="#83eaf7", font="lucida 11 bold", bg="#7d7d7d", padx=10,
                                relief="solid", bd=2, command=self.sent_message_format)
        send_button.place(x=565, y=715)

        self.entry = tk.Text(self, font="lucida 10 bold", width=57, height=2,
                             highlightcolor="blue", highlightthickness=1)
        self.entry.place(x=40, y=710)

        self.entry.focus_set()

        m_frame = tk.Frame(self.scrollable_frame, bg="#ffc6bf")

        t_label = tk.Label(m_frame, bg="#d9d5d4", text=datetime.now().strftime('%H:%M'), font="lucida 9 bold")
        t_label.pack()

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

        self.pack(fill="both", expand=True)

        self.clients_online([])

        t = threading.Thread(target=self.receive_data)
        t.start()

    def receive_data(self):
        while True:
            try:
                data_type = self.client_socket.recv(1024).decode()

                if data_type == 'notification':
                    data_size = self.client_socket.recv(2048)
                    data_size_int = struct.unpack('i', data_size)[0]

                    b = b''
                    while True:
                        data_bytes = self.client_socket.recv(1024)
                        b += data_bytes
                        if len(b) == data_size_int:
                            break
                    data = pickle.loads(b)
                    self.notification_format(data)

                else:
                    data_bytes = self.client_socket.recv(1024)
                    data = pickle.loads(data_bytes)
                    self.received_message_format(data)

            except ConnectionAbortedError:
                print("you disconnected ...")
                self.client_socket.close()
                break
            except ConnectionResetError:
                messagebox.showinfo(title='No Connection !', message="Server offline..try connecting again later")
                self.client_socket.close()
                self.first_screen()
                break

    def on_closing(self):
        if self.window == 'ChatScreen':
            res = messagebox.askyesno(title='Warning !', message="Do you really want to disconnect ?")
            if res:
                import os
                os.remove(self.all_user_image[self.user_id])
                self.client_socket.close()
                self.first_screen()
        else:
            self.parent.destroy()

    def received_message_format(self, data):

        message = data['message']
        from_ = data['from']
        username = self.clients_connected[self.user_id][1]

        sender_image = self.clients_connected[from_][1]
        sender_image_extension = self.clients_connected[from_][2]

        with open(f"{from_}.{sender_image_extension}", 'wb') as f:
            f.write(sender_image)

        im = Image.open(f"{from_}.{sender_image_extension}")
        im = im.resize((40, 40), Image.ANTIALIAS)
        im = ImageTk.PhotoImage(im)

        m_frame = tk.Frame(self.scrollable_frame, bg="#595656")

        m_frame.columnconfigure(1, weight=1)

        t_label = tk.Label(m_frame, bg="#595656", fg="white", text=datetime.now().strftime('%H:%M'),
                           font="lucida 7 bold",
                           justify="left", anchor="w")
        t_label.grid(row=2, column=1, padx=2, sticky="w")

        n_label = tk.Label(m_frame, bg="#595656", fg="white", text="Him",
                           font="lucida 7 bold",
                           justify="right", anchor="w")
        n_label.grid(row=0, column=1, padx=2, sticky="w")

        m_label = tk.Label(m_frame, wraplength=250, fg="black", bg="#c5c7c9", text=message, font="lucida 9 bold",
                           justify="left",
                           anchor="w")
        m_label.grid(row=1, column=1, padx=2, pady=2, sticky="w")

        i_label = tk.Label(m_frame, bg="#595656", image=im)
        i_label.image = im
        i_label.grid(row=0, column=0, rowspan=2)

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def sent_message_format(self, event=None):

        message = self.entry.get('1.0', 'end-1c')
        username = self.clients_connected[self.user_id][0]

        if message:
            if event:
                message = message.strip()
            self.entry.delete("1.0", "end-1c")

            from_ = self.user_id

            data = {'from': from_, 'message': message}
            data_bytes = pickle.dumps(data)

            self.client_socket.send(data_bytes)

            m_frame = tk.Frame(self.scrollable_frame, bg="#595656")

            m_frame.columnconfigure(0, weight=1)

            t_label = tk.Label(m_frame, bg="#595656", fg="white", text="Sent " + datetime.now().strftime('%H:%M'),
                               font="lucida 7 bold", justify="right", anchor="e")
            t_label.grid(row=2, column=0, padx=2, sticky="e")

            n_label = tk.Label(m_frame, bg="#595656", fg="white", text="You",
                               font="lucida 7 bold",
                               justify="right", anchor="w")
            n_label.grid(row=0, column=0, padx=1, sticky="e")

            m_label = tk.Label(m_frame, wraplength=250, text=message, fg="black", bg="#40C961",
                               font="lucida 9 bold", justify="left",
                               anchor="e")
            m_label.grid(row=1, column=0, padx=2, pady=2, sticky="e")

            i_label = tk.Label(m_frame, bg="#595656", image=self.user_image)
            i_label.image = self.user_image
            i_label.grid(row=0, column=1, rowspan=2, sticky="e")

            m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

            self.canvas.update_idletasks()
            self.canvas.yview_moveto(1.0)

    def notification_format(self, data):
        global message
        if data['n_type'] == 'joined':

            name = data['name']
            image = data['image_bytes']
            extension = data['extension']
            message = data['message']
            client_id = data['id']
            self.clients_connected[client_id] = (name, image, extension)
            self.clients_online([client_id, name, image, extension])
            # print(self.clients_connected)

        elif data['n_type'] == 'left':
            client_id = data['id']
            message = data['message']
            self.remove_labels(client_id)
            del self.clients_connected[client_id]

        m_frame = tk.Frame(self.scrollable_frame, bg="#595656")

        t_label = tk.Label(m_frame, fg="white", bg="#595656", text=datetime.now().strftime('%H:%M'),
                           font="lucida 9 bold")
        t_label.pack()

        m_label = tk.Label(m_frame, wraplength=250, text=message, font="lucida 10 bold", justify="left", bg="sky blue")
        m_label.pack()

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

        self.canvas.yview_moveto(1.0)

    # Settings for the online client list on the right
    def clients_online(self, new_added):
        if not new_added:
            pass
            for user_id in self.clients_connected:
                name = self.clients_connected[user_id][0]
                image_bytes = self.clients_connected[user_id][1]
                extension = self.clients_connected[user_id][2]

                with open(f"{user_id}.{extension}", 'wb') as f:
                    f.write(image_bytes)

                self.all_user_image[user_id] = f"{user_id}.{extension}"

                user = Image.open(f"{user_id}.{extension}")
                user = user.resize((45, 45), Image.ANTIALIAS)
                user = ImageTk.PhotoImage(user)

                b = tk.Label(self, image=user, text=name, compound="left",fg="white", bg="#2b2b2b",
                             font="lucida 10 bold", padx=15)
                b.image = user
                b.place(x=700, y=self.y)
                self.clients_online_labels[user_id] = (b, self.y)

                self.y += 60

        else:
            user_id = new_added[0]
            name = new_added[1]
            image_bytes = new_added[2]
            extension = new_added[3]

            with open(f"{user_id}.{extension}", 'wb') as f:
                f.write(image_bytes)

            self.all_user_image[user_id] = f"{user_id}.{extension}"

            user = Image.open(f"{user_id}.{extension}")
            user = user.resize((45, 45), Image.ANTIALIAS)
            user = ImageTk.PhotoImage(user)

            b = tk.Label(self, image=user, text=name, compound="left", fg="white", bg="#2b2b2b",
                         font="lucida 10 bold", padx=15)
            b.image = user
            b.place(x=700, y=self.y)
            self.y += 60
            self.clients_online_labels[user_id] = (b, self.y)


    def remove_labels(self, client_id):
        for user_id in self.clients_online_labels.copy():
            b = self.clients_online_labels[user_id][0]
            y_co = self.clients_online_labels[user_id][1]
            if user_id == client_id:
                print("yes")
                b.destroy()
                del self.clients_online_labels[client_id]
                import os
                # os.remove(self.all_user_image[user_id])

            elif user_id > client_id:
                y_co -= 60
                b.place(x=510, y=y_co)
                self.clients_online_labels[user_id] = (b, y_co)
                self.y -= 60

    def insert_emoji(self, x):
        self.entry.insert("end-1c", x.widget['text'])

    def first_screen(self):
        self.destroy()
        self.parent.geometry(f"550x400+{self.parent.x_co}+{self.parent.y_co}")
        self.parent.first_frame.pack(fill="both", expand=True)
        self.window = None


FirstScreen()