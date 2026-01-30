# Aptly Production Deployment Guide

This guide walks you through deploying Aptly to production on Railway with Supabase and Redis.

## Prerequisites

- Railway account with a project created
- Supabase account with a project created
- Redis service (Railway Redis add-on or Upstash)
- (Optional) Sentry account for error tracking

## Step 1: Set Up Supabase

### 1.1 Run Database Migrations

Using the Supabase CLI:

```bash
# Link to your project (one-time setup)
supabase link --project-ref your-project-ref

# Push migrations to production
supabase db push
```

> **Note:** Get your project ref from the Supabase dashboard URL: `https://supabase.com/dashboard/project/<project-ref>`

### 1.2 Get Your Credentials

1. Go to **Project Settings** → **API**
2. Copy:
   - **Project URL** → This is your `SUPABASE_URL`
   - **service_role key** (not anon key!) → This is your `SUPABASE_SERVICE_KEY`

> **Important:** Use the service role key, not the anon key. The service role key bypasses Row Level Security, which is required for the backend.

## Step 2: Set Up Redis

### Option A: Railway Redis (Recommended)

1. In your Railway project, click **+ New**
2. Select **Database** → **Redis**
3. Once provisioned, click on the Redis service
4. Go to **Variables** tab
5. Copy the `REDIS_URL` value

### Option B: Upstash (Serverless)

1. Sign up at [upstash.com](https://upstash.com)
2. Create a new Redis database
3. Copy the Redis URL from the dashboard

## Step 3: Configure Railway

### 3.1 Connect Your Repository

1. In Railway, click **+ New** → **GitHub Repo**
2. Select your Aptly repository
3. Railway will auto-detect it as a Python project

### 3.2 Set Environment Variables

In your Railway service, go to **Variables** and add:

| Variable | Value | Required |
|----------|-------|----------|
| `SUPABASE_URL` | Your Supabase project URL | Yes |
| `SUPABASE_SERVICE_KEY` | Your Supabase service role key | Yes |
| `REDIS_URL` | Your Redis connection string | Yes |
| `APTLY_ADMIN_SECRET` | A secure random string (32+ chars) | Yes |
| `ENVIRONMENT` | `production` | Yes |
| `LOG_LEVEL` | `info` | No |
| `SENTRY_DSN` | Your Sentry DSN | No |

**Generate a secure admin secret:**
```bash
openssl rand -base64 32
```

### 3.3 Configure Build Settings

Railway should auto-detect settings from `railway.toml`, but verify:

- **Build Command:** `pip install -r requirements.txt && python -m spacy download en_core_web_sm`
- **Start Command:** `uvicorn src.main:app --host 0.0.0.0 --port $PORT`

## Step 4: Deploy

1. Push to your main branch, or
2. Click **Deploy** in Railway dashboard

Railway will build and deploy your application.

## Step 5: Verify Deployment

### Quick Check

```bash
./scripts/verify_deployment.sh https://your-app.railway.app
```

### Full Smoke Test

```bash
python scripts/smoke_test.py \
  --url https://your-app.railway.app \
  --admin-secret your-admin-secret
```

### Optional: Test Chat Completion

```bash
python scripts/smoke_test.py \
  --url https://your-app.railway.app \
  --admin-secret your-admin-secret \
  --openai-key sk-your-openai-key
```

## Step 6: Create Your First Customer

```bash
curl -X POST https://your-app.railway.app/v1/admin/customers \
  -H "X-Admin-Secret: your-admin-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@yourcompany.com",
    "company_name": "Your Company",
    "plan": "pro"
  }'
```

Save the returned API key - it's only shown once!

## Optional: Set Up Sentry

1. Create a Sentry account at [sentry.io](https://sentry.io)
2. Create a new project (Python → FastAPI)
3. Copy the DSN
4. Add `SENTRY_DSN` to your Railway environment variables
5. Redeploy

## Troubleshooting

### Health Check Shows `database: error`

- Verify `SUPABASE_URL` is correct (should be `https://xxx.supabase.co`)
- Verify `SUPABASE_SERVICE_KEY` is the service role key (starts with `eyJ...`)
- Check that migrations were run successfully

### Health Check Shows `redis: error`

- Verify `REDIS_URL` is correct
- If using Railway Redis, ensure it's in the same project
- Check that the Redis service is running

### 502 Bad Gateway

- Check Railway logs for Python errors
- Verify all required environment variables are set
- Ensure the spaCy model downloaded successfully

### Rate Limiting Not Working

- Verify Redis is connected (health check shows `redis: ok`)
- Check that `REDIS_URL` includes the password if required

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SUPABASE_URL` | Yes | - | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Yes | - | Supabase service role key |
| `REDIS_URL` | Yes | - | Redis connection string |
| `APTLY_ADMIN_SECRET` | Yes | - | Secret for admin endpoints |
| `ENVIRONMENT` | No | `development` | Environment name |
| `LOG_LEVEL` | No | `info` | Logging level |
| `PORT` | No | `8000` | Server port (set by Railway) |
| `SENTRY_DSN` | No | - | Sentry error tracking DSN |
| `RATE_LIMIT_FREE` | No | `100` | Requests/hour for free plan |
| `RATE_LIMIT_PRO` | No | `1000` | Requests/hour for pro plan |
| `RATE_LIMIT_ENTERPRISE` | No | `10000` | Requests/hour for enterprise |

## Security Checklist

- [ ] `APTLY_ADMIN_SECRET` is a strong, unique value (32+ characters)
- [ ] `SUPABASE_SERVICE_KEY` is not committed to version control
- [ ] Production environment variables are only in Railway (not in `.env`)
- [ ] `.env` file is in `.gitignore`
- [ ] HTTPS is enabled (Railway provides this automatically)
