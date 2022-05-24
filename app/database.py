import json
import queue

import docker

from fingerprints import FingerPrints

def singleton(cls):
    return cls()

@singleton
class DB:
    """A database of all Pinebot information, passed by reference to all methods"""
    def __init__(self):
        self.msg_queue = []
        self.fingerprint = []
        self.cogs = ['cogs.utils', 'cogs.social', 'cogs.owner','cogs.presence', 'cogs.purge', 'cogs.connect4', 'cogs.chatLink', 'cogs.analytics']

        self.load_containers()
        self.load_role_whitelist()
        self.build_msg_queues()
        self.build_fingerprints()

        self.client = docker.from_env()
        # Analytics
        self.connect_queue = queue.Queue()
        self.playerstats = self.load_playerstats()
        if not self.playerstats:
            self.create_playerstats()

    # Role Whitelist -----------------------------------------------------------
    def get_role_whitelist(self):
        """Returns current docker channels managed by Pinebot"""
        return self.role_Whitelist
    
    def load_role_whitelist(self):
        # Load role_Whitelist.json
        with open(r"../data/role_Whitelist.json", 'r') as read_file:
            self.role_Whitelist = json.load(read_file)

    # Docker Containers ---------------------------------------------------------
    def get_containers(self):
        """Returns current docker channels managed by Pinebot"""
        return self.containers
        
    def load_containers(self): 
        with open(r"../data/containers.json", 'r') as read_file:
            self.containers = json.load(read_file)

    def save_containers(self):
        with open(r"../data/containers.json", 'w') as write_file:
            json.dump(self.containers, write_file, indent = 2)

    def add_container(self, sDict):
        self.add_msg_queue()
        self.containers.append(sDict)
        self.save_containers()

    def remove_container(self, popID):
        self.containers.pop(popID)
        self.save_containers()

    # Msg Queues -------------------------------------------------------
    def add_msg_queue(self):
        self.msg_queue.append(queue.Queue())

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
    # Playerstats -----------------------------------------------------------
    def add_connect_event(self, msg, server):
        x = msg
        x['server'] = server
        self.connect_queue.put(x)

    def get_connect_queue(self):
        return self.connect_queue

    def load_playerstats(self):
        """Load playerstats from playerstats.json"""
        try:
            with open("../data/playerstats.json") as f:
                e = json.load(f)
        except FileNotFoundError:
            return None
        else:
            return e

    def save_playerstats(self):
        """Saves playerstats to playerstats.json"""
        with open("../data/playerstats.json", 'w') as f:
            json.dump(self.playerstats, f, indent = 2)
    
    def create_playerstats(self):
        """Creates empty playerstats.json structure""" 
        self.playerstats = [{'UUID':'','Servers':[]}]
        for server in self.containers:
            self.add_server(server['name'])
        self.save_playerstats()

# Server Add/Remove ------------------------------------------------------------------------------------------------------------------------------------------------
    def add_server(self, servername):
        """Adds empty server stats to all players"""
        server_list = []
        # Lists all servers from first entry in DB
        for item in self.playerstats[0]["Servers"]:
            server_list.extend(item.keys())

        # Catch if server already exists
        if servername in server_list:
            print(f"ERROR: add_server {servername} already present.")
            return False

        for player in self.playerstats:
            serv = {f'{servername}':{'Total Playtime':[],'Last Computed':[], 'Joins':[], 'Leaves':[]}}
            player['Servers'].append(serv)
        print(f"ADDED: added server {servername}")
        self.save_playerstats()
        return True