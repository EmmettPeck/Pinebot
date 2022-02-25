import discord
from discord.ext import commands


class OwnerCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # Add server
    @commands.command(name="addserver", hidden=True)
    @commands.is_owner()
    async def addServer(self, ctx, server_name, docker_id, ip, description):
        """Adds server name, dockerID, IP, description tied to current channel"""
        sDict = {"name": server_name, "channel_id": ctx.channel.id, "docker_name": docker_id, "ip": ip, "description": description}
        
        # Save dict to file
        dockingPort=DockingPort()
        dockingPort.mc_Channels.append(sDict)
        dockingPort.save_mc_Channels()

        # Reload Utils Cog
        try:
            self.bot.unload_extension("cogs.utils")
        except Exception as e:
            print("ERROR:Addserver Unload Utils")
        else:
            self.bot.load_extension("cogs.utils")
            print(f"Server {sDict} Added Successfully")

    #Remove server
    @commands.command(name="remserver", hidden=True)
    @commands.is_owner()
    async def remserver(self, ctx, *):
        #Search List for channel id, pop dict, then save
        dockingPort=DockingPort()
        rDict = next(item for item in dicts if item["channel_id"] == ctx.channel.id)
        popID = dockingPort.mc_Channels.index(rDict)
        dockingPort.mc_Channels.pop(popID)
        dockingPort.save_mc_Channels()

        # Reload Utils Cog
        try:
            self.bot.unload_extension("cogs.utils")
        except Exception as e:
            print("ERROR:remserver Unload Utils")
        else:
            self.bot.load_extension("cogs.utils")
            print(f"Server {rDict} Removed Successfully")

# Hidden means it won't show up on the default help.
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


def setup(bot):
    bot.add_cog(OwnerCog(bot))        