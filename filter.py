import json
from pathlib import Path

ts_path: Path = Path('//172.16.12.127/Pub/!!!TS_RESULTS/shots/')

request_TS = {
    'filter': True,
    'R_center': 41,
    'eps': 2.5
}

request_ELM = {
    'filter': False,
    'is present': True,
    'maxAbsDelay': 0.03*1e-3
}
request_NBI1 = {
    'filter': False,
    'is present': True,
    'duration_min': 0,
    'duration_max': 60
}
request_NBI2 = {
    'filter': False,
    'is present': True,
    'duration_min': 0,
    'duration_max': 300,
    'U_min': 0,
    'U_max': 100
}

limit_Bt = {
    'filter': False,
    'min': 0.8,
    'max': 0.83
}
limit_Ip = {
    'filter': False,
    'min': 295,
    'max': 305
}
limit_flattop = {
    'filter': False,
    'min': 20,
    'max': 300
}
limit_SXR = {
    'filter': False,
    'max_delay': 1.5*1e-3,
}
limit_rinv = {
    'filter': False,
    'min_delay': 0.1*1e-3,
    'max_delay': 0.35*1e-3,
    'min_amp': 0.05,
    'skip_first': 3
}
limit_maxTe = {
    'filter': False,
    'min': 1600,
    'max': 2000
}
limit_nl = {
    'filter': False,
    'min': 5.5e19,
    'max': 5.5e19
}

baddies: list[int] = [41845]

with open('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\index.json', 'r') as file:
    db = json.load(file)


out: list[str] = ['shotn, Ip, Bt, flattop duration, time, <n>42, err, we, err, T0, err\n']
elmy_out: list[str] = []

for shot_str in db:
    shot = db[shot_str]
    if shot['shotn'] in baddies:
        continue

    if 'err' in shot:
        continue
    if request_TS['filter'] and 'err' in shot['TS']:
        continue

    if request_NBI1['filter']:
        request_NBI1['pass_filter'] = False
        if 'err' not in shot['NBI1']:
            if request_NBI1['duration_min'] <= (shot['NBI1']['T_stop'] - shot['NBI1']['T_start']) * 1000 <= \
                   request_NBI1['duration_max']:
                request_NBI1['pass_filter'] = True

    if request_NBI2['filter']:
        request_NBI2['pass_filter'] = False
        if 'err' not in shot['NBI2']:
            if 'U_max' not in shot['NBI2'] or not request_NBI2['U_min'] <= shot['NBI2']['U_max'] <= request_NBI2['U_max']:
                continue
            if request_NBI2['duration_min'] <= (shot['NBI2']['T_stop'] - shot['NBI2']['T_start']) * 1000 <= \
                    request_NBI2['duration_max']:
                request_NBI2['pass_filter'] = True

    #if not (request_NBI1['pass_filter'] or request_NBI2['pass_filter']):
    #    continue

    if limit_Bt['filter']:
        if not limit_Bt['min'] <= shot['Bt'] <= limit_Bt['max']:
            continue

    if limit_Ip['filter']:
        if not limit_Ip['min'] <= shot['Ip'] <= limit_Ip['max']:
            continue

    if limit_flattop['filter']:
        if not limit_flattop['min'] <= (shot["T_flattop_stop"] - shot["T_flattop_start"]) * 1000 <= limit_flattop['max']:
            continue

    if limit_SXR['filter']:
        for event in shot['SXR']['time']:
            if -limit_SXR['max_delay'] < event['las_delay'] < limit_SXR['max_delay']:
                #print(event['las_delay'])
                break
        else:
            #print('no close SXR events')
            continue

    flattop: float = (shot["T_flattop_stop"] - shot["T_flattop_start"]) * 1000
    #print('%d %d %.3f %d' % (shot['shotn'], shot['Ip'], shot['Bt'], flattop))
    #print('%d %.3f' % (shot['Ip'], shot['Bt']))
    out_line: str = '%d, %d, %.3f, %d, ' % (shot['shotn'], shot['Ip'], shot['Bt'], flattop)


    if request_ELM['filter']:
        if request_ELM['is present'] != (len(shot['ELM']) != 0):
            continue
        for elm in shot['ELM']:
            if elm == 'err':
                continue
            if abs(elm['las_delay']) < request_ELM['maxAbsDelay']:
                elmy_out.append('%s %.3f %.5f\n' % (shot_str, elm['time']*1e3, elm['las_delay']*1e3))
                print(shot_str, elm['time']*1e3, elm['las_delay']*1e3)

    ts_data = []
    shot_path: Path = ts_path.joinpath('%s/%s_dynamics.csv' % (shot_str, shot_str))
    if not shot_path.exists():
        #print('CALC TS %s' % shot_str)
        continue
    time_ind: int = -999
    nl42_ind: int = -999
    nl42err_ind: int = -999
    We_ind: int = -999
    Weerr_ind: int = -999
    TMax_ind: int = -999
    TMaxerr_ind: int = -999
    T_max: float = -999
    nl_flattop_min: float = 1e99
    nl_flattop_max: float = -1e99
    with open(shot_path, 'r') as file:
        header = [v.strip() for v in file.readline().split(',')]
        if len(header) == 1:
            #print('RECALC TS %s' % shot_str)
            continue
        time_ind = header.index('time')
        if '<n>42' not in header:
            #print('RECALC TS %s' % shot_str)
            continue
        nl42_ind = header.index('<n>42')
        if '<n>42_err' not in header:
            continue
        nl42err_ind = header.index('<n>42_err')
        We_ind = header.index('We')
        Weerr_ind = header.index('We_err')

        file.readline()
        for line in file:
            spl = [v.strip() for v in line.split(',')]
            ts_data.append(spl)
            if shot['T_flattop_start'] <= float(spl[time_ind])*0.001 <= shot['T_flattop_stop']:
                if spl[nl42_ind] != '--' and spl[nl42_ind] != '':
                    nl_flattop_min = min(nl_flattop_min, float(spl[nl42_ind]))
                    nl_flattop_max = max(nl_flattop_max, float(spl[nl42_ind]))

        if 'T_max_measured' in header:
            TMax_ind = header.index('T_max_measured')
            TMaxerr_ind = header.index('T_max_err')
        else:
            tt_path: Path = ts_path.joinpath('%s/%s_T(t).csv' % (shot_str, shot_str))
            if not tt_path.exists():
                #print('RECALC TS %s' % shot_str)
                continue
            TMax_ind = len(header)
            TMaxerr_ind = len(header) + 1
            tt_data: list[list[str]] = []
            with open(tt_path, 'r') as tt_file:
                tt_header = [v.strip() for v in tt_file.readline().split(',')]
                selected_ind: list[int] = []
                for i in range(1, len(tt_header), 2):
                    r: float = float(tt_header[i]) * 0.1
                    if r - request_TS['eps'] <= request_TS['R_center'] <= r + request_TS['eps']:
                        selected_ind.append(i)
                tt_file.readline()
                event_ind: int = 0
                for line in tt_file:
                    spl = [v.strip() for v in line.split(',')]
                    te: float = 0
                    terr: float = 0
                    count: int = 0
                    for i in selected_ind:
                        try:
                            te += float(spl[i])
                            terr += float(spl[i + 1])
                            count += 1
                        except ValueError:
                            continue
                    if event_ind > len(ts_data) - 1:
                        continue
                    if ts_data[event_ind][1] != spl[0]:
                        continue
                    if count != 0:
                        ts_data[event_ind].append('%.1f' % (te / count))
                        ts_data[event_ind].append('%.1f' % (terr / count))
                    else:
                        ts_data[event_ind].append('--')
                        ts_data[event_ind].append('--')
                    event_ind += 1

    if len(ts_data) == 0 or len(ts_data[0]) < 7:
        #print('RECALC TS %s' % shot_str)
        continue
    #print(shot_str, 'OK')

    if limit_maxTe['filter']:
        ok: bool = False
        if not Path(ts_path.joinpath('%s/result.json' % shot_str)).exists():
            continue
        with open(ts_path.joinpath('%s/result.json' % shot_str), 'r') as ts_file:
            ts_res = json.load(ts_file)
            shot['TS_res'] = ts_res
            for ev in ts_res['events']:
                if not 'timestamp' in ev:
                    continue
                if not shot['T_start'] <= ev['timestamp']*0.001 <= shot['T_flattop_stop']:
                    continue
                if 'T_e' in ev:
                    for p in ev['T_e']:
                        if 'T' not in p:
                            continue
                        if p['error'] is not None:
                            continue
                        if 'hidden' in p and p['hidden']:
                            continue

                        if limit_maxTe['min'] <= p['T'] <= limit_maxTe['max']:
                            #print(ev[TMax_ind])
                            if p['T'] > 1900:
                                print('wtf')

                            ok = True
                            T_max = max(p['T'], T_max)
        if not ok:
            continue

    if limit_nl['filter']:
        if limit_nl['min'] > nl_flattop_max or limit_nl['max'] < nl_flattop_min:
            continue

    #print(shot['shotn'], 1, shot['Ip'], shot['Bt'], int('err' not in shot['NBI1']), int('err' not in shot['NBI2']), T_max, shot['TS_res']['spectral_name'])
    print(shot['shotn'], 1, shot['Ip'], shot['Bt'], int('err' not in shot['NBI1']), int('err' not in shot['NBI2']), int('err' not in shot['NBI1']) + int('err' not in shot['NBI2']),  nl_flattop_min, nl_flattop_max)
    for las_ind in range(len(ts_data)):
        event = ts_data[las_ind]
        if shot["T_flattop_start"] * 1000 + 10 < float(event[time_ind]) < shot["T_flattop_stop"] * 1000:
            if 'T_start' in shot['NBI1']:
                if not (shot['NBI1']["T_start"] * 1000 + 10 < float(event[time_ind]) < shot['NBI1']["T_stop"] * 1000):
                    continue
            if 'T_start' in shot['NBI2']:
                if not (shot['NBI2']["T_start"] * 1000 + 10 < float(event[time_ind]) < shot['NBI2']["T_stop"] * 1000):
                    continue

            if limit_SXR['filter']:
                for ev in shot['SXR']['time']:
                    if ev['laser_ind'] + 1 != int(event[0]):
                        continue
                    #print(event[0], event[1], ev['laser_ind'], ev['time'])
                    if -limit_SXR['max_delay'] < ev['las_delay'] < limit_SXR['max_delay']:
                        final_line: str = out_line
                        final_line += '%s, ' % event[time_ind]
                        final_line += '%s, ' % event[nl42_ind]
                        final_line += '%s, ' % event[nl42err_ind]
                        final_line += '%s, ' % event[We_ind]
                        final_line += '%s, ' % event[Weerr_ind]
                        final_line += '%s, ' % event[TMax_ind]
                        final_line += '%s, ' % event[TMaxerr_ind]
                        final_line += '%2e\n' % (ev['las_delay']*1000)

                        out.append(final_line)
                    break

            if limit_rinv['filter']:
                if las_ind < len(ts_data) - 2:

                    las_pulse_ind = int(event[0]) - 1

                    sxr_ind_1: int = 99999
                    sxr_ind_2: int = 99999
                    for sxr_ind in range(1 + limit_rinv['skip_first'], len(shot['SXR']['time'])):
                        if float(event[1]) - 0.5 <= shot['SXR']['time'][sxr_ind]['laser_time'] * 1000 <= float(event[1]) + 0.5:
                            sxr_ind_1 = sxr_ind
                            break
                    if sxr_ind_1 == 99999:
                        continue
                    for sxr_ind in range(1 + limit_rinv['skip_first'], len(shot['SXR']['time'])):
                        if float(ts_data[las_ind + 1][1]) - 0.5 <= shot['SXR']['time'][sxr_ind]['laser_time'] * 1000 <= float(ts_data[las_ind + 1][1]) + 0.5:
                            sxr_ind_2 = sxr_ind
                            break
                    if sxr_ind_2 == 99999:
                        continue
                    if (not -limit_rinv['min_delay'] < shot['SXR']['time'][sxr_ind_1]['las_delay'] < limit_rinv['min_delay'] and \
                            -limit_rinv['max_delay'] < shot['SXR']['time'][sxr_ind_1]['las_delay'] < limit_rinv['max_delay'] and \
                            not -limit_rinv['min_delay'] < shot['SXR']['time'][sxr_ind_2]['las_delay'] < limit_rinv['min_delay'] and \
                            -limit_rinv['max_delay'] < shot['SXR']['time'][sxr_ind_2]['las_delay'] < limit_rinv['max_delay'] and \
                            shot['SXR']['time'][sxr_ind_1]['las_delay'] * shot['SXR']['time'][sxr_ind_2]['las_delay'] < 0):

                        if shot['SXR']['time'][sxr_ind_1]['amp'] < limit_rinv['min_amp'] or shot['SXR']['time'][sxr_ind_2]['amp'] < limit_rinv['min_amp']:
                            continue

                        final_line: str = out_line
                        final_line += '%s, ' % event[time_ind]
                        final_line += '%s, ' % event[nl42_ind]
                        final_line += '%s, ' % event[nl42err_ind]
                        final_line += '%s, ' % event[We_ind]
                        final_line += '%s, ' % event[Weerr_ind]
                        final_line += '%s, ' % event[TMax_ind]
                        final_line += '%s, ' % event[TMaxerr_ind]
                        final_line += '%f, ' % (shot['SXR']['time'][sxr_ind_1]['time'])
                        final_line += '%f, ' % (shot['SXR']['time'][sxr_ind_2]['time'])
                        final_line += '%f, ' % (shot['SXR']['time'][sxr_ind_1]['laser_time'])
                        final_line += '%f, ' % (shot['SXR']['time'][sxr_ind_2]['laser_time'])

                        final_line += '%s, ' % (ts_data[las_ind][1].strip())
                        final_line += '%2e, ' % (shot['SXR']['time'][sxr_ind_1]['las_delay'] * 1000)
                        final_line += '%2f, ' % (shot['SXR']['time'][sxr_ind_1]['amp'])
                        final_line += '%2f, ' % (shot['SXR']['time'][sxr_ind_1]['period'] * 1000)

                        final_line += '%s, ' % (ts_data[las_ind + 1][1].strip())
                        final_line += '%2e, ' % (shot['SXR']['time'][sxr_ind_2]['las_delay'] * 1000)
                        final_line += '%2f, ' % (shot['SXR']['time'][sxr_ind_2]['amp'])
                        final_line += '%2f\n' % (shot['SXR']['time'][sxr_ind_2]['period'] * 1000)

                        out.append(final_line)


with open('out/filtered.csv', 'w') as file:
    file.writelines(out)

with open('out/elmy_out.csv', 'w') as file:
    file.writelines(elmy_out)

print('Code OK')
