"""A class used to track player activity and log it for analytics"""

import sys
import json
from datetime import datetime

sys.path.append("../Pinebot")
from username_to_uuid import UsernameToUUID

class Analytics():

    def __init__(self):
        self.playerstats = self.load_playerstats()
        if self.playerstats:
            pass
        else:
            self.create_playerstats()
    
    def get_player_UUID(self, username):
        """Get player UUID from username"""
        converter = UsernameToUUID(username)
        uuid = converter.get_uuid()
        return uuid

    def load_playerstats(self):
        """Load playerstats from playerstats.json"""
        try:
            with open("data/playerstats.json") as f:
                e = json.load(f)
        except FileNotFoundError:
            return None
        else:
            return e

    def save_playerstats(self):
        """Saves playerstats to playerstats.json"""
        with open("data/playerstats.json", 'w') as f:
            json.dump(self.playerstats, f, indent = 2)
    
    def create_playerstats(self):
        """Creates empty playerstats.json structure""" 
        self.playerstats = [{'UUID':'','Servers':[]}]
        self.save_playerstats()

    def add_server(self, servername):
        """Adds empty server stats to all players"""
        server_list = []
        for item in self.playerstats[-1]["Servers"]:
            server_list.extend(item.keys())

        if servername in server_list:
            print(f"ERROR: add_server {servername} already present.")
            return 

        for player in self.playerstats:
            serv = {f'{servername}':{'Total Playtime':[],'Last Computed':[], 'Joins':[], 'Leaves':[]}}
            player['Servers'].append(serv)
        print(f"ADDED: added server {servername}")
        self.save_playerstats()

    def add_player(self, username):
        """Adds player to json, copying servers from empty"""
        UUID = self.get_player_UUID(username)

        for D in self.playerstats:
            if UUID == D["UUID"]:
                print(f"ERROR: add_player {username} already exists.")
                return
            elif D["UUID"] == "":
                uuid_index = self.playerstats.index(D) #Example player pos

        # Create player
        self.playerstats.append({"UUID":UUID,"Servers":[]})

        # Copy servers from empty to new
        server_list = []
        tag_list = []
        for server in self.playerstats[uuid_index]["Servers"]:
            server_list.extend(server.keys())

            for tags in server.values():
                current_tags = tags.keys()

                for tag in current_tags:
                    if tag not in tag_list:
                        tag_list.append(tag)


        for dictname in server_list:
            sname = {f'{dictname}':{}}
            self.playerstats[-1]["Servers"].append(sname)
            for tag in tag_list:
                self.playerstats[-1]["Servers"][-1][dictname][tag]=[]
        
        print(f"ADDED: added player {username}")
        self.save_playerstats()
            

    def add_connect_event(self,username,serverName,Online):
        '''Adds Join/Leave event to UUID by ServerName'''
        UUID = self.get_player_UUID(username)
        try:
            Time = datetime.now()
            
            for D in self.playerstats: #Looks at each dict
                if UUID == D["UUID"]:  #If dict UUID value matches UUID
                    uuid_index = self.playerstats.index(D) #Sets index to index of dict
                    break

            for D in self.playerstats[uuid_index]["Servers"]:
                #print(D)
                if str(serverName) in D:
                    server_index = self.playerstats[uuid_index]["Servers"].index(D)
                    break
            
            if Online:
                self.playerstats[uuid_index]["Servers"][server_index][str(serverName)]["Joins"].append(str(Time))
            else:
                self.playerstats[uuid_index]["Servers"][server_index][str(serverName)]["Leaves"].append(str(Time))
        except ValueError:
            print(f'ValueError: "{UUID}" not a valid UUID.')
        except UnboundLocalError:
            print(f'UnboundLocalError: "{serverName}" not a valid server.') #Also called when invalid UUID due to fallthrough
        else:
            self.save_playerstats()
        
    def false_join(self, username, time):
        """Handles a false join message"""

        # Check if most recent is a join, and if player is on server, if so, pass

        # If not, remove previous join message
    
    def false_leave(self, username, time):
        """Handles a false leave message"""  

        # If most recent is a leave and second most recent is a leave, remove most recent leave.
        # Check if player is on server, if so, continue

        # Remove most recent leave message
    
    def update_playerstats_playtime(self):
        """Computes and updates playtimes from playerstats"""
        # edits self.playtime

    def get_playtime(self, username):
        """Gets playtime from playerstats"""

        # Returns a playtime value of a certain player
        # Playtime compute
        # Return playtime of player UUID

    # playtime command

# Test function
if __name__ == '__main__':
    anna = Analytics()
    anna.add_player("Bober")
    anna.add_player("Emmettdogg")
    anna.add_player("HolyGamer666")
    anna.add_server("MC")
    anna.add_server("MC2021")
    anna.add_player("Liam1")
    anna.add_connect_event("Bober","MC",True)
    anna.add_connect_event("Bober","MC",False)