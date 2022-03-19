class FingerPrints:

    def __init__(self):
        self.fingerprintDB = self.load_fingerprintDB()
    
    def load_fingerprintDB(self):
        """Loads the previous 100 message hashes"""
        with open(r"data/hashDump.json", 'r') as read_file:
            return json.load(read_file)
    
    def save_fingerprintDB(self):
        """Saves the previous 100 message hashes"""
        with open(r"data/hashDump.json", 'w') as write_file:
            json.dump(self.fingerprintDB, write_file, indent = 2)
    
    def get_hash_int(self, instr):
        """Returns a hashed int of provided string"""
        sha256hash = hashlib.sha256()
        sha256hash.update(instr.encode('utf8'))
        hash_id = sha256hash.hexdigest()
        hash_ = int(hash_id,16)
        return hash_

    def is_unique_fingerprint(self, fingerprint, database_list):
        """Compares hash to provided database_list"""
        try:
            comparison = database_list.index(fingerprint)
        except ValueError as v:
            database_list.insert(0, fingerprint)
            # Pop elements over pos 100 to keep the list small
            if len(database_list) > 100: 
                database_list.pop(100)
            return True
        else:
            return False