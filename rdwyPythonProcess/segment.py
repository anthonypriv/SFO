import math
from aux_funs import mean, std


class Segment:
    # road segment object
    def __init__(self, segment_id, name, description):
        self.id = segment_id
        self.name = name
        self.description = description
        self.speed = 0  # calculated speed
        self.sample = 0  # sample size
        self.congestion = .5  # congestion rating (0 - 1)
        self.confidence = 0  # confidence interval
        return

    def sample_size(self, trips):
        for trip in trips:
            if trip.seg_dist[self.id] > 0:
                self.sample += 1
        return

    def get_speed(self, trips):
        # weighted aggregate speed
        conversion = 2.23694  # m/s to mph
        speeds = []
        d_frac = []
        for trip in trips:
            d_seg = trip.seg_dist[self.id]
            if d_seg > 0:
                d = sum([trip.seg_dist[key] for key in trip.seg_dist])
                speed = d / trip.delta_t
                if 0 < speed < 60:  # reasonable speed range
                    speeds.append(d / trip.delta_t)
                    d_frac.append(d_seg / d)

        if len(speeds) > 0:  # samples exist
            self.speed = mean([speeds[i] * d_frac[i] for i in range(len(speeds))]) / mean(d_frac) * conversion
            self.get_confidence(speeds, d_frac)  # confidence interval
        return

    def get_congestion(self, segment_id, speed):
        # get congestion rating from historical speeds
        # speed distribution
        speeds = []
        for i in range(len(segment_id)):
            if segment_id[i] == self.id:
                speeds.append(speed[i])
        # speed fix
        if (self.speed == 0) and len(speeds) > 0:
            self.speed = speeds[-1]  # set speed to last speed
        # percentile rank
        if len(speeds) > 0:
            self.congestion = self.percentile_rank(speeds, self.speed)
        return

    def get_confidence(self, speed, d_frac):
        # get confidence interval range
        if self.sample > 0:
            m = mean(d_frac)
            samples = [speed[i] * d_frac[i] / m for i in range(len(speed))]
            standard_error = std(samples) / math.sqrt(self.sample)  # make sure sample is calculated before speed
            t_star = self.t_ppf(self.sample)  # t score
            self.confidence = t_star * standard_error
        return

    @staticmethod
    def percentile_rank(dist, score):
        # get the percentile rank of a score in a distribution
        cf = sum([True for x in dist if x < score])  # number of elements below score
        f = sum([True for x in dist if x == score])  # frequency of score
        return (cf + .5 * f) / len(dist)

    @staticmethod
    def t_ppf(sample_size, confidence_interval=.9):
        # find t score for confidence interval
        # confidence interval options are: .8, .9, .95, .99
        n = [1, 2, 5, 10, 20, 50, 100, 200, 500, 10 ** 9]  # sample sizes
        # t*
        ci_80 = [3.078, 1.886, 1.476, 1.372, 1.325, 1.299, 1.29, 1.286, 1.283, 1.282]
        ci_90 = [6.314, 2.92, 2.015, 1.812, 1.725, 1.676, 1.66, 1.652, 1.648, 1.645]
        ci_95 = [12.706, 4.303, 2.571, 2.228, 2.086, 2.009, 1.984, 1.972, 1.965, 1.96]
        ci_99 = [63.657, 9.925, 4.032, 3.169, 2.845, 2.678, 2.626, 2.601, 2.586, 2.576]

        # interpolate ci value between 2 sample sizes
        low = 0
        high = 0
        for i in range(len(n) - 1):
            if n[i] <= sample_size < n[i + 1]:
                low = i
                high = i + 1
                break
        d = (sample_size - n[low]) / (n[low + 1] - n[low])

        if confidence_interval == .8:
            t = ci_80[low] + (ci_80[high] - ci_80[low]) * d
        elif confidence_interval == .9:
            t = ci_90[low] + (ci_90[high] - ci_90[low]) * d
        elif confidence_interval == .95:
            t = ci_95[low] + (ci_95[high] - ci_95[low]) * d
        elif confidence_interval == .99:
            t = ci_99[low] + (ci_99[high] - ci_99[low]) * d
        else:
            t = 2
        return t
