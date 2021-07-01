"""Decomp predict"""

import datetime as dt


def predict_decomp(trends, time):
	"""Predict demand for each pred_time"""
	days = (time - dt.datetime.strptime(trends['long_term']['start_date'], '%Y-%m-%d')).days  # days since training start
	long_term = trends['long_term']['b0'] + trends['long_term']['b1'] * days  # long term component
	doy = time.timetuple().tm_yday  # day of year
	doy = doy - 1 if doy > 365 else doy  # leap year catch
	seasonal = trends['seasonal'][str(doy)]  # seasonal component
	weekly = trends['weekly'][str(time.weekday())]  # weekly component
	daily = trends['daily']['%s-%s-%s' % (time.weekday(), time.hour, time.minute)]
	pred = trends['mean'] * long_term * seasonal * weekly * daily  # prediction
	var = (trends['noise']['%s-%s' % (time.hour, time.minute)] * pred) ** 2  # variance
	return pred, var
