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
            file_list+= [file_name]
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
    # 01-EQTHR
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
            activity_report.loc[len(activity_report)] = [eq_code, 'Multi', row['PROC'], row['AVRACT'],row['NEWACT'],
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
    for code, row in df.iterrows():
        if code in quakes:
            quakes[code]['segments'] = row['SEGMENTS'].split(';')
            if quakes[code]['process'] == 'multi':
                quakes[code]['process'] = 'multi'
                nb_updated_quakes += 1
            else:
                print('Unexpected simulated occurrence process : ' + code)
        else:
            print('Unknown source code : ' + code)
    print('Nb sources updated : ' + str(nb_updated_quakes))
    return quakes


def parse_frequencies(quakes=''):
    if quakes == '':
        quakes = {}
    file_list = select_all_files_regex(r'^P-Y[0-9]{4}-PRM-ACT_(PSE|LND)_[A-Z]+[0-9]?_(INTER|INTRA|CRUST)_CV_SM.csv$')
    print('Parsing frequencies : ' + str(len(file_list)))
    for path in file_list:
        activity_report = pd.DataFrame(columns=['Code', 'Type', 'YearFreq', 'MinMag', 'Bval', 'Lat', 'Lon', 'Dep', 'Desc'])
        df = pd.read_csv(path, skiprows=7, skipinitialspace=True)
        temp = path.split('_')
        code, typ = temp[-4], temp[-3]
        code = code + '_' + typ
        eqtype = {'CRUST': 1, 'INTER': 2, 'INTRA': 3}[typ]
        print(code + ' : ' + str(df.count()[0]) + ' zones')
        for _, row in df.iterrows():
            if row['FRQ'] > 0:
                process = YearFreqProcess(row['FRQ'])
                mag = GutenbergRichter(row['MMN'], row['BVL'])
                shape = PointShape(row['# MNO'], row['WLG'], row['WLA'], row['DEP'])  # , row['STR'], row['DIP']
                code2 = code + '_' + str(int(row['ANO'])) + '_' + str(int(row['# MNO']))
                quakes[code2] = {'code': code2, 'name': code2, 'process': process, 'mag': mag, 'shape': shape,
                                 'eqtype': eqtype}
                activity_report.loc[len(activity_report)] = [code2, typ, row['FRQ'], mag.min_mag, row['BVL'], shape.lat,
                                                             shape.lon, shape.depth, mag.desc()]
        activity_report.to_csv(results_path + parsing_reports_path + '03-Frequencies/' + code + '.csv', sep=',', index=False)
    return quakes


q=parse_eqthr()
q=parse_activity(q, 'all')
q = parse_multi(q)
q = parse_frequencies(q)

