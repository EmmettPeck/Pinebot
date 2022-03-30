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
        print(f"## {i+1} line_queues built.")
        print(f"## {i+1} msg_queues built.")

        self.listener_manager(self.nodes)

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
                        self.msg_queues[i].put(self.filter.filter_mc_1_18(line))
                i += 1

    def container_listener(self, node, num):
        """Sends new messages to queue"""
        try:
            container = self.client.containers.get(node['docker_name'])
        except docker.errors.NotFound:
            print (f"ERROR: {node['docker_name']} not found by {current_process().name}")
        except docker.errors.APIError:
            print (f"ERROR: {node['docker_name']} raised APIERROR when accessed by {current_process().name}")        
        print("### " + current_process().name + " listening to " + str(container))
        """CONVERT TO SINCE logs using datetime && async functions"""
        for line in container.logs(follow=True): 
            self.line_queues[num].put(str(line))
