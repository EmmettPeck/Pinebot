"""Manages listener processes to get docker log updates"""
import docker
import asyncio
from multiprocessing import Process, Queue, current_process, cpu_count

from messages import MessageFilter

class DockingListener:
    """Listener manages input list of dockerids"""

    def __init__(self, nodes):
        print("### STARTING DOCKER LISTENER")
        self.nodes = nodes
        self.filter = MessageFilter()
        self.processes = [] 
        self.line_queues = []
        self.msg_queues = []
        self.client = docker.from_env()

        if cpu_count() < len(nodes):
            print("## WARNING: More container listeners than cpus")
        
        # Make queue for each node
        for i in range(len(nodes)):
            self.line_queues.append(Queue())
            self.msg_queues.append(Queue())
        print(f"## {i} line_queues built.")
        print(f"## {i} msg_queues built.")

        self.listener_manager()

    def __del__(self):
        for process in self.processes:
            process.join()
    
    def listener_manager(self, nodes):
        """Starts listener processes and handles logs"""
        for i in range(len(nodes)):
            p = Process(target=self.container_listener, args=(nodes[i-1],i-1))
            self.processes.append(p)
            p.start()
        
        # Turn line_queues into msg_queues
        while True:
            i = 0
            for queue in self.line_queues:
                while not queue.empty():
                    # Send line to right version filter
                    line = queue.get()
                    version = nodes[i]["version"]
                    if version.startswith("1.18"):
                        self.msg_queues[i].append(self.filter.filter_mc_1_18(line))
                i += 1

    def container_listener(self, node, num):
        """Sends new messages to queue"""
        container = self.client.containers.get(node['container_name'])
        print("###" + current_process().name + " listening to " + str(container))
        # Read Live Docker Logs
        for line in container.logs(stream=True):
            self.queue[num].put(line)
