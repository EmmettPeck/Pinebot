from dataclasses import dataclass
import discord
from fingerprints import FingerPrints
import queue



@dataclass
class Server:
    bot: discord.ext.commands.Bot  # Bot instance
    server: dict                   # containers.json dict
    statistics: list               # Statistics Filetree
    cid: int                       # Channel ID
    server_name: str               # Server Name
    docker_name: str               # Docker Name
    version: str                   # Server Version
    fingerprint: any               # Fingerprint instance
    connect_queue = queue.Queue()  # Connect Queue
    message_queue = queue.Queue()  # Message Queue
    online_players: list           # List of online players
    player_max: int = -1           # Max Players (Default -1 for ∞)
                                                      
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