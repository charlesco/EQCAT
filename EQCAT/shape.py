from shapely.geometry import LineString, Point, Polygon, MultiPoint
import pandas as pd
from math import cos, sin, pi, sqrt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.pyplot as plt
from haversine import haversine


class BaseShape(object):
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon
        self.lat_km = haversine((lat, lon), (lat + 1, lon))
        self.lon_km = haversine((lat, lon), (lat, lon + 1))
        self.shape = None
        self.depth = None

    def fmesh_distance(self, square):
        d = self.shape.distance(square)
        return round(sqrt(d**2 + self.depth**2), 1)

    def distance(self, row):
        pt = Point((row['lon'] - self.lon) * self.lon_km, (row['lat'] - self.lat) * self.lat_km)
        return self.shape.distance(pt)

    def distance2(self, row):
        return pd.Series(dict(distance=self.distance(row), depth=self.depth))


class MultiBaseShape(object):
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon
        self.lat_km = haversine((lat, lon), (lat + 1, lon))
        self.lon_km = haversine((lat, lon), (lat, lon + 1))
        self.shape_list = []
        self.depth = None

    def fmesh_distance(self, square):
        dist_list = [shape.fmesh_distance(square) for shape in self.shape_list]
        return min(dist_list)

    def distance(self, row):
        dist_list = [shape.distance(row) for shape in self.shape_list]
        return min(dist_list)

    def distance2(self, row):
        dist_list = [shape.distance(row) for shape in self.shape_list]
        dist = min(dist_list)
        i = dist_list.index(dist)
        dep = self.shape_list[i].depth
        return pd.Series(dict(distance=dist, depth=dep))


class PlaneShape(BaseShape):
    def __init__(self, idx, lon, lat, depth, length, width, strike, dip):
        super(self.__class__, self).__init__(lat, lon)
        self.id = idx
        self.depth = float(depth)
        self.length = float(length)
        self.width = float(width)
        self.strike = float(strike) * 2 * pi / 360
        self.dip = float(dip) * 2 * pi / 360
        self.pnt1_coord = (self.lat, self.lon)
        self.pnt1_xyz = (0, 0, self.depth)
        self.pnt2_xyz = (sin(self.strike) * self.length, cos(self.strike) * self.length, self.depth)
        self.pnt2_coord = (self.lon + self.pnt2_xyz[0] / self.lon_km,
                           self.lat + self.pnt2_xyz[1] / self.lat_km)
        if dip != 90.0:
            self.pnt3_xyz = (self.pnt2_xyz[0] + cos(self.strike) * cos(self.dip) * self.width,
                             self.pnt2_xyz[1] - sin(self.strike) * cos(self.dip) * self.width,
                             sin(self.dip) * self.width)
            self.pnt3_coord = (self.lon + self.pnt3_xyz[0] / self.lon_km,
                               self.lat + self.pnt3_xyz[1] / self.lat_km)
            self.pnt4_xyz = (cos(self.strike) * cos(self.dip) * self.width,
                             -sin(self.strike) * cos(self.dip) * self.width,
                             sin(self.dip) * self.width)
            self.pnt4_coord = (self.lon + self.pnt4_xyz[0] / self.lon_km,
                               self.lat + self.pnt4_xyz[1] / self.lat_km)
            self.shape = Polygon([(xyz[0], xyz[1]) for xyz in [self.pnt1_xyz, self.pnt2_xyz, self.pnt3_xyz,
                                                               self.pnt4_xyz, self.pnt1_xyz]])
        else:
            self.pnt3_xyz = (self.pnt2_xyz[0], self.pnt2_xyz[1], self.pnt2_xyz[2] + self.width)
            self.pnt3_coord = self.pnt2_coord
            self.pnt4_xyz = (self.pnt1_xyz[0], self.pnt1_xyz[1], self.pnt1_xyz[2] + self.width)
            self.pnt4_coord = self.pnt1_coord
            self.shape = LineString([(xyz[0], xyz[1]) for xyz in [self.pnt1_xyz, self.pnt2_xyz]])
        if not self.shape.is_valid:
            print("Warning : Invalid Shape")
            print(self.desc())

    def desc(self):
        out = "PLN((lat=" + str(round(self.pnt1_coord[0], 2)) + ",lon=" + str(round(self.pnt1_coord[1], 2)) +\
              ",dep=" + str(round(self.pnt1_xyz[2])) + "),(lat=" + str(round(self.pnt2_coord[0], 2)) + ",lon=" +\
              str(round(self.pnt2_coord[1], 2)) + ",dep=" + str(round(self.pnt2_xyz[2])) + "),(lat=" +\
              str(round(self.pnt3_coord[0], 2)) + ",lon=" + str(round(self.pnt3_coord[1], 2)) + ",dep=" +\
              str(round(self.pnt3_xyz[2])) + "),(lat=" + str(round(self.pnt4_coord[0], 2)) + ",lon=" +\
              str(round(self.pnt4_coord[1], 2)) + ",dep=" + str(round(self.pnt4_xyz[2])) + "))"
        return out

    def plot3d(self):
        fig = plt.figure()
        ax = Axes3D(fig)
        xyz_list = [self.pnt1_xyz, self.pnt2_xyz, self.pnt3_xyz, self.pnt4_xyz]
        x, y = [], []
        for xyz in xyz_list:
            x += [xyz[0]]
            y += [xyz[1]]
        coord_list = [self.pnt1_coord, self.pnt2_coord, self.pnt3_coord, self.pnt4_coord]
        z = [-coord[2] for coord in coord_list]
        verts = [zip(x, y, z)]
        ax.add_collection3d(Poly3DCollection(verts))
        ax.set_xlim(min(x), max(x))
        ax.set_ylim(min(y), max(y))
        ax.set_zlim(min(z), max(z))
        ax.autoscale_view()
        plt.show()


class PointShape(BaseShape):
    def __init__(self, idx, lon, lat, depth):
        super(self.__class__, self).__init__(lat, lon)
        self.id = idx
        self.depth = depth
        self.pnt_coord = (lat, lon)
        self.pnt_xyz = (0, 0, self.depth)
        self.shape = Point(0, 0)
        if not self.shape.is_valid:
            print("Warning")

    def desc(self):
        return "PNT(lat=" + str(round(self.pnt_coord[0], 2)) + ",lon=" + str(round(self.pnt_coord[1], 2)) + ",d=" +\
               str(round(self.pnt_xyz[2])) + ")"

    def plot3d(self):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter([self.pnt_coord[0]], [self.pnt_coord[1]], [self.pnt_xyz[2]], c='r', marker='o')
        plt.show()


class MultiPointShape(BaseShape):
    def __init__(self, pnt_list, depth):
        center = MultiPoint([(p.lon, p.lat) for p in pnt_list]).centroid
        lon, lat = center.x, center.y
        super(self.__class__, self).__init__(lat, lon)
        self.shape = MultiPoint([p.shape for p in pnt_list])
        if not self.shape.is_valid:
            print("Warning")
        self.depth = depth
        self.pnt_list = pnt_list

    def desc(self):
        out = "MLTPNT("
        for pnt in self.pnt_list:
            out += pnt.desc() + ","
        return out[:-1] + ")"

    def plot3d(self):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        x = []
        y = []
        z = []
        for p in self.pnt_list:
            x += [p.pnt_coord[0]]
            y += [p.pnt_coord[1]]
            z += [-p.pnt_xyz[2]]
        ax.scatter(x, y, z, c='r', marker='o')
        plt.show()


class MultiPlaneShape(MultiBaseShape):
    def __init__(self, pln_list):
        center = MultiPoint([(p.lon, p.lat) for p in pln_list]).centroid
        lon, lat = center.x, center.y
        super(self.__class__, self).__init__(lat, lon)
        self.shape_list = pln_list
        self.depth = min([pln.depth for pln in self.shape_list])

    def desc(self):
        out = "MLTPLN("
        for shp in self.shape_list:
            out += shp.desc() + ","
        return out[:-1] + ")"

    def plot3d(self):
        fig = plt.figure()
        ax = Axes3D(fig)
        x_tot, y_tot, z_tot = [], [], []
        for pln in self.shape_list:
            xyz_list = [pln.pnt1_xyz, pln.pnt2_xyz, pln.pnt3_xyz, pln.pnt4_xyz]
            x, y = [], []
            for xyz in xyz_list:
                x += [xyz[0]]
                y += [xyz[1]]
            coord_list = [pln.pnt1_coord, pln.pnt2_coord, pln.pnt3_coord, pln.pnt4_coord]
            z = [-coord[2] for coord in coord_list]
            x_tot += x
            y_tot += y
            z_tot += z
            verts = [zip(x, y, z)]
            ax.add_collection3d(Poly3DCollection(verts))
        ax.set_xlim(min(x_tot), max(x_tot))
        ax.set_ylim(min(y_tot), max(y_tot))
        ax.set_zlim(min(z_tot), max(z_tot))
        plt.show()
