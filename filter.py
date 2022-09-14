import json

request_TS: bool = True
request_NBI1 = {
    'is': True,
    'duration_min': 15,
    'duration_max': 200
}
request_NBI2 = {
    'is': True,
    'duration_min': 15,
    'duration_max': 200
}

request_Bt = {
    'is': False,
    'min': 0.85,
    'max': 1.0
}
request_flattop = {
    'is': True,
    'min': 40,
    'max': 200
}

baddies: list[int] = [41845]

with open('index_all.json', 'r') as file:
    db = json.load(file)

for shot in db:
    if shot['shotn'] in baddies:
        continue

    if 'err' in shot:
        continue
    if request_TS and 'err' in shot['TS']:
        continue

    if request_NBI1['is']:
        if 'err' in shot['NBI1']:
            continue
        if not request_NBI1['duration_min'] <= (shot['NBI1']['T_stop'] - shot['NBI1']['T_start']) * 1000 <= \
               request_NBI1['duration_max']:
            continue

    if request_NBI2['is']:
        if 'err' in shot['NBI2']:
            continue
        if not request_NBI2['duration_min'] <= (shot['NBI2']['T_stop'] - shot['NBI2']['T_start']) * 1000 <= \
               request_NBI2['duration_max']:
            continue

    if request_Bt['is']:
        if not request_Bt['min'] <= shot['Bt'] <= request_Bt['max']:
            continue

    if request_flattop['is']:
        if not request_flattop['min'] <= (shot["T_flattop_stop"] - shot["T_flattop_start"]) * 1000 <= request_flattop['max']:
            continue

    flattop: float = (shot["T_flattop_stop"] - shot["T_flattop_start"]) * 1000
    print('%d %d %.3f %d' % (shot['shotn'], shot['Ip'], shot['Bt'], flattop))
    #print('%d %.3f' % (shot['Ip'], shot['Bt']))

print('Code OK')
