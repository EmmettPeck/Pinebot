"""
dockingPort.py
By: Emmett Peck
Handles interraction with docker game servers
"""

import subprocess

import docker

from messages import MessageFilter, MessageType
from database import DB

class DockingPort:
    """Handles docker interaction on hostsystem"""

    def send(self, channelID, command, logging=False): 
        """Sends command to corresponding server. Returns a str output of response."""
        channels = DB.get_containers()
        for channel in channels: 
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

    def read(self, channelID):
        """Reads logs and updates queue"""
        resp_str = ""
        return_list = []
        cont = DB.get_containers()

        # Filters for channel, then converts tail 10 of the logs to a string
        i = 0
        for channel in cont:
            if channelID == channel.get('channel_id'):
                dockerName = channel.get('docker_name') 
                version = channel.get("version")
                resp_bytes = subprocess.Popen(f'docker logs {dockerName} --tail 10', stdout=subprocess.PIPE, shell=True).stdout.read()
                resp_str = resp_bytes.decode(encoding="utf-8", errors="ignore")
                # Break apart by newline    
                resp_str_l = resp_str.strip().split('\n')        
                for msg in resp_str_l:
                    post = MessageFilter(i).filter(msg, version)
                    if post:
                        # Analytics
                        if post.get('type') == MessageType.JOIN or post.get('type') == MessageType.LEAVE:
                            DB.add_connect_event(post, channel['name'])
                        DB.get_msg_queue(i).put(post)
                i+=1
                break
            i+=1