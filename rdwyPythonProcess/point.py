import math


class Point:
    # basic point class
    def __init__(self, x, y):
        self.x = x
        self.y = y
        return

    def distance(self, point):
        # distance to another point
        return math.sqrt((self.x - point.x) ** 2 + (self.y - point.y) ** 2)

    def snap_to_line(self, points):
        # find distance to all line segments
        # points - create line segments
        distance = []
        points1 = points
        points2 = []
        for point in points:
            for lp in point.linked_points:
                points2.append(lp)
                d, t = self.dist_to_line(point, lp)
                distance.append(d)
        return distance, points1, points2

    def dist_to_line(self, a, b):
        # snap to point on line between points a and b

        # make point a the origin (pivot axes about point a)
        x0 = self.x - a.x
        y0 = self.y - a.y

        # rotate axes by angle between line ab and x axis
        theta = math.atan((b.y - a.y) / (b.x - a.x))  # angle between ab and x axis
        x1 = x0 * math.cos(theta) + y0 * math.sin(theta)  # transformed x
        y1 = -x0 * math.sin(theta) + y0 * math.cos(theta)  # transformed y

        # segment direction
        bx = (b.x - a.x) * math.cos(theta) + (b.y - a.y) * math.sin(theta)
        if bx > 0:
            direction = 1
        else:
            direction = -1

        d0 = abs(y1)
        r = a.distance(b)  # distance between a and b (line segment length)
        t = x1 / r * direction  # distance along line (normalized by ab length)

        # get distance to line, distance along line
        if 0 <= t <= 1:
            d = d0  # distance to line
            t_line = t * r  # distance along line
        elif t > 1:
            d = math.sqrt((x1 - r)**2 + d0**2) + .01  # prefer previous segment
            t_line = r
        else:  # t < 0
            d = math.sqrt(x1**2 + d0**2)
            t_line = 0

        return d, t_line

    @staticmethod
    def geo_to_meter(lat, lon):
        # convert to meters
        m_per_lat = 110988.9  # meters per lat degree (N/S from equator)
        m_per_lon = 88307.36  # meters per lon degree @ SFO latitude (E/W from prime meridian)
        # origin (SFO)
        lon0 = -122.4
        lat0 = 37.611
        # convert to meters
        lon_meter = (lon - lon0) * m_per_lon
        lat_meter = (lat - lat0) * m_per_lat
        return lon_meter, lat_meter


class PolyPoint(Point):
    # polyline point object
    def __init__(self, point_id, lat, lon):
        x, y = self.geo_to_meter(lat, lon)  # meters
        Point.__init__(self, x, y)
        self.id = int(point_id)
        self.segments = []  # associated segments
        self.linked_points = []  # connected points on graph
        self.sequence_points = []  # all points in sequence after this point
        return

    def exhaustive_search(self, current_point):
        # find all points in sequence using exhaustive search
        # recursive
        for point in current_point.linked_points:
            if point not in self.sequence_points:
                self.sequence_points.append(point)  # add point to sequence points
            self.exhaustive_search(point)
        return


class TNCPoint(Point):
    # tnc ping object
    def __init__(self, lat, lon):
        x, y = self.geo_to_meter(lat, lon)  # convert lat/lon to meters
        Point.__init__(self, x, y)  # point class init
        self.t = 0  # distance along line
        self.poly_point = None  # snapped poly point
        return

    def dist_to_polyline(self, point2):
        d, t = self.dist_to_line(self.poly_point, point2)
        self.t = t
        return
