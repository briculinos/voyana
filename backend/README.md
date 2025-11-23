# AI Travel Concierge - Backend

Multi-agent AI system for personalized travel planning, built with LangGraph and FastAPI.

## Architecture

### Agent System (LangGraph)

1. **Intent Parser Agent** - Extracts structured travel requirements from natural language
2. **Search Orchestrator Agent** - Coordinates parallel searches across flight/hotel APIs
3. **Taste Profiler Agent** - Ranks options based on user preferences
4. **Synthesis Agent** - Creates 3 complete, curated itineraries

### Tech Stack

- **Framework**: FastAPI
- **Agent Orchestration**: LangGraph
- **LLMs**: Claude 3.5 Sonnet (Anthropic)
- **Flight API**: Amadeus (free tier)
- **Hotel API**: Mock data (or Booking.com via RapidAPI)
- **Database**: PostgreSQL (schema included, optional for MVP)

## Setup

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required API keys:
- **Anthropic API Key**: Get from https://console.anthropic.com/
- **OpenAI API Key** (optional): For alternative LLM support
- **Amadeus API**: Free tier at https://developers.amadeus.com/
  - Sign up → Create app → Get API key & secret

Optional (for Phase 2):
- Booking.com API via RapidAPI
- PostgreSQL database URL
- LangSmith for agent monitoring

### 3. Run the Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --port 8000

# Or using the main script
python -m app.main
```

Server will start at `http://localhost:8000`

## API Endpoints

### `POST /api/plan`
Main planning endpoint. Returns 3 complete itineraries.

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
  "agent_messages": ["Intent Parser: Understood your request...", ...],
  "errors": [],
  "parsed_intent": {...},
  "metadata": {
    "num_flight_options": 10,
    "num_hotel_options": 15,
    "num_itineraries": 3
  }
}
```

### `POST /api/plan/stream`
Streaming endpoint with real-time agent updates (Server-Sent Events).

### `GET /health`
Health check and service status.

### `GET /api/destinations`
List of popular destinations for autocomplete.

## Testing

### Quick Test

```bash
# Test with curl
curl -X POST http://localhost:8000/api/plan \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want a relaxing beach vacation for 2 adults, 7 days, around 3000€",
    "user_id": "test_user"
  }'
```

### Run Tests

```bash
pytest tests/
```

## Development

### Project Structure

```
backend/
├── app/
│   ├── agents/           # LangGraph agents
│   │   ├── intent_parser.py
│   │   ├── search_orchestrator.py
│   │   ├── taste_profiler.py
│   │   ├── synthesis_agent.py
│   │   └── workflow.py   # LangGraph workflow
│   ├── api/              # API routes (future)
│   ├── models/           # Pydantic models
│   │   └── travel.py
│   ├── services/         # External API clients
│   │   ├── amadeus_client.py
│   │   └── hotel_client.py
│   ├── db/               # Database (Phase 2)
│   │   └── schema.sql
│   ├── utils/
│   │   └── config.py
│   └── main.py           # FastAPI app
├── tests/
├── requirements.txt
└── README.md
```

### Agent Workflow

```
User Message
    ↓
Intent Parser (Claude)
    ↓
Search Orchestrator (Amadeus + Hotels)
    ↓
Taste Profiler (Scoring)
    ↓
Synthesis Agent (Claude)
    ↓
3 Complete Itineraries
```

### Adding New Agents

1. Create agent file in `app/agents/`
2. Define agent class with main function
3. Add node wrapper function
4. Update `workflow.py` to include new agent
5. Update graph edges

## Monitoring

Enable LangSmith for agent tracing:

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_PROJECT=travel-concierge
```

View traces at https://smith.langchain.com/

## Deployment

### Docker (recommended)

```bash
docker build -t travel-concierge-backend .
docker run -p 8000:8000 --env-file .env travel-concierge-backend
```

### Cloud Platforms

- **AWS**: Deploy on ECS/Fargate or Lambda (with increased timeout)
- **GCP**: Cloud Run or App Engine
- **Heroku**: Use Procfile with uvicorn

## Roadmap

### Phase 1 (MVP) ✅
- [x] Multi-agent system with LangGraph
- [x] Intent parsing with structured output
- [x] Flight search (Amadeus)
- [x] Hotel search (mock data)
- [x] Basic taste profiling
- [x] Itinerary synthesis

### Phase 2
- [ ] PostgreSQL integration for user profiles
- [ ] Vector database for taste embeddings
- [ ] Real hotel API integration
- [ ] Activity/experience search
- [ ] User authentication
- [ ] Feedback loop and learning

### Phase 3
- [ ] Multi-city trips
- [ ] Group travel coordination
- [ ] Price alerts and rebooking
- [ ] Calendar integration
- [ ] Booking automation

## License

MIT
