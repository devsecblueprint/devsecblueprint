"""
Deployment tasks for the static website.
Usage: invoke deploy
"""

from invoke import task, Context
import json


@task
def get_outputs(c):
    """Get Terraform outputs."""
    print("Fetching Terraform outputs...")
    with c.cd("terraform"):
        result = c.run("terraform output -json", hide=True, pty=False)
    data = json.loads(result.stdout)

    return {
        "bucket_name": data["website_bucket_name"]["value"],
        "distribution_id": data["cloudfront_distribution_id"]["value"],
    }


@task
def sync_s3(c, bucket_name):
    """Deploy built files to S3."""
    print(f"☁️  Deploying to S3 bucket: {bucket_name}")
    dist_path = "app/build"

    # Sync files to S3 (AWS CLI auto-detects content types)
    c.run(
        f"aws s3 sync {dist_path} s3://{bucket_name} --delete "
        f"--cache-control no-cache,no-store,must-revalidate",
        hide=True,
        pty=False
    )

    # Update cache control for HTML files (shorter cache)
    c.run(
        f"aws s3 cp s3://{bucket_name} s3://{bucket_name} --recursive "
        f"--exclude '*' --include '*.html' --metadata-directive REPLACE "
        f"--cache-control 'max-age=0,no-cache,no-store,must-revalidate' "
        f"--content-type 'text/html'",
        pty=True
    )

    print("✅ Deployment complete")


@task
def invalidate(c, distribution_id):
    """Invalidate CloudFront cache."""
    print(f"🔄 Invalidating CloudFront cache: {distribution_id}")
    result = c.run(
        f"aws cloudfront create-invalidation --distribution-id {distribution_id} --paths '/*'",
        hide=False,
        pty=False,
    )
    invalidation_data = json.loads(result.stdout)
    invalidation_id = invalidation_data["Invalidation"]["Id"]
    print(f"✅ Invalidation created: {invalidation_id}")


@task
def build(c):
    """Build the Docusaurus application."""
    print("📦 Building application...")
    with c.cd("app"):
        c.run(
            "npm run build",
            hide=True
        )
    print("✅ Build complete")


@task
def init(c):
    """Initialize Terraform."""
    print("🔧 Initializing Terraform...")
    with c.cd("terraform"):
        c.run(
            "terraform init",
        )
    print("✅ Terraform initialized")


@task(pre=[init])
def plan(c):
    """Run Terraform plan."""
    print("📋 Running Terraform plan...")
    with c.cd("terraform"):
        c.run(
            "terraform plan",
        )


@task(pre=[init])
def apply(c):
    """Apply Terraform changes."""
    print("🚀 Applying Terraform changes...")
    with c.cd("terraform"):
        c.run(
            "terraform apply --auto-approve",
        )
    print("✅ Infrastructure deployed")


@task
def destroy(c):
    """Destroy Terraform infrastructure."""
    print("💥 Destroying Terraform infrastructure...")
    with c.cd("terraform"):
        c.run(
            "terraform destroy --auto-approve",
        )


@task(pre=[build, apply])
def deploy(c):
    """Full deployment pipeline: build, sync to S3, and invalidate CloudFront."""
    print("🚀 Starting deployment...\n")

    # Get Terraform outputs
    tf_outputs = get_outputs(c)

    # Deploy to primary bucket (auto-replication handles failover)
    sync_s3(c, tf_outputs["bucket_name"])

    # Invalidate CloudFront
    invalidate(c, tf_outputs["distribution_id"])

    print("\n✨ Deployment successful!")
