import time
import spotipy
import json
from server.thread_types import MusicPlayerThread, drain_queue, resume_song_then_wait


class Command(object):
    command_map = {}

    def __init__(self, short_code, action):
        self.short_code = short_code
        self.action = action

    @staticmethod
    def register(command):
        Command.command_map[command.short_code] = command

    @staticmethod
    def register_new(short_code, action):
        Command.register(Command(short_code, action))

    @staticmethod
    def get_command(arg_string):
        args = arg_string.split()
        short_code = args[0].lower()
        command = Command.command_map[short_code]
        return command


def process_playpause(server_context, args):
    if not server_context.queue_draining_thread.is_alive() or server_context.queue_draining_thread.paused():
        server_context.queue_draining_thread = MusicPlayerThread(target=resume_song_then_wait,
                                                                 args=(server_context,),
                                                                 daemon=True)
        server_context.queue_draining_thread.start()
        message = "Playing"
    else:
        server_context.queue_draining_thread.pause()
        server_context.queue_draining_thread.join()
        message = "Paused"
    return bytes(message, "UTF-8")


def process_next(server_context, args):
    if server_context.queue_draining_thread.is_alive() and not server_context.queue_draining_thread.paused():
        server_context.queue_draining_thread.pause()
        server_context.queue_draining_thread.join()
    server_context.queue_draining_thread = MusicPlayerThread(target=drain_queue,
                                                             args=(server_context,),
                                                             daemon=True)
    server_context.queue_draining_thread.start()
    time.sleep(0.1)
    return bytes("Playing next", "UTF-8")


def process_add(server_context, args):
    try:
        song_id = args.split()[1]
        song = server_context.client.track(song_id)
        server_context.song_queue.update((song["uri"],))
    except spotipy.SpotifyException:
        message = "Invalid identifier entered for song id"
    else:
        message = "Enqueued {}".format(song['name'])
        print(server_context.song_queue)
    return bytes(message, "UTF-8")


def process_quit(server_context, args):
    if server_context.queue_draining_thread.is_alive() and not server_context.queue_draining_thread.paused():
        server_context.queue_draining_thread.pause()
        server_context.queue_draining_thread.join()
    server_context.stop()
    return bytes("Shutting down server", "UTF-8")


def process_get_queue(server_context, args):
    return bytes(json.dumps(server_context.song_queue), "UTF-8")
