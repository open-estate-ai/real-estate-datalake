# ========================================
# Lambda Function for Ingestion
# ========================================

# IAM role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${local.resource_name_prefix_hyphenated}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}


# Lambda policy for S3 Vectors and SageMaker
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${local.resource_name_prefix_hyphenated}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.s3_raw_bucket_arn,
          "${var.s3_raw_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sagemaker:InvokeEndpoint"
        ]
        Resource = "arn:aws:sagemaker:${var.region}:${data.aws_caller_identity.current.account_id}:endpoint/${var.sagemaker_endpoint_name}"
      },
      {
        Effect = "Allow"
        Action = [
          "s3vectors:PutVectors",
          "s3vectors:QueryVectors",
          "s3vectors:GetVectors",
          "s3vectors:DeleteVectors"
        ]
        Resource = "arn:aws:s3vectors:${var.region}:${data.aws_caller_identity.current.account_id}:bucket/${var.s3_vector_bucket_name}/index/*"
      }
    ]
  })
}


# Build Lambda package
resource "null_resource" "build_lambda" {
  triggers = {
    # Rebuild when any Python file or dependencies change
    source_hash = sha256(join("", [
      fileexists("${path.module}/lambda/pyproject.toml") ? filesha256("${path.module}/lambda/pyproject.toml") : "",
      fileexists("${path.module}/lambda/package.py") ? filesha256("${path.module}/lambda/package.py") : "",
      fileexists("${path.module}/lambda/ingest.py") ? filesha256("${path.module}/lambda/ingest.py") : ""
    ]))
  }

  provisioner "local-exec" {
    command     = "uv sync && uv run package.py"
    working_dir = "${path.module}/lambda/"
  }
}

# Data source to read the zip file hash after build
data "local_file" "lambda_zip" {
  depends_on = [null_resource.build_lambda]
  filename   = "${path.module}/lambda/lambda_function.zip"
}

# Lambda function
resource "aws_lambda_function" "ingest" {
  function_name = "${local.resource_name_prefix_hyphenated}-ingest-lambda"
  role          = aws_iam_role.lambda_role.arn

  # Note: The deployment package will be created by the build_lambda null_resource
  filename         = "${path.module}/lambda/lambda_function.zip"
  source_code_hash = data.local_file.lambda_zip.content_base64sha256

  handler     = "ingest.lambda_handler"
  runtime     = "python3.12"
  timeout     = 900
  memory_size = 1024

  environment {
    variables = {
      VECTOR_BUCKET      = var.s3_vector_bucket_name
      SAGEMAKER_ENDPOINT = var.sagemaker_endpoint_name
    }
  }

  depends_on = [null_resource.build_lambda]

}

# # CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.ingest.function_name}"
  retention_in_days = 7

}

# S3 event notification to trigger Lambda on object creation in RAW bucket
resource "aws_lambda_permission" "raw_s3" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingest.arn
  principal     = "s3.amazonaws.com"
  source_arn    = var.s3_raw_bucket_arn
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = var.s3_raw_bucket_name

  lambda_function {
    lambda_function_arn = aws_lambda_function.ingest.arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.raw_s3]
}
