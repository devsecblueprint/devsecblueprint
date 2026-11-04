#!/usr/bin/env bash
#
# apyhub_assertions.sh — Terraform validate/plan assertions for ApyHub provisioning
# (spec: student-builder-membership, task 22.3; Requirements 9.1-9.5)
#
# WHY A SHELL SCRIPT INSTEAD OF A NATIVE `terraform test` (.tftest.hcl) FILE
# --------------------------------------------------------------------------
# This root module uses an HCP Terraform (Terraform Cloud) backend — see
# providers.tf:
#
#     terraform {
#       cloud { organization = "devsecblueprint" }
#       ...
#     }
#
# Two constraints make a real `terraform plan` / native `terraform test` run
# impossible in an offline/CI-without-cloud-creds context:
#
#   1. The `cloud {}` backend requires HCP Terraform credentials to initialize.
#   2. The root module reads live AWS data sources (aws_caller_identity,
#      aws_region, aws_vpc, aws_subnets). Any `plan` (which is what
#      `terraform test` runs under the hood) evaluates those data sources and
#      therefore needs real AWS credentials.
#
# A native `.tftest.hcl` file runs `plan`/`apply` against the full root module,
# so it would hit both constraints and cannot run here without cloud + AWS
# creds. We therefore follow the same approach tasks 22.1/22.2 used:
#
#   * STRUCTURAL validation — copy the module to a temp dir, strip the `cloud {}`
#     block, run `terraform init -backend=false` + `terraform validate`. This
#     proves the configuration (including the new ApyHub wiring) is internally
#     consistent without touching any remote backend or cloud provider.
#   * GREP-based structural assertions on main.tf — robust under the cloud-backend
#     constraint — confirm the ApyHub secret module exists, its ARN is granted to
#     the ECS task role, the env var is wired, and the Stripe secret modules and
#     their IAM/env entries are present and unchanged (no add/change/destroy).
#   * VARIABLE-VALIDATION assertion — the `TFC_APYHUB_API_KEY` variable's
#     non-empty `validation {}` rule is evaluated by `terraform plan`. We prove
#     it in isolation (a tiny temp config containing only that variable block,
#     extracted verbatim from variables.tf) so we can exercise the rule with an
#     empty value WITHOUT initializing the cloud backend or any AWS provider.
#
# The script is self-contained and cleans up every temp dir it creates.
#
# USAGE:   ./terraform/tests/apyhub_assertions.sh
# EXIT:    0 = all assertions passed; non-zero = a failure (message on stderr).
#
set -uo pipefail

# ---------------------------------------------------------------------------
# Locate the terraform root module relative to this script.
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MAIN_TF="${TF_ROOT}/main.tf"
VARIABLES_TF="${TF_ROOT}/variables.tf"

PASS_COUNT=0
FAIL_COUNT=0
declare -a TMP_DIRS=()

# ---------------------------------------------------------------------------
# Cleanup: remove every temp dir we created, even on early exit.
# ---------------------------------------------------------------------------
cleanup() {
  local d
  for d in "${TMP_DIRS[@]:-}"; do
    [ -n "${d}" ] && [ -d "${d}" ] && rm -rf "${d}"
  done
}
trap cleanup EXIT

pass() { printf 'PASS: %s\n' "$1"; PASS_COUNT=$((PASS_COUNT + 1)); }
fail() { printf 'FAIL: %s\n' "$1" >&2; FAIL_COUNT=$((FAIL_COUNT + 1)); }

# grep helper: assert a Rust-free, fixed/basic-regex pattern is present in a file.
assert_grep() {
  local pattern="$1" file="$2" desc="$3"
  if grep -Eq "${pattern}" "${file}"; then
    pass "${desc}"
  else
    fail "${desc} (pattern not found: ${pattern})"
  fi
}

require_tool() {
  command -v "$1" >/dev/null 2>&1 || { echo "ERROR: required tool '$1' not found on PATH" >&2; exit 2; }
}

echo "==========================================================================="
echo "ApyHub Terraform assertions (Requirements 9.1-9.5)"
echo "Root module: ${TF_ROOT}"
echo "==========================================================================="

require_tool terraform
[ -f "${MAIN_TF}" ]      || { echo "ERROR: ${MAIN_TF} not found" >&2; exit 2; }
[ -f "${VARIABLES_TF}" ] || { echo "ERROR: ${VARIABLES_TF} not found" >&2; exit 2; }

# ===========================================================================
# ASSERTION GROUP A — configuration validity (temp copy, backend stripped)
# Requirement 9.1-9.4 rely on the config being valid.
# ===========================================================================
echo
echo "--- A. terraform validate (backend-stripped temp copy) ---"

VALIDATE_TMP="$(mktemp -d)"
TMP_DIRS+=("${VALIDATE_TMP}")

# Copy the root module, excluding local provider cache + lock (fresh init).
if command -v rsync >/dev/null 2>&1; then
  rsync -a --exclude='.terraform' --exclude='.terraform.lock.hcl' "${TF_ROOT}/" "${VALIDATE_TMP}/"
else
  cp -R "${TF_ROOT}/." "${VALIDATE_TMP}/"
  rm -rf "${VALIDATE_TMP}/.terraform" "${VALIDATE_TMP}/.terraform.lock.hcl"
fi

# Strip the `cloud {}` block so init does not require HCP Terraform creds.
# Perl slurp-mode removes the block (and its surrounding blank lines) in place.
perl -0pi -e 's/\n[ \t]*cloud[ \t]*\{[^}]*\}\n/\n/s' "${VALIDATE_TMP}/providers.tf"

if grep -Eq '^\s*cloud\s*\{' "${VALIDATE_TMP}/providers.tf"; then
  fail "cloud {} block was not stripped from the temp copy"
else
  pass "cloud {} block stripped from temp copy (local init possible)"
fi

if terraform -chdir="${VALIDATE_TMP}" init -backend=false -input=false -no-color >/tmp/apyhub_init.log 2>&1; then
  pass "terraform init -backend=false succeeded"
else
  fail "terraform init -backend=false failed (see /tmp/apyhub_init.log)"
  cat /tmp/apyhub_init.log >&2
fi

# `terraform validate` returns 0 even with deprecation warnings; we only fail on
# actual errors (non-zero exit).
if terraform -chdir="${VALIDATE_TMP}" validate -no-color >/tmp/apyhub_validate.log 2>&1; then
  pass "terraform validate passed (configuration is valid) [Req 9.1-9.4]"
else
  fail "terraform validate reported errors (see below)"
  cat /tmp/apyhub_validate.log >&2
fi

# ===========================================================================
# ASSERTION GROUP B — ApyHub secret module exists (Requirement 9.1)
# ===========================================================================
echo
echo "--- B. ApyHub secret module present [Req 9.1] ---"

assert_grep 'module[[:space:]]+"apyhub_secret"' "${MAIN_TF}" \
  'module.apyhub_secret is declared'
assert_grep 'source[[:space:]]*=[[:space:]]*"\./modules/secrets"' "${MAIN_TF}" \
  'apyhub_secret uses the ./modules/secrets pattern'
assert_grep 'dsb-platform-apyhub-api-key-\$\{random_id\.suffix\.id\}' "${MAIN_TF}" \
  'apyhub_secret name follows the dsb-platform-apyhub-api-key-${random_id.suffix.id} convention'
assert_grep 'secret_key[[:space:]]*=[[:space:]]*var\.TFC_APYHUB_API_KEY' "${MAIN_TF}" \
  'apyhub_secret passes var.TFC_APYHUB_API_KEY as the single-value secret_key'

# Confirm the apyhub_secret module block carries common_tags (tags = var.common_tags).
apyhub_block="$(awk '/module[[:space:]]+"apyhub_secret"/{f=1} f{print} f&&/^}/{exit}' "${MAIN_TF}")"
if printf '%s\n' "${apyhub_block}" | grep -Eq 'tags[[:space:]]*=[[:space:]]*var\.common_tags'; then
  pass 'apyhub_secret applies common_tags'
else
  fail 'apyhub_secret does not apply common_tags'
fi

# ===========================================================================
# ASSERTION GROUP C — IAM grant scoped to the ApyHub ARN (Requirement 9.2)
# ===========================================================================
echo
echo "--- C. ECS task-role IAM grant for ApyHub ARN [Req 9.2] ---"

# Extract the secrets_arns list from the iam_ecs module block.
secrets_arns_block="$(awk '
  /secrets_arns[[:space:]]*=[[:space:]]*\[/ {f=1}
  f {print}
  f && /\]/ {exit}
' "${MAIN_TF}")"

if printf '%s\n' "${secrets_arns_block}" | grep -Eq 'module\.apyhub_secret\.secret_arn'; then
  pass 'module.apyhub_secret.secret_arn is in iam_ecs.secrets_arns'
else
  fail 'module.apyhub_secret.secret_arn is NOT in iam_ecs.secrets_arns'
fi

# ===========================================================================
# ASSERTION GROUP D — ECS env var wiring (Requirement 9.3)
# ===========================================================================
echo
echo "--- D. APYHUB_SECRET_NAME env var wired into ECS [Req 9.3] ---"

assert_grep 'APYHUB_SECRET_NAME[[:space:]]*=[[:space:]]*module\.apyhub_secret\.secret_name' "${MAIN_TF}" \
  'APYHUB_SECRET_NAME = module.apyhub_secret.secret_name is in ecs.environment_variables'

# ===========================================================================
# ASSERTION GROUP E — Stripe secret modules untouched (Requirement 9.4)
# No add/change/destroy: the Stripe modules, their ARNs in secrets_arns, and
# their env entries must all still be present and unchanged.
# ===========================================================================
echo
echo "--- E. Stripe secret modules unchanged (no add/change/destroy) [Req 9.4] ---"

assert_grep 'module[[:space:]]+"stripe_secret_key"' "${MAIN_TF}" \
  'module.stripe_secret_key still declared'
assert_grep 'module[[:space:]]+"stripe_webhook_secret"' "${MAIN_TF}" \
  'module.stripe_webhook_secret still declared'
assert_grep 'dsb-platform-stripe-secret-key-\$\{random_id\.suffix\.id\}' "${MAIN_TF}" \
  'stripe_secret_key name unchanged'
assert_grep 'dsb-platform-stripe-webhook-secret-\$\{random_id\.suffix\.id\}' "${MAIN_TF}" \
  'stripe_webhook_secret name unchanged'
assert_grep 'secret_key[[:space:]]*=[[:space:]]*var\.TFC_STRIPE_SECRET_KEY' "${MAIN_TF}" \
  'stripe_secret_key input unchanged (var.TFC_STRIPE_SECRET_KEY)'
assert_grep 'secret_key[[:space:]]*=[[:space:]]*var\.TFC_STRIPE_WEBHOOK_SECRET' "${MAIN_TF}" \
  'stripe_webhook_secret input unchanged (var.TFC_STRIPE_WEBHOOK_SECRET)'

# Stripe ARNs still granted in iam_ecs.secrets_arns.
if printf '%s\n' "${secrets_arns_block}" | grep -Eq 'module\.stripe_secret_key\.secret_arn'; then
  pass 'module.stripe_secret_key.secret_arn still in iam_ecs.secrets_arns'
else
  fail 'module.stripe_secret_key.secret_arn missing from iam_ecs.secrets_arns'
fi
if printf '%s\n' "${secrets_arns_block}" | grep -Eq 'module\.stripe_webhook_secret\.secret_arn'; then
  pass 'module.stripe_webhook_secret.secret_arn still in iam_ecs.secrets_arns'
else
  fail 'module.stripe_webhook_secret.secret_arn missing from iam_ecs.secrets_arns'
fi

# Stripe env entries unchanged.
assert_grep 'STRIPE_SECRET_NAME[[:space:]]*=[[:space:]]*module\.stripe_secret_key\.secret_name' "${MAIN_TF}" \
  'STRIPE_SECRET_NAME env entry unchanged'
assert_grep 'STRIPE_WEBHOOK_SECRET_NAME[[:space:]]*=[[:space:]]*module\.stripe_webhook_secret\.secret_name' "${MAIN_TF}" \
  'STRIPE_WEBHOOK_SECRET_NAME env entry unchanged'

# ===========================================================================
# ASSERTION GROUP F — empty TFC_APYHUB_API_KEY fails validation (Requirement 9.5)
# We extract the variable block verbatim into an isolated temp config so the
# non-empty `validation {}` rule can be exercised via `terraform plan` without
# the cloud backend or any AWS provider/data source.
# ===========================================================================
echo
echo "--- F. empty TFC_APYHUB_API_KEY fails variable validation [Req 9.5] ---"

VAR_TMP="$(mktemp -d)"
TMP_DIRS+=("${VAR_TMP}")

# Extract the `variable "TFC_APYHUB_API_KEY" { ... }` block verbatim.
awk '
  /variable[[:space:]]+"TFC_APYHUB_API_KEY"[[:space:]]*\{/ {f=1; depth=0}
  f {
    print
    n=gsub(/\{/,"{"); depth+=n
    m=gsub(/\}/,"}"); depth-=m
    if (depth<=0) exit
  }
' "${VARIABLES_TF}" > "${VAR_TMP}/main.tf"

if ! grep -Eq 'validation[[:space:]]*\{' "${VAR_TMP}/main.tf"; then
  fail 'could not extract TFC_APYHUB_API_KEY variable block with its validation rule'
else
  pass 'extracted TFC_APYHUB_API_KEY variable block (with validation rule)'

  terraform -chdir="${VAR_TMP}" init -backend=false -input=false -no-color >/dev/null 2>&1

  # Empty value -> validation MUST fail (non-zero exit).
  if terraform -chdir="${VAR_TMP}" plan -input=false -no-color \
       -var 'TFC_APYHUB_API_KEY=' >/tmp/apyhub_empty.log 2>&1; then
    fail 'empty TFC_APYHUB_API_KEY unexpectedly PASSED validation'
  else
    if grep -q 'TFC_APYHUB_API_KEY must not be empty' /tmp/apyhub_empty.log; then
      pass 'empty TFC_APYHUB_API_KEY fails validation with the expected error [Req 9.5]'
    else
      fail 'empty TFC_APYHUB_API_KEY failed, but not via the expected validation rule'
      cat /tmp/apyhub_empty.log >&2
    fi
  fi

  # Non-empty value -> validation MUST pass (control case).
  if terraform -chdir="${VAR_TMP}" plan -input=false -no-color \
       -var 'TFC_APYHUB_API_KEY=example-key' >/tmp/apyhub_nonempty.log 2>&1; then
    pass 'non-empty TFC_APYHUB_API_KEY passes validation (control case)'
  else
    fail 'non-empty TFC_APYHUB_API_KEY unexpectedly FAILED validation'
    cat /tmp/apyhub_nonempty.log >&2
  fi
fi

# ===========================================================================
# Summary
# ===========================================================================
echo
echo "==========================================================================="
echo "RESULT: ${PASS_COUNT} passed, ${FAIL_COUNT} failed"
echo "==========================================================================="

rm -f /tmp/apyhub_init.log /tmp/apyhub_validate.log /tmp/apyhub_empty.log /tmp/apyhub_nonempty.log 2>/dev/null

[ "${FAIL_COUNT}" -eq 0 ]
