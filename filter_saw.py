import json
from pathlib import Path

ts_path: Path = Path('//172.16.12.127/Pub/!!!TS_RESULTS/shots/')


request_NBI1 = {
    'duration_min': 0,
    'duration_max': 60
}
request_NBI2 = {
    'duration_min': 0,
    'duration_max': 300
}

limit_flattop = {
    'min': 20,
    'max': 300
}
limit_SXR = {
    'min_amp': 0.05,
    'skip_first': 3,
    'max_period': 6
}


baddies: list[int] = [41845]

with open('db/index.json', 'r') as file:
    db = json.load(file)

out: list[str] = ['shotn, Ip, Bt, flattop duration, time, NBI, period, amp\n',
                  '#, kA, T, ms, ms, bool, ms, V\n']

for shot_str in db:
    shot = db[shot_str]
    if shot['shotn'] in baddies:
        continue

    if 'err' in shot:
        continue

    if not limit_flattop['min'] <= (shot["T_flattop_stop"] - shot["T_flattop_start"]) * 1000 <= limit_flattop['max']:
        continue

    if 'time' not in shot['SXR']:
        continue

    for event in shot['SXR']['time'][limit_SXR['skip_first']:]:
        if event['amp'] <= limit_SXR['min_amp']:
            continue

        NBI = 0
        if 'err' not in shot['NBI1']:
            if request_NBI1['duration_min'] <= (shot['NBI1']['T_stop'] - shot['NBI1']['T_start']) * 1000 <= \
                    request_NBI1['duration_max'] and shot['NBI1']['T_start'] < event['time'] < shot['NBI1']['T_stop']:
                NBI += 1
        if 'err' not in shot['NBI2']:
            if request_NBI2['duration_min'] <= (shot['NBI2']['T_stop'] - shot['NBI2']['T_start']) * 1000 <= \
                    request_NBI2['duration_max'] and shot['NBI2']['T_start'] < event['time'] < shot['NBI2']['T_stop']:
                NBI += 2

        flattop: float = (shot["T_flattop_stop"] - shot["T_flattop_start"]) * 1000

        if event['period']*1000 > limit_SXR['max_period']:
            continue

        out_line: str = '%d, %d, %.2f, %d, %.1f, %d, %.3f, %.4f\n' % (shot['shotn'], shot['Ip'], shot['Bt'], flattop, event['time']*1000, NBI, event['period']*1000, event['amp'])

        out.append(out_line)


with open('out/filtered_saw.csv', 'w') as file:
    file.writelines(out)


print('Code OK')
