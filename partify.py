import socket
import sys
from server.server_config import HOST, PORT


if __name__ == '__main__':
    from client import commands
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        response = commands.Command.send_command(sys.argv, s)
        if response:
            print(response)