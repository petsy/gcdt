import boto3
import logger
from datetime import tzinfo, timedelta, datetime

ZERO = timedelta(0)

class UTC(tzinfo):
  def utcoffset(self, dt):
    return ZERO
  def tzname(self, dt):
    return "UTC"
  def dst(self, dt):
    return ZERO


# gets Outputs for a given StackName
def get_outputs_for_stack(stack_name):
    cf = boto3.client("cloudformation")
    response = cf.describe_stacks(StackName=stack_name)
    result = {}
    for output in response["Stacks"][0]["Outputs"]:
        result[output["OutputKey"]] = output["OutputValue"]
    return result

def get_ssl_certificate(domain):
    client = boto3.client("iam")
    response = client.list_server_certificates()
    arn = ""
    for cert in response["ServerCertificateMetadataList"]:
        if domain in cert["ServerCertificateName"]:
            if datetime.now(UTC()) > cert['Expiration']:
                logger.debug("certificate has expired")
            else:
                arn = cert["Arn"]
                break
    return arn