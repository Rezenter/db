from pathlib import Path

R_norm = 490

req = []
with open('out/filtered.csv', 'r') as file:
    header = [v.strip() for v in file.readline().split(',')]
    shotn_ind = header.index('shotn')
    time_ind = header.index('time')
    for line in file:
        spl = line.split(',')
        req.append({
            'shotn': int(spl[shotn_ind]),
            'ind': int(spl[-1]),
            #'time': float(spl[time_ind]),
            'delay': float(spl[-2]),
            'amp': float(spl[-5]),
            'line': line[:-1],
            'period': float(spl[-7])
        })
        req.append({
            'shotn': int(spl[shotn_ind]),
            'ind': int(spl[-3]),
            # 'time': float(spl[time_ind]),
            'delay': float(spl[-4]),
            'amp': float(spl[-6]),
            'line': line[:-1]
        })

#req.sort(key=lambda x: x['delay'])
for t in req:
    if 'time' not in t:
        filename: Path = Path(
            '\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\%05d\\%05d_dynamics.csv' % (t['shotn'], t['shotn']))
        if not filename.exists():
            continue
        with open(filename, 'r') as ts_file:
            header = [v.strip() for v in ts_file.readline().split(',')]
            norm_ind = header.index('<T>V')
            ts_file.readline()
            for line in ts_file:
                spl = line.split(',')
                if t['ind'] + 1 == int(spl[0]):
                    t['time'] = float(spl[1])
                    if spl[norm_ind].strip() == '--':
                        t['norm'] = 1e35
                    else:
                        #t['norm'] = float(spl[norm_ind])
                        t['norm'] = 1
                    break
            else:
                fuck
    filename: Path = Path(
        '\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\%05d\\%05d_T(R).csv' % (t['shotn'], t['shotn']))
    if not filename.exists():
        continue
    with open(filename, 'r') as ts_file:
        head = [v.strip() for v in ts_file.readline().split(',')]


        data_ind = head.index('%.1f' % t['time'])
        t['R'] = []
        t['P'] = []
        ts_file.readline()
        for line in ts_file:
            spl = line.split(',')
            t['R'].append(float(spl[0]))
            if spl[data_ind].strip() == '--':
                t['P'].append(spl[data_ind])
            else:
                t['P'].append(float(spl[data_ind])/t['norm'])

    closest_ind = 0
    for r_ind in range(len(t['R'])):
        if abs(float(t['R'][r_ind]) - R_norm) < abs(float(t['R'][closest_ind]) - R_norm):
            closest_ind = r_ind
    t['r_ind'] = closest_ind
    #val = float(t['P'][closest_ind])
    #print(t['delay'], (float(t['P'][closest_ind-1]) - float(t['P'][closest_ind+1]))/(float(t['R'][closest_ind-1]) - float(t['R'][closest_ind+1])), t['shotn'], t['time'])
    #for i in range(len(t['P'])):
        #if t['P'][i] != ' --':
        #    t['P'][i] = float(t['P'][i]) / val

with open('out/filtered_profiles.csv', 'w') as file:
    line = ''
    for r in req:
        line += 'R, %s %s %s P_e, ' % (r['shotn'], r['time'], r['delay'])
    file.write(line[:-2] + '\n')
    flag = True
    c = 0
    while flag:
        flag = False
        line = ''
        for r in req:
            if 'R' in r and len(r['R']) > c:
                flag = True
                line += '%s, %s, ' % (r['R'][c], r['P'][c])
            else:
                line += '%s, %s, ' % ('--', '--')
        if flag:
            file.write(line[:-2] + '\n')
            c += 1

for line_ind in range(0, len(req), 2):
    for r_ind in range(len(req[line_ind]['R']) - 2, -1, -1):
        if req[line_ind]['R'][r_ind] > 580:
            break
        if req[line_ind]['R'][r_ind + 1] < 400:
            continue
        if not type(req[line_ind]['P'][r_ind]) == type(0.1):
            break
        #print(req[line_ind]['P'][r_ind], req[line_ind + 1]['P'][r_ind], req[line_ind]['P'][r_ind + 1], req[line_ind + 1]['P'][r_ind + 1])
        if (req[line_ind]['P'][r_ind] - req[line_ind + 1]['P'][r_ind]) * (req[line_ind]['P'][r_ind + 1] - req[line_ind + 1]['P'][r_ind + 1]) < 0:
            r_inv = req[line_ind]['R'][r_ind] + (abs(req[line_ind]['P'][r_ind] - req[line_ind + 1]['P'][r_ind]) * (req[line_ind]['R'][r_ind + 1] - req[line_ind]['R'][r_ind])) / (abs(req[line_ind]['P'][r_ind] - req[line_ind + 1]['P'][r_ind]) + abs(req[line_ind]['P'][r_ind + 1] - req[line_ind + 1]['P'][r_ind + 1]))

            if r_inv < 400:
                print(req[line_ind]['R'])
                fuck

            print(req[line_ind]['line'].replace(',', ''), req[line_ind]['R'][r_ind], r_inv, req[line_ind]['R'][r_ind + 1], (req[line_ind]['amp'] + req[line_ind]['amp'])/2)
            break

print('Code OK')