import pandas as pd
hazard_inputs_path = '../01-Hazard Inputs/'


def parse_fault_info5(line):
    flt_info = line.split(',')
    code = flt_info[0].split('_')[-1]
    nb_dom = int(flt_info[1])
    nb_mag = int(flt_info[2])
    return code, nb_dom, nb_mag



def parse_domain_info(line):
    dom_info = line.split(',')
    dom_id = int(dom_info[0])
    leng = float(dom_info[1])
    wid = float(dom_info[2])
    nb_planes = int(dom_info[3])
    return dom_id, leng, wid, nb_planes


codes = {'COUT_INTRA': [1, 2, 3], 'CPCF_INTER': [1, 2, 3, 4, 5, 6, 7, 8, 9, 12],
             'CPCF_INTRA': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13], 'CPHL_INTER': [1, 5, 6, 7],
             'CPHL_INTRA': [1, 3, 5, 6, 7]}
for code, zone_id_list in codes.viewitems():
    for i in zone_id_list:
        out = pd.DataFrame(columns=['lat', 'lon'])
        zone_id = str(i)
        if i < 10:
            zone_id = '0' + zone_id
        eq_code = code + '_' + zone_id
        file_name = hazard_inputs_path + 'P-Y2017-PRM-SHP_TYPE4_PSE_' + eq_code + '.csv'
        print(file_name)
        fil = open(file_name)
        data = fil.readlines()[4:]
        _, nb_dom, nb_mag = parse_fault_info5(data[0])
        data = data[1:]
        data = data[nb_mag:]
        for k in range(nb_dom):
            dom_id, leng, wid, nb_planes = parse_domain_info(data[0])
            data = data[1:]
            for j in range(nb_planes):
                line = data[j].split(',')
                lon = float(line[3])
                lat = float(line[4])
                out=out.append({'lat':lat, 'lon':lon}, ignore_index=True)
            data = data[nb_planes:]
        out.to_csv('../08-Results/' + eq_code + '.csv')