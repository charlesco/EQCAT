import os
import re
import pandas as pd
from attenuation import mercalli


def weighted_average(df, data_col, weight_col, by_col=''):
    df['_data_times_weight'] = df[data_col] * df[weight_col]
    df['_weight_where_notnull'] = df[weight_col] * pd.notnull(df[data_col])
    if by_col != '':
        somme = df[['_data_times_weight', weight_col, by_col]].groupby(by_col).sum()
    else:
        somme = df[['_data_times_weight', weight_col]].sum()
    result = somme['_data_times_weight'] / somme[weight_col]
    del df['_data_times_weight'], df['_weight_where_notnull']
    return result


def select_aggreg_cols(cols):
    residential = []
    count_cols = ['bldg_cost']
    prob_cols = []
    for col in cols:
        if re.search(r'count|Fatalities|pop', col):
            count_cols += [col]
        if re.search(r'residential', col) and re.search(r'prob|Fatality_rate', col):
            residential += [col]
        elif re.search(r'prob|Fatality_rate', col):
            prob_cols += [col]
    return residential, count_cols, prob_cols


def aggregate_sites(buildings, historical=False):
    _, count_cols, prob_cols = select_aggreg_cols(list(buildings))
    if historical:
        sites = buildings[['grid_id', 'lat', 'lon', 'pref_id', 'pref_name', 'JCODE', 'AVS', 'AmpPGA', 'AmpPGV',
                           'PGA (g)']].drop_duplicates().copy()
        sites = mercalli(sites)
    else:
        sites = buildings[['grid_id', 'lat', 'lon', 'pref_id', 'pref_name', 'distance', 'JCODE', 'AVS', 'AmpPGA',
                           'AmpPGV', 'PGAb', 'PGVb', 'PGAbg', 'PGA (cm/s2)', 'PGV (cm/s)', 'PGA (g)', 'MMI', 'MMI_num',
                           'JMA']].drop_duplicates().copy()
    sites.set_index('grid_id', inplace=True)
    sums = buildings.groupby('grid_id')[count_cols].sum()
    for col in count_cols:
        sums[col] = sums[col]
    sites = sites.merge(sums, left_index=True, right_index=True)
    for col in prob_cols:
        probs = weighted_average(buildings, col, 'type_pop', 'grid_id')
        sites[col] = probs
    for col in prob_cols:
        probs = weighted_average(buildings, col, 'bldg_count', 'grid_id')
        sites[col + '_residential'] = probs
    print('Total : ', sites.shape[0], ' sites')
    return sites


def aggregate_pref(sites):
    res_cols, count_cols, prob_cols = select_aggreg_cols(list(sites))
    prefs = sites[['pref_id']].drop_duplicates()
    prefs.set_index('pref_id', inplace=True)
    sums = sites.groupby('pref_id')[count_cols].sum()
    intensity_list = ['V', 'VI', 'VII', 'VIII', 'IX', 'X']
    time_list = ['day', 'night', 'transit']
    for t in time_list:
        for i in intensity_list:
            sums[t + '_pop_' + i] = sites.loc[sites['MMI'] == i, t + '_pop'].sum()
    prefs = prefs.merge(sums, left_index=True, right_index=True)
    for col in prob_cols:
        probs = weighted_average(sites, col, 'type_pop', 'pref_id')
        prefs[col] = probs
    for col in res_cols:
        probs = weighted_average(sites, col, 'bldg_count', 'pref_id')
        prefs[col] = probs
    print('Total : ', prefs.shape[0], ' prefectures')
    return prefs


def aggregate_bldg_type(sites):
    res_cols, count_cols, prob_cols = select_aggreg_cols(list(sites))
    types = sites[['bldg_type', 'occ_type']].drop_duplicates()
    types.set_index(['bldg_type', 'occ_type'], inplace=True)
    sums = sites.groupby(['bldg_type', 'occ_type'])[count_cols].sum()
    types = types.merge(sums, left_index=True, right_index=True)
    for col in prob_cols:
        probs = weighted_average(sites, col, 'type_pop', 'bldg_type')
        types[col] = probs
    for col in res_cols:
        probs = weighted_average(sites, col, 'bldg_count', 'bldg_type')
        types[col] = probs
    print('Total : ', types.shape[0], ' building types * occupancy')
    return types


def aggregate_all(prefs):
    res_cols, count_cols, prob_cols = select_aggreg_cols(list(prefs))
    sums = prefs[count_cols].sum()
    for col in prob_cols:
        probs = weighted_average(prefs, col, 'type_pop')
        sums[col] = probs
    for col in res_cols:
        probs = weighted_average(prefs, col, 'bldg_count')
        sums[col] = probs
    return sums


def outputs(buildings, dir_name, historical=False):
    # buildings = buildings.loc[buildings['PGA (g)'] > [0.0039]]
    if not os.path.isdir(dir_name):
        os.makedirs(dir_name)
    # print('Total : ', buildings.shape[0], ' buildings')
    # buildings.to_csv(dir_name + '/buildings.csv', index=False)
    sites = aggregate_sites(buildings, historical)
    # sites.to_csv(dir_name + '/sites.csv')
    prefs = aggregate_pref(sites)
    prefs.to_csv(dir_name + '/prefectures.csv')
    # types = aggregate_bldg_type(buildings)
    # types.to_csv(dir_name + '/building_types.csv')
    out = aggregate_all(prefs)
    out = pd.DataFrame([out.transpose()])
    return out
