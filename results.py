import requests
import json

#0.9T 0.4MA
shots = [41644, 41645, 41649, 41661, 41662, 41664, 41665, 41666, 42123]

#0.9T 0.35MA
shots = [42095]

NBI_delay_start = 10 # ms
NBI_delay_stop = 0 # ms

lines = []

with open('index_all.json', 'r') as file:
    db_arr = json.load(file)
    db = {
        shot['shotn']: shot for shot in db_arr
    }

    for shotn in shots:
        print(shotn)
        resp = requests.post('https://172.16.12.130/api', json={
            'subsystem': 'db',
            'reqtype': 'get_shot_verified',
            'shotn': shotn
        }, verify=False).text
        shot = json.loads(resp)
        shot['sht'] = db[shotn]

        with open('tmp.json', 'w') as dump:
            json.dump(shot, dump)

        if shot['sht']["T_flattop_start"]*1000 < shot['shot']['override']['t_start'] or \
                shot['sht']["T_flattop_stop"]*1000 > shot['shot']['override']['t_stop']:
            fuck

        for cfm_event in shot['cfm']['data']:
            event = shot['shot']['events'][cfm_event['event_index']]
            if not shot['sht']["T_flattop_start"]*1000 < event['timestamp'] < shot['sht']["T_flattop_stop"]*1000:
                continue
            if not shot['sht']['NBI1']["T_start"] * 1000 + NBI_delay_start < event['timestamp'] < shot['sht']['NBI1']["T_stop"] * 1000 - NBI_delay_stop:
                continue
            if not shot['sht']['NBI2']["T_start"] * 1000 + NBI_delay_start < event['timestamp'] < shot['sht']['NBI2']["T_stop"] * 1000 - NBI_delay_stop:
                continue
            lines.append('%d %.2f %.2e %.2e %.2e %.2e %.3f %.3f' % (shotn,
                                              event['timestamp'],
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