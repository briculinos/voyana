-- AI Travel Concierge Database Schema
-- PostgreSQL schema for user profiles, preferences, and trip history

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User taste profiles
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    preferred_styles JSONB DEFAULT '[]',
    budget_consciousness VARCHAR(50) DEFAULT 'moderate',
    accommodation_preferences JSONB DEFAULT '[]',
    interests JSONB DEFAULT '[]',
    dietary_restrictions JSONB DEFAULT '[]',
    mobility_requirements TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trip history
CREATE TABLE IF NOT EXISTS trips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    destination VARCHAR(255) NOT NULL,
    start_date DATE,
    end_date DATE,
    total_cost DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'EUR',
    num_travelers INTEGER,
    trip_data JSONB,  -- Full itinerary data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Feedback and preferences learned from user behavior
CREATE TABLE IF NOT EXISTS user_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    trip_id UUID REFERENCES trips(id) ON DELETE CASCADE,
    feedback_type VARCHAR(50),  -- 'liked', 'booked', 'rejected', 'explicit'
    item_type VARCHAR(50),  -- 'flight', 'hotel', 'activity', 'itinerary'
    item_data JSONB,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Saved itineraries (before booking)
CREATE TABLE IF NOT EXISTS saved_itineraries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    itinerary_data JSONB NOT NULL,
    notes TEXT,
    is_booked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_trips_user_id ON trips(user_id);
CREATE INDEX IF NOT EXISTS idx_trips_destination ON trips(destination);
CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON user_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_itineraries_user_id ON saved_itineraries(user_id);

-- For Phase 2: Vector embeddings for taste matching
-- Requires pgvector extension
-- CREATE EXTENSION IF NOT EXISTS vector;
--
-- CREATE TABLE IF NOT EXISTS destination_embeddings (
--     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--     destination VARCHAR(255) NOT NULL,
--     description TEXT,
--     embedding vector(1536),  -- OpenAI embedding dimension
--     metadata JSONB
-- );
--
-- CREATE INDEX ON destination_embeddings USING ivfflat (embedding vector_cosine_ops);
