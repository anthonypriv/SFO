from point import TNCPoint


class Route:
    # tnc route object
    def __init__(self, point):
        self.route = [point]  # poly point (route start)
        return

    def get_distance(self):
        # get distance along route
        if len(self.route) > 1:
            distance = sum([self.route[i].distance(self.route[i+1]) for i in range(len(self.route)-1)])
        else:
            distance = 0
        return distance


class Trip:
    # tnc trip object
    def __init__(self, delta_t, origin_lat, origin_lon, destination_lat, destination_lon, points):
        self.delta_t = delta_t
        self.origin = TNCPoint(origin_lat, origin_lon)
        self.destination = TNCPoint(destination_lat, destination_lon)
        self.seg_dist = {}  # distance on each segment
        self.snap_to_poly_points(points)  # find origin & destination points
        return

    def total_distance(self):
        return sum([self.seg_dist[key] for key in self.seg_dist])

    def snap_to_poly_points(self, points, buffer=25):
        # get origin, destination poly points
        # buffer = max meters from line

        # find valid points
        o_points1, o_points2 = self.valid_segments(self.origin, points, buffer)
        d_points1, d_points2 = self.valid_segments(self.destination, points, buffer)

        if min([len(o_points1), len(d_points1)]) == 0:  # no segments to snap to
            return

        # find distance to all segments, keep best
        o_best = None  # best origin point index
        d_best = None  # best destination point index
        best_dist = 10**6  # best distance
        for o in range(len(o_points1)):
            od, ot = self.origin.dist_to_line(o_points1[o], o_points2[o])
            for d in range(len(d_points1)):
                dd, dt = self.destination.dist_to_line(d_points1[d], d_points2[d])
                if (od < buffer) and (dd < buffer):
                    if (od + dd < best_dist) and (d_points2[d] in o_points1[o].sequence_points):
                        o_best = o
                        d_best = d

        if (o_best is None) or (d_best is None):  # no segments to snap to
            return

        # segment snap found
        self.origin.poly_point = o_points1[o_best]  # origin poly point
        self.destination.poly_point = d_points1[d_best]  # destination poly point
        self.origin.dist_to_polyline(o_points2[o_best])  # distance to origin poly line
        self.destination.dist_to_polyline(d_points2[d_best])  # distance to destination poly line

        return

    def get_route(self, segments):
        # get route travelled along polyline graph
        route = Route(self.origin.poly_point)
        routes = [route]  # start at origin
        while True:
            current_point = route.route[-1]  # current point
            if current_point == self.destination.poly_point:  # destination reached (for best route)
                route = self.get_best_route(routes)  # choose final route
                break
            else:  # keep searching
                branch = False  # add route?
                change = False  # were any routes changed?
                for link_point in current_point.linked_points:  # loop through linked points
                    x = link_point == self.destination.poly_point   # destination is link point
                    if (self.destination.poly_point in link_point.sequence_points) or x:
                        if branch:  # stay on current route
                            route.route.append(link_point)
                            branch = True
                        else:  # branch off from current route
                            new_route = Route(current_point)  # create new route
                            new_route.route = route.route  # copy current route
                            new_route.route.append(link_point)
                            routes.append(new_route)  # add to routes
                        change = True

                if not change:  # dead end -- emergency break
                    break

                # choose new best route
                route = self.get_best_route(routes)

        # get segment distance, adjust for t distance
        for segment in segments:  # init seg_dist
            self.seg_dist[segment.id] = 0

        if self.origin.poly_point == self.destination.poly_point:
            for segment in self.origin.poly_point.segments:
                self.seg_dist[segment.id] += self.destination.t - self.origin.t
        else:
            for i in range(len(route.route)-1):
                point = route.route[i]
                for segment in point.segments:
                    seg_id = segment.id
                    if point == self.destination.poly_point:  # destination reached
                        self.seg_dist[seg_id] += self.destination.t
                    next_point = route.route[i + 1]
                    if point == self.origin.poly_point:  # origin
                        self.seg_dist[seg_id] += point.distance(next_point) - self.origin.t
                    else:  # normal point
                        self.seg_dist[seg_id] += point.distance(next_point)  # line segment traversed

        return

    @staticmethod
    def valid_segments(tnc_point, points, buffer):
        # find valid line segments for distance calculation
        # box around tnc_point of radius = buffer
        points1 = []
        points2 = []
        for point in points:
            for link_point in point.linked_points:
                if (point.x > tnc_point.x + buffer) and (link_point.x > tnc_point.x + buffer):  # right of buffer
                    continue
                elif (point.x < tnc_point.x - buffer) and (link_point.x < tnc_point.x - buffer):  # left of buffer
                    continue
                elif (point.y > tnc_point.y + buffer) and (link_point.y > tnc_point.y + buffer):  # above buffer
                    continue
                elif (point.y < tnc_point.y - buffer) and (link_point.y < tnc_point.y - buffer):  # below buffer
                    continue
                else:  # line segment is within buffer (square) of tnc_point
                    points1.append(point)
                    points2.append(link_point)
        return points1, points2

    @staticmethod
    def get_best_route(routes):
        best_route = 0  # key of best route
        best_dist = 10 ** 6  # best distance
        for route in routes:  # loop through routes
            dist = route.get_distance()
            if dist < best_dist:
                best_dist = dist
                best_route = route
        return best_route
