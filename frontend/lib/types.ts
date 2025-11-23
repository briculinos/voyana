// TypeScript types matching backend Pydantic models

export interface FlightSegment {
  origin: string
  destination: string
  departure: string
  arrival: string
  carrier: string
  flight_number: string
  duration_minutes: number
  aircraft?: string
  booking_class: string
}

export interface FlightOption {
  outbound_segments: FlightSegment[]
  return_segments: FlightSegment[]
  total_price: number
  currency: string
  total_duration_minutes: number
  number_of_stops: number
  booking_link?: string
  source: string
}

export interface AccommodationOption {
  name: string
  type: string
  address: string
  city: string
  country: string
  price_per_night: number
  total_price: number
  currency: string
  rating?: number
  review_count?: number
  amenities: string[]
  room_type?: string
  check_in: string
  check_out: string
  latitude?: number
  longitude?: number
  distance_to_center_km?: number
  booking_link?: string
  source: string
}

export interface Activity {
  name: string
  description: string
  category: string
  duration_hours: number
  price_per_person: number
  currency: string
  location: string
  rating?: number
  booking_link?: string
  suitable_for_children: boolean
  min_age?: number
  physical_intensity: string
}

export interface DayPlan {
  day_number: number
  date: string
  location: string
  activities: Activity[]
  meals: any[]
  accommodation?: AccommodationOption
  notes?: string
  estimated_cost: number
}

export interface Itinerary {
  title: string
  summary: string
  style_tag: string
  flights: FlightOption
  accommodations: AccommodationOption[]
  daily_plans: DayPlan[]
  flight_cost: number
  accommodation_cost: number
  activities_cost: number
  estimated_food_cost: number
  total_cost: number
  currency: string
  why_this_option: string
  tradeoffs: string
  taste_score?: number
}

export interface TravelResponse {
  success: boolean
  itineraries: Itinerary[]
  agent_messages: string[]
  errors: string[]
  parsed_intent: any
  metadata: {
    num_flight_options: number
    num_hotel_options: number
    num_itineraries: number
  }
}

export interface AgentUpdate {
  type: 'agent_update' | 'complete' | 'error'
  agent?: string
  messages?: string
  current_step?: string
  errors?: string[]
  success?: boolean
  itineraries?: Itinerary[]
  parsed_intent?: any
  metadata?: any
  error?: string
}
