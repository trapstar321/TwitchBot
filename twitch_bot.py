from protocol import Protocol
from twitch_irc_client import TwitchIRCClient
from irc import IRC
from events import Events
from twitch_message import TwitchMessage
from threading import Thread, Lock
import datetime
import time
from utils import extract_username, extract_message, parse_command

class TwitchBotException(Exception):
    pass

class TwitchBot:
    _delay=30
    _limit=100
    _sleep = 0.3

    def twitch_irc_cap_cmd(self):
        return 'CAP REQ :twitch.tv/tags\r\nCAP REQ :twitch.tv/membership\r\nCAP REQ :twitch.tv/commands\r\n'

    def __init__(self, address, oauth, username, channel):
        self.irc=IRC()
        self.oauth = oauth
        self.username = username
        self.channel = channel
        self.address = address
        self.events=Events()

        self.users = []
        self.commands=[]
        self.messages = []
        self.l = Lock()
        self.is_connected = False
        self.messages_sent = 0
        self.last_sent = datetime.datetime.now()

        self.protocol = Protocol(self.irc, self)
        self.client = TwitchIRCClient(self.protocol, self.address, self.on_socket_error)
        self.transport=None

    def process_messages(self):
        while True:
            if not self.is_connected:
                print("TwitchBot.process_messages: not connected, exit thread")
                return

            now = datetime.datetime.now()

            if (now - self.last_sent).seconds > self._delay:
                #print('TwitchBot.process_messages: reset check')
                self.messages_sent = 0
                self.last_sent = datetime.datetime.now()

            if self.messages_sent == self._limit:
                #print('TwitchBot.process_messages: limit reached')
                time.sleep(self._sleep)
                continue

            self.l.acquire()
            to_send = self.messages[0:self._limit - self.messages_sent]
            self.messages = self.messages[len(to_send):]
            self.l.release()

            if len(to_send) > 0:
                #print('TwitchBot.process_messages: send {} messages'.format(len(to_send)))

                data = ''
                for msg in to_send:
                    data+=msg

                print('TwitchBot.process_messages: to send={!r}'.format(data))

                self.transport.write(self.irc.encode(data))
                self.messages_sent += len(to_send)

            time.sleep(self._sleep)

    def set_commands(self, commands):
        self.commands=commands

    def start(self):
        self.client.connect()

    def stop(self):
        #force socket close if we have a open socket
        if not self.transport is None:
            try:
                self.transport._sock.close()
            except Exception as ex:
                print('TwitchBot.stop: {}'.format(ex))
        #force loop stop
        else:
            print('TwitchBot.stop: stop loop')
            self.protocol.loop.stop()

    # TODO Check is_connected flag so we know if we were attempting to connect and raise socket_error event
    def on_socket_error(self, exc):
        print('TwitchBot.on_socket_error: {}'.format(exc))
        self.events.socket_error(exc, self.is_connected)

    def disconnected(self):
        self.transport=None
        self.is_connected = False
        self.events.disconnected()
        print('TwitchBot.disconnected')

    def connected(self, transport):
        self.write_thread = Thread(target=self.process_messages)
        self.is_connected = True
        self.events.connected()

        self.transport = transport
        self.write_thread.start()

        cmd = self.irc.login_cmd(self.oauth, self.username)
        self.write(cmd)

    def write(self, message):
        self.l.acquire()
        self.messages.extend(message.splitlines(True))
        self.l.release()

    def joined(self, username):
        self.events.joined(username)
        print('TwitchBot.joined: {}'.format(username))
        self.users.append(username)

    def parted(self, username):
        self.events.parted(username)
        print('TwitchBot.parted: {}'.format(username))
        self.users.remove(username)

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
                    print('TwitchBot.process: received message with code 376. Proceed to join {} channel'.format(self.channel))
                    cmd = self.twitch_irc_cap_cmd()
                    self.write(cmd)
                    cmd = self.irc.join_cmd(self.channel)
                    self.write(cmd)
                elif parts[0]=='PING':
                    cmd = self.irc.pong_cmd(message)
                    self.write(cmd)
                elif parts[1]=='JOIN':
                    self.joined(extract_username(parts[0]))
                elif parts[1]=='PART':
                    self.parted(extract_username(parts[0]))
                elif 'PRIVMSG' in message:
                    username = extract_username(parts[1])
                    message = extract_message(parts)
                    self.events.message_received(TwitchMessage(username,message))

                    if message[0]=='!':
                        cmd, args = parse_command(message)

                        print('TwitchBot.process: find command {}'.format(cmd))
                        print('TwitchBot.process: args = {}'.format(args))

                        commands = list(filter(lambda x: x.cmd==cmd, self.commands))

                        if len(commands)>0:
                            command = commands[0]
                            print('TwitchBot.process: execute command {}'.format(cmd))
                            try:
                                output = command.execute(self, username, args)
                                print('TwitchBot.process: command output = {}'.format(output))
                                self.write(self.irc.sendmsg_cmd(self.channel, output))
                            except Exception as e:
                                print('TwitchBot.process: Error while executing command {}'.format(cmd))
                                print('TwitchBot.process: Exception: {}'.format(e))

                        else:
                            print('TwitchBot.process: command {} does not exist'.format(cmd))
            except IndexError as e:
                print('TwitchBot.process: IndexError: {}'.format(e))
            except ValueError as e:
                print('TwitchBot.process: ValueError: {}'.format(e))