"""
dockingPort.py
By: Emmett Peck
Handles interraction with docker game servers
### How to reload functions effectively? How far do pointers go, as will changing DChannels here result in a different self.nodes in DockingListener?
"""

import asyncio
from datetime import datetime
import json
import subprocess
import queue

import docker
from messages import MessageFilter

def singleton(cls):
    return cls()

@singleton
class DChannels:
    """Handles channel/docker information serialization"""
    def __init__(self):
        self.DChannels = self.load_channels()

    def get_channels(self):
        """Returns current docker channels managed by Pinebot"""
        return self.DChannels

# DT ----------------------------------
# Datetimes stored as formatted strings in DChannels, get_dt_accessed returns list of datetimes
    async def get_dt_accessed(self):
        """Returns list of last accessed DT for DChannels"""
        list = []
        save = False
        i = 0
        for channel in self.DChannels:
            if not "dt_accessed" in channel: 
                self.DChannels[i]['dt_accessed'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
                save = True
            list.append(self.DChannels[i]['dt_accessed'])
            i += 1
        if save: self.save_channels()

        i = 0
        for item in list:
            list[i] = datetime.strptime(item,'%Y-%m-%dT%H:%M:%S.%f') 
            i += 1
        return list

    def set_dt(self, index, dt = datetime.now()):
        """Sets datetime of serverindex to now or specified time"""
        self.DChannels[index]['dt_accessed'] = dt.strftime('%Y-%m-%dT%H:%M:%S.%f')

    async def get_dt(self, index):
        """Returns dt_accessed of given index"""
        return datetime.strptime(self.DChannels[index]['dt_accessed'], '%Y-%m-%dT%H:%M:%S.%f')
# ---------------------------------------
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
        with open(r"data/mc_Channels.json", 'w') as write_file:
            json.dump(self.DChannels, write_file, indent = 2)

class DockingListener:
    """Manages listener processes to get accurate docker log updates"""

    def __init__(self, nodes):
        self.nodes = nodes
        self.line_queues = []                       # List of queues of unprocessed str
        self.msg_queues = []                        # List of queues of processed dicts  # Log of previous dt vals for use with docker logs since
        self.client = docker.from_env()
        
        # Make queue for each node
        for i in range(len(nodes)):
            self.line_queues.append(queue.Queue())
            self.msg_queues.append(queue.Queue())
        print(f"Built queues for {i+1} containers")

    def get_queue(self, index):
        return self.msg_queues[index]
    
    async def listener_manager(self):
        """Calls multiple async listeners"""
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
            text = MessageFilter().filter_mc_1_18(line)
            #self.msg_queues[index].put({"time":"Test", "username":"Test", "message": "Test", "type": 1}) #Test for dict access outside dockingport 
            if text:
                self.msg_queues[index].put(text)
                print(f"Q- {text} added to queue.")

    async def container_listener(self, node, num):
        """Sends new messages to queue"""
        try:
            container = self.client.containers.get(node['docker_name'])
        except docker.errors.NotFound:
            print (f"ERROR: {node['docker_name']} not found.")
        except docker.errors.APIError:
            print (f"ERROR: {node['docker_name']} raised APIERROR.")

        # Check docker logs since last dt
        now = datetime.now()
        t = await DChannels.get_dt_accessed()
        print(f"--#{num} - {t[num]} - {type(t[num])}")
        for line in container.logs(since=t[num]): 
            self.line_queues[num].put(str(line))
            print(str(line) + f" {type(line)}")
        # Compare end compute time to precompute time as messages could get printed twice if sent after now, but before log compute
        DChannels.set_dt(num, now)

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
    
    async def listen(self):
        """Listen to """
        await self.listener.listener_manager()

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
        return self.listener.msg_queues[server_index]