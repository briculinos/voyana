'use client'

import { useState, useRef, useEffect } from 'react'
import { Itinerary, AgentUpdate } from '@/lib/types'

interface DestinationInfo {
  destination: string
  description: string
  imageUrl: string
}

interface ChatInterfaceProps {
  onItinerariesReceived: (itineraries: Itinerary[]) => void
  onLoadingChange: (loading: boolean) => void
  onDestinationReceived: (destination: DestinationInfo | null) => void
}

interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
}

export default function ChatInterface({ onItinerariesReceived, onLoadingChange, onDestinationReceived }: ChatInterfaceProps) {
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [isProcessing, setIsProcessing] = useState(false)

  // Form fields
  const [origin, setOrigin] = useState('')
  const [numAdults, setNumAdults] = useState(2)
  const [numChildren, setNumChildren] = useState(0)
  const [childAges, setChildAges] = useState<number[]>([])

  const messagesEndRef = useRef<HTMLDivElement>(null)

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Update child ages array when number of children changes
  useEffect(() => {
    if (numChildren > childAges.length) {
      // Add more ages
      setChildAges([...childAges, ...Array(numChildren - childAges.length).fill(5)])
    } else if (numChildren < childAges.length) {
      // Remove extra ages
      setChildAges(childAges.slice(0, numChildren))
    }
  }, [numChildren])

  const addMessage = (role: Message['role'], content: string) => {
    setMessages(prev => [...prev, { role, content, timestamp: new Date() }])
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim() || isProcessing) return

    // Build enhanced message with structured data
    let enhancedMessage = message.trim()

    if (origin) {
      enhancedMessage += ` Traveling from ${origin}.`
    }

    enhancedMessage += ` ${numAdults} adult${numAdults !== 1 ? 's' : ''}`

    if (numChildren > 0) {
      enhancedMessage += ` and ${numChildren} child${numChildren !== 1 ? 'ren' : ''}`
      if (childAges.length > 0) {
        enhancedMessage += ` aged ${childAges.join(', ')}`
      }
    }
    enhancedMessage += '.'

    setMessage('')
    setIsProcessing(true)
    onLoadingChange(true)

    // Add user message
    addMessage('user', enhancedMessage)

    try {
      // Use streaming endpoint
      const response = await fetch(`${API_URL}/api/plan/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: enhancedMessage,
          user_id: 'demo_user',
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No reader available')

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6)) as AgentUpdate

            if (data.type === 'agent_update' && data.messages) {
              addMessage('system', data.messages)
            } else if (data.type === 'complete') {
              // Extract destination info from parsed_intent
              if (data.parsed_intent?.destination && data.parsed_intent?.destination_description) {
                onDestinationReceived({
                  destination: data.parsed_intent.destination,
                  description: data.parsed_intent.destination_description,
                  imageUrl: data.parsed_intent.destination_image_url || 'https://source.unsplash.com/1600x900/?travel'
                })
              }

              if (data.itineraries && data.itineraries.length > 0) {
                addMessage('assistant', `I've created ${data.itineraries.length} personalized itineraries for you! Check them out on the right.`)
                onItinerariesReceived(data.itineraries)
              } else {
                addMessage('assistant', "I couldn't find suitable options for your request. Please try adjusting your requirements.")
              }
            } else if (data.type === 'error') {
              addMessage('assistant', `Sorry, I encountered an error: ${data.error}`)
            }
          }
        }
      }
    } catch (error) {
      console.error('Error:', error)
      addMessage('assistant', 'Sorry, I encountered an error processing your request. Please try again.')
    } finally {
      setIsProcessing(false)
      onLoadingChange(false)
    }
  }

  const updateChildAge = (index: number, age: number) => {
    const newAges = [...childAges]
    newAges[index] = age
    setChildAges(newAges)
  }

  const examplePrompts = [
    "Visit Rome, Italy for 10 days in May with 5000€. We love museums and good food.",
    "Relaxing beach vacation for 7 days, around 3000€",
    "Adventure trip to Japan in fall, flexible dates, love hiking and food"
  ]

  return (
    <div className="bg-white rounded-2xl shadow-xl flex flex-col h-[700px]">
      {/* Chat Header */}
      <div className="bg-gradient-to-r from-blue-600 to-cyan-600 text-white p-6 rounded-t-2xl">
        <h2 className="text-2xl font-bold mb-1">Tell Us Your Dream Trip</h2>
        <p className="text-blue-100 text-sm">Share your details and preferences</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="space-y-3">
            <p className="text-gray-600 text-sm font-medium">Try one of these examples:</p>
            {examplePrompts.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => setMessage(prompt)}
                className="w-full text-left p-3 rounded-lg bg-blue-50 hover:bg-blue-100 text-sm text-gray-700 transition-colors"
              >
                {prompt}
              </button>
            ))}
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : msg.role === 'system'
                  ? 'bg-gray-100 text-gray-700 text-sm'
                  : 'bg-gray-200 text-gray-800'
              }`}
            >
              {msg.role === 'system' && (
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                  <span className="text-xs font-semibold text-gray-500">Agent</span>
                </div>
              )}
              <p className="whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="p-6 border-t bg-gray-50 rounded-b-2xl">
        {/* Structured Fields */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          {/* Origin */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Traveling from <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={origin}
              onChange={(e) => setOrigin(e.target.value)}
              placeholder="e.g., Paris, New York"
              required
              disabled={isProcessing}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 text-gray-900 placeholder-gray-400"
            />
            {!origin && (
              <p className="text-xs text-red-500 mt-1">Required: Please enter your departure city</p>
            )}
          </div>

          {/* Adults */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Adults
            </label>
            <select
              value={numAdults}
              onChange={(e) => setNumAdults(parseInt(e.target.value))}
              disabled={isProcessing}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 text-gray-900"
            >
              {[1, 2, 3, 4, 5, 6].map(num => (
                <option key={num} value={num}>{num}</option>
              ))}
            </select>
          </div>

          {/* Children */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Children
            </label>
            <select
              value={numChildren}
              onChange={(e) => setNumChildren(parseInt(e.target.value))}
              disabled={isProcessing}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 text-gray-900"
            >
              {[0, 1, 2, 3, 4, 5].map(num => (
                <option key={num} value={num}>{num}</option>
              ))}
            </select>
          </div>

          {/* Child Ages */}
          {numChildren > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Children&apos;s Ages
              </label>
              <div className="flex gap-2">
                {childAges.map((age, idx) => (
                  <input
                    key={idx}
                    type="number"
                    min="0"
                    max="17"
                    value={age}
                    onChange={(e) => updateChildAge(idx, parseInt(e.target.value) || 0)}
                    disabled={isProcessing}
                    placeholder={`Child ${idx + 1}`}
                    className="w-16 px-2 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 text-center text-gray-900 placeholder-gray-400"
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Message Input */}
        <div className="flex gap-3">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Describe your trip: destination, dates, budget, preferences..."
            disabled={isProcessing}
            className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed text-gray-900 placeholder-gray-400"
          />
          <button
            type="submit"
            disabled={isProcessing || !message.trim() || !origin.trim()}
            className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
            title={!origin.trim() ? 'Please enter your departure city' : ''}
          >
            {isProcessing ? 'Planning...' : 'Send'}
          </button>
        </div>
      </form>
    </div>
  )
}
