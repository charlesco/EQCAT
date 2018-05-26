from __future__ import division
from functools import partial
import pandas as pd
import os
from geography import fmesh_distance, quarter_meshcode, prefecture, load_prefs
from attenuation import amp_factors

nb_sites_max = 50000
exposure_path = '../04-Exposure/'
gem_path = 'GEM/'
site_effects_path = '../02-Site Effects/'


def collect_exposure(shape, radius):
    file_names = os.listdir(exposure_path + gem_path)
    buildings = pd.DataFrame()
    sites = pd.DataFrame()
    for name in file_names:
        fcode = name.split('.')[0]
        if fmesh_distance(fcode, shape, radius):
            exposure = pd.read_csv(exposure_path + gem_path + name)
            positions = exposure[['grid_id', 'lat', 'lon', 'AmpPGA', 'AmpPGV']].drop_duplicates()
            positions = positions.loc[([shape.lat - radius / shape.lat_km] < positions['lat']) &
                                      (positions['lat'] < [shape.lat + radius / shape.lat_km]) &
                                      ([shape.lon - radius / shape.lon_km] < positions['lon']) &
                                      (positions['lon'] < [shape.lon + radius / shape.lon_km])]
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
    site_effects = pd.read_csv(site_effects_path + name + '/' + name + '.csv', skiprows=6, skipinitialspace=True)
    site_effects.rename(columns={'# CODE': 'qcode'}, inplace=True)
    amp = site_effects.apply(amp_factors, axis=1)
    site_effects = site_effects.merge(amp, left_index=True, right_index=True)
    meshcode = positions.apply(quarter_meshcode, axis=1)
    positions = positions.merge(meshcode, left_index=True, right_index=True)
    positions = positions.merge(site_effects, on='qcode', how='inner')
    print('Site Effects : OK')
    return positions


def assign_prefectures(positions):
    prefecture2 = partial(prefecture, pref_df=load_prefs())
    prefs = positions.apply(prefecture2, axis=1)
    positions = positions.merge(prefs, left_index=True, right_index=True)
    print('Prefectures : OK')
    return positions


def prepare_exposure():
    file_names = os.listdir(exposure_path + gem_path)
    for name in file_names:
        if not name.endswith('.csv'):
            file_names.remove(name)
    for name in file_names:
        exposure = pd.read_csv(exposure_path + gem_path + name)
        if not exposure.empty:
            del exposure['ARV'], exposure['pref_id']
            positions = exposure[['grid_id', 'lon', 'lat']].drop_duplicates()
            positions = collect_site_effects(name, positions)
            positions = assign_prefectures(positions)
            del positions['lon'], positions['lat']
            exposure = exposure.merge(positions, on='grid_id')
            exposure.to_csv(exposure_path + gem_path + name, index=False)
# prepare_exposure()
