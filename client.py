import socket
from threading import Thread
import random
from tkinter.filedialog import askopenfilename

file_path =""
send_file_var = False

def get_file_name(message_box):
    global file_path
    file_path = askopenfilename()  # show an "Open" dialog box and return the path to the selected file
    if(len(file_path)!=0):
        list = file_path.split("/")
        message_box.insert_message("The "+list[len(list)-1]+" file was selected.")

def send_file(message_box):
    global send_file_var
    send_file_var = True
    message_box.insert_message("The transmission has started.")

class Client():
    def __init__(self, ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ip = ip
        self.port = port
        self.state = 0
    def send(self):
        while True:
            if self.state == 0:    # se trimite SYN si un SEQ NUM random
                message = bytearray(11)
                num = random.randint(0, 1000)  # se alege un SEQ NUM aleatoriu
                message[2] = num//256
                message[3] = num%256
                message[8] = message[8] | int('00000010', 2)   # se activeaza SYN
                self.sock.sendto(message, (self.ip, self.port))
                self.message_box.insert_message("The connection request has been sent.")
                self.state = 1
            elif self.state == 1:  # se asteapta acceptarea/respingerea conexiunii(clientul trebuie sa primeasca un mesaj cu bitul SYN activat)
                data, address = self.sock.recvfrom(1024)
                if (data[8] >> 1) % 2 == 1:  #conexiune acceptata(SYN e activ)
                    self.state = 2
                    self.message_box.insert_message("The connection with the server has been accepted.")
                else:   #conexiune respinsa(SYN nu e activ)
                    self.message_box.insert_message("The connection with the server has been refused.")
                    break   # conexiune respinsa
            elif self.state == 2:  # conexiune acceptata, se asteapta alegerea fisierului si apasarea butonului de transmisie a acestuia
                if send_file_var:
                    self.rf = open(file_path, "rb")
                    self.state = 3
            elif self.state == 3:  # fisierul a fost ales, iar butonul de transmitere a fost apasat
                read_bool = True
                length = 0
                while read_bool:
                    message = bytes(11)+self.rf.read(64)
                    if (len(message) == 11):  # s-au citit toti octetii din fisier, deci acesta a fost transmis cu succes
                        message = bytearray(11)
                        message[8] = message[8] | int('00000001', 2)  # se activeaza FIN
                        self.sock.sendto(message, (self.ip, self.port))
                        read_bool = False
                        self.state = 4
                    else:
                        self.sock.sendto(message, (self.ip, self.port))  # se transmit pachete
                        length += len(message)
                        print(length)
            elif self.state == 4:  #fisierul a fost transmis, inchidem conexiunile
                self.message_box.insert_message("File transmitted, the connection is closed now.")
                self.sock.close()
                self.rf.close()
                break

    def run(self):
        thread = Thread(target = self.send)
        thread.start()

    def set_message_box(self, message_box):
        self.message_box = message_box