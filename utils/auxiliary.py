import json
import math
from pathlib import Path
import phys_const  # at least v1.3
from datetime import date
import statistics

DB_PATH: str = '\\\\172.16.12.130\\d\\data\\db\\'
FIBER_FOLDER: str = 'fibers/calculated/'
FILTER_FOLDER = 'filters/'
APD_FOLDER = 'apd/'
JSON: str = '.json'
CSV: str = '.csv'
CONFIG_FOLDER: str = 'config/'
CALIBRATION_FOLDER: str = 'calibration/'
SPECTRAL_FOLDER: str = 'spectral/'
LAMP: str = 'lamp/Lab_spectrum.txt'
EXPECTED_FOLDER: str = 'expected/'


class Filters:
    def __init__(self, filter_set: str):
        self.trans = []
        self.name: str = filter_set
        for ch_filename in Path('%s%s%s/' % (DB_PATH, FILTER_FOLDER, filter_set)).iterdir():
            filter = {
                't': [],
                'wl': []
            }
            #print(ch_filename)
            with open(ch_filename, 'r') as filter_file:
                for line in filter_file:
                    splitted = line.split(',')
                    filter['wl'].append(float(splitted[0]))
                    filter['t'].append(0.01 * float(splitted[1]))
                if filter['wl'][0] > filter['wl'][-1]:
                    filter['wl'].reverse()
                    filter['t'].reverse()
            self.trans.append(filter)

    def dump(self):
        with open('%s.csv' % self.name, 'w') as file:
            wl = 700
            file.write('wl, ch1, ch2, ch3, ch4, ch5\n')
            while wl < 1070:
                line = '%.1f, ' % wl
                for ch in range(5):
                    line += '%.3e, ' % self.transmission_nm(ch + 1, wl)
                file.write(line[:-2] + '\n')
                wl += 0.1
        print('filters written to file')

    def transmission_nm(self, ch: int, wl: float) -> float:  # whole polychromator
        if wl >= self.trans[ch - 1]['wl'][-1] or wl <= self.trans[ch - 1]['wl'][0]:
            return 0.0
        res: float = 1
        curr: int = 1
        while curr != ch:
            if wl >= self.trans[curr - 1]['wl'][-1] or wl <= self.trans[curr - 1]['wl'][0]:
                prev: float = 0.0
            else:
                prev: float = max(0.0, phys_const.interpolate_arr(self.trans[curr - 1]['wl'], self.trans[curr - 1]['t'], wl))
            res *= 1 - prev
            curr += 1
        return max(0.0, res * phys_const.interpolate_arr(self.trans[ch - 1]['wl'], self.trans[ch - 1]['t'], wl))

    def transmission(self, ch: int, wl_m: float) -> float:
        return self.transmission_nm(ch=ch, wl=wl_m*1e9)

class APD:
    mult: float = 0.01 * phys_const.h * phys_const.c / phys_const.q_e

    def __init__(self, apd_name: str):
        self.apd = {
                'wl': [],
                'aw': []
            }
        with open('%s%s%s/aw.csv' % (DB_PATH, APD_FOLDER, apd_name), 'r') as filter_file:
            for header in range(2):
                filter_file.readline()

            for line in filter_file:
                splitted = line.split(',')
                self.apd['wl'].append(float(splitted[0]))
                self.apd['aw'].append(float(splitted[1]))

    def qe(self, wl_m: float) -> float:
        return self.aw(wl_m=wl_m) * self.mult / wl_m

    def aw_nm(self, wl_nm: float) -> float:
        return phys_const.interpolate_arr(self.apd['wl'], self.apd['aw'], wl_nm)

    def aw(self, wl_m: float) -> float:
        return self.aw_nm(wl_nm=wl_m * 1e9)
