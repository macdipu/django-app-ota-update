#!/bin/sh

echo "⏳ Waiting for MinIO..."

until curl -s http://minio:9000/minio/health/live; do
  sleep 2
done

echo "✅ MinIO is ready"

# Use python to set up bucket and policy
python3 -c "
import boto3
client = boto3.client('s3', endpoint_url='http://minio:9000', aws_access_key_id='minioadmin', aws_secret_access_key='minioadmin')
client.create_bucket(Bucket='ota-media')
policy = {'Version': '2012-10-17', 'Statement': [{'Effect': 'Allow', 'Principal': {'AWS': '*'}, 'Action': 's3:GetObject', 'Resource': 'arn:aws:s3:::ota-media/*'}]}
client.put_bucket_policy(Bucket='ota-media', Policy=str(policy).replace(\"'\", '\"'))
print('Bucket policy set successfully')
"

echo "✅ Bucket ready & public"