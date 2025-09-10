variable "bucket_name" {
  type = string
}

variable "bucket_object_lock_enabled" {
  type    = bool
  default = false
}

variable "bucket_encryption_algorithm" {
  type    = string
  default = "aws:kms"
}

variable "bucket_encryption_key_id" {
  type    = string
  default = ""
}

variable "bucket_key_enabled" {
  type    = string
  default = true
}

variable "bucket_versioning_enabled" {
  type    = string
  default = "Disabled"
}
