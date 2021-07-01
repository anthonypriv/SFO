# auxiliary functions
import math


def mean(x):
    # get the mean of a list
    return sum(x) / len(x)


def std(x):
    # get standard deviation of list
    u = mean(x)  # sample mean
    var = [(xx - u)**2 for xx in x]  # difference from mean
    return math.sqrt(mean(var))
