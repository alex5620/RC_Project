import socket
from package import Package
from threading import Thread
import random

""" Clasa ajuta la reordonarea pachetelor receptionate, stocandu-le pe cele care nu au venit in ordinea corespunzatoare.
    De exemplu, daca in fisier au fost scrise primele 14 pachete si se asteapta pachetul cu nr. 15, dar inaintea acestuia
    au fost receptionate pachetele 16 si 17 atunci acestea vor fi stocate temporar intr-un dictionar. Cand pachetul cu nr. 15 
    va fi receptionat, acesta va fi scris in fisier si imediat dupa aceea vor fi scrise si pachetele 16 si 17, dar si altele
    daca acestea se aflau in ordinea corespunzatoare. """
class ServerPackagesHandler:
    def __init__(self):
        self.packages = {}

    # adaugarea unui pachet in dictionar, cheia va fi reprezentata de numarul pachetelui, iar valoarea de pachetul insusi
    def add_package(self, package):
        self.packages[package.get_num()] = package

    # se verifica existenta unui pachet
    def exists(self, num):
        return num in self.packages.keys()

    """ De fiecare data cand este scris un pachet in fisier se verifica si elementele dictionarului pentru a determina
        daca exista pachete ulterioare acestuia, functia returnand astfel numarul ultimului pachet din aceasta lista de
        pachete ulterioare. """
    def get_last_existing_package_num(self, start_num):
        end_num = start_num
        cond = True
        while cond:
            if end_num + 1 in self.packages.keys():
                end_num = end_num + 1
            else:
                cond = False
        return end_num

    # functia scoate din dictionar un pachet si il returneaza
    def pop_package(self, key):
        pack = self.packages[key]
        del self.packages[key]
        return pack

# Clasa se ocupa de receptionarea pachetelor, reordonarea acestora si scrierea lor in fisier.
class Server():
    def __init__(self, ip, port, widgets):
        self.message_box = widgets.receiver_msg_box
        self.download_percentage = widgets.download_percentage
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((ip, port))
        # setam socket-ul ca fiind neblocant
        self.sock.setblocking(False)
        self.pack_cnt = 0
        # procentul de pachete carora li se va face 'drop'
        self.lost_percentage = 0
        self.pack_size = 512
        self.widgets = widgets
        # cream handler-ul care va stoca temporar pachetele ce nu apar in ordine
        self.handler = ServerPackagesHandler()

    def run(self):
        thread = Thread(target=self.listen)
        thread.start()

    def listen(self):
        data = None
        address = None
        while True:
            try:
                data, address = self.sock.recvfrom(self.pack_size)
            except BlockingIOError:
                # buffer-ul este gol
                pass
            # a fost receptionat un pachet
            if data:
                # este creat pachetul pe baza datelor receptionate
                pack = Package()
                pack.set_data(data)
                # verificam ca pachetul are dimensiunea specificata, altfel ii facem 'drop'
                if pack.get_dim() == len(pack.get_data()[8:]):
                    # se verifica daca a fost receptionat pachetul SYN
                    if self.pack_cnt == 0 and pack.get_flag(0):
                        self.handle_syn_pack(pack, address)
                    # se verifica daca a fost receptionat pachetul FIN
                    elif pack.get_flag(1):
                        # se verifica daca pachetul FIN este cel asteptat
                        if pack.get_num() == self.pack_cnt:
                            # daca pachetul FIN este cel asteptat atunci trimitem ack-ul si incheiem conexiunea.
                            self.handle_fin_pack(address)
                            break
                    # s-a receptionat un pachet normal(cu flag-urile SYN si FIN inactive).
                    else:
                        rand_val = random.random()
                        # facem 'drop' pachetelor conform procentului indicat
                        if rand_val > self.lost_percentage:
                            # am primit pachetul cu numarul asteptat, adica care urmeaza a fi scris in fisier
                            if pack.get_num() == self.pack_cnt:
                               self.handle_normal_pack(pack, address)
                            # a fost receptionat un pachet care a fost deja scris in fisier
                            elif pack.get_num() < self.pack_cnt:
                                self.handle_old_package(pack, address)
                            # a fost receptionat un pachet ulterior celui asteptat
                            else:
                                self.handle_following_package(pack, address)
                        else:
                            self.message_box.insert_message("Package no. " + str(pack.get_num()) + " has been dropped.")
                data = None

    """ Functia se ocupa de gestionarea primirii unui pachet SYN, adica a crearii unei conexiuni, acest lucru constand in
    deschiderea fisierului in care va avea loc scrierea pachetelor si de asemenea in transmiterea ack-ului pentru
    pachetul SYN primit. """
    def handle_syn_pack(self, pack, address):
        self.message_box.insert_message("SYN package has been received.")
        list = pack.get_data()[8:].decode().split("/")
        self.file_name = list[-4]
        self.wf = open("r" + list[-4], "wb")
        self.total_pack_num = int(list[-3])
        self.pack_size = int(list[-2])
        self.lost_percentage = int(list[-1])/100
        syn_pack = self.get_ack_for_syn_pack(pack.get_dim())
        self.sock.sendto(syn_pack.get_data(), address)
        self.message_box.insert_message("SYN package has been sent.")

    # returneaza un packet ack pentru pachetul SYN
    def get_ack_for_syn_pack(self, dim):
        ack_pack = Package()
        ack_pack.set_flag(0)
        ack_pack.set_num(self.pack_cnt)
        self.inc_cnt()
        ack_pack.set_ack(dim)
        return ack_pack

    """ Functia gestioneaza primirea pachetului FIN, ceea ce costa in inchiderea fisierului, trimiterea ack-ului pentru
        pachetul FIN primit si inchiderea conexiunii. """
    def handle_fin_pack(self, address):
        self.wf.close()
        self.message_box.insert_message("FIN pack has been received.")
        ack_pack = Package()
        ack_pack.set_flag(1)
        ack_pack.set_num(self.pack_cnt)
        self.sock.sendto(ack_pack.get_data(), address)
        self.message_box.insert_message("FIN pack has been sent.")
        self.message_box.insert_message("File " + self.file_name + " has been received successfully.")
        self.sock.close()

    """ Functia gestioneaza primirea unui pachet normal, adica a unui pachet care conform ordinii urmeaza a fi scris in fisier.
    Asadar, scriem datele in fisier, cream si trimitem pachetul ack si in cazul in care in dictionarul handler-ului
    exista pachete ce urmeaza acestuia, le scriem si pe ele in fisier si le eliminam din dictionar. """
    def handle_normal_pack(self, pack, address):
        self.wf.write(pack.get_data()[8:])
        self.message_box.insert_message("Package no. " + str(pack.get_num()) + " has been received.")
        ack_pack = self.get_ack_pack(pack)
        self.sock.sendto(ack_pack.get_data(), address)
        self.message_box.insert_message("Ack for package no. " + str(pack.get_num()) + " has been sent.")
        self.write_next_packages_if_exists()
        self.download_percentage['text'] = "-- Downloading: {:.1f}% --".format(
            ((self.pack_cnt - 1) / self.total_pack_num) * 100, 1)

    # returneaza un pachet ack normal
    def get_ack_pack(self, pack):
        ack_pack = Package()
        ack_pack.set_num(pack.get_num())
        ack_pack.set_ack(pack.get_dim())
        return ack_pack

    """ Atunci cand este receptionat pachetul cu nr. asteptat, se verifica daca exista pachete ulterioare acestuia in 
        dictionarul handler-ului pentru a putea fi scrise in fisier conform ordinii. """
    def write_next_packages_if_exists(self):
        last_pack_num = self.handler.get_last_existing_package_num(self.pack_cnt)
        if last_pack_num != self.pack_cnt:
            for i in range(self.pack_cnt + 1, last_pack_num + 1):
                w_pack = self.handler.pop_package(i)
                self.wf.write(w_pack.get_data()[8:])
            self.set_cnt(last_pack_num + 1)
        else:
            self.inc_cnt()

    """ Functia gestioneaza primirea unui pachet care a fost deja scris in fisier(a mai fost receptionat),
        ceea ce inseamna ca sender-ul nu a primit ack-ul pentru acesta, prin urmare retrimitem pachetul ack. """
    def handle_old_package(self, pack, address):
        ack_pack = self.get_ack_pack(pack)
        if pack.get_flag(0):
            ack_pack.set_flag(0)
        self.sock.sendto(ack_pack.get_data(), address)
        self.message_box.insert_message("Package no. " + str(pack.get_num()) + " has been received again.")
        self.message_box.insert_message("Ack for package no. " + str(pack.get_num()) + " has been resent.")

    """ Functia gestioneaza primirea unui pachet ulterior celui asteptat, asadar, acesta va fi adaugat in  dictionarul
    handler-ului(in cazul in care nu exista deja), urmat de trimiterea pachetului ack. """
    def handle_following_package(self, pack, address):
        if not self.handler.exists(pack.get_num()):
            self.handler.add_package(pack)
        ack_pack = self.get_ack_pack(pack)
        self.sock.sendto(ack_pack.get_data(), address)
        self.message_box.insert_message("Package no. " + str(pack.get_num()) + " has been received.")
        self.message_box.insert_message("Ack for package no. " + str(pack.get_num()) + " has been sent.")

    def inc_cnt(self):
        self.pack_cnt = self.pack_cnt + 1

    def set_cnt(self, value):
        self.pack_cnt = value