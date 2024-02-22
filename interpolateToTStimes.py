import json
import phys_const

shotn: int = 41513

filePath: str = 'in/#%dTemperature D.txt' % shotn

data = []
with open(filePath, 'r') as f:
    header = f.readline()
    for line in f:
        spl = [float(v) for v in line.strip().split()]
        data.append({
            't': spl[0]*1e-3,
            'vals': spl[1:]
        })

db = None
with open('db/index.json', 'r') as file:
    db = json.load(file)['%d' % shotn]

result = []
for entry in db['TS']['time']:
    if not db['T_start'] <= entry <= db['T_stop']:
        continue
    #t = phys_const.interpolate_arr(x_arr=[v['t'] for v in data], y_arr=[v['vals'][0] for v in data], x_tgt=entry)
    result.append({
        't': entry,
        'v': [phys_const.interpolate_arr(x_arr=[v['t'] for v in data], y_arr=[v['vals'][t] for v in data], x_tgt=entry) for t in range(len(data[0]['vals']))]
    })

for entry in result:
    print(entry['t'] * 1e3, entry['v'][0], entry['v'][1])

print('Ok')
