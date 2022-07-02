from dataclasses import dataclass
import discord
from fingerprints import FingerPrints
import queue
from messages import split_first


@dataclass
class Server:
    # Parameters
    bot: discord.ext.commands.Bot # Bot instance
    server: dict                  # containers.json dict
    statistics: list              # Statistics Filetree
    # Post
    online_players: list = None         # List of online players
    cid: int = None                     # Channel ID
    server_name: str = None             # Server Name
    docker_name: str = None             # Docker Name
    cog_name: str = None
    version: str = None                 # Server Version
    fingerprint: FingerPrints = None    # Fingerprint instance
    connect_queue: queue.Queue = None   # Connect Queue
    message_queue: queue.Queue = None   # Message Queue
    player_max: int = -1                # Max Players (Default -1 for ∞)
    link_keys: list = None              # Codes to check against new msgs

    def __post_init__(self):
        self.link_keys = []
        self.connect_queue = queue.Queue()  # Connect Queue
        self.message_queue = queue.Queue()
        self.version = self.server.get('version')
        self.cid = self.server.get('channel_id')
        self.server_name = self.server.get('name')
        self.docker_name = self.server.get('docker_name')
        self.fingerprint = FingerPrints(self.docker_name)
    
    
    ''' Statistics Filetree
    For manipulation and access on load, not held in memory due to large amounts of data
        - data
            - accounts
                - {discord_player_id}.json
                    [Linked accounts (Each link points to a user in a server)]
            - hash
            - servers
                - Minecraft
                    - main_2021_1
                        - {uuid}.json
                        - {uuid}.json
                - Factorio
                    - factorio_1
                        - Emmettdogg.json
                        - Time_X.json
            - containers.json
            - role_Whitelist.json
    '''