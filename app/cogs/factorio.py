"""
factorio.py
A cog for discord.py that incorporates docker chatlink, header updating, and playtime logging.

Authors: Emmett Peck (EmmettPeck)
Version: July 17th, 2022
"""
import discord
from discord.ext import tasks, commands

from cogs.gamecog import GameCog, Identifier
from messages import split_first, MessageType
from dictionaries import get_msg_dict

class Factorio(GameCog):

    def get_identifier(self)-> Identifier:
        return Identifier.NO_UUID_CHANGABLE

    async def filter(self, server:dict, message:str):
        """
        OVERLOAD: Factorio:Latest
        Filters logs by version, adding leaves/joins to connectqueue and messages to message queue
        """
        post = None
        time = split_first(message,'[')[0].strip()
        in_brackets = split_first(split_first(message,'[')[1],']')[0]
        after_brackets = split_first(message,']')[1]
        
        # Message
        if in_brackets == "CHAT":
            type = MessageType.MSG
            name = split_first(after_brackets,':')[0].strip()
            msg = split_first(after_brackets,':')[1]
            post =  get_msg_dict(name, msg, type, discord.Color.dark_gold())
        # Join
        elif in_brackets == "JOIN":
            type = MessageType.JOIN
            msg = 'joined the game.'
            name = after_brackets.strip().split(' ',1)[0] # First Word
            post =  get_msg_dict(name, msg, type, discord.Color.dark_gold())
        # Leave
        elif in_brackets == "LEAVE":
            type = MessageType.LEAVE
            msg = 'left the game.'
            name = after_brackets.strip().split(' ',1)[0]
            post =  get_msg_dict(name, msg, type, discord.Color.dark_gold())

        # If Not Ignore, Messages are sent and accounted for playtime
        if post:
            if post.get('type') == MessageType.JOIN or post.get('type') == MessageType.LEAVE:
                await self.handle_connection(server=server, connection=post)
            await self.handle_message(server=server, message=post)

def setup(bot):
    bot.add_cog(Factorio(bot))