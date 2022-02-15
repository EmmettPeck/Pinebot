#   Pinebot
#   By: Emmett Peck
#
#   A simple discord bot to allow remote whitelisting through discord.
#   To be run on linux server alongside dockerized servers.

#   TO/DO
#   -   Breakout mcChannels into external file
#   -   Breakout role_Whitelist into external file
#   -   Server List Command
#   -   "Start Here" Channel Minecraft
#   -   Purge x chats admin command
#   -   Consider ideas of how to a live minecraft/server chat integrated? (Docker logs watcher/filterer)
#   *   Changing bot presence based on time of day (5-8pm playing on server) 10 - 8am sleeping, working, etc. Make lively
#   -   Whitelisting Application System (reacts?)

import discord
from discord.ext import commands
import sys, traceback

import os
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