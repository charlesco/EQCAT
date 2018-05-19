from __future__ import division, print_function
import os
import re
import numpy as np
import pandas as pd
from parse_files import parse_quakes
from magnitude import CharacteristicMag
from shape import PointShape
from earthquake import HypoEarthquake
from vulnerability import consequences
from geography import first_meshcode
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import statsmodels.api as sm


def decdeg2dms(row):
    dd_lon = row['lon']
    dd_lat = row['lat']
    mnt_lon, sec_lon = divmod(dd_lon * 3600, 60)
    deg_lon, mnt_lon = divmod(mnt_lon, 60)
    mnt_lat, sec_lat = divmod(dd_lat * 3600, 60)
    deg_lat, mnt_lat = divmod(mnt_lat, 60)
    return pd.Series(dict(deg_lon=deg_lon, mnt_lon=mnt_lon, sec_lon=sec_lon, deg_lat=deg_lat, mnt_lat=mnt_lat,
                          sec_lat=sec_lat))


def usgs_consequences(eq_code, pga_min):
    usgs = pd.read_csv('Historical/Shakemaps/' + eq_code + '.csv')
    usgs = usgs.loc[usgs['PGA (g)'] > [pga_min]]
    if 'deg_lon' not in list(usgs):
        degrees = usgs.apply(decdeg2dms, axis=1)
        usgs = usgs.merge(degrees, left_index=True, right_index=True)
        fcodes = usgs.apply(first_meshcode, axis=1)
        usgs = usgs.merge(fcodes, left_index=True, right_index=True)
        usgs.to_csv('Historical/Shakemaps/' + eq_code + '.csv', index=False)
    fcodes = np.unique(usgs['fcode'])
    del usgs['fcode']
    usgs = usgs.groupby(['deg_lon', 'deg_lat', 'mnt_lon', 'mnt_lat']).mean()
    usgs.reset_index(drop=False, inplace=True)
    lat_min, lat_max = np.min(usgs['lat']), np.max(usgs['lat'])
    lon_min, lon_max = np.min(usgs['lon']), np.max(usgs['lon'])
    file_names = os.listdir('Exposure/')
    buildings = pd.DataFrame()
    for fcode in fcodes:
        name = str(fcode) + '.csv'
        if name in file_names:
            exposure = pd.read_csv('Exposure/' + name)
            positions = exposure[['grid_id', 'lat', 'lon']].drop_duplicates()
            positions = positions.loc[(positions['lat'] > [lat_min]) & (positions['lat'] < [lat_max]) &
                                        (positions['lon'] > [lon_min]) & (positions['lon'] < [lon_max])]
            if not positions.empty:
                degrees = positions.apply(decdeg2dms, axis=1)
                positions = positions.merge(degrees, left_index=True, right_index=True)
                positions = positions.merge(usgs, how='left', on=['deg_lon', 'deg_lat', 'mnt_lon', 'mnt_lat'])
                positions = positions.loc[pd.notnull(positions['PGA (g)'])]
                if not positions.empty:
                    exposure = exposure.merge(positions, how='left', on='grid_id')
                    exposure = exposure.loc[pd.notnull(exposure['PGA (g)'])]
                    buildings = buildings.append(exposure)
                    # break
    buildings.reset_index(drop=True, inplace=True)
    summary = consequences(eq_code, buildings, historical=True)
    summary['Code'] = eq_code
    return summary


def historical_fit(pga_min=0.039):
    history = pd.read_csv('Historical/HistoricalsGS.csv', index_col=0)
    quakes = parse_quakes()
    if os.path.isfile('Results/Historical/HistoricalsGS_InHouse.csv'):
        out_inhouse = pd.read_csv('Results/Historical/HistoricalsGS_InHouse.csv')
        out_usgs = pd.read_csv('Results/Historical/HistoricalsGS_USGS.csv')
    else:
        out_inhouse = pd.DataFrame()
        out_usgs = pd.DataFrame()
    bldg_codes = ['High', 'Moderate', 'Low', 'Precode']
    collapse_cols = ['Collapse_count_' + c for c in bldg_codes]
    complete_cols = ['Complete_count_' + c for c in bldg_codes]
    bldg_cols = ['bldg_count', 'bldg_cost']
    intensity_list = ['V', 'VI', 'VII', 'VIII', 'IX', 'X']
    for code, row in history.iterrows():
        print(code)
        if row['EQCode'] in quakes:
            quake = quakes[row['EQCode']]
            quake.code = code
            quake.mag = CharacteristicMag(-row['Mag'])
            summary_inhouse = quake.sesm(1, pga_min)
        else:
            shape = PointShape(0, row['Lon'], row['Lat'], row['Dep'])
            mag = CharacteristicMag(-row['Mag'])
            dico = {'code': code, 'mag': mag, 'shape': shape, 'type': row['Type']}
            quake = HypoEarthquake(dico)
            summary_inhouse = quake.sesm(pga_min)
        summary_inhouse.to_csv('Results/Instrumental/' + code + '/summary.csv', index=False)
        summary_usgs = usgs_consequences(code, pga_min)
        summary_usgs.to_csv('Results/Historical/' + code + '/summary.csv', index=False)
        t = row['Time']
        fatality_cols = ['Fatalities_' + t + '_' + c for c in bldg_codes]
        pop_col = t + '_pop'
        pop_cols = [t + '_pop_' + i for i in intensity_list] + [pop_col]
        summary_inhouse = summary_inhouse[bldg_cols + collapse_cols + complete_cols + pop_cols + fatality_cols]
        summary_usgs = summary_usgs[bldg_cols + collapse_cols + complete_cols + pop_cols + fatality_cols]
        summary_inhouse.rename(columns={pop_col: 'Affected Population'}, inplace=True)
        summary_usgs.rename(columns={pop_col: 'Affected Population'}, inplace=True)
        for c in bldg_codes:
            summary_inhouse.rename(columns={'Fatalities_' + t + '_' + c: 'Fatalities_' + c}, inplace=True)
            summary_usgs.rename(columns={'Fatalities_' + t + '_' + c: 'Fatalities_' + c}, inplace=True)
        for i in intensity_list:
            summary_inhouse.rename(columns={t + '_pop_' + i: 'Pop_' + i}, inplace=True)
            summary_usgs.rename(columns={t + '_pop_' + i: 'Pop_' + i}, inplace=True)
        summary_inhouse['Code'] = code
        summary_usgs['Code'] = code
        summary_inhouse['Deaths'] = row['Deaths']
        summary_usgs['Deaths'] = row['Deaths']
        summary_inhouse['Collapse'] = row['Collapse']
        summary_usgs['Collapse'] = row['Collapse']
        summary_inhouse['Year'] = row['Year']
        summary_usgs['Year'] = row['Year']
        print(summary_inhouse)
        print(summary_usgs)
        out_inhouse = out_inhouse.append(summary_inhouse)
        out_usgs = out_usgs.append(summary_usgs)
    out_inhouse.to_csv('Results/Historical/HistoricalsGS_InHouse.csv', index=False)
    out_usgs.to_csv('Results/Historical/HistoricalsGS_USGS.csv', index=False)

# historical_fit(0.039)


def adjust_pop(summary_prefs, prefs_pop_adjust):
    summary_prefs = summary_prefs.merge(prefs_pop_adjust, on='pref_id', how='left')
    for col in list(summary_prefs):
        if re.search(r'pop|Fatalities|count', col):
            summary_prefs[col] = summary_prefs[col] * summary_prefs['Adjustment']
        if re.search(r'prob|_rate_', col):
            del summary_prefs[col]
    del summary_prefs['Adjustment'], summary_prefs['pref_id'], summary_prefs['pref_name']
    return pd.DataFrame([summary_prefs.sum().transpose()])


def regress():
    historical = pd.read_csv('Historical/HistoricalsGS.csv', index_col=0)
    population_real = pd.read_csv('Population/population_records.csv')
    population_ged = pd.read_csv('Population/GED_pop.csv')
    tot_inhouse = pd.DataFrame()
    tot_usgs = pd.DataFrame()
    intensity_list = ['V', 'VI', 'VII', 'VIII', 'IX', 'X']
    codes = ['High', 'Moderate', 'Low', 'Precode']
    for code, row in historical.iterrows():
        year = row['Year']
        print(code, year)
        prefs_pop_real = population_real[['pref_id', str(year)]].copy()
        prefs_pop_real.rename(columns={str(year): 'true_pop'}, inplace=True)
        prefs_pop_adjust = prefs_pop_real.merge(population_ged, on='pref_id')
        prefs_pop_adjust['Adjustment'] = prefs_pop_adjust['true_pop'] / prefs_pop_adjust['type_pop'] * 1000
        del prefs_pop_adjust['true_pop'], prefs_pop_adjust['type_pop']
        inhouse = pd.read_csv('Results/Instrumental/' + code + '/' + 'prefectures.csv')
        usgs = pd.read_csv('Results/Historical/' + code + '/' + 'prefectures.csv')
        inhouse_sum = adjust_pop(inhouse, prefs_pop_adjust)
        usgs_sum = adjust_pop(usgs, prefs_pop_adjust)
        hour = row['Time']
        usgs_dict = {'exposed_pop': usgs_sum[hour + '_pop']}
        inhouse_dict = {'exposed_pop': inhouse_sum[hour + '_pop']}
        for i in intensity_list:
            usgs_dict['Pop_' + i] = usgs_sum[hour + '_pop_' + i]
            inhouse_dict['Pop_' + i] = inhouse_sum[hour + '_pop_' + i]
        for c in codes:
            usgs_dict['Fatalities_' + c] = usgs_sum['Fatalities_' + hour + '_' + c]
            inhouse_dict['Fatalities_' + c] = inhouse_sum['Fatalities_' + hour + '_' + c]
        usgs_dict['Deaths'] = row['Deaths']
        inhouse_dict['Deaths'] = row['Deaths']
        usgs_dict['Code'] = code
        inhouse_dict['Code'] = code
        usgs_dict['Year'] = row['Year']
        inhouse_dict['Year'] = row['Year']
        tot_inhouse = tot_inhouse.append(pd.DataFrame(inhouse_dict))
        tot_usgs = tot_usgs.append(pd.DataFrame(usgs_dict))
    for df in [tot_usgs, tot_inhouse]:
        for col in list(df):
            df.loc[df[col] == 0, col] = 0.05
    formula1 = 'np.log(Deaths) ~ np.log(Fatalities_High) + np.log(Fatalities_Moderate) + np.log(Fatalities_Low) + np.log(Fatalities_Precode)'
    results_usgs1 = smf.ols(formula1, data=tot_usgs).fit()
    # print(results_usgs1.summary())
    tot_usgs['Pred1'] = np.exp(results_usgs1.predict(tot_usgs))
    results_inhouse1 = smf.ols(formula1, data=tot_inhouse).fit()
    print(results_inhouse1.summary())
    fig, ax = plt.subplots()
    fig = sm.graphics.plot_fit(results_inhouse1, 1, ax=ax)
    plt.show()
    tot_inhouse['Pred1'] = np.exp(results_inhouse1.predict(tot_inhouse))
    formula2 = 'np.log(Deaths) ~ np.log(Pop_VII) + np.log(Pop_VIII) + np.log(Pop_IX) + np.log(Pop_X)'
    results_usgs2 = smf.ols(formula2, data=tot_usgs).fit()
    # print(results_usgs2.summary())
    tot_usgs['Pred2'] = np.exp(results_usgs2.predict(tot_usgs))
    results_inhouse2 = smf.ols(formula2, data=tot_inhouse).fit()
    # print(results_inhouse2.summary())
    tot_inhouse['Pred2'] = np.exp(results_inhouse2.predict(tot_inhouse))
    tot_usgs.to_csv('usgs_tot.csv', index=False)
    tot_inhouse.to_csv('inhouse_tot.csv', index=False)

# regress()




df_in = pd.read_csv('inhouse_tot2.csv')

df_in_log10 = df_in.copy()
for col in list(df_in_log10):
    if col not in ['Code', 'Year']:
        df_in_log10[col] = np.log10(df_in_log10[col])
def plot_fitted(df):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    for code, col in {'High': 'b', 'Moderate': 'g', 'Low': 'r', 'Precode': 'c'}.viewitems():
        ax.scatter(df['Deaths'], df['Fatalities_' + code], color=col, label=code)
    duplic = df['Deaths'].duplicated(False)
    df1 = df.loc[duplic == False]
    deaths = np.unique(df.loc[duplic, 'Deaths'])
    labels = [df1.loc[i, 'Code'] + ' ' + str(int(df1.loc[i, 'Year'])) for i in df1.index]
    labels = labels + [str(round(d, 2)) for d in deaths]
    plt.xticks(list(df1['Deaths']) + list(deaths), labels, rotation=45)
    ax.plot([0, np.max(df['Deaths'])], [0, np.max(df['Deaths'])], color='k')
    plt.legend(loc=2)
    ax.xlabel = 'Observe'
    ax.ylabel = 'Predit'
    ax.set_title('Nombre de deces')
    plt.show()
#plot_fitted(df_in)