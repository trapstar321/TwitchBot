import asyncio

class Protocol(asyncio.Protocol):
    def __init__(self, coder, bot):
        self.incomplete_msg = None
        self.coder = coder
        self.bot = bot

    def attach_loop(self, loop):
        self.loop=loop

    #login to server when connection is made
    def connection_made(self, transport):
        self.bot.connected(transport)

    def _get_messages(self, data):
        if self.incomplete_msg:
            data+=self.incomplete_msg
            self.incomplete_msg=None

        datastr = self.coder.decode(data)

        messages = datastr.split('\r\n')

        if messages[-1]!='':
            self.incomplete_msg = messages[-1]
            print('Protocol._get_messages: incomplete message received: {}'.format(self.incomplete_msg))

        messages = messages[0:-1]
        return messages

    def data_received(self, data):
        messages = self._get_messages(data)
        print('Protocol.data_received: received: {!r}'.format(self.coder.decode(data)))
        print('Protocol.data_received: received {} messages => {}'.format(len(messages), messages))

        self.bot.process(messages)

    def connection_lost(self, exc):
        print('Protocol.connection_lost: the server closed the connection')
        self.loop.stop()
        self.bot.disconnected()