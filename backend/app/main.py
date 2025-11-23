"""
FastAPI Application
Main entry point for the Voyana API.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json

from app.agents.workflow import workflow
from app.utils.config import settings
from app.utils.auth import verify_google_token, create_access_token, verify_token

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    logger.info("Starting Voyana API")
    yield
    logger.info("Shutting down Voyana API")


# Create FastAPI app
app = FastAPI(
    title="Voyana API",
    description="Multi-agent AI system for personalized travel planning",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API
class TravelRequest(BaseModel):
    """Request model for travel planning"""
    message: str
    user_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "message": "I want to visit Italy for 10 days in May with 5000€, we have two kids aged 5 and 8",
                "user_id": "user123"
            }
        }


class TravelResponse(BaseModel):
    """Response model for travel planning"""
    success: bool
    itineraries: list
    agent_messages: list
    errors: list
    parsed_intent: Optional[dict]
    metadata: dict


class GoogleAuthRequest(BaseModel):
    """Request model for Google OAuth"""
    token: str

    class Config:
        json_schema_extra = {
            "example": {
                "token": "google_oauth_token_here"
            }
        }


class AuthResponse(BaseModel):
    """Response model for authentication"""
    access_token: str
    token_type: str
    user: dict


# Auth dependency
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Dependency to get current user from JWT token"""
    if not authorization:
        return None

    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            return None

        payload = verify_token(token)
        if not payload:
            return None

        return payload

    except Exception:
        return None


# Routes
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Voyana",
        "status": "running",
        "version": "0.1.0"
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "agents": [
            "intent_parser",
            "search_orchestrator",
            "taste_profiler",
            "synthesis_agent"
        ],
        "features": {
            "flight_search": True,
            "hotel_search": True,
            "personalization": True,
            "streaming": True,
            "authentication": True
        }
    }


@app.post("/api/auth/google", response_model=AuthResponse)
async def google_auth(request: GoogleAuthRequest):
    """
    Authenticate with Google OAuth token.
    Frontend sends Google ID token, backend verifies it and returns JWT.
    """
    try:
        # Verify Google token
        user_info = await verify_google_token(request.token)
        if not user_info:
            raise HTTPException(status_code=401, detail="Invalid Google token")

        # Check email whitelist
        if settings.allowed_emails:
            user_email = user_info['email'].lower()
            if user_email not in settings.allowed_emails:
                logger.warning(f"Access denied for non-whitelisted email: {user_email}")
                raise HTTPException(
                    status_code=403,
                    detail="Access denied. Your email is not authorized to use this application."
                )

        logger.info(f"User authenticated: {user_info['email']}")

        # Create JWT token
        access_token = create_access_token(
            data={
                "sub": user_info['google_id'],
                "email": user_info['email'],
                "name": user_info['name'],
                "picture": user_info['picture']
            }
        )

        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "email": user_info['email'],
                "name": user_info['name'],
                "picture": user_info['picture']
            }
        )

    except Exception as e:
        logger.error(f"Authentication error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return {
        "email": current_user.get("email"),
        "name": current_user.get("name"),
        "picture": current_user.get("picture")
    }


@app.post("/api/plan", response_model=TravelResponse)
async def plan_trip(request: TravelRequest):
    """
    Main endpoint for travel planning.
    Processes natural language request and returns 3 complete itineraries.
    """
    try:
        logger.info(f"Received travel request from user: {request.user_id}")
        logger.info(f"Message: {request.message}")

        # Run workflow
        result = await workflow.run(
            user_message=request.message,
            user_id=request.user_id
        )

        return TravelResponse(**result)

    except Exception as e:
        logger.error(f"Travel planning error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/plan/stream")
async def plan_trip_stream(request: TravelRequest):
    """
    Streaming endpoint for travel planning.
    Returns Server-Sent Events with real-time agent updates.
    """
    async def event_generator():
        """Generate SSE events"""
        try:
            async for update in workflow.run_with_streaming(
                user_message=request.message,
                user_id=request.user_id
            ):
                # Format as SSE
                event_data = json.dumps(update)
                yield f"data: {event_data}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            error_event = json.dumps({"type": "error", "error": str(e)})
            yield f"data: {error_event}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/api/destinations")
async def get_popular_destinations():
    """
    Get list of popular destinations.
    Useful for autocomplete in frontend.
    """
    destinations = [
        {"name": "Paris", "country": "France", "code": "PAR"},
        {"name": "Rome", "country": "Italy", "code": "ROM"},
        {"name": "Barcelona", "country": "Spain", "code": "BCN"},
        {"name": "London", "country": "United Kingdom", "code": "LON"},
        {"name": "Amsterdam", "country": "Netherlands", "code": "AMS"},
        {"name": "Tokyo", "country": "Japan", "code": "TYO"},
        {"name": "New York", "country": "USA", "code": "NYC"},
        {"name": "Dubai", "country": "UAE", "code": "DXB"},
        {"name": "Bali", "country": "Indonesia", "code": "DPS"},
        {"name": "Lisbon", "country": "Portugal", "code": "LIS"},
    ]
    return {"destinations": destinations}


# For development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
