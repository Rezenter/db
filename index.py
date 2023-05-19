import shtRipper
from pathlib import Path
import phys_const as c
import math
import json

#start_shotn = 41157
#start_shotn = 42169
start_shotn = 42000
stop_shotn = 43044
overrite: bool = False

db_file: str = 'db/index.json'

bad_sht = [
    42412
]

save_interval = 10
sht_size_threshold = 8  # MB

plasma_current_threshold = 50e3  # A

#sht_path = 'd:/data/globus/sht/sht'
sht_path = 'W:/sht'
sht_ext = '.SHT'

def downsample(x: list[float], y: list[float], scale: int) -> (list[float], list[float]):
    index: int = 0
    res_x: list[float] = []
    res_y: list[float] = []
    while index + scale < len(y):
        res_x.append((x[index] + x[index + scale - 1]) * 0.5)
        res_y.append(sum(y[index: index + scale]) / scale)
        index += scale
    return res_x, res_y


def window_average(y: list[float], half_window: int) -> list[float]:
    window: int = half_window * 2 + 1
    window_half: int = (window - 1) // 2
    index: int = window_half
    curr: float = sum(y[0:window])
    res_y: list[float] = []
    while index + window_half + 1 < len(y):
        curr += y[index + window_half + 1] - y[index - window_half]
        res_y.append(curr / window)
        index += 1
    return res_y


def time_to_ind(time: float) -> int:
    step: float = 1e-6
    return math.floor(time / step)


def dump(x, y):
    with open('tmp.txt', 'w') as file:
        for i in range(len(x)):
            file.write('%.2e, %.2e\n' % (x[i], y[i]))


class Shot:
    Ip_name: str = 'Ip внутр.(Пр2ВК) (инт.18)'
    Itf_name: str = 'Itf (2TF)(инт.23)'
    NBI1_name: str = 'Emission electrode current'
    NBI2_I_name: str = 'Ток пучка новый инжектор'
    NBI2_U_name: str = 'Напряжение пучка новый инжектор'
    laser_name: str = 'Лазер'
    Up_name: str = 'Up (внутреннее 175 петля)'
    D_alpha_42: str = 'D-alfa  хорда R=42 cm'
    D_alpha_50: str = 'D-alfa  хорда R=50 cm'

    def __init__(self, shotn: int):
        self.result = {
            'shotn': shotn
        }
        filename = Path('%s%05d%s' % (sht_path, shotn, sht_ext))
        if not filename.exists():
            self.result['err'] = 'shot %d does not exist\n' % shotn
            return
        if filename.stat().st_size < sht_size_threshold * 1024 * 1024:
            self.result['err'] = 'shot %d has suspicious file size\n' % shotn
            return

        self.sht = shtRipper.ripper.read(filename)

        if not self.scan_ip():
            return

        if not self.scan_Bt():
            return

        self.scan_NBI1()
        self.scan_NBI2()
        self.scan_TS()
        if 'err' not in self.result['TS']:
            self.scan_H_alpha()

    def scan_ip(self) -> bool:
        breakdown_threshold: float = 10e3  # A
        flattop_range: float = 0.7  # from maximum

        start_ind: int = 0
        stop_ind: int = 0

        if self.Ip_name not in self.sht:
            self.result['err'] = 'SHT file has no plasma current'
            return False
        ip_x, ip_y = downsample(x=self.sht[self.Ip_name]['x'], y=window_average(self.sht[self.Ip_name]['y'], 1500), scale=100)

        max_ind: int = 0
        plasma_found: bool = False
        for ind in range(len(ip_x)):
            if ip_y[ind] > breakdown_threshold:
                if start_ind == 0:
                    start_ind = ind
                if ip_y[ind] > plasma_current_threshold:
                    plasma_found = True
                if ip_y[ind] > ip_y[max_ind]:
                    max_ind = ind
            elif ip_y[ind] < breakdown_threshold:
                if plasma_found:
                    stop_ind = ind
                    break

        if not plasma_found:
            self.result['err'] = 'Plasma current %d does not reach threshold %d.' % (ip_y[max_ind], plasma_current_threshold)
            return False

        flat_start_ind: int = 0
        flat_stop_ind: int = 0
        low_limit = ip_y[max_ind] * flattop_range
        for ind in range(start_ind, stop_ind):
            if ip_y[ind] > low_limit:
                flat_start_ind = ind
                break
        for ind in range(stop_ind, start_ind, -1):
            if ip_y[ind] > low_limit:
                flat_stop_ind = ind
                break
        ip_prev: float = -1e99
        ip: float = 0.0
        while ip - ip_prev > 1:
            if flat_stop_ind > flat_start_ind:
                low_limit = sum(ip_y[flat_start_ind: flat_stop_ind]) / (flat_stop_ind - flat_start_ind) * 0.95
                for ind in range(flat_start_ind, stop_ind):
                    if ip_y[ind] > low_limit:
                        flat_start_ind = ind
                        break
                for ind in range(flat_stop_ind, start_ind, -1):
                    if ip_y[ind] > low_limit:
                        flat_stop_ind = ind
                        break
                if flat_stop_ind > flat_start_ind:
                    ip_prev = ip
                    ip = sum(ip_y[flat_start_ind: flat_stop_ind]) / c.Unit.k / (flat_stop_ind - flat_start_ind)
                else:
                    break
            else:
                break

        if ip == 0.0:
            self.result['err'] = 'No flattop detected'
            return False

        self.result.update({
            'T_start': ip_x[start_ind],
            'T_stop': ip_x[stop_ind],
            'T_max': ip_x[max_ind],
            'Ip_max': ip_y[max_ind] / c.Unit.k,
            'T_flattop_start': ip_x[flat_start_ind],
            'T_flattop_stop': ip_x[flat_stop_ind],
            'Ip': ip,
            'flattop_start_ind': time_to_ind(ip_x[flat_start_ind]),
            'flattop_stop_ind': time_to_ind(ip_x[flat_stop_ind]),
            'T_start_index': time_to_ind(ip_x[start_ind]),
            'T_stop_index': time_to_ind(ip_x[stop_ind]),
        })
        return True

    def scan_Bt(self) -> bool:
        Itf_to_Bt: float = 0.9e-5
        freq_reduction: int = 10

        if self.Itf_name not in self.sht:
            self.result['err'] = 'SHT file has no Itf'
            return False

        self.result['Bt'] = Itf_to_Bt * sum(self.sht[self.Itf_name]['y'][self.result['flattop_start_ind'] // freq_reduction: self.result['flattop_stop_ind'] // freq_reduction]) / \
                            (self.result['flattop_stop_ind'] // freq_reduction - self.result['flattop_start_ind'] // freq_reduction)
        return True

    def scan_NBI1(self) -> bool:
        freq_reduction: int = 10
        scale: int = 100
        threshold: float = 0.5
        shutdown: float = 0.8

        if self.NBI1_name not in self.sht:
            self.result['NBI1'] = {
                'err': 'SHT file has no NBI_1 signal.'
            }
            return False

        plasma_start_ind = self.result['T_start_index'] // (freq_reduction * scale)
        plasma_stop_ind = self.result['T_stop_index'] // (freq_reduction * scale)
        x, y = downsample(x=self.sht[self.NBI1_name]['x'], y=self.sht[self.NBI1_name]['y'], scale=scale)
        start_ind: int = -1
        stop_ind: int = plasma_stop_ind
        found: bool = False
        y_max: float = 0
        for i in range(plasma_start_ind, plasma_stop_ind):
            if y[i] > threshold and start_ind < 0:
                start_ind = i
                found = True
            if y[i] < y_max * shutdown and start_ind > 0:
                stop_ind = i
                break
            y_max = max(y_max, y[i])
        if found:
            self.result['NBI1'] = {
                'T_start': x[start_ind],
                'T_stop': x[stop_ind],
                'I_max': y_max
            }
        else:
            self.result['NBI1'] = {
                'err': 'NBI1 current does not reach threshold.',
                'I_max': y_max
            }
        return True

    def scan_NBI2(self) -> bool:
        freq_reduction: int = 10
        scale: int = 100
        threshold_u: float = 1.0
        threshold_i: float = 1.0
        shutdown: float = 0.8

        if self.NBI2_I_name not in self.sht or self.NBI2_U_name not in self.sht:
            self.result['NBI2'] = {
                'err': 'SHT file has not enough NBI_2 signals.'
            }
            return False

        plasma_start_ind = self.result['T_start_index'] // (freq_reduction * scale)
        plasma_stop_ind = self.result['T_stop_index'] // (freq_reduction * scale)
        x, y = downsample(x=self.sht[self.NBI2_I_name]['x'], y=self.sht[self.NBI2_I_name]['y'], scale=scale)
        start_ind: int = -1
        stop_ind: int = plasma_stop_ind
        i_max: float = 0
        found: bool = False
        for i in range(plasma_start_ind, plasma_stop_ind):
            if y[i] > threshold_i and start_ind < 0:
                start_ind = i
                found = True
            if y[i] < i_max * shutdown and start_ind > 0:
                stop_ind = i
                break
            i_max = max(i_max, y[i])

        if found:
            x, y = downsample(x=self.sht[self.NBI2_U_name]['x'], y=self.sht[self.NBI2_U_name]['y'], scale=scale)
            u_max: float = max(y[start_ind: stop_ind])
            self.result['NBI2'] = {
                'T_start': x[start_ind],
                'T_stop': x[stop_ind],
                'U_max': u_max,
                'I_max': i_max
            }
        else:
            self.result['NBI2'] = {
                'err': 'NBI2 current does not reach threshold',
                'U_max': i_max
            }
        return True

    def scan_TS(self) -> bool:
        der_threshold: float = -0.15
        pulse_length: int = 210

        if self.laser_name not in self.sht:
            self.result['TS'] = {
                'err': 'SHT file has no laser signal.'
            }
            return False

        x = self.sht[self.laser_name]['x']
        y = self.sht[self.laser_name]['y']

        pulses: list[float] = []
        i: int = 0
        while i < len(y) - 1:
            if y[i + 1] - y[i] < der_threshold:
                pulses.append((x[i] + x[i + 1]) * 0.5)
                i += pulse_length
            i += 1

        if len(pulses) == 0:
            self.result['TS'] = {
                'err': 'No laser pulses detected'
            }
        else:
            self.result['TS'] = {
                'time': pulses
            }
            return True
        return False

    def find_closest_TS(self, time: float) -> int:
        for ind in range(len(self.result['TS']['time']) - 1):
            if self.result['TS']['time'][ind] <= time < self.result['TS']['time'][ind + 1]:
                if time - self.result['TS']['time'][ind] <= self.result['TS']['time'][ind + 1] - time:
                    return ind
                else:
                    return ind + 1
        return -1

    def scan_H_alpha(self) -> bool:
        freq_reduction: int = 1
        scale: int = 150
        der_threshold: float = 0.4
        pulse_length: int = 5

        if self.D_alpha_42 not in self.sht:
            self.result['ELM'] = {
                'err': 'SHT file has no d_alpha signal.'
            }
            return False


        flattop_start_ind = self.result['flattop_start_ind'] // (freq_reduction * scale)
        flattop_stop_ind = self.result['flattop_stop_ind'] // (freq_reduction * scale)
        x, y = downsample(x=self.sht[self.D_alpha_42]['x'], y=self.sht[self.D_alpha_42]['y'], scale=scale)

        self.result['ELM']: list[float] = []
        i: int = flattop_start_ind
        while i < flattop_stop_ind - 1:
            if y[i + 1] - y[i] > der_threshold:
                highRes_ind = i * freq_reduction * scale

                max_der: float = 0
                max_ind: int = highRes_ind
                der_halfWindow: int = 3

                for j in range(highRes_ind, highRes_ind + scale):
                    candidate: float = self.sht[self.D_alpha_42]['y'][j + der_halfWindow] - self.sht[self.D_alpha_42]['y'][j - der_halfWindow]
                    if candidate > max_der:
                        max_der = candidate
                        max_ind = j
                las_ind: int = self.find_closest_TS(self.sht[self.D_alpha_42]['x'][max_ind])
                self.result['ELM'].append({
                    'time': self.sht[self.D_alpha_42]['x'][max_ind],
                    'laser_ind': las_ind,
                    'las_delay': self.result['TS']['time'][las_ind] - self.sht[self.D_alpha_42]['x'][max_ind]
                })
                i += pulse_length
            i += 1

        return True


def save(res):
    with open(db_file, 'w') as file:
        json.dump(res, file, indent=2)
        print('\nSAVED\n')


res = {}
last_save = start_shotn
if not overrite:
    index_path = Path(db_file)
    if index_path.is_file():
        with open(index_path, 'r') as file:
            res = json.load(file)

current_ind = 0
for shotn in range(start_shotn, stop_shotn + 1):
    if shotn in bad_sht:
        res[shotn] = {
            'shotn': shotn,
            'err': 'sht is marked "bad"'
        }
        continue
    if not overrite and str(shotn) in res:
        continue

    print(shotn)

    current = Shot(shotn=shotn)
    res[shotn] = current.result
    if shotn - last_save > save_interval - 1:
        save(res)
        last_save = shotn

save(res)

print('Code OK.')

'''
['Plasma shift', 'D-alfa верхний купол', 'Напряжение пучка новый инжектор', ' B 343 nm', 
'Emission electrode voltage', 'Ток пучка новый инжектор', 'Emission electrode current', 
'ДГП квадрупольный (инт. 19) (петли  176,178,181,184)', 'МГД наружный', 'МГД быстрый зонд тор.',
 'D-alfa нижний купол', 'МГД быстрый зонд рад.', 'HeI 587 nm', 'МГД быстрый зонд верт.', 'D-alfa  хорда R=42 cm',
  'EFC N (инт. 27)', 'EFC E (инт. 30)', 'D-alfa  хорда R=50 cm', 'EFC W (инт. 32)', 'Fe I', 'EFC S (инт. 35)',
   'N II 568 nm', 'ВЧ отраженная    ', 'ВЧ падающая', 'CIII 465 nm', 'OIII 559 nm', 'ФДУК 4 (мягкий рентген)', 
   'Радиометр 8 mm', 'ФДУК  2 (обзорный)', 'nl 42 cm (1.5мм) 64pi', 'ФДУК  1 (на столб)', 'ФДУК 3 (периферийный)',
    'SXR 50 mkm', 'Радиометр 1.5 cm', 'continuum', 'Пирометр 3 мкм', 'НXR Подушниковой', 
    'ДГП (петли 180,169) (инт.15)', 'SXR 127 мкм', 'Лазер', 'Up (внутреннее 175 петля)', 'Пирометр 4 мкм',
     'Up (внешнее,183 петля, 171 канал)', 'Диамагнитный сигнал (новый инт.)', 'SXR 15 мкм', 'Iнак. vfc,
      hfc (10 фидер vfc) (инт.3)', 'Ipf3 (6PF3)(инт.17)', 'I efcc (7CC) (инт.6)', 'Icc (4pf2) (инт.24)',
       'Ipf1(2PF1) (инт.26)', 'Ivfc (7vfc) (инт.2)', 'Ihfc (8 HFC) (инт.1)', 'Itf (2TF)(инт.23)',
        'Ics (4CS) (инт.22)', 'D-alpha (на столб)', 'Ток пушки (2 ступень)', 'ДВП внутренний (инт.20)',
         'SXR 80 mkm', 'Петля на инжекторе', 'Ip новый (Пр1ВК) (инт.16)', 'Ip внутр.(Пр2ВК) (инт.18)']
'''