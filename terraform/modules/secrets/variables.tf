variable "secret_name" {
  description = "Name of the Secrets Manager secret"
  type        = string
}

variable "secret_description" {
  description = "Description of the Secrets Manager secret"
  type        = string
}

variable "client_id" {
  type    = string
  default = ""
}

variable "client_secret" {
  type    = string
  default = ""
}

variable "secret_key" {
  description = "Secret key value (for JWT secrets)"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to the secret"
  type        = map(string)
  default     = {}
}
