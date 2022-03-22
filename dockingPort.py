#   dockingPort.py
#   by: Emmett Peck
"""A python library that allows interracting with docker minecraft servers on PineServer"""

import json
import subprocess
from datetime import datetime
import docker

from fingerprints import FingerPrints
from messages import Death
from messages import MessageType

client = docker.from_env()

class DockingPort():

    def __init__(self):
        self.fp = FingerPrints()
        self.mc_Channels = self.load_mc_Channels()

    def load_mc_Channels(self): 
        with open(r"data/mc_Channels.json", 'r') as read_file:
            return json.load(read_file)

    def save_mc_Channels(self):
        # Overwrites json
        with open(r"data/mc_Channels.json", 'w') as write_file:
            json.dump(self.mc_Channels, write_file, indent = 2)

    def filter_logs_mc_1_18(self, resp_str):
        """Filters string by significant lines to playeractions in Minecraft 1.18"""
        return_list = []
        # Filter line by line for '] [Server thread/INFO]:'
        for line in resp_str.split('\n'):
            # If msg hash isn't unique, kick out. 
            if self.fp.is_unique_fingerprint(self.fp.get_hash_int(line), self.fp.fingerprintDB):
                split_line = line.split('] [Server thread/INFO]:')
                
                # Separate and save time from messages
                if len(split_line) == 2: 
                    time = split_line[0].split('[',1)[1]

                    # Message Detection using <{user}> {msg}
                    if '<' and '>' in split_line[1]:
                        msg  = split_line[1].split('> ', 1)[1]
                        user = split_line[1][split_line[1].find('<')+1: split_line[1].find('> ')] 
                        self.append_msg_dict(time, user, msg, MessageType.MSG, return_list)
                    # Join/Leave Detection by searching for "joined the game." and "left the game." -- Find returns -1 if not found
                    elif split_line[1].find(" joined the game") >= 0: 
                        msg = "joined the game"
                        user = split_line[1].split(msg)[0].strip()
                        self.append_msg_dict(time, user, msg, MessageType.JOIN,return_list)
                    elif split_line[1].find(" left the game") >= 0:
                        msg = "left the game"
                        user = split_line[1].split(msg)[0].strip()
                        self.append_msg_dict(time, user, msg, MessageType.LEAVE,return_list)
                    # Death Message Detection
                    else:
                        dm = Death(split_line[1])
                        if dm.is_death():
                            self.append_msg_dict(time, dm.player, dm.stripped_msg, MessageType.DEATH, return_list)
        # Save DB and return
        self.fp.save_fingerprintDB()
        return return_list


    def append_msg_dict(self, time, username, message, MessageType, return_list):
        """Adds unique messages to return_list as dicts"""
        print (f" --- Time:{time}, User:{username}, Msg:{message}")
        local_dict = {"time":time, "username":username, "message": message, "type": MessageType}
        return_list.append(local_dict)

    def portSend(self, channelID, command, logging=False): 
        """Sends command to corresponding server. Returns a str output of response."""
        for channel in self.mc_Channels: 
                if channelID == channel.get('channel_id'):
                    dockerName = channel.get('docker_name')
                    filtered_command = command.replace("'", "'\\''") # Single-Quote Filtering (Catches issue #9)
                    resp_bytes = subprocess.Popen(f"docker exec {dockerName} rcon-cli '{filtered_command}'", stdout=subprocess.PIPE, shell=True).stdout.read()
                    resp_str = resp_bytes.decode(encoding="utf-8", errors="ignore")
                    
                    if logging:
                        print(f"\nSent command /{command} to {dockerName}")
                        print(f' --- {resp_str}')
                    return resp_str
        return None

    def portRead(self, channelID):
        """Awaits text in streamed dockerlogs, sends parsed message to chat_link"""
        # Filters for channel, then converts tail 10 of the logs to a string
        for channel in self.mc_Channels:
            if channelID == channel.get('channel_id'):
                dockerName = channel.get('docker_name') 
                resp_bytes = subprocess.Popen(f'docker logs {dockerName} --tail 10', stdout=subprocess.PIPE, shell=True).stdout.read()
                resp_str = resp_bytes.decode(encoding="utf-8", errors="ignore")
                break
        return self.filter_logs_mc_1_18(resp_str)                        

# PortRead test function 
if __name__ == '__main__':
    dockingPort=DockingPort()
    print(dockingPort.portRead(942193852058574949))