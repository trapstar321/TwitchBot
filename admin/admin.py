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

def start_bot(ip, port, oauth, username, channel):
   irc = IRC()
   bot = TwitchBot((ip,port), oauth, username, channel)

   test_cmd = TestCmd()
   bot.set_commands([test_cmd])

   bot.events.disconnected = lambda: print('Event: disconnected')
   bot.events.connected = lambda: print('Event: connected')
   bot.events.joined = lambda x: print('Event: {} joined'.format(x))
   bot.events.parted = lambda x: print('Event: {} parted'.format(x))
   bot.events.message_received = lambda x: print('Event: message {} received from {}'.format(x.message, x.username))

   bot.start()

class Admin(WebSocket):
   def notifyClient(self, command, data, status):
      response = json.dumps({
            'command':command,
            'data':data,
            'status':status
         })

      print('Response: {}'.format(response))
      self.sendMessage(response)

   def handleMessage(self):
      data = json.loads(self.data)
      print("Request: {}".format(data))

      try:
         s = ""
         #start_bot(
         #   data['ip'],
         #   data['port'],
         #   data['oauth_token'],
         #   data['username'],
         #   data['channel']
         #)
      except OSError as e:
         print('admin.py OSError: {}'.format(e))
         self.notifyClient(data['command'], str(e), 'ERROR')
      except Exception as e:
         print('admin.py Exception: {}'.format(e))
         self.notifyClient(data['command'],str(e), 'ERROR')
      else:
         self.notifyClient(data['command'], "Twitch bot running", 'SUCCESS')


   def handleConnected(self):
      print(self.address, 'connected')

   def handleClose(self):
      pass

if __name__ == "__main__":

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