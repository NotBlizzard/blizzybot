class What:
    match_line = r'what|wat'

    def __repr__(self):
        return "<Plugin:What>"

    def run(self, message, last_message):
        print(last_message)
        return "**{}**".format(last_message[4].upper())
