import json

request_TS: bool = True
request_ELM = {
    'filter': True,
    'is present': True,
    'maxAbsDelay': 0.05*1e-3
}
request_NBI1 = {
    'filter': False,
    'is present': True,
    'duration_min': 15,
    'duration_max': 200
}
request_NBI2 = {
    'filter': False,
    'is present': True,
    'duration_min': 15,
    'duration_max': 200
}

limit_Bt = {
    'filter': False,
    'min': 0.85,
    'max': 1.0
}
limit_Ip = {
    'filter': False,
    'min': 375,
    'max': 415
}
limit_flattop = {
    'filter': False,
    'min': 40,
    'max': 200
}

baddies: list[int] = [41845]

with open('db/index.json', 'r') as file:
    db = json.load(file)

for shot_str in db:
    shot = db[shot_str]
    if shot['shotn'] in baddies:
        continue

    if 'err' in shot:
        continue
    if request_TS and 'err' in shot['TS']:
        continue

    if request_ELM['filter']:
        if request_ELM['is present'] != (len(shot['ELM']) != 0):
            continue
        for elm in shot['ELM']:
            if abs(elm['las_delay']) < request_ELM['maxAbsDelay']:
                print(shot_str, elm['time']*1e3, elm['las_delay']*1e3)


    if request_NBI1['filter']:
        pass_filter: bool = True
        if 'err' in shot['NBI1']:
            pass_filter = False
        if not request_NBI1['duration_min'] <= (shot['NBI1']['T_stop'] - shot['NBI1']['T_start']) * 1000 <= \
               request_NBI1['duration_max']:
            pass_filter = False
        if request_NBI1['is present'] != pass_filter:
            continue

    if request_NBI2['filter']:
        pass_filter: bool = True
        if 'err' in shot['NBI2']:
            pass_filter = False
        if not request_NBI2['duration_min'] <= (shot['NBI2']['T_stop'] - shot['NBI2']['T_start']) * 1000 <= \
               request_NBI2['duration_max']:
            pass_filter = False
        if request_NBI2['is present'] != pass_filter:
            continue

    if limit_Bt['filter']:
        if not limit_Bt['min'] <= shot['Bt'] <= limit_Bt['max']:
            continue

    if limit_Ip['filter']:
        if not limit_Ip['min'] <= shot['Ip'] <= limit_Ip['max']:
            continue

    if limit_flattop['filter']:
        if not limit_flattop['min'] <= (shot["T_flattop_stop"] - shot["T_flattop_start"]) * 1000 <= limit_flattop['max']:
            continue

    flattop: float = (shot["T_flattop_stop"] - shot["T_flattop_start"]) * 1000
    #print('%d %d %.3f %d' % (shot['shotn'], shot['Ip'], shot['Bt'], flattop))
    #print('%d %.3f' % (shot['Ip'], shot['Bt']))

print('Code OK')
