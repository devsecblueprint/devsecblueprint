variable "layer_name" {
  description = "Name of the Lambda layer"
  type        = string
}

variable "layer_zip_path" {
  description = "Path to the layer zip file"
  type        = string
}

variable "compatible_runtimes" {
  description = "List of compatible runtimes"
  type        = list(string)
  default     = ["python3.12"]
}

variable "description" {
  description = "Description of the Lambda layer"
  type        = string
  default     = ""
}
