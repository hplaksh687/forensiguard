import hashlib

def generate_evidence_hash(file_path):

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        while True:

            data = f.read(65536)

            if not data:
                break

            sha256.update(data)

    return sha256.hexdigest()