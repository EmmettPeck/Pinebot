"""
A module to calculate a total playtime from a lists (join/leave) datetimes.

Authors: Emmett Peck (EmmettPeck)
Version: July 14th, 2022
"""
from pymongo import collection
from datetime import datetime, timedelta
import logging

from bson import ObjectId
from dictionaries import playtime_dict

# DateTime Functions -----------------------------------------------------------
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

# Connect Event ----------------------------------------------------------------
def is_recentest_join(col:collection.Collection, id:ObjectId) -> bool:
    """
    Returns true if Join is most recent connect event, otherwise returns false
    """
    statistics = col.find_one({'_id' : id})
    joinList, leaveList = statistics['joins'], statistics['leaves']
    join_len, leave_len = len(joinList), len(leaveList)

    if(leave_len > 0) and (join_len > 0):
        if(joinList[-1] > leaveList[-1]):
            return True
        else:
            return False

    # First Leave Catch
    elif (join_len == 1) and (leave_len == 0):
        return True

    # First Join Catch
    elif(join_len == 0) and (leave_len == 0):
        return False

# Playtime -----------------------------------------------------------------------------------------------------------------------------------------------
def calculate_playtime(col:collection.Collection, id:ObjectId) -> datetime:
    """
    Intelligently calculates playtime of a server for a player.
    Usage: calculate_playtime(server.statistics) -> playtime

    Increments total, calculating only new pairs and current online status. 
    Total stored as firstjoin+totalplaytime. On load converted to timedelta.
    """
    # Get Element from MongoDB
    statistics = col.find_one({'_id' : id})
    if statistics is None: return None

    # Variables
    total = statistics['total_playtime']
    c_index = statistics['calculated_index']
    joinList = statistics['joins']
    leaveList = statistics['leaves']
    package = {
        'first_join':joinList[0],
        'last_connected':leaveList[-1],
        'playtime':None
    }
    # Return timedelta if no joins in list
    if len(joinList) == 0: return timedelta()

    # If no leaves/joins since last calculation, return previous total
    if ((c_index <= len(leaveList)) 
    and (len(leaveList) == len(leaveList))):
        return total

    # Fixing: If first leave before first join
    if len(leaveList)>0 and len(joinList)>0:
        if leaveList[0] < joinList[0]:
            statistics['leaves'].pop()

    # Main calculate if there is a leave
    if len(leaveList) > 0:
        for index in range(c_index+1,len(leaveList)):
            total += (leaveList[index] - joinList[index])
            c_index+=1

    # Update Database
    statistics['total_playtime'] = str(total+joinList[0])
    statistics['calculated_index'] = c_index
    col.update_one({'_id':id}, {"$set":statistics})

    # Set Returntime to total
    package['playtime'] = total 

    # Playtime for online players -- If there's 1 more join than leaves
    if (len(joinList) == len(leaveList) + 1) or (joinList and not leaveList):
        now = datetime.now()
        package['playtime'] = total + now - joinList[c_index+1]

    logging.debug(f"calculate_playtime: {package}")
    return package