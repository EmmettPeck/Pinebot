"""A cog for discord.py that carries an assortment of utility commands for Pineserver"""
from discord.ext import commands
from discord.ext.commands import has_permissions, CheckFailure

from database import DB
from dockingPort import DockingPort

class Utilities(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    # GetID --------------------------------------------------------------------------------------------------------------------------------------------------
    @commands.command(name='getID',help='Returns current channel ID',brief='Returns channel ID', hidden=True)
    async def getID(self, ctx):
        ''' Command which returns current channel ID'''
        await ctx.send(ctx.channel.id)

    # Whitelist -----------------------------------------------------------------------------------------------------------------------------------------------
    @commands.command(name='whitelist', help=f"Usage: >whitelist <arg>. Requires a {DB.get_role_whitelist()} role.", brief="Whitelist a player.")
    @commands.has_any_role(*DB.get_role_whitelist())
    async def whitelist(self, ctx, *, mess):
        ''' Whitelists <args> to corresponding server as is defined in DChannels if user has applicable role'''
        response = DockingPort().send(ctx.channel.id, f"whitelist add {mess}",True)
        if response:
            await ctx.send(response)
        else:
            await ctx.send("Server not found. Use command only in 'Minecraft' text channels.")
    @whitelist.error
    async def whitelist_error(self, error, ctx):
        if isinstance(error, CheckFailure):
            await self.bot.send_message(ctx.message.channel, "You do not have the necessary roles.")

    # Send --------------------------------------------------------------------------------------------------------------------------------------------------
    @commands.command(name='send', help="Usage: >send <arg>. Requires administrator permissions.", brief="Sends command to server.")
    @has_permissions(administrator=True)
    async def send(self, ctx, *, mess):
        ''' Sends <args> as /<args> to corresponding server as is defined in DChannels if user has applicable role'''
        response = DockingPort().send(ctx.channel.id, mess, True)
        if response:
            await ctx.send(response)
        else:
            await ctx.send("Server not found. Use command only in 'Minecraft' text channels.")
    @send.error
    async def send_error(self, error, ctx):
        if isinstance(error, CheckFailure):
            await self.bot.send_message(ctx.message.channel, "You do not have the necessary permissions.")

    # List -------------------------------------------------------------------------------------------------------------------------------------------------------
    @commands.command(name='list', help="Usage `>list` in desired corresponding channel.", brief="Lists online players.")
    async def list(self, ctx):
        response = DockingPort().send(ctx.channel.id, "/list")
        
        await ctx.message.delete()
        if response:
            await ctx.send(response)
        else:
            await ctx.send("Server not found. Use command only in 'Minecraft' text channels.")

    # ServerList --------------------------------------------------------------------------------------------------------------------------------------------------
    @commands.command(name='serverlist', help="Lists all currently registered servers, whitelist may be required to join", brief="Lists all pineserver.net servers")
    async def server_list(self, ctx):
        message = f"""``Server List``\n```Name    | IP                 | Description\n"""
        for dict in DB.get_containers():
            # Don't display hidden servers
            if dict.get("hidden"):
                continue
            # Format Spacing
            ni = len(dict.get("name"))
            name_spacing = ""
            while ni < 8:
                name_spacing += " "
                ni+=1

            pi = len(dict.get("ip"))
            ip_spacing = ""
            while pi < 19:
                ip_spacing += " "
                pi+=1

            # Print Element
            message += dict.get("name") + name_spacing + "| " + dict.get("ip") + ip_spacing + "| " + dict.get("description")+ "\n"

        message +="```"
        await ctx.message.delete()
        await ctx.send(message)
    # --------------------------------------------------------------------------------------------------------------------------------------------------

def setup(bot):
    bot.add_cog(Utilities(bot))