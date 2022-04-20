"""
dockingPort.py
By: Emmett Peck
Handles interraction with docker game servers
### How to reload functions effectively? How far do pointers go, as will changing DChannels here result in a different self.nodes in DockingListener?
"""

import asyncio
import json
import queue
import subprocess

import docker

from messages import MessageFilter


def singleton(cls):
    return cls()

# --------------------------------------------------------------------------
@singleton
class DChannels:
    """Handles channel/docker information serialization"""
    def __init__(self):
        self.DChannels = self.load_channels()

    def get_channels(self):
        """Returns current docker channels managed by Pinebot"""
        return self.DChannels
        
    def load_channels(self): 
        with open(r"data/containers.json", 'r') as read_file:
            return json.load(read_file)

    def save_channels(self):
        with open(r"data/containers.json", 'w') as write_file:
            json.dump(self.DChannels, write_file, indent = 2)
# --------------------------------------------------------------------------------------------------------------------------------------------
class DockingListener:
    """Manages listener processes to get accurate docker log updates"""

    def __init__(self, nodes):
        self.nodes = nodes
        self.loop = asyncio.get_event_loop()
        self.line_queues = []                       # List of queues of unprocessed str
        self.msg_queues = []                        # List of queues of processed dicts
        self.client = docker.from_env()
        
        # Make queue for each node
        for i in range(len(self.nodes)):
            self.line_queues.append(queue.Queue())
            self.msg_queues.append(queue.Queue())
        print(f"Built queues for {i+1} containers")

        # Start listeners
        asyncio.ensure_future(self.listener_manager())

    def get_queue(self, index):
        """Returns queue of message dictionaries for given index"""
        return self.msg_queues[index]
    
    async def listener_manager(self):
        """Begins async event loop"""

        # Start async processes based on server dict index
        await asyncio.gather(*[self.container_listener(self.nodes[i],i) for i in range(len(self.nodes))])

        #for i in range(len(self.nodes)):
         #   asyncio.ensure_future(self.container_listener(self.nodes[i], i))

        # Start msgqueue processing
        #for i in range(len(self.nodes)):
            #asyncio.ensure_future(self.process_line_queue(self.nodes[i],i))
        await asyncio.gather(*[self.process_line_queue(self.nodes[i],i) for i in range(len(self.nodes))])

    async def process_line_queue(self, node, index):
        """Processes node w/ corresponding index's line queue int msg queue"""
        q = self.line_queues[index]
        q.join()
        # Send line to right version filter
        while True:
            try:
                line = q.get()
                text = MessageFilter().filter_mc_1_18(line)

                #self.msg_queues[index].put({"time":"Test", "username":"Test", "message": "Test", "type": 1}) #Test for dict access outside dockingport 
                if text:
                    self.msg_queues[index].put(text)
                    print(f"Q- {text} added to queue.")
            except queue.Empty:
                break

    async def container_listener(self, node, num):
        """Sends new messages to queue"""
        
        try: # Get Docker Container
            container = self.client.containers.get(node['docker_name'])
        except docker.errors.NotFound:
            print (f"ERROR: {node['docker_name']} not found.")
        except docker.errors.APIError:
            print (f"ERROR: {node['docker_name']} raised APIERROR.")

        # Attach to container logs
        for line in container.attach(stream=True, logs=True): 
            self.line_queues[num].put(bytes.decode(line))
            await asyncio.sleep(0)
            # count iterable, then iterate that many times, creating that many hashes? What are the right options for this?
            # read function?
            # What if we used the old commandline read function, and docker attach to more securely send data? It isn't like we need all this complexity, right?
            # As simple as functional
# --------------------------------------------------------------------------------------------------------------------------------------------
class DockingPort(commands.Cog):
    """Handles docker interaction on hostsystem"""
    def __init__(self):
        self.filter = MessageFilter()
        self.nodes = DChannels.get_channels()
        self.listener = DockingListener(self.nodes)

    def reload(self):
        """Reloads dockingPort to match updated D_Channels"""
        del self.listener
        self.nodes = DChannels.get_channels()
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

def setup(bot):
    bot.add_cog(DockingPort(bot))      