from shapely.geometry import LineString, Point, Polygon, MultiPoint
import pandas as pd
from math import cos, sin, pi, sqrt
from geography import cartesian
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.pyplot as plt


class BaseShape(object):
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon
        self.shape = None
        self.depth = None

    def fmesh_distance(self, square):
        d = self.shape.distance(square)
        return round(sqrt(d**2 + self.depth**2), 1)

    def distance(self, row):
        pt = Point(cartesian(row['lat'], row['lon']))
        return self.shape.distance(pt)

    def distance2(self, row):
        return pd.Series(dict(distance=self.distance(row), depth=self.depth))


class MultiBaseShape(object):
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon
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
        lon = float(lon)
        lat = float(lat)
        depth = float(depth)
        length = float(length)
        width = float(width)
        strike = float(strike) * 2 * pi / 360
        x_origin, y_origin = cartesian(lat, lon)
        pnt1 = (x_origin, y_origin)
        self.pnt1 = (x_origin, y_origin, depth)
        pnt2 = (x_origin + sin(strike) * length, y_origin + cos(strike) * length)
        self.pnt2 = (x_origin + sin(strike) * length, y_origin + cos(strike) * length, depth)
        if dip != 90.0:
            dip = float(dip) * 2 * pi / 360
            pnt3 = (pnt2[0] + cos(strike) * cos(dip) * width, pnt2[1] - sin(strike) * cos(dip) * width)
            self.pnt3 = (pnt2[0] + cos(strike) * cos(dip) * width, pnt2[1] - sin(strike) * cos(dip) * width,
                         sin(dip) * width)
            pnt4 = (pnt1[0] + cos(strike) * cos(dip) * width, pnt1[1] - sin(strike) * cos(dip) * width)
            self.pnt4 = (pnt1[0] + cos(strike) * cos(dip) * width, pnt1[1] - sin(strike) * cos(dip) * width,
                         sin(dip) * width)
            self.shape = Polygon([pnt1, pnt2, pnt3, pnt4, pnt1])
        else:
            self.shape = LineString([pnt1, pnt2])
            self.pnt3 = (x_origin + sin(strike) * length, y_origin + cos(strike) * length, depth + width)
            self.pnt4 = (x_origin, y_origin, depth + width)
        self.depth = depth
        self.length = length
        self.width = width
        self.strike = strike
        self.dip = dip
        if not self.shape.is_valid:
            print("Warning : Invalid Shape")

    def desc(self):
        out = "PLN("
        for pnt in [self.pnt1, self.pnt2, self.pnt3, self.pnt4]:
            out += "(x=" + str(round(pnt[0], 2)) + ",y=" + str(round(pnt[1], 2)) + ",d=" + str(round(pnt[2])) + ")"
        return out + ")"

    def plot3d(self):
        fig = plt.figure()
        ax = Axes3D(fig)
        pnt_list = [self.pnt1, self.pnt2, self.pnt3, self.pnt4]
        x = []
        y = []
        z = []
        for pnt in pnt_list:
            x += [pnt[0]]
            y += [pnt[1]]
            z += [-pnt[2]]
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
        x, y = cartesian(lat, lon)
        self.shape = Point(x, y)
        self.depth = depth
        self.pnt = (x, y, depth)
        if not self.shape.is_valid:
            print("Warning")

    def desc(self):
        return "PNT(x=" + str(round(self.pnt[0], 2)) + ",y=" + str(round(self.pnt[1], 2)) + ",d=" +\
               str(round(self.pnt[2])) + ")"

    def plot3d(self):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter([self.pnt[0]], [self.pnt[1]], [self.pnt[2]], c='r', marker='o')
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
            x += [p.pnt[0]]
            y += [p.pnt[1]]
            z += [-p.pnt[2]]
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
            pnt_list = [pln.pnt1, pln.pnt2, pln.pnt3, pln.pnt4]
            x, y, z = [], [], []
            for pnt in pnt_list:
                x += [pnt[0]]
                y += [pnt[1]]
                z += [-pnt[2]]
            x_tot += x
            y_tot += y
            z_tot += z
            verts = [zip(x, y, z)]
            ax.add_collection3d(Poly3DCollection(verts))
        ax.set_xlim(min(x_tot), max(x_tot))
        ax.set_ylim(min(y_tot), max(y_tot))
        ax.set_zlim(min(z_tot), max(z_tot))
        plt.show()
