#   dockingPort.py
#   by: Emmett Peck
"""Handles interracting with docker minecraft servers"""

import json
import subprocess
import docker

from messages import MessageFilter

client = docker.from_env()

class DChannels:
    def __init__(self):
        self.DChannels = self.load_DChannels()

    def get_DChannels(self):
        return self.DChannels

    def load_DChannels(self): 
        with open(r"data/mc_Channels.json", 'r') as read_file:
            return json.load(read_file)

    def save_DChannels(self, var=self.mc_Channels):
        # Overwrites json -- Careful
        with open(r"data/mc_Channels.json", 'w') as write_file:
            json.dump(var, write_file, indent = 2)

class DockingPort:

    def __init__(self):
        dchannel = DChannels()
        self.mc_Channels = dchannel.get_DChannels()
        self.filter = MessageFilter()

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

class Manager:
    """Listener manages input list of dockerids"""
