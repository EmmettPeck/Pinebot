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
Version: July 1st, 2022
"""

import asyncio
import datetime
import json
import os
import queue
import logging

from discord.ext import commands, tasks
import discord

import analytics_lib
from database import DB
from embedding import embed_message
from messages import MessageType, split_first
from server import Server
from dictionaries import get_msg_dict, make_statistics


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
        self.servers = self.load_servers()
                # Update Online List 
                    # TODO: Check if online players most recent is join, 
                    # if not, add a join at discovery time. Also would need to
                    # include addplayer for unrecognized players
                        # TODO break out addplayer function

        # Ensure fingerprinted messages before cog was online
        for server in self.servers:
            self.read(server, ignore=True)
        
        # Start Scheduled tasks
        self.pass_message.start()

    @commands.Cog.listener()
    async def on_ready(self):
        # Update Headers On Launch
        for server in self.servers:
            await self.header_update(server=server)

    def cog_unload(self):
        self.pass_message.cancel()

    # To Be Overloaded: --------------------------------------------------------

    def get_version(self) -> str:
        """
        Returns: Version of cog implementation

        The Version Of The GameCog ie: "Minecraft", "Factorio" -- 
        To be overloaded by GameCog children
        """
        return None

    def get_uuid(self, username:str) -> str:
        """
        Returns: UUID of username if present, otherwise returns none.
        
        To be overloaded by GameCog children.     
        """
        return None

    def get_player_list(self, server:Server=None) -> list:
        """
        Does nothing. To be overloaded by GameCog children.

        For versions without a getlist function, returns None
        Called on cog init for each server

        `server`: `Server`
            -- object to reference
        Precondition: server is a Server dataclass object
        """

        pass

    def get_username_fixes(self) -> tuple:
        """
        Returns tuple of chat message prefix and suffix for usernames

        To be overloaded by GameCog children.
        """
        return ("","")

    def is_player_online(self, server:Server, playername:str = None) -> bool:
        """
        Returns: True if playername matches element in online_player list

        To be overloaded by GameCog children.
        Not certain, as not all games get online players on launch

        Parameters:
        ---
        `server` : `Server`
            -- Server to search in
        `playername` : `str`
            -- Playername to search server.online_players for
        """
        if playername:
            for player in server.online_players:
                if playername == player: return True
            return False
        else:   
            raise NotImplementedError(
                "is_player_online: Called without True playername.")
                
    def send_message(self, server:Server, message:str):
        """
        Does nothing. To be overloaded by GameCog children.

        Interface for Discord->Server Chatlink messaging.
        Sends Message To gameserver based on version implementation:
         - If no consolebased say command, does nothing.

        Parameters:
        ---
        `server` : `Server`
            -- Server to to reference the information of
        `message` : `str`
            -- Message to format
        """

        logging.warning(f"{message} GameCog send_message not implemented.")

    def discord_message_format(self, server:Server, message:str) -> str:
        """
        Formats message based on version and logs to console.
        - Default "<User> Message"

        Parameters:
        ---
        `server` : `Server`
            -- Server to to reference the information of
        `message` : `str`
            -- Message to format
        """

        item = f"<{message.author.name}> {message.content}"
        logging.critical(f'{server.server_name}.{server.cog_name}: "{item}"')
        return item

    def filter(self, server:Server, message:str, ignore:bool):
        """
        Filters logs using versionbased conditions by type and content. 
        Adds leaves/joins to connectqueue and messages to message queue.
        
        To be overloaded by GameCog Children

        Parameters:
        ---
        `server` : `Server`
            -- Server to store fingerprints in
        `message` : `str`
            -- Message string to filter using conditions
        `ignore` : `Bool`
            -- Whether or not to put events to queues
        """
        # Fingerprints message, only uniques get sent
        if not server.fingerprint.is_unique_fingerprint(message): return

        # Filter message into a dictionary
        dict = get_msg_dict(username="__default__",
            message=message,
            type=MessageType.MSG,
            color=discord.Color.blue())

        # If Not Ignore, Messages are sent and accounted for playtime
        if dict and (not ignore):
            mtype =dict.get('type')
            if mtype == MessageType.JOIN or mtype == MessageType.LEAVE:
                dict["server"] = server.server_name
                server.connect_queue.put(dict)
            server.message_queue.put(dict)
            
#---------------------------- Headers ------------------------------------------
    async def header_update(self,server:Server):
        """
        Updates header with server playercount & docker status

        Parameters:
        ---
        `server` : `Server`
            -- Server object to update the linked channel header for
        """

        if (DB.client.containers.get
        (server.server.get("docker_name")).status.title().strip() == 'Running'):
            status = "Online"
        else:
            status = "Offline"
        await self.update_channel_header(server=server, container_status=status)
    
    async def update_channel_header(self, server:Server, container_status:str):
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
            topic=f"{server.server_name} | {server.version} | "
                f"{len(server.online_players)}/"
                f"{server.player_max if server.player_max > -1 else 'ꝏ'}"
                f" | Status: {container_status}")
        logging.info(f"Updated Header {server.server_name}.{server.cog_name}")

#==========================Structural Methods===================================
#   Contains filesystem add/load/create, setters/getters, and search methods
#------------------------- Setters/Getters -------------------------------------
    
    def set_statistics(self, 
        statistics:dict, 
        server_name:str,
        server:Server=None,
        request:str=None, 
        uuid:str=None, 
        playername:str=None 
        ):
        """
        Sets dictionary in server with matching server_name and matching request 
        to uuid/playername to statistics
        
        Either uuid, playername, or request required. Based on provided 
        criteria, searches server for approprate dict to update. Otherwise does 
        not update.

        Parameters:
        ---
        `statistics` : `dict`
            -- The statistics dict to update self to
        `server_name` : `str` 
            -- server_name containing the statistics instance
        `uuid` : str
            -- uuid to set statistics entry of
        `playername` : str
            -- playername to set statistics entry of
        `request` : str
            -- Used when unsure if str is uuid or playername
        """
        # Find Server
        serv = self.find_server(server_name=server_name)
        if serv == None: 
            logging.warning(f'set_statistics server is {serv}, returning')
            return

        # Get Server
        if server == None:
            server = self.servers[serv]

        if uuid != None:
            player_index = self.find_player(server=server,uuid=uuid)
            if player_index != None:
                logging.info(f'set_statistics uuid is uuid at {player_index}, setting statistics.')
                server.statistics[player_index] = statistics
            else:
                logging.error(f'set_statistics uuid not None, {player_index} found with findplayer, returning None')
                return
        elif playername != None:
            player_index = self.find_player(server=server,username=playername)
            if player_index != None:
                
                logging.info(f'set_statistics username is username at {player_index}, setting statistics.')
                server.statistics[player_index] = statistics
            else:
                logging.error(f'set_statistics user not None, {player_index} found with findplayer, returning None')
                return
        elif request != None:
            find1 = self.find_player(server=server,uuid=request)
            find2 = self.find_player(server=server,username=request)
            if find1 != None: 
                logging.info(f'set_statistics request is uuid {request} at {find1}, setting statistics.')
                server.statistics[find1] = statistics
            elif find2 != None: 
                logging.info(f'set_statistics request is user {request} at {find2}, setting statistics.')
                server.statistics[find2] = statistics
            else:
                logging.error(f'set_statistics request {request} not found.')
        else:
            logging.error('set_statistics called with request, playername, and uuid == None')
            return

    def get_statistics(self, 
        server_name:str,
        server:Server=None,
        request:str=None, 
        uuid:str=None, 
        playername:str=None 
        ) -> dict:
        """
        Returns: First dtatistics dictionary matching request & server_name 
        
        Either uuid, playername, or request required. Based on provided 
        criteria, searches server for approprate dict to return. Otherwise
        returns None.

        Parameters:
        ---
        `server_name` : `str`
            -- server_name containing the statistics instance
        `request`: `str`
            -- The uuid or playername to get statistics of
        `uuid` : `str`
            -- The uuid to get statistics of
        `playername` : `str` 
            -- The username to get statistics of
        """
        serv = self.find_server(server_name=server_name)
        if serv == None: 
            logging.warning(f'get_statistics server is {serv}, returning')
            return

        # Get Server
        if server == None:
            server = self.servers[serv]

        if uuid != None:
            found = self.find_player(server=server,uuid=uuid)
            if found != None:
                logging.info(f'get_statistics uuid is uuid at index {found}, returning statistics')
                return server.statistics[found]
            else:
                logging.error(f'get_statistics uuid not None, index {found} found with findplayer, returning None')
                return
        elif playername != None:
            found = self.find_player(server=server,username=playername)
            if found != None:
                logging.info(f'get_statistics user is user at index {found}, returning statistics')
                return server.statistics[found]
            else:
                logging.error(f'get_statistics user not None, index {found} found with findplayer, returning None')
                return
        elif request != None:
            logging.info("get_statistics requesting two findplayers")
            find1 = self.find_player(server=server, uuid=request) 
            find2 = self.find_player(server=server, username=request)

            # Switch between found uuid & username 
            if find1 != None:
                logging.info(f'get_statistics request is uuid at index {find1}, returning statistics')
                ret_val = server.statistics[find1]
            elif find2 != None: 
                logging.info(f'get_statistics request is username at index {find2}, returning statistics')
                ret_val = server.statistics[find2]
            else:
                logging.warning(f'get_statistics request not found at index {find1}, index{find2}, returning none')
                return
            return ret_val
        else:
            logging.error('get_statistics called with request, playername, and uuid == None')
#----------------------------- Find --------------------------------------------
    def find_server(self, cid:int=None, server_name:str=None) -> int:
        """
        Returns: Index of matching server to criteria, otherwise returns None

        Requires cid or server_name to be provided.

        Parameters:
        ---
        `server_name` : `str`
            -- Server name to find match to
        `cid` : `int`
            -- Server discord channel id to match to
        """
        i = 0
        if cid != None:
            for server in self.servers:
                if server.cid == cid: 
                    logging.info(f"find_server found cid at index {i}")
                    return i
                i+=1
        elif server_name != None:
            for server in self.servers:
                if server.server_name == server_name: 
                    logging.info(f"find_server found server_name at index {i}")
                    return i
                i+=1
        else:
            logging.error('find_server cid & servername == None')
            raise NotImplementedError('find_server called with no paramenters ya dummy')
        logging.warning(f"find_server found no server for {server_name}:{cid}")
        return

    def find_player(self, 
        server:Server=None,
        username:str=None, 
        uuid=None) -> int:
        """ 
        Returns: Index of player statistics obj matching parameters, None if not
        
        Finds player statistics object, returns index of it. Accounts for UUIDs
        and usernames. Requires server and either username or uuid parameter.
        
        Parameters:
        ---
        `server` : `Server`
            -- server to search for player statistics in
        `username` : `str`
            -- username of player to be found
        `uuid` : `str`
            -- uuid of player to be found, if exists
        """
        i = 0
        if not uuid:
            uuid = self.get_uuid(username=username)
            logging.info(f"find_player: UUID not provided, got UUID {uuid}")
        for stat in server.statistics:
            if uuid != None:
                if stat.get('uuid') == uuid: 
                    logging.info(f"find_player found uuid at {i}")
                    return i
            else:
                if stat.get('username') == username: 
                    logging.info(f"find_player found username at {i}")
                    return i
            i+=1
        logging.warning("find_player found no player")
        return
#----------------------------- Filesystem --------------------------------------
    def load_servers(self, bot=None, cog_version:str=None) -> list:
        """
        Returns list of loaded Server objects from containers matching version

        Parameters:
        ---
        `bot` : `discord.bot`
            -- The current discord bot instance
        `cog_version` : `str`:
            -- The version of GameCog to match
        """
        server_list = []
        bot = self.bot if bot == None else bot
        cog_version = self.get_version() if cog_version == None else cog_version

        # Add Containers with matching version
        for container in DB.get_containers():
            cog_name = split_first(container.get('version'),':')[0]
            if cog_name == cog_version:
                # Create Server Object
                server=Server(server=container, bot=bot, cog_name=cog_name,
                    statistics=self.load_statistics(cog_name=cog_name,server_name=container.get('name')))

                # Get Online PlayerList
                pl = self.get_player_list(server)
                server.online_players = pl if pl else []
                
                server_list.append(server)
                logging.critical(f"loaded {server.server_name} with {len(server.online_players)}/{server.player_max} players.")
        return server_list

    def load_statistics(self, cog_name:str, server_name:str) -> list:
        """
        Returns: list of files in data/servers/{cog_name}/{docker_name} loaded
        
        Parameters:
        ---
        `cog_name` : `str`
            -- name of cog, loads matching directory name's files
        `server_name` : `str`
            -- name of server in cog, loads matching dir files
        """
        stats = []
        try:
            # Ensure directory existance
            path = f'../../data/servers/{cog_name}/{server_name}/'
            if not os.path.exists(path):
                logging.info(f"load_statistics creating file structure {path}")
                os.makedirs(path)

            # For file in folder
            for item in os.listdir(path):
                logging.info(f"load_statistics loading item: {item}")
                with open(path+item) as f:
                    stats.append(json.load(f))
        except FileNotFoundError:
            logging.warning(f"{server_name}.{__name__} no files found for load_statistics")
            return stats
        else:
            return stats
        
    def create_statistics(self, server:Server, username:str=None, 
        uuid:str=None):
        """
        Creates a new statistics dict in server.statistics & file for given user
        
        Server and either username or uuid parameters are required.

        Parameters:
        ---
        `server` : `Server`
            -- object to reference when creating & saving statistics
        `username` : `str`
            -- username to assign to statistics (Used to find)
        `uuid` : `str`
            -- uuid to assign to statistics (Used to find & update)
        """
        dict = make_statistics()

        # Get Filename (UUID if uuid, otherwise username)
        if username: dict['username']= filename = username
        if uuid: dict['uuid']= filename = uuid
        path = (
            f"../../data/servers/{server.cog_name}/"
            f"{server.server_name}/{filename}.json")

        # Save dict to file
        logging.critical(f"Adding player: {username} at {path}")
        with open(path, 'w') as f:
            json.dump(dict, f, indent=2)

        # Save dict to cog
        logging.info(f"create_statistics adding: {dict}")
        server.statistics.append(dict)

    def save_statistics(self, 
        server_name:str,
        server:Server=None, 
        username:str=None, 
        uuid:str=None, 
        request:str=None,
        index:int=None,
        server_index:int=None):
        ''' 
        Saves player statistic file for server. 
        Requires a uuid, username, or request.
        
        Parameters:
        ---
        `server_name` : `str`
            -- name of server containing statistics instance
        `server` : `Server`
            -- object containing statistics instance to save
        `username` : `str`
            -- username of player to save
        `uuid` : `str`
            -- uuid of player to save
        `request` : `str`
            -- uuid OR username of player to save
        `index` : `int` 
            -- index of playerfile to save
        `server_index` : `int`
            -- index of server to save to
        ''' 
        logging.info(f"Saving {request}({username}:{uuid}) to {server_name}")

        # Get indexes if not present
        if server_index == None:
            server_index = self.find_server(server_name=server_name)
            if server_index == None:
                logging.error(f"server_index not found, throwing exception.")
                raise NotImplementedError(f"sindex:{server_index}, sname:{server_name}")

        # Set Server
        if server == None:
            server = self.servers[server_index]
            if server == None:
                logging.error(f"server is None, returning, any unsaved data may be lost")
                return

        # Request Handling
        if uuid != None:
            found = self.find_player(server=server, uuid=uuid) 
            if found != None:
                index = found
            else:
                logging.error(f"save_statistics uuid not None, {found} found with findplayer, returning before saving")
                return
        elif username != None:
            found = self.find_player(server=server, username=username) 
            if found != None:
                index = found
            else:
                logging.error(f"save_statistics user not None, {found} found with findplayer, returning before saving")
                return
        elif request != None:
            find1 = self.find_player(server=server, uuid=request) 
            find2 = self.find_player(server=server, username=request)

            if find1 != None:
                # Request is a existing UUID
                uuid = request
                index = find1
            elif find2 != None:
                # Request is an existing Username
                username = request
                index = find2
            else:
                # Request is neither
                logging.error(f"save_statistics request not None, {find1},{find2} found with findplayer, returning before saving")
                return

        # Determine filename
        if not uuid:
            uuid = self.get_uuid(username=username)
        filename = uuid if uuid != None else username
        logging.info(f'save_statistics evaluated filename: {filename}')

        # Raise exception if missing uuid or username
        if filename == None:
            logging.error(f"{server.server_name}.{server.cog_name}: filename is None, returning before saving.")
            return

        # Dumps json to path, otherwise throws exception
        try:
            path = (f'../../data/servers/{server.cog_name}'
                    f'/{server.server_name}/{filename}.json')
            with open(path, 'w') as f:
                json.dump(server.statistics[index], f, indent = 2)
            logging.info(f"Successfully saved {server.server_name} {path}")
        except FileNotFoundError:
            logging.error(f"{server.server_name}.{server.cog_name}: filename does not exist")

#============================Core Methods=======================================
# Contains scheduled tasks, boilerplate read/send, queue handling

    def read(self, server:Server, ignore=False):
        """
        Tails docker logs of server, sending output to filter().
        (Tail length defined in database.py)

        Parameters:
        ---
        `server` : `Server`
            -- The server to tail logs of

        `ignore` : `bool`
            -- Whether to print, log, and act on events
        """
        # Filters, then reads set_tail_len of logs to an iterable
        container = DB.client.containers.get(server.docker_name)
        response = container.logs(tail=DB.get_tail_len()).decode(
            encoding="utf-8", 
            errors="ignore")
                
        for msg in response.strip().split('\n'):
            self.filter(message=msg, server=server,ignore=ignore)

    def send(self, server:Server, command:str, log:bool=False, filter=True) -> str: 
        """
        Sends command to server, logging response if true
        Returns: Server response to command (str)

        Parameter server: The server to send command to
        Preconditon: server is a Server dataclass object

        Parameter command: The command to send to server
        
        Parameter logging: Bool to log command sent, and response
        """
        # Attach Container
        container = DB.client.containers.get(server.docker_name)

        # Single-Quote Filtering (Catches issue #9)
        if filter:
            command = command.replace("'", "'\\''") 
        
        # Send Command, and decipher tuple
        resp_bytes = container.exec_run(command)
        resp_str = resp_bytes[1].decode(encoding="utf-8", errors="ignore")
        logging.info(f"Sent {command} to {server.server_name}: {resp_str}")

        # Logging
        if log:
            logging.critical(f"Sent {command} to {server.server_name}.{server.cog_name}")
            logging.critical(f"Response: {resp_str}")
        return resp_str

#------------------------- Queue Handlers --------------------------------------
    async def handle_connect_queue(self, server:Server):
        """
        Empties provided connect_queue, digesting events to corresponding dicts

        Adds modifications to playtime as appropriate
        Updates Header after a connect event
        Saves statistics after modifications

        Parameter server: The server to reference for a connect_queue
        """
        save_list = [] 

        # Digest Events
        try:
            while True:
                x = server.connect_queue.get_nowait()
                
                # Event Type (Join/Leave)
                temp = x.get('type')
                if temp == None: 
                    logging.error(f"connect_queue type None from {x}, skipping dictionary")
                    continue
                join = True if temp == MessageType.JOIN else False
                
                # Find Player Index
                user = x.get('username')
                uuid = self.get_uuid(user)
                logging.info(f'connect_queue user={user}, uuid={uuid}, join={join}')

                # Get index of player -- adding player if not present
                player_index = self.find_player(server=server, username=user, uuid=uuid)
                logging.info(f'handle_connect_queue playerindex={player_index}')
                if player_index == None:
                    logging.info(f'handle_connect_queue creating user')
                    self.create_statistics(server=server, username=user, uuid=uuid)

                    # Get new player_index
                    player_index = self.find_player(server=server, username=user, uuid=uuid)
                    logging.info(f'handle_connect_queue new playerindex is {player_index}')
                    if player_index == None:
                        logging.critical(f'New playerindex is {player_index}, skipping entry, filesystem likely compromised.')
                        continue
                
                # Add Connect Events w/ fixing logic
                recentest_is_join = analytics_lib.is_recentest_join(statistics=server.statistics[player_index])
                logging.info(f'handle_connect_queue joinType, recentest_is_join ={join},{recentest_is_join}')
                # Based on recentest is join, prevents double joins/leaves which would otherwise mess up calculations later
                # If Adding Join and the most recent entry is a join, remove previous join
                if join == True:
                    if recentest_is_join == True:
                        logging.info(f'handle_connect_queue: popping {user} join')
                        server.statistics[player_index]['joins'].pop()
                    logging.info(f'handle_connect_queue: adding {user} join')
                    server.statistics[player_index]['joins'].append(
                        str(x.get('time')))

                # If adding Leave and the most recent entry is a leave, ignore adding leave
                elif join == False: 
                    if recentest_is_join == True:
                        logging.info(f'handle_connect_queue: adding {user} leave')
                        server.statistics[player_index]['leaves'].append(
                            str(x.get('time')))

                # Add modification to savelist to later be saved
                save_dict = {'index':player_index,'uuid':uuid,'user':user}
                logging.info(f"adding dict to file_save list: {save_dict}")
                save_list.append(save_dict)

                # Online List Logging
                if join and not (x['username'] in server.online_players):
                    logging.info(f'Adding {x["username"]} to online players')
                    server.online_players.append(x['username'])
                elif (not join) and (x['username'] in server.online_players):
                    logging.info(f'Removing {x["username"]} from online players') 
                    server.online_players.remove(x['username'])
        except queue.Empty:
            #logging.info(f'{server.server_name} queue.Empty exception')

            # Update Header (Without hanging up execution, as I believe headers can only be updated so frequently)
            if save_list:
                loop = asyncio.get_event_loop()
                loop.create_task(self.header_update(server=server))
                logging.info(f'Scheduled header_update for {server.server_name}')

            # Save Statistics
            for index in save_list:
                await asyncio.sleep(0)
                self.save_statistics(
                    server_name=server.server_name,
                    server=server,
                    uuid=index.get('uuid'),
                    username=index.get('user'),
                    index=index.get('index'))

#-------------------------Scheduled Tasks---------------------------------------
    @tasks.loop(seconds=DB.get_chat_link_time())
    async def pass_message(self):
        """
        Reads servers on interval, sends new msgs to linked discord channel.
        
        Reads each server each interval, handles queues of each server each 
        interval. Manages chat-link functionality from servers->discord.
        """
        for server in self.servers:
            self.read(server)
            ctx = self.bot.get_channel(server.cid)

            # Connect Queue
            await self.handle_connect_queue(server=server)
            
            # Message Queue
            try:
                while True:
                    message = server.message_queue.get_nowait()

                    # link-key checking (Account Link)
                    for key in server.link_keys:
                        if message.get('username') == key.get('name'):
                            if message.get('message') == key.get('keyID'):
                                # TODO Confirm Key w/ account handler
                                
                        # Throw out old keys
                        if datetime.utcnow() >= key.get('time'):
                            logging.debug(f"link-key removing old key {key} at {datetime.utcnow()}")
                            server.link_keys.remove(key)
                            

                    # Message Handling
                    await ctx.send(embed=embed_message(
                        msg_dict=message,
                        username_fixes=self.get_username_fixes()))
            except queue.Empty:
                await asyncio.sleep(0)

            
            
    @pass_message.before_loop
    async def before_pass_mc_message(self):
        await self.bot.wait_until_ready() 

    @commands.Cog.listener("on_message")
    async def on_disc_message(self, message):
        """
        Sends new discord messages to linked gameserver channels

        Does not send commands or bot responses.
        """
        if message.author.bot or message.content.startswith('>'):
            return
        for server in self.servers:
            if message.channel.id == server.cid:
                self.send_message(server=server, message=
                    self.discord_message_format(server=server,message=message))