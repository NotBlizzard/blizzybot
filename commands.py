# commands.py

import json
import re
import random
import traceback
import importlib
import requests
import battle
import commands
import sys
import time
import subprocess
import os
import time
import arrow

sys.path.append(os.path.abspath("./plugins"))

def can(command, user, bot):
    if user[1:] in bot.admins:
        return True

    rank_data = json.loads(open("./data/ranks.json", "r").read())
    ranks = {
        " ": 0,
        "+": 1,
        "%": 2,
        "@": 3,
        "&": 4,
        "~": 5
    }
    if user[0] not in list(ranks.keys()):
        return False

    if command not in list(rank_data.keys()):
        return True

    if ranks[user[0]] >= int(rank_data[command]):
        return True
    else:
        return False


def command_about(args, room, user, bot):
    if not can("about", user, bot): return ""
    return "BlizzyBot: A Pokemon Showdown bot written in Python {}".format(sys.version.split(" ")[0])

def command_vaporwave(args, room, user, bot):
    if not can("vaporwave", user, bot): return ""
    return "".join([" ".join([i, ""]) for i in args])

def command_restart(args, room, user, bot):
    if not can("restart", user, bot): return ""
    if len(bot.battles) > 0:
        return "Wait for all battles to finish first."
    else:
        bot.ws.send("{}|Restarting....".format(room))
        if os.name == "nt": # Windows
            subprocess.Popen(["cd", "scripts", "&&", "restart.bat", "{}".format(os.getpid())], shell=True)
        else: # Linux / Mac
            # TODO: Add script for Linux / Mac
            pass


def command_join(args, room, user, bot):
    if not can("join", user, bot): return ""
    return bot.join(args)

def command_set(args, room, user, bot):
    if not can("set", user, bot): return ""
    args = args.replace(" ", "").split(",")
    rank_data = json.loads(open("./data/ranks.json", "r").read())
    if not int(args[1]) in list(range(1, 6)):
        return "'{}' is not a valid rank. rank must be a number between 0 and 5 (0 being a normal user, 5 being administrator)".format(args[1])

    rank_data[args[0]] = args[1]
    with open("./data/ranks.json", "w") as f:
        f.write(json.dumps(rank_data))

    return "'{}' is now set to {}".format(args[0], args[1])

    if not can("uptime", user, bot): return ""
def command_uptime(args, room, user, bot):
    if not can("uptime", user, bot): return ""
    uptime = arrow.get(time.time() - bot.start_time).format("HH:mm:ss")
    hours = int(uptime.split(":")[0])
    minutes = int(uptime.split(":")[1])
    seconds = int(uptime.split(":")[2])

    if hours == 1:
        hours = str(hours) + " hour"
    else:
        hours = str(hours) + " hours"

    if minutes == 1:
        minutes = str(minutes) + " minute"
    else:
        minutes = str(minutes) + " minutes"


    if seconds == 1:
        seconds = str(seconds) + " second"
    else:
        seconds = str(seconds) + " seconds"


    uptime = "{}, {}, {}".format(hours, minutes, seconds)

    return "I have been running for {}.".format(uptime)

def command_battling(args, room, user, bot):
    if not can("battling", user, bot): return ""
    if bot.battling == True:
        bot.battling = False
    else:
        bot.battling = True

    return "{} is now {} battles.".format(bot.username, ["not accepting", "accepting"][bot.battling])

def command_eval(args, room, user, bot):
    if not can("eval", user, bot): return ""

    try:
        if re.match(r'battle-(.+)-(\d+)', room) is None:
            exec("self=bot;result={}".format(args), locals(), globals())
            return result
        else:
            current_battle = bot.current_battle()
            exec("self=current_battle;result={}".format(args), locals(), globals())
            return result
    except:
        traceback.print_exc()
        return "Error."

def command_reload(args, room, user, bot):

    if not can("reload", user, bot): return ""
    args = re.sub(r' ', '', args).split(",")

    if args[0] == "bot":
        import bot
        importlib.reload(bot)
    elif args[0] == "plugins":
        plugin = args[1]
        module = importlib.import_module(plugin)
        importlib.reload(module)
        return "'{}' have been reloaded.".format(plugin)
    elif args[0] == "commands":
        importlib.reload(commands)
    elif args[0] == "battles":
        if len(bot.battles) > 0:
            return "Wait until all battles are finished."
        else:
            importlib.reload(battle)
    else:
        return "'{}' is not a valid module to reload.".format(args[0])

    return "The module '{}' has been reloaded.".format(args[0])

def command_echo(args, room, user, bot):

    if ", " in args:
        if not can("say", user, bot): return ""
        args = args.split(", ")
        room = args[0]
        if room == "lobby":
            room = ""

        bot.ws.send("{}|{}".format(room, args[1]))
        return ""
    else:
        return args


def command_rps(args, room, user, bot):
    if not can("rps", user, bot): return ""
    args = args.split(",")
    if len(args) > 1:
        return "There can only be one choice."

    args[0] = args[0].capitalize()

    data = {
        "Rock": {
            "Scissors": "beats",
            "Paper": "loses to",
            "Rock": "ties"
        },
        "Paper": {
            "Rock": "beats",
            "Scissors": "loses to",
            "Paper": "ties"
        },
        "Scissors": {
            "Paper": "beats",
            "Rock": "loses to",
            "Scissors": "ties"
        }
    }
    bot_option = random.choice(["Rock", "Paper", "Scissors"])
    return "I chose {} so {} {} {}.".format(bot_option, bot_option, data[bot_option][args[0]], args[0])
