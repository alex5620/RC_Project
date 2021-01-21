from package import Package
import socket
import threading
import math
import time
import os

# Calea catre fisierul ce va fi transmis
file_path = ""

# Functie getter pentru obtinerea caii pentru fisierul selectat
def get_path():
    global file_path
    return file_path

# Functie setter pentru calea catre fisier
def set_path(path):
    global file_path
    file_path = path

""" Clasa se ocupa de transmiterea pachetelor si retransmiterea celor pentru care nu s-a primit ack.
    Pachetele sunt stocate intr-un dictionar in care cheia reprezinta pachetul, iar valoarea este data de momentul
    transmiterii pachetului.
    Clasa ClientPackagesHandler consta intr-un thread care itereaza constant peste elementele dictionarului si
    retransmite pachetele in cazul in care a trecut un interval de 0.5 secunde de la transmiterea pachetului, 
    interval in care nu s-a primit pachetul de ack.
    Atunci cand are loc o cerere de trimitere/stergere a unui pachet aceasta are loc dintr-un alt Thread, de aceea
    trebuie utilizat un mecanism prin care se asigura sincronizarea(de aici si utilizarea Lock-urilor).
    De exemplu, daca intr-un moment Thread-ul din clasa ClientPackagesHandler itera peste elemente dictionarului
    si un alt Thread(al clasei Client) ar fi dus la adaugarea/stergerea unui element in/din dictionar atunci ar fi
    fost generata o eroare de sincronizare. """
class ClientPackagesHandler:
    def __init__(self, socket, address):
        # dictionarul ce va contine pachetele
        self.packages = {}
        self.socket = socket
        self.address = address
        # Lock folosit pentru sincronizare atunci cand se adauga un element in dictionar
        self.add_lock = threading.Lock()
        # Lock folosit pentru sincronizare atunci cand se elimina un element din dictionar
        self.remove_lock = threading.Lock()
        # Lock folosit pentru sincronizare atunci cand se retransmit pachetele pentru care nu s-a primit ack
        self.send_lock = threading.Lock()
        self.total_pack_sent = 0

    # Este creat un Thread ce va itera peste elementele dictionarului si va retransmite pachetele daca este cazul.
    def run(self):
        thread = threading.Thread(target=self.send_packages)
        self.is_running = True
        thread.start()

    """ Inainte de iterarea peste elementele dictionarului ne asiguram ca nu exista un alt Thread care sa modifice
        dimensiunea acestuia(care sa adauge un nou pachet sau care sa elimine unul existent).
        Dupa ce s-a asigurat sincronizarea cu celelalte thread-uri, are loc retransmiterea pachetelor daca este cazul,
        adica daca nu s-a primit pachetul de ack intr-un interval de 0.5 secunde.
        Cand un pachet este retransmis este reinitializata si starea de slow start.
        Dupa fiecare iterare Thread-ul intra in starea de sleep pentru un interval de timp. """
    def send_packages(self):
        while self.is_running:
            while self.add_lock.locked() or self.remove_lock.locked():
                time.sleep(0.001)
            self.send_lock.acquire()
            for package in self.packages:
                new_time = int(round(time.time() * 1000))
                if new_time - self.packages[package] >= 500:
                    self.send_package(package)
                    self.message_box.insert_message("Package no. " + str(package.get_num()) + " has been resent.")
                    self.packages[package] = new_time
                    self.client.slow_start()
            self.send_lock.release()
            time.sleep(0.3)

    # Functia de transmitere a unui pachet
    def send_package(self, package):
        self.socket.sendto(package.get_data(), self.address)
        self.total_pack_sent = self.total_pack_sent + 1
        time.sleep(0.08)

    """ Functia de adaugare a unui nou pachet in dictionar.
        Avand in vedere faptul ca aceasta functie este apelata de catre un alt thread decat cel al handler-ului, trebuie sa ne
        asiguram ca dictionarul nu este modificat in timp ce thread-ul clasei handler itera peste elementele dictionarului. """
    def add_package(self, package):
        while self.remove_lock.locked() or self.send_lock.locked():
            time.sleep(0.001)
        self.add_lock.acquire()
        self.send_package(package)
        self.message_box.insert_message("Package no. " + str(package.get_num()) + " has been sent.")
        self.packages[package] = int(round(time.time() * 1000))
        self.add_lock.release()

    """ Functia de eliminare a unui pachet din dictionar.
        Avand in vedere faptul ca aceasta functie este apelata de catre un alt thread decat cel al handler-ului trebuie sa
        asiguram ca dictionarul nu este modificat in timp ce thread-ul clasei handler itera peste elementele dictionarului. """
    def remove_package(self, r_pack):
        while self.add_lock.locked() or self.send_lock.locked():
            time.sleep(0.001)
        self.remove_lock.acquire()
        for pack in self.packages:
            if pack.get_num() == r_pack.get_num() and pack.get_dim() == r_pack.get_ack():
                self.message_box.insert_message("Ack for package no. " + str(r_pack.get_num()) + " has been received.")
                del self.packages[pack]
                break
        self.remove_lock.release()

    # Functia este apelata in urma primirii pachetului FIN si duce la oprirea thread-ului ce itera dictionarul.
    def set_run(self, val):
        self.is_running = val

    # Functia returneaza numarul total de pachete transmise.
    def get_total_pack_sent(self):
        return self.total_pack_sent

    # Functia seteaza referinta catre clasa Client.
    def set_client(self, client):
        self.client = client

    def set_message_box(self, message_box):
        self.message_box = message_box

""" Clasa consta in 2 thread-uri, unul pentru citirea datelor din fisier, crearea pachetelor si adaugare acestora
    in dictionarul detinut de clasa handler care se ocupa de transmiterea acestora, si un altul care se ocupa de
    receptarea pachetelor de ack urmate de cererea catre clasa handler ce va duce la scoaterea pachetului receptionat.
    Tot aceasta clasa se ocupa de gestionarea ferestrei de congestie si a numarului de pachete aflate in tranzit.
    Astfel, client-ul poate avea in tranzit un numar de pachete cel mult egal cu dimensiunea ferestrei de congestie.
    Dimensiunea ferestrei de congestie(cwnd) este modificata in functie de starea in care se afla algoritmul, mai exact
    daca dimensiunea ferestrei este mai mica decat valoarea de prag(sstresh), atunci aceasta va creste cu 1 in urma
    transmiterii unui pachet, iar daca dimensiunea a depasit valoarea de prag atunci fereastra va creste cu o valoare
    egala cu 1/cwnd.
    De fiecare data cand are loc retransmiterea unui pachet este reinitializata si starea de slow start, adica
    noua valoarea de prag va fi egala cu jumatatea valorii ferestrei de congestie, iar ferestra va fi reinitializata cu 1
    (sstresh = cwnd/2, cwnd = 1). """
class Client():
    def __init__(self, ip, port, widgets):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # socket-ul va fi neblocant pentru a nu forta thread-ul sa astepte pana datele sunt receptionate
        self.sock.setblocking(False)
        # counter pentru numerotarea pachetelor
        self.pack_cnt = 0
        self.message_box = widgets.sender_msg_box
        # crearea handler-ului ce se va ocupa de transmiterea/retransmiterea pachetelor
        self.handler = ClientPackagesHandler(self.sock, (ip, port))
        self.handler.set_client(self)
        self.handler.set_message_box(self.message_box)
        # timer-ul folosit pentru a inchide conexiunea in cazul in care ack-ul pentru pachetul FIN nu mai este primit
        self.timer = 0
        self.widgets = widgets
        # dimensiunea ferestrei de congestie
        self.cwnd = self.widgets.cwnd_value.get()
        # valoarea de prag ce ajuta la distingerea starii de slow start de starea de evitare a congestiei
        self.sstresh = self.widgets.sstresh_value.get()
        # numarul de pachete aflate in tranzit
        self.pack_in_transit = 0

    """ Functia consta intr-un thread ce se ocupa de citirea datelor din fisier, formarea pachetelor
        si transmiterea acestora catre clasa handler. """
    def send(self):
        self.handler.run()
        # are loc starea de initializare(este transmis pachetul SYN si se asteapta ack-ul pentru acesta).
        self.send_syn_pack()
        self.wait_for_syn_pack()
        while True:
            # un nou pachet este creat doar daca nr. de pachete aflate in tranzit este mai mic decat dim. ferestrei
            if self.pack_in_transit < self.cwnd:
                data = self.rf.read(self.widgets.pack_size.get()-16)
                # nu s-a ajuns la finalul fisierului, asadar un nou pachet este creat si transmis clasei handler
                if len(data) != 0:
                    pack = self.create_pack(data)
                    self.handler.add_package(pack)
                    self.inc_pack_in_transit()
                # s-a ajuns la finalul fisierului prin urmare trebuie transmis pachetul FIN pentru incheierea conexiunii.
                else:
                    pack = Package()
                    pack.set_flag(1)
                    pack.set_num(self.pack_cnt)
                    self.message_box.insert_message("FIN pack has been sent.")
                    self.handler.add_package(pack)
                    # salvam momentul trimiterii pachetului FIN
                    self.timer = int(round(time.time() * 1000))
                    self.rf.close()
                    break
            time.sleep(0.001)

    """ Functia consta intr-un thread ce se ocupa de receptionarea pachetelor de ack. In urma receptionarii unui pachet
        se va apela si functia de eliminare a pachetelui din dictionarul detinut de handler. """
    def receive(self):
        r_data = None
        while True:
            try:
                r_data, address = self.sock.recvfrom(self.widgets.pack_size.get())
            except BlockingIOError:
                # buffer-ul socket-ului este gol
                pass
            except ConnectionResetError:
                """ Daca ack-ul pentru pachetul FIN nu a fost receptionat in cel mult 2 secunde de la
                trimiterea acestuia, atunci inchidem conexiunea automat. """
                if (self.timer != 0 and int(round(time.time() * 1000)) - self.timer > 2000):
                    self.handle_end_of_connection()
                    break
                time.sleep(0.5)

            # daca s-a primit un pachet de ack atunci acesta este eliminat din dictionar si este actualizata fereastra
            if r_data:
                r_pack = Package()
                r_pack.set_data(r_data)
                self.handler.remove_package(r_pack)
                self.update_cwnd()
                self.dec_pack_in_transit()
                # s-a receptionat ultimul pachet, adica cel care are flag-ul de FIN activ, asadar conexiunea este incheiata
                if r_pack.get_flag(1):
                    self.handle_end_of_connection()
                    break
                r_data = None

    """ Crearea pachetului SYN consta in setarea flag-ului SYN, a numarului pachetului
        si in adaugarea in campul de date a denumirii fisierului, a numarului total de pachete ce vor fi transmise,
        si a dimensiunii unui pachet. """
    def send_syn_pack(self):
        self.widgets.connection_is_active = True
        syn_pack = Package()
        syn_pack.set_flag(0)
        file_size = os.path.getsize(file_path)
        total_pack_num = int(math.ceil(file_size/(self.widgets.pack_size.get()-16)))
        file_path_encoded = (file_path+"/"
                             +str(total_pack_num)+"/"
                             +str(self.widgets.pack_size.get())+"/"
                             +str(self.widgets.lost_percentage.get())).encode()
        syn_pack.set_num(self.pack_cnt)
        self.inc_cnt()
        syn_pack.add_data(file_path_encoded)
        syn_pack.set_dim(len(file_path_encoded))
        self.handler.add_package(syn_pack)
        self.message_box.insert_message("SYN package has been sent.")

    """ Primirea pachetului ack pentru pachetul SYN. Pachetul ack pentru SYN este gestionat diferit deoarece
        pe langa asteptarea propriu-zisa a pachetului mai consta si in deschiderea fisierului a carui date
        urmeaza a fi transmise, dar si a crearii thread-ului ce se va ocupa de gestionarea receptionarii pachetelor ack. """
    def wait_for_syn_pack(self):
        data = None
        while not data:
            data, address = self.sock.recvfrom(self.widgets.pack_size.get())
            time.sleep(0.01)
        server_syn_pack = Package()
        server_syn_pack.set_data(data)
        if server_syn_pack.get_flag(0):
            self.message_box.insert_message("SYN package has been received. Successful connection.")
            self.rf = open(file_path, "rb")
            self.handler.remove_package(server_syn_pack)
        thread2 = threading.Thread(target=self.receive)
        thread2.start()

    # Functia creeaza un pachet pe baza datelor citite din fisier.
    def create_pack(self, data):
        pack = Package()
        pack.add_data(data)
        pack.set_dim(len(data))
        pack.set_num(self.pack_cnt)
        self.inc_cnt()
        return pack

    def inc_pack_in_transit(self):
        self.pack_in_transit = self.pack_in_transit + 1

    def dec_pack_in_transit(self):
        self.pack_in_transit = self.pack_in_transit - 1

    """ Functia de actualizare a ferestrei de congestie in functie de starea algoritmului.
        In faza de slow start fereastra(cwnd) va creste cu 1, iar in faza de evitare a congestiei dimensiunea ferestrei
        va creste cu 1/cwnd. """
    def update_cwnd(self):
        if self.cwnd < self.sstresh:
            self.cwnd = self.cwnd + 1
        else:
            self.cwnd = self.cwnd + 1/int(self.cwnd)
        self.widgets.cwnd_size_label['text'] = "CWND size: {:.1f}".format(self.cwnd)

    """ Reinitializarea starii de slow start in urma retransmiterii unui pachet.
        Noua valoare de prag(sstresh) va fi egala cu jumatatea valorii dimensiunii ferestrei de congestie(cwnd) de dinaintea
        retransmiterii pachetului, iar fereastra de congestie va avea valoarea 1. """
    def slow_start(self):
        self.sstresh = self.cwnd // 2
        self.cwnd = 1
        self.widgets.sstresh_size_label['text']= "SStresh value: " + str(self.sstresh)
        self.widgets.cwnd_size_label['text'] = "CWND size: {:.1f}".format(self.cwnd)

    # Incheierea conexiunii, socket-ul este inchis, iar handler-ul iese din starea running.
    def handle_end_of_connection(self):
        self.widgets.connection_is_active = False
        self.handler.set_run(False)
        self.sock.close()
        self.message_box.insert_message("FIN pack has been received.")
        self.message_box.insert_message("File has been sent successfully.")
        self.message_box.insert_message("Total packages sent: " + str(self.handler.get_total_pack_sent()) + ".")

    def run(self):
        thread = threading.Thread(target = self.send)
        thread.start()

    def inc_cnt(self):
        self.pack_cnt = self.pack_cnt + 1

