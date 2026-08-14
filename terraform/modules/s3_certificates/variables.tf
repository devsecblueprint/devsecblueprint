variable "bucket_name" {
  description = "Name of the S3 bucket for certificate storage"
  type        = string
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
