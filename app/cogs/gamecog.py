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
Version: May 27th, 2022
"""

import json
import os

from discord.ext import commands, tasks
import discord

import analytics_lib
from database import DB
from embedding import embed_message
from messages import MessageType, get_msg_dict, split_first
from server import Server


class GameCog(commands.Cog):
    """
    A class implementing the basic loops and instance methods used to integrate
    a dockerized gameserver with chat-link using discord, discord commands that
    send commands to dockerized server, or log player activity & store player
    specific information.

    Attribute bot: The current discord bot instance
    Invarient: Is a Discord.py bot object
    """
    ### Hidden Attributes
    # Attribute servers: List of loaded servers
    # Invariant: Is a list of accessable dockerized servers of same version
    # --------------------------------------------------------------------------
    def __init__(self, bot):
        self.bot = bot
        self.servers = []
        
        # LOAD SERVERS
        # -----------------------------------------------------
        # Adds Containers with matching version
        for cont in DB.get_containers():
            cog_name = split_first(cont.get('version'),':')[0]
            if cog_name == self.get_version():
                server = Server(
                    server=cont, 
                    bot=self.bot, 
                    statistics=self.load_statistics(
                        cog_name=cog_name,
                        server_name=cont.get('name')),
                    cog_name=cog_name)

                # Update Online List 
                    # TODO: Check if online players most recent is join, 
                    # if not, add a join at discovery time. Also would need to
                    # include addplayer for unrecognized players
                        # TODO break out addplayer function
                pl = self.get_player_list(server)
                server.online_players = pl if pl else []
                self.servers.append(server)

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

        Parameter server: Server object to reference
        Precondition: server is a Server dataclass object
        """

        pass

    def is_player_online(self, server:Server, playername:str = None) -> bool:
        """
        Returns: True if playername matches element in online_player list

        To be overloaded by GameCog children.
        Not certain, as not all games get online players on launch

        Parameter server: Server to search for players in

        Parameter playername: player to search for in online_players
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

        Parameter server: Server object to reference
        Precondition: server is a Server dataclass object

        Parameter message: The message to send to server.
        """

        print(f"EEE - {message} GameCog send_message not implemented.")

    def discord_message_format(self, server:Server, message:str) -> str:
        """
        Formats message based on version and logs to console.
        - Default "<User> Message"

        Parameter server: Server object to reference
        Precondition: server is a Server dataclass object

        Parameter message: message to format. 
        """

        item = f"<{message.author.name}> {message.content}"
        print(f" {server.server_name}.{server.cog_name}: {item}")
        return item

    def filter(self, server:Server, message:str, ignore:bool):
        """
        Filters logs using versionbased conditions by type and content. 
        Adds leaves/joins to connectqueue and messages to message queue.
        
        To be overloaded by GameCog Children

        Parameter server: server to store fingerprints in
        Precondition: server is a Server dataclass object

        Parameter message: string to filter using conditions

        Parameter ignore: Bool whether or not to put events to queues
        """
        # Fingerprints message, only uniques get sent
        if not server.fingerprint.is_unique_fingerprint(message): return

        # Filter message into a dictionary
        dict = get_msg_dict(username="__default__",
            message=message,
            MessageType=MessageType.MSG,
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

        Parameter server: server object to reference
        Precondition: server is a Server dataclass object
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

        Parameter server: Server object to reference
        Precondition: server is a Server dataclass object

        Parameter container_status: String of online/offline status
        """
        ctx = self.bot.get_channel(server.cid)
        await ctx.edit(
            topic=f"{server.server_name}.{server.cog_name} | "
                f"{len(server.online_players)}/"
                f"{server.player_max if server.player_max > -1 else 'ꝏ'}"
                f" | Status: {container_status}")
        print(f"[Logging] -Header- {server.server_name}.{server.cog_name}:"
            " Header Updated")

#==========================Structural Methods===================================
#   Contains filesystem add/load/create, setters/getters, and search methods
#------------------------- Setters/Getters -------------------------------------
    
    def set_statistics(self, 
        statistics:dict, 
        server_name:str,
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

        Parameter statistics: The statistics dict to update self to
        Preconditions: statistics is a dict

        Parameter server_name: server_name containing the statistics instance
        Preconditons: server_name is an str

        Parameter uuid: 
        Preconditon: uuid is an str

        Parameter playername: 
        Precondition: playername is an str

        Parameter request: Used when unsure if str is uuid or playername
        Precondition: request is an str, a uuid or a playername 
        """
        try:
            serv = self.find_server(server_name=server_name)
            if serv == None: return

            if uuid:
                self.servers[serv].statistics[self.find_player(
                    server=self.servers[serv],
                    uuid=uuid)] = statistics
            elif playername:
                self.servers[serv].statistics[self.find_player(
                    server=self.servers[serv],
                    username=playername)] = statistics
            elif request:
                find1 = self.find_player(
                    server=self.servers[serv],
                    uuid=request)
                find2 = self.find_player(
                    server=self.servers[serv],
                    username=request)
                if find1:
                    self.servers[serv].statistics[find1] = statistics
                elif find2:
                    self.servers[serv].statistics[find2] = statistics
            else:
                raise NotImplementedError(
                    'set_statistics called with no paramenters ya dummy')
        except:
            return

    def get_statistics(self, 
        server_name:str,
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
        if serv == None: return

        if uuid:
            return self.servers[serv].statistics[self.find_player(
                server=self.servers[serv],
                uuid=uuid)]
        elif playername:
            return self.servers[serv].statistics[self.find_player(
                server=self.servers[serv],
                username=playername)]
        elif request:
            find1 = self.find_player(
                    server=self.servers[serv], 
                    uuid=request) 
            find2 = self.find_player(
                    server=self.servers[serv], 
                    username=request)

            # Switch between found uuid & username 
            try:
                if find1 != None:
                    ret_val = self.servers[serv].statistics[find1]
                elif find2 != None: 
                    ret_val = self.servers[serv].statistics[find2]
                else:
                    return None
            except IndexError:
                raise NotImplementedError(
                    f'Index Error in get_statistics:{find1}, {find2}')
            return ret_val
        else:
            raise NotImplementedError(
                'get_statistics called with no paramenters ya dummy')
#----------------------------- Find --------------------------------------------
    def find_server(self, cid:int=None, server_name:str=None) -> int:
        """
        Returns: Index of matching server to criteria, otherwise returns None

        Requires cid or server_name to be provided.

        Parameter server_name: Server name to find match to
        Preconditon: server_name is an str, server_name != ''

        Parameter cid: Server discord channel id to match to
        Precondition: cid is an int, cid != 0
        """
        i = 0
        if cid != None:
            for server in self.servers:
                if server.cid == cid: return i
                i+=1
            return None
        elif server_name != None:
            for server in self.servers:
                if server.server_name == server_name: return i
                i+=1
            return None
        else:
            raise NotImplementedError(
                'find_server called with no paramenters ya dummy')

    def find_player(self, 
        server:Server=None,
        username:str=None, 
        uuid=None) -> int:
        """ 
        Returns: Index of player statistics obj matching parameters, None if not
        
        Finds player statistics object, returns index of it. Accounts for UUIDs
        and usernames. Requires server and either username or uuid parameter.
        
        Parameter server: server to search for player statistics in
        Precondition: server is a Server dataclass object

        Parameter username: username of player to be found
        Preconditon: username is an str, username != ''

        Parameter uuid: uuid of player to be found, if exists
        Precondition: uuid is an str, uuid != ''
        """
        i = 0
        if not uuid:
            uuid = self.get_uuid(username=username)
        for stat in server.statistics:
            if uuid:
                if stat['uuid'] == uuid: return i
            else:
                if stat['user'] == username: return i
            i+=1
        return None
#----------------------------- Filesystem --------------------------------------
    def load_statistics(self, cog_name:str, server_name:str) -> list:
        """
        Returns: list of files in data/servers/{cog_name}/{docker_name} loaded
        
        Parameter cog_name: name of cog, loads matching directory name's files
        Parameter server_name: name of server in cog, loads matching dir files
        """
        stats = []
        try:
            # Ensure directory existance
            path = f'../../data/servers/{cog_name}/{server_name}/'
            if not os.path.exists(path):
                os.makedirs(path)

            # For file in folder
            for item in os.listdir(path):
                print(f"    -Filesystem- load_item: {item}")
                with open(path+item) as f:
                    stats.append(json.load(f))
        except FileNotFoundError:
            print(
                f"{server_name}.{__name__}"
                f" Error: No files found for load_statistics")
            return stats
        else:
            return stats
        
    def create_statistics(self, server:Server, username:str=None, 
        uuid:str=None):
        """
        Creates a new statistics dict in server.statistics & file for given user
        
        Server and either username or uuid parameters are required.
        Creates file with below structure for parameters in server.
        
        {
            username:'',
            uuid:'',
            total_playtime:'',
            calculated_index:-1,
            joins:[],
            leaves:[]
        }

        Parameter server: object to reference when creating & saving statistics
        Preconditons: server is a Server dataclass object

        Parameter username: username to assign to statistics (Used to find)

        Parameter uuid: uuid to assign to statistics (Used to find & update)
        """
        # Build Dict
        dict = {
            'username':'',
            'uuid':'',
            'total_playtime':'', 
            'calculated_index':-1, 
            'joins':[], 
            'leaves':[]}

        # Get Filename (UUID if uuid, otherwise username)
        if username: dict['username']= filename = username
        if uuid: dict['uuid']= filename = uuid
        path = (
            f"../../data/servers/{server.cog_name}/"
            f"{server.server_name}/{filename}.json")

        # Save dict to file
        print(f"Adding player: {username} at {path}")
        with open(path, 'w+') as f:
            json.dump(dict, f, indent=2)

        # Save dict to cog
        try:
            self.servers[self.find_server(
                server_name=server.server_name)].statistics.append(dict)
        except:
            raise NotImplementedError(
                "Create Statistics: Called without server")

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
        # Get indexes if not present
        if server_index == None:
            server_index = self.find_server(server_name=server_name)
            if server_index == None:
                raise NotImplementedError(f"sindex:{server_index}, sname:{server_name}")

        # Set Server
        if server == None:
            server = self.servers[server_index]
            if server == None:
                raise NotImplementedError()#

        # Request Handling
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
            return None

        # Determine filename
        if not uuid:
            uuid = self.get_uuid(username=username)
        filename = uuid if uuid != None else username

        # Raise exception if missing uuid or username
        if filename == None:
            raise NotImplementedError(
                f"{server.server_name}.{server.cog_name} Error: "
                " called without username or uuid ya dummy.")

        # Dumps json to path, otherwise throws exception
        try:
            path = (f'../../data/servers/{server.cog_name}'
                    f'/{server.server_name}/{filename}.json')
            with open(path, 'w') as f:
                     json.dump(
                         self.servers[server_index].statistics[index], 
                         f, 
                         indent = 2)
                     print(f"[Logging] -Filesystem- Successfully Saved {path}")
        except FileNotFoundError:
            raise NotImplementedError(
                f"{server.server_name}.{server.cog_name} Error: {filename}"
                " does not exist in current filestructure")

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

    def send(self, server:Server, command:str, logging:bool=False) -> str: 
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
        filtered_command = command.replace("'", "'\\''") 
        
        # Send Command, and decipher tuple
        resp_bytes = container.exec_run(f"{filtered_command}")
        resp_str = resp_bytes[1].decode(encoding="utf-8", errors="ignore")

        # Logging
        if logging:
            print(
                f"\nSent {command} to {server.server_name}.{server.cog_name}:")
            print(f' --- {resp_str}')
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
        # Quick Return
        if server.connect_queue.qsize() == 0: return

        # Logging stats indexes that need to be saved
        save_list = [] 

        # Digest Events
        while not (server.connect_queue.qsize() == 0):
            x = server.connect_queue.get()
            
            # Event Type (Join/Leave)
            temp = x.get('type')
            if temp == None: 
                raise NotImplementedError(
                    f"handle_connect_queue none 'type': {x}")
            join = True if temp == MessageType.JOIN else False
            
            # Find Player Index
            user = x.get('username')
            uuid = self.get_uuid(user)
            player_index = self.find_player(
                server=server, 
                username=user, 
                uuid=uuid)

            # Add Player If Not Present
            if player_index == None:
                if uuid:
                    self.create_statistics(
                        server=server,
                        username=user, 
                        uuid=uuid)
                else:
                    self.create_statistics(server=server,username=user)
                # Get Index of new player
                player_index = self.find_player(
                    username=user,
                    server=server, 
                    uuid=uuid)
                if player_index == None:
                    raise NotImplemented(
                        "Player not being created in create_statistics"
                        " or appended to statistics.")
            
            # Add Connect Events w/ fixing logic
            recentest_is_join = analytics_lib.is_recentest_join(
                statistics=server.statistics[player_index])
            print(f"Jointype: {join}, Recentest is join: {recentest_is_join}")

            # Based on recentest is join, prevents double joins/leaves which 
            # would otherwise mess up calculations later
            try:
                # If Adding Join and the most recent entry is a join, 
                # remove previous join
                if join == True:
                    if recentest_is_join == True:
                        server.statistics[player_index]['joins'].pop()
                    server.statistics[player_index]['joins'].append(
                        str(x.get('time')))

                # If adding Leave and the most recent entry is a leave, 
                # ignore adding leave
                elif join == False: 
                    if recentest_is_join == True:
                        server.statistics[player_index]['leaves'].append(
                            str(x.get('time')))

                # Add modification to savelist to later be saved
                save_list.append({'index':player_index,'uuid':uuid,'user':user})
            except:
                raise NotImplementedError(
                    f"{server.cog_name}:{x} event not added.")

            # Online List Logging
            if join and not (x['username'] in server.online_players):
                server.online_players.append(x['username'])
            elif (not join) and (x['username'] in server.online_players): 
                server.online_players.remove(x['username'])
            
        # Update Header
        await self.header_update(server=server)

        # Save Statistics
        for index in save_list:
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

            # Message Queue
            while not (server.message_queue.qsize() == 0): 
                await ctx.send(embed=embed_message(server.message_queue.get()))

            await self.handle_connect_queue(server=server)
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
                self.send_message(
                    server=server, 
                    message=self.discord_message_format(
                        server=server,
                        message=message))