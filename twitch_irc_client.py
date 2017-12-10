import asyncio
import threading
import socket

class TwitchIRCClient:
    def __init__(self, protocol, address):
        self.address=address
        self.loop = asyncio.new_event_loop()
        self.protocol = protocol
        self.protocol.attach_loop(self.loop)

    def f(self, loop, coro):
        asyncio.set_event_loop(loop)
        loop.run_until_complete(coro)
        loop.run_forever()

    def connect(self):
        coro = self.loop.create_connection(lambda: self.protocol, *self.address)

        t = threading.Thread(target=self.f, args=(self.loop, coro))
        t.start()