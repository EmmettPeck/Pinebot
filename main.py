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
from dotenv import load_dotenv
from dockingPort import portSend

load_dotenv()
bot = commands.Bot(command_prefix='>') # Set Prefix

role_Whitelist = {'Member', 'Moderator'} #Permissible Roles

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('hello') | message.content.startswith('hi'):
        await message.channel.send('Hello!')

    await bot.process_commands(message)


@bot.command(name='whitelist', help="Usage: >whitelist <arg>.", brief="Whitelists <arg> player on the corresponding channel's server.")
async def whitelist(ctx, *, mess):
 
    # Check Roles
    if not discord.ext.commands.has_any_role(role_Whitelist):
        return
    
    # Send command
    response = portSend(ctx.channel.id, f"whitelist add {mess}")
    await ctx.send(response) # Bot response

@bot.command(name='send', help="Usage: >send <arg>.", brief="Sends <arg> command to the corresponding channel's server.")
async def whitelist(ctx, *, mess):
 
    # Check Roles
    if not discord.ext.commands.has_any_role(role_Whitelist):
        return
        
    response = portSend(ctx.channel.id, mess)

    await ctx.send(response) # Bot response


bot.run(os.getenv('TOKEN'))
