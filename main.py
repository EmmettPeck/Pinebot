#   Pinebot
#   By: Emmett Peck
#
#   A simple discord bot to allow remote whitelisting through discord.
#   To be run on linux server alongside dockerized servers.

#   TO/DO
#   -   Server List Command
#   -   "Start Here" Channel Minecraft
#   -   Purge x chats admin command
#   -   Consider ideas of how to a live minecraft/server chat integrated? (Docker logs watcher/filterer)
#   -   Whitelisting Application System (reacts?)
#   -   Test if admin commands are hidden from non-admins (ifso you can make a command that sets a channel as a dockerID)

import discord
from discord.ext import commands
import sys, traceback

import os
import json
from dotenv import load_dotenv

load_dotenv()
extensions = ['cogs.utils', 'cogs.social', 'cogs.owner','cogs.presence'] #Cogfiles

def get_prefix(bot, message):
    """A callable Prefix for our bot. This could be edited to allow per server prefixes."""

    prefixes = ['>', 'lol ']

    return commands.when_mentioned_or(*prefixes)(bot, message)

# Set Prefix
bot = commands.Bot(command_prefix=get_prefix, description="Hi! I'm PineBot, Pineserver's discord interface.")

if __name__ == '__main__': # Load cogs listed in extensions
    for extension in extensions:
        bot.load_extension(extension)

bot.run(os.getenv('TOKEN'),bot=True, reconnect=True)