from __future__ import division
import os
import pandas as pd
from EQCAT.sites import collect_exposure
from EQCAT.attenuation import ground_motion, felt_distance
from EQCAT.vulnerability import consequences

results_path = "../08-Results/"
events_reports_path = "02-Events Reports/"
simulation_reports_path = "03-Simulation Reports/"


class Earthquake(object):
    def __init__(self, code, name, eqtype, crtype):
        self.code = code
        self.name = name
        self.eqtype = eqtype
        self.crtype = crtype


class SegmentEarthquake(Earthquake):
    def __init__(self, dico):
        super(self.__class__, self).__init__(dico['code'], dico['name'], dico['eqtype'], dico['correction'])
        self.proc = dico['process']
        self.mag = dico['mag']
        self.shape = dico['shape']

    def events(self, time_lapse, mag_step):
        proba = self.proc.occ_proba(time_lapse)
        mag_probs = self.mag.mag_probs(mag_step)
        return pd.DataFrame({'Code': [self.code for i in range(len(mag_probs))],
                             'Magnitude': [mag_probs[i][0] for i in range(len(mag_probs))],
                             'Proba': [proba * mag_probs[i][1] for i in range(len(mag_probs))],
                             'Shape': [self.shape.desc() for i in range(len(mag_probs))]})

    def sesm(self, time_lapse, min_pga=0.039):
        mag_probs = self.mag.mag_probs()
        max_mag = mag_probs[-1][0]
        radius = felt_distance(self.shape.depth, max_mag, self.eqtype, min_pga)
        print('Radius : ', radius)
        buildings, sites = collect_exposure(self.shape, radius)
        summary = pd.DataFrame()
        if not sites.empty:
            proba = self.proc.occ_proba(time_lapse)
            for mag, p in mag_probs:
                sites2 = ground_motion(sites, mag, self.eqtype)
                buildings2 = buildings.merge(sites2, how='right', on=['grid_id', 'lat', 'lon'])
                df = consequences(self.code, buildings2)
                df['Proba'] = p
                df['Mag'] = mag
                summary = summary.append(df)
            if not summary.empty:
                summary['Code'] = self.code
                summary['Proba'] = summary['Proba'] * proba
            summary.to_csv(results_path + simulation_reports_path + '/Instrumental/' + self.code + '/summary.csv',
                           index=False)
        return summary


class MultiSegmentEarthquake(Earthquake):
    def __init__(self, dico):
        super(self.__class__, self).__init__(dico['code'], dico['name'], dico['eqtype'], dico['correction'])
        self.mag = dico['mag']
        self.shape = dico['shape']
        self.proc = dico['process']
        self.segments = dico['segments']

    def events(self, time_lapse, mag_step):
        proba = self.proc.occ_proba(time_lapse)
        mag_probs = self.mag.mag_probs(mag_step)
        return pd.DataFrame({'Code': [self.code for i in range(len(mag_probs))],
                             'Magnitude': [mag_probs[i][0] for i in range(len(mag_probs))],
                             'Proba': [proba * mag_probs[i][1] for i in range(len(mag_probs))],
                             'Shape': [self.shape.desc() for i in range(len(mag_probs))]})

    def sesm(self, time_lapse, min_pga=0.039):
        mag_probs = self.mag.mag_probs()
        max_mag = mag_probs[-1][0]
        radius = felt_distance(self.shape.depth, max_mag, self.eqtype, min_pga)
        print('Radius : ', radius)
        buildings, sites = collect_exposure(self.shape, radius)
        summary = pd.DataFrame()
        if not sites.empty:
            proba = 1
            for quake in self.segments:
                proba = proba * quake.proc.occ_proba(time_lapse)
            for mag, p in mag_probs:
                sites2 = ground_motion(sites, mag, self.eqtype)
                buildings2 = buildings.merge(sites2, how='right', on=['grid_id', 'lat', 'lon'])
                df = consequences(self.code, buildings2)
                df['Proba'] = p
                df['Mag'] = mag
                summary = summary.append(df)
            if not summary.empty:
                summary['Code'] = self.code
                summary['Proba'] = summary['Proba'] * proba
            summary.to_csv(results_path + simulation_reports_path + '/Instrumental/' + self.code + '/summary.csv',
                           index=False)
        return summary


class PointsEarthquake(Earthquake):
    def __init__(self, dico):
        super(self.__class__, self).__init__(dico['code'], dico['name'], dico['eqtype'], dico['correction'])
        self.mag = dico['mag']
        self.shape = dico['shape']
        self.proc = dico['process']
        if self.proc == 'multi':
            self.segments = dico['segments']

    def events(self, time_lapse, mag_step):
        proba = self.proc.occ_proba(time_lapse)
        mag_probs = self.mag.mag_probs(mag_step)
        return pd.DataFrame({'Code': [self.code for i in range(len(mag_probs))],
                             'Magnitude': [mag_probs[i][0] for i in range(len(mag_probs))],
                             'Proba': [proba * mag_probs[i][1] for i in range(len(mag_probs))],
                             'Shape': [self.shape.desc() for i in range(len(mag_probs))]})

    def sesm(self, time_lapse, min_pga=0.039):
        mag_probs = self.mag.mag_probs()
        max_mag = mag_probs[-1][0]
        radius = felt_distance(self.shape.depth, max_mag, self.eqtype, min_pga)
        print('Radius : ', radius)
        buildings, sites = collect_exposure(self.shape, radius)
        summary = pd.DataFrame()
        if not sites.empty:
            proba = self.proc.occ_proba(time_lapse)
            for mag, p in mag_probs:
                sites2 = ground_motion(sites, mag, self.eqtype)
                buildings2 = buildings.merge(sites2, how='right', on=['grid_id', 'lat', 'lon'])
                df = consequences(self.code, buildings2)
                df['Proba'] = p
                df['Mag'] = mag
                summary = summary.append(df)
            if not summary.empty:
                summary['Code'] = self.code
                summary['Proba'] = summary['Proba'] * proba
            summary.to_csv(results_path + simulation_reports_path + '/Instrumental/' + self.code + '/summary.csv',
                           index=False)
        return summary


class MultiPointsEarthquake(Earthquake):
    def __init__(self, dico):
        super(self.__class__, self).__init__(dico['code'], dico['name'], dico['eqtype'], dico['correction'])
        self.quakes = dico['earthquakes']
        self.proc = dico['process']
        self.mag = None
        self.shape = None

    def events(self, time_lapse, mag_step):
        out = []
        for quake in self.quakes.values():
            out += [quake.events(time_lapse, mag_step)]
        out = pd.concat(out)
        out['Code'] = self.code + '_' + out['Code']
        out['Proba'] = self.proc.occ_proba(time_lapse) / len(self.quakes)
        return out

    def sesm(self, time_lapse, min_pga=0.039):
        summary = pd.DataFrame()
        proba = self.proc.occ_proba(time_lapse)
        for q in self.quakes:
            q = self.quakes[q]
            print(q.code, q, q.proc, q.mag, q.shape)
            out = q.sesm(time_lapse, min_pga)
            out['Code'] = self.code + '_' + out['Code']
            summary = summary.append(out)
        if not summary.empty:
            summary['Proba'] = proba / len(self.quakes)
            dir_name = results_path + simulation_reports_path + '/Instrumental/' + self.code
            if not os.path.isdir(dir_name):
                os.makedirs(dir_name)
            summary.to_csv(dir_name + '/summary.csv', index=False)
        return summary


class DomainEarthquake(Earthquake):
    def __init__(self, dico):
        super(self.__class__, self).__init__(dico['code'], dico['name'], dico['eqtype'], dico['correction'])
        self.mag = dico['mag']
        self.dom_dict = dico['shape']
        self.proc = dico['process']
        self.shape = None
        self.curr_mag = None

    def sesm(self, time_lapse, min_pga=0.039):
        summary = pd.DataFrame()
        proba = self.proc.occ_proba(time_lapse)
        for mag, p, dom_id in self.mag.mag_probs():
            self.curr_mag = mag
            summary2 = pd.DataFrame()
            domain = self.dom_dict[dom_id]
            for plane in domain.shape_list:
                self.shape = plane
                radius = felt_distance(self.shape.depth, mag, self.eqtype, min_pga)
                print('Radius : ', radius)
                buildings, sites = collect_exposure(self.shape, radius)
                if not sites.empty:
                    sites = ground_motion(sites, self.curr_mag, self.eqtype)
                    buildings = buildings.merge(sites, how='right', on=['grid_id', 'lat', 'lon'])
                    df = consequences(self.code, buildings)
                    df['Code'] = self.code + '_' + str(dom_id) + '_' + plane.id
                    df['Proba'] = 1 / float(len(domain.shape_list))
                    df['Mag'] = mag
                    summary2 = summary2.append(df)
            if not summary2.empty:
                summary2['Proba'] = summary2['Proba'] * p
                summary = summary.append(summary2)
        if not summary.empty:
            summary['Proba'] = summary['Proba'] * proba
            summary.to_csv(results_path + simulation_reports_path + '/Instrumental/' + self.code + '/summary.csv',
                           index=False)
        return summary


class ZoneEarthquake(Earthquake):
    def __init__(self, dico):
        super(self.__class__, self).__init__(dico['code'], dico['name'], dico['eqtype'], dico['correction'])
        self.proc = dico['process']
        self.mag = dico['mag']
        self.shape = dico['shape']

    def sesm(self, time_lapse, min_pga=0.039):
        mag_probs = self.mag.mag_probs()
        max_mag = mag_probs[-1][0]
        radius = felt_distance(self.shape.depth, max_mag, self.eqtype, min_pga)
        buildings, sites = collect_exposure(self.shape, radius)
        summary = pd.DataFrame()
        if not sites.empty:
            proba = self.proc.occ_proba(time_lapse)
            for mag, p in mag_probs:
                sites = ground_motion(sites, mag, self.eqtype)
                buildings = buildings.merge(sites, how='right', on=['grid_id', 'lat', 'lon'])
                df = consequences(self.code, buildings)
                df['Proba'] = p
                df['Mag'] = mag
                summary = summary.append(df)
            if not summary.empty:
                summary['Code'] = self.code
                summary['Proba'] = summary['Proba'] * proba
                summary.to_csv(results_path + simulation_reports_path + '/Instrumental/' + self.code + '/summary.csv',
                               index=False)
        return summary


class HypoEarthquake(object):
    def __init__(self, dico):
        self.code = dico['code']
        self.mag = dico['mag']
        self.shape = dico['shape']
        self.eqtype = dico['type']

    def sesm(self, min_pga=0.039):
        mag_probs = self.mag.mag_probs()
        max_mag = mag_probs[-1][0]
        radius = felt_distance(self.shape.depth, max_mag, self.eqtype, min_pga)
        print('Radius : ', radius)
        buildings, sites = collect_exposure(self.shape, radius)
        summary = pd.DataFrame()
        if not sites.empty:
            for mag, p in mag_probs:
                sites2 = ground_motion(sites, mag, self.eqtype)
                buildings2 = buildings.merge(sites2, how='right', on=['grid_id', 'lat', 'lon'])
                df = consequences(self.code, buildings2)
                df['Mag'] = mag
                summary = summary.append(df)
            if not summary.empty:
                summary['Code'] = self.code
            summary.to_csv(results_path + simulation_reports_path + '/Instrumental/' + self.code + '/summary.csv',
                           index=False)
        return summary
