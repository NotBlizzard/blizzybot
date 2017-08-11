
class Hello:
    match_line = r'hello, blizzybot'

    def __repr__(self):
        return "<Plugin:Hello>"

    def run(self, message, last_message):
        return "Hello, {}".format(message[3])
