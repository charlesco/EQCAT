import requests
import os
from jpmesh import parse_mesh_code
from tqdm import tqdm

url_login='https://platform.openquake.org/account/login/'
client = requests.session()
client.get(url_login)
# Identification for openquake platform
login_data = {'username':'###','password':'###'}
r1=client.post(url_login,data=login_data)
def scrap_expo():
    dir_names=os.listdir('Site Effects/')
    for name in dir_names:
        fcode = name.split('-')[-1]
        mesh = parse_mesh_code(fcode)
        sw = mesh.south_west
        ne = sw+ mesh.size
        lng1 = str(sw.lon.degree)
        lng2 = str(ne.lon.degree)
        lat1 = str(ne.lat.degree)
        lat2 = str(sw.lat.degree)
        for occ in ['residential', 'non-residential']:
            url_add_run='http://platform.openquake.org/exposure/export_exposure?output_type=csv&sr_id=113&occupancy_filter='+occ+'&lng1='+lng1+'&lat1='+lat1+'&lng2='+lng2+'&lat2='+lat2
            output = open('Exposure/'+occ+'/'+fcode+'.csv', 'wb')
            print(fcode)
            r2=client.get(url_add_run, stream=True)
            for data in tqdm(r2.iter_content()):
                output.write(data)
            output.close()
            print(r2.status_code)


def scrap_consequences():
    eq_code = str(134)
    url_add_run = 'https://platform.openquake.org/ecd/eventoverview/' + eq_code + '?&zoomtoextent=True&f_b=False&f_c=False&f_i=False&f_p=False&f_s=False&all=True'
    file_name = 'Consequences/' + eq_code + '.txt'
    output = open(file_name, 'wb')
    print client
    r2 = client.get(url_add_run, stream=True)
    print r2.status_code
    for data in tqdm(r2.iter_content()):
        print data
        output.write(data)
    output.close()
    data = open(file_name).readlines()
    print data.split('')

# scrap_consequences()