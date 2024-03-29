#presence.py
#by: Emmett Peck
"""A cog that adds logging on_ready and scheduled set_presence"""
# Due to custompresence not being implemented for bots, I had to get creative
# Status not seeming to work currently

from itertools import cycle
from datetime import datetime
import logging
from random import randint
import discord
from discord.ext import tasks, commands

# TODO Add more presence options.cycle
disturbing_songs = ["a podcast ☕","Bot Club (feat. Lil Botty)","Gymnopédie No. 1", "Kill EVERYBODY","Get Into It (Yuh)","Ex Machina (Original Motion Picture Soundtrack)","Have Mercy",">help", "The Third Monke at Noah's Ark","The Art of Monke"]
cycle_songs = cycle(disturbing_songs)

class Presence(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.set_presence.start()

    def cog_unload(self):
        self.set_presence.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info("----------------- PineBot -----------------")
        logging.info(f'Logged in as: {self.bot.user.name} - {self.bot.user.id} Version: {discord.__version__}')
        logging.info('Successfully logged in and booted...')
    
    @tasks.loop(minutes = 1)
    async def set_presence(self):
        hour = int(datetime.now().strftime("%H"))

        #print(f"Hour: {hour}")
        if hour >= 22 or hour < 7:
            _activity = discord.Activity(type = discord.ActivityType.watching, name = 'the night roll by 💤')
            _status = discord.Status.idle
        elif hour >= 7 and hour < 8:
            # Grab a "random" playlist song
            for i in range(randint(1,10)):
                _name = next(cycle_songs)
            _activity = discord.Activity(type = discord.ActivityType.listening, name = _name)
            _status = discord.Status.online
        elif hour >= 8 and hour < 17:
            _activity = discord.Activity(type = discord.ActivityType.playing, name = '>help')
            _status = discord.Status.idle
        elif hour >= 21 and hour < 22:
            _activity = discord.Activity(type = discord.ActivityType.watching, name = 'you')
            _status = discord.Status.online
        else:#elif hour >= 17 and hour < 21:
            _activity = discord.Activity(type = discord.ActivityType.playing, name = 'mc.pineserver.net')
            _status = discord.Status.online

        await self.bot.change_presence(status=_status, activity=_activity)
    @set_presence.before_loop
    async def before_set_presence(self):
        await self.bot.wait_until_ready() 
def setup(bot):
    bot.add_cog(Presence(bot))        