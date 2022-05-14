"""
embedding.py

Embedded text blocks for a variety of discord bot purposes
"""

import discord
from datetime import datetime

from messages import MessageType

# Table
    #  Name | Description | Address
    #  Main | Main MC Serv| mc.pineserver.net
    #  Liam | Liams MC Ser| liam.pineserver.net

# Playtime Table
    # Total:
        # Highest Playtime Server:
        # 2nd
        # 3rd

# Message
def embed_message(msg_dict):
    type_uni = ""

    # Type Unicode -- Switch 
    # TODO Do I need to use numbers in enum? Maybe just these chars instead?
    type = msg_dict.get("type")
    if (type == MessageType.JOIN) or (type == MessageType.LEAVE):
        type_uni = "🚪"
    elif (type == MessageType.MSG):
        type_uni = "💬"
    elif (type == MessageType.DEATH):
        type_uni = "💀"
    elif (type == MessageType.ACHIEVEMENT):
        type_uni = "🏆"
    else:
        type_uni = ""

    # Embed Message & Datetime, then add playername as author
    return discord.Embed(title=f"{type_uni} {msg_dict.get('username')} {msg_dict.get('message')}",timestame=msg_dict.get("time"), color = msg_dict.get("color"))
    #ctx.send(embed=<embed obj>)
    