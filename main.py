#   Pinebot
#   By: Emmett Peck
#
#   A simple discord bot to allow remote whitelisting through discord.
#   To be run on linux server alongside dockerized servers.

#   TO/DO
#   -   Help Command
#   -   Check Roles

import os
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, CheckFailure
from dotenv import load_dotenv
from dockingPort import portSend

load_dotenv()
bot = commands.Bot(command_prefix='>') # Set Prefix

role_Whitelist = {'Member', 'Moderator', 'Liam'} #Permissible Roles

# Hello!
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('hello') | message.content.startswith('hi'):
        await message.channel.send('Hello!')

    await bot.process_commands(message)

# >whitelist
@bot.command(name='whitelist', help=f"Usage: >whitelist <arg>. Requires a {role_Whitelist} role.", brief="Whitelists <arg> player on the corresponding channel's server.")
@commands.has_any_role(role_Whitelist)
async def whitelist(ctx, *, mess):
 
    # Check Roles
    if not discord.ext.commands.has_any_role(role_Whitelist):
        return
    
    # Send command
    response = portSend(ctx.channel.id, f"whitelist add {mess}")
    await ctx.send(response) # Bot response
@whitelist.error
async def whitelist_error(error, ctx):
    if isinstance(error, CheckFailure):
        await bot.send_message(ctx.message.channel, "You do not have the necessary roles.")

# >send
@bot.command(name='send', help="Usage: >send <arg>. Requires administrator permissions.", brief="Sends <arg> command to the corresponding channel's server.")
@has_permissions(administrator=True)
async def send(ctx, *, mess):

    response = portSend(ctx.channel.id, mess)

    await ctx.send(response) # Bot response
@send.error
async def send_error(error, ctx):
    if isinstance(error, CheckFailure):
        await bot.send_message(ctx.message.channel, "You do not have the necessary permissions.")



bot.run(os.getenv('TOKEN'))