"""Decomp training functions"""

import datetime as dt
from aux_functions import mean, std, linear_regression, smooth, day_data, rmse, sort_data


def get_trend(date_keys, vals, trend_keys, aggregator, s=0):
	"""Get trend from data
	date_keys = trend-specific keys for date values
	vals = demand values
	trend_keys = keys for trend
	aggregator = mean() or std() to aggregate values
	"""
	trend = {str(key): [] for key in trend_keys}  # {key: [values]}
	for key, val in zip(date_keys, vals):
		trend[key].append(val)
	trend = {key: aggregator(values) for key, values in trend.items()}  # {key: value}
	if s > 0:  # smoothing
		smoothed = smooth(list(trend.values()), s=s)
		trend = {key: value for key, value in zip(list(trend.keys()), smoothed)}  # apply smoothing
	trend_vals = [trend[key] for key in date_keys]
	trend_removed = [val / trend_val for val, trend_val in zip(vals, trend_vals)]
	return trend, trend_vals, trend_removed  # ternd lookup, trend values, trend removed from vals


def decomposition(data):
	"""Trend decomposition model
	data - dates and vals
	"""
	# split data into dates and exits (vals)
	dates = [dt.datetime.strptime(key, '%Y-%m-%d %H:%M:%S') for key in data.keys()]  # unsorted dates
	vals = [value['exits'] for value in data.values()]
	dates, vals = sort_data(dates, vals)

	# time interval
	n = min([(dates1 - dates0).seconds for dates1, dates0 in zip(dates[1:], dates[:-1])])

	# aggregate data by day for faster processing
	day_dates, day_vals = day_data(dates, vals)

	# mean
	average = mean(day_vals)
	mean_removed = [v / average for v in day_vals]

	# long term
	step = int(364/2)  # 6 months on either side (centered moving average)
	moving_avg = [mean(mean_removed[i-step:i+step]) for i in range(step, len(day_vals)-step)]  # year-long moving average
	a, b = linear_regression(range(step, len(day_vals)-step), moving_avg)  # linear regression coeffs
	trend = [a + b*x for x in range(len(day_vals))]  # long term trend
	trend_removed = [mean_removed[i] / trend[i] for i in range(len(day_vals))]  # long term trend removed

	# seasonality
	seasonal_trend, seasonal, season_removed = get_trend([str(date.timetuple().tm_yday) for date in day_dates], trend_removed, range(1, 366), mean, s=7)

	# weekday
	weekly_trend, weekly, _ = get_trend([str(date.weekday()) for date in day_dates], season_removed, range(7), mean)

	# daily & noise
	# remove trends from original data
	weekly_removed = []
	for date, val in zip(dates, vals):
		i = day_dates.index(date.date())
		weekly_removed.append(val / (average * trend[i] * seasonal[i] * weekly[i]))
	hms = ['%s-%s' % (h, m) for h in range(24) for m in range(0,60,5)]
	whms = ['%s-%s' % (w, hm) for w in range(7) for hm in hms]
	daily_trend, daily, daily_removed = get_trend(['%s-%s-%s' % (date.weekday(), date.hour, date.minute) for date in dates], weekly_removed, whms, mean, s=2)
	noise_trend, noise_std, _ = get_trend(['%s-%s' % (date.hour, date.minute) for date in dates], daily_removed, hms, std, s=2)

	trends = {  # only model data for prediction (smaller)
		'n': n,
		'mean': average,  # mean
		'long_term': {'start_date': str(day_dates[0]), 'b0': a, 'b1': b},  # {start_date, b0, b1}
		'seasonal': seasonal_trend,  # {month: value}
		'weekly': weekly_trend,  # {day: value}
		'daily': daily_trend,  # {day-hour-minute: value}
		'noise': noise_trend  # {hour-minute: value} - std of noise at time
	}
	return trends


def validate_decomp(trends, data):
	"""Validate model using test data
	trends = model
	data = test data
	"""
	# split data into dates and exits (vals)
	dates = [dt.datetime.strptime(key, '%Y-%m-%d %H:%M:%S') for key in data.keys()]
	vals = [value['exits'] for value in data.values()]

	predictions = [predict_decomp(trends, date) for date in dates]  # get prediction for each date
	errors = [predictions[i] - vals[i] for i in range(len(dates))]
	trends['rmse'] = rmse(errors) / trends['mean']


def predict_decomp(trends, time):
	"""Predict demand for each pred_time"""
	days = (time - dt.datetime.strptime(trends['long_term']['start_date'], '%Y-%m-%d')).days  # days since training start
	long_term = trends['long_term']['b0'] + trends['long_term']['b1'] * days  # long term component
	doy = time.timetuple().tm_yday  # day of year
	doy = doy - 1 if doy > 365 else doy  # leap year catch
	seasonal = trends['seasonal'][str(doy)]  # seasonal component
	weekly = trends['weekly'][str(time.weekday())]  # weekly component
	daily = trends['daily']['%s-%s-%s' % (time.weekday(), time.hour, time.minute)]
	pred = trends['mean'] * long_term * seasonal * weekly * daily
	return pred
