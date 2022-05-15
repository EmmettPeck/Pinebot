"""
embedding.py

Embedded text blocks for a variety of discord bot purposes
"""

import discord

from messages import get_type_icon

def embed_server_list(input):
    #table = ["Title", {"name": "server","desc":"description"}]
    embed = discord.Embed(title = input[0], color = discord.Color.dark_blue())
    for i in range(len(input)-1):
        sname = input[i+1].get("name")
        sdesc = input[i+1].get("desc")
        sip = input[i+1].get("ip")

        if (sname == None) or (sdesc == None) or (sip == None): continue

        embed.add_field(name=f"{sname.title()}\n ``{sip}``", value=f'{sdesc}\n', inline=False)

    return embed
def embed_playtime(input):
    pass
# Playtime Table
    # Total:
        # Highest Playtime Server:
        # 2nd
        # 3rd

def embed_message(msg_dict):
    """Returns a discord embed message object corresponding with a chat-link message"""
    return discord.Embed(title=f"{get_type_icon(msg_dict.get('type'))} {msg_dict.get('username')} {msg_dict.get('message')}",timestame=msg_dict.get("time"), color = msg_dict.get("color"))
    