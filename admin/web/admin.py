'''
The MIT License (MIT)
Copyright (c) 2013 Dave P.
'''

import signal
import sys
import ssl
from SimpleWebSocketServer import WebSocket, SimpleWebSocketServer, SimpleSSLWebSocketServer
from optparse import OptionParser

from twitch_bot import TwitchBot
from irc import IRC
from commands.test_cmd import TestCmd

import json

class Admin(WebSocket):
   clients = []
   bot = None

   def notifyClient(self, command, data, description, status):
      response = json.dumps({
            'command':command,
            'description':description,
            'data':data,
            'status':status
         })

      print('Response: {}'.format(response))
      self.sendMessage(response)

   def handleMessage(self):
      data = json.loads(self.data)
      print("Request: {}".format(data))

      #store clients token for permission check in db
      if data['command']=='TOKEN':
         self.token=data['token']
      elif data['command']=='START':
         if not self.can_start_bot():
            self.notifyClient(data['command'], '', self.bot_status(), 'WARNING')
            return
         try:
            self.start_bot(
               data['ip'],
               data['port'],
               data['oauth_token'],
               data['username'],
               data['channel']
            )
         except OSError as e:
            print('admin.py OSError: {}'.format(e))
            self.notifyClient(data['command'], '', str(e), 'ERROR')
         except Exception as e:
            print('admin.py Exception: {}'.format(e))
            self.notifyClient(data['command'], '', str(e), 'ERROR')
         else:
            self.notifyClient(data['command'], '', self.bot_status(), 'SUCCESS')
      elif data['command']=='SHUTDOWN':
         if self.can_shutdown_bot():
            Admin.bot.stop()
         else:
            self.notifyClient(data['command'], '', self.bot_status(), 'WARNING')
      else:
         self.notifyClient(data['command'], '', "Unknown command {}".format(data['command']), 'WARNING')

   def can_start_bot(self):
      return True if Admin.bot is None or not Admin.bot.protocol.loop.is_running() else False

   def can_shutdown_bot(self):
      return True if Admin.bot is None or Admin.bot.protocol.loop.is_running() else False

   def handleConnected(self):
      Admin.clients.append(self)
      print(self.address, 'connected')

      self.notifyBotStatus()

   def bot_status(self):
      return 'Twitch bot {} and {}'.format(
         'running' if Admin.bot.protocol.loop.is_running() else 'not running',
         'connected' if Admin.bot.is_connected else 'not connected'
      )

   def notifyBotStatus(self):
      if Admin.bot is not None:
         self.notifyClient('BOT_STATUS', '',
                           self.bot_status(),
                           'SUCCESS' if Admin.bot.protocol.loop.is_running and Admin.bot.is_connected else 'WARNING')
      else:
         self.notifyClient('BOT_STATUS', '', 'Twitch bot not running and not connected', 'WARNING')

   def notifyBotStatusExc(self, exc):
      self.notifyClient('BOT_STATUS', str(exc),
                        self.bot_status(),
                        'SUCCESS' if Admin.bot.protocol.loop.is_running and Admin.bot.is_connected else 'WARNING')


   def handleClose(self):
      Admin.clients.remove(self)

      if(Admin.bot is not None and len(Admin.clients)==0):
         print('Last client disconnected. Stop twitch bot')
         Admin.bot.stop()

   def bot_connected(self):
      for client in Admin.clients:
         client.notifyBotStatus()

   def bot_disconnected(self):
      for client in Admin.clients:
         client.notifyBotStatus()

   def bot_socket_error(self, exc, is_connected):
      for client in Admin.clients:
         client.notifyBotStatusExc(exc)

   def bot_user_joined(self, username):
      self.notifyClient("JOINED", username, "User {} joined".format(username), "")

   def start_bot(self,ip, port, oauth, username, channel):
      irc = IRC()
      Admin.bot = TwitchBot((ip, port), oauth, username, channel)

      test_cmd = TestCmd()
      Admin.bot.set_commands([test_cmd])

      Admin.bot.events.disconnected = self.bot_disconnected
      Admin.bot.events.connected = self.bot_connected
      Admin.bot.events.joined = lambda x: self.bot_user_joined(x)
      Admin.bot.events.parted = lambda x: print('Event: {} parted'.format(x))
      Admin.bot.events.message_received = lambda x: print('Event: message {} received from {}'.format(x.message, x.username))
      Admin.bot.events.socket_error = lambda exc, is_connected: self.bot_socket_error(exc, is_connected)

      Admin.bot.start()

if __name__ == "__main__":
   import os, django
   import sys

   sys.path.append(os.path.abspath('web'))

   # set the specific django settings file
   os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.settings")
   django.setup()

   from django.contrib.auth.models import User,Permission
   from app.models import Token

   #print(User.objects.all())

   parser = OptionParser(usage="usage: %prog [options]", version="%prog 1.0")
   parser.add_option("--host", default='', type='string', action="store", dest="host", help="hostname (localhost)")
   parser.add_option("--port", default=8001, type='int', action="store", dest="port", help="port (8000)")
   parser.add_option("--ssl", default=0, type='int', action="store", dest="ssl", help="ssl (1: on, 0: off (default))")
   parser.add_option("--cert", default='./cert.pem', type='string', action="store", dest="cert", help="cert (./cert.pem)")
   parser.add_option("--key", default='./key.pem', type='string', action="store", dest="key", help="key (./key.pem)")
   parser.add_option("--ver", default=ssl.PROTOCOL_TLSv1, type=int, action="store", dest="ver", help="ssl version")

   (options, args) = parser.parse_args()
   cls = Admin

   if options.ssl == 1:
      server = SimpleSSLWebSocketServer(options.host, options.port, cls, options.cert, options.key, version=options.ver)
   else:
      server = SimpleWebSocketServer(options.host, options.port, cls)

   def close_sig_handler(signal, frame):
      server.close()
      sys.exit()

   signal.signal(signal.SIGINT, close_sig_handler)

   server.serveforever()