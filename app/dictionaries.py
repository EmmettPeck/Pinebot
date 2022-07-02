"""
A module to hold build functions for any used dictionary structures

This is intended to keep keys well documented, preventing instances where "user"
is looked for rather than "username". Additionally, having in one file simplifys
streamlining keys

Authors: Emmett Peck (EmmettPeck)
Version: July 1st, 2022
"""

import datetime

import discord

from messages import MessageType


def make_link_key(username:str,keyID:str,expires:datetime.datetime):
    """
    Returns: a link key dictionary with given structure

    Keys
    ---
    `username`:`str`
        -   Username tied to the key

    `keyID`:`str`
        - Unique key to store 

    `expires`:`datetime`
        - Time the key expires
    """

    return {'username':username,'keyID':keyID,'expires':expires}

def get_msg_dict(username:str, message:str, type:MessageType, color:discord.Color, time=datetime.now()):
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
        "message": message, 
        "type": type, 
        "time": time, 
        'color': color}

def make_statistics():
    """
    Returns an empty statistics dictionary.

    Used by GameCog to store player account information.
    """
    return {
        'username':'',
        'uuid':'',
        'total_playtime':'', 
        'calculated_index':-1, 
        'joins':[], 
        'leaves':[],
        'linked':''}

def make_useraccount(id:int):
    """
    Returns an empty user account.

    Used by Accounts cog to store discord user account-links.
    """
    return {
        'id':id,
        'linked':[]
    }

def make_linkaccount():
    """
    Returns a linked account dictionary.

    Used by Accounts cog to store discord user account-links.

    Keys:
    ---
    `server`:`str`
        - Name of server of linked account
    `username`:`str`
        - Username of linked account
    `UUID`:`str`
        - UUID of linked account
    """
    pass