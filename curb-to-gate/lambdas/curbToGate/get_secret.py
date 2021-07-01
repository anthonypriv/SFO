import boto3
import json


# secret id's for each environment
secrets = {
    'dev': 'dev/pwifi/devpostdb01',
    'tqa': 'tqa/pwifi/tqardspostd',
    'stg': '',  # ADD for stg
    'prd': ''  # ADD for prd
}


def get_secret(env):
    secret_name = secrets[env]
    region_name = "us-west-2"

    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name,)

    secret_value = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(secret_value['SecretString'])  # convert to dict
    
    return secret
