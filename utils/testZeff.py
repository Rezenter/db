#stolen from Kate

import phys_const as const
import math

def linear_interpolate(x, list_of_xs, list_of_ys):
    y = 1e10
    for i in range(len(list_of_xs)-1):
        #print(i)
        #print(list_of_xs[i+1], x, list_of_xs[i])
        if list_of_xs[i+1] < x < list_of_xs[i] or list_of_xs[i+1] > x > list_of_xs[i]:
            y = (x - list_of_xs[i+1]) / (list_of_xs[i] - list_of_xs[i+1]) * (list_of_ys[i] - list_of_ys[i+1]) + list_of_ys[i+1]
            continue
        elif list_of_xs[i+1] == x:
            y = list_of_ys[i + 1]
        elif list_of_xs[i] == x:
            y = list_of_ys[i]
    if y == 1e10:
        print('x %f not in range [%f,%f]' %(x, min(list_of_xs), max(list_of_xs)))
        stop
    return y


def txtToDict(path: str, filename: str, delimeter=None, units=False) -> dict:
    data = {}
    l = 0
    keyList = []
    with open('%s%s' % (path, filename), 'r') as file:
        for line in file:
            if l:
                if units:
                    if l == 1:
                        data['units'] = line.strip().split()
                        l+=1
                        continue
                for j, el in enumerate(list(line.strip().split(delimeter))):
                    try:
                        data[keyList[j]].append(float(el))
                    except ValueError:
                        data[keyList[j]].append(el)
            else:
                for j, el in enumerate(list(line.strip().split(delimeter))):
                    keyList.append(el)
                    data[el] = []
            l+=1
    return data


def brem(wl_nm, ne, te, i):
    if te[i] < 0.1:
        return 0
    gff = 0.55 * math.log(0.0018 * te[i] * wl_nm)
    exp_milt = math.exp(-1240 / (te[i] * wl_nm))
    return 0.763 * 10 ** (-20) * ne[i] ** 2 * gff * exp_milt / (te[i] ** 0.5 * wl_nm)

def dN_withoutZeff(ld, data):
    ne = data['ne']
    Te = data['Te']

    int: float = 0
    for i in range(len(data['L los']) - 1):
        int += (brem(ld, ne, Te, i) + brem(ld, ne, Te, i+1)) * 0.5 * ((data['L los'][i+1] - data['L los'][i]) * 1e-3)
    return int

data_OH = txtToDict(path='d:\\docs\\КТМ\\2024\\фон\\BG_anal_Globus\\', filename='Globus_LOS.csv', delimeter=',', units=False)
apd = txtToDict('d:\\data\\db\\apd\\S11519-15\\', filename='aw.csv', delimeter=',', units=True)

filters_tmp = {
    'wl': [],
    'ch1': [],
    'ch2': [],
    'ch3': [],
    'ch4': [],
    'ch5': []
}
for ch in range(5):
    path = 'd:\\data\\db\\filters\\GTS-core_poly1-10\\ch%d.csv' % (ch + 1)
    with open(path, 'r') as file:
        wl = []
        val = []
        flag = False
        for line in file:
            sp = line.split(',')
            wl.append(float(sp[0]))
            val.append(max(float(sp[1]) * 0.01, 0.0))
        if len(filters_tmp['wl']) == 0:
            filters_tmp['wl'] = wl
            filters_tmp['ch%d' % (ch + 1)] = val
        else:
            for i in range(len(filters_tmp['wl'])):
                if filters_tmp['wl'][i] == wl[0]:
                    filters_tmp['ch%d' % (ch + 1)].append(val[0])
                    val.pop(0)
                    wl.pop(0)
                    flag = True
                elif filters_tmp['wl'][i] > wl[0]:
                    if flag:
                        filters_tmp['ch%d' % (ch + 1)].append(const.interpolate(x_tgt=filters_tmp['wl'][i], x_prev=filters_tmp['wl'][i-1], x_next=wl[0], y_prev=filters_tmp['ch%d' % (ch + 1)][-1], y_next=val[0]))
                    else:
                        filters_tmp['ch%d' % (ch + 1)].append(0.0)
                else:
                    print('WTF', i, wl[0], filters_tmp['wl'][i])
            for i in range(len(wl)):
                filters_tmp['wl'].append(wl[i])
                for ch_i in range(5):
                    if len(filters_tmp['ch%d' % (ch_i + 1)]) > 0:
                        if ch_i == ch:
                            filters_tmp['ch%d' % (ch_i + 1)].append(val[i])
                        else:
                            filters_tmp['ch%d' % (ch_i + 1)].append(0.0)

filters = {
    'wl': filters_tmp['wl'],
    'ch1': [],
    'ch2': [],
    'ch3': [],
    'ch4': [],
    'ch5': []
}
for i in range(len(filters_tmp['wl'])):
    incoming = 1
    for ch in range(5):
        filters['ch%d' % (ch + 1)].append(incoming * filters_tmp['ch%d' % (ch + 1)][i])
        incoming *= (1 - filters_tmp['ch%d' % (ch + 1)][i])

corr = 1
A_OH = 0.4
Zeff = 1.5

ae_OH = [1, 0.9896, 0.9597, 0.8047, 0.5523]

apd_mult = 0.01 * const.h * const.c / const.q_e
apd_new = [linear_interpolate(filters['wl'][i], apd['wl'], apd['aw'])*apd_mult / (filters['wl'][i]*1e-9) for i in range(len(filters['wl']))]
dN_OH = [dN_withoutZeff(l, data_OH)*Zeff for l in filters['wl']]

l_sp_ch = [1056.25,
           1039.2,
           1007.25,
           943.97,
           818.01
           ]

dN_ch_OH ={}
for ch in range(1, 6):
    dN_ch_OH[ch] = 0.0
    spectralDens = [dN_OH[i] * filters['ch%i' % ch][i]*apd_new[i] for i in range(len(filters['wl']))]
    for i in range(len(filters['wl']) - 1):
        dN_ch_OH[ch] += (spectralDens[i] + spectralDens[i+1]) * 0.5 * (filters['wl'][i] - filters['wl'][i+1])# * 1e-9

dt = 30e-9
dh = 4.5e-3
cos_alpha = 0.9
L = 16.8 *1e-3
dOmega = 0.0175
T = 0.8*0.3*0.7
T_polar = 0.5
const = dt*dh*cos_alpha*L*T*dOmega*T_polar
Nphe_br_OH = [dN_ch_OH[ch]*const*corr*A_OH*ae_OH[ch-1] for ch in range(1, 6)]

print('OH')
for ch in range(5):
    print(Nphe_br_OH[ch])