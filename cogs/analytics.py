"""A class used to track player activity and log it for analytics"""

import json

from username_to_uuid import UsernameToUUID

class Analytics():

    def __init__(self):
        self.playerstats = self.load_playerstats()
        if self.playerstats:
            pass
        else:
            self.create_playerstats()
    
    def get_player_UUID(username):
        """Get player UUID from username"""
        converter = UsernameToUUID(username)
        uuid = converter.get_uuid()
        return uuid

    def load_playerstats(self):
        """Load playerstats from playerstats.json"""
        try:
            with open("data/playerstats.json") as f:
        except FileNotFoundError:
            return None:
        else:
            return json.load(f)

    def save_playerstats(self):
        """Saves playerstats to playerstats.json"""
        with open("data/playerstats.json", 'w') as f:
            json.dump(self.playerstats, f, indent = 2)
    
    def create_playerstats(self):
        """Creates empty playerstats.json structure"""
            # Save playerstat structure
            # players
                # UUIDS 
                    # Playtime w/ Last computed tag
                        # Join/Leave Pairs
                            # Join/Leaves w/ Times & servers
                            
        return 

    def on_player_join(self, server, username, time):
        """Adds player join to playerstats."""
        
        # If previous join unmatched, call false_join()

    def on_player_leave(self, server, username, time):
        """Add player leave to playerstats"""
        
        # If previous leave unmatched, call false_leave()
        
    def false_join(self, username, time):
        """Handles a false join message"""

        # Check if player is on server, if so, pass

        # If not, remove previous join message
    
    def false_leave(self, username, time):
        """Handles a false leave message"""  

        # Check if player is on server, if not, pass

        # If so, remove leave message in question.
    
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
    