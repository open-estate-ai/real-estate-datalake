module "ingest_lambda" {
  source         = "../tf-modules/ingest-lambda"
  region         = var.resource_region
  env            = var.env
  component_name = var.component_name

  # module specific vars
  s3_raw_bucket_name      = module.s3_bucket_raw.bucket_name
  s3_raw_bucket_arn       = module.s3_bucket_raw.bucket_arn
  s3_vector_bucket_name   = local.s3_vector_bucket_name
  sagemaker_endpoint_name = module.sagemaker_embedding_model.sagemaker_endpoint_name
}
