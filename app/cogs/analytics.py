"""
Discord cog to handle analytics, including accessing of server playtime info.

This module holds commands to interface with information gathered by pinebot.

Authors: Emmett Peck (EmmettPeck)
Version: April 5st, 2023
"""

from datetime import datetime, timedelta
import logging
from discord.ext import commands

import analytics_lib
from dictionaries import playtime_dict
from embedding import embed_build, embed_playtime
from database import DB


class Analytics(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def plt(self, ctx, discord_id):
        acctcol = DB.mongo['Guilds']['Pineserver']

        query = acctcol.find_one({'linked':{'id':discord_id}})
        if query is None:
            # Unlinked Account Message
            await ctx.reply(
                embed=embed_build(
                    icon="⚠️",
                    message="Unlinked Discord Account",
                    description="We can't fetch your total playtime until you link a game account to your discord user. Link accounts using `>link`. See '>help link' for more information."
                ),
                mention_author=False
            )
            return
        
        dicts = self.fetch_total(query)
        await ctx.send(embed=embed_playtime(dicts))

    def fetch_total(self, account:dict):
        list = []
        
        for link in account['linked']:
            # For each game, search every server for user. Append each servername, playtime, game, and first join to a list as a dict to be sorted by playtime command
            # Search each server for player
            col = DB.mongo[link['game']][link['server_name']]
            query = col.find_one({'_id':link['servers_id']})
            if query is None: continue

            # Calculate Playtime
            package = analytics_lib.calculate_playtime(
                    col=col,
                    id=link['servers_id'],
            )

            list.append(playtime_dict(
                username=link['username'], #TODO Update account namechange in GameCog Get_UUID
                server_name=link['servers_name'],
                game=link['game'],
                playtime=package['playtime'],
                first_join=package['first_join'],
                last_connected=package['last_connected']
                )
            )
        return list

    @commands.command(
        name='playtime', 
        help=('Returns playtime on pineservers.' 
            '>playtime <player-name> <server-name>,' 
            'otherwise returns total of player.'),
        brief='Get total playtime.')
    async def playtime(self, ctx, name:str=None, server:str=None):
        """
        Prints playtime information to channel
        
        Gets playtime for requesting user if no args provided, gathers playtime for referenced users. In linked server, searches for playtime of specific user. If server is provided, gathers playtime of username or matching UUID in that server. (Leverage getUUID)
        """
        logging.debug(f"Gathering playtime for {name} {server}")
        
        # If name not provided, check for linked accounts, if none, return
        if name == None:
            await self.plt(ctx, ctx.author.id)

        # If message mentions a user (Total Linked Accounts)
        elif ctx.message.mentions != None:
            # Get mentioned user account dict, then gather playtime of 
            await self.plt(ctx, ctx.message.mentions[0].id)

        # If Server Not Provided (User from Linked Channel)
        elif server == None:
            # Attempt get servername from sent channel
                #TODO
            # If so, call function to send playtime from username & servername
                #TODO
            # If not, unlinked channel or no server provided
            if not server:
                # Tell user to use in linked channel, mention a user, or specify a servername
                await ctx.reply(
                    embed = embed_build(
                        icon="",
                        message="Incorrect Command Arguments",
                        description="Sent in an unlinked channel, or no server was provided.\nSee `>help playtime` for more information."
                    ),
                )

        # Get Playtime by Username & Server
        else: 
            # Call function to send playtime from username & servername
            #TODO
            pass
def setup(bot):
    """
    Setup conditon for discord.py cog
    """
    bot.add_cog(Analytics(bot))
