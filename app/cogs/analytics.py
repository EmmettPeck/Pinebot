"""
analytics.py

By: Emmett Peck
A discord cog to interface with playtime calculation.
"""

from datetime import timedelta

import analytics_lib
from database import DB
from discord.ext import commands, tasks
from embedding import embed_build
from messages import MessageType


# =====================================================================================================================================================================
class Analytics(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.connect_event_handler.start()

    def cog_unload(self):
        self.connect_event_handler.cancel()
    
# ---------------------------------------------------------------------------------------------------
# Connect Event Queue -------------------------------------------------------------------------------
# TODO Move to callable function in analytics_lib
    @tasks.loop(seconds=1)
    async def connect_event_handler(self):
        q = DB.get_connect_queue()

        # Quick Return
        if q.qsize() == 0: return

        # Calculate
        f = False
        while not q.qsize() == 0:
            f = True
            x = q.get()
            if x['type'] == MessageType.JOIN:
                is_online = True
            else:
                is_online = False
            analytics_lib.add_connect_event(x['username'], x['server'], is_online, x['time'])
        if f: DB.save_playerstats()
    @connect_event_handler.before_loop
    async def before_connect_event_handler(self):
        await self.bot.wait_until_ready() 
        
# Commands ------------------------------------------------------------------------------------------
    @commands.command(name='playtime',help='Returns playtime on pineservers. >playtime <player-name> <server-name>, otherwise returns total of player.',brief='Get total playtime.')
    async def playtime(self, ctx, name=None, server=None):
        uuid = analytics_lib.get_player_uuid(name)
        uuid_index = analytics_lib.get_uuid_index(uuid)

        # Name Catch
        if name == None:
            await ctx.send("Please provide a playername, >playertime <name> <optional-server>")
            return

        # Catch wrong names
        if uuid_index == None:
            await ctx.send("Player name not recognized. Either misspelled or hasn't played on Pineserver.")
            return

        # Total
        if server == None:
            total = analytics_lib.handle_playtime(uuid_index)
            await ctx.send(embed = embed_build(f"{name} has played for `{analytics_lib.td_format(total)}` across all servers."))
            return

        # Specific Server Playtime
        else: 
            single = analytics_lib.handle_playtime(uuid_index, server.title())
            if single:
                await ctx.send(embed = embed_build(f"{name} has played for `{analytics_lib.td_format(single)}` on {server.title()}."))
                return
            elif single == timedelta():
                await ctx.send(embed = embed_build(f"{name} hasn't played on {server.title()}."))
            else:
                await ctx.send(embed = embed_build(f"Server not found."))
# ---------------------------------------------------------------------------------------------------

def setup(bot):
    bot.add_cog(Analytics(bot))