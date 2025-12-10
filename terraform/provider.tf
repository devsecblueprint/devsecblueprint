terraform {
  cloud {
    organization = "devsecblueprint"

    workspaces {
      name = "devsecblueprint"
    }
  }

  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
    random = {
      source = "hashicorp/random"
    }
  }
}

provider "aws" {
  region = var.aws_region
}