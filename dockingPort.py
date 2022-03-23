#   dockingPort.py
#   by: Emmett Peck
"""A python library that allows interracting with docker minecraft servers on PineServer"""

import json
import subprocess
import docker

from messages import Death
from messages import MessageType
from messages import MessageFilter

client = docker.from_env()

class DockingPort():

    def __init__(self):
        self.mc_Channels = self.load_mc_Channels()
        self.filter = MessageFilter()

    def load_mc_Channels(self): 
        with open(r"data/mc_Channels.json", 'r') as read_file:
            return json.load(read_file)

    def save_mc_Channels(self):
        # Overwrites json -- Careful
        with open(r"data/mc_Channels.json", 'w') as write_file:
            json.dump(self.mc_Channels, write_file, indent = 2)

    def portSend(self, channelID, command, logging=False): 
        """Sends command to corresponding server. Returns a str output of response."""
        for channel in self.mc_Channels: 
                if channelID == channel.get('channel_id'):
                    dockerName = channel.get('docker_name')
                    filtered_command = command.replace("'", "'\\''") # Single-Quote Filtering (Catches issue #9)
                    resp_bytes = subprocess.Popen(f"docker exec {dockerName} rcon-cli '{filtered_command}'", stdout=subprocess.PIPE, shell=True).stdout.read()
                    resp_str = resp_bytes.decode(encoding="utf-8", errors="ignore")
                    
                    if logging:
                        print(f"\nSent command /{command} to {dockerName}")
                        print(f' --- {resp_str}')
                    return resp_str
        return None

    def portRead(self, channelID):
        """Awaits text in streamed dockerlogs, sends parsed message to chat_link"""
        # Filters for channel, then converts tail 10 of the logs to a string
        for channel in self.mc_Channels:
            if channelID == channel.get('channel_id'):
                dockerName = channel.get('docker_name') 
                resp_bytes = subprocess.Popen(f'docker logs {dockerName} --tail 10', stdout=subprocess.PIPE, shell=True).stdout.read()
                resp_str = resp_bytes.decode(encoding="utf-8", errors="ignore")
                break
        return self.filter.filter_mc_1_18(resp_str)