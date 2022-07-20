""" 
Pinebot
By: Emmett Peck
A discord bot to allow remote whitelisting, chat intergration, & playtime logging through discord. To be run in a network of dockerized servers.
"""
import os
import sys
import logging

from discord.ext import commands
from dotenv import load_dotenv

from database import DB

load_dotenv()
logging.basicConfig(filename='../data/pinebot.log', 
                    level=logging.DEBUG,
                    filemode='w',
                    format='%(asctime)s [%(module)s]-[%(lineno)d] [%(levelname)s]: %(message)s')



def get_prefix(bot, message):
    prefixes = ['>']
    return commands.when_mentioned_or(*prefixes)(bot, message)

bot = commands.Bot(
    command_prefix=get_prefix, 
    description="Hi! I'm PineBot, Pineserver's discord interface.") # Set Prefix

if __name__ == '__main__': # Load cogs listed in extensions
    for extension in DB.get_cogs():
        bot.load_extension(extension)
        logging.debug(f"loaded {extension}")

bot.run(os.getenv('TOKEN'),bot=True, reconnect=True)