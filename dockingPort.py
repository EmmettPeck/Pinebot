#   dockingPort.py
#   by: Emmett Peck
"""A python library that allows interracting with docker minecraft servers on PineServer"""

import json
import subprocess
import hashlib
import datetime

class DockingPort():

    def __init__(self):
        self.load_mc_Channels()
        self.load_fingerprintDB()

    # JSON Load
    def load_mc_Channels(self): 
        with open(r"data/mc_Channels.json", 'r') as read_file:
            self.mc_Channels = json.load(read_file)

    def save_mc_Channels(self):
        # Overwrites json
        with open(r"data/mc_Channels.json", 'w') as write_file:
            json.dump(self.mc_Channels,write_file)

    def load_fingerprintDB(self):
        """Loads the previous 100 message hashes"""
        with open(r"data/hashDump.json", 'r') as read_file:
            self.fingerprintDB = json.load(read_file)
    
    def save_fingerprintDB(self):
        """Saves the previous 100 message hashes"""
        with open(r"data/hashDump.json", 'w') as write_file:
            json.dump(self.fingerprintDB, write_file)

    # Command Send -> 
    def portSend(self, channelID, command): # Sends a command to corresponding server ID. Returns a string output of command response.
        for channel in self.mc_Channels: # Check all channels in list for channel ID, then execute if found.
                if channelID == channel.get('channel_id'):

                    # Command Execution Via Commandline through Docker
                    dockerName = channel.get('docker_name')
                    resp_bytes = subprocess.Popen(f'docker exec {dockerName} rcon-cli /{command}', stdout=subprocess.PIPE, shell=True, executable="/bin/bash").stdout.read()
                    resp_str = resp_bytes.decode(encoding="utf-8", errors="ignore")
                    
                    # Logging
                    print(f"Sent command /{command} to {dockerName}")
                    print(f'--- {resp_str}')
                    return resp_str
        # CHANNEL NOT FOUND/WRONG CHANNEL MSG
        return "Channel Not Found. Use command only in 'Minecraft' text channels."
                
    # THE GAMEPLAN
    # Stream logs until a specific point in time
    # docker logs --follow --until=1s Shows last 1 second of logs
    # from the last 1 second of logs, filter, send player chat commands to corresponding channels
    # From messages sent in channel, rcon send non-bot messages to server
    # Constantly checking -> How to efficiently handle? Check every tiny interval using async?
    # ```[<playername>]: <msg>```

    # In future migrated to using docker API, SO much better
    def portRead(self, channelID):
        """A python function that checks past 15 messages of a channel, and returns a list of strings of formatted messages to be sent (in order) to caller"""

        resp_str = ""
        return_list = []

        # Filter for channel
        for channel in self.mc_Channels:
                if channelID == channel.get('channel_id'):
                    # Follow logs
                    dockerName = channel.get('docker_name')
                    # Uses tail, assuming there won't be more than 10-15 msgs per runtime
                    resp_bytes = subprocess.Popen(f'docker logs {dockerName} --tail 15', stdout=subprocess.PIPE, shell=True, executable="/bin/bash").stdout.read()
                    resp_str = resp_bytes.decode(encoding="utf-8", errors="ignore")
                    break

        # Parse and send information to msger using tellraw
        msg_list = []
        for line in resp_str.split('\n'):
            split_line = line.split('] [Server thread/INFO]:')
                
            if len(split_line) == 2: # 1 Corresponds to 1 element, 2 to 2 elements
                # Save Time
                time = split_line[0].split('[',1)[1]

            # Message Detection using <{user}> {msg}
                if '<' and '>' in split_line[1]:
                    user = split_line[1][split_line[1].find('<')+1: split_line[1].find('> ')] 
                    msg  = split_line[1].split('> ', 1)[1]
                    print (f" --- Time:{time}, User:{user}, Msg:{msg}")

                # Fingerprint handling
                    # Create SHA256 Hash to prevent message conflicts
                    sha256hash = hashlib.sha256()
                    sha256hash.update(f"{time}{user}{msg}".encode('utf8'))
                    hash_id = sha256hash.hexdigest()
                    hash_int = int(hash_id,16)
                    print(f" --- {hash_int}")

                    # Compare hash to list, not staging information if present
                    try:
                        comparison = self.fingerprintDB.index(hash_int)
                    except ValueError as v:
                        # Insert into pos 0
                        self.fingerprintDB.insert(0, hash_int)

                        # Pop elements over pos 100
                        if len(self.fingerprintDB) > 100:
                            self.fingerprintDB.pop(100)
                        
                        # Stage list
                        local_dict = {"time":time, "username":user, "message": msg}
                        return_list.insert(0, local_dict)
                        
                    else:
                        continue
        # Save DB and return
        self.save_fingerprintDB()
        return return_list
                            
                    
                        
# PortRead test function 
if __name__ == '__main__':
    dockingPort=DockingPort()
    print(dockingPort.portRead(942193852058574949))