#   dockingPort.py
#   by: Emmett Peck
"""A python library that allows interracting with docker minecraft servers on PineServer"""

import json
import subprocess
import hashlib
import datetime

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
    def message_handler(self, time, username, message, return_list):
        """Returns list of dictionaries if fingerprint not present in database"""
        
        # Print fancy message; Generate hash
        sha256hash = hashlib.sha256()
        sha256hash.update(f"{time}{username}{message}".encode('utf8'))
        hash_id = sha256hash.hexdigest()
        hash_int = int(hash_id,16)

        # Compares Hash to database, if present does not insert dict into return_list
        try:
            comparison = self.fingerprintDB.index(hash_int)
        except ValueError as v:
            print (f" --- Time:{time}, User:{username}, Msg:{message}")
            self.fingerprintDB.insert(0, hash_int) # Insert into pos 0

            if len(self.fingerprintDB) > 100: # Pop elements over pos 100
                self.fingerprintDB.pop(100)

            # dict insertion to list
            local_dict = {"time":time, "username":username, "message": message}
            return_list.insert(0, local_dict)
        return return_list

    # Command Send -> 
    def portSend(self, channelID, command): # Sends a command to corresponding server ID. Returns a string output of command response.
        for channel in self.mc_Channels: # Check all channels in list for channel ID, then execute if found.
                if channelID == channel.get('channel_id'):

                    # Command Execution Via Commandline through Docker
                    dockerName = channel.get('docker_name')
                    resp_bytes = subprocess.Popen(f"docker exec {dockerName} rcon-cli '{command}'", stdout=subprocess.PIPE, shell=True).stdout.read()
                    resp_str = resp_bytes.decode(encoding="utf-8", errors="ignore")
                    
                    # Logging
                    print(f"Sent command /{command} to {dockerName}")
                    print(f'--- {resp_str}')
                    return resp_str
        # CHANNEL NOT FOUND/WRONG CHANNEL MSG
        return "Channel Not Found. Use command only in 'Minecraft' text channels."

    # In future migrated to using docker API, SO much better
    def portRead(self, channelID):
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
            
            if len(split_line) == 2: # Separate time from messages of interest; 1 Corresponds to 1 element, 2 to 2 elements
                time = split_line[0].split('[',1)[1] # Save Time

                # Message Detection using <{user}> {msg}
                if '<' and '>' in split_line[1]:
                    msg  = split_line[1].split('> ', 1)[1]
                    user = split_line[1][split_line[1].find('<')+1: split_line[1].find('> ')] 
                    self.message_handler(time, user, msg, return_list)

                # Join/Leave Detection by searching for "joined the game." and "left the game." -- Find returns -1 if not found
                elif split_line[1].find(" joined the game") >= 0: 
                    msg = "joined the game"
                    user = split_line[1].split(msg)[0].strip()
                    self.message_handler(time, user, msg, return_list)

                elif split_line[1].find(" left the game") >= 0:
                    msg = "left the game"
                    user = split_line[1].split(msg)[0].strip()
                    self.message_handler(time, user, msg, return_list)

        # Save DB and return
        self.save_fingerprintDB()
        return return_list
                            
                    
                        
# PortRead test function 
if __name__ == '__main__':
    dockingPort=DockingPort()
    print(dockingPort.portRead(942193852058574949))