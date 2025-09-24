import json
import msgpack
from pathlib import Path

shotn_start = 39000

db = None
with open('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\index.msgpk', 'rb') as file:
    db = msgpack.unpackb(file.read(), strict_map_key=False)

shots: list[Path] = [shot_dir for shot_dir in Path('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\').iterdir() if shot_dir.is_dir()]
shots.sort()
for shot_dir in shots:
    spl = str(shot_dir).split('\\')[-1]
    if len(spl) != 5:
        continue
    shotn = int(spl)
    if shotn < shotn_start:
        continue
    ts = []
    dynamics_path = shot_dir.joinpath('cfm_res.json')
    if not dynamics_path.exists():
        continue
    t_path = shot_dir.joinpath('result.json')
    if not t_path.exists():
        continue
    with open(dynamics_path, 'r') as file:
        ts = json.load(file)['data']
    with open(t_path, 'r') as file:
        tmp = json.load(file)
        for ev in ts:
            ev['main'] = tmp['events'][ev['event_index']]

    sxr = db['%d' % shotn]['SXR']

    print(shotn)