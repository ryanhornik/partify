import threading
import time
import spotipy
from random import choice
from server.spotify_apple_script import execute_spotify_command, pause_song, resume_song


class MusicPlayerThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pause = threading.Event()
        self._pause.clear()

    def pause(self):
        self._pause.set()

    def paused(self):
        return self._pause.isSet()


def dream_until_wake(sleep_left):
    sleep_step = 0.1
    while sleep_left > 0:
        time.sleep(min(sleep_left, sleep_step))
        sleep_left -= sleep_step
        if threading.current_thread().paused():
            pause_song()
            return True
    return False


def get_random_weighted_song(server_context):
    song_uri = choice(list(server_context.song_queue.elements()))
    return server_context.client.track(song_uri)


def drain_queue(server_context):
    while len(server_context.song_queue) > 0:
        next_song = get_random_weighted_song(server_context)
        del server_context.song_queue[next_song["uri"]]
        if play_song_and_wait(next_song):
            break


def play_song_and_wait(song):
    duration = song["duration_ms"]
    execute_spotify_command('play track "{}"'.format(song["uri"]))
    execute_spotify_command('play')  # Seems to sometimes not actually start playback from the play track command
    print("Now playing {} by {}".format(song["name"], song["artists"][0]["name"]))

    sleep_left = duration / 1000
    return dream_until_wake(sleep_left)


def resume_song_then_wait(server_context):
    player_position = float(execute_spotify_command('return player position').decode())
    song_duration = float(execute_spotify_command('return duration of current track'))
    remaining = (song_duration / 1000) - player_position
    resume_song()
    if not dream_until_wake(remaining):
        drain_queue(server_context)


def add_song_when_nearly_empty(queue, all_songs):
    while len(queue) > 1:
        time.sleep(1)
    while len(queue) < 2:
        queue.update((choice(all_songs),))

    threading.Thread(target=add_song_when_nearly_empty, args=(queue, all_songs)).start()
