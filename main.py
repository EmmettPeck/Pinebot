#   Pinebot
#   By: Emmett Peck
"""   A simple discord bot to allow remote whitelisting through discord.
      To be run on linux server alongside dockerized servers."""

from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
extensions = ['cogs.dockingPort','cogs.utils', 'cogs.social', 'cogs.owner','cogs.presence', 'cogs.purge', 'cogs.connect4', 'cogs.chatLink'] #Cogfiles

def get_prefix(bot, message):
    """A callable Prefix for our bot. This could be edited to allow per server prefixes."""

    prefixes = ['>']

    return commands.when_mentioned_or(*prefixes)(bot, message)

# Set Prefix
bot = commands.Bot(command_prefix=get_prefix, description="Hi! I'm PineBot, Pineserver's discord interface.")

if __name__ == '__main__': # Load cogs listed in extensions
    for extension in extensions:
        bot.load_extension(extension)

bot.run(os.getenv('TOKEN'),bot=True, reconnect=True)