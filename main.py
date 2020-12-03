import socket
from contextlib import closing
from tkinter import *  # more configurable library
from tkinter import ttk  # more styled library
from tkinter import scrolledtext
from tkinter import messagebox as mb
from server import Server
from client import Client
from client import get_file_name
from client import send_file


def create_server(message_box, root, percentage):
    cond = True
    try:
        value = int(percentage.get())
        if value > 40 or value < 0:
            cond = False
    except ValueError:
        cond = False
    if cond == False:
        mb.showinfo(title="Error", message="The percentage value must be between 0-40.")
    hostname = socket.gethostname()
    IP = socket.gethostbyname(hostname)
    port = find_free_port()
    my_server = Server(IP, port)
    my_server.set_message_box(message_box)
    my_server.set_root(root)
    message_box.insert_message("The server has been created.")
    message_box.insert_message("Local ip: " + IP + ", port: " + str(port) + ".")
    my_server.run()


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def create_client_server_connexion(message_box, ip_entry, port_entry):
    ip = ip_entry.get()
    if (len(ip) == 0):
        mb.showinfo(title="Error", message="The IP was not inserted.")
        return
    port = port_entry.get()
    if (len(port) == 0):
        mb.showinfo(title="Error", message="The PORT was not inserted.")
        return
    my_client = Client(ip, int(port))
    my_client.set_message_box(message_box)
    my_client.run()


class MessageBox():
    def __init__(self, master, w, h):
        self.message_box = scrolledtext.ScrolledText(master=master, state=DISABLED, width=w, height=h)

    def place(self, x, y):
        self.message_box.place(x=x, y=y)

    def insert_message(self, message):
        self.message_box['state'] = 'normal'
        self.message_box.insert('end', " " + message + "\n")
        self.message_box['state'] = 'disabled'
        self.message_box.see("end")


class GUI:
    def __init__(self, master):
        self.master = master
        self.master.resizable(False, False)
        self.master.title("RCP")
        self.app_width = 550
        self.app_height = 450
        self.init_window_size()
        self.init_menu()
        self.init_sender()
        self.init_receiver()
        self.raise_frame(self.receiver_frame)

    def init_window_size(self):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = (screen_width / 2) - (self.app_width / 2)
        y = (screen_height / 2) - (self.app_height / 2)
        self.master.geometry('%dx%d+%d+%d' % (self.app_width, self.app_height, x, y))

    def init_menu(self):
        main_menu = Menu(self.master)  # bara de meniu
        mode_menu = Menu(main_menu, tearoff=False)
        mode_menu.add_command(label="Sender",  # meniul mode ce va contine submeniurile sender si receiver
                              command=lambda: self.raise_frame(self.sender_frame))
        mode_menu.add_command(label="Receiver",
                              command=lambda: self.raise_frame(self.self.receiver_frame))
        main_menu.add_cascade(label="Mode", menu=mode_menu)  # meniul mode al barei de meniu
        self.master.config(menu=main_menu)  # adaugam bara de meniu

    def init_sender(self):
        self.sender_frame = Frame(self.master)  # permite organizarea widget-urilor
        self.sender_frame.config(width=self.app_width, height=self.app_height)
        self.sender_frame.place(x=0, y=0)
        self.sender_msg_window = MessageBox(self.sender_frame, 60, 10)
        self.sender_msg_window.place(30, 280)
        self.init_sender_buttons()
        self.init_sender_labels()
        self.init_sender_entries()

    def init_sender_buttons(self):
        connect_button = ttk.Button(master=self.sender_frame, text="Connect",
                                    command=lambda: create_client_server_connexion(self.sender_msg_window,
                                                                                   self.s_ip_entry, self.s_port_entry))
        connect_button.place(x=244, y=140)
        choose_file_button = ttk.Button(master=self.sender_frame, text="Choose file",
                                        command=lambda: get_file_name(self.sender_msg_window))
        choose_file_button.place(x=200, y=195)
        transmit_button = ttk.Button(master=self.sender_frame, text="Transmit file",
                                     command=lambda: send_file(self.sender_msg_window))
        transmit_button.place(x=285, y=195)

    def init_sender_labels(self):
        title = Label(master=self.sender_frame, text="Sender's view")
        title.configure(font=("Times New Roman", 18, "bold"))
        title.place(x=210, y=15)
        ip_label = Label(master=self.sender_frame, text="IP:")
        ip_label.place(x=200, y=70)
        port_label = Label(master=self.sender_frame, text="PORT:")
        port_label.place(x=180, y=100)
        message_box_title = Label(master=self.sender_frame, text="Message box")
        message_box_title.place(x=245, y=255)

    def init_sender_entries(self):
        self.s_ip_entry = Entry(master=self.sender_frame)
        self.s_ip_entry.place(x=221, y=72)
        self.s_port_entry = Entry(master=self.sender_frame)
        self.s_port_entry.place(x=221, y=102)

    def init_receiver(self):
        self.receiver_frame = Frame(self.master)
        self.receiver_frame.config(width=self.app_width, height=self.app_height)
        self.receiver_frame.place(x=0, y=0)
        self.init_receiver_buttons()
        self.init_receiver_labels()
        self.init_receiver_entries()
        self.receiver_msg_window = MessageBox(self.receiver_frame, 60, 10)
        self.receiver_msg_window.place(30, 280)

    def init_receiver_buttons(self):
        receiver_connect_button = ttk.Button(master=self.receiver_frame, text="Create server",
                                             command=lambda: create_server(self.receiver_msg_window, self.master,
                                                                           self.r_ip_entry))
        receiver_connect_button.place(x=244, y=140)

    def init_receiver_labels(self):
        title = Label(master=self.receiver_frame, text="Receiver's view")
        title.configure(font=("Times New Roman", 18, "bold"))
        title.place(x=200, y=15)
        ip_label = Label(master=self.receiver_frame, text="Lost packets(%):")
        ip_label.place(x=140, y=80)
        message_box_title = Label(master=self.receiver_frame, text="Message box")
        message_box_title.place(x=245, y=255)

    def init_receiver_entries(self):
        self.r_ip_entry = Entry(master=self.receiver_frame, width=15)
        self.r_ip_entry.insert(0, "0")
        self.r_ip_entry.place(x=235, y=82)

    def raise_frame(self, frame):  # comuta intre frame-ul sender-ului si cel al receiver-ului
        frame.tkraise()


if __name__ == "__main__":
    root = Tk()
    my_gui = GUI(root)
    root.mainloop()





