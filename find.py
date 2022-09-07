import shtRipper
from pathlib import Path
import phys_const as c
import math

start_shotn = 41894
start_shotn = 42169
stop_shotn = 42214
plasma_current_threshold = 50e3  # A

sht_path = 'd:/data/globus/sht/sht'
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


def window_average_gen(y: list[float]) -> float:
    window: int = 31  # must be odd
    window_half: int = (window - 1) // 2
    index: int = window_half
    curr: float = sum(y[0:window])
    while index + window_half + 1 < len(y):
        curr += y[index + window_half + 1] - y[index - window_half]
        yield curr / window
        index += 1


def time_to_ind(time: float) -> int:
    step: float = 1e-6
    return math.floor(time / step)


class Shot:
    Ip_name: str = 'Ip внутр.(Пр2ВК) (инт.18)'
    Itf_name: str = 'Itf (2TF)(инт.23)'
    NBI1_name: str = 'Emission electrode current'

    def __init__(self, shotn: int):
        self.result = {
            'shotn': shotn
        }
        filename = Path('%s%05d%s' % (sht_path, shotn, sht_ext))
        if not filename.exists():
            self.result['err'] = 'shot %d does not exist\n' % shotn
            return
        self.sht = shtRipper.ripper.read(filename)

        if not self.scan_ip():
            return

        if not self.scan_Bt():
            return

        if not self.scan_NBI1():
            return

    def scan_ip(self) -> bool:
        breakdown_threshold = 10e3  # A
        flattop_range: float = 0.8  # from maximum

        start_ind: int = 0
        stop_ind: int = 0

        ip_x, ip_y = downsample(x=self.sht[self.Ip_name]['x'], y=self.sht[self.Ip_name]['y'], scale=100)

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
                if flat_start_ind == 0:
                    flat_start_ind = ind

            else:
                if flat_start_ind != 0:
                    flat_stop_ind = ind
                    break
        self.result.update({
            'T_start': ip_x[start_ind],
            'T_stop': ip_x[stop_ind],
            'T_max': ip_x[max_ind],
            'Ip_max': ip_y[max_ind] / c.Unit.k,
            'T_flattop_start': ip_x[flat_start_ind],
            'T_flattop_stop': ip_x[flat_stop_ind],
            'Ip': sum(ip_y[flat_start_ind: flat_stop_ind]) / c.Unit.k / (flat_stop_ind - flat_start_ind),
            'flattop_start_ind': time_to_ind(ip_x[flat_start_ind]),
            'flattop_stop_ind': time_to_ind(ip_x[flat_stop_ind])
        })
        return True

    def scan_Bt(self):
        Itf_to_Bt: float = 0.9e-5
        freq_reduction = 10
        self.result['Bt'] = Itf_to_Bt * sum(self.sht[self.Itf_name]['y'][self.result['flattop_start_ind'] // freq_reduction: self.result['flattop_stop_ind'] // freq_reduction]) / \
                            (self.result['flattop_stop_ind'] // freq_reduction - self.result['flattop_start_ind'] // freq_reduction)
        return True

    def scan_NBI1(self):
        freq_reduction = 10
        scale = 1000
        threshold = 0.5

        flattop_start_ind = self.result['flattop_start_ind'] // (freq_reduction * scale)
        flattop_stop_ind = self.result['flattop_stop_ind'] // (freq_reduction * scale)
        x, y = downsample(x=self.sht[self.NBI1_name]['x'], y=self.sht[self.NBI1_name]['y'], scale=scale)
        start_ind: int = -1
        stop_ind: int = -1
        for i in range(flattop_start_ind, flattop_stop_ind):
            if y[i] > threshold and start_ind < 0:
                start_ind = i
            if y[i] > self.result['T_flattop_stop']:
                stop_ind = i - 1
                break

        return True

for shotn in range(start_shotn, stop_shotn):
    current = Shot(shotn=shotn)
    print(current.result)
    break

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