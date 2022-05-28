"""
Module containing commands for managing discord cogs & containers at runtime

Attributions: This module is an adaptation of an example of cogload/reload in
the discord.py documenatation

Authors: Emmett Peck (EmmettPeck)
Version: May 27th, 2022
"""


import discord
from discord.ext import commands

from database import DB
from messages import split_first

class OwnerCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="addserver",
        brief="Assigns current channel to a gameserver.", 
        help="Adds args dictionary assigned to channel"
        "\n Args {name, version, docker_name, ip, description} in that order. "
        "Version must be formatted 'GameCog:version'")
    @commands.is_owner()
    async def addServer(self, ctx, server_name, 
        version, docker_id, ip, *, description):
        """
        Assigns current channel to a docker gameserver instance 

        Adds server name, dockerID, IP, description tied to current channel

        All parameters are str seperated by spaces, except for description
        """
        sDict = {
            "name": server_name, 
            "version": version, 
            "channel_id": ctx.channel.id, 
            "docker_name": docker_id, 
            "ip": ip, 
            "description": description, 
            "hidden": False}
        
        # Ensure Version Contains :
        if not (':' in version):
            await ctx.send(f"Version must be formatted 'GameCog:version'")
            return

        # TODO Check that docker_name is a real container

        # Add & save container registry
        DB.add_container(sDict)
        server = self.bot.get_cog(split_first(version,':')[0].title())
        server.servers.append(sDict)

        await ctx.send(f"Server {sDict} Added Successfully")
        print(f"Server {sDict} Added Successfully")

    @commands.command(
        name="remserver", 
        brief=">remserver <cog:version>",
        help="Removes dictionary assigned to channel")
    @commands.is_owner()
    async def remserver(self, ctx, version:str):
        """
        Removes linked container registry
        """
        list = DB.get_containers()
        try:
            # Find server
            rDict = next(item for item in list if item["channel_id"] == ctx.channel.id)
            popID = list.index(rDict)
            name = list[popID]["name"]
            DB.remove_container(popID)

            # Remove server from corresponding cog
            server = self.bot.get_cog(split_first(version,':')[0].title())
            server.servers.remove(rDict)
        except:
            await ctx.send(f"Server {name} {rDict} Removal Failed")
            print(f"Server {name} {rDict} Removal Failed")
        else:
            await ctx.send(f"Server {name} {rDict} Removed Successfully")
            print(f"Server {name} {rDict} Removed Successfully")

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


def setup(bot):
    bot.add_cog(OwnerCog(bot))        