#   dockingPort.py
#   by: Emmett Peck
"""A python library that allows interracting with docker minecraft servers on PineServer"""

import json
import subprocess

class DockingPort():

    def __init__(self):
        self.load_mc_Channels()

    # JSON Load
    def load_mc_Channels(self): 
        with open(r"data/mc_Channels.json", 'r') as read_file:
            self.mc_Channels = json.load(read_file)

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

    def portRead():
        """A python function that allows bot reacting to the live reading of docker minecraft logs on PineServer"""