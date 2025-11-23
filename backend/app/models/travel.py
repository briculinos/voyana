"""
Pydantic models for travel data structures.
These models define the shape of data flowing through the agent system.
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator


class TravelerType(str, Enum):
    """Types of travelers in a group"""
    ADULT = "adult"
    CHILD = "child"
    INFANT = "infant"


class TravelStyle(str, Enum):
    """Travel style preferences"""
    RELAXED = "relaxed"
    BALANCED = "balanced"
    PACKED = "packed"
    ADVENTURE = "adventure"
    LUXURY = "luxury"
    BUDGET = "budget"


class Traveler(BaseModel):
    """Individual traveler information"""
    type: TravelerType
    age: Optional[int] = None
    name: Optional[str] = None


class TravelIntent(BaseModel):
    """
    Structured output from Intent Parser Agent.
    Represents the user's travel requirements extracted from natural language.
    """
    # Core requirements
    origin: Optional[str] = Field(None, description="Departure city/airport code")
    destination: Optional[str] = Field(None, description="Destination city or 'flexible' for suggestions")
    destination_description: Optional[str] = Field(None, description="Why this destination was chosen for the user's needs")
    destination_image_url: Optional[str] = Field(None, description="Unsplash image URL for the destination")
    departure_date: Optional[date] = Field(None, description="Preferred departure date")
    return_date: Optional[date] = Field(None, description="Preferred return date")
    duration_days: Optional[int] = Field(None, description="Trip duration in days")
    date_flexibility: int = Field(3, description="Days of flexibility (+/-)")

    # Travelers
    travelers: List[Traveler] = Field(default_factory=list)
    num_adults: int = Field(1, ge=1)
    num_children: int = Field(0, ge=0)
    num_infants: int = Field(0, ge=0)

    # Budget
    total_budget: Optional[float] = Field(None, description="Total budget in EUR")
    budget_flexibility: float = Field(0.1, description="Budget flexibility as percentage")
    budget_priorities: List[str] = Field(default_factory=lambda: ["balanced"])

    # Preferences
    travel_style: TravelStyle = TravelStyle.BALANCED
    accommodation_type: List[str] = Field(default_factory=lambda: ["hotel", "apartment"])
    must_haves: List[str] = Field(default_factory=list)
    must_not_haves: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)

    # Additional context
    special_occasions: List[str] = Field(default_factory=list)
    mobility_requirements: Optional[str] = None
    dietary_restrictions: List[str] = Field(default_factory=list)

    @validator('duration_days', always=True)
    def calculate_duration(cls, v, values):
        """Automatically calculate duration_days from dates if not provided"""
        if v is not None:
            return v  # Use provided value if present

        departure = values.get('departure_date')
        return_date = values.get('return_date')

        if departure and return_date:
            duration = (return_date - departure).days
            return duration if duration > 0 else 1  # At least 1 day

        return None


class FlightSegment(BaseModel):
    """Single flight segment"""
    origin: str
    destination: str
    departure: datetime
    arrival: datetime
    carrier: str
    flight_number: str
    duration_minutes: int
    aircraft: Optional[str] = None
    booking_class: str = "economy"


class FlightOption(BaseModel):
    """Complete flight option (can include connections)"""
    outbound_segments: List[FlightSegment]
    return_segments: List[FlightSegment]
    total_price: float
    currency: str = "EUR"
    total_duration_minutes: int
    number_of_stops: int
    booking_link: Optional[str] = None

    # Metadata
    source: str = Field(default="amadeus")
    last_updated: datetime = Field(default_factory=datetime.now)


class AccommodationOption(BaseModel):
    """Hotel or accommodation option"""
    name: str
    type: str  # hotel, apartment, resort, etc.
    address: str
    city: str
    country: str

    # Pricing
    price_per_night: float
    total_price: float
    currency: str = "EUR"

    # Details
    rating: Optional[float] = Field(None, ge=0, le=5)
    review_count: Optional[int] = None
    amenities: List[str] = Field(default_factory=list)
    room_type: Optional[str] = None
    check_in: date
    check_out: date

    # Location
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_to_center_km: Optional[float] = None

    # Booking
    booking_link: Optional[str] = None
    source: str = Field(default="booking.com")
    last_updated: datetime = Field(default_factory=datetime.now)


class Activity(BaseModel):
    """Activity or experience option"""
    name: str
    description: str
    category: str  # museum, tour, food, adventure, etc.
    duration_hours: float
    price_per_person: float
    currency: str = "EUR"
    location: str
    rating: Optional[float] = None
    booking_link: Optional[str] = None

    # Suitability
    suitable_for_children: bool = True
    min_age: Optional[int] = None
    physical_intensity: str = "low"  # low, medium, high


class DayPlan(BaseModel):
    """Single day in an itinerary"""
    day_number: int
    date: date
    location: str
    activities: List[Activity] = Field(default_factory=list)
    meals: List[Dict[str, Any]] = Field(default_factory=list)
    accommodation: Optional[AccommodationOption] = None
    notes: Optional[str] = None
    estimated_cost: float = 0.0


class Itinerary(BaseModel):
    """
    Complete travel itinerary produced by Synthesis Agent.
    One of 3 options presented to the user.
    """
    # Metadata
    title: str
    summary: str
    style_tag: str  # "Budget Explorer", "Balanced Family", "Luxury Escape"

    # Travel components
    flights: FlightOption
    accommodations: List[AccommodationOption]
    daily_plans: List[DayPlan]

    # Costs
    flight_cost: float
    accommodation_cost: float
    activities_cost: float
    estimated_food_cost: float
    total_cost: float
    currency: str = "EUR"

    # Reasoning
    why_this_option: str = Field(description="Explanation of why this itinerary matches user preferences")
    tradeoffs: str = Field(description="What this option prioritizes vs alternatives")

    # Taste alignment score (from Taste Profiler Agent)
    taste_score: Optional[float] = Field(None, ge=0, le=1)

    @validator("total_cost", always=True)
    def calculate_total(cls, v, values):
        """Auto-calculate total cost"""
        if v == 0 or v is None:
            return (
                values.get("flight_cost", 0)
                + values.get("accommodation_cost", 0)
                + values.get("activities_cost", 0)
                + values.get("estimated_food_cost", 0)
            )
        return v


class AgentState(BaseModel):
    """
    LangGraph state object.
    Passed between agents and updated at each step.
    """
    # Input
    user_message: str
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None

    # Intent parsing
    parsed_intent: Optional[TravelIntent] = None

    # Search results
    flight_options: List[FlightOption] = Field(default_factory=list)
    accommodation_options: List[AccommodationOption] = Field(default_factory=list)
    activity_options: List[Activity] = Field(default_factory=list)

    # User preferences (from database)
    user_taste_profile: Optional[Dict[str, Any]] = None
    past_trips: List[Dict[str, Any]] = Field(default_factory=list)

    # Final output
    itineraries: List[Itinerary] = Field(default_factory=list)

    # Agent communication
    agent_messages: List[str] = Field(default_factory=list)
    current_step: str = "start"
    errors: List[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True
