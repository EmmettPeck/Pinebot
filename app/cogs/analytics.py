"""
Discord cog to handle Account-Link and analytics, including accessing of server 
playtime information.

This module holds commands used by users to interface with information gathered
by pinebot. Calls methods and provides conditions for multiple input conditions.

Authors: Emmett Peck (EmmettPeck)
Version: May 27th, 2022
"""

from datetime import datetime, timedelta
import json
import logging
from operator import ge
import os
import random
import string

from discord.ext import commands

import analytics_lib
from embedding import embed_build, embed_playtime
from database import DB

def generateCode(length=5):
    """
    Returns a randomized code of digits and letters

    Parameters:
    ---

    `length`:`int`
        - Determines the length of the code
    """
    digits = random.choices(string.digits, k=length)
    letters = random.choices(string.ascii_letters, k=length)

    return random.sample(digits + letters, length)
# ------------------------------------------------------------------------------
def load_accounts() -> list:
    """
    Returns: list of files in data/accounts/ loaded
    """
    stats = []
    try:
        # Ensure directory existance
        path = f'../../data/accounts/'
        if not os.path.exists(path):
            logging.info(f"load_accounts creating file structure {path}")
            os.makedirs(path)

        # For file in folder
        for item in os.listdir(path):
            logging.info(f"load_accounts loading item: {item}")
            with open(path+item) as f:
                stats.append(json.load(f))
    except FileNotFoundError:
        logging.warning(f"No accounts found for load_accounts")
        return stats
    else:
        return stats
# ------------------------------------------------------------------------------
def get_server_name(cid):
    '''
    Returns corresponding container name matching cid
    '''
    for container in DB.get_containers():
        if container.get('channel_id') == cid:
            return container.get('name')

class Analytics(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.accounts = load_accounts()

    #---------------------------------------------------------------------------
    def add_link_key(self, cid, link_key:dict):
        """
        Returns True if successful, False if player doesn't exist, None if server not found.
        
        Adds a link-key dict (Username, keyID, Timestamp) to server cog to be listened for.
        """
        for cog in DB.get_game_cogs():
                current = self.bot.get_cog(cog.split('.',1)[1].title())
                if current == None: continue

                # Loop searching for matching server cid
                for server in current.servers:
                    if server.cid == cid:
                        # Ensure player exists on server (return False case)
                            # TODO
                        # Add link key
                        server.link_keys.append(link_key)
                        return True

        logging.warning(f"add_link_key: No matching server to {cid} found.")

    # Account Link -------------------------------------------------------------

    # Apply Command (Whitelist tie to account without ensured link)

    @commands.command(
        name='link',
        brief='link a non-discord account to your account',
        help='Link a whitelisted account, enabling analytics. Usage `>link <account-name>` in a gameserver channel. Case Sensitive.')
    async def link(self, ctx, name:str):
        logging.info(f"{ctx.author.name} invoked link command `>link {name}` in {ctx.channel.name}:{ctx.id}")

        # Ensure is sent in container channel
        flag = False
        for container in DB.get_containers():
            if ctx.id == container.get("channel_id"):
                flag = True
        if not flag:
            logging.info(f"link command: server not appropriate")
            await ctx.author.send(embed=embed_build(
                message="Please use command in a gameserver channel."))
            return
 
        # Check if is already linked to any account (Ensures matching servername and username)
        for account in self.accounts:
            for subaccount in account.accounts: 
                if (get_server_name(cid=ctx.id) == subaccount.get('servername')) and (subaccount.get("name") == name):
                    logging.info(f"link command: {name} already linked to {account.get('name')}")
                    await ctx.send(embed=embed_build(message=f"Account {name} is already linked to {account.get('name')}"))
                    return

        code = generateCode()
        
        # Attempt to add link-key
        result = self.add_link_key(cid=ctx.id,
            link_key={'name':name,'keyID':code,'time':datetime.utcnow()})

        # DM code to user
        if result == True: # If succesfully added, inform player
            logging.info(f"link command: {name} added link-key `{code}` to link to {ctx.author.name}")
            await ctx.author.send(embed=embed_build(
                message=f"Your link-key is `{code}`",
                description=f"Send this in {ctx.channel.name}'s server chat to link your account."))
        elif result == False: # If unsuccessful, inform player
            logging.info(f"link command: {name} not recognized.")
            await ctx.send(embed=embed_build(message=f"Player {name} is not recognized on Pineserver."description="Usernames are Case-Sensitive. Have they played on a server?"))
        elif result == None:
            logging.error("link command: Server Not Found.")
        else:
            logging.error('link command: Fallthrough')
         
    @commands.command(
        name='playtime', 
        help=('Returns playtime on pineservers.' 
            '>playtime <player-name> <server-name>,' 
            'otherwise returns total of player.'),
        brief='Get total playtime.')
    async def playtime(self, ctx, name:str=None, server:str=None):
        """
        Prints playtime information to channel
        
        Gets playtime for requesting user if no args provided, 
        otherwise gathers playtime for other user. If server is provided,
        Gathers playtime of username or matching UUID in that server.

        Parameter ctx: discord channel used by discord.py
        Preconditon: ctx is a discord channel

        Parameter name: Username to search for in server if provided, 
        otherwise looks for discord user w/ linked accounts.
        Precondition: name is a str

        Parameter server: Server to get playtime from.
        Precondition: server is an str
        """
        logging.info(f"Gathering playtime for {name} {server}")
        # If name not provided, prompt user and return.
        if name == None:
            await ctx.send(
                "Please provide a playername,"
                " >playertime <name> <optional-server>")
            return

        # If server not provided, prompt user and return.
        if server == None:
            await ctx.send(
                "Please provide a server, "
                ">playertime <name> <optional-server>")
            return

        # TODO If server not provided, print total w/ list of top servers
        if server == None:
            total = analytics_lib.handle_playtime(
                bot=self.bot,
                server_name=server, 
                request=name)
            await ctx.send(
                embed = embed_build(
                reference=ctx.author,
                message=
                    f"{name} has played for `{analytics_lib.td_format(total)}` "
                    "across all servers."))
            return

        # Look for server. found? print total: prompt user of input error. -----
        else: 
            # Get Playtime From Server
            single = analytics_lib.handle_playtime(
                bot=self.bot, 
                request=name,
                server_name=server)

            # Print Playtime
            if single:
                await ctx.send(
                    embed = embed_playtime(
                        reference=ctx.author, 
                        username=name,
                        total_playtime=single.get('playtime'), 
                        dict_list=[single]))
                logging.info("Playtime command complete")
                return

            # If Playtime present, but empty, prompt user
            if single == timedelta():
                await ctx.send(
                    embed = embed_build(
                        reference=ctx.author,
                        message=
                        "Player & Server recognized, yet no tengo playtime on `"
                        f"{server}`."))

            # If None
            elif single == None:
                await ctx.send(
                    embed = embed_build(
                        reference=ctx.author,
                        message=
                        f"Either player or server not found. Are you sure `"
                        f"{server}` is a server and `{name}` has played on that" 
                        "server? Playernames and servernames are case sensitive"))

            # For other false evaluating conditons, notify developer.
            else:
                logging.ERROR(f"ERROR: Other false evaluating condition in analytics single == {single}")

def setup(bot):
    """
    Setup conditon for discord.py cog
    """
    bot.add_cog(Analytics(bot))
