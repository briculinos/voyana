# Voyana Deployment Guide

This guide covers deploying Voyana to production with Railway (backend) and Vercel (frontend).

## Prerequisites

1. Railway account (https://railway.app)
2. Vercel account (https://vercel.com)
3. Google Cloud Console project with OAuth 2.0 credentials
4. API keys for Amadeus, SerpAPI, Hotelbeds, OpenAI, and Anthropic

## Backend Deployment (Railway)

### 1. Deploy to Railway

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Select the `ai-travel-concierge` repository
4. Railway will auto-detect the Python app in the `backend` folder

### 2. Configure Environment Variables

In Railway project settings, add these environment variables:

```bash
# API Keys
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
LANGSMITH_API_KEY=your_langsmith_api_key

# Amadeus
AMADEUS_API_KEY=your_amadeus_api_key
AMADEUS_API_SECRET=your_amadeus_api_secret

# SerpAPI
SERPAPI_KEY=your_serpapi_key

# Hotels API
HOTELBEDS_API_KEY=your_hotelbeds_api_key
HOTELBEDS_API_SECRET=your_hotelbeds_api_secret

# Database
DATABASE_URL=sqlite:///./voyana.db

# App Settings
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=generate-a-strong-random-secret-key-here
ALLOWED_ORIGINS=https://voyana.vercel.app

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
ALLOWED_EMAILS=email1@gmail.com,email2@gmail.com,email3@gmail.com

# LangSmith
LANGCHAIN_TRACING_V2=false
LANGCHAIN_PROJECT=travel-concierge
```

### 3. Get Railway URL

After deployment, Railway will provide a URL like:
```
https://voyana-production.up.railway.app
```

Save this URL - you'll need it for frontend configuration.

## Frontend Deployment (Vercel)

### 1. Deploy to Vercel

1. Go to https://vercel.com
2. Click "Add New Project" → "Import Git Repository"
3. Select the `ai-travel-concierge` repository
4. Set the root directory to `frontend`
5. Framework preset: Next.js
6. Build command: `npm run build`
7. Output directory: `.next`

### 2. Configure Environment Variables

In Vercel project settings, add these environment variables:

```bash
# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# NextAuth
NEXTAUTH_URL=https://voyana.vercel.app
NEXTAUTH_SECRET=generate-a-strong-random-secret-key-here

# Backend API
NEXT_PUBLIC_API_URL=https://voyana-production.up.railway.app
```

### 3. Generate NEXTAUTH_SECRET

Run this command to generate a secure random secret:

```bash
openssl rand -base64 32
```

## Google Cloud Console Setup

### 1. Configure OAuth Consent Screen

1. Go to https://console.cloud.google.com
2. Navigate to "APIs & Services" → "OAuth consent screen"
3. Add authorized domains:
   - `vercel.app`
   - `railway.app`

### 2. Configure OAuth Credentials

1. Go to "Credentials" → Click your OAuth 2.0 Client ID
2. Add authorized redirect URIs:
   ```
   http://localhost:3000/api/auth/callback/google
   https://voyana.vercel.app/api/auth/callback/google
   ```

## Post-Deployment Checklist

- [ ] Backend is deployed on Railway and health check passes
- [ ] Frontend is deployed on Vercel
- [ ] CORS is configured with Vercel URL in Railway
- [ ] Google OAuth redirect URIs are updated
- [ ] Email whitelist is configured in Railway
- [ ] Test authentication flow on production
- [ ] Test travel planning flow on production

## Troubleshooting

### CORS Errors

If you see CORS errors in the browser console:
1. Check `ALLOWED_ORIGINS` in Railway includes your Vercel URL
2. Ensure the URL format is exact (https://, no trailing slash)
3. Restart the Railway service after changing environment variables

### Authentication Fails

If Google login doesn't work:
1. Check `GOOGLE_CLIENT_ID` matches in both Railway and Vercel
2. Verify redirect URIs are correctly configured in Google Cloud Console
3. Check browser console for specific error messages
4. Ensure `NEXTAUTH_URL` in Vercel matches your Vercel deployment URL

### Email Whitelist Not Working

If unauthorized emails can access:
1. Check `ALLOWED_EMAILS` is set in Railway (comma-separated, no spaces)
2. Restart Railway service to pick up new environment variables
3. Check Railway logs for authentication attempts

## Monitoring

### Railway Logs

View backend logs in Railway dashboard:
- Check for authentication events
- Monitor API errors
- Track agent execution

### Vercel Logs

View frontend logs in Vercel dashboard:
- Check for build errors
- Monitor runtime errors
- Track user sessions

## Updating the Application

### Backend Updates

1. Push changes to GitHub
2. Railway auto-deploys on push to main branch
3. Check Railway logs for deployment status

### Frontend Updates

1. Push changes to GitHub
2. Vercel auto-deploys on push to main branch
3. Check Vercel deployment logs

## Security Notes

- Never commit `.env` files to git
- Rotate `SECRET_KEY` and `NEXTAUTH_SECRET` regularly
- Review `ALLOWED_EMAILS` list periodically
- Monitor API usage for unusual patterns
- Keep dependencies updated for security patches
