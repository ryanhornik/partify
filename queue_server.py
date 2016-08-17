import spotipy
from spotipy import util
from subprocess import check_output
import time
import threading
from random import choice
from collections import deque
import socket


class MusicPlayerThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pause = threading.Event()
        self._pause.clear()

    def pause(self):
        self._pause.set()

    def paused(self):
        return self._pause.isSet()


def drain_queue(queue):
    while len(queue) > 0:
        if play_song_and_wait(queue.popleft()):
            break


def add_tracks(tracks, song_list):
    for item in tracks['items']:
        song_list.append(item["track"])


def play_song_and_wait(song):
    duration = song["duration_ms"]
    execute_spotify_command('play track "{}"'.format(song["uri"]))
    execute_spotify_command('play')  # Seems to sometimes not actually start playback from the play track command
    print("Now playing {} by {}".format(song["name"], song["artists"][0]["name"]))

    sleep_left = duration / 1000
    return dream_until_wake(sleep_left)


def dream_until_wake(sleep_left):
    sleep_step = 0.1
    while sleep_left > 0:
        time.sleep(min(sleep_left, sleep_step))
        sleep_left -= sleep_step
        if threading.current_thread().paused():
            pause_song()
            return True
    return False


def pause_song():
    execute_spotify_command('pause')


def resume_song():
    execute_spotify_command('play')


def resume_song_then_wait(queue):
    player_position = float(execute_spotify_command('return player position').decode())
    song_duration = float(execute_spotify_command('return duration of current track'))
    remaining = (song_duration / 1000) - player_position
    resume_song()
    if not dream_until_wake(remaining):
        drain_queue(queue)


def execute_spotify_command(cmd):
    script = 'tell application "Spotify" to {}'.format(cmd)
    command = ['osascript', '-e', script]
    return check_output(command)


def get_all_users_songs():
    users_songs = []
    tracks = client.user_playlist_tracks(username, "55wosJOkE6D68GTXRQ9kI0")
    add_tracks(tracks, users_songs)
    while tracks["next"]:
        tracks = client.next(tracks)
        add_tracks(tracks, users_songs)
    return users_songs


def add_song_when_nearly_empty(queue, all_songs):
    while len(queue) > 1:
        time.sleep(1)
    while len(queue) < 2:
        queue.append(choice(all_songs))

    threading.Thread(target=add_song_when_nearly_empty, args=(queue, all_songs)).start()


def main():
    song_queue = deque()
    all_songs = get_all_users_songs()

    command_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    command_socket.bind(('', 50007))
    command_socket.listen(1)

    threading.Thread(target=add_song_when_nearly_empty, args=(song_queue, all_songs), daemon=True).start()

    queue_draining_thread = MusicPlayerThread(target=drain_queue, args=(song_queue,), daemon=True)
    queue_draining_thread.start()

    time.sleep(0.1)
    while True:
        connection, address = command_socket.accept()
        with connection:
            message = 'Success'
            command = connection.recv(1024).decode()
            if not command:
                continue

            lowercase_command = command.lower()
            if lowercase_command == 'p':
                queue_draining_thread = process_playpause(queue_draining_thread, song_queue)
                connection.sendall(bytes("Played/Paused", 'UTF-8'))
            elif lowercase_command == 'n':
                queue_draining_thread = process_next(queue_draining_thread, song_queue)
                connection.sendall(bytes("Playing next song", 'UTF-8'))
            elif lowercase_command.startswith('a'):
                message = process_add(command, song_queue)
                connection.sendall(bytes(message, 'UTF-8'))
            elif lowercase_command == 'q':
                queue_draining_thread = process_quit(queue_draining_thread)
                connection.sendall(bytes('Quitting', 'UTF-8'))
                break
    queue_draining_thread.join()


def process_playpause(queue_draining_thread, song_queue):
    if not queue_draining_thread.is_alive() or queue_draining_thread.paused():
        queue_draining_thread = MusicPlayerThread(target=resume_song_then_wait, args=(song_queue,), daemon=True)
        queue_draining_thread.start()
    else:
        queue_draining_thread.pause()
        queue_draining_thread.join()
    return queue_draining_thread


def process_next(queue_draining_thread, song_queue):
    if queue_draining_thread.is_alive() and not queue_draining_thread.paused():
        queue_draining_thread.pause()
        queue_draining_thread.join()
    queue_draining_thread = MusicPlayerThread(target=drain_queue, args=(song_queue,), daemon=True)
    queue_draining_thread.start()
    time.sleep(0.1)
    return queue_draining_thread


def process_add(command, song_queue):
    try:
        song_id = command.split()[1]
        song = client.track(song_id)
        song_queue.append(song)
    except IndexError:
        return "Command 'a' requires a song id"
    except spotipy.SpotifyException:
        return "Invalid identifier entered for song id"
    else:
        return "Enqueued {}".format(song['name'])


def process_quit(queue_draining_thread):
    if queue_draining_thread.is_alive() and not queue_draining_thread.paused():
        queue_draining_thread.pause()
        queue_draining_thread.join()
    return queue_draining_thread


if __name__ == '__main__':
    username = "ooplease"
    token = util.prompt_for_user_token(username, 'playlist-read-private')
    client = spotipy.Spotify(auth=token)
    main()
