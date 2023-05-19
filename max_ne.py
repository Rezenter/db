import requests
import json

with open('db/index.json', 'r') as file:
    db_arr = json.load(file)
    db = {
        shot['shotn']: shot for shot in db_arr
    }

    shots = list(db.keys())
    shots.reverse()

lines = []

for shotn in shots:
    if shotn <= 42400:
        break
    print(shotn)
    resp = requests.post('https://172.16.12.130/api', json={
        'subsystem': 'db',
        'reqtype': 'get_shot_verified',
        'shotn': shotn
    }, verify=False).text
    shot = json.loads(resp)
    if not shot['ok']:
        if shot['description'] == 'Verified shotn "%d" does not exist' % shotn:
            continue
        print(shot['description'])
        fuck
    shot['sht'] = db[shotn]

    #with open('tmp.json', 'w') as dump:
    #    json.dump(shot, dump, indent=2)

    if 'data' not in shot['cfm']:
        continue
    for cfm_event in shot['cfm']['data']:
        event = shot['shot']['events'][cfm_event['event_index']]
        if event['error'] is not None:
            continue
        if 'data' not in cfm_event:
            continue
        if 'nl_eq' not in cfm_event['data']:
            continue
        if cfm_event['data']['nl_eq'] is None:
            continue
        if cfm_event['data']['nl_eq'] > 7e19:
            lines.append('%d %.2e' % (shotn, cfm_event['data']['nl_eq']))

for line in lines:
    print(line)

print('Code OK')