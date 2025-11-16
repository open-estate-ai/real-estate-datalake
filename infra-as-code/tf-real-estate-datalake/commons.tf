data "aws_caller_identity" "current" {}


## Local variables
locals {
  resource_name_prefix_hyphenated = format("%s-%s", lower(var.env), lower(var.component_name))
  s3_vector_bucket_name           = "${data.aws_caller_identity.current.account_id}-${lower(var.resource_region)}-${lower(var.env)}-datalake-vectors"
}
