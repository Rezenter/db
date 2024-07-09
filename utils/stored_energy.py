import math

import phys_const as const
import utils.CurrentCoils as ccm
import copy

r_step = 0.5  # cm


def interpol(x_prev, x, x_next, y_prev, y_next):
    return y_prev + (y_next - y_prev) * (x - x_prev) / (x_next - x_prev)


class StoredCalculator:
    def __init__(self, shotn, ts_data, shift: float=999):
        self.ccm_data = ccm.CCM(shotn=shotn, shift=shift)
        self.error = self.ccm_data.error
        if self.error is not None:
            return
        self.ts_data = ts_data
        self.polys = []
        for poly in ts_data['config']['poly']:
            self.polys.append({
                'ind': poly['ind'],
                'R': poly['R'] * 0.1
            })

    def get_profile(self, surfaces, coordinate, is_vertical=True):
        profile = []
        not_used_surfaces = []
        for surf_ind in range(len(surfaces)):
            surf = surfaces[surf_ind]
            if is_vertical:
                key = 'r'
                sort_key = 'z'
            else:
                key = 'z'
                sort_key = 'r'

            if surf['%s_min' % key] == coordinate == surf['%s_max' % key]:
                profile.append({
                    'r': surf['r'],
                    'z': surf['z'],
                    'surf_ind': surf_ind,
                    'Te': surf['Te'],
                    'ne': surf['ne'],
                    'Te_err': surf['Te_err'],
                    'ne_err': surf['ne_err']
                })
            elif surf['%s_min' % key] <= coordinate <= surf['%s_max' % key]:
                for index in range(len(surf[key]) - 1):
                    if (surf[key][index] - coordinate) * (surf[key][index + 1] - coordinate) <= 0:
                        ne = surf['ne']
                        ne_err = surf['ne_err']
                        profile.append({
                            'r': surf['r'][index],
                            'z': surf['z'][index],
                            'surf_ind': surf_ind,
                            'Te': surf['Te'],
                            'ne': ne,
                            'Te_err': surf['Te_err'],
                            'ne_err': ne_err
                        })
            else:
                not_used_surfaces.append(surf_ind)
        return sorted(profile, key=lambda point: point[sort_key], reverse=True)  # debug
        # unreacheble: Not implemented yet
        fuck

        closest_ind = not_used_surfaces[0]
        for surf_ind in not_used_surfaces:
            if surfaces[surf_ind]['r_min'] - coordinate < surfaces[closest_ind]['r_min'] - coordinate or \
               coordinate - surfaces[surf_ind]['r_max'] < coordinate - surfaces[closest_ind]['r_max']:
                closest_ind = surf_ind

        surf = surfaces[closest_ind]
        if surf['a'] != 0:
            for index in range(len(surf['r']) - 1):
                if (coordinate < surf['r_min'] and surf['r'][index] == surf['r_min']) or \
                        (coordinate > surf['r_max'] and surf['r'][index] == surf['r_max']):
                    profile.append({
                        'z': surf['z'][index],
                        'surf_ind': closest_ind,
                        'val': interpol(),
                        'closest': True
                    })
        else:
            profile.append({
                'z': surf['z'],
                'surf_ind': closest_ind,
                'val': 0,  # interpolated value
                'closest': True
            })

        return sorted(profile, key=lambda point: point['z'], reverse=True)

    def integrate(self, surfaces, nl_r=42):
        area = 0
        volume = 0
        w = 0
        w_err = 0
        nl_prof = []
        equator_prof = []
        nl_val = 0
        nl_err = 0
        nl_eq = 0
        nl_eq_err = 0
        t_ave = 0
        t_ave_err = 0
        n_ave = 0
        n_ave_err = 0
        pressure = []
        equator = []
        if len(surfaces) != 0:
            radius = surfaces[0]['r_min']
            while radius < surfaces[0]['r_max']:
                l_prof = self.get_profile(surfaces, radius, is_vertical=True)
                pressure.append({
                    'R': radius,
                    'vertical': l_prof
                })
                if 0 <= radius - nl_r < r_step:
                    nl_prof = l_prof
                    for point_ind in range(len(l_prof) - 1):
                        dz = l_prof[point_ind]['z'] - l_prof[point_ind + 1]['z']
                        n_curr = (l_prof[point_ind]['ne'] + l_prof[point_ind + 1]['ne']) * 0.5
                        nl_val += dz * n_curr
                        nl_err += dz * (l_prof[point_ind]['ne_err'] + l_prof[point_ind + 1]['ne_err']) * 0.5
                for point_ind in range(len(l_prof) - 1):
                    dz = l_prof[point_ind]['z'] - l_prof[point_ind + 1]['z']
                    n_curr = (l_prof[point_ind]['ne'] + l_prof[point_ind + 1]['ne']) * 0.5
                    t_curr = (l_prof[point_ind]['Te'] + l_prof[point_ind + 1]['Te']) * 0.5
                    n_curr_err = (l_prof[point_ind]['ne_err'] + l_prof[point_ind + 1]['ne_err']) * 0.5
                    t_curr_err = (l_prof[point_ind]['Te_err'] + l_prof[point_ind + 1]['Te_err']) * 0.5
                    if t_curr == 0:
                        rel_t = 1
                    else:
                        rel_t = t_curr_err / t_curr
                    if n_curr == 0:
                        rel_n = 1
                    else:
                        rel_n = n_curr_err / n_curr
                    area += dz
                    volume += dz * radius
                    w += dz * n_curr * t_curr * radius
                    w_err += dz * n_curr * t_curr * radius * math.sqrt(math.pow(rel_t, 2) + math.pow(rel_n, 2))
                    t_ave += dz * t_curr * radius
                    t_ave_err += dz * t_curr_err * radius
                    n_ave += dz * n_curr * radius
                    n_ave_err += dz * n_curr_err * radius
                radius += r_step


            coordinate: float = 0.0
            equator_prof = self.get_profile(surfaces, coordinate, is_vertical=False)
            equator.append(equator_prof)
            stop_ind = 0
            for point_ind in range(len(equator_prof)):
                if equator_prof[point_ind]['r'] > 17:
                    equator_prof[point_ind]['l'] = math.sqrt(math.pow(equator_prof[point_ind]['r'], 2) - (17 * 17))
                    stop_ind = point_ind
            if len(equator_prof) > stop_ind:
                dl = equator_prof[stop_ind]['l']
                nl_eq += dl * equator_prof[stop_ind]['ne']
                nl_eq_err += dl * equator_prof[stop_ind]['ne_err']
            for point_ind in range(stop_ind - 1):
                if equator_prof[point_ind]['r'] > 17:
                    dl = equator_prof[point_ind]['l'] - equator_prof[point_ind + 1]['l']
                    nl_eq += dl * (equator_prof[point_ind]['ne'] + equator_prof[point_ind + 1]['ne']) * 0.5
                    nl_eq_err += dl * (equator_prof[point_ind]['ne_err'] + equator_prof[point_ind + 1]['ne_err']) * 0.5

        final_vol = volume * 1e-6 * r_step * math.tau
        if final_vol != 0:
            t_ave /= final_vol
            n_ave /= final_vol
            t_ave_err /= final_vol
            n_ave_err /= final_vol
        return {
            'area': r_step * area * 1e-4,
            'volume': final_vol,
            'vol_w': w * 1e-6 * const.q_e * r_step * math.tau * 1.5,
            'w_err': w_err * 1e-6 * const.q_e * r_step * math.tau * 1.5,
            'nl_prof': nl_prof,
            'eq_prof': equator_prof,
            'nl_val': nl_val * 1e-2,
            'nl_err': nl_err * 1e-2,
            'nl_eq': nl_eq * 1e-2 * 2,
            'nl_eq_err': nl_eq_err * 1e-2 * 2,
            't_vol': t_ave * r_step * 1e-6 * math.tau,
            't_vol_err': t_ave_err * r_step * 1e-6 * math.tau,
            'n_vol': n_ave * r_step * 1e-6 * math.tau,
            'n_vol_err': n_ave_err * r_step * 1e-6 * math.tau,
            'pressure': pressure,
            'equator': equator,
            'Pe_vol': w * 1e-6 * const.q_e * r_step * math.tau / final_vol
        }

    def calc_laser_shot(self, requested_time, nl_r=42, shaf_shift=999):
        t_ind = 0
        for t_ind in range(len(self.ccm_data.timestamps) - 1):
            if self.ccm_data.timestamps[t_ind] <= requested_time < self.ccm_data.timestamps[t_ind + 1]:
                if (requested_time - self.ccm_data.timestamps[t_ind]) >= (self.ccm_data.timestamps[t_ind + 1] - requested_time):
                    t_ind += 1
                break
        if len(self.ccm_data.data['boundary']['rbdy']['variable'][t_ind]) == 0:
            return {
                'error': 'no boundary'
            }
        for i in range(len(self.ccm_data.data['boundary']['zbdy']['variable'][t_ind])):
            if self.ccm_data.data['boundary']['zbdy']['variable'][t_ind][i] * self.ccm_data.data['boundary']['zbdy']['variable'][t_ind][i - 1] < 0:
                break
        else:
            print('bad plasma: LCFS does not cross equator')
            return {
                'error': 'bad plasma: LCFS does not cross equator'
            }

        self.ccm_data.data['boundary']['rbdy']['variable'][t_ind], self.ccm_data.data['boundary']['zbdy']['variable'][t_ind] = \
            self.ccm_data.clockwise(self.ccm_data.data['boundary']['rbdy']['variable'][t_ind],
                                    self.ccm_data.data['boundary']['zbdy']['variable'][t_ind],
                                    t_ind)

        #print('clockwise')
        poly_a = self.ccm_data.find_poly(self.polys, t_ind)
        #print('poly found')
        if 'error' in poly_a:
            return {
                'error': poly_a['error']
            }
        #for poly in poly_a:
        #    print(poly['a'], poly['Te'], poly['ne'])
        for poly in poly_a:
            if poly['a'] == 0:
                continue
            poly['r_min'] = 60
            poly['r_max'] = 20
            for point in poly['r']:
                poly['r_min'] = min(poly['r_min'], point)
                poly['r_max'] = max(poly['r_max'], point)
            poly['z_min'] = 50
            poly['z_max'] = -50
            for point in poly['z']:
                poly['z_min'] = min(poly['z_min'], point)
                poly['z_max'] = max(poly['z_max'], point)
        integration = self.integrate(poly_a, nl_r)
        return {
            'area': integration['area'],
            'vol': integration['volume'],
            'vol_w': integration['vol_w'],
            'w_err': integration['w_err'],
            'surfaces': poly_a,
            'nl_profile': integration['nl_prof'],
            'nl': integration['nl_val'],
            'nl_err': integration['nl_err'],
            't_vol': integration['t_vol'],
            't_vol_err': integration['t_vol_err'],
            'n_vol': integration['n_vol'],
            'n_vol_err': integration['n_vol_err'],
            'pressure': integration['pressure'],
            'eq_prof': integration['eq_prof'],
            'equator': integration['equator'],
            'nl_eq': integration['nl_eq'],
            'nl_eq_err': integration['nl_eq_err'],
            'Pe_vol': integration['Pe_vol']
        }

    def calc_dynamics(self, t_from, t_to, nl_r=42):
        #print('calc dynamics')
        result = []
        for event_ind in range(1, len(self.ts_data['events'])):
            event = self.ts_data['events'][event_ind]
            if 'error' in event and event['error'] is not None:
                result.append({
                    'event_index': event_ind,
                    'error': event['error']
                })
                continue
            if t_from <= event['timestamp'] <= t_to:
                if event['error'] is not None:
                    print('Laser shot %d = %.1fs skip due to error in ts_data: %s' %
                          (event_ind, event['timestamp'], event['error']))
                    continue
                if not self.ccm_data.timestamps[0] <= event['timestamp'] * 0.001 <= self.ccm_data.timestamps[-1]:
                    print('No ccm data for laser shot %d = %.1fs' % (event_ind, event['timestamp']))
                    continue
                #print('Process event laser shot %d = %.1fs' % (event_ind, event['timestamp']))
                for poly in self.polys:
                    if event['T_e'][poly['ind']]['error']:
                        poly['skip'] = True
                        poly['Te'] = None
                        poly['ne'] = None
                        continue
                    poly['skip'] = False
                    poly['Te'] = event['T_e'][poly['ind']]['T']
                    poly['ne'] = event['T_e'][poly['ind']]['n']
                    poly['Te_err'] = event['T_e'][poly['ind']]['Terr']
                    poly['ne_err'] = event['T_e'][poly['ind']]['n_err']
                #print('calc dynamics', event['timestamp'])
                data = copy.deepcopy(self.calc_laser_shot(event['timestamp'] * 0.001, nl_r))
                if 'error' in data:
                    result.append({
                        'event_index': event_ind,
                        'error': data['error']
                    })
                else:
                    result.append({
                        'event_index': event_ind,
                        'data': data
                    })
        return {
            'ok': True,
            'data': result
        }
