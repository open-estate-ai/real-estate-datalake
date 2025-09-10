variable "env" {
  type = string
}


variable "resource_region" {
  type        = string
  description = "Region in which you want to create resources"
}
variable "default_tags" {
  description = "Default set of tags to apply to AWS resources"
  type        = map(string)
  default     = {}
}
