data "aws_caller_identity" "current" {}


## Local variables
locals {
  resource_name_prefix_hyphenated = format("%s-%s-%s", data.aws_caller_identity.current.account_id, lower(var.region), lower(var.env))
}
