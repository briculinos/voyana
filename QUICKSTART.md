# Quick Start Guide

Get your AI Travel Concierge running in 10 minutes.

## Prerequisites Checklist

Before you begin, make sure you have:

- [ ] Python 3.11 or higher installed
- [ ] Node.js 18 or higher installed
- [ ] An Anthropic API key ([get one here](https://console.anthropic.com/))
- [ ] An Amadeus API key ([get one here](https://developers.amadeus.com/))

## Step-by-Step Setup

### Step 1: Get API Keys (5 minutes)

#### Anthropic API Key (Required)

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Click "API Keys" in the sidebar
4. Click "Create Key"
5. Copy the key (starts with `sk-ant-...`)

#### Amadeus API Key (Required)

1. Go to https://developers.amadeus.com/
2. Click "Register" (top right)
3. Complete registration and verify email
4. Go to "My Self-Service Workspace"
5. Click "Create New App"
6. Name it "Travel Concierge" (or anything)
7. Copy **API Key** and **API Secret**

**Note**: Amadeus Test API is completely free with generous limits.

---

### Step 2: Backend Setup (3 minutes)

```bash
# Navigate to project
cd ai-travel-concierge/backend

# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies (takes 1-2 minutes)
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

Now edit the `.env` file with your API keys:

```bash
# Open .env in your editor
# On macOS:
open .env
# On Windows:
notepad .env
# On Linux:
nano .env
```

**Minimum required configuration:**

```env
ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE
AMADEUS_API_KEY=YOUR_AMADEUS_KEY
AMADEUS_API_SECRET=YOUR_AMADEUS_SECRET

# These can stay as defaults for testing
OPENAI_API_KEY=sk-placeholder
BOOKING_COM_API_KEY=placeholder
DATABASE_URL=postgresql://user:password@localhost:5432/travel_concierge
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your_secret_key_here_change_in_production
```

**Start the backend:**

```bash
# Still in backend/ directory
uvicorn app.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Test it**: Open http://localhost:8000/health in your browser. You should see:
```json
{
  "status": "healthy",
  "agents": ["intent_parser", "search_orchestrator", "taste_profiler", "synthesis_agent"],
  "features": {...}
}
```

Leave this terminal running! Open a **new terminal** for the frontend.

---

### Step 3: Frontend Setup (2 minutes)

In a **new terminal**:

```bash
# Navigate to frontend
cd ai-travel-concierge/frontend

# Install dependencies (takes 1-2 minutes)
npm install

# Create .env.local file
cp .env.local.example .env.local

# Start dev server
npm run dev
```

You should see:
```
  ▲ Next.js 14.2.0
  - Local:        http://localhost:3000
  - Ready in 2.5s
```

**Open the app**: Go to http://localhost:3000

---

### Step 4: Test It! (1 minute)

In the chat interface at http://localhost:3000, type:

> "We want to visit Italy for 10 days in May with 5000€, we have two kids aged 5 and 8"

Click **Send** and watch:

1. ✅ Agent messages appear in real-time
2. ✅ Progress updates show each agent working
3. ✅ After ~10-15 seconds, 3 complete itineraries appear
4. ✅ Click between options to compare

**Expected result**: 3 itinerary cards (Budget, Balanced, Premium) with:
- Flight details
- Hotel recommendations
- Daily plans
- Cost breakdowns
- Explanations

---

## Troubleshooting

### Backend won't start

**Error: `ModuleNotFoundError`**
```bash
# Make sure venv is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**Error: `pydantic_core._pydantic_core.ValidationError`**
- Check that your `.env` file has all required keys
- Make sure API keys don't have extra spaces or quotes

### Frontend won't start

**Error: `Cannot find module`**
```bash
# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Error: `EADDRINUSE: address already in use`**
- Port 3000 is taken. Kill the process or use a different port:
```bash
npm run dev -- -p 3001
```

### API Errors

**Error: `401 Unauthorized` in backend logs**
- Your API keys are invalid or expired
- Double-check keys in `.env` file
- Amadeus: Make sure you copied both API Key AND API Secret

**Error: `No flights found`**
- Amadeus Test API has limited routes
- Try common routes: LON→PAR, NYC→LAX, etc.
- Or use mock mode (agents will generate sample data)

**Error: `CORS` errors in browser console**
- Make sure backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL` in frontend `.env.local`
- Restart both servers

### Slow responses

**First request takes 20-30 seconds**
- This is normal! Cold start includes:
  - Loading LLM models
  - Authenticating with APIs
  - Searching thousands of flights
- Subsequent requests are much faster (~5-10 seconds)

---

## What's Next?

Now that it's running:

1. **Try different prompts** (see examples below)
2. **Read the architecture** (`README.md`)
3. **Explore the code** (start with `backend/app/agents/workflow.py`)
4. **Customize the UI** (`frontend/components/`)
5. **Add features** (see Phase 2 roadmap)

### More Example Prompts

```
"Weekend in Paris for 2, around 1500€, we love art and food"

"Two weeks in Japan, flexible dates in fall, into hiking and authentic food experiences, budget 6000€"

"Relaxing beach vacation for 2 adults, 7 days, around 3000€"

"Family trip to Barcelona for 5 days, budget-friendly, kids ages 3 and 6"

"Solo backpacking trip to Southeast Asia, 3 weeks, ultra budget"
```

---

## Development Tips

### Backend Development

**Watch logs in detail:**
```bash
uvicorn app.main:app --reload --log-level debug
```

**Test agents individually:**
```python
# In Python REPL
from app.agents.intent_parser import IntentParserAgent
from app.models.travel import AgentState

agent = IntentParserAgent()
state = AgentState(user_message="Trip to Italy for 10 days with 5000€")
result = agent.parse_intent(state)
print(result.parsed_intent)
```

**Enable LangSmith tracing:**
```bash
# In .env
LANGCHAIN_TRACING_V2=true
LANGSMITH_API_KEY=your_langsmith_key
```

### Frontend Development

**Component hot reload:**
- Just save files in `components/` and see changes instantly

**Debug API calls:**
- Open browser DevTools → Network tab
- Filter by "plan" to see API requests
- Check SSE events in EventStream

**Customize styling:**
- Edit `tailwind.config.ts` for colors
- Modify `app/globals.css` for global styles

---

## Next Steps

1. ✅ **Working MVP**: You have a functional multi-agent travel planner
2. 📚 **Learn the system**: Read `README.md` for architecture details
3. 🎨 **Customize**: Modify UI, add your branding
4. 🚀 **Deploy**: Follow deployment guides in READMEs
5. 💾 **Add database**: Set up PostgreSQL for user profiles (Phase 2)
6. 🤖 **Improve agents**: Better reasoning, more data sources

---

## Support

- **Full documentation**: `README.md`
- **Backend details**: `backend/README.md`
- **Frontend details**: `frontend/README.md`
- **API docs**: http://localhost:8000/docs (when backend is running)

**Having issues?** Check:
1. Both terminals are running (backend + frontend)
2. API keys are correct in `.env`
3. Python venv is activated
4. No port conflicts (8000, 3000)

---

**Congratulations!** You're now running a production-ready multi-agent AI travel concierge. 🎉
