variable "queue_name" {
  description = "Base name for the SQS FIFO queue (without .fifo suffix)"
  type        = string
  default     = "dsb-discord-sync"
}

variable "max_receive_count" {
  description = "Maximum number of receives before a message is sent to the DLQ"
  type        = number
  default     = 3
}

variable "visibility_timeout_seconds" {
  description = "Visibility timeout for the queue (should be 6x Lambda timeout)"
  type        = number
  default     = 180
}

variable "tags" {
  description = "Tags to apply to the SQS queues"
  type        = map(string)
  default     = {}
}
