"""
messages.py
By: Emmett Peck
Message filtering and dictionary building from serverlogs for various MC versions/games
"""
from enum import Enum

def split_first(split_str, character) -> tuple:
    """Splits by first instance of character. split_first('Hi[Emmett]','[') --> ['Hi','Emmett]']"""
    index = split_str.find(character)
    before, after = "",""
    for i in range(len(split_str)):
        if i < index:
            before += split_str[i]
        if i > index:
            after += split_str[i]

    return before, after

def get_between(in_str, beginning_char, end_char) -> str:
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
        type_uni = "⚙️"
    elif (type == MessageType.MSG):
        type_uni = "💬"
    elif (type == MessageType.DEATH):
        type_uni = "💀"
    elif (type == MessageType.ACHIEVEMENT):
        type_uni = "🏆"
    else:
        type_uni = ""
    return type_uni