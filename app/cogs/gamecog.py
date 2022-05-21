from discord.ext import tasks, commands

import queue

from database import DB
from embedding import embed_message
from messages import MessageType
import analytics_lib
from fingerprints import FingerPrints


class GameCog(commands.Cog):
    """
    GameCog - A discord game cog w/ ChatLink & Playtime logging
    
    For A Game Specific Cog, Implement:
    - Send
    - Filter
    - get_player_list
    """

    def __init__(self, bot, server):
        self.bot = bot
        self.server = server                            # containers.json dict

        # Container Information
        self.cid: int = self.server.get("channel_id")   # Channel ID
        self.ctx = self.bot.get_channel(self.cid)       # Linked Channel
        self.server_name: str = self.server.get('name') # Server Name
        self.docker_name: str = self.server.get('docker_name')
        
        self.fingerprints = FingerPrints(self.docker_name)  # Fingerprint instance

        # Runtime Information
        temp = self.get_player_list()
        self.connect_queue = queue.Queue()
        self.message_queue = queue.Queue()
        self.online_players: list = temp if temp else []# List of online players
        self.player_max: int = -1                       # Max Player Count (Default -1 for ∞)

        # Ensure fingerprinted messages before cog was online
        self.read(ignore=True)

        # Start Loop Functions
        self.pass_message.start()

    # Unload ----------------------------------------------------------------------------------------------------------------------------------------------------------------
    def cog_unload(self):
        self.pass_message.cancel()
    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # GameCog Functions
    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def read(self, ignore=False):
        """
        Reads docker logs (Tail defined in database) and appends connections to a connect queue, messages to a message queue.
        """
        # Filters, then reads set_tail_len of logs to an iterable
        container = DB.client.containers.get(self.docker_name)
        response = container.logs(tail=DB.get_tail_len()).decode(encoding="utf-8", errors="ignore")
                
        for msg in response.strip().split('\n'):
            self.filter(msg, ignore)

    def send(self, command, logging=False): 
        """
        Sends command to server. Returns a str output of response if logging = True.
        """
        # Attach Container
        container = DB.client.containers.get(self.docker_name)

        # Send Command, and decipher tuple
        filtered_command = command.replace("'", "'\\''") # Single-Quote Filtering (Catches issue #9)
        resp_bytes = container.exec_run(f"{filtered_command}")
        resp_str = resp_bytes[1].decode(encoding="utf-8", errors="ignore")

        if logging:
            print(f"\nSent {command} to {self.server_name}.{__name__}:")
            print(f' --- {resp_str}')
        return resp_str
    
    def filter(self, message:str, ignore):
        """
        Filters logs by to gameversion, adding leaves/joins to connectqueue and messages to message queue
        """
        # Fingerprints message, only uniques get sent
        if not self.fingerprint.is_unique_fingerprint(message): return

        # If Not Ignore, Messages are sent and accounted for playtime
        if message and (not ignore):
            mtype = message.get('type')
            if mtype == MessageType.JOIN or mtype == MessageType.LEAVE:
                message["server"] = self.server_name #TODO Unsafe access?
                self.connect_queue.put(message)
            self.message_queue.put(message)


    # Analytics -------------------------------------------------------------------------------------------------------------------------------------------------------------
    def is_player_online(self, uuid_index:int = None, playername:str = None) -> bool:
        """
            If uuid_index or playername in online_players: Returns True, else False
        """
        if uuid_index:
            for player in self.online_players:
                if analytics_lib.get_player_uuid(player) == DB.playerstats[uuid_index]["UUID"]: return True
            return False
        elif playername:
            for player in self.online_players:
                if playername == player: return True
            return False
        raise NotImplementedError("is_player_online: Called without True uuid or playername.")
    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def handle_connect_queue(self):
        """
        Handles connect queue, saving playerstats after modifications, adding modifications to playtime as appropriate
        """
        # Quick Return
        if self.connect_queue.qsize() == 0: return

        # Add Events
        while not self.connect_queue.qsize() == 0:
            x = self.connect_queue.get()
            
            temp = x.get('type')
            if temp == None: raise NotImplementedError(f"handle_connect_queue none 'type': {x}")
            join = True if temp == MessageType.JOIN else False
            analytics_lib.add_connect_event(x['username'], x['server'], join, x['time']) # TODO #46
            
            #TODO Implement online logging for header
            if join and not (x['username'] in self.online_players):
                self.online_players.append(x['username'])
            else: 
                # LEAVE REMOVE TODO
                pass
        DB.save_playerstats()

    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # Chat-Link
    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------

    # Server -> Discord -----------------------------------------------------------------------------------------------------------------------------------------------------
    @tasks.loop(seconds=DB.get_chat_link_time())
    async def pass_message(self):
        self.read(self.cid)

        # Message Queue
        while not self.message_queue.qsize() == 0: 
            await self.ctx.send(embed=embed_message(self.message_queue.get()))
        # Connect Queue
        self.handle_connect_queue()

    @pass_message.before_loop
    async def before_pass_mc_message(self):
        await self.bot.wait_until_ready() 

    # Discord -> Server -----------------------------------------------------------------------------------------------------------------------------------------------------
    @commands.Cog.listener("on_message")
    async def on_disc_message(self, message):
        if message.author.bot or message.content.startswith('>'):
            return
        elif message.channel.id == self.cid:
            self.send_message(self, self.discord_message_format(message))

    def send_message(self, formatted_msg):
        """
        Sends Message To Server Based On Version Implementation:
         - If no consolebased say command, does nothing.
        """
        print(f"EEE - {formatted_msg} GameCog send_message not implemented.")
        return

    def discord_message_format(self, message) -> str:
        """
        Formats Message Based On Version: 
         - Default "<User> Message"
         - Logs to console
        """
        item = f"<{message.author.name}> {message.content}"
        print(f" {self.server_name}.{__name__}: {item}")
        return item
                
    # Headers -------------------------------------------------------------------------------------------------------------------------------------------------------------------
    async def header_update(self):
         
        # Docker Status Switch
        status = "Online" if (DB.client.containers.get(self.server.get("docker_name")).status.title().strip() == 'Running') else "Offline"
        await self.update_channel_header(status)
    
    async def update_channel_header(self, container_status : str):
        """
        Updates Linked Discord Channel Heading
        """
        await self.ctx.edit(topic=f"{self.server_name} | {len(self.online_players)}/{self.player_max if self.player_max > -1 else '∞'} | Status: {container_status}")
    
    def get_player_list(self) -> list:
        """
        get_player_list(self) -> ["Playername", "Playername"...]
        For versions without a getlist function, returns None

        """
        return None
    # -----------------------------------------------------------------------------------------------------------------------------------------------------------------------