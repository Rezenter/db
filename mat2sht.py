import shtRipper
import scipy.io
from pathlib import Path
import time

full_names = {
    'I_P': {
        'comment': 'Ток плазмы',
        'unit': 'I(A)',
        'offset': 0,
        'yRes': 5,
        'name': 'Ip внутр.(Пр2ВК) (инт.18)'
    },
    'I_CS': {
        'comment': 'ток центрального соленоида',
        'unit': 'I(A)',
        'offset': 0,
        'yRes': 5,
        'name': 'Ics (4CS) (инт.22)'
    },
    'I_CC': {
        'comment': 'ток корректирующих катушек',
        'unit': 'I(A)',
        'offset': 0,
        'yRes': 5,
        'name': 'Icc (4pf2) (инт.24)'
    },
    'I_PF1': {
        'comment': 'ток катушки PF1',
        'unit': 'I(A)',
        'offset': 0,
        'yRes': 5,
        'name': 'Ipf1(2PF1) (инт.26)'
    },
    'I_PF2_1': {
        'comment': 'ток катушки PF2',
        'unit': 'I(A)',
        'offset': 0,
        'yRes': 5,
        'name': 'Ipf2_1'
    },
    'I_PF2_2': {
        'comment': 'ток катушки PF2',
        'unit': 'I(A)',
        'offset': 0,
        'yRes': 5,
        'name': 'Ipf2_2'
    },
    'I_PF3': {
        'comment': 'ток катушки PF3',
        'unit': 'I(A)',
        'offset': 0,
        'yRes': 5,
        'name': 'Ipf3 (6PF3)(инт.17)'
    },
    'I_HFC': {
        'comment': 'ток катушки горизонтального поля',
        'unit': 'I(A)',
        'offset': 0,
        'yRes': 5,
        'name': 'Ihfc (8 HFC) (инт.1)'
    },
    'I_VFC': {
        'comment': 'ток катушки вертикального поля',
        'unit': 'I(A)',
        'offset': 0,
        'yRes': 5,
        'name': 'Ivfc (7vfc) (инт.2)'
    },
    'I_TF': {
        'comment': 'ток катушки тороидального поля',
        'unit': 'I(A)',
        'offset': 0,
        'yRes': 5,
        'name': 'Itf (2TF)(инт.23)'
    },
    'PSI_Mloops': {
        'comment': '???',
        'unit': 'I(A)',
        'offset': 0,
        'yRes': 5,
        'name': 'Magnetic flux, loop №',
        'arr': True
    },
    'I_PF_ref': {
        'comment': '???',
        'unit': 'I(A)',
        'offset': 0,
        'yRes': 5,
        'name': 'Программа тока №',
        'arr': True
    },
    'u_PF': {
        'comment': '???',
        'unit': 'I(A)',
        'offset': 0,
        'yRes': 5,
        'name': 'Управляющий сигнал №',
        'arr': True
    }
}


in_path: Path = Path('\\\\172.16.12.127\\Pub\\!!!CURRENT_COIL_METHOD\\magn_data_mat\\')
out_path: Path = Path('\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\test_moscow_sht\\')


while (1):
    mats = [str(x).split('\\')[-1][:-4] for x in in_path.iterdir()]
    shts = [str(x).split('\\')[-1][:-4] for x in out_path.iterdir()]

    for m in mats:
        if m not in shts:
            print(m)

            shotn = int(m[5:])

            mat = scipy.io.loadmat('%s\\shot_%06d.mat' % (in_path, shotn))
            #print(mat['time'][0])

            t = mat['time'][0].tolist()

            dat = mat['data'][0].tolist()

            to_pack = {}
            for i in range(len(mat['data'][0].dtype.names)):
                name = mat['data'][0].dtype.names[i]
                #print(name)
                #print(dat[0][i][0].tolist())
                if name in full_names:
                    if 'arr' not in full_names[name] or not full_names[name]['arr']:
                        to_pack[full_names[name]['name']] = full_names[name]
                        to_pack[full_names[name]['name']]['tMin'] = t[0]
                        to_pack[full_names[name]['name']]['tMax'] = t[-1]
                        to_pack[full_names[name]['name']]['y'] = dat[0][i][0].tolist()
                    else:
                        for j in range(len(dat[0][i])):
                            n = full_names[name]['name'] + '%d' % j
                            to_pack[n] = full_names[name].copy()
                            to_pack[n]['tMin'] = t[0]
                            to_pack[n]['tMax'] = t[-1]
                            to_pack[n]['y'] = dat[0][i][j].tolist()
                else:
                    print(name, ' not listed')

            print('%sshot_%06d.sht' % (out_path, shotn))
            packed = shtRipper.ripper.write(path=out_path, filename='shot_%06d.SHT' % shotn, data=to_pack)
    time.sleep(1)

print('OK')
