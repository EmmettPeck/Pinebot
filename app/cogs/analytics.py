"""A class used to track player activity and log it for analytics"""

from ast import Index
from ntpath import join
import sys
from datetime import datetime
from discord.ext import tasks, commands

sys.path.append("../app")
import dockingPort
from database import DB
from username_to_uuid import UsernameToUUID
from messages import MessageType
from datetime import timedelta  

# =====================================================================================================================================================================
class Analytics(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.connect_event_handler.start()

    def cog_unload(self):
        self.connect_event_handler.cancel()
    
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

        # Analytics names MUST match case sensitive Container Names (titletext)
        for D in DB.playerstats[uuid_index]["Servers"]:
            if serverName in D.keys():
                return DB.playerstats[uuid_index]["Servers"].index(D)
        return None

    # DateTime Stuff ------------------------------------------------------------------------------------------------

    def str_to_dt(self, dt_str):
        """Converts string to datetime format"""
        return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S.%f')    

    def td_format(self, td_object):
        seconds = int(td_object.total_seconds())
        periods = [
            ('year',        60*60*24*365),
            ('month',       60*60*24*30),
            ('day',         60*60*24),
            ('hour',        60*60),
            ('minute',      60),
            ('second',      1)
        ]

        strings=[]
        for period_name, period_seconds in periods:
            if seconds > period_seconds:
                period_value , seconds = divmod(seconds, period_seconds)
                has_s = 's' if period_value > 1 else ''
                strings.append("%s %s%s" % (period_value, period_name, has_s))

        return ", ".join(strings)

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
    # ------------------------------------------------------------------------------------------------------------------------------------------------

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

    def get_player_list(self, serverName):
        """"Returns a list of players currently online"""
        response = None
        player_list = []

        # Match servername to channel ID, then get list 
        for server in DB.get_containers():
            if serverName == server['name']:
                if server['version'] == 'mc':
                    response = dockingPort.DockingPort().send(server['channel_id'], "/list")
                    break
        # Catch 1
        if not response:
            return None
        # Filter Playernames from logs
        stripped = response.split("online:")
        try:
            for player in stripped[1].split(','):
                player_list.append(player.strip())
            # Catch 3
            if player_list == ['']:
                return None
        # Catch 2
        except IndexError:
            return None
        else:
            return player_list
        
    def is_player_online(self, uuid_index, serverName):
        """Returns true if player is on server"""
        player_list = self.get_player_list(serverName)
        # Catch 1
        if not player_list:
            return None
        # Itterate list, looking for certain player
        for player in player_list:
            if self.get_player_uuid(player) == DB.playerstats[uuid_index]["UUID"]:
                return True
        return False
    
    # Connect Event -----------------------------------------------------------------------------------------------------------------------------------------------
    def is_recentest_join(self, uuid_index, serverIndex, serverName):
        "Returns true if Join is most recent connect event"
        joinList = self.get_join_list_dt(uuid_index, serverIndex, serverName)
        leaveList = self.get_leave_list_dt(uuid_index, serverIndex, serverName)
        try:
            if(len(leaveList) > 0):
                if(joinList[-1] > leaveList[-1]):
                    return True
                else:
                    return False
            else:
                return True
        except IndexError:
            if(len(joinList) > 0):
                print(f"Fatal IndexError is_recentest_join: Server:{serverName}, {len(joinList)} joins, {len(leaveList)} leaves at {datetime.now()}")
            return None

    def add_connect_event(self,username,serverName,is_online):
        '''Adds Join/Leave event to UUID by ServerName'''
        uuid = self.get_player_uuid(username)

        # Check if player is in DB, if not, adds
        try:
            Time = datetime.now()
            server_index = self.get_server_index(serverName)
            uuid_index = self.get_uuid_index(uuid)
            
            # Add Player
            if uuid_index == None:
                self.add_player(username)
                uuid_index = self.get_uuid_index(uuid)
            
            # Add Join/Leaves w/ fixing logic
            response = self.is_recentest_join(uuid_index, server_index, serverName)
            if is_online:
                # If Adding Join, most recent entry is a join, remove previous join
                if response == True:
                    DB.playerstats[uuid_index]["Servers"][server_index][serverName]["Joins"].pop()
                DB.playerstats[uuid_index]["Servers"][server_index][serverName]["Joins"].append(str(Time))

            else:
                # If adding Leave, most recent entry is a leave, ignore adding leave
                if response == True:
                    DB.playerstats[uuid_index]["Servers"][server_index][serverName]["Leaves"].append(str(Time))
        except ValueError:
            print(f'ValueError: "{uuid}" not a valid UUID.')
        except UnboundLocalError:
            print(f'UnboundLocalError: "{serverName}" not a valid server.')
        
    # Connect Event Queue -------------------------------------------------------------------------------
    @tasks.loop(seconds=1)
    async def connect_event_handler(self):
        q = DB.get_connect_queue()

        # Quick Return
        if q.qsize() == 0: return

        # Calculate
        f = False
        while not q.qsize() == 0:
            f = True
            x = q.get()
            if x['type'] == MessageType.JOIN:
                is_online = True
            else:
                is_online = False
            self.add_connect_event(x['username'], x['server'], is_online)
        if f: DB.save_playerstats()
    @connect_event_handler.before_loop
    async def before_connect_event_handler(self):
        await self.bot.wait_until_ready() 
    
    # Calculate Playtime ------------------------------------------------------------------------------------------
    def calculate_playtime(self, joinList, leaveList, uuid_index, serverName):
        """Computes playtimes from list of leave and join dt"""
        total = timedelta()
        # Main calculate if there is a leave
        try: 
            if len(leaveList) > 0:
                for index in range(len(leaveList)):
                    total += (leaveList[index] - joinList[index])
            else:
                index = -1
        except IndexError:
            print(f"Index Error in Calculate Playtime: {uuid_index} {serverName} with {len(joinList)} joins and {len(leaveList)} leaves.")
        
        # If there's 1 more join than leaves
        if (len(joinList) == len(leaveList) + 1) or (joinList and not leaveList):
            now = datetime.now()
            total += (now - joinList[index+1])
        return total  

    def get_playtime(self, uuid_index, serverIndex, serverName):
        """Returns calculated time for server; Handles listbuilding for joins/leaves"""
        joinList = self.get_join_list_dt(uuid_index, serverIndex, serverName)
        leaveList = self.get_leave_list_dt(uuid_index, serverIndex, serverName)
        return self.calculate_playtime(joinList, leaveList, uuid_index, serverName)
    
    def update_playtime(self, uuid_index, serverIndex, serverName, pt):
        """Updates playtime and last computed of player by server"""
        DB.playerstats[uuid_index]["Servers"][serverIndex][serverName]["Total Playtime"] = str(pt)
        DB.playerstats[uuid_index]["Servers"][serverIndex][serverName]["Last Computed"] = str(datetime.now())

    def handle_playtime(self, uuid_index, serverName='total'):
        """Calls calculation functions, returns appropriate playtime"""   
        if serverName.lower() == 'total':
            pinetotal = timedelta()
            
            serverIndex = 0
            for server in DB.playerstats[uuid_index]["Servers"]:
                playt = self.get_playtime(uuid_index, serverIndex, list(server.keys())[0])
                self.update_playtime(uuid_index, serverIndex, list(server.keys())[0], playt)
                pinetotal += playt
                serverIndex += 1

            DB.save_playerstats()
            return pinetotal
        else: # Catch to check if servername matches valid container, otherwise returns none?
            playt = self.get_playtime(uuid_index, serverName)
            self.update_playtime(uuid_index, serverName, playt)

            DB.save_playerstats()
            return playt
        
    # Commands -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    @commands.command(name='playtime',help='Returns playtime on pineservers. >playtime <player-name> <server-name>, otherwise returns total of player.',brief='Get total playtime.')
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
            total = self.handle_playtime(uuid_index)
            await ctx.send(f"{name} has played for `{self.td_format(total)}` across all servers.")
            return

        # Specific Server Playtime
        else: 
            single = self.handle_playtime(uuid_index, server.title())
            if single:
                await ctx.send(f"{name} has played for `{self.td_format(single)}` on {server.title()}.")
                return
            elif single == timedelta():
                await ctx.send(f"{name} hasn't played on {server.title()}.")
            else:
                await ctx.send(f"Server not found.")
    
def setup(bot):
    bot.add_cog(Analytics(bot))