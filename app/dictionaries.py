"""
A module to hold build functions for any used dictionary structures

This is intended to keep keys well documented, preventing instances where "user"
is looked for rather than "username". Additionally, having in one file simplifys
streamlining keys

Authors: Emmett Peck (EmmettPeck)
Version: July 19th, 2022
"""

from datetime import datetime, timedelta

import discord

from messages import MessageType


def make_link_key(username:str, keyID:str, id:int, expires):
    """
    Returns: a link key dictionary with given structure

    Keys
    ---
    `username`:`str`
        -   Username tied to the key

    `keyID`:`str`
        - Unique key to store 

    `id`:int
        - Discord userid that requested the link

    `expires`:`datetime`
        - Time the key expires

    
    """

    return {'username':username,'keyID':keyID,'expires':expires, 'id':id}

def get_msg_dict(username:str, message:str, type:MessageType, color:discord.Color, time=datetime.now()): #TODO change to offset-aware UTC datetimes (In analytics too)
    """
    Returns a dictionary with given elements

    Keys
    ---
    `username`:`str`
        - Username that sent message

    `message`:`str`
        - The message

    `type`:`messages.MessageType`
        - MessageType associated with the message

    `color`:`discord.Color`
        - The color of the embedded printed message
        
    `time`:`datetime`
        - The time associated with the message
    """
    return {
        "username":username, 
        "message": message.strip(), 
        "type": type, 
        "time": time, 
        'color': color}

def make_statistics(username="", uuid=""):
    """
    Returns an empty statistics dictionary.

    Used by GameCog to store player account information.
    """
    return {
        'username':username,
        'uuid':uuid,
        'total_playtime':timedelta(), 
        'calculated_index':-1, 
        'joins':[], 
        'leaves':[],
        'linked':''}

def make_user_account(id:int):
    """
    Returns an empty user account.

    Used by Accounts cog to store discord user account-links.
    """
    return {
        'id':id,
        'linked':[]
    }

def make_link_account(username:str,uuid:str,game:str,_id):
    """
    Returns a linked account dictionary.

    Used by Accounts cog to store discord user account-links.

    Keys:
    ---
    `username`:`str`
        - Most recent username of linked account.

    `UUID`:`str`
        - UUID of linked account, if present.

    `game`:`str`
        - Name of service that holds the account
    """
    return {
        'username':username,
        'UUID':uuid,
        'game':game,
        'servers_id':_id
    }

def playtime_dict(server_name:str, last_connected, playtime, first_join, game):
    return {
        'servername' : server_name,
        'last_connected': last_connected,
        'playtime' : playtime,
        'first_join' : first_join,
        'game' : game
    }

def build_server(name:str, game:str, version:str, docker:str, cid:list, ip:str, description:str, hidden:bool)->dict:
    return {
        "name":name,                # Server Name
        "game":game,                # Game (Ie: Minecraft)
        "version":version,          # Version (Ie: 1.18, 1.19)
        "docker_name":docker,       # Docker Name
        "cid":cid,                  # Channel ID List
        "ip":ip,                    # IP to display in the server-list
        "description":description,  # Description to display in the server-list
        "hidden":hidden,            # Whether or not to display in the server list
        "active" : True,            # Determines whether or not the server is watched
        "online_players": list(),   # List of online players
        "player_max": -1,           # Max Players (Default -1 for ∞)
        "link_keys": list()         # Codes to check against new msgs
    }