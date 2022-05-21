"""
messages.py
By: Emmett Peck
Message filtering and dictionary building from serverlogs for various MC versions/games
"""
import discord
from enum import Enum
from datetime import datetime
from database import DB

def split_first(split_str, character):
    """Splits by first instance of character. split_first('Hi[Emmett]','[') --> ['Hi','Emmett]']"""
    index = split_str.find(character)
    before, after = "",""
    for i in range(len(split_str)):
        if i < index:
            before += split_str[i]
        if i > index:
            after += split_str[i]

    return [before, after]

def get_between(in_str, beginning_char, end_char):
    '''Gets text between first instance of beginning_char and first instance of end_char'''
    string = ""
    middle = split_first(in_str,beginning_char)[1]
    for i in range(len(middle)):
        if middle[i] == end_char:
            return string
        else:
            string += middle[i]
    return None

class MessageType(Enum):
    MSG = 1
    JOIN = 2
    LEAVE = 3
    DEATH = 4
    ACHIEVEMENT = 5

def get_type_icon(type):
    """Returns corresponding icon to msgtype enumerable"""
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
    return type_uni

def get_msg_dict(username, message, MessageType, color):
        """Appends and prints messages to return_list as dictionaries"""
        local_dict = {"username":username, "message": message, "type": MessageType, "time": datetime.utcnow(), 'color': color}
        print (f" --- Time:{local_dict['time']}, User:{username}, Msg:{message}, Type:{MessageType}")
        return local_dict   

def filter_factorio(self, in_str):
    if DB.fingerprint[self.i].is_unique_fingerprint(in_str):

        time = split_first(in_str,'[')[0].strip()
        in_brackets = split_first(split_first(in_str,'[')[1],']')[0]
        after_brackets = split_first(in_str,']')[1]
        
        # Message
        if in_brackets == "CHAT":
            type = MessageType.MSG
            name = split_first(after_brackets,':')[0].strip()
            msg = split_first(after_brackets,':')[1]
            return self.get_msg_dict(f'<{name}>', msg, type, discord.Color.dark_gold())
        # Join
        elif in_brackets == "JOIN":
            type = MessageType.JOIN
            msg = 'joined the game.'
            name = after_brackets.strip().split(' ',1)[0] # First Word
            return self.get_msg_dict(name, msg, type, discord.Color.dark_gold())
        # Leave
        elif in_brackets == "LEAVE":
            type = MessageType.LEAVE
            msg = 'left the game.'
            name = after_brackets.strip().split(' ',1)[0]
            return self.get_msg_dict(name, msg, type, discord.Color.dark_gold())
