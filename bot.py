# bot.py

# TODO:
# organize imports
# organize

from websocket import create_connection
from threading import Thread
from battle import Battle
import commands
import traceback
import requests
import inspect
import json
from fractions import Fraction
import random
import time
import sys
import re
import os
from learn import Learn

class Bot:
    pokedex = json.loads(open(os.path.join(os.path.dirname(__file__), "./data/pokedex.json"), "r").read())
    pokemon_teams = json.loads(open(os.path.join(os.path.dirname(__file__), "./data/pokemon_teams.json"), "r").read())

    def __init__(self, username, password, server, admins, rooms, symbol, avatar, plugins, log):
        self.start_time = float(time.time())
        self.commands = []
        self.last_message = {}
        self.i = 0
        self.url = "http://play.pokemonshowdown.com/action.php"
        self.room = ""
        self.username = username
        self.password = password
        self.joined_all_rooms = False
        self.avatar = avatar
        self.server = server
        self.admins = admins
        self.rooms = rooms
        self.symbol = symbol
        self.battles = []
        self.plugins = plugins
        self.rooms_joined = []
        self.log = log
        self.tiers = ["randombattle", "ou", "ubers", "uu", "ru", "nu", "pu", "lc", "anythinggoes", "battlespotsingles"]

    def __str__(self):
        return "<Bot:{}>".format(self.username)


    def join(self, room):
        self.ws.send("|/join {}".format(room))

    def current_battle(self):
        return [i for i in self.battles if i.room == self.room][0]

    def battle(self, message):
        message[1] = re.sub(r'[^A-z0-9]', '', message[1])
        if message[1] == "turn" or message[1] == "start":
            getattr(self.current_battle()[self.room], "decide")()
        else:
            getattr(self.current_battle()[self.room], message[1])(message)

    def plugin(self, room, plugin, message):
        self.ws.send("{}|{}".format(room, plugin.run(message, self.last_message[self.room])))

    def command(self, message, room, user):
        cmd = message[4].split(self.symbol)[1].split(" ")[0]
        try:
            if " " in message[4]:
                args = message[4].split("{} ".format(cmd))[1]
            else:
                args = []

            command = getattr(commands, "command_{}".format(cmd), __name__)(args, room.strip().lower(), user.lower(), self)
            self.ws.send("{}|{}".format(room, command))
        except (IndexError, TypeError):
            print(traceback.print_exc())
            self.ws.send("{}|Luffy: so it's a mystery command! (\"{}\" is not recognized)".format(room, cmd))
        except:
            print(traceback.print_exc())
            self.ws.send("{}|Something went wrong.".format(room))

    def login(self, message):
        key = message[2]
        challenge = message[3]

        if self.password == "":
            data = { "act": "getassertion", "userid": self.username, "challengekeyid": key, "challenge": challenge }
            data = requests.get(self.url, data=data)
            self.ws.send("|/trn {},0,{}".format(self.username, data.text))
        else:
            data = { "act": "login", "name": self.username, "pass": self.password, "challengekeyid": key, "challenge": challenge }
            data = requests.post(self.url, data=data)
            data = json.loads(data.text.split("]")[1])
            self.ws.send("|/trn {},0,{}".format(self.username, data["assertion"]))

    def disconnect(self):
        self.ws = None
        sys.exit()

    def start(self):
        try:
            self.connect()
        except SystemExit:
            return sys.exit()


    def message(self, messages):
        timestamp = int(messages[2])
        user = messages[3]
        print(self.room)
        print(self.rooms_joined)
        match_line = [x for x in self.plugins if re.match(x.match_line, messages[4], flags=re.IGNORECASE)]
        if len(match_line) > 0 and self.room in self.rooms_joined:
            plugin = [x for x in self.plugins if x == match_line[0]][0]
            if self.room == "lobby":
                self.room = ""

            self.commands.append(Thread(target=self.plugin, args=(self.room, plugin, messages)).start())

        if self.room in self.rooms_joined and messages[4][0] == self.symbol:
            if self.room == "lobby":
                self.room = ""

            self.commands.append(Thread(target=self.command, args=(messages, self.room, user)).start())

    def battle_message(self, messages):
        user = re.sub(r'[^A-z0-9]', '', messages[2])
        if messages[3][0] == self.symbol:
            messages = [""] + messages # now the list has five elements.
            self.commands.append(Thread(target=self.command, args=(messages, self.room, " " + user)).start())

    def raw(self, messages):
        if self.rooms[self.i] not in self.rooms_joined and "infobox" in messages[2]:
            if self.rooms[self.i] == "lobby":
                self.rooms[self.i] = ""

            self.rooms_joined.append(self.rooms[self.i])
            if len(self.rooms) > self.i + 1:
                self.i += 1


    def update(self):
        [self.join(room) for room in self.rooms]

    def request(self, messages):

        data = [x for x in self.battles if self.room in str(x)]
        battle_tier = re.search("battle-(.+)-(\d+)", self.room).group(1)
        if len(data) == 0: # new battle
            self.battles.append(Battle(battle_tier, self.room, self))
            print("NEW BATTLE")
            self.battles[-1].run(messages)
        else:
            pass

    def update_battle(self, messages):
        data = json.loads(messages[2])
        if len(data["challengesFrom"].keys()) > 0:
            who = list(data["challengesFrom"].keys())[0]
            tier = data["challengesFrom"][who]
            if tier in self.tiers:
                if "random" not in tier:
                    team = Bot.pokemon_teams[tier][random.choice(list(Bot.pokemon_teams[tier].keys()))]
                    self.ws.send("|/utm {}".format(team))

                self.ws.send("|/accept {}".format(who))

    def connect(self):
        self.ws = create_connection("ws://{}/showdown/websocket".format(self.server))

        while True:

            messages = [x for x in self.ws.recv().split("\n")]


            for message in messages:
                print("it is ")
                print(self.rooms_joined)
                if self.log:
                    print(message.encode("utf-8", "ignore"))

                try:
                    if ">" in self.last_message:
                        self.room = message[1:]
                except:
                    self.room = "" # lobby


                message = message.split("|")

                # battles
                if self.room in [x.room for x in self.battles] and len(message) > 1:
                    battle = [i for i in self.battles if i.room == self.room][0]
                    battle.run(message)


                if len(message) > 1:
                    if message[1] == "c:":
                        self.message(message)
                        self.last_message[self.room] = message

                    elif message[1] == "title":
                        room = re.sub(r' ', '', message[2].lower())
                        self.rooms_joined.append(room)

                    elif message[1] == "raw":
                        self.raw(message)

                    elif message[1] == "c":
                        self.battle_message(message)

                    elif message[1] == "challstr":
                        self.login(message)


                    elif message[1] == "updateuser":
                        if not self.joined_all_rooms:
                            for room in self.rooms:
                                self.join(room)

                            self.joined_all_rooms = True

                    elif message[1] == "request":
                        self.request(message)

                    elif message[1] == "updatechallenges":
                        self.update_battle(message)
                    else:
                        pass
