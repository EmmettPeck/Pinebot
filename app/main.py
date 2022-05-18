""" 
Pinebot
By: Emmett Peck
A discord bot to allow remote whitelisting, chat intergration, & playtime logging through discord. To be run in a network of dockerized servers.
"""
import os

from discord.ext import commands
from dotenv import load_dotenv

from database import DB

# -----------------------------------------------------------------------------------------
def get_prefix(bot, message):
    """A callable Prefix for our bot. This could be edited to allow per server prefixes."""
    prefixes = ['>']
    return commands.when_mentioned_or(*prefixes)(bot, message)

# --------------------------------------------------------------------------------------------
load_dotenv()
bot = commands.Bot(command_prefix=get_prefix, description="Hi! I'm PineBot, Pineserver's discord interface.") # Set Prefix

if __name__ == '__main__': # Load cogs listed in extensions
    for extension in DB.get_cogs():
        bot.load_extension(extension)

bot.run(os.getenv('TOKEN'),bot=True, reconnect=True)
