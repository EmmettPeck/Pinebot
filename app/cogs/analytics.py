"""
Discord cog to handle accessing of server playtime information.

This module holds commands used by users to interface with information gathered
by pinebot. Calls methods and provides conditions for multiple input conditions.

Authors: Emmett Peck (EmmettPeck)
Version: May 27th, 2022
"""

from datetime import timedelta

from discord.ext import commands

import analytics_lib
from embedding import embed_build, embed_playtime


class Analytics(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(
        name='playtime', 
        help='''Returns playtime on pineservers. 
            >playtime <player-name> <server-name>, 
            otherwise returns total of player.''',
        brief='Get total playtime.')
    async def playtime(self, ctx, name:str=None, server:str=None):
        """
        Prints playtime information to channel
        
        Gets playtime for requesting user if no args provided, 
        otherwise gathers playtime for other user. If server is provided,
        Gathers playtime of username or matching UUID in that server.

        Parameter ctx: discord channel used by discord.py
        Preconditon: ctx is a discord channel

        Parameter name: Username to search for in server if provided, 
        otherwise looks for discord user w/ linked accounts.
        Precondition: name is a str

        Parameter server: Server to get playtime from.
        Precondition: server is an str
        """

        # If name not provided, prompt user and return.
        if name == None:
            await ctx.send(
                "Please provide a playername,"
                " >playertime <name> <optional-server>")
            return

        # If server not provided, prompt user and return.
        if server == None:
            await ctx.send(
                "Please provide a server, "
                ">playertime <name> <optional-server>")
            return

        # TODO If server not provided, print total w/ list of top servers
        if server == None:
            total = analytics_lib.handle_playtime(
                bot=self.bot,
                server_name=server, 
                who=name)
            await ctx.send(
                embed = embed_build(
                reference=ctx.author,
                message=
                    f"{name} has played for `{analytics_lib.td_format(total)}` "
                    "across all servers."))
            return

        # Look for server. found? print total: prompt user of input error. -----
        else: 
            # Get Playtime From Server
            single = analytics_lib.handle_playtime(
                bot=self.bot, 
                who=name,
                server_name=server)

            # Print Playtime
            if single:
                await ctx.send(
                    embed = embed_playtime(
                        reference=ctx.author, 
                        username=name,
                        total_playtime=single.get('playtime'), 
                        dict_list=[single]))
                return

            # If Playtime present, but empty, prompt user
            if single == timedelta():
                await ctx.send(
                    embed = embed_build(
                        reference=ctx.author,
                        message=
                        "Player & Server recognized, yet no tengo playtime on `"
                        f"{server}`."))

            # If None
            elif single == None:
                await ctx.send(
                    embed = embed_build(
                        reference=ctx.author,
                        message=
                        f"Either player or server not found. Are you sure `"
                        f"{server}` is a server and `{name}` has played on that" 
                        "server? [Case Sensitive, I know, I know]"))

            # For other false evaluating conditons, notify developer.
            else:
                raise NotImplementedError(f"single == {single}")


def setup(bot):
    """
    Setup conditon for discord.py cog
    """
    bot.add_cog(Analytics(bot))
