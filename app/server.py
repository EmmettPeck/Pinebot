from dataclasses import dataclass
import discord
from fingerprints import FingerPrints
import queue



@dataclass
class Server:
    # Requires Parameters
    bot: discord.ext.commands.Bot                       # Bot instance
    server: dict                                        # containers.json dict
    temp_pl: list = []                                  # Temp Online List To Switch
    statistics: list = []                               # Statistics Filetree

    # Auto-Generates
    cid: int = server.get("channel_id")                 # Channel ID
    ctx: discord.abc.GuildChannel = bot.get_channel(cid)# Linked Channel
    server_name: str = server.get('name')               # Server Name
    docker_name: str = server.get('docker_name')        # Docker Name
    fingerprint = FingerPrints(docker_name)             # Fingerprint instance
    connect_queue = queue.Queue()                       # Connect Queue
    message_queue = queue.Queue()                       # Message Queue
    online_players: list = temp_pl if temp_pl else []   # List of online players
    player_max: int = -1                                # Max Players (Default -1 for ∞)
                                                      
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