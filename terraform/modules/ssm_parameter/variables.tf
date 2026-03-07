variable "parameter_name" {
  description = "Name of the SSM parameter"
  type        = string
}

variable "parameter_description" {
  description = "Description of the SSM parameter"
  type        = string
  default     = ""
}

variable "parameter_value" {
  description = "Value of the SSM parameter"
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "Tags to apply to the SSM parameter"
  type        = map(string)
  default     = {}
}
