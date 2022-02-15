import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, CheckFailure
from dockingPort import portSend

role_Whitelist = {'Member', 'Moderator', 'Liam'} #Permissible Roles That REALLY need to be broken out into a file

class UtilsCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='getID',help='Returns current channel ID',brief='Returns channel ID')
    @has_permissions(administrator=True)
    async def getID(ctx):
        ''' Command which returns current channel ID'''
        await ctx.send(ctx.channel.id)

    bot.add_command(getID)


    @bot.command(name='whitelist', help=f"Usage: >whitelist <arg>. Requires a {role_Whitelist} role.", brief="Whitelists <arg> player on the corresponding channel's server.")
    @commands.has_any_role(*role_Whitelist)
    async def whitelist(ctx, *, mess):
        ''' Whitelists <args> to corresponding server as is defined in dockingPort.py if user has applicable role'''
        # Send command
        response = portSend(ctx.channel.id, f"whitelist add {mess}")
        await ctx.send(response) # Bot response
    @whitelist.error
    async def whitelist_error(error, ctx):
        if isinstance(error, CheckFailure):
            await bot.send_message(ctx.message.channel, "You do not have the necessary roles.")


    @bot.command(name='send', help="Usage: >send <arg>. Requires administrator permissions.", brief="Sends <arg> command to the corresponding channel's server.")
    @has_permissions(administrator=True)
    async def send(ctx, *, mess):
        ''' Sends <args> as /<args> to corresponding server as is defined in dockingPort.py if user has applicable role'''
        response = portSend(ctx.channel.id, mess)
        await ctx.send(response) # Bot response
    @send.error
    async def send_error(error, ctx):
        if isinstance(error, CheckFailure):
            await bot.send_message(ctx.message.channel, "You do not have the necessary permissions.")


def setup(bot):
    bot.add_cog(UtilsCog(bot))