# AI Travel Concierge

**Multi-agent AI system that transforms travel planning from chaos into clarity.**

Instead of spending hours juggling tabs and comparing options across dozens of websites, simply tell the AI what you want, and it delivers 3 perfectly curated travel itineraries—complete with flights, hotels, activities, and costs—all aligned with your preferences and budget.

---

## The Problem

Travel planning is broken. Families spend 10+ hours:
- Opening 20+ browser tabs
- Comparing flights they've never taken
- Reading hotel reviews from strangers
- Making expensive decisions with incomplete information
- Losing track of what they actually want

**Our solution**: A conversational AI layer that replaces search-and-filter with intelligent curation.

---

## How It Works

### User Experience

1. **Tell us what you want** (one message):
   > "We have 10 days, 5000€ budget, two kids aged 5 and 8, and we love Italy. Show me the best options."

2. **Watch AI agents work in real-time**:
   - Intent Parser extracts your requirements
   - Search Orchestrator queries flight/hotel APIs in parallel
   - Taste Profiler ranks options by your preferences
   - Synthesis Agent creates 3 complete trip plans

3. **Get 3 curated itineraries**:
   - **Budget Explorer**: Smart spending without missing out
   - **Balanced Discovery**: Sweet spot of comfort and value
   - **Premium Escape**: Elevated travel with every detail perfected

Each itinerary includes:
- Complete flight details (with connections, times, prices)
- Hotels matched to your style (with ratings, amenities, location)
- Day-by-day activity plans
- Full cost breakdown
- Reasoning for why this option fits you

---

## Architecture

### Multi-Agent System (LangGraph)

```
User Message
    ↓
Intent Parser Agent (Claude)
    ├─ Extracts dates, budget, travelers, preferences
    ├─ Validates requirements
    └─ Structures into TravelIntent
    ↓
Search Orchestrator Agent
    ├─ Parallel flight search (Amadeus API)
    ├─ Parallel hotel search (Booking.com / Mock)
    └─ Multi-objective optimization (cost, time, quality)
    ↓
Taste Profiler Agent
    ├─ Scores options against user taste profile
    ├─ Learns from past trips and preferences
    └─ Ensures diversity in recommendations
    ↓
Synthesis Agent (Claude)
    ├─ Creates 3 distinct itineraries (Budget, Balanced, Premium)
    ├─ Generates day-by-day plans
    ├─ Explains tradeoffs and reasoning
    └─ Returns complete, bookable trips
```

### Tech Stack

**Backend:**
- **Framework**: FastAPI (Python)
- **Agent Orchestration**: LangGraph
- **LLMs**: Claude 3.5 Sonnet (Anthropic)
- **Flight API**: Amadeus (free tier)
- **Hotel API**: Mock data (or Booking.com via RapidAPI)
- **Database**: PostgreSQL (schema included, optional for MVP)
- **Caching**: Redis

**Frontend:**
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Streaming**: Server-Sent Events (SSE)

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- API Keys:
  - **Anthropic** (required): https://console.anthropic.com/
  - **Amadeus** (required): https://developers.amadeus.com/ (free tier)
  - **OpenAI** (optional): For alternative LLM support

### 1. Clone & Setup

```bash
git clone <your-repo>
cd ai-travel-concierge
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API keys

# Run server
uvicorn app.main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`

API docs: `http://localhost:8000/docs`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# Edit .env.local if backend is not on localhost:8000

# Run dev server
npm run dev
```

Frontend will be available at `http://localhost:3000`

### 4. Test It Out

Open `http://localhost:3000` and try:

> "We want to visit Italy for 10 days in May with 5000€, we have two kids aged 5 and 8"

Watch the agents work and receive 3 complete itineraries in ~10 seconds.

---

## Project Structure

```
ai-travel-concierge/
├── backend/
│   ├── app/
│   │   ├── agents/              # LangGraph agents
│   │   │   ├── intent_parser.py
│   │   │   ├── search_orchestrator.py
│   │   │   ├── taste_profiler.py
│   │   │   ├── synthesis_agent.py
│   │   │   └── workflow.py
│   │   ├── services/            # External API clients
│   │   │   ├── amadeus_client.py
│   │   │   └── hotel_client.py
│   │   ├── models/              # Pydantic models
│   │   │   └── travel.py
│   │   ├── db/                  # Database schema
│   │   └── main.py              # FastAPI app
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── app/                     # Next.js pages
│   ├── components/              # React components
│   │   ├── ChatInterface.tsx
│   │   └── ItineraryDisplay.tsx
│   ├── lib/                     # Types and utilities
│   ├── package.json
│   └── README.md
└── README.md
```

---

## Key Features

### Current (MVP)

✅ **Multi-agent orchestration** with LangGraph
✅ **Natural language intent parsing** (Claude)
✅ **Real flight search** (Amadeus API)
✅ **Hotel search** (mock data for MVP)
✅ **Taste-based ranking** (heuristic profiling)
✅ **3 complete itineraries** per request
✅ **Real-time streaming** (Server-Sent Events)
✅ **Beautiful responsive UI**
✅ **Cost breakdown and reasoning**

### Phase 2 (Next)

- [ ] **PostgreSQL integration** for user profiles
- [ ] **Vector embeddings** for taste matching (Pinecone/Weaviate)
- [ ] **Real hotel API** (Booking.com or alternative)
- [ ] **Activity search** (Viator, GetYourGuide)
- [ ] **User authentication** (OAuth, JWT)
- [ ] **Learning from feedback** (saves, bookings, ratings)
- [ ] **Price alerts** and tracking

### Phase 3 (Future)

- [ ] **Multi-city trips** and complex routing
- [ ] **Group travel** coordination
- [ ] **Direct booking** integration
- [ ] **Calendar sync**
- [ ] **Mobile app** (React Native)
- [ ] **Proactive suggestions** ("It's spring, revisit Italy?")

---

## API Reference

### `POST /api/plan`

Main planning endpoint.

**Request:**
```json
{
  "message": "We want to visit Italy for 10 days in May with 5000€, we have two kids aged 5 and 8",
  "user_id": "user123"
}
```

**Response:**
```json
{
  "success": true,
  "itineraries": [
    {
      "title": "Budget Explorer - Italy",
      "summary": "...",
      "flights": {...},
      "accommodations": [...],
      "daily_plans": [...],
      "total_cost": 4800,
      "why_this_option": "...",
      "tradeoffs": "..."
    }
  ],
  "agent_messages": ["Intent Parser: Understood...", ...],
  "metadata": {...}
}
```

### `POST /api/plan/stream`

Streaming endpoint with real-time agent updates (SSE).

### `GET /health`

Service health check.

---

## Configuration

### Backend API Keys

**Required:**
- `ANTHROPIC_API_KEY`: Claude API key
- `AMADEUS_API_KEY`: Amadeus API key
- `AMADEUS_API_SECRET`: Amadeus secret

**Optional:**
- `OPENAI_API_KEY`: For OpenAI models
- `BOOKING_COM_API_KEY`: Real hotel data (RapidAPI)
- `LANGSMITH_API_KEY`: Agent monitoring
- `DATABASE_URL`: PostgreSQL connection
- `REDIS_URL`: Caching layer

### Frontend

- `NEXT_PUBLIC_API_URL`: Backend URL (default: `http://localhost:8000`)

---

## Development

### Adding a New Agent

1. Create agent file in `backend/app/agents/`
2. Define agent class with processing logic
3. Add node function for LangGraph
4. Update `workflow.py` to include new agent
5. Test with `pytest`

### Monitoring Agents

Enable LangSmith tracing:

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_PROJECT=travel-concierge
```

View traces at https://smith.langchain.com/

---

## Deployment

### Backend

**Recommended**: Docker + AWS ECS/Fargate

```bash
cd backend
docker build -t travel-concierge-backend .
docker run -p 8000:8000 --env-file .env travel-concierge-backend
```

**Alternatives**: GCP Cloud Run, Heroku, Railway

### Frontend

**Recommended**: Vercel

1. Push to GitHub
2. Import in Vercel
3. Set `NEXT_PUBLIC_API_URL` environment variable
4. Deploy

**Alternatives**: Netlify, AWS Amplify, Cloudflare Pages

---

## Example Prompts

Try these to see the system in action:

1. **Family Trip**:
   > "We have 10 days, 5000€ budget, two kids aged 5 and 8. We love Italy—show me the best options."

2. **Romantic Getaway**:
   > "Weekend in Paris for 2, around 1500€, we love art and food"

3. **Adventure Travel**:
   > "Two weeks in Japan, flexible dates in fall, into hiking and authentic food experiences, budget 6000€"

4. **Beach Vacation**:
   > "Relaxing beach vacation for 2 adults, 7 days, around 3000€, prefer all-inclusive"

5. **Budget Backpacking**:
   > "Month in Southeast Asia, ultra budget, solo traveler, love street food and nature"

---

## Why This Matters

### The Vision

Travel planning should feel like having a personal concierge who:
- **Knows you**: Remembers your preferences, learns from every trip
- **Thinks for you**: Compares thousands of options in seconds
- **Explains clearly**: Shows tradeoffs, not just prices
- **Saves time**: Hours of research → one conversation

### The Market

- **$817B** global travel industry (2024)
- **70%** of travelers report planning stress
- **12 hours** average time spent planning a trip
- **Untapped opportunity**: No one has built true AI-native travel planning

### The Product

Not another booking site. A **horizontal intelligence layer** that:
- Sits on top of the entire travel ecosystem
- Turns complexity into clarity
- Gives travelers confidence without the work

---

## Contributing

We welcome contributions! Areas of focus:

- **Agent improvements**: Better reasoning, more sources
- **UI/UX**: Design enhancements, mobile optimization
- **Integrations**: New APIs (activities, car rentals, etc.)
- **Features**: Save trips, share itineraries, price tracking
- **Performance**: Caching, optimization, parallel processing

---

## License

MIT License - see LICENSE file for details

---

## Support

- **Documentation**: See `/backend/README.md` and `/frontend/README.md`
- **Issues**: GitHub Issues
- **API Docs**: `http://localhost:8000/docs` (when running)

---

## Acknowledgments

Built with:
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Agent orchestration
- [Claude](https://www.anthropic.com/claude) - LLM reasoning
- [Amadeus](https://developers.amadeus.com/) - Flight data
- [Next.js](https://nextjs.org/) - Frontend framework
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework

---

**Built by**: Your Team
**Status**: MVP Complete
**Next**: Phase 2 - User profiles and learning
