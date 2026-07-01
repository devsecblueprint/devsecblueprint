# Membership System Deployment Runbook

## Prerequisites

- AWS account with Terraform state backend configured
- Stripe account (test mode for staging, live for production)
- Discord application with bot created
- Terraform >= 1.5 installed
- AWS CLI configured with appropriate credentials

---

## 1. Stripe Product Setup

### Create Products in Stripe Dashboard

Create the following products in Stripe with `dsb_tier` metadata:

| Product Name     | Metadata Key | Metadata Value   | Recurring |
|-----------------|--------------|------------------|-----------|
| Explorer         | dsb_tier     | EXPLORER         | Monthly   |
| Builder          | dsb_tier     | BUILDER          | Monthly   |
| Builder Academy  | dsb_tier     | BUILDER_ACADEMY  | Monthly   |

Steps:
1. Go to Stripe Dashboard → Products → Add Product
2. Set product name, description, and price
3. Under "Additional options" → "Metadata", add key `dsb_tier` with the corresponding tier value
4. Save and note the Price ID (`price_xxx`) for each product

### Configure Webhook Endpoint

1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://{api-domain}/api/stripe/webhook`
3. Select events:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
4. Copy the webhook signing secret (`whsec_xxx`)

### Configure Customer Portal

1. Go to Stripe Dashboard → Settings → Billing → Customer Portal
2. Enable: Cancel subscription, Update payment method, View invoices
3. Set redirect URL: `https://{frontend-domain}/settings/subscription`

---

## 2. Discord Bot Setup

### Create Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create New Application → name it "DSB Membership Bot"
3. Go to OAuth2 → note the Client ID and Client Secret
4. Set redirect URI: `https://{frontend-domain}/auth/discord/callback`

### Configure Bot

1. Go to Bot tab → Create Bot
2. Copy the Bot Token
3. Enable these Privileged Gateway Intents:
   - Server Members Intent
4. Under OAuth2 → URL Generator, select scopes: `identify`, `guilds`, `guilds.join`

### Bot Permissions

The bot requires these permissions in your Discord guild:
- Manage Roles
- View Channels (to verify guild membership)

Numeric permission value: `268435456` (Manage Roles)

### Guild Role Setup

Create managed roles in your Discord guild:

| Role Name        | Purpose              | Note                           |
|-----------------|----------------------|--------------------------------|
| Free             | FREE tier (default)  | Position below bot's role      |
| Explorer         | EXPLORER tier access | Position below bot's role      |
| Builder          | BUILDER tier access  | Position below bot's role      |
| Builder Academy  | BUILDER_ACADEMY tier | Position below bot's role      |

**Important:** The bot's role must be positioned ABOVE all managed roles in the guild role hierarchy.

Note each role's ID (enable Developer Mode → right-click role → Copy ID).

### Invite Bot to Guild

Use this URL template:
```
https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&permissions=268435456&scope=bot
```

Note the Guild ID (right-click server name → Copy Server ID).

---

## 3. Environment Variable Configuration

### Terraform Variables (`terraform.tfvars` or TFC workspace variables)

```hcl
# Discord OAuth
TFC_DISCORD_CLIENT_ID     = "your-discord-client-id"
TFC_DISCORD_CLIENT_SECRET = "your-discord-client-secret"

# Discord Bot
TFC_DISCORD_BOT_TOKEN = "your-discord-bot-token"

# Stripe
TFC_STRIPE_SECRET_KEY    = "sk_live_xxx"  # or sk_test_xxx for staging
TFC_STRIPE_WEBHOOK_SECRET = "whsec_xxx"

# Discord Guild & Roles
TFC_DISCORD_GUILD_ID                = "123456789012345678"
TFC_DISCORD_ROLE_FREE_ID            = "000000000000000000"
TFC_DISCORD_ROLE_EXPLORER_ID        = "111111111111111111"
TFC_DISCORD_ROLE_BUILDER_ID         = "222222222222222222"
TFC_DISCORD_ROLE_BUILDER_ACADEMY_ID = "333333333333333333"
```

### Lambda Environment Variables (set via Terraform)

These are configured automatically by the Terraform module:

| Variable                | Source                          |
|------------------------|---------------------------------|
| MEMBERSHIP_TABLE       | DynamoDB table name             |
| DISCORD_SECRET_NAME    | Secrets Manager ARN (OAuth)     |
| DISCORD_BOT_SECRET_NAME| Secrets Manager ARN (Bot)       |
| STRIPE_SECRET_NAME     | Secrets Manager ARN (Stripe)    |
| STRIPE_WEBHOOK_SECRET_NAME | Secrets Manager ARN (Webhook) |
| JWT_SECRET_NAME        | Secrets Manager ARN (JWT)       |
| SQS_QUEUE_URL          | SQS FIFO queue URL              |
| DISCORD_GUILD_ID       | Guild ID                        |
| DISCORD_ROLE_EXPLORER_ID | Role ID                       |
| DISCORD_ROLE_BUILDER_ID  | Role ID                       |
| DISCORD_ROLE_ACADEMY_ID  | Role ID                       |
| FRONTEND_URL           | Frontend domain URL             |
| ADMIN_USERS            | Comma-separated admin list      |

---

## 4. Terraform Deployment Steps

### Initial Deployment

```bash
cd terraform

# Initialize Terraform (first time or after provider changes)
terraform init

# Review the plan
terraform plan -out=tfplan

# Apply
terraform apply tfplan
```

### Post-Apply Verification

After `terraform apply` succeeds:

```bash
# Verify DynamoDB table created
aws dynamodb describe-table --table-name dsb-platform-membership

# Verify SQS queues created
aws sqs get-queue-url --queue-name dsb-discord-sync.fifo
aws sqs get-queue-url --queue-name dsb-discord-sync-dlq.fifo

# Verify Lambda function
aws lambda get-function --function-name dsb-membership

# Verify secrets exist
aws secretsmanager describe-secret --secret-id dsb/discord-oauth
aws secretsmanager describe-secret --secret-id dsb/discord-bot
aws secretsmanager describe-secret --secret-id dsb/stripe-keys
```

### Updating an Existing Deployment

```bash
cd terraform
terraform plan -out=tfplan
terraform apply tfplan
```

---

## 5. Verification Checklist

### Infrastructure

- [ ] DynamoDB `dsb-platform-membership` table exists with GSI1 and GSI2
- [ ] SQS FIFO queue `dsb-discord-sync.fifo` exists with DLQ configured
- [ ] Lambda function deployed with correct environment variables
- [ ] API Gateway routes resolve (`/auth/discord/*`, `/api/discord/*`, `/api/stripe/*`, `/admin/discord/*`)
- [ ] SQS event source mapping active on Lambda
- [ ] EventBridge Scheduler rule active (24h rate)
- [ ] IAM role has correct permissions (DynamoDB, SQS, Secrets Manager, CloudWatch)

### Stripe Integration

- [ ] `GET /api/stripe/products` returns product list with `dsb_tier` metadata
- [ ] Checkout session creates successfully in Stripe test mode
- [ ] Webhook endpoint receives events (check Stripe Dashboard → Webhooks → Recent Events)
- [ ] Webhook signature validation works (400 on tampered payload)
- [ ] Customer portal session creates successfully

### Discord Integration

- [ ] Bot is online in the target guild
- [ ] Bot can manage roles (verify bot role is above managed roles)
- [ ] OAuth flow redirects correctly to Discord and back
- [ ] Identity confirmation activates the connection
- [ ] Role sync assigns correct role based on tier
- [ ] Disconnect removes managed roles

### End-to-End Flow

- [ ] User signs up → sees pricing page → subscribes via Stripe checkout
- [ ] Webhook fires → membership tier updates in DynamoDB
- [ ] SQS message published → Discord roles sync
- [ ] User connects Discord → confirms identity → joins guild → roles assigned
- [ ] User disconnects Discord → roles removed
- [ ] Admin can view user details, trigger sync, and disconnect users
- [ ] Reconciliation runs on schedule without errors

### Monitoring

- [ ] CloudWatch Logs show Lambda invocations
- [ ] DLQ is empty (no stuck messages)
- [ ] Audit log entries appear for key operations

---

## Troubleshooting

### Common Issues

**Webhook signature validation failing:**
- Verify `STRIPE_WEBHOOK_SECRET_NAME` points to the correct secret
- Ensure the raw request body is passed (not parsed/modified)

**Discord role sync failing:**
- Verify bot token is valid and bot is in the guild
- Check bot role is positioned above managed roles
- Check `DISCORD_GUILD_ID` matches the target server

**OAuth state expired:**
- State tokens have a 10-minute TTL; if user takes too long on Discord's page, they'll get an error
- User can retry the flow

**SQS messages going to DLQ:**
- Check CloudWatch Logs for the Lambda execution errors
- Verify Discord API rate limits aren't being hit
- Messages retry 3 times before DLQ
