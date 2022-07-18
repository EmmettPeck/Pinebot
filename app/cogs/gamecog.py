"""
Module containing parent class for gamecog framework.

This module is to be used with GameCog as a parent class for a gamespecific cog 
implementation. Integrates a linked discord chat channel with game server chat
channels hosted in a docker network with Pinebot. Provides a framework for 
logging of in-game msgs, logging of playtime, keeping unique updated channel 
headers, logging online players, and storing of player-specific data.

Contains loops, filters, and send commands for linking discord & game chat 
channels using docker logs.

Authors: Emmett Peck (EmmettPeck)
Version: July 17th, 2022
"""

import asyncio
import logging
from enum import Enum

from discord.ext import commands, tasks
import discord
from datetime import timezone, datetime
import analytics_lib
from database import DB
from embedding import embed_message
from messages import MessageType
from hash import get_hash
from dictionaries import get_msg_dict, make_statistics


@classmethod
def class_name(cls):
    return cls.__name__

class Identifier(Enum):
    """
    Used for UUID/Username implementation, changing handling, sorting, and addition conditons based on information storage conditions

    - Centralized UUIDs (Steam, Minecraft, etc) - On command/join get UUID, if UUID matches old UUID with different name change that name to the new name.
    - Noncentralized UUID Unchangable Name - Search by name, save UUID when available.
    - Noncentralized UUID Changable Name - Allows namechange command (with special condition that leverages UUID when available?)
    - No UUID Unchangable Name - Search by name, no worries
    - No UUID Changable Name -- Allows namechange command
    """
    CENTRALIZED = 1
    NONCENTRALIZED_UNCHANGABLE = 2
    NONCENTRALIZED_CHANGABLE = 3
    NO_UUID_UNCHANGABLE = 4
    NO_UUID_CHANGABLE = 5

@classmethod
class GameCog(commands.Cog):
    """
    A class implementing the basic loops and instance methods used to integrate
    a dockerized gameserver with chat-link using discord, discord commands that
    send commands to dockerized server, or log player activity & store player
    specific information.

    Attributes
    ---
    `bot` : `discord.bot`
        -- The current discord bot instance
    `servers` - `list(Server)`
        -- List of version matching servers
    """

    def __init__(self, bot):
        self.bot = bot
        self.load_servers()

    @commands.Cog.listener()
    async def on_ready(self):
        for server in self.servers:
            await self.header_update(server=server)

#===========================To Be Overloaded====================================
#   Functions to be overloaded by children for unique GameCog implementations
# Implementation Getters (Affects function of main functions)

    def get_uuid(self, server:dict, username:str, uuid=None) -> str:
        """
        Returns: UUID of username if present, otherwise returns none.
        
        To be overloaded by GameCog children.     
        """

        # Noncentralized_Nonchangable: Search for dict by Username, return matching uuid
        if self.get_identifier() is Identifier.NONCENTRALIZED_UNCHANGABLE:
            result = DB.mongo[class_name()][server['name']].find_one({'username':username})
            if result is None:
                logging.debug(f'get_uuid found no matching user for {username}')
                return None
            else:
                return result.get('uuid')

        # Centralized: Get uuid from name, search for matching uuid, update username if different
        if self.get_identifier() is Identifier.CENTRALIZED:
            result = DB.mongo[class_name()][server['name']].find_one({'uuid':uuid})
            if result is None:
                logging.debug(f'get_uuid found no matching uuid for {username}:{uuid}')
                return uuid
            else:
                if result['username'] != username:
                    DB.mongo[class_name()][server['name']].update_one({'_id':result['_id']},{"$set":{'username':username}}) 
                return uuid
        return None

    def get_identifier(self)-> Identifier:
        """
        Returns: Identifier structure of cog information, see Identifier Enum for 
        details.

        To be overloaded by GameCog children.
        """
        return None


    def get_player_list(self, server:dict) -> list:
        """
        Does nothing. To be overloaded by GameCog children.

        For versions without a getlist function, returns None
        Called on cog init for each server

        `server`: `dict`
            -- dict to reference
        """

        pass

    def get_username_fixes(self) -> tuple:
        """
        Returns tuple of chat message prefix and suffix for usernames

        To be overloaded by GameCog children.
        """
        return ("<",">")

    def is_player_online(self, server:dict, playername:str = None) -> bool:
        """
        Returns: True if playername matches element in online_player list

        To be overloaded by GameCog children.
        Not certain, as not all games get online players on launch

        Parameters:
        ---
        `server` : `dict`
            -- Server to search in
        `playername` : `str`
            -- Playername to search online_players for
        """
        if playername:
            for player in server['online_players']:
                if playername == player: return True
            return False
        else:   
            raise NotImplementedError(
                "is_player_online: Called without True playername.")
                
    def send_message(self, server:dict, message:str):
        """
        Interface for Discord->Server Chatlink messaging.

        Does nothing. To be overloaded by GameCog children.

        Sends Message To gameserver based on version implementation:
         - If no consolebased say command, does nothing.

        Parameters:
        ---
        `server` : `dict`
            -- Server to to reference
        `message` : `str`
            -- Message to format
        """

        logging.warning(f"{message} GameCog send_message not implemented.")

    async def filter(self, server:dict, message:str):
        """
        Filters logs using versionbased conditions by type and content. 
        Adds leaves/joins to connectqueue and messages to message queue.
        
        To be overloaded by GameCog Children

        Parameters:
        ---
        `server` : `dict`
            -- server to reference

        `message` : `str`
            -- Message string to filter using conditions
        """
        # Build Dictionary
        dict = get_msg_dict(
            username="__default__",
            message=message,
            type=MessageType.MSG,
            color=discord.Color.blue()
        )

        # Messages are sent 
        if dict:
            msg_type = dict.get('type')
            if msg_type == MessageType.JOIN or msg_type == MessageType.LEAVE:
                await self.handle_connection(
                    server=server,
                    connection=dict,
                )
            await self.handle_message(message=dict)
        
#---------------------------- Headers ------------------------------------------
    async def header_update(self,server:dict):
        """
        Updates header with server playercount & docker status

        Parameters:
        ---
        `server` : `dict`
            -- Server object to update the linked channel header for
        """

        # Check Docker Status (Running vs Not)
        if (DB.client.containers.get
        (server["docker_name"]).status.title().strip() == 'Running'):
            status = "Online"
        else:
            status = "Offline"
        await self.update_channel_header(server=server, container_status=status)
    
    async def update_channel_header(self, server:dict, container_status:str):
        """
        Uses implemented formatting to update linked channel heading.

        Contains formatting for channel_header, overload this to change.

        Parameters:
        ---
        `server` : `Server`
            -- Server object to update the linked channel header for
        `container_status` : `str`
            -- current container status
        """
        ctx = self.bot.get_channel(server.cid)
        await ctx.edit(
            topic=f"{server['name']} | {server['version']} | "
                f"{len(server['online_players'])}/"
                f"{server['player_max'] if server['player_max'] > -1 else 'ꝏ'}"
                f" | Status: {container_status}")
        logging.debug(f"Updated Header {server['name']}.{class_name()}")


#============================Core Methods=======================================
# Contains scheduled tasks, boilerplate read/send, queue handling
    def load_servers(self):
        """
        Loads server configuration from database by class_name()
        """
        self.servers = []
        
        self.server_col = DB.mongo['Servers'][class_name()] 
        for document in self.server_col.find():
            self.servers.append(document)

    async def read(self, server:dict):
        """
        Tails docker logs of server, sending output to filter().
        (Tail length defined in database.py)

        Parameters:
        ---
        `server` : `dict`
            -- The server to tail logs of

        `ignore` : `bool`
            -- Whether to print, log, and act on events
        """
        new_context = {'last':datetime.utcnow(), 'hashes':list(), 'name':server['name']}
        
        # Find Context
        flag = False
        for c in self.contexts:
            try:
                if c['name'] == server['name']:
                    context = c
                    flag = True
                    break
            except KeyError:
                continue
        if not flag:
            self.contexts.append(new_context)
            logging.debug(f'Context not found in {self.contexts}')
            self.read(server)
            return

        # Stream Logs
        container = DB.client.containers.get(server['docker_name'])
        for log in container.logs(since=context['last'], stream=True):
            # Check if it's an empty byte object, if so, set context and return
            if log == bytes():
                i = 0
                for c in self.contexts:
                    try:
                        if c['name'] == server['name']:
                            self.contexts[i] = new_context
                    except KeyError:
                        pass
                    i+=1
                return
            
            log = log.decode(encoding="utf-8", errors="ignore")
            log_hash = get_hash(log)
            if log_hash in context['hashes']:
                continue
            new_context['hashes'].append(log_hash)

            await self.filter(message=log, server=server)

    def send(self, server:dict, command:str, log:bool=False, filter=True) -> str: 
        """
        Sends command to server, logging response if true
        Returns: Server response to command (str)

        Parameters:
        ---
        `server`:`dict`:
            - The server to send to

        'command`:`str`
            - The command to be sent
        
        `logging`:`bool`
            - Bool to log command send and response
        """
        container = DB.client.containers.get(server['docker_name'])

        # Single-Quote Filtering (Catches issue #9)
        if filter:
            command = command.replace("'", "'\\''") 
        
        # Send Command, and decipher tuple
        resp_bytes = container.exec_run(command)
        resp_str = resp_bytes[1].decode(encoding="utf-8", errors="ignore")
        logging.info(f"Sent {command} to {server['name']}: {resp_str}")

        if log:
            logging.info(f"Sent {command} to {server['name']}.{class_name()}")
            logging.info(f"Response: {resp_str}")
        
        return resp_str

#------------------------- Event Handlers --------------------------------------
    async def handle_message(self, server:dict, message:dict):
        """
        Empies message queue, sending messages to corresponding channels.


        Parameters:
        `server`:`dict`
            - Server information dictionary 
        `ctx`:``
            - The channel corresponding to the server
        """
        ctx = self.bot.get_channel(server['cid'])
        accounts = self.bot.get_cog("Accounts")

# Account Link TODO IMPROVE ACCESS QUANTITY (CURRENTLY ONCE PER MESSAGE) --> Reduce to only pull link_keys?
        for key in DB.mongo['Servers'][class_name()].find_one({'_id':server['id']}['link_keys']):
            try:
                t = datetime.utcnow().replace(tzinfo=timezone.utc)
                
                # Match Message to active link-keys
                logging.debug(f"checking {message['username']} against {key['username']}")
                if message['username'] == key['username']:
                    logging.debug(f"checking {message['message']} against {key['keyID']}")
                    if message['message'] == key['keyID']:
                        # Link Key Match
                        logging.debug(f"link-key match found {message} for {key}")
                        await accounts.confirm_link(
                            link_key=key,
                            server_name=server['name'],
                            uuid=self.get_uuid(username=key['username']),
                            game=class_name())
                        server['link_keys'].remove(key)
                        DB.mongo['Servers'][class_name()].update_one({'_id':server['id']},{'$pull':{'link_keys':key}})
                        return

                # Throw out expired keys
                elif t >= key['expires']:
                    logging.debug(f"link-key removing old key {key} at {t}")
                    DB.mongo['Servers'][class_name()].update_one({'_id':server['id']},{'$pull':{'link_keys':key}})

            except KeyError as e:
                logging.error(e)
                continue
                
        # Send Messages
        logging.info(f"Message {server['name']}:{message}")
        await ctx.send(embed=embed_message(
            msg_dict=message,
            username_fixes=self.get_username_fixes()))

    async def handle_connection(self, server:dict, connection:dict):
        """
        Empties provided connect_queue, digesting events to corresponding dicts

        Adds modifications to playtime as appropriate
        Updates Header after a connect event
        Saves statistics after modifications

        `server`:`dict`:
            - server info dictionary to reference
        """
        
        # Event Type (Join/Leave)
        join = True if connection['type'] == MessageType.JOIN else False
        
        # Find Player Index
        user = connection['username']
        uuid = self.get_uuid(user)
        time = connection['time']

        # Find Player
        query = DB.mongo[class_name()][server['name']].find_one({'username':user, 'uuid':uuid})
        if query is None:
            # Add Player
            DB.mongo[class_name()][server['name']].insert_one(make_statistics(username=user, uuid=uuid))
            query = DB.mongo[class_name()][server['name']].find_one({'username':user, 'uuid':uuid})
            if query is None:
                logging.critical(f"Unable to upsert and find new user: {user}:{uuid} with query:{query}")
                return
        id = query['_id']
        
        # Add Connect Events w/ fixing logic
        recentest_is_join = analytics_lib.is_recentest_join(col=DB.mongo[class_name()][server['name']], id=id)

        # Based on recentest is join, prevents double joins/leaves which would otherwise mess up calculations later
        # If Adding Join and the most recent entry is a join, remove previous join
        if join == True:
            if recentest_is_join == True:
                logging.debug(f'Handle_connection: Popping join from {user}')
                DB.mongo[class_name()][server['name']].update_one({'_id':id}, {'$pop': {'joins': -1}})
            logging.debug(f'Handle_connection: Adding join to {user} ')
            DB.mongo[class_name()][server['name']].update_one({'_id':id}, {'$addToSet': {'joins':time}})

        # If adding Leave and the most recent entry is a leave, ignore adding leave
        elif join == False:  
            if recentest_is_join == True:
                logging.debug(f'Handle_connection: Adding leave to {user}')
                DB.mongo[class_name()][server['name']].update_one({'_id':id}, {'$addToSet': {'leaves':time}})

        # Online List Logging
        if join and not (user in server['online_players']):
            logging.debug(f'Adding {user} to online players')
            server['online_players'].append(user)
        elif (not join) and (user in server['online_players']):
            logging.debug(f'Removing {user} from online players') 
            server['online_players'].remove(user)
            
        # Update Header (Without hanging up execution, as I believe headers can only be updated so frequently)
        loop = asyncio.get_event_loop()
        loop.create_task(self.header_update(server=server))
        logging.debug(f"Scheduled header_update for server:{server['name']}")


#------------------------------Events-------------------------------------------
    @tasks.loop(seconds=DB.get_chat_link_time())
    async def read_messages(self):
        """
        Reads servers on interval, sends new msgs to linked discord channel.
        
        Manages chat-link functionality from servers->discord.
        """
        await asyncio.gather(self.read(server) for server in self.servers)
    @read_messages.before_loop
    async def before_read_messages(self):
        await self.bot.wait_until_ready() 

    @commands.Cog.listener("on_message")
    async def on_disc_message(self, message):
        """
        Sends new discord messages to linked gameserver channels

        Does not send commands or bot responses.
        """
        if message.author.bot or message.content.startswith('>'): return
        f = self.get_username_fixes()
        msg = f"{f[0]}{message.author.name}{f[1]} {message.content}"
        logging.info(f'{server["name"]}.{class_name()}: "{msg}"')
        
        for server in self.servers:
            if message.channel.id == server['cid']:
                self.send_message(
                    server=server, 
                    message=msg
                )