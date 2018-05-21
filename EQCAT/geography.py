from haversine import haversine
from jpmesh import Angle, Coordinate, QuarterMesh, FirstMesh, ThirdMesh, parse_mesh_code
from shapely.geometry import Point, shape
import pandas as pd
import shapefile
from shapely.geometry import Polygon


exposure_path = '../04-Exposure/'
admin_path = 'Administrative/'
pref_shape_path = 'Japan_adm1'
Prefecture = shapefile.Reader(exposure_path + admin_path + pref_shape_path)
pref = pd.DataFrame(columns=['ID', 'Name', 'Shape'])
pref['ID'] = [r[3] for r in Prefecture.records()]
pref['Name'] = [r[4] for r in Prefecture.records()]
pref['Shape'] = [shape(s) for s in Prefecture.shapes()]

def cartesian(lat, lon):
    #  Convert lat, long to x, y in km
    #  Projection with fundamental point = Azabudai, Minato-ku, Tokyo
    reference = (35.658099, 139.741358)  # (lat, lon)
    if lon >= reference[1]:
        x = haversine(reference, (reference[0], lon))
    else:
        x = -haversine(reference, (reference[0], lon))
    if lat >= reference[0]:
        y = haversine(reference, (lat, reference[1]))
    else:
        y = -haversine(reference, (lat, reference[1]))
    return x, y


def first_meshcode(row):
    # lat = min([max([row['lat'], 20]), 46])
    # lon = min([max([row['lon'], 122]), 154])
    coordinate = Coordinate(lon=Angle.from_degree(row['lon']), lat=Angle.from_degree(row['lat']))
    mesh = FirstMesh.from_coordinate(coordinate)
    return pd.Series(dict(fcode=int(mesh.code)))


def quarter_meshcode(row):
    coordinate = Coordinate(lon=Angle.from_degree(row['lon']), lat=Angle.from_degree(row['lat']))
    mesh = QuarterMesh.from_coordinate(coordinate)
    return pd.Series(dict(qcode=int(mesh.code)))


def prefecture(row):
    lat, lon = row['lat'], row['lon']
    pt = Point(lon, lat)
    pref_df = pref
    pref_df['contain'] = pref_df.apply(lambda l: l['Shape'].contains(pt), axis=1)
    pref_df.sort_values('contain', ascending=False, inplace=True)
    if not pref_df.iloc[0]['contain']:
        pref_df['distance'] = pref_df.apply(lambda l: l['Shape'].distance(pt), axis=1)
        pref_df.sort_values('distance', inplace=True)
        pref_row = pref_df.iloc[0]
    else:
        pref_row = pref_df.iloc[0]
    return pd.Series(dict(pref_id=pref_row['ID'], pref_name=pref_row['Name']))


def fmesh_distance(mesh, quake_shape, radius):
    mesh = parse_mesh_code(mesh)
    lon_min = mesh.south_west.lon.degree
    lat_min = mesh.south_west.lat.degree
    lon_max = lon_min + mesh.size.lon.degree
    lat_max = lat_min + mesh.size.lat.degree
    sw = cartesian(lat_min, lon_min)
    se = cartesian(lat_min, lon_max)
    ne = cartesian(lat_max, lon_max)
    nw = cartesian(lat_max, lon_min)
    shape = Polygon([sw, se, ne, nw, sw])
    dist = quake_shape.fmesh_distance(shape)
    if dist < radius:
        return True
    else:
        return False
