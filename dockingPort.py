#   dockingPort.py
#   by: Emmett Peck
#   A python function that allows interracting with docker minecraft servers on PineServer
#

import subprocess


# Temp list to be moved to a serialized file later
mc_Channels = [ # Channel List of dictionaries
    {'name':"mc", 'channel_id':942193852058574949, 'docker_name':"build_main_2021_1"},
    {'name':"liam", 'channel_id':942241180421328896, 'docker_name':"build_liam_2022_1"}
]

def portSend(channelID, command): # Sends a command to corresponding server ID. Returns a string output of command response.
    for channel in mc_Channels: # Check all channels in list for channel ID, then execute if found.
            if channelID == channel.get('channel_id'):

                # Command Execution Via Commandline through Docker
                dockerName = channel.get('docker_name')
                resp_bytes = subprocess.Popen(f'docker exec {dockerName} rcon-cli /{command}', stdout=subprocess.PIPE, shell=True, executable="/bin/bash").stdout.read()
                resp_str = resp_bytes.decode(encoding="utf-8", errors="ignore")
                
                # Logging
                print(f"Sent command /{command} to {dockerName}")
                print(f'--- {resp_str}')
                return resp_str
            else:
                # CHANNEL NOT FOUND/WRONG CHANNEL MSG
                return "Channel Not Found. Use command only in 'Minecraft' text channels."
            