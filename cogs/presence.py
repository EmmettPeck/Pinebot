#presence.py
#by: Emmett Peck
"""A cog that adds logging on_ready and scheduled set_presence"""


import asyncio
from datetime import datetime
import discord
from discord.ext import tasks, commands

class Presence(commands.Cog):
    def __init__(self):
        self.set_presence.start()

    def cog_unload(self):
        self.set_presence.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print("----------------- PineBot -----------------")
        print(f'Logged in as: {self.bot.user.name} - {self.bot.user.id}\nVersion: {discord.__version__}\n')
        print('Successfully logged in and booted...\n')
    
    @tasks.loop(minutes=1.0)
    async def set_presence(self):
        now = datetime.now()
        hour = now.strftime("%H")

        if hour >= 22 and hour < 7:
            self.bot.change_presence(activity = discord.Activity(type = discord.ActivityType.Custom, emoji=":zzz:",name = 'Sleeping'))
        elif hour >= 7 and hour < 8:
            self.bot.change_presence(activity = discord.Activity(type = discord.ActivityType.Custom, emoji=":coffee:",name = 'Getting Ready For The Day'))
        elif hour >= 8 and hour < 17:
            self.bot.change_presence(activity = discord.Activity(type = discord.ActivityType.Custom, emoji=":evergreen:",name = 'Working for www.pineserver.net'))
        elif hour >= 17 and hour < 21:
            self.bot.change_presence(activity = discord.Activity(type = discord.ActivityType.playing, name = 'mc.pineserver.net'))
        elif hour >= 21 and hour < 22:
            self.bot.change_presence(activity = discord.Activity(type = discord.ActivityType.Custom, emoji=":book:",name = 'Getting Ready For Bed'))
        else:
            print("ERROR: Bot Presence detected outside of 0-24HR range.")
        
def setup(bot):
    bot.add_cog(Presence(bot))        