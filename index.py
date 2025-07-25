import shtRipper
from pathlib import Path
import phys_const as c
import math
import json
import utils.auxiliary as aux
import msgpack

start_shotn: int = 37000
#start_shotn: int = 37000

# calc inner- outer- spacings between LCFS and walls, Rsep
# calc Ip using both signals. Trust second for >45000

#start_shotn: int = 42777

stop_shotn: int = 0
with open('\\\\172.16.12.127\\Data\\SHOTN.txt', 'r') as f:
    stop_shotn = int(f.readline()) - 1
    print('Stop at: ', stop_shotn)
stop_shotn = 46128

'''
shot_list = []  #overriding
with open('in/4Nikita.csv', 'r') as f:
    line = f.readline()
    for line in f:
        s = int(line.split(',')[1])
        if s not in shot_list:
            shot_list.append(s)
'''
#overrite: bool = False
overrite: bool = False

#db_file: str = 'db/index_test.json'
db_file: str = '\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\index.json'
db_file_bin: str = '\\\\172.16.12.127\\Pub\\!!!TS_RESULTS\\shots\\index.msgpk'

bad_sht: list[int] = []

save_interval: int = 1000
sht_size_threshold: int = 8  # MB

plasma_current_threshold: float = 50e3  # A

#sht_path = 'd:/data/globus/sht/sht'
#sht_path: str = 'W:/sht'
sht_path_1: str = '\\\\172.16.12.127\\Data\\sht'
sht_path_2: str = '\\\\172.16.12.28\\Data\\sht'
sht_ext: str = '.SHT'
ts_path: Path = Path('//172.16.12.127/Pub/!!!TS_RESULTS/shots/')

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
    index: int = 0
    curr: float = sum(y[:window_half])
    res_y: list[float] = []
    while index < window_half:
        curr += y[index + window_half - 1]
        index += 1
        res_y.append(curr / (index + window_half))

    while index + window_half + 1 < len(y):
        curr += y[index + window_half + 1] - y[index - window_half]
        index += 1
        res_y.append(curr / window)

    while index < len(y):
        curr -= y[index]
        res_y.append(curr / (len(y) - index))
        index += 1
    return res_y


def time_to_ind(time_s: float) -> int:
    step: float = 1e-6
    return math.floor(time_s / step)


def dump(x, y):
    with open('tmp.txt', 'w') as file:
        for i in range(len(x)):
            file.write('%.2e, %.2e\n' % (x[i], y[i]))


class Shot:
    Ip_name: str = 'Ip внутр.(Пр2ВК) (инт.18)'
    Ip_name_2: str = 'Ip новый (Пр1ВК) (инт.16)'
    Ip_shotn_threshold: int = 45000
    Itf_name: str = 'Itf (2TF)(инт.23)'
    NBI1_U_name: str = 'Emission electrode voltage'
    NBI1_name: str = 'Emission electrode current'
    NBI2_I_name: str = 'Ток пучка новый инжектор'
    NBI2_U_name: str = 'Напряжение пучка новый инжектор'
    laser_name: str = 'Лазер'
    Up_name: str = 'Up (внутреннее 175 петля)'
    D_alpha_42: str = 'D-alfa  хорда R=42 cm'
    D_alpha_50: str = 'D-alfa  хорда R=50 cm'
    SXR_15: str = 'SXR 15 мкм'
    #SXR_50: str = SXR_15
    SXR_50: str = 'SXR 50 mkm'
    EFC_N: str = 'EFC N (инт. 27)'
    EFC_E: str = 'EFC E (инт. 30)'
    EFC_S: str = 'EFC S (инт. 35)'
    EFC_W: str = 'EFC W (инт. 32)'

    def __init__(self, shotn: int):
        self.result = {
            'shotn': shotn
        }
        filename = Path('%s%05d%s' % (sht_path_1, shotn, sht_ext))
        if not filename.exists():
            filename = Path('%s%05d%s' % (sht_path_2, shotn, sht_ext))
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
        self.scan_DTS()
        if 'err' not in self.result['TS']:
            self.scan_H_alpha()
            self.scan_trapped()
            #self.scan_Zeff()
        self.scan_isotope()
        self.scan_SXR()

        #print(self.result['plasma isotope'])

    def scan_isotope(self) -> bool:
        is_D: bool = 'Газонапуск 2 дейтерий' in self.sht or 'Газонапуск 2, внутренний, дейтерий' in self.sht
        is_H: bool = 'Газонапуск 1 водород' in self.sht or 'Газонапуск 1, верх, водород' in self.sht
        if is_D and not is_H:
            self.result['plasma isotope'] = 'D'
            return True

        if not is_D and is_H:
            self.result['plasma isotope'] = 'H'
            return True

        self.result['plasma isotope'] = '???'
        return False

    def scan_Ip_name(self, name: str):
        breakdown_threshold: float = 10e3  # A
        flattop_range: float = 0.7  # from maximum

        res = {
            'ok': False
        }

        start_ind: int = 0
        stop_ind: int = 0

        if name not in self.sht:
            res['err'] = 'SHT file has no plasma current'
            return res
        ip_x, ip_y = downsample(x=self.sht[name]['x'], y=window_average(self.sht[name]['y'], 1500),
                                scale=100)

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
            res['err'] = 'Plasma current %d does not reach threshold %d.' % (
            ip_y[max_ind], plasma_current_threshold)
            return res

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
            res['err'] = 'No flattop detected'
            return res

        res.update({
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
            'used_Ip': name
        })
        return res

    def scan_ip(self) -> bool:
        self.result['IpOld'] = self.scan_Ip_name(self.Ip_name)
        self.result['IpNew'] = self.scan_Ip_name(self.Ip_name_2)
        tmp = self.result['IpOld']
        if 'err' in self.result['IpOld']:
            if 'err' not in self.result['IpNew']:
                tmp = self.result['IpNew']
                self.result['Ip warning'] = 'error in %s' % self.Ip_name
            else:
                self.result['err'] = "Both Ip signals have errors"
                return False
        else:
            if 'err' not in self.result['IpNew']:
                if abs(self.result['IpOld']['Ip'] - self.result['IpNew']['Ip']) > 0.1*0.5*(self.result['IpOld']['Ip'] + self.result['IpNew']['Ip']):
                    if self.result['shotn'] > self.Ip_shotn_threshold:
                        tmp = self.result['IpNew']
                    else:
                        tmp = self.result['IpOld']
                    self.result['Ip warning'] = 'Ip signals differs %f vs %f' % (abs(self.result['IpOld']['Ip'] - self.result['IpNew']['Ip']), 0.1*0.5*(self.result['IpOld']['Ip'] + self.result['IpNew']['Ip']))
            else:
                tmp = self.result['IpOld']
                self.result['Ip warning'] = 'error in %s' % self.Ip_name_2

        self.result.update({
            'date': self.sht[self.Ip_name]['time'],
            'T_start': tmp['T_start'],
            'T_stop': tmp['T_stop'],
            'T_max': tmp['T_max'],
            'Ip_max': tmp['Ip_max'],
            'T_flattop_start': tmp['T_flattop_start'],
            'T_flattop_stop': tmp['T_flattop_stop'],
            'Ip': tmp['Ip'],
            'flattop_start_ind': tmp['flattop_start_ind'],
            'flattop_stop_ind': tmp['flattop_stop_ind'],
            'T_start_index': tmp['T_start_index'],
            'T_stop_index': tmp['T_stop_index'],
            'used_Ip': tmp['used_Ip']
        })
        return True

    def scan_Bt(self) -> bool:
        #Itf_to_Bt: float = 0.9e-5
        Itf_to_Bt: float = 1.26e-6 * 16 / (math.tau * 0.36)
        #                   vacuum   coils            R

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
            u_ave = 999
            if self.NBI1_U_name in self.sht:
                u_ave = sum(self.sht[self.NBI1_U_name]['y'][start_ind: stop_ind])/(stop_ind - start_ind)
            self.result['NBI1'] = {
                'T_start': x[start_ind],
                'T_stop': x[stop_ind],
                'I_max': y_max,
                'U': u_ave
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
        Upl: list[float] = []
        i: int = 0
        while i < len(y) - 1:
            if y[i + 1] - y[i] < der_threshold:
                pulses.append((x[i] + x[i + 1]) * 0.5)
                Upl.append(self.match_Upl(pulses[-1]))
                #print(shotn, pulses[-1] * 1e3, Upl[-1])
                i += pulse_length
            i += 1

        if len(pulses) == 0:
            self.result['TS'] = {
                'err': 'No laser pulses detected'
            }
        else:
            self.result['TS'] = {
                'time': pulses,
                'Upl': Upl,
                'processed': ts_path.joinpath('%05d/%05d_dynamics.csv' % (shotn, shotn)).exists()
            }
            return True
        return False

    def find_closest_TS(self, time: float) -> int:
        if 'time' not in self.result['TS']:
            return -1
        for ind in range(len(self.result['TS']['time']) - 1):
            if self.result['TS']['time'][ind] <= time < self.result['TS']['time'][ind + 1]:
                if time - self.result['TS']['time'][ind] <= self.result['TS']['time'][ind + 1] - time:
                    return ind
                else:
                    return ind + 1
        return -1

    def find_closest_TS_t(self, time: float) -> int:
        if 'time' not in self.result['TS']:
            return -1
        for ind in range(len(self.result['TS']['time']) - 1):
            if self.result['TS']['time'][ind] <= time < self.result['TS']['time'][ind + 1]:
                if time - self.result['TS']['time'][ind] <= self.result['TS']['time'][ind + 1] - time:
                    return self.result['TS']['time'][ind]
                else:
                    return self.result['TS']['time'][ind + 1]
        return -1

    def scan_DTS(self) -> bool:
        laser_frequency: int = 100
        signal_threshold: float = 0.25

        if 'Лазер ДТР' in self.sht:
            x_data: list = self.sht['Лазер ДТР']['x']
            y_data: list = self.sht['Лазер ДТР']['y']
        elif 'Лазер ДДТР' in self.sht:
            x_data: list = self.sht['Лазер ДДТР']['x']
            y_data: list = self.sht['Лазер ДДТР']['y']
        else:
            self.result['DTS'] = {
                'err': 'SHT file has no laser signal.'
            }
            return False

        DTR_times = []
        for time, signal in zip(x_data, y_data):
            if signal > signal_threshold:
                if len(DTR_times) == 0:
                    DTR_times.append(round(time, 5))  # seconds to ms
                elif time > DTR_times[-1] + 1 / laser_frequency * 0.8:
                    DTR_times.append(round(time, 5))  # seconds to ms


        self.result['DTS'] = {
            'time': DTR_times
        }
        return True

    def match_Upl(self, time: float) -> float:
        if self.Up_name not in self.sht:
            self.result['err'] = 'SHT file has no loop voltage!'
            return -999
        if time > 0.26:
            return -888
        if 'Upl' not in self.sht:
            self.sht['Upl'] = window_average(self.sht[self.Up_name]['y'], 165)
            #print(1/ (2*165 * (self.sht[self.Up_name]['x'][1] - self.sht[self.Up_name]['x'][0])))
        step: float = self.sht[self.Up_name]['x'][1] - self.sht[self.Up_name]['x'][0]
        t_prev_ind: int = math.floor(time / step)
        res = c.interpolate(x_prev=self.sht[self.Up_name]['x'][t_prev_ind], x_tgt=time, x_next= self.sht[self.Up_name]['x'][t_prev_ind + 1],
                                     y_prev=self.sht['Upl'][t_prev_ind], y_next=self.sht['Upl'][t_prev_ind + 1])
        return res

    def scan_H_alpha(self) -> bool:
        freq_reduction: int = 1
        scale: int = 150
        der_threshold: float = 0.35
        pulse_length: int = 5

        if self.D_alpha_42 not in self.sht:
            self.result['ELM'] = {
                'err': 'SHT file has no d_alpha 42 signal.'
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

                for j in range(highRes_ind, highRes_ind + scale*2):
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

        self.result['TS']['d-alpha'] = {}
        # for every D-alpha signal in sht
        signals = [
            {
                'k': '42',
                'v': self.D_alpha_42
            }, {
                'k': '50',
                'v': self.D_alpha_50
            }, {
                'k': 'column',
                'v': 'D-alpha (на столб)'
            }, {
                'k': 'lower',
                'v': 'D-alfa нижний купол'
            }, {
                'k': 'upper',
                'v': 'D-alfa верхний купол'
            }
        ]
        for s in signals:
            if s['v'] not in self.sht:
                self.result['TS']['d-alpha'][s['k']] = {
                    'err': 'SHT file has no signal %s' % s['v']
                }
            else:
                self.result['TS']['d-alpha'][s['k']] = {
                    'zero': 0,
                    'val': []
                }
                stop_ind = time_to_ind(30e-3)
                self.result['TS']['d-alpha'][s['k']]['zero'] = sum(self.sht[s['v']]['y'][:stop_ind]) / (stop_ind)
                for t in self.result['TS']['time']:
                    half_window: float = 1.5e-3  # ms
                    start_ind = time_to_ind(t - half_window)
                    stop_ind = time_to_ind(t + half_window)
                    ave: float = sum(self.sht[s['v']]['y'][start_ind:stop_ind]) / (stop_ind - start_ind)
                    self.result['TS']['d-alpha'][s['k']]['val'].append(ave-self.result['TS']['d-alpha'][s['k']]['zero'])

        if self.D_alpha_50 not in self.sht:
            self.result['ELM2'] = {
                'err': 'SHT file has no d_alpha 50 signal.'
            }
            return False

        der_window = 300
        half_window: int = der_window // 2
        der_threshold = 2e-6
        min_tau = 50
        max_tau = 500
        signal = []

        for i in range(len(self.sht[self.D_alpha_50]['y'])):
            signal.append({
                'ave': sum(self.sht[self.D_alpha_50]['y'][i - half_window: i + half_window]) / der_window
            })
        for i in range(der_window + 1, len(self.sht[self.D_alpha_50]['y']) - der_window):
            signal[i]['der'] = (signal[i + 1]['ave'] - signal[i - 1]['ave']) / der_window
        for i in range(der_window * 2 + 1, len(self.sht[self.D_alpha_50]['y']) - der_window * 2):
            signal[i]['der_ave'] = sum([signal[v]['der'] for v in range(i - half_window, i + half_window)]) / der_window

        self.result['ELM2']: list[float] = []
        i = 115000
        while i < len(self.sht[self.D_alpha_50]['y']) - der_window * 3 - max_tau:
            if signal[i]['der_ave'] >= der_threshold:
                max_ind = i
                min_ind = i
                ave_max = 0
                for j in range(i, i + max_tau):
                    ave_max = max(ave_max, signal[j]['ave'])
                    if signal[j]['der_ave'] > signal[max_ind]['der_ave']:
                        max_ind = j
                    elif signal[j]['der_ave'] < signal[min_ind]['der_ave']:
                        min_ind = j
                if signal[min_ind]['der_ave'] < -der_threshold:
                    self.result['ELM2'].append({
                        't': max_ind * 1e-6,
                        'tau': (min_ind - max_ind),
                        'der': signal[max_ind]['der_ave'],
                        'level': signal[max_ind]['ave'],
                        'max': ave_max
                    })
                    i += max_tau
            i += min_tau
        return True

    def scan_trapped(self) -> bool:
        '''
        Kate:
        delta_efc = [data['EFC S (инт. 35)']['data'][i] - data['EFC N (инт. 27)']['data'][i] for i in
                 range(len(data['EFC N (инт. 27)']['data']))]

        '''
        self.result['TS']['trapped'] = {}
        if self.EFC_N not in self.sht or self.EFC_S not in self.sht:
            self.result['TS']['trapped']['SN'] = {
                'err': 'SHT file has no EFC_N or EFC_S signal.'
            }
        else:
            if len(self.sht[self.EFC_N]['y']) != len(self.sht[self.EFC_S]['y']):
                self.result['TS']['trapped']['SN'] = {
                    'err': 'SHT file has bad EFC_N or EFC_S signal.'
                }
            diff = [self.sht[self.EFC_S]['y'][i] - self.sht[self.EFC_N]['y'][i] for i in range(len(self.sht[self.EFC_N]['y']))]
            self.result['TS']['trapped']['SN'] = []
            for t in self.result['TS']['time']:
                half_window: float = 0.5e-3 #ms
                start_ind = time_to_ind(t - half_window)
                stop_ind = time_to_ind(t + half_window)
                ave: float = sum(diff[start_ind:stop_ind]) / (stop_ind - start_ind)
                self.result['TS']['trapped']['SN'].append(ave)

        if self.EFC_W not in self.sht or self.EFC_E not in self.sht:
            self.result['TS']['trapped']['WE'] = {
                'err': 'SHT file has no EFC_W or EFC_E signal.'
            }
        else:
            if len(self.sht[self.EFC_W]['y']) != len(self.sht[self.EFC_E]['y']):
                self.result['TS']['trapped']['WE'] = {
                    'err': 'SHT file has bad EFC_W or EFC_E signal.'
                }
            diff = [self.sht[self.EFC_W]['y'][i] - self.sht[self.EFC_E]['y'][i] for i in range(len(self.sht[self.EFC_W]['y']))]
            self.result['TS']['trapped']['WE'] = []
            for t in self.result['TS']['time']:
                half_window: float = 0.5e-3 #ms
                start_ind = time_to_ind(t - half_window)
                stop_ind = time_to_ind(t + half_window)
                ave: float = sum(diff[start_ind:stop_ind]) / (stop_ind - start_ind)
                self.result['TS']['trapped']['WE'].append(ave)
        return True

    def scan_Zeff(self) -> bool:
        self.result['TS']['zeff'] = {}

        zeff_path: Path = Path('\\\\172.16.12.127\\Pub\\Tuxmeneva\\Zeff\\%05d_Zeff.txt' % self.result['shotn'])
        if(zeff_path.exists()):
            self.result['TS']['zeff']['Kate'] = []
            data = {}
            with open(zeff_path, 'r') as f:
                for line in f:
                    if len(line) <= 2:
                        continue
                    spl = line.split('\t')
                    if len(spl) < 4:
                        spl = line.split(' ')
                    if len(spl) == 5:
                        data[float(spl[1])] = float(spl[3])
                    elif len(spl) == 4:
                        data[float(spl[1])] = float(spl[2])
                    else:
                        fuck
            for ts_i in range(len(self.result['TS']['time'])):
                ts_t = self.result['TS']['time'][ts_i]
                for i in data:
                    if ts_t - 0.001 <= i <= ts_t + 0.001:
                        self.result['TS']['zeff']['Kate'].append(data[i])
                        break
                else:
                    self.result['TS']['zeff']['Kate'].append(0)
        else:
            self.result['TS']['zeff']['Kate'] = {
                'err': 'no Zeff data file found.'
            }

        ch_ind = 1
        poly_ind = -1
        path: Path = ts_path.joinpath(Path('%05d\\result.json' % self.result['shotn']))
        path2: Path = ts_path.joinpath(Path('%05d\\signal.json' % self.result['shotn']))
        if path.exists() and path2.exists():
            self.result['TS']['zeff']['TS'] = []
            ts_res = None
            with open(path, 'r') as f:
                ts_res = json.load(f)
            with open(path2, 'r') as f:
                ts_res['sig'] = json.load(f)['data']
            with open('\\\\172.16.12.130\\d\\data\\db\\calibration\\abs\\processed\\%s.json' % ts_res['absolute_name'], 'r') as f:
                ts_res['A'] = json.load(f)['A']

            #poly_los_ind = 9
            poly_los_ind = 0
            r_min = 999
            for i, poly in enumerate(ts_res['config']['poly']):
                R = ts_res['config']['fibers'][ts_res['config']['poly'][i]['fiber']]['R']
                if abs(R - 404) < r_min:
                    r_min = abs(R - 404)
                    poly_los_ind = i

            filters = aux.Filters(ts_res['config']['poly'][poly_los_ind]['filter_set'])
            apd = aux.APD(ts_res['config']['poly'][poly_los_ind]['detectors'])
            dh = ts_res['config']['sockets'][
                     ts_res['config']['fibers'][ts_res['config']['poly'][poly_los_ind]['fiber']]['lens_socket_ind']][
                     'image_h'] * 1e-3
            # cos_alpha = 0.9
            # L = 16.8 * 1e-3 * cos_alpha #use poloidal_length instead
            L = ts_res['config']['fibers'][ts_res['config']['poly'][poly_los_ind]['fiber']]['poloidal_length'] * 1e-3


            for ev_i, ev in enumerate(ts_res['events']):
                if 'error' in ev and ev['error'] != '' and ev['error'] is not None:
                    self.result['TS']['zeff']['TS'].append(0)
                elif not self.result['T_start'] <= ev['timestamp']*1e-3 <= self.result['T_stop']:
                    self.result['TS']['zeff']['TS'].append(0)
                else:
                    los_prof = []
                    for i, poly in enumerate(ev['T_e']):
                        if not ('error' in poly and poly['error'] != '' and poly['error'] is not None):
                            R = ts_res['config']['fibers'][ts_res['config']['poly'][i]['fiber']]['R']
                            if R < 400:
                                continue
                            los_prof.append({
                                'L': (math.sqrt(866**2 - 391.7**2) - math.sqrt(R**2-391.7**2))*1e-3,
                                'n_e': poly['n'],
                                't_e': poly['T']
                            })
                    if len(los_prof) == 0:
                        continue
                    los_prof.sort(key=lambda x: x['L'])
                    los_prof.append({
                        'L': (math.sqrt(866 ** 2 - 391.7 ** 2) - math.sqrt(391.7 ** 2 - 391.7 ** 2)) * 1e-3,
                        'n_e': los_prof[-1]['n_e'],
                        't_e': los_prof[-1]['t_e']
                    })

                    #math.pow(pre_std * matching_gain * 4 / sp_ch['fast_gain'], 2) * 6715 * 0.0625 - 1.14e4 * 0.0625
                    n_ts_arr = [math.sqrt(math.pow(ts_res['sig'][ev_i]['poly']['%d' % poly_los_ind]['ch'][ch]['pre_std'] * ts_res['config']['preamp']['matchingFastGain'] * 4 / ts_res['config']['poly'][poly_los_ind]['channels'][ch]['fast_gain'], 2) * 6715 * 0.0625 - 1.14e4 * 0.0625) for ch in range(len(filters.trans))]
                    #n_ts = math.sqrt(math.pow(ts_res['sig'][ev_i]['poly']['%d' % poly_los_ind]['ch'][1]['pre_std'] * ts_res['config']['preamp']['matchingFastGain'] * 4 / ts_res['config']['poly'][poly_los_ind]['channels'][0]['fast_gain'], 2) * 6715 * 0.0625 - 1.14e4 * 0.0625)
                    #n_brem: float = 0
                    n_brem_ch = [0.0 for ch in filters.trans]

                    #dt = 34e-9 #s
                    dt = ts_res['config']['common']['integrationTime'] * 1e-9 #s
                    A_OH = 0.4 * 4
                    #dh = 4.5e-3 #use config instead

                    dOmega = 0.0175
                    T = 0.8 * 0.3 * 0.7
                    T_polar = 0.5

                    const = A_OH * dt * dh * L * T * dOmega * T_polar
                    wl_step: float = 0.1 * 1e-9
                    for ind in range(len(los_prof) - 1):
                        wl: float = 1055*1e-9

                        Te = (los_prof[ind]['t_e'] + los_prof[ind + 1]['t_e']) * 0.5
                        ne = (los_prof[ind]['n_e'] + los_prof[ind + 1]['n_e']) * 0.5
                        step = los_prof[ind + 1]['L'] - los_prof[ind]['L']
                        while wl > 1025*1e-9:
                            ae = 1
                            filter = filters.transmission(ch=1, wl_m=wl) * ae * apd.qe(wl_m=wl)
                            # if calibration version == 2:
                            # A kate = A*pi/(3*Lscat*Omega)
                            #else =  A*pi*1.864E-19/(3*Lscat*Omega)  #1.864E-19=h*c/lambda_0
                            #print('fuck up')

                            #gff = 0.55 * math.log(0.0018 * Te * wl * 1e9)
                            #exp_milt = math.exp(-1240 / (Te * wl * 1e9))
                            #n_brem += 0.763 * 10**(-20) * ne**2 * Zeff * gff * exp_milt / (Te**0.5 * wl)

                            constant = (const * step * 0.763 * 1e-20 * ne ** 2 *
                                       0.55 * math.log(0.0018 * Te * wl * 1e9) *
                                       math.exp(-1240 / (Te * wl * 1e9)) / (Te ** 0.5 * wl * 1e9)) *2 * wl_step * 1e9
                            for ch_ind in range(len(filters.trans)):
                                n_brem_ch[ch_ind] += constant * filters.transmission(ch=ch_ind+1, wl_m=wl) * ae * apd.qe(wl_m=wl)

                            wl -= wl_step
                    #n_brem *= 2 * wl_step * 1e9  # half los integration * d(wl)
                    res = []
                    for ch_ind in range(len(filters.trans)):
                        if n_brem_ch[ch_ind] == 0:
                            res.append(0)
                        else:
                            res.append(n_ts_arr[ch_ind] / n_brem_ch[ch_ind])
                    self.result['TS']['zeff']['TS'].append(res)
                    #self.result['TS']['zeff']['TS'].append(n_ts / n_brem)
                    #print(n_ts, n_brem)
        else:
            self.result['TS']['zeff']['TS'] = {
                'err': 'no TS json data file found.'
            }
        return True

    def scan_SXR(self) -> bool:
        if self.SXR_15 not in self.sht:
            self.result['SXR'] = {
                'err': 'SHT file has no SXR_15 signal.'
            }
            return False
        if self.SXR_50 not in self.sht:
            self.result['SXR'] = {
                'err': 'SHT file has no SXR_50 signal.'
            }
            return False

        freq_reduction: int = 1
        scale: int = 30

        #flattop_start_ind = self.result['flattop_start_ind'] // (freq_reduction * scale)
        start_ind = self.result['T_start_index'] // (freq_reduction * scale)
        flattop_stop_ind = self.result['flattop_stop_ind'] // (freq_reduction * scale)


        x, y = downsample(x=self.sht[self.SXR_50]['x'], y=self.sht[self.SXR_50]['y'], scale=scale)

        xx, yy = downsample(x=x, y=y, scale=scale)
        #for i in range(flattop_start_ind//scale, flattop_stop_ind//scale):
        #    print(xx[i], yy[i])
        #fuck

        if(flattop_stop_ind//scale - start_ind//scale <=1):
            self.result['SXR'] = {
                'err': 'too small flattop'
            }
            #print("FUCK!")
            return False

        self.result['SXR'] = {
            'max': max(yy[start_ind//scale: flattop_stop_ind//scale]) - y[333],
            'time': []
        }
        der_threshold: float = self.result['SXR']['max'] * 0.03
        i: int = start_ind
        while i < flattop_stop_ind - 1:
            if y[i] - y[i + 1] > der_threshold:

                highRes_ind = i * freq_reduction * scale
                #print(self.sht[self.SXR_50]['x'][highRes_ind - scale * 2], self.sht[self.SXR_50]['x'][highRes_ind + scale * 2])
                max_der: float = 0
                max_ind: int = highRes_ind
                der_halfWindow: int = 20
                for j in range(highRes_ind - scale * 1, highRes_ind + scale * 1):
                    candidate: float = self.sht[self.SXR_50]['y'][j - der_halfWindow] - \
                                        self.sht[self.SXR_50]['y'][j + der_halfWindow]
                    #print(j / 1000, self.sht[self.SXR_50]['y'][j], candidate)
                    if candidate > max_der:
                        max_der = candidate
                        max_ind = j
                        #print('__________________up')
                las_time: int = self.find_closest_TS_t(self.sht[self.SXR_50]['x'][max_ind])
                amp = (y[i - 5] - y[i + 5])
                if amp > 0.002 and (len(self.result['SXR']['time']) == 0 or self.sht[self.SXR_50]['x'][max_ind] != self.result['SXR']['time'][-1]['time']):
                    delay = 999
                    if las_time > 0:
                        delay = las_time - self.sht[self.SXR_50]['x'][max_ind]
                    period = 999
                    if len(self.result['SXR']['time']):
                        period = self.sht[self.SXR_50]['x'][max_ind] - self.result['SXR']['time'][-1]['time']
                    if period > 0.4*1e-3:
                        self.result['SXR']['time'].append({
                            'time': self.sht[self.SXR_50]['x'][max_ind],
                            'laser_time': las_time,
                            'las_delay': delay,
                            'amp': amp,
                            'period': period
                        })
            i += 1
        '''
        debug = {
            #'x': self.sht[self.SXR_50]['x'],
            #'y': self.sht[self.SXR_50]['y'],
            'down_x': x,
            'down_y': y,
            'der': [y[i] - y[i + 1] for i in range(0, len(y) - 1)],
            'res': self.result['SXR'],
            'der_tres': der_threshold
        }
        with open('out/debug.json', 'w') as outfile:
            json.dump(debug, outfile, indent=2)
        fuck'''
        return False

def save(res, fast=True):
    if not fast:
        with open(db_file, 'w') as file:
            json.dump(res, file, separators=(',', ':'))
    with open(db_file_bin, 'wb') as file:
        msgpack.dump(res, file)
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

save(res, fast=False)

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
         'SXR 80 mkm', 'Петля на инжекторе', 'Ip новый (Пр1ВК) (инт.16)', 'Ip внутр.(Пр2ВК) (инт.18)', 'Газонапуск 2 дейтерий']
'''