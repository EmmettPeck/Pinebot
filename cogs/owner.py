import discord
from discord.ext import commands

class OwnerCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def cogs_reload(self, cogs):
        """Returns true if successful; reloads cogs referenced in parameters"""
        for cog in cogs:    
            try:
                self.bot.unload_extension(cog)
            except Exception as e:
                print("ERROR:Unload cogs_reload")
                return False
            else:
                self.bot.load_extension(cog)
        return True
    
    # Add server
    @commands.command(name="addserver", help="Adds args dictionary assigned to channel\n Acceptable args {name, version, docker_name, ip, description}")
    @commands.is_owner()
    async def addServer(self, ctx, server_name, version, docker_id, ip, *, description):
        """Adds server name, dockerID, IP, description tied to current channel"""
        sDict = {"name": server_name, "version": version, "channel_id": ctx.channel.id, "docker_name": docker_id, "ip": ip, "description": description}
        
        DChannels.add_channel(sDict)

        await ctx.send(f"Server {sDict} Added Successfully")
        print(f"Server {sDict} Added Successfully")

    #Remove server
    @commands.command(name="remserver", help="Removes dictionary assigned to channel")
    @commands.is_owner()
    async def remserver(self, ctx):
        """Remove server corresponding with channel_id"""
        list = DChannels.get_channels()
        try:
            rDict = next(item for item in list if item["channel_id"] == ctx.channel.id)
            popID = DChannels.get_channels.index(rDict)
            DChannels.remove_channel(popID)
        except:
            await ctx.send(f"Server {rDict} Removal Failed")
            print(f"Server {rDict} Removal Failed")
        else:
            await ctx.send(f"Server {rDict} Removed Successfully")
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