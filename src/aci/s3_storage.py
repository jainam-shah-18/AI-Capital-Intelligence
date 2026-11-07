from pathlib import Path
import boto3
from botocore.exceptions import ClientError

def upload_file(local_path: Path, bucket: str, key: str, region: str) -> None:
    client = boto3.client("s3", region_name=region)
    try:
        client.upload_file(str(local_path), bucket, key)
    except ClientError:
        raise
