variable "bucket_name" {
  description = "Name of the S3 bucket for content registry"
  type        = string
}

variable "tags" {
  description = "Resource tags to apply to the S3 bucket"
  type        = map(string)
  default     = {}
}
