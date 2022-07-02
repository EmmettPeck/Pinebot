"""
fingerprints.py
By: Emmett Peck
Log and filter out past 100 non-unique fingerprints per class
"""

import json
import hashlib
import logging
import os

class FingerPrints:

    def __init__(self, docker_name):
        self.name = docker_name
        self.fingerprintDB = self.load_fingerprintDB()
    
    def load_fingerprintDB(self):
        try:
            # Create Path if it doesn't exist (Otherwise will throw exception)
            path = f'data/hashes/'
            if not os.path.exists(path):
                logging.debug(f"FingerPrints creating file structure {path}")
                os.makedirs(path)
                
            # Load Fingerprints
            with open(rf"data/hashes/hash_{self.name}.json", 'r') as read_file:
                return json.load(read_file)
        except FileNotFoundError:
            with open(rf"data/hashes/hash_{self.name}.json", 'w+') as write_file:
                json.dump([], write_file, indent = 2)
            return self.load_fingerprintDB()
    
    def save_fingerprintDB(self):
        with open(rf"data/hashes/hash_{self.name}.json", 'w') as write_file:
            json.dump(self.fingerprintDB, write_file, indent = 2)
    
    def get_hash_int(self, instr):
        """Returns a hashed int of provided string"""
        sha256hash = hashlib.sha256()
        sha256hash.update(instr.encode('utf8'))
        hash_id = sha256hash.hexdigest()
        hash_ = int(hash_id,16)
        return hash_

    def is_unique_fingerprint(self, string, database_list=None):
        """Compares hash to provided database_list"""
        fingerprint = self.get_hash_int(string)
        length = 100

        # Catch to set to own fingerprintdb
        if database_list == None:
            if self.fingerprintDB == None:
                return True
            database_list = self.fingerprintDB

        try:
            comparison = database_list.index(fingerprint)
        except ValueError as v:
            # Insert new elements to list 
            database_list.insert(0, fingerprint)
            # Pop elements over length to keep the list small
            if len(database_list) > length-1: 
                try:
                    database_list.pop(length)
                except IndexError:
                    logging.error(f"Pop index out of range {string}")
            self.save_fingerprintDB()
            return True
        else:
            return False
