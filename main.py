#   Pinebot
#   By: Emmett Peck
#
#   A simple discord bot to allow remote whitelisting through discord.
#   To be run on linux server alongside dockerized servers.

#   TO/DO
#   -   Breakout mcChannels into external file
#   -   Breakout role_Whitelist into external file


import discord
from discord.ext import commands
import sys, traceback

import os
from dotenv import load_dotenv


load_dotenv()
extensions = ['cogs.utils', 'cogs.social'] #Cogfiles

def get_prefix(bot, message):
    """A callable Prefix for our bot. This could be edited to allow per server prefixes."""

    prefixes = ['>', 'lol ']

    return commands.when_mentioned_or(*prefixes)(bot, message)

# Set Prefix
bot = commands.Bot(command_prefix=get_prefix, description="Hi! I'm PineBot, Pineserver's discord interface.")

if __name__ == '__main__': # Load cogs listed in extensions
    for extension in extensions:
        bot.load_extension(extension)

@bot.event
async def on_ready():
    print("----------------- PineBot -----------------")
    print(f'Logged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')

    # Change bot playing status
    await bot.change_presence(activity = discord.Activity(type = discord.ActivityType.playing, name = 'mc.pineserver.net'))
    print('Successfully logged in and booted...\n')

bot.run(os.getenv('TOKEN'),bot=True, reconnect=True)