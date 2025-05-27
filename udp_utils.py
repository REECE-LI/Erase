import socket


class UdpClass:
    def __init__(self, local_address, remote_address):
        self.local_address = local_address
        self.remote_address = remote_address
        self.sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_recv.bind(local_address)
        #  self.sock_recv.setblocking(False)
        self.sock_recv.settimeout(0.002)

    def send(self, data):
        self.sock_send.sendto(data, self.remote_address)

    def recv(self):
        try:
            return self.sock_recv.recvfrom(100)
        except Exception as e:
            return '0'

    def close(self):
        self.sock_recv.close()
        self.sock_send.close()
