# Start Your AI Travel Concierge

## ⚠️ CRITICAL: Add Amadeus API Key First

Before starting, you MUST add your Amadeus API credentials:

1. Go to https://developers.amadeus.com/
2. Register/Login
3. Create a new app
4. Copy your API Key and API Secret
5. Open `backend/.env` and update these lines:
   ```
   AMADEUS_API_KEY=your_actual_key_here
   AMADEUS_API_SECRET=your_actual_secret_here
   ```

## Start the Application

### Terminal 1: Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Terminal 2: Frontend

Open a NEW terminal window:

```bash
cd frontend
npm run dev
```

You should see:
```
▲ Next.js 14.2.0
- Local:        http://localhost:3000
```

## Access the App

Open your browser to: **http://localhost:3000**

## Test It

In the chat interface, try:

> "We want to visit Italy for 10 days in May with 5000€, we have two kids aged 5 and 8"

Watch the AI agents work their magic! You'll see:
- Real-time agent status updates
- 3 complete itineraries (Budget, Balanced, Premium)
- Flight details
- Hotel recommendations
- Daily plans
- Cost breakdowns

## Troubleshooting

### Backend won't start?

1. Make sure you added Amadeus API keys to `backend/.env`
2. Activate virtual environment: `source backend/venv/bin/activate`
3. Check port 8000 isn't in use: `lsof -i :8000`

### Frontend won't connect?

1. Make sure backend is running at http://localhost:8000
2. Check browser console for errors
3. Verify `frontend/.env.local` has correct API URL

### No results returned?

1. Verify Amadeus API keys are correct
2. Check backend logs for errors
3. Try simpler prompts first
4. Check network tab for API responses

## Next Steps

- Read `README.md` for full documentation
- Customize the UI in `frontend/components/`
- Add more agents in `backend/app/agents/`
- Deploy to production (see deployment guides)

---

**Need help?** Check the main README.md or the individual backend/frontend READMEs.
