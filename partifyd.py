from server.queue_server import Server
import sys

if __name__ == '__main__':
    username = sys.argv[1]
    fallback = sys.argv[2]  # "55wosJOkE6D68GTXRQ9kI0"
    Server(username=username, fallback_playlist_id=fallback).start()
