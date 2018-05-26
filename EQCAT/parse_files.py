import re
import os
import pandas as pd
from EQCAT.earthquake import SegmentEarthquake, MultiSegmentEarthquake, PointsEarthquake, MultiPointsEarthquake,\
    DomainEarthquake, ZoneEarthquake
from EQCAT.shape import PlaneShape, MultiPlaneShape, PointShape, MultiPointShape
from EQCAT.magnitude import GutenbergRichter, CharacteristicMag, DiscreteMagnitude
from EQCAT.occurrence import PoissonProcess, BrownianPTProcess, YearFreqProcess, MultiSegmentProcess

hazard_inputs_path = '../01-Hazard Inputs/'
results_path = "../08-Results/"
parsing_reports_path = "01-Parsing Reports/"


def select_file_regex(regex):
    file_name = ''
    for name in os.listdir(hazard_inputs_path):
        if re.search(regex, name):
            file_name = os.path.join(hazard_inputs_path, name)
            return file_name
    return file_name


def select_all_files_regex(regex):
    file_list = []
    for name in os.listdir(hazard_inputs_path):
        if re.search(regex, name):
            file_name = os.path.join(hazard_inputs_path, name)
            file_list += [file_name]
    return file_list


def detect_blocks(data):
    start_lines = []
    for i, line in enumerate(data):
        if re.search(r'[A-Z]', line):
            start_lines += [i]
    return start_lines


def parse_fault_info(line):
    flt_info = line.split(',')
    eq_code = flt_info[0]
    avract = float(flt_info[1])
    min_mag = float(flt_info[2])
    max_mag = float(flt_info[3])
    b_val = float(flt_info[4])
    nb_planes = int(flt_info[5])
    name = flt_info[6]
    if max_mag > min_mag:
        mag = GutenbergRichter(min_mag, b_val, max_mag)
    else:
        mag = CharacteristicMag(min_mag)
    proc = PoissonProcess(avract)
    return eq_code, proc, mag, nb_planes, name


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


def parse_eqthr(quakes=''):
    if quakes == '':
        quakes = {}
    file_name = select_file_regex(r'P-Y[0-9]{4}-PRM_MAX_LND_A98F_EQTHR_EN.csv')
    fil = open(file_name)
    data = fil.readlines()[5:]
    start_lines = detect_blocks(data)
    print("Parsing major active faults with EQTHR : " + str(len(start_lines)) + ' sources')
    mag_col_names = ['Code', 'Process', 'Magnitude', 'NbPlanes', 'Name']
    mag_report = pd.DataFrame(columns=mag_col_names)
    pln_col_names = ['Code', 'Latitude', 'Longitude', 'Length', 'Width', 'Strike', 'Dip']
    pln_report = pd.DataFrame(columns=pln_col_names)
    for i in start_lines:
        eq_code, proc, mag, nb_planes, name = parse_fault_info(data[i])
        mag_report.loc[len(mag_report)] = [eq_code, proc.desc(), mag.desc(), nb_planes, name]
        plane_list = []
        for j in range(nb_planes):
            plane = parse_plane_info(data[i + j + 1])
            plane_list += [plane]
            pln_report.loc[len(pln_report)] = [eq_code, plane.lat, plane.lon, plane.length, plane.width, plane.strike,
                                               plane.dip]
        shape = MultiPlaneShape(plane_list)
        quakes[eq_code] = {'code': eq_code, 'process': proc, 'mag': mag, 'shape': shape, 'name': name}
    fil.close()
    mag_report.to_csv(results_path + parsing_reports_path + '01-EQTHR/magnitude_report.csv', sep=',', index=False)
    pln_report.to_csv(results_path + parsing_reports_path + '01-EQTHR/planes_report.csv', sep=',', index=False)
    print(' - ' + str(mag_report.count()[0]) + ' magnitudes/process parsed')
    print(' - ' + str(pln_report.count()[0]) + ' rectangles parsed')
    return quakes


def parse_activity(quakes='', eq_category='all'):
    if quakes == '':
        quakes = {}
    major_path = select_file_regex(r'P-Y[0-9]{4}-PRM-ACT_MAX_LND_A98F_EN.csv')
    minor_path = select_file_regex(r'P-Y[0-9]{4}-PRM-ACT_AVR_LND_AGR1_EN.csv')
    subduction_path = select_file_regex(r'P-Y[0-9]{4}-PRM-ACT_MAX_PME_MTTL_EN.csv')
    if eq_category == 'all':
        activity = pd.read_csv(major_path, skiprows=8, skipinitialspace=True, index_col=0)
        activity2 = pd.read_csv(minor_path, skiprows=8, skipinitialspace=True, index_col=0)
        activity = activity.append(activity2)
        activity2 = pd.read_csv(subduction_path, skiprows=8, skipinitialspace=True, index_col=0)
        activity = activity.append(activity2)
    elif eq_category == 'all active faults':
        activity = pd.read_csv(major_path, skiprows=8, skipinitialspace=True, index_col=0)
        activity2 = pd.read_csv(minor_path, skiprows=8, skipinitialspace=True, index_col=0)
        activity = activity.append(activity2)
    elif eq_category == 'major active faults':
        activity = pd.read_csv(major_path, skiprows=8, skipinitialspace=True, index_col=0)
    elif eq_category == 'minor active faults':
        activity = pd.read_csv(minor_path, skiprows=8, skipinitialspace=True, index_col=0)
    elif eq_category == 'subduction':
        activity = pd.read_csv(subduction_path, skiprows=8, skipinitialspace=True, index_col=0)
    else:
        activity = pd.DataFrame()
    print('Parsing  seismic activity for ' + eq_category + ' : ' + str(activity.count()[0]) + ' sources')
    activity_report = pd.DataFrame(columns=['Code', 'Process', 'Multi', 'AvrAct', 'LastAct', 'Alpha', 'Desc', 'Name'])
    nb_new_quakes = 0
    nb_updated_quakes = 0
    for eq_code, row in activity.iterrows():
        if row['PROC'] in ['POI', 'PSI'] and row['AVRACT'] != '-':
            process = PoissonProcess(row['AVRACT'])
            activity_report.loc[len(activity_report)] = [eq_code, 'Poisson', row['PROC'], row['AVRACT'], None, None,
                                                         process.desc(), row['NAME']]
        elif row['PROC'] in ['BPT', 'BSI', 'COM']:
            process = BrownianPTProcess(row['AVRACT'], row['NEWACT'], row['ALPHA'])
            activity_report.loc[len(activity_report)] = [eq_code, 'BrownianPassageTime', row['PROC'], row['AVRACT'],
                                                         row['NEWACT'], row['ALPHA'], process.desc(), row['NAME']]
        else:
            # print(eq_code)
            process = 'multi'
            activity_report.loc[len(activity_report)] = [eq_code, 'Multi', row['PROC'], row['AVRACT'], row['NEWACT'],
                                                         row['ALPHA'], process, row['NAME']]
        dico = {'process': process}
        if eq_code in quakes:
            if 'process' not in quakes[eq_code]:
                nb_updated_quakes += 1
                quakes[eq_code].update(dico)
            elif quakes[eq_code]['process'].desc()[0] == "P" and process.desc()[0] == "B":
                nb_updated_quakes += 1
                quakes[eq_code].update(dico)
        else:
            dico.update({'code': eq_code, 'name': row['NAME']})
            quakes[eq_code] = dico
            nb_new_quakes += 1
    activity_report.to_csv(results_path + parsing_reports_path + '02-Seismic Activity Evaluation/' + eq_category +
                           '/activity_report.csv', sep=',', index=False)
    print('Nb sources updated : ' + str(nb_updated_quakes))
    print('Nb new sources : ' + str(nb_new_quakes))
    return quakes


def parse_multi(quakes):
    df = pd.read_csv(hazard_inputs_path + 'MultiActivity.csv', index_col=0)
    print('Parsing sources triggered by simulated occurrences : ' + str(df.count()[0]) + ' sources')
    nb_updated_quakes = 0
    nb_unknown = 0
    for code, row in df.iterrows():
        if code in quakes:
            quakes[code]['segments'] = row['SEGMENTS'].split(';')
            if quakes[code]['process'] == 'multi':
                quakes[code]['process'] = 'multi'
                nb_updated_quakes += 1
            else:
                print('Unexpected simulated occurrence process : ' + code)
        else:
            nb_unknown += 1
            # print('Unknown source code : ' + code)
    print('Nb sources updated : ' + str(nb_updated_quakes))
    print('Nb unknown source codes : ' + str(nb_unknown))
    return quakes


def parse_frequencies(quakes=''):
    if quakes == '':
        quakes = {}

    types_path = select_file_regex(r'P-Y[0-9]{4}-PRM-ATTENUATION_FORMULA.csv')
    types_df = pd.read_csv(types_path, skiprows=4, skipinitialspace=True, index_col=0)

    file_list = select_all_files_regex(r'^P-Y[0-9]{4}-PRM-ACT_(PSE|LND)_[A-Z]+[0-9]?_(INTER|INTRA|CRUST)_CV_SM.csv$')
    print('Parsing frequencies : ' + str(len(file_list)) + " files")

    for path in file_list:
        activity_report = pd.DataFrame(columns=['Code', 'Zone', 'Type', 'YearFreq', 'MinMag', 'Bval', 'Lat', 'Lon',
                                                'Dep', 'Desc'])
        df = pd.read_csv(path, skiprows=7, skipinitialspace=True)

        temp = path.split('_')
        code, typ = temp[-4], temp[-3]
        code = code + '_' + typ

        print(code + ' : ' + str(df.count()[0]) + ' zones')
        eqtype = {'CRUST': 1, 'INTER': 2, 'INTRA': 3}[typ]
        correct = types_df.loc[temp[-5] + "_" + temp[-4]]['CRTYPE']

        for _, row in df.iterrows():
            if row['FRQ'] > 0:
                process = YearFreqProcess(row['FRQ'])
                mag = GutenbergRichter(row['MMN'], row['BVL'])
                shape = PointShape(row['# MNO'], row['WLG'], row['WLA'], row['DEP'])  # , row['STR'], row['DIP']
                code2 = code + '_' + str(int(row['ANO'])) + '_' + str(int(row['# MNO']))
                quakes[code2] = {'code': code2, 'name': code2, 'process': process, 'mag': mag, 'shape': shape,
                                 'eqtype': eqtype, 'correction': correct}
                quakes[code2] = ZoneEarthquake(quakes[code2])
                activity_report.loc[len(activity_report)] = [code2, int(row['ANO']), typ, row['FRQ'], mag.min_mag,
                                                             row['BVL'], shape.lat, shape.lon, shape.depth, mag.desc()]
        activity_report.to_csv(results_path + parsing_reports_path + '03-Frequencies/' + code + '.csv', sep=',',
                               index=False)
    return quakes


def parse_types(quakes):
    file_name = select_file_regex(r'P-Y[0-9]{4}-PRM-ATTENUATION_FORMULA.csv')
    df = pd.read_csv(file_name, skiprows=4, skipinitialspace=True, index_col=0)
    df.drop('LND_A98F', inplace=True)
    df.drop('LND_AGR1', inplace=True)
    for code in quakes:
        if code[0] in ['F', 'G']:
            quakes[code].update({'eqtype': 1, 'correction': 0})
    for code0, row in df.iterrows():
        code = code0.split('_')[-1]
        if code in quakes:
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
    file_list = select_all_files_regex(r'P-Y[0-9]{4}-PRM-SHP_TYPE1_(LND|PLE)_A(98)?[A-Z]+1?_EN.csv')
    print("Parsing rectangles : " + str(len(file_list)) + " files")
    nb_sources_updated = 0
    nb_planes_parsed = 0
    nb_mags_parsed = 0
    for path in file_list:
        fil = open(path)
        data = fil.readlines()[5:]
        start_lines = detect_blocks(data)
        for i in start_lines:
            eq_code, mag, nb_planes, name = parse_fault_info2(data[i])
            if eq_code in quakes and 'process' in quakes[eq_code]:
                if 'mag' not in quakes[eq_code]:
                    quakes[eq_code]['mag'] = mag
                    nb_mags_parsed += 1
                if 'shape' not in quakes[eq_code]:
                    plane_list = []
                    for j in range(nb_planes):
                        plane = parse_plane_info(data[i+j+1])
                        plane_list += [plane]
                    shape = MultiPlaneShape(plane_list)
                    nb_planes_parsed += nb_planes
                    quakes[eq_code]['shape'] = shape
                if quakes[eq_code]['process'] == 'multi':
                    quakes[eq_code]['segments'] = [quakes[i] for i in quakes[eq_code]['segments']]
                    quakes[eq_code]['proc'] = MultiSegmentProcess(quakes[eq_code]['segments'])
                    quakes[eq_code] = MultiSegmentEarthquake(quakes[eq_code])
                else:
                    quakes[eq_code] = SegmentEarthquake(quakes[eq_code])
                nb_sources_updated += 1
            elif eq_code in quakes:
                quakes.pop(eq_code)
        fil.close()
    print(" - Nb planes parsed : " + str(nb_planes_parsed))
    print(" - Nb mags parsed : " + str(nb_mags_parsed))
    print(" - Nb sources updated : " + str(nb_sources_updated))
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
    file_list = select_all_files_regex(r'P-Y[0-9]{4}-PRM-SHP_TYPE2_PLE_A[A-Z]+_EN.csv')
    print("Parsing points : " + str(len(file_list)) + " files")
    nb_sources_updated = 0
    nb_mags_updated = 0
    nb_points_updated = 0
    for path in file_list:
        fil = open(path)
        data = fil.readlines()
        eq_code = data[4].split(',')[0].split('_')[-1]
        data = data[5:]
        start_lines = detect_blocks(data)
        faults = {}
        for i in start_lines:
            flt_code, mag, depth, nb_points, name = parse_fault_info3(data[i])
            nb_mags_updated += 1
            pnt_list = []
            for j in range(nb_points):
                point = parse_point_info(data[i + j + 1])
                pnt_list += [point]
                nb_points_updated += 1
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
                nb_sources_updated += 1
        if faults != {}:
            quakes[eq_code].update({'earthquakes': faults})
            quakes[eq_code] = MultiPointsEarthquake(quakes[eq_code])
            nb_sources_updated += 1
        fil.close()
    print(" - Nb points parsed : " + str(nb_points_updated))
    print(" - Nb mags parsed : " + str(nb_mags_updated))
    print(" - Nb sources updated : " + str(nb_sources_updated))
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
    file_list = select_all_files_regex(r'P-Y[0-9]{4}-PRM-SHP_TYPE3_(PSE|LND)_B[A-Z]+.csv')
    print("Parsing discrete rectangles : " + str(len(file_list)) + " files")
    nb_mag_pars = 0
    nb_sources_up = 0
    nb_planes_up = 0
    for path in file_list:
        fil = open(path, 'r')
        data = fil.readlines()[4:]
        eq_code, nb_dom, nb_mag, nb_occ = parse_fault_info4(data[0])
        nb_mag_pars += 1
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
                nb_planes_up += 1
            shape = MultiPlaneShape(pln_list)
            dom_dict[dom_id] = shape
            data = data[nb_planes:]
        quakes[eq_code].update({'mag': mag, 'shape': dom_dict})
        quakes[eq_code] = DomainEarthquake(quakes[eq_code])
        nb_sources_up += 1
        fil.close()
    print(" - Nb planes parsed : " + str(nb_planes_up))
    print(" - Nb mags parsed : " + str(nb_mag_pars))
    print(" - Nb sources updated : " + str(nb_sources_up))
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
            if i - 1 < 10:
                zone_id = '0' + zone_id
            eq_code = code.split('_')[1]
            for c in quakes:
                if re.search(eq_code + '_' + zone_id, c):
                    if isinstance(quakes[c], dict):
                        quakes[c] = ZoneEarthquake(quakes[c])
    return quakes


def parse_quakes(category='all'):
    q = ''
    if category in ['all', 'all active faults', 'major active faults']:
        q = parse_eqthr(q)
    if category in ['all', 'all active faults', 'major active faults', 'minor active faults', 'subduction']:
        q = parse_activity(q, category)
    q = parse_multi(q)
    if category in ['all', 'zones']:
        q = parse_frequencies(q)
    q = parse_types(q)
    if category in ['all', 'all active faults', 'major active faults', 'minor active faults', 'subduction']:
        q = parse_rectangles(q)
    if category in ['all', 'subduction']:
        q = parse_points(q)
        q = parse_domains(q)

    for quake in q:
        if isinstance(q[quake], dict):
            print(quake)
    return q


yesy = parse_quakes('major active faults')

output = pd.DataFrame(columns=['Code', 'Process', 'Multi', 'AvrAct', 'LastAct', 'Alpha', 'Desc', 'Name'])
for cp in yesy:
    seisme = yesy[cp]



