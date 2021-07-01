from segment import Segment
from point import PolyPoint
from trip import Trip


def roadcon(tnc_audit_get, points_get, segments_get, segment_points_get, connections_get, congestion_stats_get, logger):
    # main function
    # create segments
    segments = [Segment(int(row['segment_id']), row['segment_name'], row['segment_description'])
                for row in segments_get]
    logger.info('segments_created')

    # create polyline points
    poly_points = [PolyPoint(int(row['point_id']), float(row['latitude']), float(row['longitude']))
                   for row in points_get]

    # link poly points together (form directed graph)
    point_ids = [point.id for point in poly_points]  # list of point ids
    for row in connections_get:
        point1 = poly_points[point_ids.index(int(row['point1']))]  # current point
        point2 = poly_points[point_ids.index(int(row['point2']))]  # linked point
        point1.linked_points.append(point2)  # link point 2 to point 1
    for point in poly_points:
        point.exhaustive_search(point)

    # link polyline points to segments (so trip will know which segments it passed through)
    segment_ids = [segment.id for segment in segments]
    for row in segment_points_get:
        point = poly_points[point_ids.index(int(row['point_id']))]
        segment = segments[segment_ids.index(int(row['segment_id']))]
        point.segments.append(segment)

    # create trips, link to poly points
    trips = [Trip(int(row['delta_t']), float(row['origin_lat']), float(row['origin_lon']),
                  float(row['destination_lat']), float(row['destination_lon']), poly_points)
             for row in tnc_audit_get]
    trips = [trip for trip in trips if trip.origin.poly_point is not None]  # valid trips (has o/d point snaps)
    for trip in trips:  # get segment distances
        trip.get_route(segments)
    trips = [trip for trip in trips if trip.total_distance() > 0]  # valid trips (has total distance > X meters)

    # sample size
    for segment in segments:
        segment.sample_size(trips)

    # calculate speed
    for segment in segments:
        segment.get_speed(trips)

    # congestion
    segment_id = [int(row['segment_id']) for row in congestion_stats_get]
    speed = [float(row['speed']) for row in congestion_stats_get]
    for segment in segments:
        segment.get_congestion(segment_id, speed)

    # generate output
    update_id = max([stats['update_id'] for stats in congestion_stats_get]) + 1  # update id
    update_time = tnc_audit_get[0]['local_tnc_timestamp']  # first timestamp is newest (local may be removed - UTC)
    results = []
    for segment in segments:
        results.append({'update_time': update_time,
                        'update_id': update_id,
                        'segment_id': segment.id,
                        'speed': segment.speed,
                        'sample_size': segment.sample,
                        'confidence': segment.confidence,
                        'congestion': segment.congestion})

    return results
