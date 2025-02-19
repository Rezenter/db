import json
import msgpack
import copy

saw_filter = 5e-4
max_elm_delay = 2e-4
inter_elm_delay = 5e-4



db = None
#with open('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\index_new.json', 'r') as file:
#    db = json.load(file)
with open('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\index.msgpk', 'rb') as file:
    db = msgpack.unpackb(file.read(), strict_map_key=False)
print('loaded\n\n')

elmy = []
reference = []

for shotn in db:
    shot = db[shotn]
    if 'TS' not in shot or 'time' not in shot['TS'] or not shot['TS']['processed']:
        continue
    if 'err' in shot['SXR']:
        continue
    for t in shot['TS']['time']:

        if not shot['T_flattop_start'] <= t <= (shot['T_flattop_stop'] - 5e-3):
            continue
        for saw in shot['SXR']['time']:
            if abs(saw['time'] - t) <= saw_filter:
                #print('SAW filter: ', t, saw['time'], shotn)
                break
        else:
            for elm in shot['ELM2']:
                if elm['tau'] <= 0:
                    continue
                if 0 <= t - elm['t'] <= max_elm_delay:
                    elmy.append({
                        'shotn': shotn,
                        'time': t
                    })
                elif 2e-5 <= elm['t'] - t <= max_elm_delay:
                    reference.append({
                        'shotn': shotn,
                        'time': t
                    })


print('filtering closest ', len(elmy), len(reference))

closest_arr = []
for elm in elmy:
    closest_ind = None
    for candidate_ind in range(len(reference)):
        if elm['shotn'] != reference[candidate_ind]['shotn']:
            continue
        if closest_ind is None:
            closest_ind = candidate_ind
        elif abs(reference[candidate_ind]['time'] - elm['time']) < abs(reference[closest_ind]['time'] - elm['time']):
            closest_ind = candidate_ind
    if closest_ind is not None:
        closest_arr.append(copy.deepcopy(reference[closest_ind]))
        print(elm['shotn'], elm['time'], reference[closest_ind]['shotn'], reference[closest_ind]['time'])
        del reference[closest_ind]

norm = None
with open('in/normalised.json', 'r') as f:
    norm = json.load(f)

elm_dat = []
ref_dat = []

with open('out/normalised_elmy.csv', 'w') as f:
    for elm in elmy:
        for e in norm:
            if e['R-R_lcfs'] < -5:
                continue
            if (e['shotn']) == elm['shotn'] and elm['time'] - 1e-3 <= e['time'] * 1e-3 <= elm['time'] + 1e-3:
                elm_dat.append(e)
                f.write('%d, %.2f, %.3f, %.3e, %.3e, %d, %.3f, %.3f, %.3f, %.2f, %.3f, %.3f, %d, %.2f, %.2f, %.2f, %.2f, %.2f, %.1f\n'
                           % (e['shotn'],
                              e['time'],
                              e['R-R_lcfs'],
                              e['T_e/<Te>'],
                              e['n_e/<ne>'],
                              e['I_p'],
                              e['B_T'],
                              e['Volume'],
                              e['W_e'],
                              e['l42'],
                              e['<n>l'],
                              e['elong'],
                              e['before sawtooth #'],
                              e['Upl*Ipl'],
                              e['NBI1'],
                              e['NBI2'],
                              e['<Te>'],
                              e['<ne>'],
                              e['R']
                              ))

with open('out/normalised_elm.json', 'w') as f:
    json.dump(elm_dat, f)

with open('out/normalised_ref.csv', 'w') as f:
    for elm in closest_arr:
        for e in norm:
            if e['R-R_lcfs'] < -5:
                continue
            if (e['shotn']) == elm['shotn'] and elm['time'] - 1e-3 <= e['time'] * 1e-3 <= elm['time'] + 1e-3:
                ref_dat.append(e)
                f.write('%d, %.2f, %.3f, %.3e, %.3e, %d, %.3f, %.3f, %.3f, %.2f, %.3f, %.3f, %d, %.2f, %.2f, %.2f, %.2f, %.2f, %.1f\n'
                           % (e['shotn'],
                              e['time'],
                              e['R-R_lcfs'],
                              e['T_e/<Te>'],
                              e['n_e/<ne>'],
                              e['I_p'],
                              e['B_T'],
                              e['Volume'],
                              e['W_e'],
                              e['l42'],
                              e['<n>l'],
                              e['elong'],
                              e['before sawtooth #'],
                              e['Upl*Ipl'],
                              e['NBI1'],
                              e['NBI2'],
                              e['<Te>'],
                              e['<ne>'],
                              e['R']
                              ))

with open('out/normalised_ref.json', 'w') as f:
    json.dump(ref_dat, f)

print('OK')
