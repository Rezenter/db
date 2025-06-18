import json
import msgpack
import copy

saw_filter = 5e-4
max_elm_delay = 2e-4
#max_elm_delay = 2e-3



db = None
#with open('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\index_new.json', 'r') as file:
#    db = json.load(file)
with open('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\index_test.msgpk', 'rb') as file:
    db = msgpack.unpackb(file.read(), strict_map_key=False)
print('loaded')

elmy = []

before = 0
after = 0

for shotn in db:
    shot = db[shotn]
    if 'TS' not in shot or 'time' not in shot['TS'] or not shot['TS']['processed']:
        continue
    if 'err' in shot['SXR']:
        continue
    for elm_i in range(1, len(shot['ELM2']) - 1):
        elm = shot['ELM2'][elm_i]
        if not shot['T_flattop_start'] <= shot['ELM2'][elm_i]['t'] <= (shot['T_flattop_stop'] - 5e-3):
            continue
        if elm['tau'] <= 0:
            continue
        if elm['level'] >= 1.2:
            continue
        if elm['max'] - elm['level'] <= 0.09:
            continue
        for saw in shot['SXR']['time']:
            if abs(saw['time'] - shot['ELM2'][elm_i]['t']) <= saw_filter:
                #print('SAW filter: ', shot['ELM2'][elm_i]['t'], saw['time'], shotn)
                break
        else:
            t_from = max((shot['ELM2'][elm_i - 1]['t'] + shot['ELM2'][elm_i]['t']) * 0.5, shot['ELM2'][elm_i]['t'] - max_elm_delay)
            t_to = min((shot['ELM2'][elm_i]['t'] + shot['ELM2'][elm_i + 1]['t']) * 0.5, shot['ELM2'][elm_i]['t'] + max_elm_delay)

            for t in shot['TS']['time']:
                if t_from <= t <= t_to:
                    if not -0.02 < (t - elm['t'])*1e3 < 0.2: #filter close to elms
                        #print(t - elm['t'])
                        continue
                    if t <= (t_from + t_to)*0.5:
                        before += 1
                    else:
                        after += 1
                    elmy.append({
                        'shotn': shotn,
                        'time': t,
                        'delay': t - elm['t'],
                        'level': elm['level'],
                        'max': elm['max']
                    })

print('counters: ', before, after)

norm = None
with open('in/normalised.json', 'r') as f:
    norm = json.load(f)
print('loaded')

elm_dat = []

count = 0
with open('out/normalised_not_elmy.csv', 'w') as f:
    for elm in elmy:
        if count % 100 == 0:
            print('%d' % (100 * count/len(elmy)))
        count += 1
        for e in norm:
            if e['R-R_lcfs'] < -5:
                continue

            if e['NBI1'] + e['NBI2'] < 100:
                pass
                #continue

            if not e['<Te>'] - 100 <= 283 <= e['<Te>'] + 100:
                pass
                #continue

            if not e['<ne>'] - 1 <= 4.9 <= e['<ne>'] + 1:
                pass
                #continue

            if (e['shotn']) == elm['shotn'] and elm['time'] - 1e-3 <= e['time'] * 1e-3 <= elm['time'] + 1e-3:
                elm_dat.append(e)
                f.write('%d, %.2f, %.3f, %.3e, %.3e, %d, %.3f, %.3f, %.3f, %.2f, %.3f, %.3f, %d, %.2f, %.2f, %.2f, %.2f, %.2f, %.1f, %.3f, %.3f, %.3f\n'
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
                              e['R'],
                              elm['delay']*1e3,
                              elm['level'],
                              elm['max']
                              ))

print(len(elm_dat))

with open('out/normalised_elm.json', 'w') as f:
    json.dump(elm_dat, f)


print('OK')
