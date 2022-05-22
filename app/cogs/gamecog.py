import asyncio
from discord.ext import tasks, commands

from database import DB
from embedding import embed_message
from messages import MessageType, split_first
from server import Server
import analytics_lib


class GameCog(commands.Cog):
    """
    GameCog - A discord game cog w/ ChatLink & Playtime logging
    
    For A Game Specific Cog, Implement:
    - Send
    - Filter
    - get_player_list
    """

    def __init__(self, bot):
        self.bot = bot
        self.servers = []
        
        # For server in DB, check if matches game
        for cont in DB.get_containers():
            if split_first(cont.get('version'),':')[0] == self.get_version():
                self.servers.append(Server(server=cont, bot=bot, temp_pl=self.get_player_list(cont)))

        # Ensure fingerprinted messages before cog was online
        for server in self.servers:
            self.read(server, ignore=True)

        # Start Loop Functions
        self.pass_message.start()

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

        # If Not Ignore, Messages are sent and accounted for playtime
        if message and (not ignore):
            mtype = message.get('type')
            if mtype == MessageType.JOIN or mtype == MessageType.LEAVE:
                message["server"] = server.server_name #TODO Unsafe access?
                server.connect_queue.put(message)
            server.message_queue.put(message)

    # Analytics -------------------------------------------------------------------------------------------------------------------------------------------------------------
    def is_player_online(self, server, uuid_index:int = None, playername:str = None) -> bool:
        """
        If uuid_index or playername in online_players: Returns True, else False
        """
        if uuid_index:
            for player in server.online_players:
                if analytics_lib.get_player_uuid(player) == DB.playerstats[uuid_index]["UUID"]: return True
            return False
        elif playername:
            for player in server.online_players:
                if playername == player: return True
            return False
        raise NotImplementedError("is_player_online: Called without True uuid or playername.")
    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def handle_connect_queue(self, server:Server):
        """
        Handles connect queue, saving playerstats after modifications, adding modifications to playtime as appropriate
        """
        # Quick Return
        if server.connect_queue.qsize() == 0: return

        # Add Events
        while not server.connect_queue.qsize() == 0:
            x = server.connect_queue.get()
            
            # Add Event
            temp = x.get('type')
            if temp == None: raise NotImplementedError(f"handle_connect_queue none 'type': {x}")
            join = True if temp == MessageType.JOIN else False
            analytics_lib.add_connect_event(x['username'], x['server'], join, x['time']) # TODO #46
            
            # Online Logging
            if join and not (x['username'] in server.online_players):
                server.online_players.append(x['username'])
            elif (not join) and (x['username'] in server.online_players): 
                server.online_players.remove(x['username'])

        # Update Header & Save
        loop = asyncio.get_event_loop()
        loop.create_task(self.header_update(server=server))
        DB.save_playerstats()

    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # Chat-Link
    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------

    # Server -> Discord -----------------------------------------------------------------------------------------------------------------------------------------------------
    @tasks.loop(seconds=DB.get_chat_link_time())
    async def pass_message(self):
        for server in self.servers:
            self.read(server.cid)

            # Message Queue
            while not server.message_queue.qsize() == 0: 
                await server.ctx.send(embed=embed_message(server.message_queue.get()))
            # Connect Queue
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
                self.send_message(self, server=server, formatted_msg = self.discord_message_format(server=server,message=message))

    def send_message(self, server:Server, formatted_msg):
        """
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
        await server.ctx.edit(topic=f"{server.server_name} | {len(server.online_players)}/{server.player_max if server.player_max > -1 else '∞'} | Status: {container_status}")
    
    def get_player_list(self, server:dict=None) -> list:
        """
        get_player_list(self) -> ["Playername", "Playername"...]
        For versions without a getlist function, returns None
        Called on cog init for each server

        """
        return None
    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------