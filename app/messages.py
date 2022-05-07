"""
messages.py
By: Emmett Peck
Message filtering and dictionary building from serverlogs for various MC versions/games
"""
from enum import Enum
from posixpath import split
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

class Death:
    """Filters death messages using startswith and possible MC death messages"""

    def __init__(self, msg):
        self.msg = msg.strip()
        self.player = self.msg.split()[0]
        self.stripped_msg = self.msg.split(self.player)[1].strip()
        self.death_msg_startw = ["was shot by","was pummeled by","was pricked to death","walked into a cactus whilst trying to escape","drowned","drowned whilst trying to escape","experienced kinetic energy","experienced kinetic energy whilst trying to escape","blew up","was blown up by","was killed by","hit the ground too hard","fell from a high place","fell off a ladder","fell off some vines","fell off some weeping vines","fell off some twisting vines","fell off scaffolding","fell while climbing","was impaled on a stalagmite","was squashed by a falling anvil","was squashed by a falling block","was skewered by a falling stalactite","went up in flames","burned to death","was burnt to a crisp whilst fighting","went off with a bang","tried to swim in lava","was struck by lightning","discovered the floor was lava","walked into danger zone due to","was killed by magic","was killed by","froze to death","was frozen to death by","was slain by","was fireballed by","was stung to death","was shot by a skull from","starved to death","suffocated in a wall","was squished too much","was squashed by","was poked to death by a sweet berry bush","was killed trying to hurt","was impaled by","fell out of the world","didn't want to live in the same world as","withered away","died from dehydration","died","was roasted in dragon breath","was doomed to fall","fell too far and was finished by","was stung to death by","went off with a bang","was killed by even more magic","was too soft for this world"]


    def is_death(self):
        """Checks if playerless string matches death message"""
        for item in self.death_msg_startw:
            #print(f"E--- {self.stripped_msg} vs {item}:")
            if self.stripped_msg.startswith(item):
                return True
        return False

class MessageFilter:
    """Filters server logs into organized dictionaries"""
    def __init__(self,i=None):
        self.i = i

    def get_msg_dict(self, time, username, message, MessageType):
        """Appends and prints messages to return_list as dictionaries"""
        local_dict = {"time":time, "username":username, "message": message, "type": MessageType}
        print (f" --- Time:{time}, User:{username}, Msg:{message}, Type:{MessageType}")
        return local_dict

    # Format ------------------------------------------------------------------------------------------------
    def format_message(self, item):
        """Message Type Sort and Formatting """
        #try:
        user = item.get("username")
        msg = item.get("message")
        #except AttributeError:
            #return None
        #else:
        if   item.get("type") == MessageType.MSG:
            out_str = f"```yaml\n💬 <{user}> {msg}\n```"
        elif item.get("type") == MessageType.JOIN or item.get("type") == MessageType.LEAVE:
            out_str = f"```fix\n🚪 {user} {msg}\n```"
        elif item.get("type") == MessageType.DEATH:
            out_str = f"```💀 {user} {msg}```"
        elif item.get("type") == MessageType.ACHIEVEMENT:
            out_str = f"```🏆 {user} {msg}```"
        else:
            out_str = ""
            print("ERROR: out_str fallthrough")
        return out_str

    # Filter Version Handler --------------------------------------------------------------------------
    def filter(self, in_str, version):
        """Filters log by container version"""

        # Switch between versions
        if version == "mc":
            return self.filter_mc(in_str)
        elif version == "factorio":
            return self.filter_factorio(in_str)
    
    # Filters ------------------------------------------------------------------------------------------------
    def filter_mc(self, in_str):
        """Filters Deaths, Messages, Leaves/Joins from Minecraft 1.18 server log and returns as a dict"""

        # Fingerprint Filtering
        if DB.fingerprint[self.i].is_unique_fingerprint(in_str):

            # Ensure '[Server thread/INFO]:'
            info_split = in_str.split('] [Server thread/INFO]',1)
            if len(info_split) != 2:
                return

            # Separate time; break apart entry from info
            entry = split_first(info_split[1],':')[1].strip()
            time = split_first(info_split[0], '[')[1]

            # Message Detection using <{user}> {msg}
            if (entry[0] == '<') and ('<' and '>' in entry):
                msg  = split_first(entry,'> ')[1]
                user = get_between(entry, '<','>')
                return self.get_msg_dict(time, user, msg, MessageType.MSG)

            # Join/Leave Detection by searching for "joined the game." and "left the game." -- Find returns -1 if not found
            elif entry.find(" joined the game") >= 0: 
                msg = "joined the game"
                user = entry.split(' ',1)[0]
                return self.get_msg_dict(time, user, msg, MessageType.JOIN)
            elif entry.find(" left the game") >= 0:
                msg = "left the game"
                user = entry.split(' ',1)[0]
                return self.get_msg_dict(time, user, msg, MessageType.LEAVE)

            # Achievement Detection
            elif entry.find("has made the advancement") >= 0:
                user = entry.split(' ',1)[0]
                msg = f" has made the advancement [{split_first(entry,'[')[1]}"
                return self.get_msg_dict(time, user, msg, MessageType.ACHIEVEMENT)

            # Death Message Detection
            else:
                dm = Death(entry)
                if dm.is_death():
                    return self.get_msg_dict(time, dm.player, dm.stripped_msg, MessageType.DEATH)

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
                return self.get_msg_dict(time, name, msg, type)
            # Join
            elif in_brackets == "JOIN":
                type = MessageType.JOIN
                msg = 'joined the game.'
                name = after_brackets.strip().split(' ',1)[0] # First Word
                return self.get_msg_dict(time, name, msg, type)
            # Leave
            elif in_brackets == "LEAVE":
                type = MessageType.LEAVE
                msg = 'left the game.'
                name = after_brackets.strip().split(' ',1)[0]
                return self.get_msg_dict(time, name, msg, type)
