"""
dockingPort.py
By: Emmett Peck
Handles interraction with docker game servers
"""

import asyncio
import datetime
import json
import subprocess
from multiprocessing import Queue

import docker

from messages import MessageFilter

def singleton(cls):
    return cls()

@singleton
class DChannels:
    """Handles channel/docker information serialization"""
    def __init__(self):
        self.DChannels = self.load_channels()
        self.dt_accessed = self.get_dt_accessed()

    def get_channels(self):
        """Returns current channels"""
        return self.DChannels

    def get_dt_accessed(self):
        """Returns list of last accessed DT"""
        list = []

        for channel in self.DChannels:
            if not "dt_accessed" in channel:
                channel['dt_accessed'] = datetime.datetime.now()
            list.append(channel['dt_accessed'])
        self.save_channels()
        return list

    def get_dt(self, index):
        return self.dt_accessed[index]

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
        return self.listener.get_queue(server_index)

    
class DockingListener:
    """Manages listener processes to get accurate docker log updates"""

    def __init__(self, nodes):
        self.nodes = nodes
        self.line_queues = []                       # List of queues of unprocessed str
        self.msg_queues = []                        # List of queues of processed dicts  # Log of previous dt vals for use with docker logs since
        self.client = docker.from_env()
        
        # Make queue for each node
        for i in range(len(nodes)):
            self.line_queues.append(Queue())
            self.msg_queues.append(Queue())

        self.listener_manager()

    def get_queue(self, index):
        return self.msg_queues[index]
    
    async def listener_manager(self):
        """Calls multiple async listeners on event loop"""
        # Start async processes based on server dict index
        await asyncio.gather(*[self.container_listener(self.nodes[i],i) for i in range(len(self.nodes))])
        # Start msgqueue processing
        await asyncio.gather(*[self.line_msg_queue(self.nodes[i],i) for i in range(len(self.nodes))])

    async def line_msg_queue(self, node, index):
        """Processes node w/ corresponding index's line queue int msg queue"""
        queue = self.line_queues[index]
        while not queue.empty():
            # Send line to right version filter
            line = queue.get()
            version = node["version"]
            if version.startswith("mc_1.18"):
                self.msg_queues[index].put(MessageFilter().filter_mc_1_18(line))

    async def container_listener(self, node, num):
        """Sends new messages to queue"""
        try:
            container = self.client.containers.get(node['docker_name'])
        except docker.errors.NotFound:
            print (f"ERROR: {node['docker_name']} not found.")
        except docker.errors.APIError:
            print (f"ERROR: {node['docker_name']} raised APIERROR.")

        """CONVERT TO SINCE logs using datetime && async functions"""
        for line in container.logs(since=DChannels.get_dt()): 
            self.line_queues[num].put(str(line))