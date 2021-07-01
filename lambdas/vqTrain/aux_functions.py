"""Decomp aux functions"""

import datetime as dt


def mean(x):
	"""Get mean value of list"""
	return sum(x) / len(x)  # if len(x) > 0 else 0


def std(x):
	"""Standard deviation"""
	u = mean(x)
	return (sum([(xx - u)**2 for xx in x]) / (len(x)-1)) ** .5


def rmse(errors):
	"""root mean squared error"""
	return mean([error**2 for error in errors]) ** .5


def linear_regression(x, y):
	"""Find average slope (proxy for linear regression"""
	slopes = []
	for i in range(len(x)):  # i = starting location
		for j in range(i+1, len(x)):  # j = destination location
			slopes.append((y[j] - y[i]) / (x[j] - x[i]))
	b = mean(slopes)
	a = mean(y) - b * mean(x)
	return a, b


def smooth(data, s=1):
	"""Smooth data over interval s (moving average)"""
	padded = data[len(data)-s:] + data + data[:s]  # pad data
	smoothed = [mean(padded[i-s:i+s+1]) for i in range(s, len(padded)-s)]  # smooth padded data
	return smoothed


def day_data(dates, vals):
	"""Aggregate data by day"""
	day_dat = {}
	for date, val in zip(dates, vals):
		day_dat.setdefault(str(date.date()), []).append(val)
	day_dates = [dt.datetime.strptime(date, '%Y-%m-%d').date() for date in day_dat]
	day_values = [mean(values) for date, values in day_dat.items()]
	return day_dates, day_values


def sort_data(keys, vals):
	"""Sort keys and vals by keys ascending"""
	sidx = sorted(range(len(keys)), key=lambda k: keys[k])  # sorted index
	keys_sort = [keys[i] for i in sidx]  # sort keys
	vals_sort = [vals[i] for i in sidx]  # sort vals
	return keys_sort, vals_sort
