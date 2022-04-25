"""A class used to track player activity and log it for analytics"""

from ntpath import join
import sys
from datetime import datetime
from discord.ext import tasks, commands

sys.path.append("../Pinebot")
from dockingPort import DockingPort
from database import DB
from username_to_uuid import UsernameToUUID
from messages import MessageType
from datetime import timedelta  

class Analytics(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.connect_event_handler.start()

    def cog_unload(self):
        self.connect_event_handler.cancel()

    def str_to_dt(self, dt_str):
        """Converts string to datetime format"""
        return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S.%f')    
    
    def get_player_uuid(self, username):
        """Get player UUID from username"""
        converter = UsernameToUUID(username)
        uuid = converter.get_uuid()
        return uuid
    
    def get_uuid_index(self, uuid):
        """Returns index of specific UUID in playerstats"""
        for D in DB.playerstats: #Looks at each dict
                if uuid == D["UUID"]:  #If dict UUID value matches UUID
                    return DB.playerstats.index(D) #Sets index to index of dict
        return None

    def get_server_index(self, serverName):
        """Returns index of specific serverName in playerstats"""
        uuid_index = self.get_uuid_index("")

        for D in DB.playerstats[uuid_index]["Servers"]:
            if serverName in D.keys():### ERROR TODO Here? in D doesn't refer to keys? WHY IS IT NONE
                return DB.playerstats[uuid_index]["Servers"].index(D)
        return None

    def get_join_list_dt(self, uuid_index, server_index, serverName):
        """Breaks joins into dt list"""
        joinList = []
        for join in DB.playerstats[uuid_index]["Servers"][server_index][serverName]["Joins"]:
            joinList.append(self.str_to_dt(join))
        return joinList

    def get_leave_list_dt(self, uuid_index, server_index,serverName):
        """Breaks leaves into dt list"""
        leaveList = []
        for leave in DB.playerstats[uuid_index]["Servers"][server_index][serverName]["Leaves"]:
            leaveList.append(self.str_to_dt(leave))
        return leaveList    

    def add_server(self, servername):
        """Adds empty server stats to all players"""
        server_list = []
        for item in DB.playerstats[-1]["Servers"]:
            server_list.extend(item.keys())

        if servername in server_list:
            print(f"ERROR: add_server {servername} already present.")
            return 

        for player in DB.playerstats:
            serv = {f'{servername}':{'Total Playtime':[],'Last Computed':[], 'Joins':[], 'Leaves':[]}}
            player['Servers'].append(serv)
        print(f"ADDED: added server {servername}")
        DB.save_playerstats()

    def add_player(self, username):
        """Adds player to json, copying servers from empty"""
        uuid = self.get_player_uuid(username)

        if self.get_uuid_index(uuid):
            print(f"ERROR: add_player {username} already exists.")
        totem_index = self.get_uuid_index("")

        # Create player
        DB.playerstats.append({"UUID":uuid,"Servers":[]})

        # Copy servers from empty to new
        server_list = []
        tag_list = []
        for server in DB.playerstats[totem_index]["Servers"]:
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
            DB.playerstats[-1]["Servers"].append(sname)
            for tag in tag_list:
                DB.playerstats[-1]["Servers"][-1][dictname][tag]=[]
        
        print(f"ADDED: added player {username}")
        DB.save_playerstats()

    def add_connect_event(self,username,serverName,online):
        '''Adds Join/Leave event to UUID by ServerName'''
        uuid = self.get_player_uuid(username)

        # Check if player is in DB, if not, adds

        try:
            Time = datetime.now()
            
            uuid_index = self.get_uuid_index(uuid)
            if uuid_index == None:
                self.add_player(username)
                uuid_index = self.get_uuid_index(uuid)

            server_index = self.get_server_index(serverName)
            
            if online:
                DB.playerstats[uuid_index]["Servers"][server_index][str(serverName)]["Joins"].append(str(Time))
            else:
                DB.playerstats[uuid_index]["Servers"][server_index][str(serverName)]["Leaves"].append(str(Time))
        except ValueError:
            print(f'ValueError: "{uuid}" not a valid UUID.')
        except UnboundLocalError:
            print(f'UnboundLocalError: "{serverName}" not a valid server.') #Also called when invalid UUID due to fallthrough
        else:
            DB.save_playerstats()

    def get_player_list(self, serverName):
        """"Returns a list of players currently online"""

        response = None
        # Match servername to channel ID, then get list 
        for server in DB.get_containers():
            if serverName == server['name']:
                response = DockingPort().send(server['channel_id'], "/list")



        if response:
            player_list = []

            # Strip Online:
            stripped = response.split("online:")
            for player in stripped[1].split(','):
                player_list.append(player.strip())

            # None detection
            if player_list == ['']:
                return None

            return player_list
        return None

    def is_player_online(self, uuid_index, serverName):
        """Returns true if player is on server"""

        player_list = self.get_player_list(serverName)
        if player_list:
            for player in player_list:
                if self.get_player_uuid(player) == DB.playerstats[uuid_index]["UUID"]:
                    print (f"is_player_online: {player} is online {serverName}")
                    return True
            return False
        return None

    # Connect Event Queue -------------------------------------------------------------------------------
    @tasks.loop(seconds=3)
    async def connect_event_handler(self):
        q = DB.get_connect_queue()
        while not q.qsize() == 0:
            x = q.get()
            if x['type'] == MessageType.JOIN:
                online = True
            else:
                online = False
            self.add_connect_event(x['username'], x['server'], online)
    @connect_event_handler.before_loop
    async def before_connect_event_handler(self):
        await self.bot.wait_until_ready() 

    # Playtime ------------------------------------------------------------------------------------------
    def handle_playtime(self, uuid, serverName='total'): #Needs renaming and refactoring
        """Calls calculation functions, returns appropriate playtime"""   
        uuid_index = self.get_uuid_index(uuid)

        if uuid_index:
            if serverName.lower() == 'total':
                pinetotal = timedelta()
                
                for server in DB.playerstats[uuid_index]["Servers"]:
                    playt = self.get_playtime(uuid_index, list(server.keys())[0])
                    pinetotal += playt
                    self.update_playtime(uuid_index, list(server.keys())[0], playt)

                DB.save_playerstats()
                return pinetotal
                
            else: # Catch to check if servername matches valid container, otherwise returns none?
                playt = self.get_playtime(uuid_index, serverName)
                self.update_playtime(uuid_index, serverName, playt)

                DB.save_playerstats()
                return playt

        return None

    def update_playtime(self, uuid_index, serverName, pt):
        """Updates playtime and last computed of player by server"""
        serverIndex = self.get_server_index(serverName)
        DB.playerstats[uuid_index]["Servers"][serverIndex][serverName]["Total Playtime"] = str(pt)
        DB.playerstats[uuid_index]["Servers"][serverIndex][serverName]["Last Computed"] = str(datetime.now())

    def get_playtime(self, uuid_index, serverName):
        """Gets playtime for player and server"""
        server_index = self.get_server_index(serverName)

        if server_index != None:
            joinList = self.get_join_list_dt(uuid_index, server_index, serverName)
            leaveList = self.get_leave_list_dt(uuid_index, server_index, serverName)
            return self.calculate_playtime(joinList, leaveList, uuid_index, serverName, server_index)
        else:
            return None

    def calculate_playtime(self, leaveList, joinList, uuid_index, serverName, server_index):
        """Computes playtimes from list of leave and join dt"""
        total = timedelta()

        # Check if first leave if before first join
        try:
            if leaveList[0] < joinList[0]:
                self.check_false_join(leaveList, joinList, uuid_index, serverName, server_index)
        except IndexError:
            pass

        # If there are 2 or more joins then leaves
        if len(joinList) > len(leaveList) + 1:
            self.check_false_leave(leaveList, joinList, uuid_index, serverName, server_index)

        # If there are more leaves than joins
        if len(leaveList) > len(joinList):
            self.check_false_leave(leaveList, joinList, uuid_index, serverName, server_index)

        # Calculate
        for index in range(len(joinList)):
            total += (leaveList[index] - joinList[index])

        # If there's 1 more join than leaves
        if len(joinList) == len(leaveList) + 1:
            self.check_false_join(leaveList, joinList, uuid_index, serverName, server_index)
            now = datetime.now()
            total += (now - joinList[index])

        return total  

    def check_false_join(self, leaveList, joinList, uuid_index, serverName, server_index, online=None):
        """Handles a false/missing join message"""

        if online == None:
            online = self.is_player_online(uuid_index, serverName)

        # If first leave is before first join, removes. [Missing Join]
        try:
            if leaveList[0] < joinList[0]:
                DB.playerstats[uuid_index]["Servers"][server_index][serverName]["Leaves"].pop(0)
        except IndexError:
            try: 
                if leaveList[0]:
                    DB.playerstats[uuid_index]["Servers"][server_index][serverName]["Leaves"].pop(0)
            except IndexError:
                pass
        try:
            # Check if most recent is a join and player is offline [Extra Join]
            if joinList[-1] > leaveList[-1] and not online:
                # Remove previous join message
                DB.playerstats[uuid_index]["Servers"][server_index][serverName]["Joins"].pop()

            # Check if most recent is a leave and player is online [Missing Join]
            elif leaveList[-1] > joinList[-1] and online:
                # Add join at time of discovery
                DB.playerstats[uuid_index]["Servers"][server_index][serverName]["Joins"].append(str(datetime.now()))
        except IndexError:
            pass
    
    def check_false_leave(self, leaveList, joinList, uuid_index, serverName, server_index, online=None):
        """Handles a false/missing leave message""" 
        if online == None: 
            online = self.is_player_online(uuid_index, serverName)
        
        try:
            # If two most recent are leaves and the player is not online [Extra Leave]
            if leaveList[-1] > joinList[-1] and leaveList[-2] > joinList[-1]:
                # Remove most recent leave
                DB.playerstats[uuid_index]["Servers"][server_index][serverName]["Leaves"].pop()
                if online: 
                    # Calls check_false_join, adding join at time discovered
                    self.check_false_join(leaveList, joinList, uuid_index, serverName, online)                

            # If two most recent are joins and player is online [Missing Leave] 
            elif joinList[-1] > leaveList[-1] and joinList[-2] > leaveList[-1]:
                if online:
                    # Remove second most recent join
                    DB.playerstats[uuid_index]["Servers"][server_index][serverName]["Joins"].pop(-2)

                else:
                    # Otherwise remove first, falsejoin 
                    DB.playerstats[uuid_index]["Servers"][server_index][serverName]["Joins"].pop()
                    self.check_false_join(leaveList, joinList, uuid_index, serverName, online)
        except IndexError:
            pass
    # Commands -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    @commands.command(name='playtime',help='Returns playtime on pineservers. >playtime <account-name> <server-name>, otherwise returns total of player.',brief='Returns total playtime on pineservers')
    async def playtime(self, ctx, name=None, server=None):
        uuid = self.get_player_uuid(name)
        uuid_index = self.get_uuid_index(uuid)

        # Name Catch
        if name == None:
            await ctx.send("Please provide a playername, >playertime <name> <optional-server>")
            return

        # Catch wrong names
        if uuid_index == None:
            await ctx.send("Player name not recognized. Either misspelled or hasn't played on Pineserver.")
            return

        # Total
        if server == None:
            total = self.handle_playtime(uuid)
            await ctx.send(f"{name} has played {total} across all servers.")
            return

        # Specific Server Playtime
        else: 
            val = self.handle_playtime(uuid, server)
            if val:
                await ctx.send(f"{name} has played {val} on {server}")
                return
            else:
                await ctx.send(f"Server not found.")
    
def setup(bot):
    bot.add_cog(Analytics(bot))