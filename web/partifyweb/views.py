from django.shortcuts import render
import spotipy
import socket


# Create your views here.
def do_command(data):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('localhost', 7674))
        s.sendall(data)
        return s.recv(1024).decode()


def now_playing(request):
    client = spotipy.Spotify()
    song_uri = do_command(b'c')
    song = client.track(song_uri)
    song['artist_names'] = list(map(lambda a: a['name'], song['artists']))
    return render(request, 'now_playing.html', {'track': song})
