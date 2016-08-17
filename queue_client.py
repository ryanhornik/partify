import socket
import sys

if __name__ == '__main__':
    HOST = '127.0.0.1'  # The remote host
    PORT = 50007  # The same port as used by the server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(bytes(' '.join(sys.argv[1:]), 'UTF-8'))
        response = s.recv(1024).decode()
        if response:
            print(response)
