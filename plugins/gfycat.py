import json
import requests

class Gfycat:
    match_line = r'(.+).gif'

    def __repr__(self):
        return "<Plugin:Gfycat>"

    def run(self, message, last_message):
        url = [x for x in message[4].split(" ") if ".gif" in x][0]
        gfycat_url = "https://upload.gfycat.com/transcode?fetchUrl={}".format(url)
        data = requests.get(gfycat_url)
        return "Gfycat version: https://gfycat.com/{}".format(data.json()["gfyname"])
