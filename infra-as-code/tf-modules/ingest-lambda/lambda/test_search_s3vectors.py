"""
Test script for searching S3 Vectors - Real Estate Projects.
This demonstrates how to search the indexed UP RERA property listings.
"""

import os
import json
import boto3
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from project root
env_path = Path(__file__) / '.env'
load_dotenv(env_path, override=True)

# Get configuration
VECTOR_BUCKET = os.getenv(
    'VECTOR_BUCKET', '756375699536-us-east-1-dev-datalake-vectors')
SAGEMAKER_ENDPOINT = os.getenv(
    'SAGEMAKER_ENDPOINT', 'us-east-1-dev-datalake-embedding-endpoint')
INDEX_NAME = os.getenv('INDEX_NAME', 'property-research')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

if not VECTOR_BUCKET:
    print("Error: Please run Guide 3 Step 4 to save VECTOR_BUCKET to .env")
    exit(1)

# Initialize AWS clients
s3_vectors = boto3.client('s3vectors', region_name=AWS_REGION)
sagemaker_runtime = boto3.client('sagemaker-runtime', region_name=AWS_REGION)


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


def list_all_vectors():
    """List sample vectors from the index."""
    print(
        f"Listing sample vectors in bucket: {VECTOR_BUCKET}, index: {INDEX_NAME}")
    print("=" * 60)

    try:
        # S3 Vectors doesn't have a direct list operation, so we'll do a broad search
        # Search for a common term to get some results
        test_embedding = get_embedding("residential apartment lucknow")

        response = s3_vectors.query_vectors(
            vectorBucketName=VECTOR_BUCKET,
            indexName=INDEX_NAME,
            queryVector={"float32": test_embedding},
            topK=10,
            returnDistance=True,
            returnMetadata=True
        )

        vectors = response.get('vectors', [])
        print(f"\nFound {len(vectors)} vectors in the index:\n")

        for i, vector in enumerate(vectors, 1):
            metadata = vector.get('metadata', {})
            text = metadata.get('text', '')

            # Parse project details from text
            print(f"{i}. Vector ID: {vector['key']}")

            # Extract key information from the text field
            if 'Project Name:' in text:
                lines = text.split('|')
                for line in lines[:4]:  # Show first 4 fields
                    print(f"   {line.strip()}")
            else:
                print(f"   {text[:150]}...")

            if metadata.get('timestamp'):
                print(f"   Indexed: {metadata['timestamp']}")
            print()

    except Exception as e:
        print(f"Error listing vectors: {e}")


def search_vectors(query_text, k=5):
    """Search for property vectors by query text."""
    print(f"\nSearching for: '{query_text}'")
    print("-" * 40)

    try:
        # Get embedding for query
        query_embedding = get_embedding(query_text)

        # Search S3 Vectors
        response = s3_vectors.query_vectors(
            vectorBucketName=VECTOR_BUCKET,
            indexName=INDEX_NAME,
            queryVector={"float32": query_embedding},
            topK=k,
            returnDistance=True,
            returnMetadata=True
        )

        vectors = response.get('vectors', [])
        print(f"Found {len(vectors)} results:\n")

        for i, vector in enumerate(vectors, 1):
            metadata = vector.get('metadata', {})
            distance = vector.get('distance', 0)
            text = metadata.get('text', '')

            # Convert distance to similarity score (cosine distance: 0 = identical, 2 = opposite)
            similarity_score = 1 - (distance / 2)
            print(f"{i}. Similarity Score: {similarity_score:.3f}")

            # Parse and display project information
            if 'Project Name:' in text:
                lines = text.split('|')
                for line in lines:
                    line = line.strip()
                    if line:
                        print(f"   {line}")
            else:
                print(f"   {text[:250]}...")
            print()

    except Exception as e:
        print(f"Error searching: {e}")


def main():
    """Explore the Real Estate S3 Vectors database."""
    print("=" * 60)
    print("UP RERA Real Estate Property Search")
    print("=" * 60)
    print(f"Bucket: {VECTOR_BUCKET}")
    print(f"Index: {INDEX_NAME}")
    print(f"Endpoint: {SAGEMAKER_ENDPOINT}")
    print()

    # List sample vectors
    list_all_vectors()

    # Example searches
    print("=" * 60)
    print("Example Semantic Property Searches")
    print("=" * 60)

    # Search for specific property types and locations
    search_queries = [
        "residential apartments in Lucknow",
        "commercial property Noida",
        "affordable housing Greater Noida",
        "luxury apartments Gautam Buddha Nagar",
        "upcoming residential projects Ghaziabad",
        "residential property in Mathura"
    ]

    for query in search_queries:
        search_vectors(query, k=3)

    print("\nS3 Vectors provides semantic search - it finds properties based on")
    print("meaning and context, not just exact keyword matches!")
    print("\nYou can search for:")
    print("  - Location: 'properties in Lucknow', 'Noida real estate'")
    print("  - Type: 'residential apartments', 'commercial spaces'")
    print("  - Features: 'affordable housing', 'luxury projects'")
    print("  - Promoter: 'Mahagun projects', 'specific developer name'")


if __name__ == "__main__":
    main()
