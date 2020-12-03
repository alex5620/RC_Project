import socket
from threading import Thread
import tkinter as tk
from tkinter import ttk
import random

class ConnectionWindow:     # fereastra care interogheaza acceptarea/respingerea conexiunii
    def __init__(self, root):
        self.top = tk.Toplevel(root)
        self.is_connected = None
        self.top.geometry("230x100+{}+{}".format(root.winfo_x() + root.winfo_width() // 2 - 115,
                                             root.winfo_y() + root.winfo_height() // 2 - 50))
        self.top.title("Connection")
        self.top.resizable(False, False)
        label1 = tk.Label(self.top, image="::tk::icons::question")
        label1.place(x=8, y=8)
        label2 = tk.Label(self.top, text="Do you agree the connection?")
        label2.place(x=53, y=15)
        button1 = ttk.Button(self.top, text="Yes", command=self.establish_connection)
        button1.place(x=25, y=60)
        button2 = ttk.Button(self.top, text="No", command=self.refuse_connection)
        button2.place(x=125, y=60)

    def establish_connection(self):
        self.is_connected = True
        self.top.destroy()

    def refuse_connection(self):
        self.is_connected = False
        self.top.destroy()

    def get_is_connected(self):
        return self.is_connected

class Server():
    def __init__(self, ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((ip, port))
        self.sock.setblocking(0)
        self.state = 0
    def run(self):
        thread = Thread(target=self.listen)
        thread.start()

    def listen(self):
        data = None
        address = None
        while True:
            try:
                data, address = self.sock.recvfrom(128)
            except BlockingIOError:
                pass #empty buffer
            if self.state == 0:
                if data and (data[8]>>1)%2 == 1:   # s-au primit date, se verifica SYN
                    self.message_box.insert_message("A request from "+address[0]+" has been received.")
                    self.window = ConnectionWindow(self.root)  # SYN activ, se accepta conexiunea?
                    self.state = 1
            elif self.state == 1:
                if self.window.get_is_connected() == True:  # conexiunea a fost acceptata
                    self.message_box.insert_message("The connection with the client has been established.")
                    self.state = 2
                elif self.window.get_is_connected() == False:  # conexiunea a fost respinsa
                    self.message_box.insert_message("The connection with the client has been refused.")
                    self.state = 3                             # trimitere mesaj respingere conexiune si revenire la starea 0
            elif self.state == 2:   # conexiunea a fost acceptata
                message = bytearray(11)
                num = random.randint(0, 1000)
                message[2] = num // 256
                message[3] = num % 256
                message[8] = message[8] | int('00000010', 2)
                self.sock.sendto(message, (address[0], address[1]))
                data = None
                self.wf = open("received_file.pdf", "wb")
                self.state = 4
            elif self.state == 3:  # trimitere mesaj conexiune respinsa
                message = bytearray(11)  # bitul syn e pe 0
                self.sock.sendto(message, (address[0], address[1]))
                data = None
                self.state = 0
            elif self.state == 4:  # scriere in fisier date primite
                if data:
                    if data[8]%2 == 0: # se verifica daca s-a primit fin
                        self.wf.write(data[11:])
                    else:
                        self.message_box.insert_message("The file has been received.")
                        self.message_box.insert_message("The connection with "+str(address[0])+" is closed now.")
                        self.wf.close()
                        self.state = 0
                    data = None

    def set_message_box(self, message_box):
        self.message_box = message_box

    def set_root(self, root):
        self.root = root