#   Pinebot
#   By: Emmett Peck
#
#   A simple discord bot to allow remote whitelisting through discord.
#   To be run on linux server alongside dockerized servers.

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
bot = commands.Bot(command_prefix='/', help_command=None) # Set Prefix


role_Whitelist = {'Member', 'Moderator'} #Permissible Roles
mc_Channels = [ # Channel List of dictionaries
    {'name':"mc", 'channel_id':942193852058574949, 'docker_name':"build_main_2021_1"},
    {'name':"liam", 'channel_id':942241180421328896, 'docker_name':"build_liam_2022_1"}
]


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('hello'):
        await message.channel.send('Hello!')

    await bot.process_commands(message)


@bot.command(name='whitelist')
async def whitelist(ctx, *, mess):
    usrname = mess
    finalmsg = mess + " has been whitelisted."
    
    # Check Roles
    if not discord.ext.commands.has_any_role(role_Whitelist):
        return
       
    # Check Channel to determine server ID to execute through
    channelID = ctx.channel.id

    # Check all channels in list for channel ID, then execute if found.
    for channel in mc_Channels:
            if channelID == channel.get('channel_id'):

                # Command Execution Via Commandline through Docker
                dockerName = channel.get('docker_name')
                os.system(f'cmd /k "docker exec {dockerName} rcon-cli /whitelist add {usrname}"')
                print(f"{mess} has been whitelisted in {dockerName}.")

    await ctx.send(finalmsg) #sends finalmsg to the discord channel


bot.run(os.getenv('TOKEN'))
