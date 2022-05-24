import asyncio
from datetime import datetime
import json
import os
from discord.ext import tasks, commands
import discord

from database import DB
from embedding import embed_message
from messages import MessageType, split_first, get_msg_dict
from fingerprints import FingerPrints
from server import Server
import analytics_lib



class GameCog(commands.Cog):
    """
    GameCog - A discord.py cog w/ ChatLink & Playtime logging for docker games
    
    For A Game Specific Cog, Implement:
    - Send
    - Filter
    - get_player_list
    """

    def __init__(self, bot):
        self.bot = bot
        self.servers = []
        
        # Adds containers based on gameversion to appropriate cog 
        for cont in DB.get_containers():
            if split_first(cont.get('version'),':')[0] == self.get_version():
                server = Server(server=cont, bot=self.bot, statistics=self.load_statistics(cont.get('docker_name')))

                # Update Online List
                pl = self.get_player_list(server)
                server.online_players = pl if pl else []

                self.servers.append(server)
        # Ensure fingerprinted messages before cog was online
        for server in self.servers:
            self.read(server, ignore=True)

        # Start Loop Functions
        self.pass_message.start()


    # Update Headers On Launch
    @commands.Cog.listener()
    async def on_ready(self):
        for server in self.servers:
            await self.header_update(server=server)

    # Cog Functions ----------------------------------------------------------------------------------------------------------------------------------------------------------------
    def cog_unload(self):
        self.pass_message.cancel()

    def get_version(self) -> str:
        """
        The Version Of The GameCog To Be Overloaded
        """
        return None

    def find_server(self, cid:int) -> Server:
        """
        Returns the server object with a matching cid, otherwise returns None
        """
        for server in self.servers:
            if server.cid == cid: return server
        return None

    def find_player(self, username:str, server:Server=None, uuid=None) -> tuple:
        """
        Finds player statistics object, returns index of it. Accounts for UUIDs
        Returns [serverIndex, statisticsIndex] with no server, otherwise returns statisticsIndex
        """
        s = 0
        i = 0
        if not uuid:
            uuid = self.get_uuid(username=username)

        if server:
            if uuid:
                for stat in server.statistics:
                        if stat['uuid'] == uuid:
                            print("Got user with server and uuid")
                            return i
                        i+=1
            else:
                for stat in server.statistics:
                        if stat['user'] == uuid:
                            print("Got user with server and no uuid")
                            return i
                        i+=1
        else:
            if uuid:
                for server in self.servers:
                    for stat in server.statistics:
                        if stat['uuid'] == uuid:
                            print("Got user without server and uuid")
                            return s, i
                        i+=1
                    s+=1
            else:
                for server in self.servers:
                    for stat in server.statistics:
                        if stat['user'] == uuid:
                            print("Got user without server and no uuid")
                            return s, i
                        i+=1
                    s+=1
        return None
    # Local Statistics Save/Load/Create ---------------------------------------------------------------------------------------------------------------------------------------------------------
    def load_statistics(self, docker_name:str) -> list:
        """
        For each file in data/servers/{CogName}/{docker_name}, appends dict to list
        Returns list
        """
        stats = []
        try:
            for path in os.listdir(f'data/servers/{__name__}/{docker_name}'):
                with open(path) as f:
                    stats.append(json.load(f))
        except FileNotFoundError:
            # raise NotImplementedError(f"{__name__} Error: No files found for load_statistics")
            pass
        else:
            return stats
        
    def create_statistics(self, server, username:str=None, uuid:str=None):
        """
        Creates a statistics file with given structure for username in server
        {
            username:'',
            uuid:'',
            total_playtime:'',
            calculated_index:0,
            joins:[],
            leaves:[]
        }
        """
        dict = {'total_playtime':'', 'calculated_index':0, 'joins':[], 'leaves':[]}
        if username: dict['username'], filename = username
        if uuid: dict['uuid'], filename = uuid
        
        with open(f'data/servers/{__name__}/{server.docker_name}/{filename}.json', 'w') as f:
            json.dump(dict, f, indent=2)

    def save_statistics(self, server, filename:str, index:int=None):
        ''' 
        Saves file from server statistics dict w/ filename
        ''' 
        try:
            if index:
                with open(f'data/servers/{__name__}/{server.docker_name}/{filename}.json', 'w') as f:
                     json.dump(server.statistics[index], f, indent = 2)
            else:
                with open(f'data/servers/{__name__}/{server.docker_name}/{filename}.json', 'w') as f:
                    json.dump(next(d for i,d in enumerate(server.statistics) if filename in d), f, indent = 2)
        except FileNotFoundError:
            raise NotImplementedError(f"{server.server_name}.{__name__} Error: {filename} does not exist in current filestructure")
        except  StopIteration:
            raise NotImplementedError(f"{server.server_name}.{__name__} Error: {filename} does not exist in statistics database")
    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # GameCog Functions
    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def read(self, server, ignore=False):
        """
        Reads docker logs (Tail defined in database) and appends connections to a connect queue, messages to a message queue.
        """
        # Filters, then reads set_tail_len of logs to an iterable
        container = DB.client.containers.get(server.docker_name)
        response = container.logs(tail=DB.get_tail_len()).decode(encoding="utf-8", errors="ignore")
                
        for msg in response.strip().split('\n'):
            self.filter(message=msg, server=server,ignore=ignore)

    def send(self, server:Server, command:str, logging:bool=False): 
        """
        Sends command to server. Returns a str output of response if logging = True.
        """
        # Attach Container
        container = DB.client.containers.get(server.docker_name)

        # Send Command, and decipher tuple
        filtered_command = command.replace("'", "'\\''") # Single-Quote Filtering (Catches issue #9)
        resp_bytes = container.exec_run(f"{filtered_command}")
        resp_str = resp_bytes[1].decode(encoding="utf-8", errors="ignore")

        if logging:
            print(f"\nSent {command} to {server.server_name}.{__name__}:")
            print(f' --- {resp_str}')
        return resp_str
    
    def filter(self, server, message:str, ignore):
        """
        Filters logs by to gameversion, adding leaves/joins to connectqueue and messages to message queue
        """
        # Fingerprints message, only uniques get sent
        if not server.fingerprint.is_unique_fingerprint(message): return

        # Filter message into a dictionary
        dict = get_msg_dict(username="__default__",message=message,MessageType=MessageType.MSG,color=discord.Color.blue())

        # If Not Ignore, Messages are sent and accounted for playtime
        if dict and (not ignore):
            mtype =dict.get('type')
            if mtype == MessageType.JOIN or mtype == MessageType.LEAVE:
                dict["server"] = server.server_name
                server.connect_queue.put(dict)
            server.message_queue.put(dict)

    # Analytics -------------------------------------------------------------------------------------------------------------------------------------------------------------
    def get_uuid(self, username):
        """
        To Be Overloaded
        Returns UUID of username if present, otherwise returns none.
        """

        return None

    def is_player_online(self, server, playername:str = None) -> bool:
        """
        To be overloaded
        If playername in online_players: Returns True, else False
        Not certain for checking if a player is online, they may be online when this is false.
        """
        if playername:
            for player in server.online_players:
                if playername == player: return True
            return False
        raise NotImplementedError("is_player_online: Called without True playername.")
    
    def handle_connect_queue(self, server:Server):
        """
        Handles connect queue, saving playerstats after modifications, adding modifications to playtime as appropriate
        """
        # Quick Return
        #if server.connect_queue.qsize() == 0: return
        save_list = [] # Logging indexes that need to be saved

        # Add Events
        while not (server.connect_queue.qsize() == 0):
            print("Inside whilenot")
            x = server.connect_queue.get()
            print(f"Got {x}")
            # Add Event
            temp = x.get('type')
            if temp == None: raise NotImplementedError(f"handle_connect_queue none 'type': {x}")
            join = True if temp == MessageType.JOIN else False
            print(f"join = {join}")
            # Player Index Finding &Addition
            try:
                user = x.get('username')
                uuid = self.get_uuid(user)
                player_index = self.find_player(username=user,server=server, uuid=uuid)
            except StopIteration:
                if uuid:
                    self.create_statistics(server=server,username=user, uuid=uuid)
                else:
                    self.create_statistics(server=server,username=user)
                try:
                    player_index = self.find_player(username=user,server=server, uuid=uuid)
                except StopIteration:
                    raise NotImplementedError(f"{__name__}:{server.server_name} handle_connect_queue: {user}:{uuid} player not present in server.statistics {server.statistics}")
            
            # Add Connect Events w/ fixing logic
            recentest_is_join = analytics_lib.is_recentest_join(statistics=server.statistics)
            try:
                if join == True:
                    # If Adding Join, most recent entry is a join, remove previous join
                    if recentest_is_join == True:
                        server.statistics[player_index]['joins'].pop()
                    server.statistics[player_index]['joins'].append(str(x.get('time')))
                elif join == False: 
                    # If adding Leave, most recent entry is a leave, ignore adding leave
                    if recentest_is_join == True:
                        server.statistics[player_index]['leaves'].append(str(x.get('time')))
                save_list.append({'index':player_index,'uuid':uuid,'user':user})
            except:
                print(f"{__name__}:{x} event not added.")

            # Online Logging
            if join and not (x['username'] in server.online_players):
                server.online_players.append(x['username'])
            elif (not join) and (x['username'] in server.online_players): 
                server.online_players.remove(x['username'])

            

        # Save & Update Header
        if save_list:
            loop = asyncio.get_event_loop()
            loop.create_task(self.header_update(server=server))

        for index in save_list:
            if index.get('uuid'): self.save_statistics(server=server, filename=index.get('uuid'),index=index.get('index'))
            else: self.save_statistics(server=server, filename=index.get('user'),index=index.get('index'))
    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # Chat-Link
    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------

    # Server -> Discord -----------------------------------------------------------------------------------------------------------------------------------------------------
    @tasks.loop(seconds=DB.get_chat_link_time())
    async def pass_message(self):
        for server in self.servers:
            self.read(server)
            ctx = self.bot.get_channel(server.cid)

            # Message Queue
            while not (server.message_queue.qsize() == 0): 
                await ctx.send(embed=embed_message(server.message_queue.get()))

            self.handle_connect_queue(server=server)
    @pass_message.before_loop
    async def before_pass_mc_message(self):
        await self.bot.wait_until_ready() 

    # Discord -> Server -----------------------------------------------------------------------------------------------------------------------------------------------------
    @commands.Cog.listener("on_message")
    async def on_disc_message(self, message):
        if message.author.bot or message.content.startswith('>'):
            return
        for server in self.servers:
            if message.channel.id == server.cid:
                self.send_message(server=server, formatted_msg=self.discord_message_format(server=server,message=message))

    def send_message(self, server:Server, formatted_msg):
        """
        To Be Overloaded:
        Sends Message To Server Based On Version Implementation:
         - If no consolebased say command, does nothing.
        """
        print(f"EEE - {formatted_msg} GameCog send_message not implemented.")
        return

    def discord_message_format(self, server:Server, message:str) -> str:
        """
        Formats Message Based On Version: 
         - Default "<User> Message"
         - Logs to console
        """
        item = f"<{message.author.name}> {message.content}"
        print(f" {server.server_name}.{__name__}: {item}")
        return item
                
    # Headers -------------------------------------------------------------------------------------------------------------------------------------------------------------------
    async def header_update(self,server:Server):
         
        # Docker Status Switch
        status = "Online" if (DB.client.containers.get(server.server.get("docker_name")).status.title().strip() == 'Running') else "Offline"
        await self.update_channel_header(server=server, container_status=status)
    
    async def update_channel_header(self, server:Server, container_status : str):
        """
        Updates Linked Discord Channel Heading
        """
        ctx = self.bot.get_channel(server.cid)
        await ctx.edit(topic=f"{split_first(server.version, ':')[0]} {server.server_name} | {len(server.online_players)}/{server.player_max if server.player_max > -1 else 'ꝏ'} | Status: {container_status}")
        print(f"{server.server_name}.{__name__}: Header Updated")
    
    def get_player_list(self, server:dict=None) -> list:
        """
        get_player_list(self) -> ["Playername", "Playername"...]
        For versions without a getlist function, returns None
        Called on cog init for each server

        """
        return None
    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------