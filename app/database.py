"""
Module containing singleton class for data access across multiple discord cogs.

This module handles file loading and saving for settings information for PineBot

Authors: Emmett Peck (EmmettPeck)
Version: July 1st, 2022
"""

import json
import docker

def singleton(cls):
    return cls()

@singleton
class DB:
    """
    A singleton class containing settings information for data access across 
    multiple discord cogs. Handles saving/loading of settings information.
    """
    def __init__(self):
        self.CHAT_LINK_TIME = 1
        self.TAIL_LEN = 20

        self.load_containers()
        self.load_role_whitelist()
        self.load_cogs()
        self.client = docker.from_env()

    def get_chat_link_time(self):
        return self.CHAT_LINK_TIME

    def get_tail_len(self):
        return self.TAIL_LEN

    def get_cogs(self):
        return self.COGS + self.GAME_COGS

    def get_game_cogs(self):
        return self.GAME_COGS

    def get_role_whitelist(self):
        return self.role_Whitelist

    def get_containers(self):
        return self.containers
    
    def load_role_whitelist(self):
        with open("../data/role_Whitelist.json", 'r') as read_file:
            self.role_Whitelist = json.load(read_file)
        
    def load_containers(self): 
        with open("../data/containers.json", 'r') as read_file:
            self.containers = json.load(read_file)

    def save_containers(self):
        with open("../data/containers.json", 'w') as write_file:
            json.dump(self.containers, write_file, indent = 2)

    def save_cogs(self):
        with open("../data/settings/cogs.json", 'w') as f:
            dict = {'cogs':self.COGS,'gamecogs':self.GAME_COGS}
            json.dump(dict, f, indent = 2)

    def load_cogs(self):
        with open("../data/settings/cogs.json", 'r') as f:
            dict = json.load(f)
            self.COGS = dict.get('cogs')
            self.GAME_COGS = dict.get('gamecogs')

    def add_container(self, sDict):
        self.containers.append(sDict)
        self.save_containers()

    def remove_container(self, popID):
        self.containers.pop(popID)
        self.save_containers()
    
    def get_server_name(cid):
        '''
        Returns corresponding container name matching cid
        '''
        for container in DB.get_containers():
            if container.get('channel_id') == cid:
                return container.get('name')