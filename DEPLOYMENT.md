# Voyana Deployment Guide

This guide will help you deploy Voyana to production using:
- **Render** for the backend (FastAPI)
- **Vercel** for the frontend (Next.js)

## Prerequisites

1. GitHub account with your code pushed to a repository
2. Render account (https://render.com)
3. Vercel account (https://vercel.com)
4. All required API keys ready

## Part 1: Deploy Backend to Render

### Step 1: Push Code to GitHub

```bash
cd /Users/bogdantudosoiu/Desktop/code/ai-travel-concierge
git add .
git commit -m "Prepare for production deployment"
git push origin master
```

### Step 2: Create Render Web Service

1. Go to https://render.com/dashboard
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `voyana-backend`
   - **Region**: Choose closest to your users
   - **Branch**: `master`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free (or paid for better performance)

### Step 3: Configure Environment Variables on Render

In the Render dashboard, add these environment variables:

**Required:**
- `OPENAI_API_KEY` = your OpenAI API key
- `AMADEUS_API_KEY` = your Amadeus API key
- `AMADEUS_API_SECRET` = your Amadeus API secret
- `HOTELBEDS_API_KEY` = your Hotelbeds API key
- `HOTELBEDS_API_SECRET` = your Hotelbeds API secret
- `SECRET_KEY` = generate a random string (e.g., `openssl rand -hex 32`)
- `ALLOWED_ORIGINS` = `*` (or specific frontend URL after Vercel deployment)
- `ANTHROPIC_API_KEY` = your Anthropic API key

**Optional (can set to dummy values for now):**
- `DATABASE_URL` = `sqlite:///./voyana.db` (or PostgreSQL URL if you have one)
- `REDIS_URL` = `redis://localhost:6379` (or actual Redis URL)
- `SERPAPI_KEY` = your SerpAPI key (optional)
- `LANGSMITH_API_KEY` = your LangSmith key (optional)
- `ENVIRONMENT` = `production`
- `DEBUG` = `False`

### Step 4: Deploy Backend

1. Click **"Create Web Service"**
2. Render will automatically build and deploy
3. Wait for the deployment to complete (check logs)
4. Note your backend URL: `https://voyana-backend.onrender.com`

### Step 5: Test Backend

Visit your backend URL + `/health`:
```
https://voyana-backend.onrender.com/health
```

You should see a healthy response.

---

## Part 2: Deploy Frontend to Vercel

### Step 1: Prepare Frontend Environment

1. Update your frontend to use the production backend URL
2. The API URL should point to your Render backend

### Step 2: Deploy to Vercel

#### Option A: Using Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Navigate to frontend
cd frontend

# Deploy
vercel

# Follow prompts:
# - Link to existing project or create new
# - Set root directory: frontend (if deploying from root)
# - Override settings: No
```

#### Option B: Using Vercel Dashboard

1. Go to https://vercel.com/dashboard
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository
4. Configure the project:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
   - **Install Command**: `npm install`

### Step 3: Configure Environment Variables on Vercel

Add this environment variable in Vercel:

- `NEXT_PUBLIC_API_URL` = `https://voyana-backend.onrender.com`

### Step 4: Deploy Frontend

1. Click **"Deploy"**
2. Vercel will build and deploy automatically
3. Your app will be live at: `https://your-app.vercel.app`

### Step 5: Update Backend CORS

Now that you have your frontend URL, update the backend:

1. Go to Render dashboard → your backend service
2. Update environment variable:
   - `ALLOWED_ORIGINS` = `https://your-app.vercel.app,https://www.yourapp.com`
3. Save and redeploy

---

## Part 3: Post-Deployment

### Test the Full Application

1. Visit your Vercel URL
2. Try creating a travel plan
3. Check that:
   - Chat interface works
   - Agent streaming works
   - Itineraries are generated
   - Images load correctly

### Monitor Logs

**Backend (Render):**
- Go to Render dashboard → Logs tab

**Frontend (Vercel):**
- Go to Vercel dashboard → Deployments → View Function Logs

### Common Issues

**Issue 1: CORS errors**
- Solution: Make sure `ALLOWED_ORIGINS` on Render includes your Vercel URL

**Issue 2: API not responding**
- Solution: Check Render logs, ensure all environment variables are set

**Issue 3: Build failures**
- Solution: Check build logs, ensure all dependencies are in package.json/requirements.txt

---

## Custom Domain (Optional)

### For Frontend (Vercel)
1. Go to Vercel project settings → Domains
2. Add your custom domain
3. Configure DNS records as shown

### For Backend (Render)
1. Go to Render service settings → Custom Domain
2. Add your custom domain
3. Configure DNS records as shown

---

## Environment Variables Reference

### Backend (.env)
```env
# OpenAI
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Amadeus
AMADEUS_API_KEY=...
AMADEUS_API_SECRET=...

# Hotelbeds
HOTELBEDS_API_KEY=...
HOTELBEDS_API_SECRET=...

# App Config
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=https://your-app.vercel.app
ENVIRONMENT=production
DEBUG=False

# Database (optional for MVP)
DATABASE_URL=sqlite:///./voyana.db
REDIS_URL=redis://localhost:6379

# Optional
SERPAPI_KEY=...
LANGSMITH_API_KEY=...
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=https://voyana-backend.onrender.com
```

---

## Costs Estimate

### Free Tier
- **Render Free**: Backend with 512MB RAM, sleeps after inactivity
- **Vercel Free**: Unlimited deployments, 100GB bandwidth
- **Total**: $0/month

### Recommended Paid
- **Render Starter**: $7/month (no sleep, better performance)
- **Vercel Pro**: $20/month (better performance, analytics)
- **Total**: $27/month

---

## Next Steps

1. ✅ Deploy backend to Render
2. ✅ Deploy frontend to Vercel
3. Set up custom domain (optional)
4. Configure monitoring (Sentry, LogRocket, etc.)
5. Set up CI/CD for automatic deployments
6. Add database (PostgreSQL on Render or Supabase)
7. Add Redis (Redis Cloud or Upstash)

---

## Support

If you encounter issues:
1. Check Render logs
2. Check Vercel deployment logs
3. Test API endpoints directly
4. Verify all environment variables are set
