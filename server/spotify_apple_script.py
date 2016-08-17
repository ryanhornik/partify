from subprocess import check_output


def execute_spotify_command(cmd):
    script = 'tell application "Spotify" to {}'.format(cmd)
    command = ['osascript', '-e', script]
    return check_output(command)


def pause_song():
    execute_spotify_command('pause')


def resume_song():
    execute_spotify_command('play')
