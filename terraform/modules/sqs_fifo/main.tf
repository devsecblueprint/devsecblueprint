# SQS FIFO Queue Module
# Creates a FIFO queue with dead-letter queue for Discord sync processing

# Dead-letter queue for failed messages
resource "aws_sqs_queue" "dlq" {
  name                        = "${var.queue_name}-dlq.fifo"
  fifo_queue                  = true
  content_based_deduplication = true

  tags = var.tags
}

# Main FIFO queue for Discord role sync events
resource "aws_sqs_queue" "main" {
  name                        = "${var.queue_name}.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
  visibility_timeout_seconds  = var.visibility_timeout_seconds

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = var.tags
}
