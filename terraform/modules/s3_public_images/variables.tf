variable "bucket_name" {
  description = "Name of the S3 bucket for public images"
  type        = string
}

variable "allowed_origins" {
  description = "List of allowed origins for CORS (e.g. frontend domain)"
  type        = list(string)
  default     = ["*"]
}

variable "tags" {
  description = "Resource tags to apply to the S3 bucket"
  type        = map(string)
  default     = {}
}
