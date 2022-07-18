import hashlib

def get_hash(instr):
    """Returns a hashed hexidecimal of provided string"""
    sha256hash = hashlib.sha256()
    sha256hash.update(instr.encode('utf8'))
    return sha256hash.hexdigest()