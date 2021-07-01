from botocore.vendored import requests  # replaces requests library in lambda
# import requests  # for local testing
import logging
from roadcon import roadcon

# set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get(base_url, header, endpoint, params):
    # get call to web service
    param_string = '/'
    for key in params:
        param_string += str(key) + '=' + str(params[key]) + '/'
    param_string = param_string[:-1]
    request_string = base_url + '/' + endpoint + param_string
    call = requests.get(request_string, headers=header)
    if call.status_code == 200:
        return call.json()
    return None


def post(base_url, header, endpoint, congestion_stats):
    requests.post(base_url + '/' + endpoint, headers=header, json=congestion_stats)
    return


def lambda_handler(event, context):
    # api requests
    base_url = 'https://api.sfo-cloud.com/rdwy/prd'  # change url
    header = {'x-api-key': 'BHUvx6qjuJ2Klp7dNV235jLDn0tb8UQp1pi8Azf0'}  # change api key
    logger.info('base url: ' + base_url)

    segments = get(base_url, header, 'segments', {})['results']
    points = get(base_url, header, 'points', {})['results']
    connections = get(base_url, header, 'connections', {})['results']
    segment_points = get(base_url, header, 'segment-points', {})['results']
    tnc_audit = get(base_url, header, 'tnc', {})['results']
    congestion_stats = get(base_url, header, 'congestions', {})['results']
    logger.info('GET calls made')

    # run roadcon
    outputs = roadcon(tnc_audit, points, segments, segment_points, connections, congestion_stats, logger)
    logger.info(outputs)

    # post to congestion stats
    post(base_url, header, 'congestions', outputs)
    logger.info('posted congestion stats')

    return
