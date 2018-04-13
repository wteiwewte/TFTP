#!/usr/bin/env python3
import sys
import socket
import threading

opcodes_str = {'RRQ': '\x00\x01', 'WRQ': '\x00\x02', 'DATA': '\x00\x03', 'ACK': '\x00\x04', 'ERROR': '\x00\x05',
               'OACK': '\x00\x06'}
opcodes_nr = {'RRQ': 1, 'WRQ': 2, 'DATA': 3, 'ACK': 4, 'ERROR': 5, 'OACK': 6}


def is_correct_number_of_arguments_passed():
    if len(sys.argv) == 3:
        return True
    else:
        return False


def prev_nr(nr):
    if nr == 0:
        return 2 ** 16
    else:
        return nr - 1


def next_nr(nr):
    if nr == 2 ** 16 - 1:
        return 0
    else:
        return nr + 1


def get_file_name(packet):
    return packet[2:(packet[2:].index("\0") + 2)]


def get_path_to_file(file_name):
    return sys.argv[2] + '/' + file_name

def get_window_size(packet):
    return int(packet[(packet.index('windowsize') + len('windowsize') + 1):(len(packet)-1)])

def is_this_new_RRQ(packet):
    if packet.count('\0') == 3 and packet[len(packet)-1] == '\0':
        return False
    else:
        return True


class TFTP_server:
    def __init__(self, port_nr):
        self.port_nr = port_nr
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def serve(self):
        self.sock.bind(('', self.port_nr))
        while True:
            packet, address = self.sock.recvfrom(4096)

            if int.from_bytes(packet[0:2], byteorder='big') == opcodes_nr['RRQ']:
                packet = packet.decode()
                class handler(threading.Thread):
                    def __init__(self, addr, RRQ_packet):
                        super().__init__()
                        self.connection_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        self.connection_socket.settimeout(0.1)
                        self.addr = addr
                        self.pathfile = get_path_to_file(get_file_name(packet))
                        self.block_nr = 1
                        self.window_size = None
                        self.RRQ_packet = RRQ_packet
                        self.mapped_data = dict()
                        self.read_blocks = 1

                    def run(self):
                        """Check version of given RRQ and set then windowsize (if type of RRQ is old windowsize = 1)"""
                        if is_this_new_RRQ(self.RRQ_packet):
                            self.window_size = get_window_size(self.RRQ_packet)
                            if self.window_size > 16:
                                self.window_size = 16
                        else:
                            self.window_size = 1
                        """Send OACK to client"""
                        self.connection_socket.sendto((opcodes_str['OACK']+ 'windowsize\x00{}\x00').format(str(self.window_size)).encode(), self.addr)
                        """read whole file"""
                        with open(self.pathfile, 'rb') as f:
                            while True:
                                self.mapped_data[self.read_blocks] = f.read(512)
                                self.read_blocks += 1
                                if len(self.mapped_data[self.read_blocks-1]) < 512:
                                    self.read_blocks -= 1
                                    break


                        """send this file to client"""
                        while True:
                            """send windowsize blocks of data"""
                            for i in range(self.window_size):
                                try:
                                    if self.block_nr+i > self.read_blocks:
                                        """if we sent all previous data end connection"""
                                        break
                                    self.connection_socket.sendto(opcodes_str['DATA'].encode() + (self.block_nr+i).to_bytes(2, byteorder='big')
                                                                  + self.mapped_data[self.block_nr+i], self.addr)
                                except IOError:
                                    break
                            """and then get ack from client"""
                            while True:
                                try:
                                    ack, ack_addr = self.connection_socket.recvfrom(4096)
                                    self.block_nr = next_nr(int.from_bytes(ack[2:4], byteorder='big'))
                                    break
                                except socket.timeout:
                                    """send this window again"""
                                    break
                            if self.block_nr == self.read_blocks + 1:
                                break

                        self.connection_socket.close()

                handler(address, packet).start()


if __name__ == "__main__":
    if is_correct_number_of_arguments_passed():
        server = TFTP_server(int(sys.argv[1]))
        server.serve()
