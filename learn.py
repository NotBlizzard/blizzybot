# learn.py
import json
# TODO:

class Learn:
    def __init__(self, battle):
        self.battle = battle

    def write(self, pokemon, move):
        data = json.loads(open("./data/pokemon_moves_data.json", "r").read())

        if pokemon in data:
            if move in data[pokemon]:
                data[pokemon][move] += 1
            else:
                data[pokemon][move] = 0
                data[pokemon][move] += 1
        else:
            data[pokemon] = {}
            data[pokemon][move] = 0
            data[pokemon][move] += 1


        with open("./data/pokemon_moves_data.json", "w") as pokemon_moves_data:
            pokemon_moves_data.write(json.dumps(data))
