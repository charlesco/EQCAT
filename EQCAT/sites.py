from __future__ import division
import pandas as pd
import os
from geography import fmesh_distance, quarter_meshcode, prefecture
from attenuation import amp_factors

nb_sites_max = 50000

def collect_exposure(shape, radius):
    file_names = os.listdir('Exposure/')
    buildings = pd.DataFrame()
    sites = pd.DataFrame()
    for name in file_names:
        fcode = name.split('.')[0]
        if fmesh_distance(fcode, shape, radius):
            exposure = pd.read_csv('Exposure/' + name)
            positions = exposure[['grid_id', 'lat', 'lon', 'AmpPGA', 'AmpPGV']].drop_duplicates()
            positions = positions.loc[([shape.lat - radius / 111.195] < positions['lat']) &
                                      (positions['lat'] < [shape.lat + radius / 111.195]) &
                                      ([shape.lon - radius / 65.265] < positions['lon']) &
                                      (positions['lon'] < [shape.lon + radius / 65.265])]
            if not positions.empty:
                dists = positions.apply(shape.distance2, axis=1)
                positions = positions.merge(dists, left_index=True, right_index=True)
                positions = positions.loc[positions['distance'] <= radius]
                if not positions.empty:
                    print('Nb Sites : ', positions.shape[0])
                    sites = sites.append(positions)
                    buildings = buildings.append(exposure)
                    # break
                    # if sites.shape[0] > nb_sites_max:
                        # break
    if not sites.empty:
        to_del_cols = ['bldg_area', 'AmpPGV', 'AmpPGA']
        for col in to_del_cols:
            del buildings[col]
        if sites.shape[0] > nb_sites_max:
            sites.sort_values(by='distance', inplace=True)
            sites = sites.iloc[0:nb_sites_max]
    return buildings, sites

# Preparation of exposure
def collect_site_effects(name, positions):
    fcode = name.split('.')[0]
    name = 'Z-V3-JAPAN-AMP-VS400_M250-' + fcode
    site_effects = pd.read_csv('site_effects/' + name + '/' + name + '.csv', skiprows=6, skipinitialspace=True)
    site_effects.rename(columns={'# CODE': 'qcode'}, inplace=True)
    amp = site_effects.apply(amp_factors, axis=1)
    site_effects = site_effects.merge(amp, left_index=True, right_index=True)
    meshcode = positions.apply(quarter_meshcode, axis=1)
    positions = positions.merge(meshcode, left_index=True, right_index=True)
    positions = positions.merge(site_effects, on='qcode', how='inner')
    print('Site Effects : OK')
    return positions


def assign_prefectures(positions):
    prefs = positions.apply(prefecture, axis=1)
    positions = positions.merge(prefs, left_index=True, right_index=True)
    print('Prefectures : OK')
    return positions


def prepare_exposure():
    file_names = os.listdir('Exposure/')
    for name in file_names:
        if not name.endswith('.csv'):
            file_names.remove(name)
    for name in file_names:
        exposure = pd.read_csv('Exposure/' + name)
        if not exposure.empty:
            del exposure['ARV'], exposure['pref_id']
            positions = exposure[['grid_id', 'lon', 'lat']].drop_duplicates()
            positions = collect_site_effects(name, positions)
            positions = assign_prefectures(positions)
            del positions['lon'], positions['lat']
            exposure = exposure.merge(positions, on='grid_id')
            exposure.to_csv('Exposure/' + name, index=False)
# prepare_exposure()
