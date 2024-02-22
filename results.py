import requests
import json


#0.9T 0.4MA
#H-D
shots = [41644, 41645, 41649, 41661, 41662, 41664, 41665, 41666, 42123]

#D-D
shots = [
    {
        'shotn': 42416
    }, {
        'shotn': 42417
    }
]

#0.9T 0.35MA H-D
shots = [
    {
        'shotn': 42095
    }, {
        'shotn': 42116
    }, {
        'shotn': 42118
    }, {
        'shotn': 42119
    }, {
        'shotn': 42120
    }, {
        'shotn': 42093
    }, {
        'shotn': 41623
    }, {
        'shotn': 41625
    }, {
        'shotn': 41626
    }, {
        'shotn': 41627
    }, {
        'shotn': 41628
    }, {
        'shotn': 41629
    }, {
        'shotn': 41630
    }, {
        'shotn': 41631
    }
]

#0.9T 0.35MA D-D
shots = [
    {
        'shotn': 41585
    }, {
        'shotn': 42362
    }, {
        'shotn': 42364
    }, {
        'shotn': 42366
    }, {
        'shotn': 42367
    }, {
        'shotn': 42368
    }, {
        'shotn': 42410
    }, {
        'shotn': 42414
    }
]

'''
#0.9T 0.30MA
shots = [
    {
        'shotn': 41602,
        'skip':[
            210,
            212,
            216,
            219,
            206
        ]
    },{
        'shotn': 41608
    },{
        'shotn': 41610
    },{
        'shotn': 41611,
        'skip:': [204]
    },{
        'shotn': 41612
    },{
        'shotn': 41613,
        'skip:': [192,
                  195]
    },{
        'shotn': 41615
    },{
        'shotn': 41616,
        'skip':[
            207,
            210,
            213,
            216
        ]
    },{
        'shotn': 41620
    },{
        'shotn': 42089
    }]
'''

#H-H
#0.9T 0.30MA
'''shots = [{
        'shotn': 41730,
        'skip:': [207, 210, 213, 216, 219]
    }]'''


#0.8T 0.4MA OH
shots = [{'shotn': x} for x in range(41504, 41517)]

NBI_delay_start = 10 # ms
NBI_delay_stop = 0 # ms

lines = []

with open('db/index.json', 'r') as file:
    db = json.load(file)

    for req_shot in shots:
        shotn = req_shot['shotn']
        print(shotn)
        resp = requests.post('https://172.16.12.130/api', json={
            'subsystem': 'db',
            'reqtype': 'get_shot_verified',
            'shotn': shotn
        }, verify=False).text
        shot = json.loads(resp)
        if not shot['ok']:
            print(shot['description'])
            fuck
        shot['sht'] = db[str(shotn)]

        with open('tmp.json', 'w') as dump:
            json.dump(shot, dump, indent=2)

        for cfm_event in shot['cfm']['data']:
            event = shot['shot']['events'][cfm_event['event_index']]
            if event['error'] is not None:
                continue
            if 'skip' in req_shot:
                flag: bool = False
                for skip in req_shot['skip']:
                    if skip - 1.1 < event['timestamp'] < skip + 1.1:
                        flag = True
                        break
                if flag:
                    continue
            if not shot['sht']["T_flattop_start"] * 1000 < event['timestamp'] < shot['sht']["T_flattop_stop"] * 1000:
                continue
            '''
            if not shot['sht']['NBI1']["T_start"] * 1000 + NBI_delay_start < event['timestamp'] < shot['sht']['NBI1']["T_stop"] * 1000 - NBI_delay_stop:
                continue
            if not shot['sht']['NBI2']["T_start"] * 1000 + NBI_delay_start < event['timestamp'] < shot['sht']['NBI2']["T_stop"] * 1000 - NBI_delay_stop:
                continue
            '''
            lines.append('%d %.2f %.2f %d %.2e %.2e %.2e %.2e %.3f %.3f' % (shotn,
                                              event['timestamp'],
                                              shot['sht']['Bt'],
                                              shot['sht']['Ip'],
                                              cfm_event['data']['nl'] / (cfm_event['data']['nl_profile'][0]['z'] - cfm_event['data']['nl_profile'][-1]['z']) * 1e2,
                                              cfm_event['data']['nl_err'] / (cfm_event['data']['nl_profile'][0]['z'] - cfm_event['data']['nl_profile'][-1]['z']) * 1e2,
                                              cfm_event['data']['n_vol'],
                                              cfm_event['data']['n_vol_err'],
                                              cfm_event['data']['vol_w'] * 1e-3,
                                              cfm_event['data']['w_err'] * 1e-3
                                              ))

for line in lines:
    print(line)

print('Code OK')