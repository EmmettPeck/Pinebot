from dataclasses import dataclass
import discord
from fingerprints import FingerPrints
import queue



@dataclass
class Server:
    # Setup Information
    bot: discord.ext.commands.Bot                       # Bot instance
    server: dict                                        # containers.json dict
    cid: int = server.get("channel_id")                 # Channel ID
    ctx: discord.abc.GuildChannel = bot.get_channel(cid)# Linked Channel
    server_name: str = server.get('name')               # Server Name
    docker_name: str = server.get('docker_name')        # Docker Name
    fingerprint = FingerPrints(docker_name)            # Fingerprint instance

    # Runtime Information
    temp_pl: list = []                                  # Temp List To Switch
    connect_queue = queue.Queue()                       # Connect Queue
    message_queue = queue.Queue()                       # Message Queue
    online_players: list = temp_pl if temp_pl else []   # List of online players
    player_max: int = -1                                # Max Players (Default -1 for ∞)