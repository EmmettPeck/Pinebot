"""
analytics_lib.py

By: Emmett Peck
A group of indexing, handling datetime & connection logging, playtime calculating functions.
"""
from datetime import datetime, timedelta
from database import DB
from username_to_uuid import UsernameToUUID

# Indexing --------------------------------------------------------------------------------------------------------
def get_player_uuid(username):
        """Get player UUID from username"""
        converter = UsernameToUUID(username)
        uuid = converter.get_uuid()
        return uuid
    
def get_uuid_index(uuid):
    """Returns index of specific UUID in playerstats"""
    for D in DB.playerstats: #Looks at each dict
            if uuid == D["UUID"]:  #If dict UUID value matches UUID
                return DB.playerstats.index(D) #Sets index to index of dict
    return None

def get_server_index(serverName):
    """Returns index of specific serverName in playerstats"""
    uuid_index = get_uuid_index("")

    # Analytics names MUST match case sensitive Container Names (titletext)
    for D in DB.playerstats[uuid_index]["Servers"]:
        if serverName in D.keys():
            return DB.playerstats[uuid_index]["Servers"].index(D)
    return None

# DateTime Stuff ------------------------------------------------------------------------------------------------
def str_to_dt(dt_str):
    """Converts string to datetime format"""
    return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S.%f')    

def td_format(td_object):
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

def get_connect_dt_list(uuid_index, server_index, serverName) -> tuple:
    """Returns tuple(joinList, leaveList) for corresponding server"""
    joinList = leaveList = []

    for join in DB.playerstats[uuid_index]["Servers"][server_index][serverName]["Joins"]:
        joinList.append(str_to_dt(join))
    for leave in DB.playerstats[uuid_index]["Servers"][server_index][serverName]["Leaves"]:
        leaveList.append(str_to_dt(leave))
    
    return joinList, leaveList

# Connect Event -----------------------------------------------------------------------------------------------------------------------------------------------
def is_recentest_join(uuid_index, serverIndex, serverName):
    "Returns true if Join is most recent connect event"
    joinList, leaveList = get_connect_dt_list(uuid_index, serverIndex, serverName)
    
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
            print(f"Fatal IndexError is_recentest_join: Server:{serverName}, {len(joinList)} joins, {len(leaveList)} leaves at {datetime.utcnow()}")
        return None

def add_connect_event(username, serverName, is_join, Time):
    '''Adds Join/Leave event to UUID by ServerName'''
    try:
        uuid = get_player_uuid(username)
        server_index = get_server_index(serverName)
        uuid_index = get_uuid_index(uuid)
        
        if (server_index is None) or (uuid is None):
            return

        # Add New Players
        if uuid_index == None:
            add_player(username)
            uuid_index = get_uuid_index(uuid)
        
        # Add Join/Leaves w/ fixing logic
        response = is_recentest_join(uuid_index, server_index, serverName)
        if is_join:
            # If Adding Join, most recent entry is a join, remove previous join
            if response == True:
                DB.playerstats[uuid_index]["Servers"][server_index][serverName]["Joins"].pop()
            DB.playerstats[uuid_index]["Servers"][server_index][serverName]["Joins"].append(str(Time))
        else:
            # If adding Leave, most recent entry is a leave, ignore adding leave
            if response == True:
                DB.playerstats[uuid_index]["Servers"][server_index][serverName]["Leaves"].append(str(Time))\
        
    except ValueError:
        print(f'ValueError: "{uuid}" not a valid UUID.')
    except UnboundLocalError:
        print(f'UnboundLocalError: "{serverName}" not a valid server.')

# Player ------------------------------------------------------------------------------------------------------------------------------------------------
def add_player( username):
    """Adds player to json, copying servers from empty"""
    uuid = get_player_uuid(username)

    if get_uuid_index(uuid):
        print(f"ERROR: add_player {username} already exists.")
    totem_index = get_uuid_index("")

    # Create player
    DB.playerstats.append({"UUID":uuid,"Servers":[]})

    # Copy servers from empty to new
    server_list = tag_list = []
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

# Playtime ------------------------------------------------------------------------------------------
def calculate_playtime(joinList, leaveList, uuid_index, serverName):
    """Computes betweentime for leave & join dt lists"""
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
        now = datetime.utcnow()
        total += (now - joinList[index+1])
    return total  

def get_playtime(self, uuid_index, serverIndex, serverName):
    """Returns calculated time for server; Handles listbuilding for joins/leaves"""
    joinList, leaveList = get_connect_dt_list(uuid_index=uuid_index,server_index=serverIndex,serverName=serverName)
    # TODO Check if below TODO Is still relevent 
        # TODO If joinList len == leavelist len, check if player is online, if so, then well fuck. 
    return self.calculate_playtime(joinList, leaveList, uuid_index, serverName)

def update_playtime(uuid_index, serverIndex, serverName, pt):
    """Updates playtime and last computed of player by server"""
    DB.playerstats[uuid_index]["Servers"][serverIndex][serverName]["Total Playtime"] = str(pt)
    DB.playerstats[uuid_index]["Servers"][serverIndex][serverName]["Last Computed"] = str(datetime.utcnow())

def handle_playtime(uuid_index, serverName='total'):
    """Default:Returns total playtime for 'total', otherwise returns serverName playtime."""   
    # TODO move to return list of dicts for total, otherwise a single dict
    if serverName.lower() == 'total':
        play_total = timedelta()
        
        serverIndex = 0
        for server in DB.playerstats[uuid_index]["Servers"]:
            playt = get_playtime(uuid_index, serverIndex, list(server.keys())[0])
            update_playtime(uuid_index, serverIndex, list(server.keys())[0], playt)
            play_total += playt
            serverIndex += 1

        DB.save_playerstats()
        return play_total
    else:
        server_index = get_server_index(serverName) 
        playt = get_playtime(uuid_index, server_index, serverName)
        update_playtime(uuid_index, server_index, serverName, playt)
        DB.save_playerstats()
        return playt