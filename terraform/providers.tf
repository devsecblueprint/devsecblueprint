terraform {
  cloud {

    organization = "devsecblueprint"

    workspaces {
      name = "dsb-platform"
    }
  }
}

provider "aws" {
  region = var.primary_region

  default_tags {
    tags = var.common_tags
  }
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = var.common_tags
  }
}
