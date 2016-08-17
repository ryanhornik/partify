class Command(object):
    command_map = {}

    def __init__(self, aliases, data, argument_usage, description, required_arguments=0):
        self.aliases = aliases
        self.data = data
        self.usage = "{}|{} {}".format(data, '|'.join(aliases), argument_usage)
        self.description = description
        self.required_arguments = required_arguments
        self.full_description = "{}\n\t{}".format(self.usage, self.description)

    def format_with_args(self, argv):
        if len(argv) < 2 + self.required_arguments:
            return None

        data = self.data
        if len(argv) > 2:
            data = data + ' ' + ' '.join(argv[2:])
        return data

    @staticmethod
    def register(command):
        for alias in command.aliases:
            assert alias not in Command.command_map
            Command.command_map[alias] = command
        assert command.data not in Command.command_map
        Command.command_map[command.data] = command

    @staticmethod
    def register_new(aliases, data, argument_usage, description, required_arguments=0):
        Command.register(Command(aliases, data, argument_usage, description, required_arguments))

    @staticmethod
    def show_general_usage():
        print('TODO fill in this usage')

    @staticmethod
    def send_command(argv, server):
        if len(argv) < 2:
            Command.show_general_usage()
            return

        command_text = argv[1].lower()

        command = Command.command_map.get(command_text, None)
        if not command:
            Command.show_general_usage()
            return

        data = command.format_with_args(argv)
        if not data:
            Command.show_general_usage()
            return

        server.sendall(bytes(data, 'UTF-8'))
        return server.recv(1024).decode()

Command.register_new(aliases=('play', 'pause', 'playpause'),
                     data='p',
                     argument_usage='',
                     description='If playback is paused resumes playback. Otherwise pauses playback.')

Command.register_new(aliases=('next', 'skip'),
                     data='n',
                     argument_usage='',
                     description='Skips to the next song in the queue.')

Command.register_new(aliases=('add', 'enqueue', 'e'),
                     data='a',
                     argument_usage='<track id>',
                     description='Adds the track specified by <track id> to the end of the play queue.',
                     required_arguments=1)

Command.register_new(aliases=('quit', 'exit', 'x'),
                     data='q',
                     argument_usage='',
                     description='Stops the server and ends playback.')

Command.register_new(aliases=('get', 'queue'),
                     data='g',
                     argument_usage='',
                     description='Retrieves the current contents of the queue')
