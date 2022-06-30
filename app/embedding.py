"""
Module containing formatting functions for embedded discord messages

Authors: Emmett Peck (EmmettPeck)
Version: May 28th, 2022
"""

import discord

from messages import get_type_icon, split_first, MessageType
from datetime import datetime
from analytics_lib import td_format


def embed_server_list(reference:discord.Member, input:list):
    """
    Returns: A formatted serverlist embed object sorted by cog.

    Parameter reference: Discord member that requested playtime
    """
    version_list = []
    # Build Embed
    embed = discord.Embed(
        title = 'Server List',
        description='Current servers organized by game.\n',
        timestamp=datetime.utcnow(),
        color = discord.Color.dark_gold())

    # Sort input by version
    for i in range(len(input)):
        # List of lists of indexes, each element in the first list is a cog,
        #  the indexes being of the input set.
        cog_type = split_first(input[i].get("version"),':')[0]
        flag = False
        for item in version_list:
            if item.get('name') == cog_type:
                item['children'].append(i)
                flag = True
                break
        if not flag:
            version_list.append({'name':cog_type,'children':[i]})

    # Print sorted by version
    for item in version_list:
        # Add category header
        embed.add_field(
            name=f' \n\u200b{item.get("name")}',
            value='='*len([ele for ele in item.get('name') if ele.isalpha()]),
            inline=False)
        # Add sorted children
        for i in item.get('children'):
            sname = input[i].get("name")
            sdesc = input[i].get("desc")
            sip = input[i].get("ip")
        
            embed.add_field(
                name=f"🌲 {sname.title()}", 
                value=f'IP: ``{sip}`` | {sdesc}\n', 
                inline=False)
    
    embed.set_footer(
        text='Requested by: '+reference.display_name, 
        icon_url= reference.avatar_url );
    return embed


def embed_playtime(
    reference:discord.Member, 
    total_playtime:str, 
    dict_list:list,
    username:str = None):
    """
    Returns: A formatted playtime embed object from playtime and dict_lists
    
    Parameter total_playtime: timedelta total of playtime

    Parameter reference: Discord member that requested playtime

    Parameter username: Username to reference in embed, otherwise defaults to 
    reference.

    Parameter dict_list: dictionaries to use for top playtime entries
    Preconditon: list of dictionaries in the following format
        Example input dict:
        {'servername': ,'last_connected': ,'playtime': ,'first_join':}
    """
    # Username Defaulting
    if username:
        title = f"Playtime {username}"
    else:
        title =f"Playtime {reference.display_name}"

    # Build Embed
    embed = discord.Embed(
        title=f"Playtime {username}",
        description=
            'Total on Pineserver: ``⌛ '+td_format(total_playtime)+'``\n\u200b',
        timestamp=datetime.utcnow(),
        color=discord.Color.dark_purple())

    # Add Top Server Dicts
    for dictionary in dict_list:
        server_name = dictionary.get('servername')
        #last_con = dictionary.get('last_connected')
        playtime = dictionary.get('playtime')
        first_join = dictionary.get('first_join')

        embed.add_field(
            name=f"🌲 {server_name}", 
            value=f"``⌛ {td_format(playtime)}`` since `📆`<t:{int(round(first_join.timestamp()))}:d>", 
            inline=False)

    # Set Requested by
    embed.set_footer(
        text='Requested by: '+reference.display_name, 
        icon_url=reference.avatar_url)
    return embed


def embed_build(message:str, description:str=None, reference:discord.Member=None, icon='📄'):
    """
    Returns: A formatted message by reference
    """
    # Build Embed
    embed = discord.Embed(
        title=f"{icon} {message}",
        color=discord.Color.dark_gold(),
        timestamp=datetime.utcnow())

    # Description
    if description:
        embed.description = description

    # Set User Reference
    if reference:
        embed.set_footer(
            text='Requested by: '+reference.display_name, 
            icon_url= reference.avatar_url)
    return embed

def embed_message(msg_dict:dict, username_fixes:tuple=("",""), fix_type:MessageType=MessageType.MSG):
    """
    Returns an embedded object of given message dictionary.

    Parameters:
    ---
    `msg_dict`:`dict`
        - A dict with keys `username`,`type`,`message`,`color`,`time`

    `fix_type`:`MessageType`
        - The message types to apply username fixes to. Set to `None` for always.
        
    `username_fixes`:`tuple`
        - tuple of desired prefix & suffix for messages. Defaults to `("","")`
    """
    
    mtype = msg_dict.get('type')
    username = msg_dict.get('username')
    message = msg_dict.get('message')
    color = msg_dict.get("color")

    if (mtype == fix_type) or (mtype is None):
        username = username_fixes[0]+username+username_fixes[1]
    
    return discord.Embed(title=f"{get_type_icon(mtype)} {username} {message}",
        color = color)
    