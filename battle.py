from fractions import Fraction
from statistics import median
from learn import Learn

import random
import json
import sys
import re
import os

import requests


# TODO:
# Allow Pokemon to use moves like Sleep Powder, Toxic, etc.
# Allow Pokemon to use moves like Recovery, etc.
# Allow other tiers (at the moment this only works for tiers like OU, UU, RU, Ubers, etc.)
# Update to work with Generation 7 (Sun and Moon)

class Battle:
    pokedex = json.loads(open(os.path.join(os.path.dirname(__file__), "./data/pokedex.json"), "r").read())
    pokedex_moves = json.loads(open(os.path.join(os.path.dirname(__file__), "./data/pokedex_moves.json"), "r").read())
    pokedex_effectiveness = json.loads(open(os.path.join(os.path.dirname(__file__), "./data/pokedex_effectiveness.json"), "r").read())
    teams_for_battle = json.loads(open(os.path.join(os.path.dirname(__file__), "./data/pokemon_teams.json"), "r").read())
    moves_that_switch = ["uturn", "voltswitch"]
    status_moves = [{"name":"spore", "type":"grass","effect":"sleep"}]
    status_moves_names = ["spore"]

    def __init__(self, tier, room, bot):
        self.learn = Learn(room)
        self.opponent = {}
        self.generation = "generation 6"
        self.bot = bot
        self.weather = ""
        self.statuses = []
        self.opponent_pokemon_team = []
        self.do_not_switch = False
        self.ws = self.bot.ws
        self.team = None
        self.strongest_move = ""
        self.active = ""
        self.id = ""
        self.tier = tier
        self.room = room
        self.turn = 0


    def __repr__(self):
        return "<Battle: room:{}>".format(self.room)

    def __str__(self):
        return "<Battle: room:{}>".format(self.room)

    def run(self, messages):
        try:
            if messages[1] == "turn":
                return getattr(self, "decide")()
            else:
                return getattr(self, re.sub(r'[^A-z0-9]', '', messages[1]))(messages)
        except (TypeError, AttributeError):
            pass

    def start(self, message):
        self.ws.send("{}|Good Luck, Have Fun".format(self.room))
        self.ws.send("{}|/timer")

    def turn(self, message):
        self.decide()

    def weather(self, message):
        self.weather = message[2].lower()
        # cheesy lines
        if self.weather == "hail":
            self.ws.send("{}|Oh, it's hailing. It's ok though, because the cold never bothered me anyway.".format(self.room))
        elif self.weather == "sandstorm":
            pokemon = message[4].split(": ")[1].lower()
            self.ws.send("{}|Darude Sandstorm?".format(self.room, pokemon))
        elif self.weather == "raindance":
            self.ws.send("{}|Shouldn't it be raining men now?".format(self.room))
        else:
            pass

    def move(self, message):
        if self.id == "p1":
            _id = "p2a"
        else:
            _id = "p1a"

        if _id in message[2]:
            move = message[3].replace("-", "").replace(" ", "").lower()
            self.learn.write(self.opponent["name"], move)


    def update_pokemon_move(self, move, pokemon):
        pokemon_move = {}
        if "hiddenpower" in move:
            pokemon_move["name"] = move[:-2]
            pokemon_move["power"] = 60
            pokemon_move["type"] = move.split("hiddenpower")[1][:-2]
        else:
            pokemon_move["name"] = move
            pokemon_move["power"] = self.pokedex_moves[move]["power"]
            pokemon_move["type"] = self.pokedex_moves[move]["type"]

            if move == "return":
                pokemon_move["power"] = 102

            if move in ["eruption", "waterspout"]:
                pokemon_move["power"] = 150 * float(pokemon["hp"])

        return pokemon_move



    def update_pokemon_team(self, pokemon_team):
        json_data = json.loads(pokemon_team)["side"]["pokemon"]
        team = []
        i = 0
        for pokemon in json_data:
            pkmn = {}
            pkmn["id"] = i + 1
            pkmn["name"] = re.sub(r'[^A-z0-9]', '', json_data[i]["ident"].split(": ")[1]).lower()
            pkmn["moves"] = json_data[i]["moves"]
            pkmn["stats"] = json_data[i]["stats"]
            pkmn["active"] = json_data[i]["active"]
            pkmn["ability"] = json_data[i]["baseAbility"]
            pkmn["type"] = [x.lower() for x in self.pokedex[pkmn["name"]]["types"]]
            pkmn["hp"] = json_data[i]["condition"]
            if " " in pkmn["hp"]: # condition
                pkmn["status"] = pkmn["hp"].split(" ")[1]
                pkmn["hp"] = pkmn["hp"].split(" ")[0]

            if "/" in pkmn["hp"]: # fraction
                pkmn["hp"] = float(Fraction(int(pkmn["hp"].split("/")[0]), int(pkmn["hp"].split("/")[1])))

            team.append(pkmn)
            i += 1

        self.team = team
        return team

    def teampreview(self, message = None):
        self.ws.send("{}|/team {}|1".format(self.room, random.randint(1, 6)))

    def player(self, message):
        if len(message) > 2:
            if self.bot.username == message[3]:
                self.id = message[2]
            else:
                if message[2] == "p1":
                    self.id = "p2"
                else:
                    self.id = "p1"

    def request(self, message):
        self.team = self.update_pokemon_team(message[2])
        self.id = json.loads(message[2])["side"]["id"]
        if "random" in self.tier:
            self.teampreview()

    def faint(self, message):
        if self.id in message[2]:
            pokemon = message[2].split(": ")[1].lower()
            if len([x for x in self.team if x["name"] == pokemon]) > 0:
                self.active["hp"] = 0
                self.switch_pokemon()


    def switch(self, message):
        if self.id == "p1":
            _id = "2a"
        else:
            _id = "1a"
        if _id in message[2]:
            opponent = re.sub(r'[^A-z0-9]', '', message[3].split(",")[0]).lower()
            print("opponent is "+opponent)
            self.opponent["hp"] = float(Fraction(int(message[4].split("/")[0]), int(message[4].split("/")[1])))
            self.opponent["name"] = opponent
            self.do_not_switch = False



    def win(self, message):
        self.ws.send("{}|Good Game.".format(self.room))
        self.ws.send("{}|/part".format(self.room))

    def damage(self, message):
        pokemon = message[2].split(": ")[1].lower()
        if pokemon == self.opponent["name"] and "/" in message[3] and " " not in message[3]:
            self.opponent["hp"] = float(Fraction(int(message[3].split("/")[0]), int(message[3].split("/")[1])))

    def lose(self, message):
        self.win(message)

    def tie(self, message):
        self.win(message)

    def moves_power(self, pokemon = None):

        pokemon_moves = []
        if pokemon is None:
            pokemon = self.active
            moves = self.active["moves"]
        else:
            moves = pokemon["moves"]
            pokemon = pokemon

        for move in moves:


            move = self.update_pokemon_move(move, pokemon)

            move["power"] = self.ability_of_pokemon_modifies_power_of_pokemon_move(pokemon, move)


            if "multihit" in list(self.pokedex_moves[move["name"]].keys()):
                move["power"] *= median(self.pokedex_moves[move["name"]]["multihit"])

            pokemon_moves.append(move)

        moves_power = []
        for move in pokemon_moves:
            modifier = self.pokemon_move_modifier(pokemon, move)

            moves_power.append({"name": move["name"], "power": move["power"] * modifier, "pokemon": pokemon["name"]})

        return moves_power

    def pokemon_move_modifier(self, pokemon, pokemon_move):
        modifier = 1
        if pokemon_move["type"] in pokemon["type"]:
            if pokemon["ability"] == "adaptability":
                modifier = 2
            else:
                modifier = 1.5

        if self.calculate_effectiveness()["weak"].count(pokemon_move["type"]) == 2:
            modifier *= 4
        elif self.calculate_effectiveness()["weak"].count(pokemon_move["type"]) == 1:
            modifier *= 2

        if self.calculate_effectiveness()["resist"].count(pokemon_move["type"]) == 2:
            modifier *= 0.25
        elif self.calculate_effectiveness()["resist"].count(pokemon_move["type"]) == 1:
            modifier *= 0.5

        if pokemon_move["type"] in self.calculate_effectiveness()["immune"]:
            if pokemon["ability"] == "scrappy" and pokemon_move["type"] in ["fighting", "normal"]:
                return modifier
            else:
                return 0

        if pokemon["ability"] in ["teravolt", "moldbreaker"]:
            return modifier

        opponent_pokemon = [x.lower().replace(" ", "") for x in self.pokedex[self.opponent["name"]]["abilities"]]

        if pokemon_move["type"] == "water" and "waterabsorb" in opponent_pokemon:
            return 0
        elif pokemon_move["type"] == "grass" and "sapsipper" in opponent_pokemon:
            return 0
        elif pokemon_move["type"] == "fire" and "flashfire" in opponent_pokemon:
            return 0
        elif pokemon_move["type"] == "electric" and "voltabsorb" in opponent_pokemon:
            return 0
        elif pokemon_move["type"] == "ground" and "levitate" in opponent_pokemon:
            return 0
        else:
            return modifier



    def ability_of_pokemon_modifies_power_of_pokemon_move(self, pokemon, pokemon_move):
        ability = pokemon["ability"]

        if ability == "aerilate" and pokemon_move["type"] == "normal":
            pokemon_move["type"] == "flying"

        if ability in ["blaze", "overgrow", "torrent", "swarm"] and float(pokemon["hp"]) <= 0.33:
            i = {"blaze": "fire", "overgrow": "grass", "torrent": "water", "swarm": "bug"}
            if i[ability] == pokemon_move["type"]:
                pokemon_move["power"] *= 1.5

        if ability == "darkaura" and pokemon_move["type"] == "dark":
            pokemon_move["power"] *= 1.33

        if ability == "fairyaura" and pokemon_move["type"] == "fairy":
            pokemon_move["power"] *= 1.33

        # One Punch Man
        if ability == "ironfist" and "punch_move" in list(self.pokedex_moves[pokemon_move["name"]].keys()):
            pokemon_move["power"] *= 1.2

        if ability == "megalauncher" and "pulse_move" in list(self.pokedex_moves[pokemon_move["name"]].keys()):
            pokemon_move["power"] *= 1.5

        if ability == "reckless" and "recoil" in list(self.pokedex_moves[pokemon_move["name"]].keys()):
            pokemon_move["power"] *= 1.2

        if ability == "sandforce" and self.weather == "sandstorm" and pokemon_move["type"] in ["rock", "ground", "steel"]:
            pokemon_move["power"] *= 1.3

        if ability == "sheerforce" and "secondary_effect" in list(self.pokedex_moves[pokemon_move["name"]].keys()):
            pokemon_move["power"] *= 1.3

        if ability == "strongjaw" and "bite_move" in list(self.pokedex_moves[pokemon_move["name"]].keys()):
            pokemon_move["power"] *= 1.5

        if ability == "technician" and pokemon_move["power"] <= 60:
            pokemon_move["power"] *= 1.5

        if ability == "tintedlens":
            opponent_pkmn_resistant_against = self.calculate_effectiveness(self.opponent["name"])["resist"]
            if pokemon_move["type"] in opponent_pkmn_resistant_against:
                pokemon_move["power"] *= 2

        if ability == "toughclaws" and "contact_move" in list(self.pokedex_moves[pokemon_move["name"]].keys()):
            pokemon_move["power"] *= 1.3

        return pokemon_move["power"]

    def switch_pokemon(self):
        strongest_moves = [sorted(self.moves_power(pkmn), key=lambda x: x["power"])[::-1][0] for pkmn in self.team if pkmn["active"] != True]
        strongest_move_index = strongest_moves.index(sorted(strongest_moves, key=lambda x: x["power"])[::-1][0])
        strongest_move = sorted(strongest_moves, key=lambda x: x["power"])[::-1][0]
        strongest_pokemon = [x for x in self.team if x["name"] == strongest_move["pokemon"]][0]


        strongest_pokemon_id = strongest_pokemon["id"]
        current_pokemon_id = 1

        strongest_pokemon_index = self.team.index(strongest_pokemon)
        current_pokemon_index = self.team.index([i for i in self.team if i["active"] == True][0])

        self.team[current_pokemon_index]["id"] = strongest_pokemon_id
        self.team[strongest_pokemon_index]["id"] = 1

        opponent_pkmn_type = [x.lower() for x in self.pokedex[self.opponent["name"]]["types"]]
        weak_against = self.calculate_effectiveness(strongest_pokemon["name"])["weak"]

        if len([i for i in weak_against if i in opponent_pkmn_type]) > 0:
            self.do_not_switch = True

        self.ws.send("{}|/switch {}".format(self.room, strongest_pokemon_id))



    def calculate_effectiveness(self, pkmn = None):
        effectiveness = {"weak": [], "resist": [], "immune": []}

        if pkmn is not None:
            pokemon_type = [x.lower() for x in Battle.pokedex[pkmn]["types"]]
        else:
            pokemon_type = [x.lower() for x in Battle.pokedex[self.opponent["name"]]["types"]]


        for pkmn_type in pokemon_type:
            effectiveness["weak"].append(Battle.pokedex_effectiveness[pkmn_type]["weak_against"])
            effectiveness["resist"].append(Battle.pokedex_effectiveness[pkmn_type]["resistant_against"])
            effectiveness["immune"].append(Battle.pokedex_effectiveness[pkmn_type]["immune_against"])


        for x in effectiveness:
            effectiveness[x] = sorted([z for x in effectiveness[x] for z in x]) # flatten the array

        for x in [z for z in effectiveness["weak"] if z in effectiveness["resist"]]:
            effectiveness["weak"].remove(x)
            effectiveness["resist"].remove(x)

        return effectiveness

    def can_use_status_move(self):
        opponent_pkmn_type = self.pokedex[self.opponent["name"]]["types"]
        moves = self.active["moves"]

    def decide(self):
        self.active = [i for i in self.team if i["active"] == True][0]

        opponent_pkmn_type = [x.lower() for x in self.pokedex[self.opponent["name"]]["types"]]
        weak_against = self.calculate_effectiveness(self.active["name"])["weak"]

        if len([i for i in weak_against if i in opponent_pkmn_type]) > 0 and self.do_not_switch == False: # current pokemon is 2x or 4x weak against opponent.
            return self.switch_pokemon()

        if self.active["hp"] == "0 fnt":
            self.do_not_switch = False
            return self.switch_pokemon()

        moves_that_heal = [i for i in list(self.pokedex_moves.keys()) if self.pokedex_moves[i].get("heal_move")]
        if self.active["hp"] < 0.25 and len([i for i in self.active["moves"] if i in moves_that_heal]) > 0:
            move_that_heals = [i for i in self.active["moves"] if i in moves_that_heal][0]
            return self.ws.send("{}|/move {}".format(self.room, move_that_heals))

        data = sorted(self.moves_power(), key=lambda x: x["power"])[::-1]


        self.strongest_move = data[0]
        if self.strongest_move["power"] == 0 or self.strongest_move["name"] in self.moves_that_switch:
            return self.switch_pokemon()

        if len([x for x in self.active["moves"] if x in self.status_moves_names]) > 0:
            _move = [x for x in self.active["moves"] if x in self.status_moves_names][0]
            move = [x for x in self.status_moves if x["name"] == _move][0]
            if move["effect"] not in self.statuses:
                self.statuses.append(move["effect"])
                return self.ws.send("{}|/move {}".format(self.room, move["name"]))

        return self.ws.send("{}|/move {}".format(self.room, data[0]["name"]))
