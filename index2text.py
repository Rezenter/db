import json

db_file: str = 'db/index.json'

db: dict = None
with open(db_file, 'r') as f:
    db = json.load(f)

for shotn in db:
    v = db[shotn]
    if 'err' in v:
        continue
    if v['T_flattop_stop'] - v['T_flattop_start'] < 0.005:
        continue
    line: str = '%s %s %.4f %.4f %.0f %.2f %d %d %d %d %s' % (shotn, v['date'], v['T_flattop_start'], v['T_flattop_stop'], v['Ip'], v['Bt'], 'err' not in v['NBI1'], 'err' not in v['NBI2'], 'err' not in v['TS'], 'err' not in v['TS'] and v['TS']['processed'], v['plasma isotope'])
    print(line)