import spotipy
from spotipy import util
import time
import threading
import socket
from collections import Counter
from server.server_config import PORT
from server.commands import Command, process_quit, process_add, process_next, process_playpause, process_get_queue
from server.thread_types import MusicPlayerThread, add_song_when_nearly_empty, drain_queue


def add_tracks(tracks, song_list):
    for item in tracks['items']:
        song_list.append(item["track"]["uri"])


class Server(object):
    def __init__(self, username, fallback_playlist_id):
        self.username = username
        self.token = util.prompt_for_user_token(self.username, 'playlist-read-private')
        self.client = spotipy.Spotify(auth=self.token)
        self.fallback_playlist_id = fallback_playlist_id

        self.command_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.command_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.command_socket.bind(('', PORT))
        self.command_socket.listen(1)
        self.register_commands()

        self.queue_draining_thread = None

        self.song_queue = Counter()
        self.all_songs = self.get_all_users_songs()
        self.running = False

    @staticmethod
    def register_commands():
        Command.register_new('p', process_playpause)
        Command.register_new('n', process_next)
        Command.register_new('a', process_add)
        Command.register_new('q', process_quit)
        Command.register_new('g', process_get_queue)

    def get_all_users_songs(self):
        users_songs = []
        tracks = self.client.user_playlist_tracks(self.username, self.fallback_playlist_id)
        add_tracks(tracks, users_songs)
        while tracks["next"]:
            tracks = self.client.next(tracks)
            add_tracks(tracks, users_songs)
        return users_songs

    def start(self):
        threading.Thread(target=add_song_when_nearly_empty, args=(self.song_queue, self.all_songs), daemon=True).start()

        self.queue_draining_thread = MusicPlayerThread(target=drain_queue, args=(self,), daemon=True)
        self.queue_draining_thread.start()

        time.sleep(0.1)
        self.running = True
        self.run()
        self.queue_draining_thread.join()
        self.command_socket.close()

    def run(self):
        while self.running:
            connection, address = self.command_socket.accept()
            with connection:
                arg_string = connection.recv(1024).decode()
                if not arg_string:
                    continue
                command = Command.get_command(arg_string)
                message = command.action(self, arg_string)
                connection.sendall(message)

    def stop(self):
        self.running = False
