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
        "failover_bucket_name": data.get("website_failover_bucket_name", {}).get("value"),
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
        f"--cache-control max-age=31536000,public"
    )

    print("✅ Deployment complete")


@task
def invalidate(c, distribution_id):
    """Invalidate CloudFront cache."""
    print(f"🔄 Invalidating CloudFront cache: {distribution_id}")
    result = c.run(
        f"aws cloudfront create-invalidation --distribution-id {distribution_id} --paths /*",
        hide=True,
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


@task
def sync_both_buckets(c):
    """Sync to both primary and failover S3 buckets."""
    tf_outputs = get_outputs(c)
    
    # Sync to primary bucket
    print("🌟 Syncing to primary bucket...")
    sync_s3(c, tf_outputs["bucket_name"])
    
    # Sync to failover bucket if it exists
    if tf_outputs["failover_bucket_name"]:
        print("🔄 Syncing to failover bucket...")
        sync_s3(c, tf_outputs["failover_bucket_name"])
    else:
        print("⚠️  No failover bucket configured")


@task(pre=[build, apply])
def deploy(c):
    """Full deployment pipeline: build, sync to S3, and invalidate CloudFront."""
    print("🚀 Starting deployment...\n")

    # Get Terraform outputs
    tf_outputs = get_outputs(c)

    # Deploy to both buckets
    sync_both_buckets(c)

    # Invalidate CloudFront
    invalidate(c, tf_outputs["distribution_id"])

    print("\n✨ Deployment successful!")
