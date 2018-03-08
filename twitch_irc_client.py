import asyncio
import threading
import socket

class TwitchIRCClient:
    def __init__(self, protocol, address, error_callback):
        self.address=address
        self.loop = asyncio.new_event_loop()
        self.protocol = protocol
        self.protocol.attach_loop(self.loop)
        self.error_callback=error_callback

    def f(self, loop, coro):
        try:
            asyncio.set_event_loop(loop)
            loop.run_until_complete(coro)
            loop.run_forever()
        except socket.gaierror as ex:
            print("TwitchIRCClient.f: {}".format(ex))
            self.error_callback(ex)
        except OSError as ex:
            print("TwitchIRCClient.f: {}".format(ex))
            self.error_callback(ex)
        except RuntimeError as ex:
            print("TwitchIRCClient.f: {}".format(ex))
            self.error_callback(ex)

        print('TwitchIRCClient.f: loop stopped')

    def connect(self):
        coro = self.loop.create_connection(lambda: self.protocol, *self.address)

        t = threading.Thread(target=self.f, args=(self.loop, coro))
        t.start()