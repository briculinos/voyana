'use client'

import { useState } from 'react'
import ChatInterface from '@/components/ChatInterface'
import ItineraryDisplay from '@/components/ItineraryDisplay'
import { Itinerary } from '@/lib/types'

interface DestinationInfo {
  destination: string
  description: string
  imageUrl: string
}

export default function Home() {
  const [itineraries, setItineraries] = useState<Itinerary[]>([])
  const [loading, setLoading] = useState(false)
  const [destinationInfo, setDestinationInfo] = useState<DestinationInfo | null>(null)

  const handleItinerariesReceived = (newItineraries: Itinerary[]) => {
    setItineraries(newItineraries)
    setLoading(false)
  }

  const handleLoadingChange = (isLoading: boolean) => {
    setLoading(isLoading)
  }

  const handleDestinationReceived = (destination: DestinationInfo | null) => {
    setDestinationInfo(destination)
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-cyan-50">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <header className="mb-12 flex items-center justify-between bg-white rounded-2xl shadow-lg px-8 py-6 border border-gray-100">
          {/* Logo/Brand */}
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-cyan-600 rounded-xl flex items-center justify-center">
              <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
              Voyana
            </h1>
          </div>

          {/* Tagline */}
          <p className="text-lg text-gray-600 max-w-xl text-right hidden lg:block">
            Tell us what you're looking for, and our AI agents will craft the perfect trip just for you
          </p>
        </header>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Chat Interface and Destination Card */}
          <div>
            <div className="lg:sticky lg:top-8 space-y-6">
              <ChatInterface
                onItinerariesReceived={handleItinerariesReceived}
                onLoadingChange={handleLoadingChange}
                onDestinationReceived={handleDestinationReceived}
              />

              {/* Destination Info Card - Shown after intent parsed */}
              {!loading && destinationInfo && (
                <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                  <div className="relative h-64">
                    <img
                      src={destinationInfo.imageUrl}
                      alt={destinationInfo.destination}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.currentTarget.src = 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=1600&h=900&fit=crop'
                      }}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
                    <div className="absolute bottom-0 left-0 right-0 p-6">
                      <h3 className="text-3xl font-bold text-white mb-2">
                        {destinationInfo.destination}
                      </h3>
                    </div>
                  </div>
                  <div className="p-6">
                    <h4 className="text-lg font-semibold mb-2 flex items-center gap-2">
                      <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-sm font-medium">Why this destination</span>
                    </h4>
                    <p className="text-gray-700 leading-relaxed">
                      {destinationInfo.description}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Column - Itinerary Display */}
          <div className="space-y-6">
            {loading && (
              <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
                <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Our AI agents are planning your perfect trip...</p>
              </div>
            )}

            {!loading && itineraries.length > 0 && (
              <ItineraryDisplay itineraries={itineraries} />
            )}

            {!loading && itineraries.length === 0 && !destinationInfo && (
              <div className="bg-white rounded-2xl shadow-lg p-12 text-center">
                <div className="text-6xl mb-4">✈️</div>
                <h2 className="text-2xl font-semibold text-gray-800 mb-2">
                  Ready for Your Next Adventure?
                </h2>
                <p className="text-gray-600">
                  Share your travel dreams with our AI concierge, and we'll create personalized itineraries tailored just for you.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  )
}
