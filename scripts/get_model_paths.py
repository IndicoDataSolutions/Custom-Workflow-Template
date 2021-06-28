"""
Kube exec moonbow
then run this script passing a range of model IDs, i.e. python3 get_model_paths.py 512 512 
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
    with open("model_file_paths.json", "w") as fd:
        json.dump(mapping, fd)
    print(mapping)