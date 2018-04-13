#!/usr/bin/env python3
import hashlib
import sys
import socket

opcodes_str = {'RRQ': '\x00\x01', 'WRQ': '\x00\x02', 'DATA': '\x00\x03', 'ACK': '\x00\x04', 'ERROR': '\x00\x05', 'OACK': '\x00\x06'}
opcodes_nr = {'RRQ': 1, 'WRQ': 2, 'DATA': 3, 'ACK': 4, 'ERROR': 5, 'OACK': 6}

def is_correct_number_of_arguments_passed():
    if len(sys.argv) == 3:
        return True
    else:
        return False

def prev_nr(nr):
    if nr == 0:
        return 2**16
    else:
        return nr-1

def next_nr(nr):
    if nr == 2 ** 16 - 1:
        return 0
    else:
        return nr + 1

def get_window_size(packet):
    return int(packet[(packet.index('windowsize') + len('windowsize') + 1):(len(packet)-1)])

class TFTP_client:
    def __init__(self, server_name, filename):
        self.server_name = server_name
        self.filename = filename
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.last_address = None
        self.desired_nr_block = 1
        self.sock.settimeout(0.1)
        self.hasher = hashlib.md5()
        self.last_address = None
        self.data = None
        self.mapped_data = dict()
        self.minimum_nr_missing_block = 1
        self.windowsize = None

    def handle_timeout(self):
        """handler for timeout in case we're coping with old-typed server"""
        if self.last_address is not None:
            self.sock.sendto(b'\x00\x04' + (prev_nr(self.desired_nr_block)).to_bytes(2, byteorder='big'),
                             self.last_address)
        else:
            self.sock.sendto(b'\x00\x04' + (prev_nr(self.desired_nr_block)).to_bytes(2, byteorder='big'),
                             (self.server_name, 69))

    def get_file(self):
        """starting connection with server via sending RRQ"""
        #print(opcodes_str['RRQ'] + '{}\x00octet\x00'.format(self.filename))
        self.sock.sendto((opcodes_str['RRQ'] + '{}\x00octet\x00windowsize\x0016\x00'.format(self.filename)).encode(), (self.server_name, 6969))
        try:
            self.data, self.last_address = self.sock.recvfrom(4096)
        except socket.timeout:
            self.handle_timeout()
        """if we got first block of data, that means we're coping with old typed server"""
        if int.from_bytes(self.data[0:2], byteorder='big') == opcodes_nr['DATA']:
            if int.from_bytes(self.data[2:4], byteorder='big') == self.desired_nr_block:
                self.hasher.update(self.data[4:])
                self.desired_nr_block = next_nr(self.desired_nr_block)
                self.sock.sendto(opcodes_str['ACK'].encode() + self.data[2:4], self.last_address)
                if len(self.data) < 516:
                    return
            while True:
                try:
                    self.data, self.last_address = self.sock.recvfrom(4096)
                    if int.from_bytes(self.data[2:4], byteorder='big') == self.desired_nr_block:
                        self.hasher.update(self.data[4:])
                        self.desired_nr_block = next_nr(self.desired_nr_block)
                        self.sock.sendto(opcodes_str['ACK'].encode() + self.data[2:4], self.last_address)
                        if len(self.data) < 516:
                            break
                except socket.timeout:
                    self.handle_timeout()
        elif int.from_bytes(self.data[0:2], byteorder='big') == opcodes_nr['OACK']:
            """getting window size from OACK"""
            self.windowsize = get_window_size(self.data.decode())
            while True:
                for i in range(self.windowsize):
                    try:
                        self.data, self.last_address = self.sock.recvfrom(4096)
                        data_nr = int.from_bytes(self.data[2:4], byteorder='big')
                        self.mapped_data[data_nr] = self.data
                        """setting minimal number of block, which isn't in our map"""
                        if data_nr == self.minimum_nr_missing_block:
                            while self.minimum_nr_missing_block in self.mapped_data.keys():
                                self.minimum_nr_missing_block += 1
                            if len(self.data) < 516:
                                break

                    except socket.timeout:
                        continue
                """sending ACK with minimal number of block absent in our map"""
                self.sock.sendto(opcodes_str['ACK'].encode() + (prev_nr(self.minimum_nr_missing_block)).to_bytes(2, byteorder='big'), self.last_address)
                if len(self.data) < 516:
                    break
            """calculating hash from our blocks"""
            for i in range(self.minimum_nr_missing_block - 1):
                self.hasher.update(self.mapped_data[i+1][4:])





    def print_hash(self):
        print(self.hasher.hexdigest())

if __name__ == "__main__":
    if is_correct_number_of_arguments_passed():
        client = TFTP_client(sys.argv[1], sys.argv[2])
        client.get_file()
        client.print_hash()






