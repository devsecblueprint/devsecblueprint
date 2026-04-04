resource "aws_lambda_layer_version" "dependencies" {
  filename            = var.layer_zip_path
  layer_name          = var.layer_name
  compatible_runtimes = var.compatible_runtimes
  source_code_hash    = try(filebase64sha256(var.layer_zip_path), "placeholder")

  description = var.description
}
