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
import pymongo

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

# Accounts Cog -----------------------------------------------------------------
class Accounts(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        
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
            cog_name = cog.split('.',1)[1].title()
            query = DB.mongo['Servers'][cog_name].find_one({'cid':cid})
            if query is None:
                continue

            servers_id = query.get('_id')
            server_name = query.get('name')
            link_key['servers_name'] = server_name
            link_key['servers_id'] = servers_id
            

            # Ensure Player is present in server
            query = DB.mongo[cog_name][server_name].find_one({'username':key_username})
            if query is None: 
                logging.debug(f"add_link_key: player not found. {link_key}")
                return False

            # Add Key To Server
            DB.mongo['Servers'][cog_name].update_one({'_id':servers_id},{'$addToSet':{link_key}})
            return True

        logging.warning(f"add_link_key: No matching server to {cid} found.")
        return None

    async def confirm_link(self, link_key:dict, uuid:str, game:str):
        col = DB.mongo['Guilds']['Pineserver']
        discord_id = link_key.get('id')
        username = link_key.get('username')
        account = col.find_one({'id':discord_id})
        account_id = account.get('_id')
        
        # Add new accounts
        if account is None:
            query = col.insert_one({make_user_account(discord_id)})
            account_id = query.inserted_id
        
        # Add link
        link = make_link_account(username=username, uuid=uuid, game=game, server_name=link_key['server_name'], _id=link_key['servers_id'])
        
        query = col.update_one({'_id':account_id},{'$addToSet':{'linked':link}})
        if query.acknowledged:
            # Update linked tag in playerfile TODO SERVERNAME
            DB.mongo['Servers'][game].update_one({'uuid':uuid,'username':username},{'$set':{'linked':account_id}})

            # Inform User
            user = await self.bot.fetch_user(discord_id)
            await user.send(embed=embed_build(message=f"Successfully Linked {game} Account {username}",icon="🔑"))
            logging.info(f"Successfully linked {username} to {discord_id}")
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
        for cog in DB.get_game_cogs():
            cog_name = cog.split('.',1)[1].title()
            query = DB.mongo['Servers'][cog_name].find_one({'cid':ctx.channel.id})
            if query is None:
                continue
            flag = True
            break
        # If unlinked server
        if not flag:
            logging.info(f"link command: channel not appropriate")
            await ctx.reply(
                embed=embed_build(message="Please use command in a gameserver-linked channel."),
                mention_author=False
            )
            return
 
        # Check if is already linked to any account 
        for linked in DB.mongo['Guilds']['Pineserver'].find({'linked':{'username':name,'game':cog_name}}):
            user = await self.bot.fetch_user(linked['id'])
            logging.info(f"link command: {name} already linked to {user.name}")
            
            # Inform user account is already linked
            await ctx.reply(
                embed=embed_build(
                    message=f"Account {name} is already linked to {user.name}#{user.discriminator}", 
                    icon='🖇'
                ),
                mention_author=False
            )
            return

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
        acctcol = DB.mongo['Guilds']['Pineserver']

        # Match cid to server TODO Potentially Useless? {First Two Comment Blocks}
        flag = False
        for cog in DB.get_game_cogs():
            cog_name = cog.split('.',1)[1].title()
            query = DB.mongo['Servers'][cog_name].find_one({'cid':ctx.channel.id})
            if query is None:
                continue
            flag = True
            break
        # Improper Channel Catch
        if not flag:
            logging.info(f"link command: channel not appropriate")
            await ctx.reply(
                embed=embed_build(message="Please use command in a gameserver-linked channel."),
                mention_author=False
            )
            return
        
        # Get Account document from discord author id
        query = acctcol.find_one({'id':ctx.author.id})
        if query is None:
            # Prompt that user was not found
            await ctx.reply(
                embed=embed_build(
                    icon="⚠️",
                    message=f"No account named `{name}` was found linked to"
                    f" {ctx.author.name}#{ctx.author.discriminator}",
                    timestamp=False
                ),
                mention_author=False
            )
        
        # Ensure linked account's account is linked to server 
        for account in query['linked']:
            # Attempt to find PlayerData in server
            col = DB.mongo[account['game']][account['server_name']]
            if query is None: continue

            # Get ID of PlayerData document from Account document
            acct_doc_id = query['linked']
            
            # Remove link dict, Remove link_id from playerdata
            col.update_one({'_id':account['servers_id']},{'$set':{'servers_id':None}})
            acctcol.update_one({'_id':acct_doc_id},{'$pop':{"linked":account['servers_id']}})

            # Find User & Prompt
            user = await self.bot.fetch_user(account['id'])
            logging.debug(f'Unlinked account {name} from {user.name}#{user.discriminator}')

            # Inform User of Unlink Via Direct Message
            await user.send(
                embed=embed_build(
                    message=f"Successfully removed {name} from {user.name}#{user.discriminator}", 
                    icon='🖇'
                    )
                )
            return
        logging.error('Linked account\'s account not present in server.')
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