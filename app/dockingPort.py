"""
dockingPort.py
By: Emmett Peck
Handles interraction with docker game servers
"""

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

                # Attach Container
                container = DB.client.containers.get(dockerName)

                # Send Command, and decipher tuple
                filtered_command = command.replace("'", "'\\''") # Single-Quote Filtering (Catches issue #9)
                resp_bytes = container.exec_run(f"rcon-cli '{filtered_command}'")
                resp_str = resp_bytes[1].decode(encoding="utf-8", errors="ignore")
                
                if logging:
                    print(f"\nSent command /{command} to {dockerName}")
                    print(f' --- {resp_str}')
                return resp_str
        return None

    def read(self, channelID, ignore = False):
        """Reads logs and updates queue if ignore=False"""
        resp_str = ""
        i = 0

        # Filters for channel, then converts tail 10 of the logs to a string
        for channel in DB.get_containers():
            if channelID == channel.get('channel_id'):
                dockerName = channel.get('docker_name') 
                version = channel.get("version")
            # Attach Container & tail logs
                container = DB.client.containers.get(dockerName)
                resp_bytes = container.logs(tail=10)
            # Decode
                resp_str = resp_bytes.decode(encoding="utf-8", errors="ignore")
            # Break apart by newline          
                for msg in resp_str.strip().split('\n'):
                    post = MessageFilter(i).filter(msg, version)
                    # If Ignore, doesn't print messages to analytics or msg queue
                    if post and (not ignore):
                        # Analytics
                        if post.get('type') == MessageType.JOIN or post.get('type') == MessageType.LEAVE:
                            DB.add_connect_event(post, channel['name'])
                        # Message
                        DB.get_msg_queue(i).put(post)
                i+=1
                break
            i+=1