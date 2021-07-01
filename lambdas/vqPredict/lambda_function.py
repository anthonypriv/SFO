"""Predict taxi demand"""

import json
import boto3
import datetime as dt
import decomp


s3 = boto3.resource('s3')


def predict(predictor, model_info, time, window, recent):
	"""Run predictor to get prediction(s)
	predictor = prediction function from model
	model_info = model info
	time = time of prediction (datetime)
	window = how far forward does forecast go (minutes)
	recent = recent data (dict - [{time, exits}])
	"""
	# find offset
	n = model_info['n']  # data time interval (seconds)
	offset = (time.minute*60 + time.second) % n  # offset between time and data interval
	f1 = 1 - offset/n  # factor for first prediction (fraction of first prediction not elapsed)
	f2 = offset/n  # factor for last prediction (fraction of last prediction needed)

	# get prediction times
	pred_times = [time - dt.timedelta(seconds=offset) + dt.timedelta(seconds=n*i) for i in range(int(window*60/n)+1)]  # times to predict at
	start_times = [time] + pred_times[1:]  # if more than 1 pred time
	end_times = pred_times[1:] + [pred_times[-1] + dt.timedelta(seconds=offset)]
	print('pred times:', [str(p) for p in pred_times])
	print('start times:', [str(p) for p in start_times])
	print('end times:', [str(p) for p in end_times])

	# get prediction for each time
	preds, var = ([], [])
	for ptime in pred_times:
		p, v = predictor(model_info, ptime)  # make prediction for time ptime
		preds.append(p)  # predictions
		var.append(v)  # variance

	# adjust first/last preds based on offset
	preds[0] *= f1
	var[0] *= f1
	preds[-1] *= f2
	var[-1] *= f2

	# adjust predictions if recent (get prediction for each recent time, scale based on mean error from actual recents (actual / pred))
	if recent:
		recent_times = [dt.datetime.strptime(r['time'], '%Y-%m-%d %H:%M:%S') for r in recent]
		recent_preds = [predictor(model_info, rtime)[0] for rtime in recent_times]
		factor = sum([recent[i]['exits'] / recent_preds[i] for i in range(len(recent))]) / len(recent)  # mean actual / pred fraction
		print('recent factor:', factor)
		preds = [p * factor for p in preds]  # scale preds
		var = [v * factor for v in var]  # scale vars

	# return all predictions and aggregate -- {total_pred, total_std, intervals: {time, pred, std}}
	prediction = {
		'total_prediction': sum(preds),
		'total_std': sum(var) ** .5,
		'time': str(time),  # prediction time
		'intervals': [{
			'start_time': str(start_times[i]),
			'end_time': str(end_times[i]),
			'prediction': preds[i],
			'std': var[i]**.5}
			for i in range(len(preds))]
	}
	return prediction


def lambda_handler(event, context):
	# get query string params
	params = event['queryStringParameters'] if type(event['queryStringParameters']) is dict else {}  # query string params
	bucket = params['bucket'] if 'bucket' in params else 'sfo-dev-virtualqueue'  # s3 bucket name
	model = params['model'] if 'model' in params else 'decomp'  # get model
	time = dt.datetime.strptime(params['time'], '%Y-%m-%d %H:%M:%S') if 'time' in params else dt.datetime.utcnow()
	window = int(params['window']) if 'window' in params else 30
	recent = json.loads(params['recent']) if 'recent' in params else None
	print('params:', {'bucket': bucket, 'model': model, 'time': str(time), 'window': window, 'recent': recent})  # log params

	# get model info
	key = 'models/%s.json' % model
	obj = s3.Object(bucket, key)
	model_info = json.loads(obj.get()['Body'].read().decode('utf-8'))

	# get predictor
	predictor = decomp.predict_decomp if model == 'decomp' else None

	# get prediction
	prediction = predict(predictor, model_info, time, window, recent)
	print('prediction:', prediction)  # log prediction

	return {
		'statusCode': 200,
		'body': json.dumps(prediction)
	}
