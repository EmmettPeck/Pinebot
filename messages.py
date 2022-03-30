"""Message filtering and dictionary building from serverlogs for various MC versions"""
from enum import Enum

class MessageType(Enum):
    MSG = 1
    JOIN = 2
    LEAVE = 3
    DEATH = 4

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

    def get_msg_dict(self, time, username, message, MessageType):
        """Appends and prints messages to return_list as dictionaries"""
        print (f" --- Time:{time}, User:{username}, Msg:{message}")
        local_dict = {"time":time, "username":username, "message": message, "type": MessageType}
        return local_dict

    def filter_mc_1_18(self, line):
        """Filters Deaths, Messages, Leaves/Joins from Minecraft 1.18 server log and returns as a dict"""
        
        # Remove newline characters
        line = line.replace('\n', '')
        # Filter for '] [Server thread/INFO]:'
        split_line = line.split('] [Server thread/INFO]:')
        # Separate and save time from messages
        if len(split_line) == 2: 
            time = split_line[0].split('[',1)[1]

            # Message Detection using <{user}> {msg}
            if '<' and '>' in split_line[1]:
                msg  = split_line[1].split('> ', 1)[1]
                user = split_line[1][split_line[1].find('<')+1: split_line[1].find('> ')]
                return self.get_msg_dict(time, user, msg, MessageType.MSG)

            # Join/Leave Detection by searching for "joined the game." and "left the game." -- Find returns -1 if not found
            elif split_line[1].find(" joined the game") >= 0: 
                msg = "joined the game"
                user = split_line[1].split(msg)[0].strip()
                return self.get_msg_dict(time, user, msg, MessageType.JOIN)
            elif split_line[1].find(" left the game") >= 0:
                msg = "left the game"
                user = split_line[1].split(msg)[0].strip()
                return self.get_msg_dict(time, user, msg, MessageType.LEAVE)

            # Death Message Detection
            else:
                dm = Death(split_line[1])
                if dm.is_death():
                    return self.get_msg_dict(time, dm.player, dm.stripped_msg, MessageType.DEATH)
        