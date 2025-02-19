import shtRipper
import json
import msgpack

shotn = 44194
shotn = 42667
shotn = 45972
shotn = 45514
shotn = 42764
shotn = 44199
signal_name = 'D-alfa  хорда R=50 cm'

der_window = 300
half_window: int = der_window // 2

der_threshold = 3e-6

min_tau = 50
max_tau = 500

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
    signal[i]['der'] = (signal[i + 1]['ave'] - signal[i - 1]['ave']) / der_window
for i in range(der_window*2 + 1, len(sht) - der_window*2):
    signal[i]['der_ave'] = sum([signal[v]['der'] for v in range(i - half_window, i + half_window)]) / der_window

candidates = []
i = 115000
while i < len(sht) - der_window * 3 - max_tau:
    if signal[i]['der_ave'] >= der_threshold:
        max_ind = i
        min_ind = i
        for j in range(i+min_tau, i + max_tau):
            if signal[j]['der_ave'] > signal[max_ind]['der_ave']:
                max_ind = j
            elif signal[j]['der_ave'] < signal[min_ind]['der_ave']:
                min_ind = j
        if signal[min_ind]['der_ave'] < -der_threshold:
            candidates.append({
                't': max_ind*1e-6,
                'tau': (min_ind - max_ind),
                'der': signal[max_ind]['der_ave']
            })
            i += max_tau
    i += min_tau

with open('out/elm_test.csv', 'w') as file:
    for i in range(len(sht)):
        if not shot['T_start'] < i * 1e-6 < shot['T_stop']:
            continue
        line = '%.5e, %.4e, %.4e, %.4e, %.4e\n' % (signal[i]['x'], signal[i]['y'], signal[i]['ave'], signal[i]['der'], signal[i]['der_ave'])
        file.write(line)

for elm in candidates:
    print(elm['t'], elm['tau'], elm['der'])

print('\n\nOK')
