#   dockingPort.py
#   by: Emmett Peck
"""A python library that allows interracting with docker minecraft servers on PineServer"""

import json
import subprocess
import hashlib
import datetime
from enum import Enum
class MessageType(Enum):
    MSG = 1
    JOIN = 2
    LEAVE = 3
    DEATH = 4

class DockingPort():

    def __init__(self):
        self.mc_Channels = self.load_mc_Channels()
        self.fingerprintDB = self.load_fingerprintDB()

    # Data Load/Saving
    # --------------------------------------------------------------
    def load_mc_Channels(self): 
        with open(r"data/mc_Channels.json", 'r') as read_file:
            return json.load(read_file)

    def save_mc_Channels(self):
        # Overwrites json
        with open(r"data/mc_Channels.json", 'w') as write_file:
            json.dump(self.mc_Channels,write_file)

    def load_fingerprintDB(self):
        """Loads the previous 100 message hashes"""
        with open(r"data/hashDump.json", 'r') as read_file:
            return json.load(read_file)
    
    def save_fingerprintDB(self):
        """Saves the previous 100 message hashes"""
        with open(r"data/hashDump.json", 'w') as write_file:
            json.dump(self.fingerprintDB, write_file)
    

    # Functions
    # --------------------------------------------------------------
    def hash_int(self, instr):
        """ Print fancy message; Generate hash """
        sha256hash = hashlib.sha256()
        sha256hash.update(instr.encode('utf8'))
        hash_id = sha256hash.hexdigest()
        hash_ = int(hash_id,16)
        return hash_

    def unique_fingerprint(self, fingerprint):
        """Compares hash to database, if unique returns true"""
        
        try:
            comparison = self.fingerprintDB.index(fingerprint)
        except ValueError as v:
            self.fingerprintDB.insert(0, fingerprint)
            # Pop elements over pos 100 to keep the list tidy
            if len(self.fingerprintDB) > 100: 
                self.fingerprintDB.pop(100)
            return True
        else:
            return False

    def message_handler(self, time, username, message, MessageType, return_list):
        """Returns list of new message dicts"""
        
        hash_ = self.hash_int(f"{time}{username}{message}")
        # Adds 
        if self.unique_fingerprint(hash_):
            print (f" --- Time:{time}, User:{username}, Msg:{message}")
            local_dict = {"time":time, "username":username, "message": message, "type": MessageType}
            return_list.append(local_dict)


    def portSend(self, channelID, command, logging): 
        """Sends command to corresponding server. Returns a str output of response."""
        # Check all channels in list for channel ID, then execute through commandline if found. Otherwise returns error message
        for channel in self.mc_Channels: 
                if channelID == channel.get('channel_id'):
                    
                    filtered_command = command.replace("'", "'\\''") # Single-Quote Filtering (Catches issue #9)

                    dockerName = channel.get('docker_name')
                    resp_bytes = subprocess.Popen(f"docker exec {dockerName} rcon-cli '{filtered_command}'", stdout=subprocess.PIPE, shell=True).stdout.read()
                    resp_str = resp_bytes.decode(encoding="utf-8", errors="ignore")
                    
                    if logging:
                        print(f"\nSent command /{command} to {dockerName}")
                        print(f' --- {resp_str}')
                    return resp_str
        return "Channel Not Found. Use command only in 'Minecraft' text channels."


    def portRead(self, channelID): # Eventually migrate to docker API?
        """Checks past 10 messages of a channel, returns a list of dicts of messages to be sent (in order) to caller channel"""

        resp_str = ""
        return_list = []

        # Filters for channel, then converts tail 10 of the logs to a string
        for channel in self.mc_Channels:
            if channelID == channel.get('channel_id'):
                dockerName = channel.get('docker_name') 
                resp_bytes = subprocess.Popen(f'docker logs {dockerName} --tail 10', stdout=subprocess.PIPE, shell=True).stdout.read()
                resp_str = resp_bytes.decode(encoding="utf-8", errors="ignore")
                break

        # Seperate lines and filter for '] [Server thread/INFO]:'
        for line in resp_str.split('\n'):
            split_line = line.split('] [Server thread/INFO]:')
            
            if len(split_line) == 2: # Separate and save time from messages; 1 to 1 element, 2 to 2 elements
                time = split_line[0].split('[',1)[1] 

                # Message Detection using <{user}> {msg}
                if '<' and '>' in split_line[1]:
                    msg  = split_line[1].split('> ', 1)[1]
                    user = split_line[1][split_line[1].find('<')+1: split_line[1].find('> ')] 
                    self.message_handler(time, user, msg, MessageType.MSG, return_list)

                # Join/Leave Detection by searching for "joined the game." and "left the game." -- Find returns -1 if not found
                elif split_line[1].find(" joined the game") >= 0: 
                    msg = "joined the game"
                    user = split_line[1].split(msg)[0].strip()
                    self.message_handler(time, user, msg, MessageType.JOIN,return_list)

                elif split_line[1].find(" left the game") >= 0:
                    msg = "left the game"
                    user = split_line[1].split(msg)[0].strip()
                    self.message_handler(time, user, msg, MessageType.LEAVE,return_list)

                # Death Message Detection

        # Save DB and return
        self.save_fingerprintDB()
        return return_list
                            
                    
# PortRead test function 
if __name__ == '__main__':
    dockingPort=DockingPort()
    print(dockingPort.portRead(942193852058574949))