import json
from pathlib import Path
import shtRipper

path_DI: str = '//172.16.12.127/Pub/DI/data/'
path_TS: str = '//172.16.12.127/Pub/!!!TS_RESULTS/shots/'
path_sht: str = '//172.16.12.127/Data/'
shotn_from: int = 42700
shotn_to: int = 42768
poly_ind: int = 5

path = Path(path_DI)
if not path.exists():
    print('DI path not found')
    fuck

for filename_DI in path.iterdir():
    if filename_DI.suffix == '.dat':
        shotn: int = int(filename_DI.stem)
        if shotn_from <= shotn <= shotn_to:
            ts_folder = Path('%s%05d/' % (path_TS, shotn))
            if ts_folder.exists():
                ts_data = {}
                with open(Path('%s%05d/result.json' % (path_TS, shotn)), 'r') as ts_file:
                    ts_data = json.load(ts_file)
                di_data = []
                with open(Path(filename_DI), 'r') as di_file:
                    di_file.readline()  # skip header
                    for line in di_file:
                        line_split = line.split()
                        di_data.append({
                            't': float(line_split[0]) * 1e3,
                            'nl': float(line_split[1])
                        })

                with open(Path('%s%05d/cfm_res.json' % (path_TS, shotn)), 'r') as ts_file:
                    ts_data['cfm'] = json.load(ts_file)
                if 'data' not in ts_data['cfm']:
                    continue

                sht_data = shtRipper.ripper.read('%ssht%d.SHT' % (path_sht, shotn), [
                    'Лазер',
                    'ne TS'
                ])

                der_threshold: float = -0.2
                val_threshold: float = -200 * 1e-3
                pulse_length: int = 210
                integrate_points: int = 20
                epsilon: float = 0.00905 * 10

                x: list[float] = sht_data['Лазер']['x']
                y: list[float] = sht_data['Лазер']['y']

                pulses: list[float] = [0]
                pulse_ind: list[int] = [0]
                transitions: list[float] = [0]
                i: int = 0
                while i < len(y) - 1:
                    if y[i + 1] - y[i] < der_threshold and y[i + 5] < val_threshold:
                        pulses.append((x[i] + x[i + 1]) * 0.5 * 1e3)
                        pulse_ind.append(i)

                        val: float = sum(sht_data['ne TS']['y'][i - integrate_points: i + integrate_points])
                        transition_ind: int = i
                        while abs(sum(sht_data['ne TS']['y'][transition_ind - integrate_points: transition_ind + integrate_points]) - val) < epsilon * 2 * integrate_points and transition_ind < len(y) - integrate_points:
                            transition_ind += 1
                        transitions.append(x[transition_ind] * 1e3)

                        i += pulse_length
                    i += 1
                if len(pulses) != len(ts_data['events']):
                    print(len(pulses), len(ts_data['events']))
                    fuck

                for event in ts_data['cfm']['data']:
                    if 'timestamp' not in ts_data['events'][event['event_index']]:
                        continue
                    line = '%05d %.1f ' % (shotn, ts_data['events'][event['event_index']]['timestamp'])
                    line += '%.2e %.2e ' % (event['data']['nl_eq']*2, event['data']['nl_eq_err']*2)
                    di_ind = 0
                    while di_data[di_ind]['t'] < ts_data['events'][event['event_index']]['timestamp']:
                        di_ind += 1
                    line += '%.2e ' % (di_data[di_ind]['nl'])
                    if 'n' in ts_data['events'][event['event_index']]['T_e'][poly_ind]:
                        line += '%.2e %.2e ' % (ts_data['events'][event['event_index']]['T_e'][poly_ind]['n'], ts_data['events'][event['event_index']]['T_e'][poly_ind]['n_err'])
                    else:
                        continue
                    line += '%.2e ' % (ts_data['header']['RT']['neMeas'][event['event_index']])
                    if not 1.5 <= transitions[event['event_index']] - pulses[event['event_index']] <= 2.4:
                        line += '--'
                    else:
                        line += '%.3f' % (transitions[event['event_index']] - pulses[event['event_index']] - 0.006)
                    print(line)
print('Code OK')
