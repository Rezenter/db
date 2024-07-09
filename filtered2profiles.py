import json
from pathlib import Path
import utils.stored_energy as ccm_energy
import phys_const

R_norm = 490

req = []
with open('out/filtered.csv', 'r') as file:
    header = [v.strip() for v in file.readline().split(',')]
    shotn_ind = header.index('shotn')
    time_ind = header.index('time')
    for line in file:
        spl = line.split(',')
        #print(spl[1])
        if float(spl[-3]) > 0:
            req.append({
                'shotn': int(spl[shotn_ind]),
                'time': spl[-4].strip(),
                'delay': float(spl[-3]),
                'amp': float(spl[-2]),
                'line': line[:-1],
                'period': float(spl[-1])
            })
            req.append({
                'shotn': int(spl[shotn_ind]),
                'time': spl[-8].strip(),
                'delay': float(spl[-7]),
                'amp': float(spl[-6]),
                'line': line[:-1]
            })
        else:
            req.append({
                'shotn': int(spl[shotn_ind]),
                'time': spl[-8].strip(),
                'delay': float(spl[-7]),
                'amp': float(spl[-6]),
                'line': line[:-1]
            })
            req.append({
                'shotn': int(spl[shotn_ind]),
                'time': spl[-4].strip(),
                'delay': float(spl[-3]),
                'amp': float(spl[-2]),
                'line': line[:-1],
                'period': float(spl[-1])
            })
#req.sort(key=lambda x: x['delay'])
for t in req:
    #print('loading ', t['shotn'])
    filename: Path = Path(
        '\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\%05d\\%05d_dynamics.csv' % (t['shotn'], t['shotn']))
    if not filename.exists():
        continue
    with open(filename, 'r') as ts_file:
        header = [v.strip() for v in ts_file.readline().split(',')]
        norm_ind = header.index('<T>V')
        if 'T_max_measured' in header:
            T_max_measured = header.index('T_max_measured')
            n_max_measured = header.index('n_max_measured')
        else:
            T_max_measured = header.index('T_center')
            n_max_measured = header.index('n_center')
        TavV = header.index('<T>V')
        navV = header.index('<n>V')
        We = header.index('We')
        ind_ind = header.index('index')

        ts_file.readline()

        for line in ts_file:
            spl = line.split(',')
            if t['time'] == spl[1].strip():
                t['T_max_measured'] = spl[T_max_measured]
                t['n_max_measured'] = spl[n_max_measured]
                t['TavV'] = spl[TavV]
                t['navV'] = spl[navV]
                t['We'] = spl[We]
                t['dynamics_ind'] = int(spl[ind_ind])
                #t['time'] = float(spl[1])
                #print(t['time'])
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


        data_ind = head.index(t['time'])
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
    '''
    cfm = {}
    with open('\\\\172.16.12.127\\Pub\\!!!CURRENT_COIL_METHOD\\V3_zad7_mcc\\mcc_%05d.json' % t['shotn'], 'r') as f:
        cfm = json.load(f)
    ind = 0
    m = 9999
    for i, tarr in enumerate(cfm['time']['variable']):
        if abs(float(t['time']) - tarr*1000) < m:
            ind = i
            m = abs(float(t['time']) - tarr*1000)
    if m == 9999:
        fuck
        
    if 'q' not in cfm:
        t['q95'] = 0
    else:
        t['q95'] = cfm['q']['variable'][ind]
        '''
    t['q95'] = 0

    #print(t['q95'], float(t['time']), cfm['time']['variable'][ind]*1000)

    filename: Path = Path(
        '\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\%05d\\result.json' % t['shotn'])
    if filename.exists():
        with open(filename, 'r') as ts_file:
            t['ts_res'] = json.load(ts_file)


print('loaded')

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
    #print(req[line_ind]['shotn'])
    for r_ind in range(len(req[line_ind]['R']) - 2, -1, -1):
        if req[line_ind]['R'][r_ind] > 560:
            #print('R > 560')
            break
        if req[line_ind]['R'][r_ind + 1] < 400:
            continue
        if not type(req[line_ind]['P'][r_ind]) == type(0.1) or not type(req[line_ind + 1]['P'][r_ind + 1]) == type(0.1):
            continue
        #print(req[line_ind]['P'][r_ind], req[line_ind + 1]['P'][r_ind], req[line_ind]['P'][r_ind + 1], req[line_ind + 1]['P'][r_ind + 1])

        #require not only cross, but correct direction

        if req[line_ind]['P'][r_ind + 1] < req[line_ind + 1]['P'][r_ind + 1] and \
                req[line_ind]['P'][r_ind] > req[line_ind + 1]['P'][r_ind]:
            r_inv = req[line_ind]['R'][r_ind] + (abs(req[line_ind]['P'][r_ind] - req[line_ind + 1]['P'][r_ind]) * (req[line_ind]['R'][r_ind + 1] - req[line_ind]['R'][r_ind])) / (abs(req[line_ind]['P'][r_ind] - req[line_ind + 1]['P'][r_ind]) + abs(req[line_ind]['P'][r_ind + 1] - req[line_ind + 1]['P'][r_ind + 1]))

            if r_inv < 400:
                print(req[line_ind]['R'])
                fuck

            if 'ts_res' in req[line_ind]:
                #integrate inside R_inv
                for j in range(line_ind, line_ind + 2):
                    new_ind = 9999
                    for poly_ind in range(len(req[j]['ts_res']['config']['poly']) - 1):
                        if req[j]['ts_res']['config']['poly'][poly_ind]['R'] >= r_inv > req[j]['ts_res']['config']['poly'][poly_ind + 1]['R']:
                            new_ind = poly_ind + 1
                            #print(req[j]['ts_res']['config']['poly'][poly_ind]['R'], r_inv, req[j]['ts_res']['config']['poly'][poly_ind + 1]['R'])
                            req[j]['ts_res']['config']['poly'].insert(poly_ind + 1, {
                                'R': r_inv,
                                'ind': poly_ind + 1
                            })
                            flag = True
                            #poly_ind = prev, +1 = r_inv, +2 = next
                            for e in req[j]['ts_res']['events']:
                                if 'timestamp' in e and e['timestamp'] - 0.3 <= float(req[j]['time']) < e['timestamp'] + 0.3:
                                    #print(e['timestamp'], req[j]['time'])
                                    e['T_e'].insert(poly_ind + 1, {
                                        'T': phys_const.interpolate(x_prev=req[j]['ts_res']['config']['poly'][poly_ind]['R'], x_next=req[j]['ts_res']['config']['poly'][poly_ind+2]['R'], x_tgt=req[j]['ts_res']['config']['poly'][poly_ind+1]['R'],
                                                                    y_prev=e['T_e'][poly_ind]['T'], y_next=e['T_e'][poly_ind+1]['T']),
                                        'Terr': max(e['T_e'][poly_ind]['Terr'], e['T_e'][poly_ind+1]['Terr']),
                                        'n': phys_const.interpolate(x_prev=req[j]['ts_res']['config']['poly'][poly_ind]['R'], x_next=req[j]['ts_res']['config']['poly'][poly_ind+2]['R'], x_tgt=req[j]['ts_res']['config']['poly'][poly_ind+1]['R'],
                                                                    y_prev=e['T_e'][poly_ind]['n'], y_next=e['T_e'][poly_ind+1]['n']),
                                        'n_err': max(e['T_e'][poly_ind]['n_err'], e['T_e'][poly_ind+1]['n_err']),
                                        'error': None
                                    })
                                    for i in range(poly_ind + 1):
                                        e['T_e'][i] = {
                                            'T': 0,
                                            'Terr': 0,
                                            'n': 0,
                                            'n_err': 0,
                                            'error': None
                                        }
                                    break
                            break

                    for poly_ind in range(new_ind + 1, len(req[j]['ts_res']['config']['poly'])):
                        req[j]['ts_res']['config']['poly'][poly_ind]['ind'] = poly_ind

                    stored_calc = ccm_energy.StoredCalculator(req[j]['shotn'], req[j]['ts_res'])
                    req[j]['cfm'] = stored_calc.calc_dynamics(float(req[j]['time']) - 0.5, float(req[j]['time']) + 0.5)['data'][0]['data']
            else:
                for j in range(line_ind, line_ind + 2):
                    req[j]['cfm'] = {
                        'vol_w': -9999
                    }
            print(req[line_ind]['line'].replace(',', ''), r_inv, (req[line_ind]['amp'] + req[line_ind+1]['amp'])/2, req[line_ind]['T_max_measured'], req[line_ind]['n_max_measured'], req[line_ind]['TavV'], req[line_ind]['navV'], req[line_ind]['We'], req[line_ind + 1]['T_max_measured'], req[line_ind + 1]['n_max_measured'], req[line_ind + 1]['TavV'], req[line_ind + 1]['navV'], req[line_ind + 1]['We'], req[line_ind]['q95'], req[line_ind+1]['cfm']['vol_w'], req[line_ind]['cfm']['vol_w'], req[line_ind+1]['cfm']['vol_w'] - req[line_ind]['cfm']['vol_w'], (req[line_ind+1]['cfm']['vol_w'] - req[line_ind]['cfm']['vol_w']) * 100 / req[line_ind+1]['cfm']['vol_w'])
            break

print('Code OK')