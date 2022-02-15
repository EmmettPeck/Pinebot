#   Pinebot
#   By: Emmett Peck
#
#   A simple discord bot to allow remote whitelisting through discord.
#   To be run on linux server alongside dockerized servers.

#   TO/DO
#   -   Breakout mcChannels into external file
#   -   Breakout role_Whitelist into external file

import os
import discord
import sys, traceback

from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
extensions = ['cogs.owner', 'cogs.utils', 'cogs.social'] #Cogfiles

def get_prefix(bot, message):
    """A callable Prefix for our bot. This could be edited to allow per server prefixes."""

    prefixes = ['>', 'lol ']

    return commands.when_mentioned_or(*prefixes)(bot, message)

# Set Prefix
bot = commands.Bot(command_prefix=get_prefix, description='A server interface bot.')

# Load cogs listed in extensions
if __name__ == '__main__':
    for extension in extensions:
        bot.load_extension(extension)

# On Ready
@bot.event
async def on_ready():
    print("----------- PineBot ---------- ")
    print(f'\n\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')

    # Change bot playing status
    await bot.change_presence(game=discord.Game(name='Minecraft', type=1, url='mc.pineserver.net'))
    print(f'Successfully logged in and booted...')

bot.run(os.getenv('TOKEN'))