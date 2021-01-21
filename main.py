from tkinter import Tk, Frame, Menu, Radiobutton, Entry, Label, Scale, DISABLED, HORIZONTAL, END, IntVar
from tkinter import ttk, scrolledtext, messagebox as mb
from tkinter.filedialog import askopenfilename
from server import Server
from client import Client, get_path, set_path
from contextlib import closing
import socket

""" Functia de creare a serverului(receiver-ului):
        - se determina ip-ul pentru socket-ul serverului
        - se genereaza un port disponibil pe care serverul va primi pachetele
        - creare server """
def create_server(widgets):
    IP = get_ip_address()
    port = find_free_port()
    my_server = Server(IP, port, widgets)
    widgets.receiver_msg_box.reset_message_box()
    widgets.receiver_msg_box.insert_message("The server has been created.")
    widgets.receiver_msg_box.insert_message("Local ip: " + IP + ", port: " + str(port) + ".")
    my_server.run()

""" Functia se conecteaza la Google Public DNS obtinand astfel ip-ul
    adaptorului de retea cu care suntem conectati la internet. """
def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

""" 'Bind-ul' la portul 0 va cere OS-ului sa genereze un port disponibil care este ulterior
    configurat in asa fel incat sa poata fi refolosit. """
def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('localhost', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

""" Functia de creare a clientului(sender-ului):
    - se verifica introducerea ip-ului, portului si se asigura faptul ca fisierul a fost selectat
    - creare client """
def create_client(widgets):
    ip = widgets.s_ip_entry.get()
    if len(ip) == 0:
        mb.showinfo(title="Error", message="The IP was not inserted.")
        return
    port = widgets.s_port_entry.get()
    if len(port) == 0:
        mb.showinfo(title="Error", message="The PORT was not inserted.")
        return
    if len(get_path()) == 0:
        mb.showinfo(title="Error", message="The file has not been selected.")
        return
    my_client = Client(ip, int(port), widgets)
    widgets.sender_msg_box.insert_message("The transmission has started.")
    my_client.run()

# Functia creeaza o fereastra ce permite alegerea fisierului ce urmeaza a fi transmis.
def get_file_name(widgets):
    file_path = askopenfilename()
    if(len(file_path)!=0):
        list = file_path.split("/")
        widgets.sender_msg_box.reset_message_box()
        widgets.sender_msg_box.insert_message("The "+list[len(list)-1]+" file was selected.")
        set_path(file_path)

""" Clasa reprezinta un 'message box' ce va permite notificarea utilizatorului cu diferite mesaje.
    Starea initiala a message box-ului va fi 'disabled' pentru a nu-i permite utilizatorului sa
    introduca mesaje in mod direct. """
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

    def reset_message_box(self):
        self.message_box['state'] = 'normal'
        self.message_box.delete('1.0', END)
        self.message_box['state'] = 'disabled'

""" Clasa Widgets ofera clientului/serverului posibilitatea de a avea acces la unele widget-uri de pe interfata grafica
    pentru a putea realiza anumite configurari(preluarea valorii dimensiunii unui pachet din meniul de setari, a ip-ului 
    introdus pe view-ul sender-ului, modificarea textului label-ului ce indica dimensiunea ferestrei). """
class Widgets():
    def __init__(self):
        self.cwnd_value = IntVar()
        self.sstresh_value = IntVar()
        self.pack_size = IntVar()
        self.lost_percentage = IntVar()
        self.sender_msg_box = None
        self.receiver_msg_box = None
        self.s_ip_entry = None
        self.s_port_entry = None
        self.download_percentage = None
        self.cwnd_size_label = None
        self.sstresh_size_label = None
        self.connection_is_active = False

# Interfata grafica a aplicatiei.
class GUI:
    def __init__(self, master):
        self.master = master
        self.master.resizable(False, False)
        self.master.title("RCP")
        self.app_width = 550
        self.app_height = 450
        self.widgets = Widgets()
        self.init_window_size()
        self.init_menu()
        self.init_sender()
        self.init_receiver()
        self.init_settings()
        self.raise_frame(self.receiver_frame)

    # Sunt setate dimensiunile ferestrei, aceasta fiind de asemenea centrata in mijlocul ecranului.
    def init_window_size(self):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = (screen_width / 2) - (self.app_width / 2)
        y = (screen_height / 2) - (self.app_height / 2)
        self.master.geometry('%dx%d+%d+%d' % (self.app_width, self.app_height, x, y))

    # Este creata bara de meniu si sunt adaugate submeniurile corespunzatoare.
    def init_menu(self):
        main_menu = Menu(self.master)
        mode_menu = Menu(main_menu, tearoff=False)
        mode_menu.add_command(label="Sender", command=lambda: self.raise_frame(self.sender_frame))
        mode_menu.add_command(label="Receiver", command=lambda: self.raise_frame(self.receiver_frame))
        main_menu.add_cascade(label="Mode", menu=mode_menu)
        main_menu.add_command(label="Settings", command=lambda: self.raise_frame(self.settings_frame))
        self.master.config(menu=main_menu)

    # Este creata interfata pentru sender.
    def init_sender(self):
        self.sender_frame = Frame(self.master)
        self.sender_frame.config(width=self.app_width, height=self.app_height)
        self.sender_frame.place(x=0, y=0)
        sender_msg_window = MessageBox(self.sender_frame, 60, 10)
        sender_msg_window.place(30, 280)
        self.init_sender_buttons()
        self.init_sender_labels()
        self.init_sender_entries()
        self.widgets.sender_msg_box = sender_msg_window

    """ Sunt create butoanele de pe interfata sender-ului.
        Fiecarui buton i se va face un 'bind' catre comanda pe care o va executa. """
    def init_sender_buttons(self):
        choose_file_button = ttk.Button(master=self.sender_frame, text="Choose file",
                                        command=lambda: get_file_name(self.widgets))
        choose_file_button.place(x=200, y=150)
        transmit_button = ttk.Button(master=self.sender_frame, text="Transmit file",
                                     command=lambda: create_client(self.widgets))
        transmit_button.place(x=285, y=150)

    # Sunt adaugate diferite label-uri pe interfata sender-ului.
    def init_sender_labels(self):
        title = Label(master=self.sender_frame, text="Sender")
        title.configure(font=("Times New Roman", 18, "bold"))
        title.place(x=243, y=15)
        ip_label = Label(master=self.sender_frame, text="IP:")
        ip_label.place(x=200, y=70)
        port_label = Label(master=self.sender_frame, text="PORT:")
        port_label.place(x=180, y=100)
        message_box_title = Label(master=self.sender_frame, text="Message box")
        message_box_title.place(x=245, y=255)
        cwnd_size_label = Label(master=self.sender_frame, text="CWND size: " + str(self.widgets.cwnd_value.get()))
        cwnd_size_label.place(x=238, y=190)
        self.widgets.cwnd_size_label = cwnd_size_label
        sstresh_size_label = Label(master=self.sender_frame,
                                   text="SStresh value: " + str(self.widgets.sstresh_value.get()))
        sstresh_size_label.place(x=238, y=220)
        self.widgets.sstresh_size_label = sstresh_size_label

    # Sunt create campurile in care se vor introduce ip-ul si portul la care se va conecta sender-ul.
    def init_sender_entries(self):
        s_ip_entry = Entry(master=self.sender_frame)
        s_ip_entry.place(x=221, y=72)
        self.widgets.s_ip_entry = s_ip_entry
        s_port_entry = Entry(master=self.sender_frame)
        s_port_entry.place(x=221, y=102)
        self.widgets.s_port_entry = s_port_entry

    # Este creata interfata pentru receiver.
    def init_receiver(self):
        self.receiver_frame = Frame(self.master)
        self.receiver_frame.config(width=self.app_width, height=self.app_height)
        self.receiver_frame.place(x=0, y=0)
        self.init_receiver_buttons()
        self.init_receiver_labels()
        receiver_msg_window = MessageBox(self.receiver_frame, 60, 10)
        receiver_msg_window.place(30, 280)
        self.widgets.receiver_msg_box = receiver_msg_window

    # Este adaugat butonul de creare a server-ului.
    def init_receiver_buttons(self):
        receiver_connect_button = ttk.Button(master=self.receiver_frame, text="Create server",
                                             command=lambda: create_server(self.widgets))
        receiver_connect_button.place(x=236, y=100)

    # Sunt adaugate diferite label-uri pe interfata receiver-ului.
    def init_receiver_labels(self):
        title = Label(master=self.receiver_frame, text="Receiver")
        title.configure(font=("Times New Roman", 18, "bold"))
        title.place(x=226, y=15)
        message_box_title = Label(master=self.receiver_frame, text="Message box")
        message_box_title.place(x=237, y=255)
        download_percentage = Label(master=self.receiver_frame, text="-- Downloading: 0% --")
        download_percentage.place(x=205, y=200)
        self.widgets.download_percentage = download_percentage

    # Este creata interfata pentru meniul de setari.
    def init_settings(self):
        self.settings_frame = Frame(self.master)
        self.settings_frame.config(width=self.app_width, height=self.app_height)
        self.settings_frame.place(x=0, y=0)
        self.init_radio_buttons()
        self.init_settings_labels()
        self.init_slider()

    # Sunt create butoanele de pe interfata sender-ului.
    def init_radio_buttons(self):
        Radiobutton(self.settings_frame, text="1", variable=self.widgets.cwnd_value, value=1).place(x=75, y=70)
        Radiobutton(self.settings_frame, text="4", variable=self.widgets.cwnd_value, value=4).place(x=145, y=70)
        Radiobutton(self.settings_frame, text="8", variable=self.widgets.cwnd_value, value=8).place(x=215, y=70)
        Radiobutton(self.settings_frame, text="16", variable=self.widgets.cwnd_value, value=16).place(x=285, y=70)
        self.widgets.cwnd_value.set(1)
        Radiobutton(self.settings_frame, text="4", variable=self.widgets.sstresh_value, value=4).place(x=75, y=200)
        Radiobutton(self.settings_frame, text="8", variable=self.widgets.sstresh_value, value=8).place(x=145, y=200)
        Radiobutton(self.settings_frame, text="16", variable=self.widgets.sstresh_value, value=16).place(x=215, y=200)
        Radiobutton(self.settings_frame, text="32", variable=self.widgets.sstresh_value, value=32).place(x=285, y=200)
        self.widgets.sstresh_value.set(8)
        Radiobutton(self.settings_frame, text="128", variable=self.widgets.pack_size, value=128).place(x=75, y=300)
        Radiobutton(self.settings_frame, text="1024", variable=self.widgets.pack_size, value=1024).place(x=145, y=300)
        Radiobutton(self.settings_frame, text="16384", variable=self.widgets.pack_size, value=16384).place(x=215, y=300)
        Radiobutton(self.settings_frame, text="65200", variable=self.widgets.pack_size, value=65200).place(x=285, y=300)
        self.widgets.pack_size.set(16384)

    # Sunt adaugate diferite label-uri in meniul de setari.
    def init_settings_labels(self):
        cwnd_label = Label(master=self.settings_frame, text="CWND size:")
        cwnd_label.configure(font=("Times New Roman", 14, "bold"))
        cwnd_label.place(x=55, y=40)
        cwnd_message = Label(master=self.settings_frame, text="The cwnd size consists in the maximum number of packages that "
                                                              "may be in transit.")
        cwnd_message.place(x=55, y=105)
        sstresh_label = Label(master=self.settings_frame, text="SSTRESH value:")
        sstresh_label.configure(font=("Times New Roman", 14, "bold"))
        sstresh_label.place(x=55, y=170)
        sstresh_label = Label(master=self.settings_frame, text="Package size(bytes):")
        sstresh_label.configure(font=("Times New Roman", 14, "bold"))
        sstresh_label.place(x=55, y=270)
        lost_packages_label = Label(master=self.settings_frame, text="Lost packages(%):")
        lost_packages_label.configure(font=("Times New Roman", 14, "bold"))
        lost_packages_label.place(x=55, y=360)

    # Creare slider pentru preluarea procentajului de pachete carora li se va face 'drop'.
    def init_slider(self):
        lost_packages_slider = Scale(self.settings_frame, from_=0, to=50, orient=HORIZONTAL, variable = self.widgets.lost_percentage)
        lost_packages_slider.place(x=225, y=347)

    # Permite comutarea intre interfata sender-ului si cea a receiver-ului.
    def raise_frame(self, frame):
        if frame == self.settings_frame and self.widgets.connection_is_active == True:
            mb.showinfo(title="Error", message="Settings may not be changed while file is transfered.")
            return
        frame.tkraise()
        self.widgets.sstresh_size_label['text'] = "SStresh value: " + str(self.widgets.sstresh_value.get())
        self.widgets.cwnd_size_label['text'] = "CWND size: " + str(self.widgets.cwnd_value.get())


if __name__ == "__main__":
    root = Tk()
    my_gui = GUI(root)
    root.mainloop()





