# Deckd (SetDB)

A Letterboxd-style web application for tracking, rating, and discovering DJ sets. Built for music enthusiasts who want to log sets they've listened to on YouTube and SoundCloud, or experienced live at festivals and clubs.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [API Architecture](#api-architecture)
- [Frontend Architecture](#frontend-architecture)
- [Key Features](#key-features)
- [Getting Started](#getting-started)
- [Development](#development)
- [External Integrations](#external-integrations)

## Overview

Deckd is a full-stack web application that allows users to:

- **Import DJ sets** from YouTube and SoundCloud
- **Log sets** they've listened to or seen live
- **Rate sets** with half-star precision (0.5 to 5.0 stars)
- **Write reviews** to share thoughts and experiences
- **Create lists** to organize favorite sets
- **Follow other users** (friends) to discover new music
- **Tag tracks** played in sets with timestamps
- **Confirm track tags** to verify accuracy (works for both manually tagged and linked tracks)
- **Search and discover tracks** from SoundCloud and Spotify
- **Rate and review tracks** independently of sets
- **Display top 5 tracks** on profile pages
- **Link tracks to multiple sets** from track detail pages
- **Create and manage events** (live shows, festivals)
- **Display top 5 sets** on profile pages
- **Search for friends** and build a social network

The application separates **Sets** (recordings/listenings) from **Events** (live shows), allowing users to track both independently while linking them when appropriate.

## Architecture

### High-Level Overview

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   React Frontend │  ──────▶│  FastAPI Backend │  ──────▶│  PostgreSQL DB  │
│   (Port 5173)    │  HTTP   │   (Port 8000)    │  SQL    │   (Port 5432)   │
└─────────────────┘         └─────────────────┘         └─────────────────┘
         │                           │
         │                           │
         ▼                           ▼
   ┌──────────┐              ┌──────────────┐
   │ Zustand  │              │  External    │
   │  Store   │              │    APIs      │
   └──────────┘              │ (YouTube/SC) │
                             └──────────────┘
```

### Communication Flow

1. **Frontend → Backend**: React components make HTTP requests via Axios to FastAPI endpoints
2. **Backend → Database**: FastAPI uses SQLAlchemy (async) to interact with PostgreSQL
3. **Backend → External APIs**: Services fetch data from YouTube Data API and SoundCloud API
4. **State Management**: Zustand stores manage client-side state (auth, sets, UI)
5. **Authentication**: JWT tokens stored in localStorage, sent via Authorization headers

## Tech Stack

### Backend

- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL with asyncpg driver
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Authentication**: JWT (python-jose), bcrypt for password hashing
- **Validation**: Pydantic 2.5
- **HTTP Client**: httpx (for external API calls)
- **Server**: Uvicorn

### Frontend

- **Framework**: React 19.2
- **Build Tool**: Vite 7.2
- **Routing**: React Router DOM 7.11
- **State Management**: Zustand 5.0
- **HTTP Client**: Axios 1.13
- **Forms**: React Hook Form 7.70
- **Styling**: Tailwind CSS 3.4
- **Language**: JavaScript (ES6+)

### Database

- **RDBMS**: PostgreSQL
- **Connection**: Async PostgreSQL (asyncpg)
- **ORM**: SQLAlchemy 2.0 with async support

## Project Structure

```
Deckd/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI app initialization, CORS, router registration
│   │   ├── config.py          # Settings (Pydantic Settings) - env vars
│   │   ├── database.py        # SQLAlchemy async engine, session factory
│   │   ├── auth.py            # JWT auth, password hashing, user dependencies
│   │   ├── models.py          # SQLAlchemy ORM models (13 models)
│   │   ├── schemas.py         # Pydantic schemas for validation
│   │   ├── core/
│   │   │   └── exceptions.py  # Custom exception classes
│   │   ├── api/               # API route handlers
│   │   │   ├── auth.py        # Registration, login, OAuth
│   │   │   ├── users.py       # User profiles, search, friends, stats
│   │   │   ├── sets.py        # Set CRUD, import, search, filtering
│   │   │   ├── events.py      # Event CRUD, linking sets, confirmations
│   │   │   ├── logs.py        # Log sets, top sets, user logs
│   │   │   ├── reviews.py     # Review CRUD, set reviews
│   │   │   ├── ratings.py     # Rating CRUD, stats
│   │   │   ├── lists.py       # List CRUD, list items
│   │   │   ├── tracks.py      # Track tags, confirmations, discovery
│   │   │   ├── track_search.py # SoundCloud & Spotify track search, URL resolution
│   │   │   ├── standalone_tracks.py # Independent track CRUD, linking to sets
│   │   │   ├── track_ratings.py # Track ratings
│   │   │   └── track_reviews.py # Track reviews
│   │   └── services/          # External API integrations
│   │       ├── set_importer.py    # Unified import interface
│   │       ├── youtube.py         # YouTube Data API v3
│   │       ├── soundcloud.py      # SoundCloud API v2
│   │       ├── soundcloud_oauth.py # SoundCloud OAuth flow
│   │       ├── soundcloud_search.py # SoundCloud track search
│   │       └── spotify_search.py # Spotify track search
│   ├── alembic/               # Database migrations
│   │   ├── versions/          # Migration files
│   │   └── env.py             # Alembic environment config
│   ├── alembic.ini            # Alembic configuration
│   ├── requirements.txt       # Python dependencies
│   └── README.md              # Backend setup guide
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── App.jsx            # Main app, routing configuration
│   │   ├── main.jsx           # React entry point
│   │   ├── components/        # Reusable UI components
│   │   │   ├── auth/          # LoginForm, RegisterForm, ProtectedRoute
│   │   │   ├── layout/        # Header, Footer, Layout wrapper
│   │   │   ├── sets/          # SetCard, SetList, SetImportForm, TrackTag, TrackTagForm
│   │   │   ├── tracks/        # SoundCloudSearch (track search component)
│   │   │   ├── events/        # CreateEventForm, LiveEventForm
│   │   │   ├── reviews/       # ReviewCard, ReviewForm, RatingDisplay
│   │   │   └── users/         # UserProfile, UserStats, TopSets, TopTracks
│   │   ├── pages/             # Page components (routes)
│   │   │   ├── HomePage.jsx
│   │   │   ├── DiscoverPage.jsx      # Sets discovery/browsing (route: /sets)
│   │   │   ├── TracksDiscoverPage.jsx # Tracks discovery/browsing (route: /tracks)
│   │   │   ├── SetDetailsPage.jsx    # Individual set view
│   │   │   ├── TrackDetailsPage.jsx  # Individual track view with ratings, reviews, linking
│   │   │   ├── EventsPage.jsx        # Events listing
│   │   │   ├── EventDetailsPage.jsx
│   │   │   ├── CreateEventPage.jsx
│   │   │   ├── UserProfilePage.jsx
│   │   │   ├── FriendsPage.jsx       # Friends listing
│   │   │   ├── SearchUsersPage.jsx   # Friend search
│   │   │   ├── ManageProfilePage.jsx # Profile editing
│   │   │   ├── LoginPage.jsx
│   │   │   ├── RegisterPage.jsx
│   │   │   └── SoundCloudCallbackPage.jsx
│   │   ├── services/          # API service functions
│   │   │   ├── api.js         # Axios instance with interceptors
│   │   │   ├── authService.js
│   │   │   ├── setsService.js
│   │   │   ├── eventsService.js
│   │   │   ├── usersService.js
│   │   │   ├── logsService.js
│   │   │   ├── reviewsService.js
│   │   │   ├── ratingsService.js
│   │   │   ├── tracksService.js      # Set-specific track tags
│   │   │   ├── standaloneTracksService.js # Independent track operations
│   │   │   ├── trackRatingsService.js # Track ratings
│   │   │   └── trackReviewsService.js # Track reviews
│   │   ├── store/             # Zustand state stores
│   │   │   ├── authStore.js   # User auth state, login/logout
│   │   │   ├── setsStore.js   # Sets state, filtering
│   │   │   └── uiStore.js     # UI state (modals, etc.)
│   │   └── utils/
│   │       └── constants.js   # App constants (API_URL, APP_NAME)
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── README.md
│
├── guides/                     # Documentation guides
│   ├── ALEMBIC_EXPLAINED.md
│   ├── FRONTEND_ARCHITECTURE.md
│   ├── IMPORT_SET_GUIDE.md
│   ├── POSTGRES_CONNECTION.md
│   ├── SOUNDCLOUD_API_SETUP.md
│   ├── SOUNDCLOUD_OAUTH_SETUP.md
│   └── SOUNDCLOUD_OAUTH_TROUBLESHOOTING.md
│
├── start.sh                    # Convenience script to start both servers
└── README.md                   # This file
```

## Database Schema

### Core Models

#### User
- **Purpose**: User accounts and profiles
- **Key Fields**: `username`, `email`, `hashed_password`, `display_name`, `bio`, `avatar_url`
- **OAuth**: SoundCloud OAuth fields (`soundcloud_user_id`, `soundcloud_access_token`, `soundcloud_refresh_token`)
- **Relationships**: 
  - One-to-many: `reviews`, `ratings`, `logs`, `created_sets`, `created_events`, `lists`
  - Many-to-many: `following` (via Follow), `followers` (via Follow)

#### DJSet
- **Purpose**: DJ sets from all sources (YouTube, SoundCloud, Live)
- **Key Fields**: `title`, `dj_name`, `source_type` (enum), `source_id`, `source_url`, `thumbnail_url`, `duration_minutes`
- **Source Types**: `YOUTUBE`, `SOUNDCLOUD`, `LIVE`
- **Relationships**:
  - Many-to-one: `created_by` (User)
  - One-to-many: `reviews`, `ratings`, `logs`, `track_tags`, `list_items`
  - Many-to-many: `events` (via EventSet)

#### Event
- **Purpose**: Live events (festivals, club nights, etc.) - separate from sets
- **Key Fields**: `title`, `dj_name`, `event_name`, `event_date`, `duration_days`, `venue_location`, `is_verified`, `confirmation_count`
- **Relationships**:
  - Many-to-one: `created_by` (User)
  - Many-to-many: `linked_sets` (via EventSet)
  - One-to-many: `confirmations` (EventConfirmation)

#### UserSetLog
- **Purpose**: Tracks when users log/view sets (like Letterboxd's diary)
- **Key Fields**: `user_id`, `set_id`, `watched_date`, `is_reviewed`, `is_top_set`, `top_set_order` (1-5)
- **Top Sets**: Users can mark up to 5 sets as their favorites with ordering
- **Unique Constraint**: One log per user per set

#### Rating
- **Purpose**: User ratings (0.5 to 5.0 stars, half-star increments)
- **Key Fields**: `user_id`, `set_id`, `rating` (float)
- **Unique Constraint**: One rating per user per set

#### Review
- **Purpose**: User-written reviews for sets
- **Key Fields**: `user_id`, `set_id`, `content`, `contains_spoilers`, `is_public`
- **Unique Constraint**: One review per user per set

#### Track
- **Purpose**: Independent track entity that can exist across multiple sets
- **Key Fields**: `track_name`, `artist_name`, `soundcloud_url`, `soundcloud_track_id`, `spotify_url`, `spotify_track_id`, `thumbnail_url`, `duration_ms`
- **Relationships**: 
  - Many-to-many: `sets` (via TrackSetLink)
  - One-to-many: `ratings` (TrackRating), `reviews` (TrackReview), `user_top_tracks` (UserTopTrack)

#### SetTrack
- **Purpose**: Track tags - manually tagged songs played in sets (legacy/manual tagging)
- **Key Fields**: `set_id`, `added_by_id`, `track_name`, `artist_name`, `soundcloud_url`, `timestamp_minutes` (MM:SS format stored as decimal)
- **Relationships**: One-to-many `confirmations` (TrackConfirmation)

#### TrackSetLink
- **Purpose**: Links independent Track entities to sets (many-to-many)
- **Key Fields**: `track_id`, `set_id`, `added_by_id`, `position`, `timestamp_minutes`
- **Relationships**: Many-to-one `track` (Track), `set` (DJSet)
- **Unique Constraint**: One link per track per set

#### TrackConfirmation
- **Purpose**: Users can confirm/deny if a track tag is correct
- **Key Fields**: `track_id` (for SetTrack), `track_set_link_id` (for TrackSetLink), `user_id`, `is_confirmed` (bool)
- **Supports**: Both SetTrack (manually tagged) and TrackSetLink (linked tracks)
- **Unique Constraints**: One confirmation per user per track (separate for each type)

#### TrackRating
- **Purpose**: User ratings for tracks (0.5 to 5.0 stars)
- **Key Fields**: `track_id` (references Track), `user_id`, `rating` (float)
- **Unique Constraint**: One rating per user per track

#### TrackReview
- **Purpose**: User-written reviews for tracks
- **Key Fields**: `track_id` (references Track), `user_id`, `content`, `contains_spoilers`, `is_public`
- **Unique Constraint**: One review per user per track

#### UserTopTrack
- **Purpose**: User's top 5 favorite tracks
- **Key Fields**: `user_id`, `track_id` (references Track), `order` (1-5)
- **Unique Constraints**: One track per order per user, one order per track per user

#### List & ListItem
- **Purpose**: User-created lists to organize sets
- **List Fields**: `name`, `description`, `is_public`, `is_featured`
- **ListItem Fields**: `list_id`, `set_id`, `position`, `notes`
- **Ordering**: Lists maintain order via `position` field

#### Follow
- **Purpose**: User following relationships (friends)
- **Key Fields**: `follower_id`, `following_id`
- **Constraints**: Cannot follow yourself, unique follow relationship

#### EventSet
- **Purpose**: Many-to-many link between events and sets
- **Key Fields**: `event_id`, `set_id`
- **Note**: Sets can be linked to events without being recordings

#### EventConfirmation
- **Purpose**: Users confirm they attended an event
- **Key Fields**: `user_id`, `event_id`
- **Unique Constraint**: One confirmation per user per event

### Database Relationships Summary

```
User
├── Reviews (1:N)
├── Ratings (1:N)
├── Logs (1:N) - includes top sets
├── Created Sets (1:N)
├── Created Events (1:N)
├── Lists (1:N)
├── Following (M:N via Follow)
└── Event Confirmations (1:N)

DJSet
├── Created By User (N:1)
├── Reviews (1:N)
├── Ratings (1:N)
├── Logs (1:N)
├── Track Tags (1:N)
├── List Items (1:N)
└── Events (M:N via EventSet)

Event
├── Created By User (N:1)
├── Linked Sets (M:N via EventSet)
└── Confirmations (1:N)
```

## API Architecture

### Endpoint Structure

All API endpoints are prefixed with `/api` and organized by resource:

- **`/api/auth`** - Authentication (register, login, OAuth)
- **`/api/users`** - User profiles, search, friends, stats
- **`/api/sets`** - Set CRUD, import, search, filtering
- **`/api/events`** - Event CRUD, linking sets, confirmations
- **`/api/logs`** - Log sets, top sets, user logs
- **`/api/reviews`** - Review CRUD
- **`/api/ratings`** - Rating CRUD, statistics
- **`/api/lists`** - List CRUD, list items
- **`/api/sets/{set_id}/tracks`** - Track tags management (SetTrack and TrackSetLink)
- **`/api/tracks`** - Independent track discovery and CRUD
- **`/api/tracks/{track_id}`** - Get track details with stats
- **`/api/tracks/{track_id}/link-to-set`** - Link track to a set
- **`/api/tracks/{track_id}/set-top`** - Add track to user's top 5
- **`/api/tracks/search`** - Search tracks across platforms (all, soundcloud, spotify)
- **`/api/tracks/search/soundcloud`** - SoundCloud track search
- **`/api/tracks/search/spotify`** - Spotify track search
- **`/api/tracks/resolve-url`** - Resolve SoundCloud or Spotify URL to track info
- **`/api/tracks/{track_id}/ratings`** - Track ratings
- **`/api/tracks/{track_id}/reviews`** - Track reviews

### Authentication

- **Method**: JWT (JSON Web Tokens)
- **Token Storage**: Frontend stores in `localStorage`
- **Token Transmission**: `Authorization: Bearer <token>` header
- **Dependencies**:
  - `get_current_active_user`: Required authentication
  - `get_optional_user`: Optional authentication (for public endpoints)
- **OAuth**: SoundCloud OAuth 2.0 flow supported

### Request/Response Flow

1. **Request**: Frontend service function → Axios instance → FastAPI endpoint
2. **Validation**: Pydantic schemas validate request data
3. **Authentication**: JWT token validated, user fetched from DB
4. **Business Logic**: Endpoint handler processes request
5. **Database**: SQLAlchemy async queries/updates
6. **Response**: Pydantic schema validates response → JSON → Frontend

### Pagination

Most list endpoints support pagination:
- Query params: `page` (default: 1), `limit` (default: 20, max: 100)
- Response: `PaginatedResponse` with `items`, `total`, `page`, `limit`, `pages`

### Error Handling

Custom exceptions in `app/core/exceptions.py`:
- `SetNotFoundError` (404)
- `UnauthorizedError` (401)
- `ForbiddenError` (403)
- `DuplicateEntryError` (409)
- `ExternalAPIError` (502)
- `ValidationError` (422)

## Frontend Architecture

### Component Hierarchy

```
App.jsx (Router)
└── Layout
    ├── Header (Navigation, User Menu)
    ├── Page Component
    │   ├── Feature Components
    │   │   ├── SetCard, SetList
    │   │   ├── ReviewCard, ReviewForm
    │   │   ├── UserProfile, UserStats
    │   │   └── TopSets
    │   └── Service Calls (via hooks)
    └── Footer
```

### State Management

**Zustand Stores**:
- **`authStore`**: User authentication state, login/logout, token management
- **`setsStore`**: Sets list, current set, filters, pagination
- **`uiStore`**: UI state (modals, notifications)

**Local State**: React `useState` for component-specific state

### Service Layer

All API calls go through service functions in `src/services/`:
- Each service file corresponds to a backend API router
- Functions return Axios promises
- Axios instance (`api.js`) handles:
  - Base URL configuration
  - JWT token injection via interceptors
  - 401 error handling (auto-logout)

### Routing

React Router DOM handles client-side routing:
- Public routes: `/`, `/sets` (sets discovery), `/tracks` (tracks discovery), `/tracks/:id` (track details), `/sets/:id` (set details), `/events`, `/events/:id`, `/users/:id`
- Protected routes: `/events/create`, `/profile/manage`, `/feed` (wrapped in `ProtectedRoute`)
- Auth routes: `/login`, `/register`, `/auth/soundcloud/callback`

### Styling

- **Framework**: Tailwind CSS
- **Approach**: Utility-first CSS
- **Custom Colors**: Primary color palette defined in `tailwind.config.js`
- **Responsive**: Mobile-first design with breakpoints

## Key Features

### Sets Management

- **Import from YouTube/SoundCloud**: Paste URL, automatically fetches metadata
- **Manual Creation**: Create live sets manually
- **Search & Filter**: By title, DJ name, source type
- **Logging**: Mark sets as "seen" (live) or "listened" (recordings)
- **Top 5 Sets**: Users can mark up to 5 favorite sets with ordering

### Track System

#### Track Discovery & Management
- **Search Tracks**: Search SoundCloud and Spotify directly from the tracks page
- **Standalone Tracks**: Tracks can exist independently and be linked to multiple sets
- **Track Details Page**: Individual track pages with:
  - Track information (name, artist, duration, platform links)
  - Ratings and reviews
  - Top track management (add to user's top 5)
  - Link to sets functionality
  - Track statistics (average rating, linked sets count)

#### Track Tagging
- **Search-Based Tagging**: Tag tracks by searching SoundCloud/Spotify or entering a URL
- **Automatic Metadata**: Track name and artist are determined from search results or URL resolution
- **Timestamps**: Enter timestamps in MM:SS format (for sets with recordings)
- **Platform Support**: Tracks can have both SoundCloud and Spotify links
- **Confirmation System**: Other users can confirm/deny track accuracy (works for both manually tagged and linked tracks)
- **Statistics**: Track confirmation/denial counts displayed
- **Linking**: Link existing tracks to sets from either the track details page or set details page

### Events System

- **Separate Entity**: Events are distinct from sets
- **Event Creation**: Users can create events (festivals, club nights)
- **Linking Sets**: Link multiple sets to an event
- **Verification**: Users can confirm attendance, events can be verified
- **Multi-day Events**: Support for events spanning multiple days

### Track Ratings & Reviews

- **Track Ratings**: Rate tracks independently with half-star precision (0.5 to 5.0 stars)
- **Track Reviews**: Write reviews for tracks with spoiler tags and public/private options
- **Top 5 Tracks**: Users can mark up to 5 favorite tracks with ordering (displayed on profile)
- **Track Statistics**: Average ratings, rating counts, and review counts per track

### Social Features

- **Friends System**: Follow other users (called "friends")
- **Friend Search**: Search users by username or display name
- **Profile Pages**: View user stats, top sets, top tracks, logged sets, reviews
- **Activity Feed**: See activity from friends (reviews, lists)
- **Profile Management**: Edit display name, bio, avatar URL

### Reviews & Ratings

- **Half-Star Ratings**: 0.5 to 5.0 stars
- **Written Reviews**: Optional reviews with spoiler tags
- **Public/Private**: Reviews can be marked public or private
- **Rating Statistics**: Average ratings, rating distribution

### Lists

- **Custom Lists**: Create lists to organize sets
- **Ordered Items**: Maintain position/order in lists
- **Public/Private**: Lists can be public or private
- **Featured Lists**: Support for featured lists

## Getting Started

### Prerequisites

- **Python 3.12+**
- **Node.js 18+** and npm
- **PostgreSQL 12+**
- **YouTube Data API Key** (optional, for YouTube imports)
- **SoundCloud API Credentials** (optional, for SoundCloud imports/OAuth/track search)
- **Spotify API Credentials** (optional, for Spotify track search)

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file** in `backend/`:
   ```env
   DATABASE_URL=postgresql://username:password@localhost:5432/deckd
   JWT_SECRET=your-secret-key-here-change-in-production
   JWT_ALGORITHM=HS256
   JWT_EXPIRATION_HOURS=24
   YOUTUBE_API_KEY=your-youtube-api-key
   SOUNDCLOUD_CLIENT_ID=your-soundcloud-client-id
   SOUNDCLOUD_CLIENT_SECRET=your-soundcloud-client-secret
   SOUNDCLOUD_REDIRECT_URI=http://localhost:5173/auth/soundcloud/callback
   SPOTIFY_CLIENT_ID=your-spotify-client-id
   SPOTIFY_CLIENT_SECRET=your-spotify-client-secret
   ```

5. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

6. **Start the server**:
   ```bash
   uvicorn app.main:app --reload
   ```

   API will be available at `http://localhost:8000`
   API docs (Swagger UI) at `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Create `.env` file** in `frontend/`:
   ```env
   VITE_API_URL=http://localhost:8000/api
   ```

4. **Start the development server**:
   ```bash
   npm run dev
   ```

   App will be available at `http://localhost:5173`

### Quick Start (Both Servers)

Use the convenience script:
```bash
./start.sh
```

This starts both backend and frontend servers simultaneously.

## Development

### Database Migrations

**Create a new migration**:
```bash
cd backend
alembic revision --autogenerate -m "description_of_changes"
```

**Apply migrations**:
```bash
alembic upgrade head
```

**Rollback migration**:
```bash
alembic downgrade -1
```

### Code Structure Guidelines

**Backend**:
- Models in `app/models.py` (SQLAlchemy ORM)
- Schemas in `app/schemas.py` (Pydantic validation)
- API routes in `app/api/` (one file per resource)
- Business logic in `app/services/` (external API integrations)
- Use async/await for all database operations

**Frontend**:
- Pages in `src/pages/` (route components)
- Reusable components in `src/components/`
- API calls via service functions in `src/services/`
- Global state in Zustand stores (`src/store/`)
- Local state with React hooks

### Testing API Endpoints

FastAPI provides interactive API documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Environment Variables

**Backend** (`.env` in `backend/`):
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET`: Secret key for JWT signing
- `JWT_ALGORITHM`: JWT algorithm (default: HS256)
- `JWT_EXPIRATION_HOURS`: Token expiration (default: 24)
- `YOUTUBE_API_KEY`: YouTube Data API v3 key
- `SOUNDCLOUD_CLIENT_ID`: SoundCloud API client ID
- `SOUNDCLOUD_CLIENT_SECRET`: SoundCloud API client secret
- `SOUNDCLOUD_REDIRECT_URI`: OAuth redirect URI
- `SPOTIFY_CLIENT_ID`: Spotify API client ID (optional, for track search)
- `SPOTIFY_CLIENT_SECRET`: Spotify API client secret (optional, for track search)

**Frontend** (`.env` in `frontend/`):
- `VITE_API_URL`: Backend API base URL

## External Integrations

### YouTube Data API v3

- **Purpose**: Import DJ sets from YouTube
- **Service**: `app/services/youtube.py`
- **Endpoints Used**: 
  - `videos.list` - Get video metadata
  - `videos.list` (part=snippet,contentDetails) - Get title, description, duration
- **Required**: YouTube Data API key

### SoundCloud API v2

- **Purpose**: Import sets, search tracks, OAuth login
- **Services**: 
  - `app/services/soundcloud.py` - Set import, track search
  - `app/services/soundcloud_oauth.py` - OAuth flow
  - `app/services/soundcloud_search.py` - Track search and URL resolution
- **Authentication**: 
  - Client credentials flow (for API access)
  - OAuth 2.0 flow (for user login)
- **Required**: SoundCloud API client ID and secret

### Spotify Web API

- **Purpose**: Search tracks, resolve track URLs
- **Service**: `app/services/spotify_search.py` - Track search and URL resolution
- **Authentication**: Client credentials flow (OAuth 2.0)
- **Endpoints Used**:
  - `GET /v1/search` - Search for tracks
  - `GET /v1/tracks/{id}` - Get track details
- **Required**: Spotify API client ID and secret
- **Setup**: Create an app at https://developer.spotify.com/dashboard

### API Rate Limits

- **YouTube**: 10,000 units/day (quota)
- **SoundCloud**: Varies by endpoint, token caching implemented
- **Spotify**: Token caching implemented, rate limits vary by endpoint

## Project Philosophy

### Sets vs Events

- **Sets**: Recordings or listenings of DJ performances (YouTube, SoundCloud, or manually created live sets)
- **Events**: Live shows/festivals that occurred (separate entity)
- **Relationship**: Sets can be linked to events via `EventSet` table, but they remain separate entities
- **Rationale**: A single event can have multiple sets, and sets can exist without events

### User Experience

- **Letterboxd-inspired**: Familiar UX patterns for film/music enthusiasts
- **Social-first**: Emphasis on following friends, discovering through social connections
- **Flexible logging**: Support for both recorded sets and live experiences
- **Community verification**: Track confirmations, event confirmations for accuracy

## Contributing

This is a personal project, but contributions and feedback are welcome!

## License

[Add your license here]

---

*Built with ❤️ for the DJ community*
