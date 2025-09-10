resource "aws_s3_bucket" "main" {
  bucket              = format("%s-%s", local.resource_name_prefix_hyphenated, var.bucket_name)
  object_lock_enabled = var.bucket_object_lock_enabled
  tags = merge({
    "Name" = format("%s-%s", local.resource_name_prefix_hyphenated, var.bucket_name)
  })
}

resource "aws_s3_bucket_server_side_encryption_configuration" "bucket_encryption" {
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.bucket_encryption_algorithm
      kms_master_key_id = var.bucket_encryption_key_id
    }
    bucket_key_enabled = var.bucket_key_enabled
  }
}

resource "aws_s3_bucket_public_access_block" "bucket_block_public_access" {
  bucket                  = aws_s3_bucket.main.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "bucket_versioning" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration {
    status = var.bucket_versioning_enabled
  }
}
