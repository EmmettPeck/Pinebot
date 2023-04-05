Database Structure
==================

Server configuration information is stored in the `Servers` collection.

Server specific information is stored in the `<game-name>` collection.
    
    * IE: playtime, username, uuid

.. code-block:: sh
   :caption: Database Structure

    mongo
    ├── Servers
    │   ├── minecraft
    │   ├── factorio
    │   └── <game>  
    │       └── [
    │               {
                    "game":game,                # Game (Ie: Minecraft)
                    "version":version,          # Version (Ie: 1.18, 1.19)
                    "docker_name":docker,       # Docker Name
                    "cid":cid,                  # Channel ID List
                    "ip":ip,                    # IP to display in the server-list
                    "description":description,  # Description to display in the server-list
                    "hidden":hidden,            # Whether or not to display in the server list
                    "active" : True,            # Determines whether or not the server is watched
                    "online_players": list(),   # List of online players
                    "player_max": -1,           # Max Players (Default -1 for ∞)
                    "link_keys": list()         # Codes to check against new msgs
                    }
    │           ]
    └── <game>
        └── <server-name>
            └── [
                    {
                        'username':username,
                        'uuid':uuid,
                        'total_playtime':timedelta(), 
                        'calculated_index':-1, 
                        'joins':[], 
                        'leaves':[],
                        'linked':''
                    }
                ]
...

Notes for database reformatting:

* Move player "statistics" dictionaries into list under Servers collection
* Add archived flag
* Move database access to ADT database class
* Always work with database remote for horizontal scaling structure.
* Remove neccesity of players knowing server-name. (let channel names work too)