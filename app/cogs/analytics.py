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
    
# ---------------------------------------------------------------------------------------------------
        
# Commands ------------------------------------------------------------------------------------------
    @commands.command(name='playtime',help='Returns playtime on pineservers. >playtime <player-name> <server-name>, otherwise returns total of player.',brief='Get total playtime.')
    async def playtime(self, ctx, name=None, server=None):

        # Name Catch
        if name == None:
            await ctx.send("Please provide a playername, >playertime <name> <optional-server>")
            return

        if server == None:
            await ctx.send("Please provide a server, >playertime <name> <optional-server>")
            return

        # Total
        if server == None:
            total = analytics_lib.handle_playtime(bot=self.bot, server_name=server, who=name)
            await ctx.send(embed = embed_build(f"{name} has played for `{analytics_lib.td_format(total)}` across all servers."))
            return

        # Specific Server Playtime
        else: 
            single = analytics_lib.handle_playtime(bot=self.bot, server_name=server, who=name)
            if single:
                await ctx.send(embed = embed_build(f"Player `{name}` has played for `{analytics_lib.td_format(single)}` on `{server}`."))
                return
            if single == timedelta():
                await ctx.send(embed = embed_build(f"Player & Server recognized, yet no tengo playtime on `{server}`."))
            else:
                await ctx.send(embed = embed_build(f"Either player or server not found. Are you sure `{server}` is a server and `{name}` has played on that server? [Case Sensitive, I know, I know]"))
# ---------------------------------------------------------------------------------------------------

def setup(bot):
    bot.add_cog(Analytics(bot))