import json
import os
from pydoc import text
import boto3
from urllib.parse import unquote_plus
import uuid
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


# Environment variables
VECTOR_BUCKET = os.environ.get(
    'VECTOR_BUCKET', '756375699536-us-east-1-dev-datalake-vectors')
SAGEMAKER_ENDPOINT = os.environ.get('SAGEMAKER_ENDPOINT')
INDEX_NAME = os.environ.get('INDEX_NAME', 'property-research')
MAX_WORKERS = int(os.environ.get('MAX_WORKERS', '10'))  # Parallel workers
# Retry attempts for failed records
MAX_RETRIES = int(os.environ.get('MAX_RETRIES', '3'))

# Initialize AWS clients
sagemaker_runtime = boto3.client('sagemaker-runtime')
s3_vectors = boto3.client('s3vectors')
s3_client = boto3.client('s3')


def get_embedding(text):
    """Get embedding vector from SageMaker endpoint."""
    response = sagemaker_runtime.invoke_endpoint(
        EndpointName=SAGEMAKER_ENDPOINT,
        ContentType='application/json',
        Body=json.dumps({'inputs': text})
    )

    result = json.loads(response['Body'].read().decode())
    # HuggingFace returns nested array [[[embedding]]], extract the actual embedding
    if isinstance(result, list) and len(result) > 0:
        if isinstance(result[0], list) and len(result[0]) > 0:
            if isinstance(result[0][0], list):
                return result[0][0]  # Extract from [[[embedding]]]
            return result[0]  # Extract from [[embedding]]
    return result  # Return as-is if not nested


def process_single_project(line: str, idx: int, retry_count: int = 0):
    """
    Process a single project record - get embedding and store in S3 Vectors.
    This function will be executed in parallel with retry logic.

    Args:
        line: JSON line containing project data
        idx: Line index for logging
        retry_count: Current retry attempt (0 for first try)

    Returns:
        tuple: (success: bool, idx: int, line: str, error: str or None, is_retryable: bool)
    """
    retry_prefix = f"[Retry {retry_count}]" if retry_count > 0 else ""

    try:
        if not line.strip():
            return (False, idx, line, "Empty line", False)

        project = json.loads(line)

        raw_text = project.get('raw_text', 'N/A')
        metadata = project.get('metadata', {})

        # Get embedding from SageMaker
        print(
            f"{retry_prefix}[{idx}] Getting embedding for text: {raw_text[:100]}...")
        embedding = get_embedding(raw_text)

        # Generate unique ID for the vector
        vector_id = str(uuid.uuid4())

        # Store in S3 Vectors
        print(
            f"{retry_prefix}[{idx}] Storing vector in bucket: {VECTOR_BUCKET}, index: {INDEX_NAME}")
        s3_vectors.put_vectors(
            vectorBucketName=VECTOR_BUCKET,
            indexName=INDEX_NAME,
            vectors=[{
                "key": vector_id,
                "data": {"float32": embedding},
                "metadata": {
                    "text": raw_text,
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    **metadata  # Include any additional metadata
                }
            }]
        )
        print(
            f"{retry_prefix}[{idx}] Successfully stored vector with ID: {vector_id}")
        return (True, idx, line, None, False)

    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse JSON: {e}"
        print(f"WARNING: {retry_prefix}[{idx}] {error_msg}")
        print(f"         Line content: {line[:100]}...")
        # Don't retry JSON parse errors
        return (False, idx, line, error_msg, False)
    except Exception as e:
        error_msg = f"Error processing project: {str(e)}"
        print(f"ERROR: {retry_prefix}[{idx}] {error_msg}")
        # Retry on transient errors (network, throttling, etc.)
        is_retryable = any(keyword in str(e).lower() for keyword in [
            'timeout', 'throttl', 'rate', 'limit', 'connection', 'network', 'unavailable'
        ])
        return (False, idx, line, error_msg, is_retryable)


def get_s3_object_and_process(bucket: str, key: str):
    """
    Fetch S3 object and process NDJSON (newline-delimited JSON) file.
    Each line is a separate JSON object representing a project.

    Args:
        bucket: S3 bucket name
        key: S3 object key
    """
    try:
        # URL-decode the key (handles %3D -> =, %2F -> /, etc.)
        decoded_key = unquote_plus(key)
        print(f"Original key: {key}")
        print(f"Decoded key: {decoded_key}")
        print(f"Fetching object from S3: s3://{bucket}/{decoded_key}")

        # Get object from S3 using decoded key
        response = s3_client.get_object(Bucket=bucket, Key=decoded_key)

        # Read the content
        content = response['Body'].read().decode('utf-8')

        print(f"Successfully fetched object. Size: {len(content)} bytes")

        # Process each line as a separate JSON object (NDJSON format)
        lines = content.strip().split('\n')
        total_lines = len(lines)
        print(
            f"Processing {total_lines} project records in parallel with {MAX_WORKERS} workers...")

        # Process records in parallel using ThreadPoolExecutor with retry logic
        successful = 0
        failed = 0
        failed_records = []  # Store failed records for retry

        # Initial processing pass
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all tasks
            future_to_data = {
                executor.submit(process_single_project, line, idx, 0): (idx, line)
                for idx, line in enumerate(lines, 1)
            }

            # Process completed tasks as they finish
            for future in as_completed(future_to_data):
                idx, line = future_to_data[future]
                try:
                    success, line_idx, line_content, error, is_retryable = future.result()
                    if success:
                        successful += 1
                    else:
                        if is_retryable:
                            failed_records.append((line_idx, line_content))
                            print(f"[{line_idx}] Marked for retry: {error}")
                        else:
                            failed += 1

                    # Log progress every 10 records
                    if (successful + failed + len(failed_records)) % 10 == 0:
                        print(f"Progress: {successful + failed + len(failed_records)}/{total_lines} processed "
                              f"({successful} successful, {failed} failed, {len(failed_records)} pending retry)")

                except Exception as e:
                    failed += 1
                    print(
                        f"ERROR: Unexpected error processing line {idx}: {e}")

        # Retry failed records
        retry_attempt = 1
        while failed_records and retry_attempt <= MAX_RETRIES:
            print(
                f"\nRetry attempt {retry_attempt}/{MAX_RETRIES}: Processing {len(failed_records)} failed records...")

            current_failed = failed_records
            failed_records = []  # Reset for this retry round

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                future_to_data = {
                    executor.submit(process_single_project, line, idx, retry_attempt): (idx, line)
                    for idx, line in current_failed
                }

                for future in as_completed(future_to_data):
                    idx, line = future_to_data[future]
                    try:
                        success, line_idx, line_content, error, is_retryable = future.result()
                        if success:
                            successful += 1
                            print(
                                f"[{line_idx}] Retry successful on attempt {retry_attempt}")
                        else:
                            if is_retryable and retry_attempt < MAX_RETRIES:
                                failed_records.append((line_idx, line_content))
                            else:
                                failed += 1
                                print(
                                    f"[{line_idx}] Failed after {retry_attempt} retries: {error}")
                    except Exception as e:
                        failed += 1
                        print(
                            f"ERROR: Unexpected error on retry for line {idx}: {e}")

            retry_attempt += 1

        print(
            f"\nCompleted processing {total_lines} records: {successful} successful, {failed} failed")
        if failed > 0:
            print(
                f"WARNING: {failed} records failed after {MAX_RETRIES} retry attempts")

        return successful

    except Exception as e:
        print(f"ERROR: Error fetching or processing S3 object: {e}")
        raise


def lambda_handler(event, context):
    print("Event:", json.dumps(event))

    total_processed = 0

    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        # Key comes URL-encoded from S3 event
        key = record['s3']['object']['key']

        print(f"\nNew object created: s3://{bucket}/{key}")

        # Process the S3 object
        try:
            count = get_s3_object_and_process(bucket, key)
            total_processed += count
        except Exception as e:
            print(f"ERROR: Failed to process s3://{bucket}/{key}: {e}")
            # Continue processing other records even if one fails
            continue

    print(
        f"\nLambda execution completed. Total records processed: {total_processed}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Successfully processed S3 events",
            "total_records_processed": total_processed
        })
    }
