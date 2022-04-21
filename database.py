import json
import queue

from fingerprints import FingerPrints

def singleton(cls):
    return cls()

@singleton
class DB:
    """A database of all Pinebot information, passed by reference to all methods"""
    def __init__(self):
        self.msg_queue = []
        self.fingerprint = []
        self.cogs = ['cogs.utils', 'cogs.social', 'cogs.owner','cogs.presence', 'cogs.purge', 'cogs.connect4', 'cogs.chatLink']

        self.load_containers()
        self.load_role_whitelist()
        self.build_msg_queues()
        self.build_fingerprints()

    # Role Whitelist -----------------------------------------------------------
    def get_role_whitelist(self):
        """Returns current docker channels managed by Pinebot"""
        return self.role_Whitelist
    
    def load_role_whitelist(self):
        # Load role_Whitelist.json
        with open(r"data/role_Whitelist.json", 'r') as read_file:
            self.role_Whitelist = json.load(read_file)

    # Docker Containers ---------------------------------------------------------
    def get_containers(self):
        """Returns current docker channels managed by Pinebot"""
        return self.containers
        
    def load_containers(self): 
        with open(r"data/containers.json", 'r') as read_file:
            self.containers = json.load(read_file)

    def save_containers(self):
        with open(r"data/containers.json", 'w') as write_file:
            json.dump(self.containers, write_file, indent = 2)

    def add_container(self, sDict):
        self.containers.append(sDict)
        self.save_containers()

    def remove_container(self, popID):
        self.containers.pop(popID)
        self.save_containers()

    # Msg Queues -------------------------------------------------------
    def build_msg_queues(self):
        for i in range(len(self.get_containers())):
            self.msg_queue.append(queue.Queue())

    def get_msg_queue(self, index):
        return self.msg_queue[index]

    # Fingerprints ------------------------------------------------------
    def build_fingerprints(self):
        containers = self.get_containers()
        for i in range(len(self.get_containers())):
            self.fingerprint.append(FingerPrints(containers[i]['docker_name']))

    def get_cogs(self):
        return self.cogs