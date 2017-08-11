# from colorama import Style, Fore
from bot import Bot

import threading
import sys
import os
import time
import json
from importlib import import_module
import traceback
from threading import Thread

# import class from each plugin
sys.path.append(os.path.abspath("./plugins"))
for i in os.listdir("./plugins"):
    if i[-3:] == ".py":
        module = import_module(i[0:-3])
        locals()[i[0:-3].capitalize()] = getattr(module, i[0:-3].capitalize())

bots = []
data = {}

if not os.path.isfile("./settings.json"):
    print("Creating settings.json file....")
    with open("./settings.json", "w") as settings:
        settings_settings = {"bots":[{"username":"","password":"","server":"","admins":[],"rooms":[],"symbol":"","plugins":[],"avatar":False,"log":True}]}

        settings.write(json.dumps(settings_settings, indent=2))

    print("settings.json file created")
    sys.exit(0)


def string_to_plugin(plugins):
    modules = []
    for plugin in plugins:
        module = import_module(plugin.lower())
        modules.append(getattr(module, plugin)())

    return modules

with open("./settings.json", "r") as settings:
    data = json.loads(settings.read())

if __name__ == "__main__":
    try:
        target=Bot(
            bot["username"],
            bot["password"],
            bot["server"],
            bot["admins"],
            bot["rooms"],
            bot["symbol"],
            bot["avatar"],
            string_to_plugin(bot["plugins"]),
            bot["log"]
        ).connect,
        args=()
    except KeyboardInterrupt:
        bots = []
        sys.exit(1)

    except:
        pass
