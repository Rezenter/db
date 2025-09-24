import shtRipper
import scipy.io

shotn = 40

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
        'name': 'Magnetic flux, some loop'
    },
    'I_PF_ref': {
        'comment': '???',
        'unit': 'I(A)',
        'offset': 0,
        'yRes': 5,
        'name': 'Программа тока Ipf'
    },
    'u_PF': {
        'comment': '???',
        'unit': 'I(A)',
        'offset': 0,
        'yRes': 5,
        'name': 'u_PF'
    }
}

mat = scipy.io.loadmat('\\\\172.16.12.127\\Pub\\!!!CURRENT_COIL_METHOD\\magn_data_mat\\shot_%06d.mat' % shotn)
out_path = '\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\test_moscow_sht\\'

#print(mat['time'][0])

t = mat['time'][0].tolist()

dat = mat['data'][0].tolist()

to_pack = {}
for i in range(len(mat['data'][0].dtype.names)):
    name = mat['data'][0].dtype.names[i]
    #print(name)
    #print(dat[0][i][0].tolist())
    if name in full_names:
        to_pack[full_names[name]['name']] = full_names[name]
        to_pack[full_names[name]['name']]['tMin'] = t[0]
        to_pack[full_names[name]['name']]['tMax'] = t[-1]
        to_pack[full_names[name]['name']]['y'] = dat[0][i][0].tolist()
    else:
        print(name, ' not listed')

print('%sshot_%06d.sht' % (out_path, shotn))
packed = shtRipper.ripper.write(path=out_path, filename='shot_%06d.SHT' % shotn, data=to_pack)

print('OK')
