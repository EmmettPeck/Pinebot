"""
Module containing singleton class for data access across multiple discord cogs.

This module handles file loading and saving for settings information for PineBot

Authors: Emmett Peck (EmmettPeck)
Version: July 1st, 2022
"""

import json
import docker
from pymongo import MongoClient

def singleton(cls):
    return cls()

@singleton
class DB:
    """
    A singleton class containing settings, Docker, and MongoDB connection info.
    """
    def __init__(self):
        # Configurations -------------------------------------------------------
        # MongoDB
        uri = "mongodb+srv://pinebot.hzrfoqe.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority"
        self.mongo = MongoClient(uri,
                     tls=True,
                     tlsCertificateKeyFile='testenv/X509-cert-2940582018631408693.pem')
        
        # Docker
        self.client = docker.from_env()

        # Settings -------------------------------------------------------------
        self.CHAT_LINK_TIME = 1
        self.TAIL_LEN = 20

        self.load_role_whitelist()
        self.load_cogs()
        # ----------------------------------------------------------------------

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
    
    def load_role_whitelist(self):
        with open("../data/role_Whitelist.json", 'r') as read_file:
            self.role_Whitelist = json.load(read_file)

    def save_cogs(self):
        with open("../data/settings/cogs.json", 'w') as f:
            dict = {'cogs':self.COGS,'gamecogs':self.GAME_COGS}
            json.dump(dict, f, indent = 2)

    def load_cogs(self):
        with open("../data/settings/cogs.json", 'r') as f:
            dict = json.load(f)
            self.COGS = dict.get('cogs')
            self.GAME_COGS = dict.get('gamecogs')