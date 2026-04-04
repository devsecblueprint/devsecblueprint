"""
Deployment tasks for DevSec Blueprint V3

Usage:
    invoke build-backend              # Build backend Lambda zip
    invoke build-layer                # Build Lambda layer with dependencies
    invoke build-frontend             # Build frontend static site
    invoke plan                       # Run terraform plan
    invoke apply                      # Build backend + layer + run terraform apply
    invoke destroy                    # Run terraform destroy
    invoke deploy-frontend            # Deploy frontend to S3/CloudFront
    invoke deploy-all                 # Deploy both backend and frontend

    # Content Management
    invoke fetch-content              # Fetch content from CodeCommit repository
    invoke build-with-fresh-content   # Fetch content + build frontend

    # Content Registry
    invoke generate-registry          # Generate content registry JSON
    invoke validate-registry          # Validate content registry without upload
"""

from invoke import task
from pathlib import Path
from datetime import datetime
import sys
import zipfile
import os
import json
import tempfile
import shutil


def get_terraform_output(c, output_name):
    """Get a Terraform output value."""
    with c.cd("terraform"):
        result = c.run(f"terraform output -raw {output_name}", hide=True)
    return result.stdout.strip()


@task
def build_backend(c):
    """Build the backend Lambda deployment package."""
    print("=" * 60)
    print("Building Backend Lambda Package")
    print("=" * 60)

    backend_dir = Path("backend")
    terraform_dir = Path("terraform")
    zip_path = terraform_dir / "backend.zip"

    # Remove old zip if it exists
    if zip_path.exists():
        print(f"\n�️  Removing old {zip_path}")
        zip_path.unlink()

    # Create zip file
    print(f"\n📦 Creating {zip_path}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add all Python files from backend/
        for root, dirs, files in os.walk(backend_dir):
            # Skip __pycache__ and test directories
            dirs[:] = [
                d for d in dirs if d not in ["__pycache__", ".pytest_cache", "tests"]
            ]

            for file in files:
                if file.endswith((".py", ".html")):
                    file_path = Path(root) / file
                    # Calculate the archive name (relative to backend/)
                    arcname = file_path.relative_to(backend_dir)
                    print(f"  Adding: {arcname}")
                    zipf.write(file_path, arcname)

    # Get zip size
    zip_size = zip_path.stat().st_size / 1024  # KB
    print(f"\n✅ Backend package created: {zip_path} ({zip_size:.1f} KB)")


@task
def build_layer(c):
    """Build the Lambda layer with Python dependencies."""
    print("=" * 60)
    print("Building Lambda Layer")
    print("=" * 60)

    terraform_dir = Path("terraform")
    layer_dir = Path("layer_build")
    zip_path = terraform_dir / "python_dependencies_layer.zip"
    requirements_file = Path("backend/lambda-requirements.txt")

    # Check if requirements.txt exists
    if not requirements_file.exists():
        print(f"\n❌ ERROR: {requirements_file} not found!")
        sys.exit(1)

    # Remove old build artifacts
    if layer_dir.exists():
        print(f"\n🗑️  Removing old build directory...")
        shutil.rmtree(layer_dir)
    if zip_path.exists():
        print(f"🗑️  Removing old {zip_path}")
        zip_path.unlink()

    # Create layer directory structure
    print(f"\n📁 Creating layer directory structure...")
    python_dir = layer_dir / "python"
    python_dir.mkdir(parents=True)

    # Install dependencies
    print(f"\n📦 Installing dependencies from {requirements_file}...")
    result = c.run(
        f"pip install -r {requirements_file} -t {python_dir} --upgrade --no-cache-dir",
        warn=True,
    )

    if result.exited != 0:
        print("\n❌ ERROR: Failed to install dependencies")
        sys.exit(1)

    # Create zip file
    print(f"\n🗜️  Creating layer zip...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(layer_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(layer_dir)
                zipf.write(file_path, arcname)

    # Clean up build directory
    print(f"\n🧹 Cleaning up build directory...")
    shutil.rmtree(layer_dir)

    # Get zip size
    zip_size = zip_path.stat().st_size / (1024 * 1024)  # MB
    print(f"\n✅ Layer package created: {zip_path} ({zip_size:.2f} MB)")


@task(pre=[build_backend, build_layer])
def plan(c, total_module_pages=None):
    """Build backend and run terraform plan.

    Args:
        total_module_pages: Total number of module pages (auto-calculated from modules.json if not provided)
    """
    print("=" * 60)
    print("Running Terraform Plan")
    print("=" * 60)

    # Calculate total module pages from modules.json
    if total_module_pages is None:
        modules_json_path = Path("frontend/lib/data/modules.json")
        if not modules_json_path.exists():
            print(f"\n❌ ERROR: {modules_json_path} not found!")
            print("This file is required to calculate total module pages.")
            sys.exit(1)

        print("\n📊 Calculating total module pages from modules.json...")
        with open(modules_json_path) as f:
            modules = json.load(f)
            total_module_pages = sum(len(module.get("pages", [])) for module in modules)
        print(f"   Found {total_module_pages} module pages")

    # Set as environment variable for Terraform
    env = os.environ.copy()
    env["TF_VAR_total_module_pages"] = str(total_module_pages)

    if env.get("TF_WORKSPACE") is None:
        print("Workspace is not set. Please set this before continuing.")
        sys.exit(1)

    with c.cd("terraform"):
        c.run("terraform init && terraform plan", env=env)

    print("\n✅ Terraform plan complete!")


@task(pre=[build_backend, build_layer])
def apply(c, total_module_pages=None):
    """Build backend and run terraform apply.

    Args:
        total_module_pages: Total number of module pages (auto-calculated from modules.json if not provided)
    """
    print("=" * 60)
    print("Running Terraform Apply")
    print("=" * 60)

    # Calculate total module pages from modules.json
    if total_module_pages is None:
        modules_json_path = Path("frontend/lib/data/modules.json")
        if not modules_json_path.exists():
            print(f"\n❌ ERROR: {modules_json_path} not found!")
            print("This file is required to calculate total module pages.")
            sys.exit(1)

        print("\n📊 Calculating total module pages from modules.json...")
        with open(modules_json_path) as f:
            modules = json.load(f)
            total_module_pages = sum(len(module.get("pages", [])) for module in modules)
        print(f"   Found {total_module_pages} module pages")

    # Set as environment variable for Terraform
    env = os.environ.copy()
    env["TF_VAR_total_module_pages"] = str(total_module_pages)

    if env.get("TF_WORKSPACE") is None:
        print("Workspace is not set. Please set this before continuing.")
        sys.exit(1)

    with c.cd("terraform"):
        c.run("terraform init && terraform apply -auto-approve", env=env)

    print("\n✅ Terraform apply complete!")
    print(f"   TOTAL_MODULE_PAGES set to: {total_module_pages}")

    # Show deployment info
    try:
        print("\n📊 Deployment Info:")
        function_name = get_terraform_output(c, "lambda_function_name")
        api_url = get_terraform_output(c, "api_gateway_invoke_url")
        custom_api_domain = get_terraform_output(c, "api_gateway_custom_domain")

        print(f"  Lambda Function: {function_name}")
        print(f"  API Gateway URL: {api_url}")
        print(f"  Custom API Domain: https://{custom_api_domain}")
    except:
        pass  # Outputs might not exist yet on first apply


@task
def destroy(c, total_module_pages=None):
    """Run terraform destroy.

    Args:
        total_module_pages: Total number of module pages (auto-calculated from modules.json if not provided)
    """
    print("=" * 60)
    print("Running Terraform Destroy")
    print("=" * 60)

    if total_module_pages is None:
        modules_json_path = Path("frontend/lib/data/modules.json")
        if modules_json_path.exists():
            with open(modules_json_path) as f:
                modules = json.load(f)
                total_module_pages = sum(
                    len(module.get("pages", [])) for module in modules
                )
        else:
            total_module_pages = 0

    env = os.environ.copy()
    env["TF_VAR_total_module_pages"] = str(total_module_pages)

    if env.get("TF_WORKSPACE") is None:
        print("Workspace is not set. Please set this before continuing.")
        sys.exit(1)

    with c.cd("terraform"):
        c.run("terraform init && terraform destroy -auto-approve", env=env)

    print("\n✅ Terraform destroy complete!")


@task
def fetch_content(c, branch="main"):
    """Fetch content from CodeCommit repository.

    Args:
        branch: Git branch to fetch. Default: main
    """
    print("=" * 60)
    print(f"Fetching Content from CodeCommit ({branch})")
    print("=" * 60)

    content_dir = Path("frontend/content")
    repo_url = f"codecommit::{os.environ["AWS_REGION"]}://dsb-platform-content"

    # Create temporary directory for cloning
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        print(f"\n📥 Cloning repository to temporary workspace...")
        print(f"   Repository: {repo_url}")
        print(f"   Branch: {branch}")

        # Clone the repository using git-remote-codecommit
        result = c.run(
            f"git clone --depth 1 --branch {branch} {repo_url} {temp_path}/content",
            warn=True,
        )

        if result.exited != 0:
            print("\n❌ ERROR: Failed to clone CodeCommit repository")
            print("\nMake sure:")
            print(
                "  1. git-remote-codecommit is installed: pip install git-remote-codecommit"
            )
            print(
                "  2. AWS credentials are configured (AWS_PROFILE or default credentials)"
            )
            print("  3. Your AWS credentials have CodeCommit access")
            print("  4. Repository 'dsb-platform-content' exists in us-east-1")
            sys.exit(1)

        cloned_repo = temp_path / "content"

        # Check if content folders exist in the cloned repo
        print("\n🔍 Checking for content folders...")
        expected_folders = []
        for item in cloned_repo.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                expected_folders.append(item.name)
                print(f"   Found: {item.name}/")

        if not expected_folders:
            print("\n❌ ERROR: No content folders found in repository")
            sys.exit(1)

        # Clear existing content directory (but keep the directory itself)
        print(f"\n🧹 Clearing existing content directory...")
        if content_dir.exists():
            for item in content_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                    print(f"   Removed: {item.name}/")
                elif item.is_file() and item.name != ".gitkeep":
                    item.unlink()
                    print(f"   Removed: {item.name}")
        else:
            content_dir.mkdir(parents=True, exist_ok=True)

        # Copy content folders from cloned repo to frontend/content
        print(f"\n📋 Copying content folders to {content_dir}...")
        for folder_name in expected_folders:
            src = cloned_repo / folder_name
            dst = content_dir / folder_name

            shutil.copytree(src, dst)

            # Count files in the copied folder
            file_count = sum(1 for _ in dst.rglob("*") if _.is_file())
            print(f"   ✓ {folder_name}/ ({file_count} files)")

        print(f"\n✅ Content fetched successfully!")
        print(f"   Total folders: {len(expected_folders)}")
        print(f"   Location: {content_dir}")


@task
def generate_registry(c, env="dev"):
    """Generate the content registry JSON file.

    Args:
        env: Environment (dev, staging, prod). Default: dev
    """
    print("=" * 60)
    print(f"Generating Content Registry ({env})")
    print("=" * 60)

    with c.cd("frontend"):
        print("\n📋 Running registry generator...")

        # Generate registry without S3 upload (no env vars set)
        result = c.run("npm run generate-registry", warn=True)

        if result.exited != 0:
            print("\n❌ ERROR: Content registry generation failed!")
            sys.exit(1)

    # Check if registry file was created
    registry_path = Path("./frontend/dist/content-registry.json")

    # Show registry stats
    with open(registry_path) as f:
        registry = json.load(f)
        entry_count = len(registry.get("entries", {}))
        schema_version = registry.get("schema_version", "unknown")

    print(f"\n✅ Content registry generated successfully!")
    print(f"   Schema version: {schema_version}")
    print(f"   Total entries: {entry_count}")
    print(f"   Output: {registry_path}")


@task
def validate_registry(c):
    """Validate the content registry without uploading."""
    print("=" * 60)
    print("Validating Content Registry")
    print("=" * 60)

    with c.cd("frontend"):
        print("\n🔍 Running registry validation...")
        result = c.run("npm run generate-registry:validate", warn=True)

        if result.exited != 0:
            print("\n❌ Validation failed! Fix errors before deployment.")
            sys.exit(1)

    print("\n✅ Content registry validation passed!")


@task
def upload_registry(c, env="dev"):
    """Upload the content registry to S3.

    Args:
        env: Environment (dev, staging, prod). Default: dev
    """
    print("=" * 60)
    print(f"Uploading Content Registry to S3 ({env})")
    print("=" * 60)

    # Check if registry file exists
    registry_path = Path("frontend/dist/content-registry.json")
    if not registry_path.exists():
        print(f"\n❌ ERROR: Registry file not found at {registry_path}")
        print("Run 'invoke generate-registry' first")
        sys.exit(1)

    # Get bucket name from Terraform
    print("\n🔍 Getting S3 bucket name from Terraform...")
    try:
        bucket_name = get_terraform_output(c, "content_registry_bucket_name")
        print(f"   Bucket: {bucket_name}")
    except Exception as e:
        print(f"\n❌ ERROR: Could not get S3 bucket name from Terraform: {e}")
        print(
            "Make sure Terraform has been applied with the S3 content registry module"
        )
        sys.exit(1)

    # Load registry to get version info
    with open(registry_path) as f:
        registry = json.load(f)
        schema_version = registry.get("schema_version", "1.0.0")
        generated_at = registry.get("generated_at", "")

    # Generate versioned filename: v{schema_version}-{YYYYMMDD}-{HHMMSS}.json
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    versioned_key = f"content-registry/v{schema_version}-{timestamp}.json"
    latest_key = "content-registry/latest.json"

    # Upload versioned file (region inherited from AWS CLI config)
    print(f"\n☁️  Uploading versioned registry: {versioned_key}")
    c.run(
        f"aws s3 cp {registry_path} s3://{bucket_name}/{versioned_key} "
        f"--content-type application/json"
    )

    # Upload latest file
    print(f"\n☁️  Uploading latest registry: {latest_key}")
    c.run(
        f"aws s3 cp {registry_path} s3://{bucket_name}/{latest_key} "
        f"--content-type application/json"
    )

    # Clean up old versions (keep last 5)
    print("\n🧹 Cleaning up old versions (keeping last 5)...")
    result = c.run(
        f"aws s3api list-objects-v2 "
        f"--bucket {bucket_name} "
        f"--prefix content-registry/v "
        f"--query 'Contents[?Key!=`content-registry/latest.json`].[Key,LastModified]' "
        f"--output json",
        hide=True,
    )

    if result.stdout.strip() and result.stdout.strip() != "null":
        versions = json.loads(result.stdout)
        if len(versions) > 5:
            # Sort by last modified (oldest first)
            versions.sort(key=lambda x: x[1])
            # Delete oldest versions
            for key, _ in versions[:-5]:
                print(f"   Deleting old version: {key}")
                c.run(f"aws s3 rm s3://{bucket_name}/{key}", hide=True)

    print("\n✅ Content registry upload task complete!")
    print(f"   Versioned: s3://{bucket_name}/{versioned_key}")
    print(f"   Latest: s3://{bucket_name}/{latest_key}")


@task
def build_with_fresh_content(c):
    """Fetch fresh content from CodeCommit and build frontend.

    This is a convenience task that combines fetch-content and build-frontend.
    """
    print("=" * 60)
    print("Building Frontend with Fresh Content")
    print("=" * 60)

    # Fetch content
    fetch_content(c)

    # Build frontend (without fetching again)
    build_frontend(c, fetch_content_flag=False)

    print("\n" + "=" * 60)
    print("✅ BUILD WITH FRESH CONTENT COMPLETE!")
    print("=" * 60)


@task(pre=[generate_registry])
def build_frontend(c, fetch_content_flag=False):
    """Build the Next.js frontend for production.

    Args:
        fetch_content_flag: Whether to fetch content from CodeCommit first. Default: False
    """
    print("=" * 60)
    print("Building Frontend")
    print("=" * 60)

    # Fetch content if requested
    if fetch_content_flag:
        fetch_content(c)

    # Install dependencies
    print("\n📦 Installing dependencies...")
    with c.cd("frontend"):
        c.run("npm install")

    # Registry is already generated by the pre=[generate_registry] task
    # No need to generate it again here

    # Build the application (with static export)
    print("\n� Building Next.js application with static export...")
    with c.cd("frontend"):
        c.run("npm run build")

    print("\n✅ Frontend build complete! Output in frontend/out/")


@task(pre=[build_with_fresh_content, upload_registry])
def deploy_frontend(c):
    """Deploy the frontend to S3 and invalidate CloudFront cache."""
    print("\n" + "=" * 60)
    print("STARTING DEPLOY FRONTEND TASK")
    print("=" * 60)
    print("Deploying Frontend")
    print("=" * 60)

    # Check if build output exists
    out_dir = Path("frontend/out")
    if not out_dir.exists():
        print("ERROR: frontend/out/ directory not found!")
        print("Run 'invoke build-frontend' first")
        sys.exit(1)

    # Get S3 bucket name from Terraform
    print("\n🔍 Getting S3 bucket name from Terraform...")
    bucket_name = get_terraform_output(c, "s3_bucket_name")
    print(f"Bucket: {bucket_name}")

    # Sync files to S3
    print("\n☁️  Uploading files to S3...")
    c.run(
        f"aws s3 sync frontend/out/ s3://{bucket_name}/ "
        f"--delete "
        f"--cache-control 'public,max-age=31536000,immutable' "
        f"--exclude '*.html'"
    )

    # Upload HTML files with shorter cache
    print("\n📄 Uploading HTML files with short cache...")
    c.run(
        f"aws s3 sync frontend/out/ s3://{bucket_name}/ "
        f"--exclude '*' "
        f"--include '*.html' "
        f"--cache-control 'public,max-age=0,must-revalidate'"
    )

    # Get CloudFront distribution ID
    print("\n🔍 Getting CloudFront distribution ID...")
    distribution_id = get_terraform_output(c, "cloudfront_distribution_id")
    print(f"Distribution: {distribution_id}")

    # Invalidate CloudFront cache
    print("\n🔄 Invalidating CloudFront cache...")
    c.run(
        f"aws cloudfront create-invalidation "
        f"--distribution-id {distribution_id} "
        f"--paths '/*'"
    )

    # Get CloudFront domain
    cloudfront_domain = get_terraform_output(c, "cloudfront_distribution_domain")
    custom_domain = get_terraform_output(c, "frontend_domain")

    print("\n✅ Frontend deployed successfully!")
    print(f"\n🌐 CloudFront URL: https://{cloudfront_domain}")
    print(f"🌐 Custom Domain: https://{custom_domain}")


@task(pre=[apply, deploy_frontend])
def deploy_all(c):
    """Deploy both backend and frontend."""
    print("\n" + "=" * 60)
    print("🎉 Full Deployment Complete!")
    print("=" * 60)
