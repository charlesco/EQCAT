from math import log10
from sympy import Symbol, nsolve, log, sympify
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def bedrock_motion(positions, moment_mag, quake_type):
    k_pga = 0.003
    k_pgv = 0.002
    c1_pga = 0.0060
    c1_pgv = 0.0028
    c2 = 0.50
    c_pga = c1_pga * 10 ** (c2 * moment_mag)
    c_pgv = c1_pgv * 10 ** (c2 * moment_mag)
    a_pga = 0.59
    a_pgv = 0.65
    h_pga = 0.0023
    h_pgv = 0.0024
    d_pga = {1: 0, 2: 0.08, 3: 0.30}[quake_type]
    d_pgv = {1: 0, 2: 0.05, 3: 0.15}[quake_type]
    e_pga = 0.02
    e_pgv = -1.77
    positions['PGAb'] = a_pga * moment_mag + h_pga * positions['depth'] + d_pga + e_pga
    positions['PGVb'] = a_pgv * moment_mag + h_pgv * positions['depth'] + d_pgv + e_pgv
    shallow = positions.loc[positions['depth'] <= 30]
    shallow['PGAb'] = shallow['PGAb'] - pd.np.log10(shallow['distance'] + c_pga) - k_pga * shallow['distance']
    shallow['PGVb'] = shallow['PGVb'] - pd.np.log10(shallow['distance'] + c_pgv) - k_pgv * shallow['distance']
    deep = positions.loc[positions['depth'] > 30]
    deep['PGAb'] = deep['PGAb'] + 0.6 * pd.np.log10(1.7 * deep['distance'] + c_pga) -\
        1.6 * pd.np.log10(deep['distance'] + c_pga) - k_pga * deep['distance']
    deep['PGVb'] = deep['PGVb'] + 0.6 * pd.np.log10(1.7 * deep['distance'] + c_pgv)\
        - 1.6 * pd.np.log10(deep['distance'] + c_pgv) - k_pgv * deep['distance']
    positions = pd.concat([shallow, deep])
    positions[['PGAb', 'PGVb']] = positions[['PGAb', 'PGVb']].rpow(10)
    return positions


def felt_distance(depth, moment_mag, quake_type, min_pga=0.003):
    min_pga = min_pga / 2.5
    g = 9.80665
    min_pga = min_pga * 100 * g
    k = 0.003
    c1 = 0.0060
    c2 = 0.50
    c = c1 * 10 ** (c2 * moment_mag)
    a = 0.59
    h = 0.0023
    d = {1: 0, 2: 0.08, 3: 0.30}[quake_type]
    e = 0.02
    b = a * moment_mag + h * depth + d + e
    x = Symbol("x", positive=True)
    if depth <= 30:
        f = log(min_pga) / log(10) - b + log(x + c) / log(10) + k * x
        min_dist = nsolve(f, x, 1, prec=2)
    else:
        f = log(min_pga) / log(10) - b - 0.6 * log(1.7 * depth + c) / log(10) + 1.6 * log(x + c) / log(10) + k * x
        min_dist = nsolve(f, x, 1, prec=2)
    return float(sympify(min_dist))


def mercalli(positions):
    positions['MMI_num'], positions['MMI'] = np.nan, ''
    positions.loc[positions['PGA (g)'] < 0.0017, ['MMI_num', 'MMI']] = [1, 'I']
    positions.loc[(0.0017 <= positions['PGA (g)']) & (positions['PGA (g)'] < 0.014),
                  ['MMI_num', 'MMI']] = [2.5, 'II-III']
    positions.loc[(0.014 <= positions['PGA (g)']) & (positions['PGA (g)'] < 0.039), ['MMI_num', 'MMI']] = [4, 'IV']
    positions.loc[(0.039 <= positions['PGA (g)']) & (positions['PGA (g)'] < 0.092), ['MMI_num', 'MMI']] = [5, 'V']
    positions.loc[(0.092 <= positions['PGA (g)']) & (positions['PGA (g)'] < 0.18), ['MMI_num', 'MMI']] = [6, 'VI']
    positions.loc[(0.18 <= positions['PGA (g)']) & (positions['PGA (g)'] < 0.34), ['MMI_num', 'MMI']] = [7, 'VII']
    positions.loc[(0.34 <= positions['PGA (g)']) & (positions['PGA (g)'] < 0.65), ['MMI_num', 'MMI']] = [8, 'VIII']
    positions.loc[(0.65 <= positions['PGA (g)']) & (positions['PGA (g)'] < 1.24), ['MMI_num', 'MMI']] = [9, 'IX']
    positions.loc[1.24 <= positions['PGA (g)'], ['MMI_num', 'MMI']] = [10, 'X']
    return positions


def intensity(positions):
    positions = mercalli(positions)
    positions['JMA'] = positions['PGV (cm/s)'].apply(log10)
    positions['JMA'] = 2.68 + 1.72 * positions['JMA']
    return positions


def amp_factors(row):
    if row['AVS'] > 0:
        r_pga = 10**(1.35 - 0.47 * log10(row['AVS']))
        r_pgv = 10**(1.83 - 0.66 * log10(row['AVS']))
    else:
        r_pga = 1.0
        r_pgv = 1.0
    return pd.Series(dict(AmpPGA=r_pga, AmpPGV=r_pgv))


def ground_motion(positions, mag, eqtype, min_pga=0.0039):
    print('Moment magnitude : ', mag)
    positions = bedrock_motion(positions, mag, eqtype)
    positions['PGA (cm/s2)'] = positions['PGAb'] * positions['AmpPGA']
    positions['PGV (cm/s)'] = positions['PGVb'] * positions['AmpPGV']
    g = 9.80665
    positions['PGA (g)'] = positions['PGA (cm/s2)'] / (100 * g)
    positions = intensity(positions)
    positions['PGAbg'] = positions['PGAb'] / (100 * g)
    print('Ground Motion : OK')
    positions = positions.loc[positions['PGA (g)'] > [min_pga]]
    return positions


def plot_attenuation(moment_mag, depth):
    dist = np.linspace(1, 300, 100)
    positions = pd.DataFrame(dict(distance=dist))
    positions['depth'] = depth
    quake_type = {1: 'crustal', 2: 'interplate', 3: 'intraplate'}
    type_col = {1: 'b', 2: 'g', 3: 'r'}
    pga = {}
    pgv = {}
    for typ in quake_type:
        motions = bedrock_motion(positions, moment_mag, typ)
        pga[typ] = motions['PGAb']
        pgv[typ] = motions['PGVb']
    fig = plt.figure()
    fig.suptitle('Mw : ' + str(moment_mag) + ', Profondeur : ' + str(round(depth)) + ' km')
    ax = fig.add_subplot(211)
    ax.set_ylabel('PGA (cm/s^2)')
    for typ in quake_type:
        ax.loglog(dist, pga[typ], type_col[typ] + '-', label=quake_type[typ], basex=10)
    plt.legend(loc=1)
    ax = fig.add_subplot(212)
    ax.set_xlabel('Distance (km)')
    ax.set_ylabel('PGV (cm/s)')
    for typ in quake_type:
        ax.loglog(dist, pgv[typ], type_col[typ] + '-', label=quake_type[typ])
    plt.legend(loc=1)
    plt.show()

# print(felt_distance(1, 7.9, 1))
# plot_attenuation(7.9, 1)
