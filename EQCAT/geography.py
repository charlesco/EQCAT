from jpmesh import Angle, Coordinate, QuarterMesh, FirstMesh, ThirdMesh, parse_mesh_code
from shapely.geometry import Point, shape
import pandas as pd
import shapefile
from shapely.geometry import Polygon


exposure_path = '../04-Exposure/'
admin_path = 'Administrative/'
pref_shape_path = 'Japan_adm1'


def load_prefs():
    prefecture_shapefile = shapefile.Reader(exposure_path + admin_path + pref_shape_path)
    pref = pd.DataFrame(columns=['ID', 'Name', 'Shape'])
    pref['ID'] = [r[3] for r in prefecture_shapefile.records()]
    pref['Name'] = [r[4] for r in prefecture_shapefile.records()]
    pref['Shape'] = [shape(s) for s in prefecture_shapefile.shapes()]
    return pref


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


def prefecture(row, pref_df):
    lat, lon = row['lat'], row['lon']
    pt = Point(lon, lat)
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
    sw = ((lon_min - quake_shape.lon) * quake_shape.lon_km, (lat_min - quake_shape.lat) * quake_shape.lat_km)
    se = ((lon_max - quake_shape.lon) * quake_shape.lon_km, (lat_min - quake_shape.lat) * quake_shape.lat_km)
    ne = ((lon_max - quake_shape.lon) * quake_shape.lon_km, (lat_max - quake_shape.lat) * quake_shape.lat_km)
    nw = ((lon_min - quake_shape.lon) * quake_shape.lon_km, (lat_max - quake_shape.lat) * quake_shape.lat_km)
    fmesh_shape = Polygon([sw, se, ne, nw, sw])
    dist = quake_shape.fmesh_distance(fmesh_shape)
    if dist < radius:
        return True
    else:
        return False
