import json
import msgpack
from pathlib import Path

from Zeff_matcher import entry

ts_path: Path = Path('//172.16.12.127/Pub/!!!TS_RESULTS/shots/')

shots = {
    44335: {
        'ref_start': 136,
        'eho_start': 145,
        'eho_stop': 155,
        'ref_stop': 162
    },
    44173: {
        'ref_start': 135,
        'eho_start': 146,
        'eho_stop': 158,
        'ref_stop': 168
    },
    44249: {
        'ref_start': 135,
        'eho_start': 145,
        'eho_stop': 157,
        'ref_stop': 162
    },
    44381: {
        'ref_start': 130,
        'eho_start': 138.5,
        'eho_stop': 150,
        'ref_stop': 150.05
    },
    44387: {
        'ref_start': 133,
        'eho_start': 144,
        'eho_stop': 159,
        'ref_stop': 160
    },
    44388: {
        'ref_start': 133,
        'eho_start': 144,
        'eho_stop': 156,
        'ref_stop': 157
    },
    44390: {
        'ref_start': 133,
        'eho_start': 144,
        'eho_stop': 156,
        'ref_stop': 183
    },
    44391: {
        'ref_start': 133,
        'eho_start': 145,
        'eho_stop': 153,
        'ref_stop': 153
    },
    44392: {
        'ref_start': 133,
        'eho_start': 145,
        'eho_stop': 153,
        'ref_stop': 154
    },
    43922: {
        'ref_start': 140,
        'eho_start': 148,
        'eho_stop': 156,
        'ref_stop': 181
    }
}

res_ref_n = ''
res_ref_t = ''
res_eho_n = ''
res_eho_t = ''
res_post_n = ''
res_post_t = ''

for shotn in shots.keys():
    shot = shots[shotn]
    shot_dir: Path = ts_path.joinpath('%d' % shotn)
    if not shot_dir.exists():
        fuck
    ts = []
    rads = []
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
        for poly in tmp['config']['poly']:
            rads.append(poly['R'])
        for ev in ts:
            ev['main'] = tmp['events'][ev['event_index']]

    for ev in ts:
        if shot['ref_start'] < ev['main']['timestamp'] < shot['ref_stop']:
            print(shotn, ev['main']['timestamp'])
            entry = '%d, %.2f, ' % (shotn, ev['main']['timestamp'])
            lcfs = 0
            if ev['data']['surfaces'][0]['z'][0] * ev['data']['surfaces'][0]['z'][-1] <= 0 and ev['data']['surfaces'][0]['r'][0] > 42:
                lcfs = ev['data']['surfaces'][0]['r'][0] * ev['data']['surfaces'][0]['r'][-1] * 0.5
            else:
                for i in range(len(ev['data']['surfaces'][0]['z']) - 1):
                    if ev['data']['surfaces'][0]['z'][i] * ev['data']['surfaces'][0]['z'][i+1] <= 0 and ev['data']['surfaces'][0]['r'][i] > 42:
                        lcfs = (ev['data']['surfaces'][0]['r'][i] + ev['data']['surfaces'][0]['r'][i+1]) * 0.5
                        break
                else:
                    fuck
            entry += '%.2f, %.2f, %.2f, ' % (lcfs*10, ev['data']['t_vol'], ev['data']['n_vol'])
            entry_t = entry
            entry_n = entry
            for poly_ind in range(len(ev['main']['T_e'])):
                if 'T' in ev['main']['T_e'][poly_ind]:
                    entry_t += '%.2f, %.2f, %.2f, ' % (rads[poly_ind]-lcfs*10, ev['main']['T_e'][poly_ind]['T']/ev['data']['t_vol'], ev['main']['T_e'][poly_ind]['Terr']/ev['data']['t_vol'])
                    entry_n += '%.2f, %.2f, %.2f, ' % (rads[poly_ind]-lcfs*10, ev['main']['T_e'][poly_ind]['n']/ev['data']['n_vol'], ev['main']['T_e'][poly_ind]['n_err']/ev['data']['n_vol'])

            entry_t = entry_t[:-2] + '\n'
            entry_n = entry_n[:-2] + '\n'
            if shot['eho_start'] < ev['main']['timestamp'] < shot['eho_stop']:
                res_eho_n += entry_n
                res_eho_t += entry_t
            else:
                if shot['eho_start'] > ev['main']['timestamp']:
                    res_ref_n += entry_n
                    res_ref_t += entry_t
                else:
                    res_post_n += entry_n
                    res_post_t += entry_t

with open('out/res_ref_n.csv', 'w') as file:
    file.write(res_ref_n)
with open('out/res_ref_t.csv', 'w') as file:
    file.write(res_ref_t)
with open('out/res_eho_n.csv', 'w') as file:
    file.write(res_eho_n)
with open('out/res_eho_t.csv', 'w') as file:
    file.write(res_eho_t)
with open('out/res_post_n.csv', 'w') as file:
    file.write(res_post_n)
with open('out/res_post_t.csv', 'w') as file:
    file.write(res_post_t)

print('Code ok')
