# AI Travel Concierge - Frontend

Beautiful, responsive Next.js frontend with real-time agent streaming and itinerary display.

## Features

- **Conversational Interface**: Chat with AI agents in natural language
- **Real-time Streaming**: Watch agents work with Server-Sent Events
- **Beautiful UI**: Modern design with Tailwind CSS
- **Responsive**: Works on desktop, tablet, and mobile
- **Itinerary Display**: Interactive cards showing flights, hotels, and daily plans
- **Multiple Options**: Compare 3 different trip styles side-by-side

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Hooks
- **API Communication**: Fetch API with SSE support

## Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Copy `.env.local.example` to `.env.local`:

```bash
cp .env.local.example .env.local
```

Make sure the API URL matches your backend:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
frontend/
├── app/
│   ├── globals.css       # Global styles and Tailwind
│   ├── layout.tsx        # Root layout
│   └── page.tsx          # Main page (chat + itinerary)
├── components/
│   ├── ChatInterface.tsx      # Chat UI with SSE
│   └── ItineraryDisplay.tsx   # Itinerary cards
├── lib/
│   └── types.ts          # TypeScript types
├── public/               # Static assets
├── next.config.js
├── tailwind.config.ts
└── tsconfig.json
```

## Usage

### Example Prompts

Try these prompts in the chat interface:

1. "We want to visit Italy for 10 days in May with 5000€, we have two kids aged 5 and 8"
2. "Relaxing beach vacation for 2 adults, 7 days, around 3000€"
3. "Adventure trip to Japan in fall, flexible dates, love hiking and food"
4. "Family trip to Barcelona for 5 days, budget-friendly, kids ages 3 and 6"

### How It Works

1. User enters travel request in natural language
2. Request is sent to backend via `/api/plan/stream`
3. Backend agents process request:
   - Intent Parser extracts requirements
   - Search Orchestrator finds flights/hotels
   - Taste Profiler ranks options
   - Synthesis Agent creates 3 itineraries
4. Frontend receives real-time updates via Server-Sent Events
5. Final itineraries are displayed with full details

## Customization

### Styling

Modify `tailwind.config.ts` to change colors:

```ts
theme: {
  extend: {
    colors: {
      primary: {
        // Your custom color palette
      }
    }
  }
}
```

### Components

All components are in `components/` and can be customized:
- `ChatInterface.tsx`: Modify chat UI, add features like file upload
- `ItineraryDisplay.tsx`: Change layout, add booking integration

### API Integration

The API client is built into `ChatInterface.tsx`. To add features:

```ts
// In ChatInterface.tsx
const response = await fetch(`${API_URL}/api/plan/stream`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    // Add auth headers here
  },
  body: JSON.stringify({
    message: userMessage,
    user_id: userId, // Use actual user ID
  }),
})
```

## Deployment

### Vercel (Recommended)

1. Push code to GitHub
2. Import project in Vercel
3. Set environment variable: `NEXT_PUBLIC_API_URL=your_backend_url`
4. Deploy

### Other Platforms

Build the app:

```bash
npm run build
```

Start production server:

```bash
npm start
```

## Features to Add

### Phase 2
- [ ] User authentication (NextAuth.js)
- [ ] Save favorite itineraries
- [ ] Share itineraries via link
- [ ] Export to PDF/Calendar
- [ ] Price alerts
- [ ] Multi-language support

### Phase 3
- [ ] Direct booking integration
- [ ] Group travel (invite others)
- [ ] Real-time collaboration
- [ ] Mobile app (React Native)

## Troubleshooting

### CORS Errors

Make sure backend allows your frontend origin in `settings.allowed_origins`:

```python
# backend/app/utils/config.py
allowed_origins = ["http://localhost:3000"]
```

### SSE Connection Issues

Check that:
1. Backend is running on correct port
2. `NEXT_PUBLIC_API_URL` is set correctly
3. No proxy/firewall blocking SSE connections

### Styles Not Loading

Make sure Tailwind is configured:

```bash
# Restart dev server
npm run dev
```

## License

MIT
