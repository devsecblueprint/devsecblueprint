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
def clear_bucket(c, bucket_name):
    """Clear all files from S3 bucket."""
    print(f"🗑️  Clearing S3 bucket: {bucket_name}")
    c.run(
        f"aws s3 rm s3://{bucket_name} --recursive",
        hide=False,
        pty=False
    )
    print("✅ Bucket cleared")


@task
def sync_s3(c, bucket_name):
    """Deploy built files to S3."""
    print(f"☁️  Deploying to S3 bucket: {bucket_name}")
    dist_path = "app/build"

    
    # Sync everything
    c.run(
        f"aws s3 sync {dist_path} s3://{bucket_name} "
        f"--cache-control 'public,max-age=0,must-revalidate'",
        hide=True,
        pty=False
    )

    # Also update index.html specifically
    c.run(
        f"aws s3 cp s3://{bucket_name}/index.html s3://{bucket_name}/index.html "
        f"--metadata-directive REPLACE "
        f"--cache-control 'max-age=0,no-cache,no-store,must-revalidate' "
        f"--content-type 'text/html'",
        hide=False,
        pty=True
    )

    print("✅ Deployment complete")


@task
def invalidate(c, distribution_id):
    """Invalidate CloudFront cache."""
    print(f"🔄 Invalidating CloudFront cache: {distribution_id}")
    
    # Create invalidation for all paths
    result = c.run(
        f"aws cloudfront create-invalidation --distribution-id {distribution_id} --paths '/*' '/index.html' '/' '/docs/*'",
        hide=False,
        pty=False,
    )
    invalidation_data = json.loads(result.stdout)
    invalidation_id = invalidation_data["Invalidation"]["Id"]
    print(f"✅ Invalidation created: {invalidation_id}")
    
    # Wait for invalidation to complete (optional but helpful for debugging)
    print("⏳ Waiting for invalidation to complete...")
    c.run(
        f"aws cloudfront wait invalidation-completed --distribution-id {distribution_id} --id {invalidation_id}",
        hide=False,
        pty=False,
    )
    print("✅ Invalidation completed")


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
    """Full deployment pipeline: build, clear bucket, sync to S3, and invalidate CloudFront."""
    print("🚀 Starting deployment...\n")

    # Get Terraform outputs
    tf_outputs = get_outputs(c)

    # Deploy to primary bucket (auto-replication handles failover)
    sync_s3(c, tf_outputs["bucket_name"])

    # Invalidate CloudFront
    invalidate(c, tf_outputs["distribution_id"])

    print("\n✨ Deployment successful!")
@task
def debug_mime_types(c):
    """Debug MIME type issues by checking S3 content and CloudFront responses."""
    print("🔍 Debugging MIME type issues...")
    
    # Get Terraform outputs
    tf_outputs = get_outputs(c)
    bucket_name = tf_outputs["bucket_name"]
    
    print(f"📋 Checking bucket: {bucket_name}")
    
    # Check if JS files exist in S3
    print("\n📁 Checking for JS files in S3...")
    c.run(f"aws s3 ls s3://{bucket_name}/assets/js/ --recursive", hide=False)
    
    # Check MIME type of a specific JS file
    print("\n🔍 Checking MIME type of main JS file...")
    try:
        result = c.run(f"aws s3api head-object --bucket {bucket_name} --key assets/js/main.8d844f71.js", hide=True)
        print("✅ File exists in S3")
    except:
        print("❌ Main JS file not found in S3")
        
        # List all JS files to see what's actually there
        print("\n📋 Available JS files:")
        c.run(f"aws s3 ls s3://{bucket_name}/assets/js/", hide=False)
    
    # Test direct S3 access
    print(f"\n🌐 Testing direct S3 access:")
    c.run(f"curl -I https://{bucket_name}.s3.amazonaws.com/assets/js/main.8d844f71.js", hide=False)
    
    # Test CloudFront access
    print(f"\n☁️  Testing CloudFront access:")
    c.run("curl -I https://devsecblueprint.com/assets/js/main.8d844f71.js", hide=False)


@task
def fix_mime_types(c):
    """Fix MIME types for JavaScript and CSS files in S3."""
    print("🔧 Fixing MIME types...")
    
    # Get Terraform outputs
    tf_outputs = get_outputs(c)
    bucket_name = tf_outputs["bucket_name"]
    
    print(f"📋 Fixing MIME types for bucket: {bucket_name}")
    
    # Fix JS files
    print("\n🔧 Fixing JavaScript MIME types...")
    c.run(
        f"aws s3 cp s3://{bucket_name}/assets/js/ s3://{bucket_name}/assets/js/ "
        f"--recursive --metadata-directive REPLACE "
        f"--content-type 'application/javascript' "
        f"--cache-control 'public,max-age=31536000,immutable'",
        hide=False
    )
    
    # Fix CSS files
    print("\n🔧 Fixing CSS MIME types...")
    c.run(
        f"aws s3 cp s3://{bucket_name}/assets/css/ s3://{bucket_name}/assets/css/ "
        f"--recursive --metadata-directive REPLACE "
        f"--content-type 'text/css' "
        f"--cache-control 'public,max-age=31536000,immutable'",
        hide=False
    )
    
    # Fix HTML files
    print("\n🔧 Fixing HTML MIME types...")
    c.run(
        f"aws s3 cp s3://{bucket_name}/ s3://{bucket_name}/ "
        f"--recursive --exclude '*' --include '*.html' "
        f"--metadata-directive REPLACE "
        f"--content-type 'text/html; charset=utf-8' "
        f"--cache-control 'public,max-age=0,must-revalidate'",
        hide=False
    )
    
    print("✅ MIME types fixed!")
    
    # Invalidate CloudFront
    distribution_id = tf_outputs["distribution_id"]
    print(f"\n🔄 Invalidating CloudFront cache...")
    invalidate(c, distribution_id)