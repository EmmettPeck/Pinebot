"""
embedding.py

Embedded text blocks for a variety of discord bot purposes
"""

import discord

from messages import get_type_icon
from datetime import datetime

def embed_server_list(title, input):
    embed = discord.Embed(title = "📄 "+title, color = discord.Color.dark_blue())

    for i in range(len(input)):
        sname, sdesc, sip = input[i].get("name"), input[i].get("desc"), input[i].get("ip")
        
        if (sname is None) or (sdesc is None) or (sip is None): continue
        embed.add_field(name=f"{sname.title()} | ``IP: {sip}``", value=f'{sdesc}\n', inline=False)
    #TODO User requested/time
    return embed

def embed_playtime(total_playtime, dict_list):
    """total playtime and sorted dict_list by playtime --> Sorted Embed"""
    embed = discord.Embed(title="Playtime",description=total_playtime,timestame=datetime.utcnow(),color=discord.Color.dark_purple())

    for dictionary in dict_list:
        server_name = dictionary.get('servername')
        last_con = dictionary.get('last_connected')
        playtime = dictionary.get('playtime')
        first_join = dictionary.get('first_join')

        embed.add_field(name=f"{server_name} | Last Played: {last_con}", value=f"``{playtime}`` since ``{first_join}``", inline=False)
    #TODO User requested/time
    return embed

def embed_build(message):
    #TODO User requested/time
    return discord.Embed(title=f"📄 {message}",color=discord.Color.blurple(),timestamp=datetime.utcnow())

def embed_message(msg_dict):
    return discord.Embed(title=f"{get_type_icon(msg_dict.get('type'))} {msg_dict.get('username')} {msg_dict.get('message')}", color = msg_dict.get("color"))
    