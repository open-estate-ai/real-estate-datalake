variable "component_tags" {
  description = "Component specific tags"
  type        = map(string)
  default     = {}
}

variable "component_name" {
  type = string
}
