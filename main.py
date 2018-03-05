import argparse
from twitch_irc_client import TwitchIRCClient
from protocol import Protocol
from twitch_bot import TwitchBot
from irc import IRC
from commands.test_cmd import TestCmd
import time

if __name__=='__main__':
    parser = argparse.ArgumentParser('Twitch IRC client')
    parser.add_argument('oauth', help='Oauth token')
    parser.add_argument('username', help='twitch username')
    parser.add_argument('channel', help='twitch channel')
    parser.add_argument('-ip', type=str, default='irc.chat.twitch.tv', help='IP of twitch IRC server')
    parser.add_argument('-port', type=int, default=6667, help='Port of twitch IRC server (default 1060)')
    args = parser.parse_args()

    address = (args.ip, args.port)

    irc = IRC()
    bot = TwitchBot(address, args.oauth, args.username, args.channel)

    test_cmd = TestCmd()
    bot.set_commands([test_cmd])

    bot.events.disconnected=lambda: print('Event: disconnected')
    bot.events.connected = lambda: print('Event: connected')
    bot.events.joined = lambda x: print('Event: {} joined'.format(x))
    bot.events.parted = lambda x: print('Event: {} parted'.format(x))
    bot.events.message_received = lambda x: print('Event: message {} received from {}'.format(x.message, x.username))

    try:
        bot.start()
    except OSError as e:
        print('main.py OSError: {}'.format(e))
