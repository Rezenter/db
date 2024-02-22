import json

txt_path = 'd:\\data\\globus\\calc\\OH\\in\\Upl\\'
index_path = 'd:\\code\\TS\\db\\db\\index.json'

shots = [40031, 40032, 40033, 40034, 40035]

t_half_window = 0.001 # seconds

for shot in shots:
    header = ''
    data = []
    with open('%s%05d.txt' % (txt_path, shot), 'r') as file:
        header += file.readline().strip() + '\n'
        header += file.readline().strip() + '\n'
        for line in file:
            data.append([float(v) for v in line.strip().split()])

    index = None
    with open(index_path, 'r') as file:
        index = json.load(file)['%05d' % shot]

    with open('%s%05d_aveTS.txt' % (txt_path, shot), 'w') as file:
        file.write(header)
        for t in index['TS']['time']:
            if index['T_flattop_start'] < t < index['T_flattop_stop']:
                count: int = 0
                ave = [0 for i in data[0]]
                for i in range(len(data)):
                    if data[i][0] - t_half_window < t < data[i][0] + t_half_window:
                        count += 1
                        for j in range(len(data[i])):
                            ave[j] += data[i][j]
                line = ''
                for j in range(len(data[0])):
                    if count != 0:
                        line += '%.3e          ' % (ave[j]/count)
                file.write(line + '\n')


print('OK')
