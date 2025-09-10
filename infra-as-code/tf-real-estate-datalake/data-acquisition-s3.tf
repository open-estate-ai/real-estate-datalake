module "s3_bucket_raw" {
  source = "../tf-modules/s3"
  # common vars
  region = var.resource_region
  env    = var.env

  # module specific vars
  bucket_name               = format("%s-raw", var.component_name)
  bucket_versioning_enabled = "Enabled"
}
