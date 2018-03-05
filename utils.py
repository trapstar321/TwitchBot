def extract_username(username):
    u = username[1:] if username[0] == ':' else username
    return u.split('!')[0] if '!' in u else u

def extract_message(parts):
    message = ' '.join(parts[4:])
    return message[1:] if message[0] == ':' else message

def parse_command(message):
    parts = message.split(' ')
    cmd = parts[0][1:]
    args = parts[1:]
    return (cmd, args)