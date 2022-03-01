"""A cog for discord.py that carries an assortment of utility commands for Pineserver"""
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, CheckFailure
import json

from dockingPort import DockingPort

def load_whitelist():
    # Load role_Whitelist.json
    with open(r"data/role_Whitelist.json", 'r') as read_file:
        role_Whitelist = json.load(read_file)
    return role_Whitelist

# Using Global (In module)
role_Whitelist = load_whitelist()

class Utilities(commands.Cog):

    def __init__(self, bot):
        self.dockingPort=DockingPort()
        self.bot = bot

    #GetID
    @commands.command(name='getID',help='Returns current channel ID',brief='Returns channel ID', hidden=True)
    async def getID(self, ctx):
        ''' Command which returns current channel ID'''
        await ctx.send(ctx.channel.id)

    #Whitelist
    @commands.command(name='whitelist', help=f"Usage: >whitelist <arg>. Requires a {role_Whitelist} role.", brief="Whitelist a player.")
    @commands.has_any_role(*role_Whitelist)
    async def whitelist(self, ctx, *, mess):
        ''' Whitelists <args> to corresponding server as is defined in dockingPort.py if user has applicable role'''

        # Check Roles agains role_Whitelist
        response = self.dockingPort.portSend(ctx.channel.id, f"whitelist add {mess}",True)
        await ctx.send(response)

    @whitelist.error
    async def whitelist_error(self, error, ctx):

        if isinstance(error, CheckFailure):
            await self.bot.send_message(ctx.message.channel, "You do not have the necessary roles.")

    #Send
    @commands.command(name='send', help="Usage: >send <arg>. Requires administrator permissions.", brief="Sends command to server.")
    @has_permissions(administrator=True)
    async def send(self, ctx, *, mess):
        ''' Sends <args> as /<args> to corresponding server as is defined in dockingPort.py if user has applicable role'''

        response = self.dockingPort.portSend(ctx.channel.id, mess,True)
        await ctx.send(response)

    @send.error
    async def send_error(self, error, ctx):
        if isinstance(error, CheckFailure):
            await self.bot.send_message(ctx.message.channel, "You do not have the necessary permissions.")

    #ServerList
    @commands.command(name='serverlist', help="Lists all currently registered servers, whitelist may be required to join", brief="Lists all pineserver.net servers")
    async def server_list(self, ctx):
        message = f"""``Server List``\n```Name    | IP                 | Description\n"""
        for dict in self.dockingPort.mc_Channels:
            
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
        await ctx.send(message)

def setup(bot):
    bot.add_cog(Utilities(bot))