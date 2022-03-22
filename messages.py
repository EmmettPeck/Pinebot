"""Contains message sorting and list information for MC"""
from enum import Enum

death_msg_startw = ["was shot by","was pummeled by","was pricked to death","walked into a cactus whilst trying to escape","drowned","drowned whilst trying to escape","experienced kinetic energy","experienced kinetic energy whilst trying to escape","blew up","was blown up by","was killed by","hit the ground too hard","fell from a high place","fell off a ladder","fell off some vines","fell off some weeping vines","fell off some twisting vines","fell off scaffolding","fell while climbing","was impaled on a stalagmite","was squashed by a falling anvil","was squashed by a falling block","was skewered by a falling stalactite","went up in flames","burned to death","was burnt to a crisp whilst fighting","went off with a bang","tried to swim in lava","was struck by lightning","discovered the floor was lava","walked into danger zone due to","was killed by magic","was killed by","froze to death","was frozen to death by","was slain by","was fireballed by","was stung to death","was shot by a skull from","starved to death","suffocated in a wall","was squished too much","was squashed by","was poked to death by a sweet berry bush","was killed trying to hurt","was impaled by","fell out of the world","didn't want to live in the same world as","withered away","died from dehydration","died","was roasted in dragon breath","was doomed to fall","fell too far and was finished by","was stung to death by","went off with a bang","was killed by even more magic","was too soft for this world"]

class MessageType(Enum):
    MSG = 1
    JOIN = 2
    LEAVE = 3
    DEATH = 4

class Death:
    def __init__(self, msg):
        self.msg = msg.strip()
        self.player = self.msg.split()[0]
        self.stripped_msg = self.msg.split(self.player)[1].strip()

    def is_death(self):
        """Checks if playerless string matches death message"""
        for item in death_msg_startw:
            #print(f"E--- {self.stripped_msg} vs {item}:")
            if self.stripped_msg.startswith(item):
                return True
        return False