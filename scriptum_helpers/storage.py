from boto3 import session
from botocore.client import Config

import json
import os


name = os.getenv("BUCKET_NAME", "scriptum-assets")

client = session.Session().client("s3",
    region_name="fra1",
    endpoint_url="https://fra1.digitaloceanspaces.com",
    aws_access_key_id=os.getenv("S3_KEY"),
    aws_secret_access_key=os.getenv("S3_SECRET"),
    config=Config(signature_version="s3v4")
    )


def mkdir(key):
    return client.put_object(
        Bucket=name,
        Key=key
    )

def put(key, value, metadata=None, content_type="json"):
    client.put_object(
        Bucket=name,
        Key=key,
        ContentType="application/%s" % content_type,
        Body=json.dumps(value) if content_type == "json" else value,
        Metadata=metadata if metadata else {}
    )

def upload_fileobj(stream, key, headers):
    client.upload_fileobj(stream,
        name,
        key,
        headers
    )

def get(key, raw=False):
    response = client.get_object(
        Bucket=name,
        Key=key
    )
    if raw:
        return response
    document = response['Body'].read()
    if response["ContentType"] == "application/json":
        document = json.loads(document)
    return document

def list_objects(*prefixes):
    response = client.list_objects_v2(
        Bucket=name,
        Prefix="/".join(prefixes)
    )
    if response["KeyCount"] == 0:
        return []
    return [item["Key"] for item in response["Contents"]]

def metadata(key, meta=None):
    head = client.head_object(
        Bucket=name,
        Key=key
    )
    if meta:
        head["Metadata"].update(meta)
        client.copy_object(
            Bucket=name,
            Key=key,
            ContentType=head["ContentType"],
            CopySource={
                "Bucket": name,
                "Key": key
            },
            MetadataDirective="REPLACE",
            Metadata=head["Metadata"]
        )

    return head["Metadata"]
