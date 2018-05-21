import re
import os
import pandas as pd
from EQCAT.earthquake import SegmentEarthquake, MultiSegmentEarthquake, PointsEarthquake, MultiPointsEarthquake,\
    DomainEarthquake, ZoneEarthquake
from EQCAT.shape import PlaneShape, MultiPlaneShape, PointShape, MultiPointShape
from EQCAT.magnitude import GutenbergRichter, CharacteristicMag, DiscreteMagnitude
from EQCAT.occurrence import PoissonProcess, BrownianPTProcess, YearFreqProcess, MultiSegmentProcess

hazard_inputs_path = '../01-Hazard Inputs/'


def detect_blocks(data):
    start_lines = []
    for i, line in enumerate(data):
        if re.search(r'[A-Z]', line):
            start_lines += [i]
    return start_lines


def parse_fault_info(line):
    flt_info = line.split(',')
    eq_code = flt_info[0]
    # avract = float(flt_info[1])
    min_mag = float(flt_info[2])
    max_mag = float(flt_info[3])
    b_val = float(flt_info[4])
    nb_planes = int(flt_info[5])
    name = flt_info[6]
    if max_mag > min_mag:
        mag = GutenbergRichter(min_mag, b_val, max_mag)
    else:
        mag = CharacteristicMag(min_mag)
    return eq_code, mag, nb_planes, name


def parse_plane_info(line):
    pln_info = line.split(',')
    idx = int(pln_info[0])
    lon = float(pln_info[3])
    lat = float(pln_info[4])
    dep = float(pln_info[5])
    leng = float(pln_info[6])
    wid = float(pln_info[7])
    strike = float(pln_info[8])
    dip = float(pln_info[9])
    plane = PlaneShape(idx, lon, lat, dep, leng, wid, strike, dip)
    return plane


def parse_eqthr(quakes):
    file_name = ""
    for name in os.listdir(hazard_inputs_path):
        if re.search('P-Y[0-9]{4}-PRM_MAX_LND_A98F_EQTHR_EN.csv', name):
            file_name = os.path.join(hazard_inputs_path, name)
            break
    fil = open(file_name)
    data = fil.readlines()[5:]
    start_lines = detect_blocks(data)
    for i in start_lines:
        eq_code, mag, nb_planes, name = parse_fault_info(data[i])
        plane_list = []
        for j in range(nb_planes):
            plane = parse_plane_info(data[i + j + 1])
            plane_list += [plane]
        shape = MultiPlaneShape(plane_list)
        quakes[eq_code] = {'code': eq_code, 'mag': mag, 'shape': shape, 'name': name}
    fil.close()
    return quakes


def parse_activity(quakes):
    activity = pd.read_csv(hazard_inputs_path + 'P-Y2017-PRM-ACT_MAX_LND_A98F_EN.csv', skiprows=8,
                           skipinitialspace=True, index_col=0)
    activity2 = pd.read_csv(hazard_inputs_path + 'P-Y2017-PRM-ACT_AVR_LND_AGR1_EN.csv', skiprows=8,
                            skipinitialspace=True, index_col=0)
    activity = activity.append(activity2)
    activity2 = pd.read_csv(hazard_inputs_path + 'P-Y2017-PRM-ACT_MAX_PME_MTTL_EN.csv', skiprows=8,
                            skipinitialspace=True, index_col=0)
    activity = activity.append(activity2)
    for eq_code, row in activity.iterrows():
        if row['PROC'] in ['POI', 'PSI'] and row['AVRACT'] != '-':
            process = PoissonProcess(row['AVRACT'])
        elif row['PROC'] in ['BPT', 'BSI', 'COM']:
            process = BrownianPTProcess(row['AVRACT'], row['NEWACT'], row['ALPHA'])
        else:
            process = ''
        dico = {'process': process}
        if eq_code in quakes:
            quakes[eq_code].update(dico)
        else:
            dico.update({'code': eq_code, 'name': row['NAME']})
            quakes[eq_code] = dico
    return quakes


def parse_multi(quakes):
    df = pd.read_csv(hazard_inputs_path + 'MultiActivity.csv', index_col=0)
    for code, row in df.iterrows():
        quakes[code]['segments'] = row['SEGMENTS'].split(';')
        quakes[code]['process'] = 'multi'
    return quakes


def parse_frequencies(quakes):
    codes1 = ['LND_CGR5_CRUST', 'LND_CIZU_CRUST', 'LND_CJPS_CRUST', 'PSE_CURA_CRUST']
    codes2 = ['PSE_CPCF_INTER', 'PSE_CPCF_INTRA', 'PSE_CPHL_INTER', 'PSE_CPHL_INTRA']
    for code in codes1:
        file_name = hazard_inputs_path + 'P-Y2017-PRM-ACT_' + code + '_CV_SM.csv'
        df = pd.read_csv(file_name, skiprows=7, skipinitialspace=True)
        temp = code.split('_')
        code, typ = temp[1], temp[2]
        eqtype = {'CRUST': 1, 'INTER': 2, 'INTRA': 3}[typ]
        for _, row in df.iterrows():
            if row['FRQ'] > 0:
                process = YearFreqProcess(row['FRQ'])
                mag = GutenbergRichter(row['MMN'], row['BVL'])
                shape = PointShape(row['# MNO'], row['WLG'], row['WLA'], row['DEP'])  # , row['STR'], row['DIP']
                code3 = code + '_' + str(int(row['ANO'])) + '_' + str(int(row['# MNO']))
                quakes[code3] = {'code': code3, 'name': code3, 'process': process, 'mag': mag, 'shape': shape,
                                 'eqtype': eqtype}
    for code in codes2:
        file_name = hazard_inputs_path + 'P-Y2017-PRM-ACT_' + code + '_CV_SM.csv'
        df = pd.read_csv(file_name, skiprows=7, skipinitialspace=True)
        temp = code.split('_')
        code, typ = temp[1] + '_' + temp[2], temp[2]
        eqtype = {'CRUST': 1, 'INTER': 2, 'INTRA': 3}[typ]
        for _, row in df.iterrows():
            if row['FRQ'] > 0:
                process = YearFreqProcess(row['FRQ'])
                mag = GutenbergRichter(row['MMN'], row['BVL'])
                shape = PointShape(row['# MNO'], row['WLG'], row['WLA'], row['DEP'])  # , row['STR'], row['DIP']
                code3 = code + '_' + str(int(row['ANO'])) + '_' + str(int(row['# MNO']))
                quakes[code3] = {'code': code3, 'name': code3, 'process': process, 'mag': mag, 'shape': shape,
                                 'eqtype': eqtype}
    return quakes


def parse_types(quakes):
    file_name = hazard_inputs_path + 'P-Y2017-PRM-ATTENUATION_FORMULA.csv'
    df = pd.read_csv(file_name, skiprows=4, skipinitialspace=True, index_col=0)
    df.drop('LND_A98F', inplace=True)
    df.drop('LND_AGR1', inplace=True)
    for code in quakes:
        if code[0] in ['F', 'G']:
            quakes[code].update({'eqtype': 1, 'correction': 0})
    for code0, row in df.iterrows():
        code = code0.split('_')[-1]
        if code not in quakes:
            if code in ['CPCF', 'CPHL']:
                types = {2: 'INTER', 3: 'INTRA'}
                code = code + '_' + types[row['EQTYPE']]
            for c in quakes:
                if code in c:
                    quakes[c].update({'eqtype': row['EQTYPE'], 'correction': row['CRTYPE']})
        else:
            quakes[code].update({'eqtype': row['EQTYPE'], 'correction': row['CRTYPE']})
            if quakes[code]['process'] == 'multi':
                for code2 in quakes[code]['segments']:
                    quakes[code2].update({'eqtype': row['EQTYPE'], 'correction': row['CRTYPE']})
    return quakes


def parse_fault_info2(line):
    flt_info = line.split(',')
    eq_code = flt_info[0]
    mag = CharacteristicMag(float(flt_info[1]))
    nb_planes = int(flt_info[2])
    name = flt_info[3]
    return eq_code, mag, nb_planes, name


def parse_rectangles(quakes):
    codes = ['LND_A98F', 'LND_AAOMW', 'LND_AGR1', 'LND_AHKDW',  'LND_AHKSW', 'LND_ANIGT', 'LND_AYMGA', 'PLE_ASNKT']
    for code in codes:
        fil = open(hazard_inputs_path + 'P-Y2017-PRM-SHP_TYPE1_'+code+'_EN.CSV')
        data = fil.readlines()[5:]
        start_lines = detect_blocks(data)
        for i in start_lines:
            eq_code, mag, nb_planes, name = parse_fault_info2(data[i])
            if eq_code in quakes and 'process' in quakes[eq_code]:
                plane_list = []
                for j in range(nb_planes):
                    plane = parse_plane_info(data[i+j+1])
                    plane_list += [plane]
                shape = MultiPlaneShape(plane_list)
                if 'mag' not in quakes[eq_code]:
                    quakes[eq_code]['mag'] = mag
                if 'shape' not in quakes[eq_code]:
                    quakes[eq_code]['shape'] = shape
                if quakes[eq_code]['process'] == 'multi':
                    quakes[eq_code] = MultiSegmentEarthquake(quakes[eq_code])
                else:
                    quakes[eq_code] = SegmentEarthquake(quakes[eq_code])
            elif eq_code in quakes:
                quakes.pop(eq_code)
        fil.close()
    return quakes


def parse_fault_info3(line):
    flt_info = line.split(',')
    flt_code = flt_info[0]
    mag = CharacteristicMag(float(flt_info[1]))
    depth = float(flt_info[2])
    nb_points = int(flt_info[3])
    name = flt_info[4]
    return flt_code, mag, depth, nb_points, name


def parse_point_info(line):
    pt_info = line.split(',')
    idx = pt_info[0]
    lon = float(pt_info[3])
    lat = float(pt_info[4])
    dep = float(pt_info[5])
    point = PointShape(idx, lon, lat, dep)
    return point


def parse_points(quakes):
    codes = ['PLE_AETRF', 'PLE_ANNKI', 'PLE_ASGMI', 'PLE_ASKTN', 'PLE_ATHOP', 'PLE_ATKNM']
    for code in codes:
        fil = open(hazard_inputs_path + 'P-Y2017-PRM-SHP_TYPE2_' + code + '_EN.csv')
        data = fil.readlines()
        eq_code = data[4].split(',')[0].split('_')[-1]
        data = data[5:]
        start_lines = detect_blocks(data)
        faults = {}
        for i in start_lines:
            flt_code, mag, depth, nb_points, name = parse_fault_info3(data[i])
            pnt_list = []
            for j in range(nb_points):
                point = parse_point_info(data[i + j + 1])
                pnt_list += [point]
            shape = MultiPointShape(pnt_list, depth)
            dico = {'code': flt_code, 'name': name, 'mag': mag, 'shape': shape}
            if flt_code not in quakes:
                dico['process'] = quakes[eq_code]['process']
                dico['eqtype'] = quakes[eq_code]['eqtype']
                dico['correction'] = quakes[eq_code]['correction']
                faults[flt_code] = PointsEarthquake(dico)
            else:
                dico.update(quakes[flt_code])
                quakes[flt_code] = PointsEarthquake(dico)
        if faults != {}:
            quakes[eq_code].update({'earthquakes': faults})
            quakes[eq_code] = MultiPointsEarthquake(quakes[eq_code])
        fil.close()
    return quakes


def parse_fault_info4(line):
    flt_info = line.split(',')
    code = flt_info[0].split('_')[-1]
    nb_dom = int(flt_info[1])
    nb_mag = int(flt_info[2])
    nb_occ = int(flt_info[3])
    return code, nb_dom, nb_mag, nb_occ


def parse_discrete_mag(lines):
    out = {}
    for i, l in enumerate(lines):
        mag_info = l.split(',')
        idx = mag_info[0]
        mag = float(mag_info[1])
        prob = float(mag_info[2])
        dom_id = int(mag_info[3])
        out[idx] = {'mag': mag, 'prob': prob, 'dom_id': dom_id}
    mag = DiscreteMagnitude(out)
    return mag


def parse_domain_info(line):
    dom_info = line.split(',')
    dom_id = int(dom_info[0])
    leng = float(dom_info[1])
    wid = float(dom_info[2])
    nb_planes = int(dom_info[3])
    return dom_id, leng, wid, nb_planes


def parse_plane_info2(line, leng, wid):
    line = line.split(',')
    pln_id = line[0]
    lon = float(line[3])
    lat = float(line[4])
    dep = float(line[5])
    strike = float(line[6])
    dip = float(line[7])
    plane = PlaneShape(pln_id, lon, lat, dep, leng, wid, strike, dip)
    return plane


def parse_domains(quakes):
    domains = ['PSE_BNRML', 'PSE_BTNMI', 'LND_BAKIT', 'PSE_BYNGN', 'LND_BHKNW', 'LND_BSDGN', 'PSE_BHGNL',
                            'PSE_BHGNS']
    for name in domains:
        file_name = hazard_inputs_path + 'P-Y2017-PRM-SHP_TYPE3_' + name + '.csv'
        fil = open(file_name, 'r')
        data = fil.readlines()[4:]
        eq_code, nb_dom, nb_mag, nb_occ = parse_fault_info4(data[0])
        data = data[1:]
        mag = parse_discrete_mag(data[:nb_mag])
        data = data[nb_mag:]
        dom_dict = {}
        for i in range(nb_dom):
            dom_id, leng, wid, nb_planes = parse_domain_info(data[0])
            data = data[1:]
            pln_list = []
            for j in range(nb_planes):
                plane = parse_plane_info2(data[j], leng, wid)
                pln_list += [plane]
            shape = MultiPlaneShape(pln_list)
            dom_dict[dom_id] = shape
            data = data[nb_planes:]
        quakes[eq_code].update({'mag': mag, 'shape': dom_dict})
        quakes[eq_code] = DomainEarthquake(quakes[eq_code])
        fil.close()
    return quakes


def parse_fault_info5(line):
    flt_info = line.split(',')
    code = flt_info[0].split('_')[-1]
    nb_dom = int(flt_info[1])
    nb_mag = int(flt_info[2])
    return code, nb_dom, nb_mag


def parse_discrete_mag2(lines):
    out = {}
    n = len(lines)
    for i, l in enumerate(lines):
        mag_info = l.split(',')
        idx = int(mag_info[0])
        mag = float(mag_info[1])
        prob = float(mag_info[2])
        dom_id = int(mag_info[3])
        out[idx] = {'mag': mag, 'prob': prob, 'dom_id': dom_id}
    for idx in range(1, n):
        out[n - idx]['prob'] = out[n - idx]['prob'] - out[n - idx + 1]['prob']
    mag = DiscreteMagnitude(out)
    return mag


def parse_discrete_rectangles(quakes):
    codes = {'COUT_INTRA': [1, 2, 3], 'CPCF_INTER': [1, 2, 3, 4, 5, 6, 7, 8, 9, 12],
             'CPCF_INTRA': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13], 'CPHL_INTER': [1, 5, 6, 7],
             'CPHL_INTRA': [1, 3, 5, 6, 7]}
    for code, zone_id_list in codes.viewitems():
        for i in zone_id_list:
            zone_id = str(i)
            if i < 10:
                zone_id = '0' + zone_id
            eq_code = code + '_' + zone_id
            file_name = hazard_inputs_path + 'P-Y2017-PRM-SHP_TYPE4_PSE_' + eq_code + '.csv'
            fil = open(file_name)
            data = fil.readlines()[4:]
            _, nb_dom, nb_mag = parse_fault_info5(data[0])
            data = data[1:]
            mag = parse_discrete_mag2(data[:nb_mag])
            data = data[nb_mag:]
            dom_dict = {}
            for k in range(nb_dom):
                dom_id, leng, wid, nb_planes = parse_domain_info(data[0])
                data = data[1:]
                pln_list = []
                for j in range(nb_planes):
                    plane = parse_plane_info2(data[j], leng, wid)
                    pln_list += [plane]
                shape = MultiPlaneShape(pln_list)
                dom_dict[dom_id] = shape
                data = data[nb_planes:]
            for c in quakes:
                if eq_code in c:
                    quakes[c].update({'mag': mag, 'shape': dom_dict})
                    quakes[c] = DomainEarthquake(quakes[c])
                    fil.close()
    return quakes


def parse_areas(quakes):
    codes = {'LND_CGR5': 25, 'LND_CIZU': 3, 'LND_CJPS': 1, 'PSE_COUT': 3, 'PSE_CPCF': 13, 'PSE_CPHL': 7,
             'PSE_CURA': 1}
    for code in codes:
        for i in range(codes[code]):
            zone_id = str(i + 1)
            if i < 10:
                zone_id = '0' + zone_id
            eq_code = code.split('_')[1]
            for c in quakes:
                if re.search(eq_code + '_' + zone_id, c):
                    if isinstance(quakes[c], dict):
                        quakes[c] = ZoneEarthquake(quakes[c])
    return quakes


def parse_quakes():
    quakes = {}
    quakes = parse_eqthr(quakes)
    quakes = parse_activity(quakes)
    quakes = parse_multi(quakes)
    quakes = parse_frequencies(quakes)
    quakes = parse_types(quakes)
    quakes = parse_rectangles(quakes)
    quakes = parse_points(quakes)
    quakes = parse_domains(quakes)
    quakes = parse_discrete_rectangles(quakes)
    quakes = parse_areas(quakes)
    for q in quakes:
        if isinstance(quakes[q], dict):
            quakes[q] = ZoneEarthquake(quakes[q])
        elif quakes[q].proc == 'multi':
            quakes[q].segments = [quakes[i] for i in quakes[q].segments]
            quakes[q].proc = MultiSegmentProcess(quakes[q].segments)
    print('Total quakes : ', len(list(quakes)))
    return quakes
