#!/bin/sh

echo "⏳ Waiting for MinIO..."

until curl -s http://minio:9000/minio/health/live; do
  sleep 2
done

echo "✅ MinIO is ready"

# Use python to create bucket only (no public policy)
python3 -c "
import boto3
from botocore.exceptions import ClientError

BUCKET = 'ota-media'
client = boto3.client('s3', endpoint_url='http://minio:9000', aws_access_key_id='minioadmin', aws_secret_access_key='minioadmin')

try:
    client.head_bucket(Bucket=BUCKET)
    print(f'Bucket "{BUCKET}" already exists')
except ClientError:
    client.create_bucket(Bucket=BUCKET)
    print(f'Bucket "{BUCKET}" created (private by default)')
"

echo "✅ Bucket ready (private)"
