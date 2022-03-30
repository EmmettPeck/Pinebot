"""Manages listener processes to get docker log updates"""
import docker
import asyncio
from multiprocessing import Queue
from dockingPort import DChannels

from messages import MessageFilter

class DockingListener:
    """Listener manages input list of dockerids"""

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
