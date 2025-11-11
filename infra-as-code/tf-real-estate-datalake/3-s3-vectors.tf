# This is bit of manual, so we are not automating it via Terraform
# Since S3 Vectors uses a different namespace than regular S3, we'll create it via the AWS Console:

# 1. Go to the [S3 Console](https://console.aws.amazon.com/s3/)
# 2. Look for **"Vector buckets"** in the left navigation (not regular buckets)
# 3. Click **"Create vector bucket"**
# 4. Configure:
#    - Bucket name: `{your-account-id}-us-east-1-dev-datalake-vectors` (replace with your actual account ID)
#    - Encryption: Keep default (SSE-S3)
# 5. After creating the bucket, create an index:
#    - Index name: `property-research`
#    - Dimension: `384`
#    - Distance metric: `Cosine`
# 6. Click **"Create vector index"**
