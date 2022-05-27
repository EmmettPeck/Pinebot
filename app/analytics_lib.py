"""
analytics_lib.py

By: Emmett Peck
A group of handling datetime & connection logging, playtime calculating functions.
"""
from datetime import datetime, timedelta
from database import DB

# DateTime Stuff ------------------------------------------------------------------------------------------------
def str_to_dt(dt_str):
    """Converts string to datetime format"""
    return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S.%f')

def str_to_timedelta(dt_str, first_join:datetime):
    """Converts datetime to string format"""
    return str_to_dt(dt_str) - first_join

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

def get_connect_dt_list(statistics:dict) -> tuple:
    """Returns tuple(joinList, leaveList) for statistics entry"""
    joinList = []
    leaveList = []

    for join in statistics["joins"]:
        joinList.append(str_to_dt(join))
    for leave in statistics["leaves"]:
        leaveList.append(str_to_dt(leave))
    return joinList, leaveList

# Connect Event -----------------------------------------------------------------------------------------------------------------------------------------------
def is_recentest_join(statistics:dict) -> bool:
    """
    Returns true if Join is most recent connect event
    """
    joinList, leaveList = get_connect_dt_list(statistics=statistics)
    try:
        if(len(leaveList) > 0):
            if(joinList[-1] > leaveList[-1]):
                return True
            else:
                return False
        # First Leave Catch
        elif (len(joinList) == 1) and (len(leaveList) == 0):
            return True
        # First Join Catch
        elif(len(joinList) == 0) and (len(leaveList) == 0):
            return False
        else:
            raise NotImplementedError(f" Server:{__name__}, {len(joinList)} joins, {len(leaveList)} leaves at {datetime.utcnow()}")
    except IndexError:
        raise NotImplementedError(f" Server:{__name__}, {len(joinList)} joins, {len(leaveList)} leaves at {datetime.utcnow()}")

# Playtime -----------------------------------------------------------------------------------------------------------------------------------------------
def calculate_playtime(statistics:dict, server_name:str, player_name:str, cog) -> datetime:
    """
    Intelligently calculates playtime of a server for a player.
    Usage: calculate_playtime(server.statistics) -> playtime

    Increments total, calculating only new pairs and current online status. 
    Total stored as firstjoin+totalplaytime. On load converted to timedelta.
    """
    c_index = statistics.get('calculated_index')
    # If calculated_index is less than leaves total_index, and joins == leaves return total
    try:
        if (c_index <= len(statistics.get('leaveList'))) and (len(statistics.get('leaveList')) == len(statistics.get('leaveList'))): return total
    except TypeError: pass # Catch for TypeError: object of type 'NoneType' has no len()

    # Ensure joinList exists, use firstJoin to load/save total
    joinList, leaveList = get_connect_dt_list(statistics=statistics)
    if len(joinList) == 0: return None
    if statistics.get('total_playtime') == '':
        total = timedelta()
    else:
        total = str_to_timedelta(statistics.get('total_playtime'), joinList[0])

    # Fixing: If first leave before first join
    try:
        if leaveList[0] < joinList[0]:
            statistics['leaves'].pop()
    except IndexError: pass #print(f"Index Error in Calculate Playtime: {__name__}:{statistics} with {len(joinList)} joins and {len(leaveList)} leaves at {c_index} index.")

    # Main calculate if there is a leave
    try:
        if len(leaveList) > 0:
            for index in range(c_index+1,len(leaveList)):
                total += (leaveList[index] - joinList[index])
                c_index+=1
    except TypeError: pass
    
    # Set Statistics
    statistics['total_playtime'] = str(total+joinList[0])
    statistics['calculated_index'] = c_index
    cog.set_statistics(statistics=statistics, server_name=server_name,request=player_name)
    # TODO cog.save_statistics()

    # Playtime for online players -- If there's 1 more join than leaves
    try:
        if (len(joinList) == len(leaveList) + 1) or (joinList and not leaveList):
            now = datetime.utcnow()
            return total + now - joinList[c_index+1]
    except TypeError: # Catch 'NoneType'
        pass

    return total 

# ---------------------------------------------------------------------------------------------------------------------------------------------------------
def handle_playtime(bot, who:str, server_name:str='total'):
    """
    Gathers playtime for applicable servers
    Gathers total playtime if requested
    Passes server data by reference to calculate_playtime
    Gathers cogs intelligently
    """   

    if server_name.title() == "Total":
        print("EEE: handle_playtime(request_name='total'): Not Implemented.")
        return None
    else:
        # Look for servername among docker_names and server_names
        for cog in DB.get_game_cogs():
            current = bot.get_cog(cog.split('.',1)[1].title())
            if current == None: continue
            stats = current.get_statistics(server_name=server_name, request=who)

            # Ensure servername
            if stats:
                cal = calculate_playtime(statistics=stats, server_name=server_name, player_name=who,cog=current)
                return cal
        return None