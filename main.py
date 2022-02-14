#   Pinebot
#   By: Emmett Peck
#
#   A simple discord bot to allow remote whitelisting through discord.
#   To be run on linux server alongside dockerized servers.

#   TO/DO
#   -   Help Command
#   -   CHANNEL NOT FOUND/WRONG CHANNEL MSG
#   -   Check Roles
#   -   Command send function from serverID & command

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import subprocess

load_dotenv()
bot = commands.Bot(command_prefix='#', help_command=None) # Set Prefix


role_Whitelist = {'Member', 'Moderator'} #Permissible Roles
mc_Channels = [ # Channel List of dictionaries
    {'name':"mc", 'channel_id':942193852058574949, 'docker_name':"build_main_2021_1"},
    {'name':"liam", 'channel_id':942241180421328896, 'docker_name':"build_liam_2022_1"}
]


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('hello') | message.content.startswith('hi'):
        await message.channel.send('Hello!')

    await bot.process_commands(message)


@bot.command(name='whitelist')
async def whitelist(ctx, *, mess):
 
    # Check Roles
    if not discord.ext.commands.has_any_role(role_Whitelist):
        return
    

    channelID = ctx.channel.id  # Check Channel to determine server ID to execute through

    for channel in mc_Channels: # Check all channels in list for channel ID, then execute if found.
            if channelID == channel.get('channel_id'):

                # Command Execution Via Commandline through Docker
                dockerName = channel.get('docker_name')
                resp_bytes = subprocess.Popen(f'docker exec {dockerName} rcon-cli /whitelist add {mess}', stdout=subprocess.PIPE, shell=True, executable="/bin/bash").stdout.read()
                resp_str = resp_bytes.decode(encoding="utf-8", errors="ignore")
                print(f"Sent command /whitelist add {mess} to {dockerName}")
                print(f'--- {resp_str}')
            else:
                # CHANNEL NOT FOUND/WRONG CHANNEL MSG
                return

    await ctx.send(resp_str) # Bot response

@bot.command(name='send')
async def whitelist(ctx, *, mess):
 
    # Check Roles
    if not discord.ext.commands.has_any_role(role_Whitelist):
        return


    channelID = ctx.channel.id  # Check Channel to determine server ID to execute through

    for channel in mc_Channels: # Check all channels in list for channel ID, then execute if found.
            if channelID == channel.get('channel_id'):

                # Command Execution Via Commandline through Docker
                dockerName = channel.get('docker_name')
                resp_bytes = subprocess.Popen(f'docker exec {dockerName} rcon-cli /{mess}', stdout=subprocess.PIPE, shell=True, executable="/bin/bash").stdout.read()
                resp_str = resp_bytes.decode(encoding="utf-8", errors="ignore")
               
                # Console Logging
                print(f"Sent command /{mess} to {dockerName}")
                print(f'--- {resp_str}')
            else:
                # CHANNEL NOT FOUND/WRONG CHANNEL MSG
                return

    await ctx.send(resp_str) # Bot response


bot.run(os.getenv('TOKEN'))
