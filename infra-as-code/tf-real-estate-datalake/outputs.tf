output "s3_bucket_raw_bucket_name" {
  description = "Name of the RAW S3 bucket. This will contain the scraped data."
  value       = module.s3_bucket_raw.bucket_name
}

output "sagemaker_embedding_model_endpoint_name" {
  description = "Name of the SageMaker embedding model endpoint"
  value       = module.sagemaker_embedding_model.sagemaker_endpoint_name
}
output "sagemaker_embedding_model_endpoint_arn" {
  description = "ARN of the SageMaker embedding model endpoint"
  value       = module.sagemaker_embedding_model.sagemaker_endpoint_arn
}
