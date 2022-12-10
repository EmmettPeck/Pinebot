""" 
main.py

A discord bot to allow remote whitelisting, chat intergration, & playtime logging through discord. To be run in a network of dockerized servers.

By: (EmmettPeck)
Edited: 12/10/22
"""
import os
import sys
import logging

from discord.ext import commands

from database import DB

# Setup Logging Configuration
logging.basicConfig(
    filename='../data/pinebot.log', 
    level=logging.DEBUG,
    filemode='w',
    format='%(asctime)s [%(module)s]-[%(lineno)d] [%(levelname)s]: %(message)s'
)

# Set Bot Prefix
def get_prefix(bot, message):
    prefixes = ['>']
    return commands.when_mentioned_or(*prefixes)(bot, message)

bot = commands.Bot(
    command_prefix=get_prefix, 
    description="Hi! I'm PineBot, Pineserver's discord interface."
)

# Ensure run as main
if __name__ == '__main__':
    # Load cogs listed in extensions
    for extension in DB.get_cogs():
        bot.load_extension(extension)
        logging.debug(f"loaded {extension}")

bot.run(os.getenv('TOKEN'),bot=True, reconnect=True)
