import boto3
import csv
import io
import os
from datetime import datetime
from botocore.client import Config
from botocore.exceptions import ClientError

# MinIO Configuration from environment variables
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://minio:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
S3_BUCKET = os.getenv("S3_BUCKET", "api-sleep-results")
S3_REGION = os.getenv("S3_REGION", "us-east-1")  # Can be any value for MinIO
CSV_FILENAME = "APIGetSomeSleep_Results.csv"

def get_s3_client():
    """Create and return an S3 client configured for MinIO."""
    return boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        region_name=S3_REGION,
        config=Config(signature_version='s3v4'),  # Required for MinIO
        use_ssl=False  # Set to True if MinIO has SSL enabled
    )

def ensure_bucket_exists():
    """Ensure the MinIO bucket exists, create if it doesn't."""
    try:
        s3 = get_s3_client()
        # Check if bucket exists
        s3.head_bucket(Bucket=S3_BUCKET)
        print(f"✓ Bucket '{S3_BUCKET}' already exists")
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        # Bucket doesn't exist (404) or NoSuchBucket
        if error_code in ['404', 'NoSuchBucket']:
            try:
                # Create bucket for MinIO (no LocationConstraint needed)
                s3.create_bucket(Bucket=S3_BUCKET)
                print(f"✓ Created bucket '{S3_BUCKET}' in MinIO")
                
                # Set bucket policy to public readable (optional)
                bucket_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": "s3:GetObject",
                            "Resource": f"arn:aws:s3:::{S3_BUCKET}/*"
                        }
                    ]
                }
                # Convert policy to JSON string
                import json
                bucket_policy_json = json.dumps(bucket_policy)
                
                # Set the bucket policy
                s3.put_bucket_policy(Bucket=S3_BUCKET, Policy=bucket_policy_json)
                print(f"✓ Set public read policy for bucket '{S3_BUCKET}'")
                
            except ClientError as create_error:
                print(f"✗ Error creating bucket: {create_error}")
                return False
        else:
            print(f"✗ Error checking bucket: {e}")
            return False
    return True

def append_result_to_csv(task_id, sleep_seconds, quality):
    """
    Append a single result to the CSV file in MinIO.
    Creates the file with headers if it doesn't exist.
    """
    timestamp = datetime.now()
    date_str = timestamp.strftime("%Y/%m/%d")
    time_str = timestamp.strftime("%H:%M:%S")
    
    # Prepare the new row
    new_row = {
        'task_id': task_id,
        'sleep_seconds': sleep_seconds,
        'quality': quality,
        'date': date_str,
        'time': time_str
    }
    
    try:
        s3 = get_s3_client()
        
        # Try to read existing CSV
        try:
            response = s3.get_object(Bucket=S3_BUCKET, Key=CSV_FILENAME)
            existing_content = response['Body'].read().decode('utf-8')
            
            # Parse existing CSV
            csv_reader = csv.DictReader(io.StringIO(existing_content))
            rows = list(csv_reader)
            
            # Get fieldnames from existing CSV
            fieldnames = csv_reader.fieldnames
            
        except ClientError as e:
            # File doesn't exist, create new with headers
            if e.response['Error']['Code'] == 'NoSuchKey':
                rows = []
                fieldnames = ['task_id', 'sleep_seconds', 'quality', 'date', 'time']
                print(f"Creating new CSV file: {CSV_FILENAME}")
            else:
                print(f"Error reading CSV: {e}")
                raise e
        
        # Append new row
        rows.append(new_row)
        
        # Write all rows back to CSV
        output = io.StringIO()
        csv_writer = csv.DictWriter(output, fieldnames=fieldnames)
        csv_writer.writeheader()
        csv_writer.writerows(rows)
        
        # Upload to MinIO
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=CSV_FILENAME,
            Body=output.getvalue().encode('utf-8'),
            ContentType='text/csv'
        )
        
        print(f"✓ Appended result for task {task_id} to CSV")
        return True
        
    except Exception as e:
        print(f"✗ Error appending to MinIO CSV: {e}")
        return False

def get_csv_download_url(expiration=3600):
    """
    Generate a presigned URL for downloading the CSV file.
    Default expiration: 1 hour (3600 seconds)
    For MinIO, we can also generate a direct URL since we set public read policy.
    """
    try:
        s3 = get_s3_client()
        
        # Generate presigned URL (works with MinIO)
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': CSV_FILENAME},
            ExpiresIn=expiration
        )
        
        # Alternative: Direct URL if bucket is public
        # direct_url = f"{S3_ENDPOINT}/{S3_BUCKET}/{CSV_FILENAME}"
        
        return url
        
    except ClientError as e:
        print(f"✗ Error generating presigned URL: {e}")
        return None

def list_all_results():
    """
    Utility function to list all stored results from CSV
    """
    try:
        s3 = get_s3_client()
        response = s3.get_object(Bucket=S3_BUCKET, Key=CSV_FILENAME)
        content = response['Body'].read().decode('utf-8')
        
        csv_reader = csv.DictReader(io.StringIO(content))
        rows = list(csv_reader)
        
        print(f"✓ Found {len(rows)} results in CSV")
        return rows
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            print("No CSV file found yet")
            return []
        else:
            print(f"✗ Error listing results: {e}")
            return []
            