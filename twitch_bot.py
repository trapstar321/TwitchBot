from protocol import Protocol
from twitch_irc_client import TwitchIRCClient
from irc import IRC
from events import Events
from twitch_message import TwitchMessage

class TwitchBotException(Exception):
    pass

class TwitchBot:
    users=[]
    commands=[]

    def twitch_irc_cap_cmd(self):
        return 'CAP REQ :twitch.tv/tags\r\nCAP REQ :twitch.tv/membership\r\nCAP REQ :twitch.tv/commands\r\n'

    def __init__(self, address, oauth, username, channel):
        self.irc=IRC()
        self.oauth = oauth
        self.username = username
        self.channel = channel
        self.address = address
        self.events=Events()

    def set_commands(self, commands):
        self.commands=commands

    def start(self):
        self.protocol = Protocol(self.irc, self)

        self.client = TwitchIRCClient(self.protocol, self.address)
        self.client.connect()

    def reconnect(self):
        self.client.connect()

    def disconnected(self):
        self.events.disconnected()
        print('TwitchBot.disconnected')

    def connected(self, transport):
        self.events.connected()
        self.transport=transport
        cmd = self.irc.login_cmd(self.oauth, self.username)
        self.write(cmd)

    def write(self, cmd):
        self.transport.write(self.irc.encode(cmd))
        print('TwitchBot.write: sent {!r}'.format(cmd))

    def joined(self, username):
        self.events.joined(username)
        print('TwitchBot.joined: {}'.format(username))
        self.users.append(username)

    def parted(self, username):
        self.events.parted(username)
        print('TwitchBot.parted: {}'.format(username))
        self.users.remove(username)

    def extract_username(self, username):
        return username[1:] if username[0] == ':' else username

    def extract_message(self, parts):
        message = ' '.join(parts[4:])
        return message[1:] if message[0] == ':' else message

    def parse_command(self, message):
        parts = message.split(' ')
        cmd = parts[0][1:]
        args = parts[1:]
        return (cmd, args)

    def process(self, messages):
        for message in messages:
            try:
                parts = message.split(' ')
                #login successfull
                if parts[1]=='NOTICE' and ('Login authentication failed' in message):
                    print('TwitchBot.process: Failed to authenticate')
                    self.transport.close()
                    raise TwitchBotException('Failed to authenticate')
                if parts[1]=='376':
                    self.events.joined_channel(self.channel)
                    print('TwitchBot.process: received message with code 376. Proceed to join {} channel'.format(self.channel))
                    cmd = self.twitch_irc_cap_cmd()
                    self.write(cmd)
                    cmd = self.irc.join_cmd(self.channel)
                    self.write(cmd)
                elif parts[0]=='PING':
                    cmd = self.irc.pong_cmd(message)
                    self.write(cmd)
                elif parts[1]=='JOIN':
                    self.joined(self.extract_username(parts[0]))
                elif parts[1]=='PART':
                    self.parted(self.extract_username(parts[0]))
                elif 'PRIVMSG' in message:
                    username = self.extract_username(parts[1])
                    message = self.extract_message(parts)
                    self.events.message_received(TwitchMessage(username,message))

                    if message[0]=='!':
                        cmd, args = self.parse_command(message)

                        print('TwitchBot.process: find command {}'.format(cmd))
                        print('TwitchBot.process: args = {}'.format(args))

                        commands = list(filter(lambda x: x.cmd==cmd, self.commands))

                        if len(commands)>0:
                            command = commands[0]
                            print('TwitchBot.process: execute command {}'.format(cmd))
                            output = command.execute(self, username, args)
                            print('TwitchBot.process: command output = {}'.format(output))
                            self.write(self.irc.sendmsg_cmd(self.channel, output))
                        else:
                            print('TwitchBot.process: command {} does not exist'.format(cmd))
            except IndexError as e:
                print('TwitchBot.process: IndexError: {}'.format(e))
            except ValueError as e:
                print('TwitchBot.process: ValueError: {}'.format(e))