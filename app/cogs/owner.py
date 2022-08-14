"""
Module containing commands for managing discord cogs & containers at runtime

Attributions: This module is an adaptation of an example of cogload/reload in
the discord.py documenatation

Authors: Emmett Peck (EmmettPeck)
Version: July 19th, 2022
"""


import discord
from discord.ext import commands

from database import DB
from messages import split_first
from dictionaries import build_server

class OwnerCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="addserver",
        brief="Assigns current channel to a gameserver.", 
        help="Adds args dictionary assigned to channel"
        "\n Args {name, game, version, docker_name, ip, description} in that order. "
        "Version must be formatted 'GameCog:version'")
    @commands.is_owner()
    async def addServer(self, ctx, server_name, game,
        version, docker_id, ip, *, description):
        """
        Assigns current channel to a docker gameserver instance 

        Adds server name, dockerID, IP, description tied to current channel

        All parameters are str seperated by spaces, except for description
        """
        new_server = build_server(
            name=server_name,
            game=game,
            version=version,
            docker=docker_id,
            ip=ip,
            description=description,
            cid = [ctx.channel.id],
            hidden = True
        )

        # TODO Ensure servername not taken

        # TODO Ensure game exists (Upsert collection on cogstart?)

        DB.mongo['Servers'][game].insert_one(new_server)#
        # TODO Update Cog

        await ctx.send(f"Server {new_server} Added Successfully")
        print(f"Server {new_server} Added Successfully")
    
        # TODO Delete add message

        # TODO Print "Beginning of channel" header

    @commands.command(
        name="remserver", 
        brief=">remserver <cog:version>",
        help="Removes dictionary assigned to channel")
    @commands.is_owner()
    async def remserver(self, ctx, version:str):
        # TODO Remove Server
        # TODO Update Cog
        pass
'''
    @commands.command(name='load', hidden=True)
    @commands.is_owner()
    async def cogLoad(self, ctx, *, cog: str):
        """Command which Loads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

    @commands.command(name='unload', hidden=True)
    @commands.is_owner()
    async def cogUnload(self, ctx, *, cog: str):
        """Command which Unloads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            self.bot.unload_extension(cog)
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

    @commands.command(name='reload', hidden=True)
    @commands.is_owner()
    async def cogReload(self, ctx, *, cog: str):
        """Command which Reloads a Module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
        else:
            await ctx.send('**`SUCCESS`**')

    def cogs_reload(self):
        """Returns true if successful; reloads cogs referenced in DB"""
        for cog in DB.get_cogs():    
            try:
                self.bot.unload_extension(cog)
            except Exception as e:
                print("ERROR:Unload cogs_reload")
                return False
            else:
                self.bot.load_extension(cog)
        return True
'''

def setup(bot):
    bot.add_cog(OwnerCog(bot))        