import shtRipper
import json

shotn = 44194
shotn = 42667
shotn = 45972
shotn = 45514
signal_name = 'D-alfa  хорда R=50 cm'

der_window = 9
half_window: int = der_window // 2

der_threshold = 0.005
min_tau = 3e-5
max_tau = 4e-4

print(shotn, '\n\n')
shot = None
with open('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\index.json', 'r') as file:
    shot = json.load(file)['%d' % shotn]


sht = shtRipper.ripper.read('\\\\172.16.12.127\\Data\\sht%05d.sht' % shotn)[signal_name]['y']

signal = []

for i in range(len(sht)):
    signal.append({
        'x': i * 1e-6,
        'y': sht[i],
        'ave': sum(sht[i - half_window: i + half_window]) / der_window
    })
for i in range(der_window + 1, len(sht) - der_window):
    signal[i]['der'] = (signal[i + half_window]['ave'] - signal[i - half_window]['ave']) / der_window
    signal[i]['is_der'] = signal[i]['der'] >= der_threshold
is_der = False
is_peak = False
is_min = False
der_max = 0
der_ind = 0
level = 0
max_level = -1e30
min_level = 1e30
candidates = []
for i in range(der_window + 1, len(sht) - der_window - 1):
    if signal[i]['is_der']:
        is_der = True
        if signal[i]['der'] > der_max:
            der_max = signal[i]['der']
            der_ind = i
            level = signal[der_ind]['ave']
            max_level = signal[der_ind]['ave']
    elif is_der:
        is_der = False
        is_peak = True
    if is_peak:
        if signal[i]['ave'] >= level:
            max_level = max(max_level, signal[i]['ave'])
        else:
            is_peak = False
            is_min = True
    if is_min:
        if signal[i]['der'] < 0:
            min_level = min(min_level, signal[i]['ave'])
        else:
            is_min = False
            der_max = -1e33
            if der_ind > 115000 and max_level - min_level > 0:
                candidates.append({
                    'ind': der_ind,
                    'tau_mks': (i - der_ind),
                    'is_elm': min_tau <= (i - der_ind) * 1e-6 <= max_tau,
                    'level': level,
                    'max': max_level,
                    'der': signal[der_ind]['der'],
                    'too_long': (i - der_ind) * 1e-6 >= max_tau - 0.5e-6,
                    'amp': max_level - min_level,
                    'amp_%': (max_level - min_level) * 100 / max_level
                })


with open('out/elm_test.csv', 'w') as file:
    for i in range(len(sht)):
        if not shot['T_start'] < i * 1e-6 < shot['T_stop']:
            continue
        line = '%.5e, %.4e, %.4e, %.4e\n' % (signal[i]['x'], signal[i]['y'], signal[i]['ave'], signal[i]['der'])
        file.write(line)

for elm in candidates:
    print(elm['ind'] * 1e-6, elm['tau_mks'], int(elm['is_elm']), elm['level'], elm['max'], elm['der'], int(elm['too_long']), elm['amp'], elm['amp_%'])

print('\n\nOK')
