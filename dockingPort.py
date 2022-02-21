#   dockingPort.py
#   by: Emmett Peck
"""A python library that allows interracting with docker minecraft servers on PineServer"""

import json
import subprocess

class DockingPort():

    def __init__(self):
        self.load_mc_Channels()
        self.mc_Channels["IP"][0] = "mc.pineserver.net"     # TEMP
        self.mc_Channels["IP"][1] = "liam.pineserver.net"   # TEMP

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

    # In future migrated to using docker API, SO much better
    def portRead(self, channelID):
        """A python function that checks past 15 messages of a channel, and returns a list of strings of formatted messages to be sent (in order) to caller"""

        resp_str = ""

        # Filter for channel
        for channel in self.mc_Channels:
                if channelID == channel.get('channel_id'):
                    # Follow logs
                    dockerName = channel.get('docker_name')
                    # Uses tail, assuming there won't be more than 10-15 msgs per runtime
                    resp_bytes = subprocess.Popen(f'docker logs {dockerName} --tail 15', stdout=subprocess.PIPE, shell=True, executable="/bin/bash").stdout.read()
                    resp_str = resp_bytes.decode(encoding="utf-8", errors="ignore")
                    break

        # Filter logs
        for line in resp_str.split('\n'): # Verify it even uses \n
            print(line.split('] [Server thread/INFO]:')[1]) # Strips text to being after [Server thread/INFO]:

        # Parse and send information to msger

        # Use a loop

# PortRead test function 
if __name__ == '__main__':
    dockingPort=DockingPort()
    dockingPort.portRead(942193852058574949)
    print("Done")