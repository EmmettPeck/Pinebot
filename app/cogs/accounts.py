"""
Discord cog to manage tying game accounts to Discord user accounts using proof.

This proof is achieved by having the user send a randomized 5-digit code through
the corresponding services' chat to prove the discord user has access to the 
account, or the account is consenting to being linked to the service.

Authors: Emmett Peck (EmmettPeck)
Version: July 6th, 2022
"""

from datetime import datetime, timedelta, timezone
import json
import logging
import os
import random
import string

from discord.ext import commands

from embedding import embed_build
from database import DB
from dictionaries import make_link_key, make_link_account, make_user_account

# ------------------------------------------------------------------------------
def generateCode(length=5) -> str:
    """
    Returns a randomized link_key of digits and letters

    Parameters:
    ---

    `length`:`int`
        - Determines the length of the link_key
    """
    out = ""
    digits = random.choices(string.digits, k=length)
    letters = random.choices(string.ascii_letters, k=length)

    for digit in random.sample(digits + letters, length):
        out += digit

    return out
# Account Database -------------------------------------------------------------
class AccountsDB:

    def __init__(self) -> None:
        self.path = f'../../data/accounts/'
        self.accounts = self.load_accounts()

    def get_accounts(self) -> list:
        """
        Gets active Discord accounts
        """
        return self.accounts
    
    def find_account(self, id:int) -> dict:
        """
        Returns account corresponding with id

        `id`:`int`
            - The discord account id of the account to be found
        """
        for account in self.accounts:
            if account.get('id') is id:
                return account
        logging.debug(f'find_account: {id} not found.')
        return None

    def load_accounts(self) -> list:
        """
        Returns list of accounts.

        Loads accounts from filesystem self.path variable folder 
        """
        stats = []
        try:
            # Ensure directory existance
            if not os.path.exists(self.path):
                logging.debug(f"load_accounts creating file structure {self.path}")
                os.makedirs(self.path)

            # For file in folder
            for item in os.listdir(self.path):
                logging.debug(f"load_accounts loading item: {item}")
                with open(self.path+item) as f:
                    stats.append(json.load(f))
        except FileNotFoundError:
            logging.warning(f"No accounts found for load_accounts")
        logging.debug(f"Stats: {stats}")
        return stats

    def add_account(self, id:int):
        """
        Adds a new user account from an id

        `id`:`int`
            - The discord account id of the account to add
        """
        logging.debug(f"Adding account {id}")
        self.accounts.append(make_user_account(id))
    
    def save_account(self, id:int):
        """
        Saves account with corresponding id to filesystem

        `id`:`int`
            - The discord account id of the account to be saved
        """

        account = self.find_account(id)

        logging.debug(f"Saving account {id}")
        with open(self.path+str(id)+'.json', 'w') as f:
            json.dump(account, f, indent=2)

# Accounts Cog -----------------------------------------------------------------
class Accounts(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.accountDB = AccountsDB()
        
    def add_link_key(self, cid, link_key:dict) -> bool:
        """
        Adds a link-key dict to server cog to be listened for.

        Returns:
        --- 
        - `True` if player exists on server.
        - `False` if player is not found
        - `None` if server not found.

        Parameters:
        ---
        `cid`:`int`
            - Discord channel id of the corresponding server
        `link_key`:`dict`
            - Dictionary to add to server 
        """
        key_username = link_key.get('username')

        # Fetch Relevant Database from Cog
        for cog in DB.get_game_cogs():
            current = self.bot.get_cog(cog.split('.',1)[1].title())
            if current == None: continue

            # Loop searching for matching server cid, ensure player is on server
            for server in current.servers:
                if server.cid == cid:
                    for player in server.statistics:
                        try:
                            if key_username == player['username']:
                                server.link_keys.append(link_key)
                                return True
                        except KeyError as argument:
                            logging.error(argument)
                    logging.debug(f"add_link_key: player not found. {link_key}")
                    return False

        logging.warning(f"add_link_key: No matching server to {cid} found.")
        return None

    async def confirm_link(self, link_key:dict, server_name:str, uuid:str, game:str):
        """
        Successfully links a link_key account to requested user.
        
        Change gameaccountfile to include "linked" discord ID
        Add a Read/Write Lock to all database files
        """
        account_id = link_key.get('id')
        username = link_key.get('username')
        account = self.accountDB.find_account(account_id)
        
        # Add new accounts
        if account is None:
            self.accountDB.add_account(account_id)
            account = self.accountDB.find_account(account_id)
            if account is None:
                logging.critical(f'confirm_link: Unable to find account after adding. {link_key}')
                return
        
        # Add link
        link = make_link_account(
            server=server_name, username=username, uuid=uuid, game=game)
        account['linked'].append(link)
        
        self.accountDB.save_account(account_id)

        # Inform User
        user = await self.bot.fetch_user(link_key['id'])
        await user.send(embed=embed_build(message=f"Successfully Linked {game} Account {link_key['username']}",icon="🔑"))
        logging.info(f"Successfully linked {username} to {account_id}")
# COMMANDS ---------------------------------------------------------------------

# LINK
    @commands.command(
        name='link',
        brief='link a non-discord account to your account.',
        help='Link a whitelisted account, enabling analytics. Usage '
            '`>link <account-name>` in a gameserver channel. Case Sensitive.')
    async def link(self, ctx, name):
        logging.info(f"{ctx.author.name} invoked command `>link {name}` in {ctx.channel.name}:{ctx.channel.id}")

        # Ensure is sent in a channel with a linked gameserver
        flag = False
        for container in DB.get_containers():
            if ctx.channel.id == container.get("channel_id"):
                flag = True
        if not flag:
            logging.info(f"link command: server not appropriate")
            await ctx.reply(
                embed=embed_build(message="Please use command in a gameserver-linked channel."),
                mention_author=False
            )
            return
 
        # Check if is already linked to any account 
            # (Ensures matching servername and username)
        for account in self.accountDB.get_accounts():
            try:
                for subaccount in account['linked']:
                    if (DB.get_server_name(cid=ctx.channel.id) == subaccount['server']) and (subaccount["username"] == name):
                        user = await self.bot.fetch_user(account['id'])
                        logging.info(f"link command: {name} already linked to {subaccount['username']}")
                        
                        # Inform user account is already linked
                        await ctx.reply(
                            embed=embed_build(
                                message=f"Account {name} is already linked to {user.name}#{user.discriminator}", 
                                icon='🖇'
                            ),
                            mention_author=False
                        )
                        return
            except KeyError as e:
                logging.error(f"Link Command: account link check failed: {e}")

        link_key = generateCode()
        expires = datetime.utcnow().replace(tzinfo=timezone.utc)+timedelta(minutes=5)
        
        # Attempt to add link-key
        result = self.add_link_key(
            cid=ctx.channel.id,
            link_key=make_link_key(
                username=name,
                keyID=link_key,
                id=ctx.author.id,
                expires=expires
            )
        )

        if result == True: 
            logging.info(f"link command: {name} added link-key `{link_key}` to link to {ctx.author.name}")
            # Direct Message Link-Key
            await ctx.author.send(
                embed=embed_build(
                    message=f"Your link-key is `{link_key}`",
                    description=f"Send this in {ctx.channel.name}'s ingame chat to link {name} to your account.\n"
                    f"Key expires in 5 minutes at <t:{int(round(expires.timestamp()))}:t>",
                    icon="🔑"
                )
            )
        
        elif result == False: 
            logging.info(f"link command: {name} not recognized.")
            # Inform player that name was not recognized
            await ctx.reply(
                embed=embed_build(
                    icon="❔",
                    message=f"Player {name} is not recognized on Pineserver.",
                    description="Usernames are Case-Sensitive. Have they played on Pineserver before?"
                ),
                mention_author=False
            )
        
        # Error Cases
        elif result == None:
            logging.error("link command: Server Not Found.")
        else:
            logging.error('link command: Fallthrough')
    @link.error
    async def link_error(self, ctx, error):
        logging.debug(f"Link Command Error: {error}")
        logging.debug(f"Link Command Error Type: {type(error)}")
        if isinstance(error, commands.MissingRequiredArgument):
            # Needs Username Parameter Message
            await ctx.reply(
                embed=embed_build(
                    icon="⚠️",
                    message="Missing Username To Link -- `>help link` for more.", 
                    timestamp=False
                ),
                mention_author=False
            )

# UNLINK
    @commands.command(
        name="unlink",
        brief='Unlink a account from your Discord user.',
        help='Unlink a whitelisted account. Useful for'
       ' transfering to other accounts. Usage `>unlink <account-name>` in a'
       ' gameserver channel. Case Sensitive.'
    )
    async def unlink(self, ctx, name):
        i = 0

        # Look for account in accounts, unlinking account if found
        for account in self.accountDB.get_accounts():
            try:
                if ctx.author.id == account['id']: # Ensure account is authors
                    for subaccount in account['linked']: 
                        if (DB.get_server_name(cid=ctx.channel.id) == subaccount['server']) and (subaccount["username"] == name):
                            user = await self.bot.fetch_user(account['id'])
                            logging.debug(f'Unlinking account {name} from {user.name}#{user.discriminator}')

                            self.accountDB.accounts[i]['linked'].remove(subaccount)
                            self.accountDB.save_account(ctx.author.id)
                            
                            # Inform User Via Direct Message
                            await user.send(
                                embed=embed_build(
                                    message=f"Successfully removed {name} from {user.name}#{user.discriminator}", 
                                    icon='🖇'
                                    )
                                )
                            return
            except KeyError as e:
                logging.error(f"Unlink Command: account link check failed: {e}")
            i+=1
        
        # Fallthrough Message, Inform in channel that no account was found.
        await ctx.reply(
            embed=embed_build(
                icon="⚠️",
                message=f"No account named `{name}` was found linked to"
                f" {ctx.author.name}#{ctx.author.discriminator}",
                timestamp=False
            ),
            mention_author=False
        )
    @unlink.error
    async def unlink_error(self, ctx, error):
        logging.debug(f"Unlink Command Error: {error}")
        logging.debug(f"Unlink Command Error Type: {type(error)}")
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply(
                embed=embed_build(
                    icon="⚠️",
                    message="Missing Username To Unlink -- `>help link` for more.", 
                    timestamp=False
                ),
                mention_author=False
            )

# 
def setup(bot):
    """
    Setup conditon for discord.py cog
    """
    bot.add_cog(Accounts(bot))