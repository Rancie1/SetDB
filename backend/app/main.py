"""
Main FastAPI application entry point.

This file creates the FastAPI app instance and includes all routers.
FastAPI automatically generates API documentation at /docs when you run the server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all API routers
from app.api import auth, users, sets, events, logs, reviews, ratings, lists, tracks, track_search, track_ratings, track_reviews, standalone_tracks

# Create FastAPI app instance
app = FastAPI(
    title="SetDB API",
    description="A Letterboxd-style app for DJ sets",
    version="1.0.0"
)

# Configure CORS (Cross-Origin Resource Sharing)
# This allows the frontend (running on a different port) to make requests to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React/Vite dev server ports
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Include all API routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(sets.router)
app.include_router(events.router)
app.include_router(logs.router)
app.include_router(reviews.router)
app.include_router(ratings.router)
app.include_router(lists.router)
app.include_router(tracks.router)
app.include_router(tracks.discover_router)
app.include_router(track_search.router)
app.include_router(track_ratings.router)
app.include_router(track_reviews.router)
app.include_router(standalone_tracks.router)

@app.get("/")
def read_root():
    """Health check endpoint - confirms the API is running"""
    return {"message": "SetDB API is running!"}

@app.get("/health")
def health_check():
    """Another health check endpoint"""
    return {"status": "healthy"}

