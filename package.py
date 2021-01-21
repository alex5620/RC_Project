import math

""" Structura unui pachet este urmatoarea:
    - 3 octeti pentru numarul pachetului
    - 2 octeti pentru dimensiunea pachetului
    - 2 octeti pentru acknowledgment
    - 1 octet pentru flag-uri: flag-urile disponibile sunt cel de SYN(bitul 0) si cel de FIN(bitul 1)
    - un numar variabil de octeti de date(insumat nr. maxim de octeti va fi de aproximativ 65536).
    Pachetele vor fi transmise dupa urmatorul principiu: sender-ul va seta fiecarui pachet un numar unic de identificare, 
    dar si campul 'dim' care va fi completat cu numarul de octeti de date transmisi, iar receiver-ul va trebui sa trimita
    inapoi un pachet care va avea setat acelasi numar de identificare plus campul ack completat cu dimensiunea 
    pachetului receptat. """

class Package:
    def __init__(self):
        self.bytes = bytearray(8)

    # Permite setarea numarului de pachet. Numarul de pachet trebuie convertit din decimal in hexadecimal
    def set_num(self, number):
        bytes_num = math.ceil(number.bit_length() / 8)
        data = (number).to_bytes(bytes_num, byteorder='little')
        for i in range(bytes_num):
            self.bytes[2-i] = data[i]

    # Functie getter pentru numarul de pachet
    def get_num(self):
        return int.from_bytes(self.bytes[0:3], "big")

    # Permite setarea campului dimensiune
    def set_dim(self, dim):
        bytes_num = math.ceil(dim.bit_length() / 8)
        data = (dim).to_bytes(bytes_num, byteorder='little')
        for i in range(bytes_num):
            self.bytes[4-i] = data[i]

    # Functie getter pentru campul dimensiune
    def get_dim(self):
        return int.from_bytes(self.bytes[3:5], "big")

    # Permite setarea campului acknowledgment
    def set_ack(self, ack):
        bytes_num = math.ceil(ack.bit_length() / 8)
        data = (ack).to_bytes(bytes_num, byteorder='little')
        for i in range(bytes_num):
            self.bytes[6 - i] = data[i]

    # Functie getter pentru campul acknowledgment
    def get_ack(self):
        return int.from_bytes(self.bytes[5:7], "big")

    # Permite activarea unui flag
    def set_flag(self, position):
        self.bytes[7] = self.bytes[7] | 1 << position

    # Functie getter pentru obtinerea valorii unui flag
    def get_flag(self, position):
        return (self.bytes[7]>>position)%2

    # Permite adaugarea datelor intr-un pachet.
    def add_data(self, data):
        self.bytes = self.bytes+data

    """ Permite crearea unui pachet folosind un array de octeti.
        De exemplu, cand server-ul preia un pachet(array de octeti) nu poate obtine direct informatiile continute
        de acesta, prin urmare trebuie creat intai un pachet folosind acele date. """
    def set_data(self, data):
        self.bytes = data

    # Functie getter pentru continutul unui pachet.
    def get_data(self):
        return self.bytes
