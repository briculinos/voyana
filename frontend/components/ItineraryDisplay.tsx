'use client'

import { useState } from 'react'
import { Itinerary } from '@/lib/types'

interface ItineraryDisplayProps {
  itineraries: Itinerary[]
}

export default function ItineraryDisplay({ itineraries }: ItineraryDisplayProps) {
  const [selectedIndex, setSelectedIndex] = useState(0)

  if (itineraries.length === 0) return null

  const selected = itineraries[selectedIndex]

  const formatCurrency = (amount: number, currency: string = 'EUR') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return `${hours}h ${mins}m`
  }

  const calculateTripDuration = (itinerary: Itinerary) => {
    // Calculate trip duration from flight dates
    const departureDate = new Date(itinerary.flights.outbound_segments[0].departure)
    const returnDate = new Date(itinerary.flights.return_segments[itinerary.flights.return_segments.length - 1].arrival)
    const durationMs = returnDate.getTime() - departureDate.getTime()
    const days = Math.ceil(durationMs / (1000 * 60 * 60 * 24))
    return days
  }

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="space-y-6">
      {/* Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {itineraries.map((itinerary, idx) => (
          <button
            key={idx}
            onClick={() => setSelectedIndex(idx)}
            className={`px-6 py-3 rounded-xl font-medium whitespace-nowrap transition-all ${
              selectedIndex === idx
                ? 'bg-blue-600 text-white shadow-lg scale-105'
                : 'bg-white text-gray-700 hover:bg-gray-50 shadow'
            }`}
          >
            <div className="text-xs mb-1">{itinerary.style_tag}</div>
            <div className="text-lg font-bold">
              {formatCurrency(itinerary.total_cost, itinerary.currency)}
            </div>
          </button>
        ))}
      </div>

      {/* Header Card */}
      <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
        <div className="bg-gradient-to-r from-blue-600 to-cyan-600 text-white p-8">
          <div className="text-sm font-semibold mb-2">{selected.style_tag}</div>
          <h2 className="text-3xl font-bold mb-3">{selected.title}</h2>
          <p className="text-blue-100 text-lg">{selected.summary}</p>
          <div className="mt-6 flex flex-wrap gap-4">
            <div className="bg-white/20 backdrop-blur rounded-lg px-4 py-2">
              <div className="text-xs text-blue-100">Total Cost</div>
              <div className="text-2xl font-bold">
                {formatCurrency(selected.total_cost, selected.currency)}
              </div>
            </div>
            <div className="bg-white/20 backdrop-blur rounded-lg px-4 py-2">
              <div className="text-xs text-blue-100">Duration</div>
              <div className="text-2xl font-bold">{calculateTripDuration(selected)} days</div>
            </div>
          </div>
        </div>
        {/* Why & Tradeoffs inside header card */}
        <div className="p-6 space-y-4 border-t">
          <div>
            <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
              <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-sm font-medium">Why this option</span>
            </h3>
            <p className="text-gray-700">{selected.why_this_option}</p>
          </div>
          <div className="border-t pt-4">
            <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
              <span className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm font-medium">Tradeoffs</span>
            </h3>
            <p className="text-gray-600 text-sm">{selected.tradeoffs}</p>
          </div>
        </div>
      </div>

      {/* Flights Card */}
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-sm font-medium">Flights</span>
        </h3>
        <div className="space-y-4">
          {/* Outbound */}
          <div className="bg-gray-50 rounded-xl p-4">
            <div className="text-sm font-semibold text-gray-500 mb-3">Outbound</div>
            {selected.flights.outbound_segments.map((segment, idx) => (
              <div key={idx} className="flex items-center justify-between mb-2">
                <div>
                  <div className="font-medium text-gray-900">
                    {segment.origin} → {segment.destination}
                  </div>
                  <div className="text-sm text-gray-500">
                    {segment.carrier} {segment.flight_number}
                  </div>
                </div>
                <div className="text-right text-sm">
                  <div className="text-gray-700">{formatDateTime(segment.departure)}</div>
                  <div className="text-gray-500">{formatDuration(segment.duration_minutes)}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Return */}
          <div className="bg-gray-50 rounded-xl p-4">
            <div className="text-sm font-semibold text-gray-500 mb-3">Return</div>
            {selected.flights.return_segments.map((segment, idx) => (
              <div key={idx} className="flex items-center justify-between mb-2">
                <div>
                  <div className="font-medium text-gray-900">
                    {segment.origin} → {segment.destination}
                  </div>
                  <div className="text-sm text-gray-500">
                    {segment.carrier} {segment.flight_number}
                  </div>
                </div>
                <div className="text-right text-sm">
                  <div className="text-gray-700">{formatDateTime(segment.departure)}</div>
                  <div className="text-gray-500">{formatDuration(segment.duration_minutes)}</div>
                </div>
              </div>
            ))}
          </div>

          <div className="text-right">
            <span className="text-sm text-gray-500">Total: </span>
            <span className="text-xl font-bold text-blue-600">
              {formatCurrency(selected.flight_cost, selected.currency)}
            </span>
          </div>
        </div>
      </div>

      {/* Hotels Card */}
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-sm font-medium">Hotels</span>
        </h3>
        <div className="space-y-3">
          {selected.accommodations.map((hotel, idx) => (
            <div key={idx} className="bg-gray-50 rounded-xl p-4 border-l-4 border-blue-500">
              <div className="flex justify-between items-start mb-3">
                <div className="flex-1">
                  <h4 className="font-bold text-xl text-gray-900 mb-1">{hotel.name}</h4>
                  <p className="text-sm text-gray-600 mb-2">{hotel.address}, {hotel.city}</p>

                  {/* Rating prominently displayed */}
                  {hotel.rating && (
                    <div className="flex items-center gap-2 mb-2">
                      <div className="bg-blue-600 text-white px-3 py-1 rounded-lg font-bold text-lg">
                        {hotel.rating.toFixed(1)}
                      </div>
                      {hotel.review_count && (
                        <span className="text-sm text-gray-600">Based on {hotel.review_count.toLocaleString()} reviews</span>
                      )}
                    </div>
                  )}

                  {/* Why this hotel was chosen */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-3">
                    <div className="text-xs font-semibold text-blue-900 mb-1">Why this hotel:</div>
                    <div className="text-sm text-gray-700">
                      {selected.style_tag === 'Budget' &&
                        `Best value - Great ${hotel.rating ? hotel.rating.toFixed(1) + '/10' : ''} rating at an affordable €${hotel.price_per_night}/night`}
                      {selected.style_tag === 'Balanced Family' &&
                        `Perfect balance - Highly rated (${hotel.rating ? hotel.rating.toFixed(1) + '/10' : 'excellent'}) with family-friendly amenities and central location`}
                      {selected.style_tag === 'Luxury' &&
                        `Premium choice - Top-rated (${hotel.rating ? hotel.rating.toFixed(1) + '/10' : 'exceptional'}) with excellent amenities and prime location`}
                    </div>
                  </div>
                </div>

                <div className="text-right ml-4">
                  <div className="text-2xl font-bold text-blue-600">
                    {formatCurrency(hotel.total_price, hotel.currency)}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    {formatCurrency(hotel.price_per_night, hotel.currency)}/night
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    for {Math.round(hotel.total_price / hotel.price_per_night)} nights
                  </div>
                </div>
              </div>

              {hotel.amenities.length > 0 && (
                <div className="border-t border-gray-200 pt-3 mt-3">
                  <div className="text-xs font-semibold text-gray-700 mb-2">Amenities:</div>
                  <div className="flex flex-wrap gap-2">
                    {hotel.amenities.slice(0, 8).map((amenity, i) => (
                      <span key={i} className="text-xs bg-white border border-blue-200 text-blue-700 px-3 py-1 rounded-full">
                        {amenity}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Daily Plans Card */}
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-sm font-medium">Daily Plans</span>
        </h3>
        {selected.daily_plans.length === 0 ? (
          <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl p-8 border-2 border-blue-200">
            <h4 className="text-xl font-semibold mb-4 text-gray-800">What are you interested in?</h4>
            <p className="text-gray-600 mb-6">Select your interests to get personalized daily activity recommendations</p>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
              <button className="bg-white hover:bg-blue-50 border-2 border-gray-200 hover:border-blue-500 rounded-lg p-4 text-left transition-all">
                <div className="font-medium text-gray-800">Cultural Sites</div>
                <div className="text-xs text-gray-500">Museums, monuments, history</div>
              </button>
              <button className="bg-white hover:bg-blue-50 border-2 border-gray-200 hover:border-blue-500 rounded-lg p-4 text-left transition-all">
                <div className="font-medium text-gray-800">Food & Dining</div>
                <div className="text-xs text-gray-500">Local cuisine, restaurants, markets</div>
              </button>
              <button className="bg-white hover:bg-blue-50 border-2 border-gray-200 hover:border-blue-500 rounded-lg p-4 text-left transition-all">
                <div className="font-medium text-gray-800">Nature & Outdoors</div>
                <div className="text-xs text-gray-500">Parks, hiking, scenic views</div>
              </button>
              <button className="bg-white hover:bg-blue-50 border-2 border-gray-200 hover:border-blue-500 rounded-lg p-4 text-left transition-all">
                <div className="font-medium text-gray-800">Shopping</div>
                <div className="text-xs text-gray-500">Markets, boutiques, local crafts</div>
              </button>
              <button className="bg-white hover:bg-blue-50 border-2 border-gray-200 hover:border-blue-500 rounded-lg p-4 text-left transition-all">
                <div className="font-medium text-gray-800">Entertainment</div>
                <div className="text-xs text-gray-500">Shows, nightlife, performances</div>
              </button>
              <button className="bg-white hover:bg-blue-50 border-2 border-gray-200 hover:border-blue-500 rounded-lg p-4 text-left transition-all">
                <div className="font-medium text-gray-800">Relaxation</div>
                <div className="text-xs text-gray-500">Spas, beaches, leisure</div>
              </button>
            </div>

            <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors">
              Generate My Daily Plans
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {selected.daily_plans.map((day, idx) => (
              <div key={idx} className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold">
                    Day {day.day_number} - {day.location}
                  </h4>
                  <span className="text-sm text-gray-500">
                    {new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </span>
                </div>
                {day.activities.map((activity, i) => (
                  <div key={i} className="ml-4 mb-2">
                    <div className="font-medium text-sm">{activity.name}</div>
                    <div className="text-xs text-gray-600">{activity.description}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {activity.duration_hours}h · {formatCurrency(activity.price_per_person * (selected.daily_plans[0].activities.length || 1))}
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Cost Breakdown Card */}
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-sm font-medium">Cost Breakdown</span>
        </h3>
        <div className="bg-gray-50 rounded-xl p-4 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-700">Flights</span>
            <span className="font-medium text-gray-900">{formatCurrency(selected.flight_cost)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-700">Accommodations</span>
            <span className="font-medium text-gray-900">{formatCurrency(selected.accommodation_cost)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-700">Activities</span>
            <span className="font-medium text-gray-900">{formatCurrency(selected.activities_cost)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-700">Estimated Food</span>
            <span className="font-medium text-gray-900">{formatCurrency(selected.estimated_food_cost)}</span>
          </div>
          <div className="border-t pt-2 mt-2 flex justify-between font-bold text-lg">
            <span className="text-gray-900">Total</span>
            <span className="text-blue-600">{formatCurrency(selected.total_cost)}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
