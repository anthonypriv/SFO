# math functions

from random import choices
from math import radians, sin, cos, atan2, sqrt


def mean(x):
	# get mean value of list x, handle divide by 0 exception
	return sum(x) / len(x) if len(x) > 0 else 0


def median(x):
	# find median of list x
	xsort = sorted(x)
	lenx = len(x)
	if lenx < 1:  # empty
		return None
	elif lenx % 2 == 0:  # even length (take average)
		return (xsort[int(lenx/2-1)] + xsort[int(lenx/2)]) / 2
	else:  # odd length
		return xsort[int(lenx/2)]


def bootstrap(pop, n=1000):
	# use bootstrap sampling method to get mean of medians from population (pop)
	# n = number of bootstrapped samples
	s = len(pop)  # number of samples in each bootstrapped sample
	if len(pop) > 1:
		return mean([median(choices(pop, k=s)) for _ in range(n)])  # mean of medians
	else:
		return pop[0]


def haversine(point0, point1):
	# calculate haversine distance (in meters) between two points (lat, lon)
	# from: https://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
	# more at: https://www.movable-type.co.uk/scripts/latlong.html
	lat0, lon0 = point0
	lat1, lon1 = point1
	radius = 6371000  # Earth's radius in meters

	dlat = radians(lat1 - lat0)
	dlon = radians(lon1 - lon0)
	a = sin(dlat/2)**2 + cos(radians(lat0)) * cos(radians(lat1)) * sin(dlon/2)**2
	c = 2 * atan2(sqrt(a), sqrt(1-a))
	return radius * c
