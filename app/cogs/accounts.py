"""
Discord cog to manage tying game accounts to Discord user accounts using proof.

Authors: Emmett Peck (EmmettPeck)
Version: July 1st, 2022
"""

from datetime import datetime, timedelta
import json
import logging
import os
import random
import string

from discord.ext import commands

from embedding import embed_build
from database import DB
from dictionaries import make_link_key

# ------------------------------------------------------------------------------
def generateCode(length=5):
    """
    Returns a randomized link_key of digits and letters

    Parameters:
    ---

    `length`:`int`
        - Determines the length of the link_key
    """
    digits = random.choices(string.digits, k=length)
    letters = random.choices(string.ascii_letters, k=length)

    return random.sample(digits + letters, length)

# ------------------------------------------------------------------------------
class Analytics(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.accounts = self.load_accounts()

# Data Handling ----------------------------------------------------------------
    def find_account(self):
        pass

    def load_accounts(self) -> list:
        """
        Returns: list of files in data/accounts/ loaded
        """
        stats = []
        try:
            # Ensure directory existance
            path = f'../../data/accounts/'
            if not os.path.exists(path):
                logging.debug(f"load_accounts creating file structure {path}")
                os.makedirs(path)

            # For file in folder
            for item in os.listdir(path):
                logging.debug(f"load_accounts loading item: {item}")
                with open(path+item) as f:
                    stats.append(json.load(f))
        except FileNotFoundError:
            logging.warning(f"No accounts found for load_accounts")
            return stats
        else:
            return stats

    def save_account():
        pass

    #---------------------------------------------------------------------------
    def add_link_key(self, cid, link_key:dict) -> bool:
        """
        Adds a link-key dict to server cog to be listened for.

        Returns:
        --- 
        - `True` if player exists on server.
        - `False` if player is not found
        - `None` if server not found.
        """
        key_username = link_key.get('username')

        for cog in DB.get_game_cogs():
            current = self.bot.get_cog(cog.split('.',1)[1].title())
            if current == None: continue

            # Loop searching for matching server cid, ensure player is on server
            for server in current.servers:
                if server.cid == cid:
                    for player in server.statistics:
                        if key_username is player.get('username'):
                            server.link_keys.append(link_key)
                            logging.debug(f"add_link_key: adding {link_key} to {cid}.")
                            return True
                    logging.debug(f"add_link_key: player not found. {link_key}")
                    return False

        logging.warning(f"add_link_key: No matching server to {cid} found.")
        return None

    async def confirm_link(link_key:dict):
        """
        Successfully links a link_key account to requested user.
        
        If player not present, add player
        Change gameaccountfile to include "linked" discord ID
        Add a Read/Write Lock to all database files
        """
        pass

# COMMANDS ---------------------------------------------------------------------
    @commands.command(
        name='link',
        brief='link a non-discord account to your account',
        help='Link a whitelisted account, enabling analytics. Usage '
            '`>link <account-name>` in a gameserver channel. Case Sensitive.')
    async def link(self, ctx, name:str):
        logging.info(f"{ctx.author.name} invoked command `>link {name}` in {ctx.channel.name}:{ctx.id}")

        # Ensure is sent in a channel with a linked gameserver
        flag = False
        for container in DB.get_containers():
            if ctx.id == container.get("channel_id"):
                flag = True
        if not flag:
            logging.info(f"link command: server not appropriate")
            await ctx.author.send(embed=embed_build(
                message="Please use command in a gameserver-linked channel."))
            return
 
        # Check if is already linked to any account 
            # (Ensures matching servername and username)
        for account in self.accounts:
            for subaccount in account.accounts: 
                if (DB.get_server_name(cid=ctx.id) == subaccount.get('servername') 
                and subaccount.get("name") == name):
                    logging.info(f"link command: {name} already linked to "
                        f"{account.get('name')}")
                    await ctx.send(embed=embed_build(
                        message=f"Account {name} is already linked to {account.get('name')}"))
                    return

        link_key = generateCode()
        
        # Attempt to add link-key
        result = self.add_link_key(cid=ctx.id,link_key=make_link_key(
            username=name,
            keyID=link_key,
            expires=datetime.utcnow()+datetime.timedelta(minutes=5)))

        # Direct Message link_key to user if successfully added
        if result == True: 
            logging.info(f"link command: {name} added link-key `{link_key}` to link to {ctx.author.name}")
            await ctx.author.send(embed=embed_build(
                message=f"Your link-key is `{link_key}`",
                description=f"Send this in {ctx.channel.name}'s server chat to link your account."))
        
        # If unsuccessful, inform player
        elif result == False: 
            logging.info(f"link command: {name} not recognized.")
            await ctx.send(embed=embed_build(
                message=f"Player {name} is not recognized on Pineserver.",
                description="Usernames are Case-Sensitive. Have they played on a server?"))
        
        # Error Cases
        elif result == None:
            logging.error("link command: Server Not Found.")
        else:
            logging.error('link command: Fallthrough')

# ------------------------------------------------------------------------------
def setup(bot):
    """
    Setup conditon for discord.py cog
    """
    bot.add_cog(Analytics(bot))