from pathlib import Path
import phys_const

ts_path: Path = Path('//172.16.12.127/Pub/!!!TS_RESULTS/shots/')

request = {}
with open('in/CXRS_unfiltered.csv', 'r') as file:
    for line in file:
        spl = line.split(',')
        shotn: int = int(spl[0])
        time: float = float(spl[1])
        if shotn not in request:
            request[shotn] = []
        request[shotn].append(time)

result = []

for i, (shotn, times) in enumerate(request.items()):
    ts_data = []
    with open(ts_path.joinpath('%d/%d_dynamics.csv' % (shotn, shotn)), 'r') as file:
        file.readline()
        file.readline()
        for line in file:
            spl = [float(v) for v in line.split(',')]
            ts_data.append(spl)
    for time in times:
        for ind in range(len(ts_data)):
            if ts_data[ind][1] <= time < ts_data[ind + 1][1]:
                res_entry = [shotn, time]

                res_entry.extend([phys_const.interpolate(x_prev=ts_data[ind][1], x_tgt=time, x_next=ts_data[ind + 1][1],
                                                         y_prev=ts_data[ind][i], y_next=ts_data[ind + 1][i])
                                  for i in range(len(ts_data[ind]))])

                result.append(res_entry)
                break

with open('out/CXRS_TS.csv', 'w') as file:
    for entry in result:
        file.write(', '.join(['%s' % v for v in entry]) + '\n')

print('OK')
