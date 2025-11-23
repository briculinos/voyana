"""
Intent Parser Agent
Extracts structured travel requirements from natural language input.
Uses OpenAI's structured output capabilities via LangChain.
"""
import logging
from typing import Dict, Any
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from app.models.travel import TravelIntent, AgentState
from app.utils.config import settings

logger = logging.getLogger(__name__)


class IntentParserAgent:
    """
    Agent that parses user's natural language travel request
    into structured TravelIntent object.
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.openai_api_key,
            temperature=0,
        )

        self.parser = PydanticOutputParser(pydantic_object=TravelIntent)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert travel intent parser and trip planner. Your job is to extract structured travel requirements from natural language.

Key responsibilities:
1. Identify all travel parameters: dates, duration, budget, travelers, preferences
2. Infer missing information using reasonable defaults
3. Parse flexible language (e.g., "spring break" -> specific dates, "two kids" -> children count)
4. Extract preferences about travel style, accommodation, activities

**CRITICAL - Origin Extraction:**
ALWAYS extract the origin city from phrases like:
- "Traveling from [City]" -> origin: "[City]"
- "From [City] to [Destination]" -> origin: "[City]"
- If no origin is mentioned, set origin: null

**CRITICAL - Destination Logic:**
If the user provides a VAGUE or FLEXIBLE destination description (like "beach", "mountains", "warm place", "cultural city"):
- You MUST suggest a SPECIFIC destination city that matches their criteria
- Consider their origin city to suggest nearby/accessible destinations
- Examples:
  * "beach vacation" from Copenhagen -> "Barcelona, Spain" or "Nice, France" or "Lisbon, Portugal"
  * "mountains" from Copenhagen -> "Innsbruck, Austria" or "Chamonix, France"
  * "warm place" in winter -> "Canary Islands, Spain" or "Dubai, UAE"
  * "cultural city" -> "Rome, Italy" or "Paris, France" or "Prague, Czech Republic"
- Set the destination field to the specific city name (e.g., "Barcelona, Spain")
- Add the general preference to interests (e.g., interests: ["beach"])

**CRITICAL - Date Suggestion Logic:**
If the user does NOT provide specific dates OR provides vague dates like "fall", "spring", "summer", "winter":
- **ALWAYS suggest dates in the FUTURE** (at least 2-4 weeks from today: {current_date})
- **If user says "fall" or "autumn" without a year:**
  * If current date is before September: suggest fall of CURRENT year
  * If current date is September or later: suggest fall of NEXT year
- **If user says "spring" without a year:**
  * If current date is before March: suggest spring of CURRENT year
  * If current date is March or later: suggest spring of NEXT year
- **If user says "summer" without a year:**
  * If current date is before June: suggest summer of CURRENT year
  * If current date is June or later: suggest summer of NEXT year
- **If user says "winter" without a year:**
  * If current date is before December: suggest winter of CURRENT year
  * If current date is December or later: suggest winter of NEXT year
- Suggest optimal dates based on:
  * Destination's best season (e.g., Rome: April-June or September-October for good weather, fewer crowds)
  * Family travel: Suggest school holiday periods if traveling with children
  * Budget constraints: Off-season dates for budget travelers
  * Duration mentioned: Calculate return date from departure date
- Set departure_date and return_date to your suggested optimal dates
- Set date_flexibility to 7 days to allow the search to find best prices

When information is ambiguous or missing:
- Use context clues (e.g., "family trip with kids" implies kid-friendly preferences)
- Make reasonable assumptions for non-critical details
- ALWAYS suggest specific destination if user provides vague description
- ALWAYS suggest dates if none provided - never leave dates empty

{format_instructions}

Examples:
User: "We want to visit Rome, Italy for 10 days with 5000€. Traveling from Copenhagen. 2 adults."
-> origin: "Copenhagen", destination: "Rome, Italy", duration_days: 10, total_budget: 5000, num_adults: 2, departure_date: [suggest], return_date: [suggest]

User: "Rome for 10 days with 5000€. Traveling from Copenhagen. 2 adults." (no dates specified)
-> origin: "Copenhagen", destination: "Rome, Italy", duration_days: 10, total_budget: 5000, num_adults: 2, departure_date: [suggest optimal like "2025-04-20"], return_date: [10 days later], date_flexibility: 7

User: "Relaxing beach vacation, budget around 3k, just me and my partner. Traveling from Copenhagen."
-> origin: "Copenhagen", destination: "Barcelona, Spain", travel_style: "relaxed", interests: ["beach"], total_budget: 3000, num_adults: 2, departure_date: [suggest], return_date: [suggest], duration_days: 7

User: "Beach for a week with 2000€. Traveling from Paris. 2 adults."
-> origin: "Paris", destination: "Lisbon, Portugal", interests: ["beach"], total_budget: 2000, num_adults: 2, duration_days: 7, departure_date: [suggest], return_date: [suggest]
"""),
            ("human", "{user_message}\n\nCurrent date: {current_date}")
        ])

    def _ensure_future_dates(self, intent: TravelIntent) -> TravelIntent:
        """
        Validates that dates are in the future. If not, moves them to next year.
        """
        today = datetime.now().date()
        min_future_date = today + timedelta(days=7)  # At least 1 week in the future

        if intent.departure_date and intent.departure_date < min_future_date:
            logger.warning(f"⚠️  Departure date {intent.departure_date} is in the past or too soon. Moving to next year.")

            # Calculate how many days into the past
            original_departure = intent.departure_date
            original_return = intent.return_date

            # Move to next year
            intent.departure_date = intent.departure_date.replace(year=intent.departure_date.year + 1)

            if intent.return_date:
                intent.return_date = intent.return_date.replace(year=intent.return_date.year + 1)

            logger.info(f"✅ Adjusted dates: {original_departure} -> {intent.departure_date}")

        return intent

    def _generate_destination_description(self, destination: str, user_message: str) -> str:
        """
        Generate a compelling description of why this destination was chosen for the user's needs.
        """
        try:
            prompt = f"""Based on the user's travel request, explain why {destination} is the perfect choice.

User's request: {user_message}
Chosen destination: {destination}

Write a compelling 2-3 sentence paragraph explaining why {destination} is ideal for what they're looking for.
Focus on what makes it special and how it matches their specific needs (interests, travel style, timing, etc.).
Be enthusiastic but authentic. Don't mention the budget or specific dates."""

            response = self.llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            logger.error(f"Error generating destination description: {e}")
            return f"{destination} offers a perfect blend of culture, experiences, and unforgettable moments for your journey."

    def _fetch_destination_image(self, destination: str) -> str:
        """
        Fetch a beautiful image URL from Unsplash for the destination.
        """
        try:
            # Extract city name (remove country if present)
            city = destination.split(',')[0].strip().lower()

            # Curated destination images from Unsplash (photo IDs)
            destination_images = {
                "barcelona": "https://images.unsplash.com/photo-1583422409516-2895a77efded?w=1600&h=900&fit=crop&q=80",
                "tokyo": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=1600&h=900&fit=crop&q=80",
                "paris": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=1600&h=900&fit=crop&q=80",
                "rome": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=1600&h=900&fit=crop&q=80",
                "london": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=1600&h=900&fit=crop&q=80",
                "new york": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=1600&h=900&fit=crop&q=80",
                "dubai": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=1600&h=900&fit=crop&q=80",
                "lisbon": "https://images.unsplash.com/photo-1585208798174-6cedd86e019a?w=1600&h=900&fit=crop&q=80",
                "madrid": "https://images.unsplash.com/photo-1539037116277-4db20889f2d4?w=1600&h=900&fit=crop&q=80",
                "amsterdam": "https://images.unsplash.com/photo-1512470876302-972faa2aa9a4?w=1600&h=900&fit=crop&q=80",
                "venice": "https://images.unsplash.com/photo-1514890547357-a9ee288728e0?w=1600&h=900&fit=crop&q=80",
                "prague": "https://images.unsplash.com/photo-1541849546-216549ae216d?w=1600&h=900&fit=crop&q=80",
                "athens": "https://images.unsplash.com/photo-1555993539-1732b0258235?w=1600&h=900&fit=crop&q=80",
                "santorini": "https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?w=1600&h=900&fit=crop&q=80",
                "bali": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=1600&h=900&fit=crop&q=80",
                "kyoto": "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=1600&h=900&fit=crop&q=80",
                "singapore": "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=1600&h=900&fit=crop&q=80",
                "hong kong": "https://images.unsplash.com/photo-1536599018102-9f803c140fc1?w=1600&h=900&fit=crop&q=80",
                "sydney": "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=1600&h=900&fit=crop&q=80",
                "istanbul": "https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?w=1600&h=900&fit=crop&q=80",
            }

            # Check if we have a curated image for this destination
            if city in destination_images:
                image_url = destination_images[city]
                logger.info(f"🖼️  Using curated image for {destination}")
            else:
                # Fallback to generic search-based URL
                city_param = city.replace(' ', '+')
                image_url = f"https://source.unsplash.com/1600x900/?{city_param},travel,city"
                logger.info(f"🖼️  Using search-based image for {destination}")

            return image_url

        except Exception as e:
            logger.error(f"Error fetching destination image: {e}")
            # Fallback to a high-quality generic travel image
            return "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=1600&h=900&fit=crop&q=80"

    def parse_intent(self, state: AgentState) -> AgentState:
        """
        Main agent function called by LangGraph.
        Extracts TravelIntent from user message.
        """
        try:
            # Get current date for date suggestions
            current_date = datetime.now().strftime("%Y-%m-%d")

            # Format the prompt with parser instructions
            formatted_prompt = self.prompt.format_messages(
                user_message=state.user_message,
                current_date=current_date,
                format_instructions=self.parser.get_format_instructions()
            )

            # Call LLM
            response = self.llm.invoke(formatted_prompt)

            # Parse into TravelIntent
            parsed_intent = self.parser.parse(response.content)

            # Ensure dates are in the future
            parsed_intent = self._ensure_future_dates(parsed_intent)

            # Generate destination description and image
            if parsed_intent.destination:
                parsed_intent.destination_description = self._generate_destination_description(
                    parsed_intent.destination,
                    state.user_message
                )
                parsed_intent.destination_image_url = self._fetch_destination_image(parsed_intent.destination)

            # Log parsed intent details
            logger.info(f"Parsed Intent - Origin: {parsed_intent.origin}, Destination: {parsed_intent.destination}")
            logger.info(f"Dates: {parsed_intent.departure_date} to {parsed_intent.return_date}")
            logger.info(f"Budget: {parsed_intent.total_budget}, Travelers: {parsed_intent.num_adults} adults, {parsed_intent.num_children} children")

            # Update state
            state.parsed_intent = parsed_intent
            state.agent_messages.append(
                f"Intent Parser: Understood your request - {parsed_intent.duration_days} days "
                f"to {parsed_intent.destination or 'flexible destination'} "
                f"for {parsed_intent.num_adults} adult(s)"
                + (f" and {parsed_intent.num_children} child(ren)" if parsed_intent.num_children > 0 else "")
            )
            state.current_step = "intent_parsed"

        except Exception as e:
            error_msg = f"Intent Parser Error: {str(e)}"
            state.errors.append(error_msg)
            state.agent_messages.append(error_msg)

        return state

    def validate_intent(self, intent: TravelIntent) -> Dict[str, Any]:
        """
        Validates parsed intent and returns missing critical fields.
        """
        missing_fields = []

        if not intent.destination:
            missing_fields.append("destination")
        if not intent.departure_date and not intent.duration_days:
            missing_fields.append("dates or duration")
        if not intent.total_budget:
            missing_fields.append("budget")

        return {
            "is_valid": len(missing_fields) == 0,
            "missing_fields": missing_fields
        }


# Standalone function for LangGraph node
def parse_intent_node(state: AgentState) -> AgentState:
    """LangGraph node wrapper for Intent Parser"""
    agent = IntentParserAgent()
    return agent.parse_intent(state)
