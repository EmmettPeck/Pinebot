#presence.py
#by: Emmett Peck
"""A cog that adds logging on_ready and scheduled set_presence"""

from datetime import datetime
import discord
from discord.ext import tasks, commands

class Presence(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    def cog_unload(self):
        self.set_presence.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print("----------------- PineBot -----------------")
        print(f'Logged in as: {self.bot.user.name} - {self.bot.user.id}\nVersion: {discord.__version__}\n')
        self.set_presence.start()
        print('Successfully logged in and booted...\n')
    
    @tasks.loop(minutes = 10)
    async def set_presence(self):
        hour = int(datetime.now().strftime("%H"))

        print(f"Hour: {hour}")
        if hour >= 22 or hour < 7:
            _activity = discord.Activity(type = discord.ActivityType.watching, name = 'the night roll by 💤')
            _status = discord.Status.idle
        elif hour >= 7 and hour < 8:
            _activity = discord.Activity(type = discord.ActivityType.listening, name = 'a podcast ☕', status=discord.Status.online)
            _status = discord.Status.online
        elif hour >= 8 and hour < 17:
            _activity = discord.Activity(type = discord.ActivityType.listening, name = 'customers 🌲', status=discord.Status.online)
            _status = discord.Status.online
        elif hour >= 21 and hour < 22:
            _activity = discord.Activity(type = discord.ActivityType.watching, name = 'the pages roll by 📖', status=discord.Status.online)
            _status = discord.Status.online
        else:#elif hour >= 17 and hour < 21:
            _activity = discord.Activity(type = discord.ActivityType.playing, name = 'mc.pineserver.net', status=discord.Status.online)
            _status = discord.Status.online

        await self.bot.change_presence(activity = _activity, status = _status)

def setup(bot):
    bot.add_cog(Presence(bot))        