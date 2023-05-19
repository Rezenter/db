from pathlib import Path
import phys_const

Zeff_path: Path = Path('//172.16.12.127/Pub/Tuxmeneva/Zeff/')

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
    Zeff_data = []
    path: Path = Zeff_path.joinpath('%d_Zeff.txt' % shotn)
    if not path.exists():
        continue
    with open(path, 'r') as file:
        file.readline()
        for line in file:
            spl = [float(v) for v in line.split()[1:]]
            spl[0] *= 1e3
            Zeff_data.append(spl)
    for time in times:
        if Zeff_data[-1][0] < time - 0.01:
            continue
        for ind in range(len(Zeff_data)):
            if Zeff_data[ind][0] - 0.01 <= time <= Zeff_data[ind][0] + 0.01:
                res_entry = [shotn, time]
                res_entry.extend(Zeff_data[ind])
                result.append(res_entry)
                break
            if Zeff_data[ind][0] <= time < Zeff_data[ind + 1][0]:
                res_entry = [shotn, time]
                res_entry.extend([phys_const.interpolate(x_prev=Zeff_data[ind][0], x_tgt=time, x_next=Zeff_data[ind + 1][0],
                                                         y_prev=Zeff_data[ind][i], y_next=Zeff_data[ind + 1][i])
                                  for i in range(len(Zeff_data[ind]))])

                result.append(res_entry)
                break

with open('out/Zeff.csv', 'w') as file:
    for entry in result:
        file.write(', '.join(['%s' % v for v in entry]) + '\n')

print('OK')
