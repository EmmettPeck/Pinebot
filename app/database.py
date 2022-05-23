import json
import queue

import docker

def singleton(cls):
    return cls()

@singleton
class DB:
    """A database of all Pinebot information, passed by reference to all methods"""
    def __init__(self):
        self.game_cogs = ['cogs.minecraft','cogs.factorio']
        self.cogs = ['cogs.utils', 'cogs.social', 'cogs.owner','cogs.presence', 'cogs.purge', 'cogs.analytics']
        self.load_containers()
        self.load_role_whitelist()
        self.client = docker.from_env()

        # Timing ------------------------------------------------
        self.chat_link_time = 1
        self.tail_len = 10

    # Timing -------------------------------------------------------------------
    def get_chat_link_time(self):
        return self.chat_link_time

    def get_tail_len(self):
        return self.tail_len

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
        self.containers.append(sDict)
        self.save_containers()

    def remove_container(self, popID):
        self.containers.pop(popID)
        self.save_containers()

    # Cogs -------------------------------------------------------------------
    def get_cogs(self):
        return self.cogs + self.game_cogs

    def get_game_cogs(self):
        return self.game_cogs

# Server Management ------------------------------------------------------------------------------------------------------------------------------------------------
def add_server(servername):
    """Adds empty server stats to all players"""
    server_list = []
    # Lists all servers from first entry in DB
    for item in DB.playerstats[0]["Servers"]:
        server_list.extend(item.keys())

    # Catch if server already exists
    if servername in server_list:
        print(f"ERROR: add_server {servername} already present.")
        return False

    for player in DB.playerstats:
        serv = {f'{servername}':{'Total Playtime':[],'Last Computed':[], 'Joins':[], 'Leaves':[]}}
        player['Servers'].append(serv)
    print(f"ADDED: added server {servername}")
    DB.save_playerstats()
    return True