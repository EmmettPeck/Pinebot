#   dockingPort.py
#   by: Emmett Peck
"""Handles interracting with docker minecraft servers"""

import json
import subprocess
import docker

from messages import MessageFilter
from dockingListener import DockingListener

client = docker.from_env()

def singleton(cls):
    return cls()

@singleton
class DChannels:
    """Handles channel/docker information serialization"""
    def __init__(self):
        self.DChannels = self.load_channels()

    def get_channels(self):
        """Returns current channels"""
        return self.DChannels

    def remove_channel(self, index):
        """Pops item[index] from DChannels"""
        self.DChannels.pop(index)
        self.save_DChannels()

    def add_channel(self, dictionary):
        """Adds dict and reloads dependencies"""
        self.DChannels.append(dictionary)
        self.save_DChannels()
        DockingPort.reload()

    def load_channels(self): 
        with open(r"data/mc_Channels.json", 'r') as read_file:
            return json.load(read_file)

    def save_channels(self):
        # Overwrites json -- Careful
        with open(r"data/mc_Channels.json", 'w') as write_file:
            json.dump(self.DChannels, write_file, indent = 2)

@singleton
class DockingPort:
    """Handles docker interaction on hostsystem"""
    def __init__(self):
        self.filter = MessageFilter()
        self.nodes = DChannels.get_channels()
        self.listener = DockingListener(self.nodes)

    def reload(self):
        """Reloads dockingPort to match updated D_Channels"""
        self.nodes = DChannels.get_channels()
        del self.listener
        self.listener = DockingListener(self.nodes)

    def send(self, channelID, command, logging=False): 
        """Sends command to corresponding server. Returns a str output of response."""
        for channel in self.nodes: 
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

    def get_msg_queue(self, server_index):
        """Returns queue to specified docker channel"""
        return self.msg_queues[server_index]