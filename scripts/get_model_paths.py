"""
Get model file paths for a given range of model IDs, example:

python3 get_model_paths.py 512 513
"""
import json
import sys
from atmosphere.database import generate_db_session
from moonbow.database import Model
session = generate_db_session()
if __name__ == "__main__":
    mapping = {}
    for mgid in range(int(sys.argv[1]), int(sys.argv[2]) + 1):
        path = session.query(Model).filter(Model.id == mgid).first().model_file_path
        mapping[mgid] = path
    print(mapping)