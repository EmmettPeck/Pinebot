"""A class used to track player activity and log it for analytics"""

import sys
import json
from datetime import datetime
from dockingPort import DChannels, DockingPort

sys.path.append("../Pinebot")
from username_to_uuid import UsernameToUUID

class Analytics():

    def __init__(self):
        self.playerstats = self.load_playerstats()
        if self.playerstats:
            pass
        else:
            self.create_playerstats()

    def str_to_dt(self, dt_str):
        """Converts string to datetime format"""
        return datetime.strptime(dt_str, '%d/%m/%y %H:%M:%S')
    
    def get_player_uuid(self, username):
        """Get player UUID from username"""
        converter = UsernameToUUID(username)
        uuid = converter.get_uuid()
        return uuid
    
    def get_uuid_index(self, uuid):
        """Returns index of specific UUID in playerstats"""
        for D in self.playerstats: #Looks at each dict
                if uuid == D["UUID"]:  #If dict UUID value matches UUID
                    return self.playerstats.index(D) #Sets index to index of dict
        return None

    def get_server_index(self, serverName):
        """Returns index of specific serverName in playerstats"""
        uuid_index = self.get_uuid_index("")

        for D in self.playerstats[uuid_index]["Servers"]:
            if str(serverName) in D:
                return self.playerstats[uuid_index]["Servers"].index(D)
        return None

    def get_join_list_dt(self, uuid_index, server_index):
        """Breaks joins into dt list"""
        joinList = []
        for join in self.playerstats[uuid_index]["Servers"][server_index]["Joins"]:
                joinList.append(self.str_to_dt(join))
        return joinList

    def get_leave_list_dt(self, uuid_index, server_index):
        """Breaks leaves into dt list"""
        leaveList = []
        for leave in self.playerstats[uuid_index]["Servers"][server_index]["Leaves"]:
                leaveList.append(self.str_to_dt(leave))
        return leaveList    
            
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
        uuid = self.get_player_uuid(username)

        if self.get_uuid_index(uuid):
            print(f"ERROR: add_player {username} already exists.")
        totem_index = self.get_uuid_index("")

        # Create player
        self.playerstats.append({"UUID":uuid,"Servers":[]})

        # Copy servers from empty to new
        server_list = []
        tag_list = []
        for server in self.playerstats[totem_index]["Servers"]:
            server_list.extend(server.keys())
            # Get tags from server
            for tags in server.values():
                current_tags = tags.keys()
                # Filter out tags already present
                for tag in current_tags:
                    if tag not in tag_list:
                        tag_list.append(tag)
        # Add tags to servers
        for dictname in server_list:
            sname = {f'{dictname}':{}}
            self.playerstats[-1]["Servers"].append(sname)
            for tag in tag_list:
                self.playerstats[-1]["Servers"][-1][dictname][tag]=[]
        
        print(f"ADDED: added player {username}")
        self.save_playerstats()

    def add_connect_event(self,username,serverName,online):
        '''Adds Join/Leave event to UUID by ServerName'''
        uuid = self.get_player_uuid(username)
        try:
            Time = datetime.now()
            
            uuid_index = self.get_uuid_index(uuid)

            if uuid_index: 
                server_index = self.get_server_index(serverName)
            
            if online:
                self.playerstats[uuid_index]["Servers"][server_index][str(serverName)]["Joins"].append(str(Time))
            else:
                self.playerstats[uuid_index]["Servers"][server_index][str(serverName)]["Leaves"].append(str(Time))
        except ValueError:
            print(f'ValueError: "{uuid}" not a valid UUID.')
        except UnboundLocalError:
            print(f'UnboundLocalError: "{serverName}" not a valid server.') #Also called when invalid UUID due to fallthrough
        else:
            self.save_playerstats()

    def get_player_list(self, serverName):
        """"Returns a list of players currently online"""

        response = None
        # Match servername to channel ID, then get list 
        for server in DChannels.get_channels():
            if serverName == server['name']:
                response = DockingPort.send(server['id'], "/list")
                print(response) # Test, then filter users out of. 

        if response:
            player_list = []
            # Filter playerlist based off response syntax
            return player_list

        return None

    def is_player_online(self, uuid_index, serverName):
        """Returns true if player is on server"""

        player_list = self.get_player_list(serverName)
        if player_list:
            for player in player_list: 
                if self.get_uuid(player) == self.playerstats[uuid_index]["UUID"]:
                    print (f"is_player_online: {player} is online {serverName}")
                    return True
            return False
        return None
    
    def handle_playtime(self, player, serverName='total'): #Needs renaming and refactoring
        """Calls calculation functions, returns appropriate playtime"""   
        uuid = self.get_player_uuid(player)
        uuid_index = self.get_uuid_index(uuid)

        if uuid_index:
            if serverName.lower() == 'total':
                pinetotal = None
                
                for server in self.playerstats[uuid_index]["Servers"]:
                    playt = self.get_playtime(uuid_index, server.keys())
                    pinetotal += playt
                    self.update_playtime(uuid_index,server.keys(), playt)

                self.save_playerstats()
                return pinetotal
                
            else: # Catch to check if servername matches valid container, otherwise returns none?
                playt = self.get_playtime(uuid_index, serverName)
                self.update_playtime(uuid_index, serverName, playt)

                self.save_playerstats()
                return playt

        return None

    def update_playtime(self, uuid_index, serverName, playt):
        """Updates playtime and last computed of player by server"""
        self.playerstats[uuid_index]["Servers"][serverName]["Total Playtime"] = str(playt)
        self.playerstats[uuid_index]["Servers"][serverName]["Last Computed"] = str(datetime.now())

    def get_playtime(self, uuid_index, serverName):
        """Gets playtime for player and server"""
        server_index = self.get_server_index(serverName)
        if server_index:
            joinList = self.get_join_list_dt(uuid_index, server_index)
            leaveList = self.get_leave_list_dt(uuid_index, server_index)
            return self.calculate_playtime(joinList, leaveList, uuid_index, serverName)
        else:
            return None

    def calculate_playtime(self, leaveList, joinList, uuid_index, serverName):
        """Computes playtimes from list of leave and join dt"""
        total = None
        for index in range(len(joinList)):
            total += (leaveList[index]- joinList[index])

        # If there's 1 more join than leaves
        if len(joinList) == len(leaveList) + 1:
            self.check_false_join(leaveList, joinList, uuid_index, serverName)
            now = datetime.now()
            total += (now - joinList[index])

        # If there are 2 more joins then leaves
        elif len(joinList) > len(leaveList) + 1:
            self.check_false_leave(leaveList, joinList, uuid_index, serverName)

        # If there are more leaves than joins
        elif len(leaveList) > len(joinList):
            self.check_false_leave(leaveList, joinList, uuid_index, serverName)

        return total  

    def check_false_join(self, leaveList, joinList, uuid_index, serverName, online = self.is_player_online(uuid_index, serverName)):
        """Handles a false/missing join message"""

        # Check if most recent is a join and player is offline [Extra Join]
        if joinList[-1] > leaveList[-1] and not online:
            # Remove previous join message
            self.playerstats[uuid_index]["Servers"][serverName]["Joins"].pop()

        # Check if most recent is a leave and player is online [Missing Join]
        elif leaveList[-1] > joinList[-1] and online:
            # Add join at time of discovery
            self.playerstats[uuid_index]["Servers"][serverName]["Joins"].append(str(datetime.now()))
    
    def check_false_leave(self, leaveList, joinList, uuid_index, serverName):
        """Handles a false/missing leave message"""  
        online = self.is_player_online(uuid_index, serverName)
        # If first leave is before first join, removes. [Extra Leave]
        try:
            if leaveList[0] < joinList[0]:
                self.playerstats[uuid_index]["Servers"][serverName]["Leaves"].pop(0)
        except IndexError:
            self.playerstats[uuid_index]["Servers"][serverName]["Leaves"].pop(0)
        
        # If two most recent are leaves and the player is not online [Extra Leave]
        if leaveList[-1] > joinList[-1] and leaveList[-2] > joinList[-1]:
            # Remove most recent leave
            self.playerstats[uuid_index]["Servers"][serverName]["Leaves"].pop()
            if online: 
                # Calls check_false_join, adding join at time discovered
                self.check_false_join(leaveList, joinList, uuid_index, serverName, online)                

        # If two most recent are joins and player is online [Missing Leave] 
        elif joinList[-1] > leaveList[-1] and joinList[-2] > leaveList[-1]:
            if online:
                # Remove second most recent join
                self.playerstats[uuid_index]["Servers"][serverName]["Joins"].pop(-2)

            else:
                # Otherwise remove first, falsejoin 
                self.playerstats[uuid_index]["Servers"][serverName]["Joins"].pop()
                self.check_false_join(leaveList, joinList, uuid_index, serverName, online)
    
     

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