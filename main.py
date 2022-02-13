import os
import discord
from discord.ext import commands
#from mcrcon import MCRcon
from dotenv import load_dotenv

load_dotenv()
bot = commands.Bot(command_prefix='/', help_command=None) # Set Prefix
role_Whitelist = {'Member', 'Moderator'}

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('hello'):
        await message.channel.send('Hello!')

    await bot.process_commands(message)

@bot.command(name='whitelist')
async def whitelist(ctx, *, mess):
    usrname = mess #this is the username that the discord user types after /whitelist
    finalmsg = mess + " has been added" #adds usrname and has been added to the varible finalmsg
    
    # Check Roles
    if not discord.ext.commands.has_any_role(role_Whitelist):
        return
       
    # Check Channel to determine server ID

    os.system('cmd /k "COMMAND"')
    ''' # MCRcon Solution to interact with servers
    with MCRcon(os.getenv('HOSTNAME'), os.getenv('RCON_PASS')) as mcr: #send the whitelist command to minecraft server
        resp = mcr.command("/whitelist add " + usrname)'''

    await ctx.send(finalmsg) #sends finalmsg to the discord channel


# Test/Run
bot.run(os.getenv('TOKEN'))
