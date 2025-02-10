import json
from pathlib import Path

shots = range(45376, 45391)

ts_path: Path = Path('//172.16.12.127/Pub/!!!TS_RESULTS/shots/')

db = None
with open('%s\\index.json' % ts_path, 'r') as file:
    db = json.load(file)

for shotn in shots:
    key = '%d' % shotn
    if key in db:
        db.pop(key, None)
        print('removed', shotn)

with open('%s\\index.json' % ts_path, 'w') as file:
    json.dump(db, file, indent=2)
