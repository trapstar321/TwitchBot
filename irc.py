#IRC commands
class IRC:
    encoding='utf-8'

    def login_cmd(self, oauth_token,username):
        return 'PASS oauth:{}\r\nNICK {}\r\n'.format(oauth_token, username)

    def join_cmd(self,channel):
        return 'JOIN #{}\r\n'.format(channel)

    def sendmsg_cmd(self, channel, message):
        return 'PRIVMSG #{} :{}\r\n'.format(channel, message)

    def pong_cmd(self, original):
        return 'PONG {}'.format(original.split(' ')[1])

    def encode(self, message):
        return message.encode(self.encoding)

    def decode(self, message):
        return message.decode(self.encoding)

