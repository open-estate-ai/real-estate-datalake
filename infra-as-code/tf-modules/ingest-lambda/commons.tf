data "aws_caller_identity" "current" {}


## Local variables
locals {
  resource_name_prefix_hyphenated = format("%s-%s", lower(var.env), lower(var.component_name))
}
