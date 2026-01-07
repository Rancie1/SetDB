# SetDB Backend

FastAPI backend for the SetDB DJ sets tracking app.

## Setup Instructions

1. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file** in the backend directory with:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/deckd
   JWT_SECRET=your-secret-key-here
   JWT_ALGORITHM=HS256
   JWT_EXPIRATION_HOURS=24
   YOUTUBE_API_KEY=your-youtube-api-key
   SOUNDCLOUD_CLIENT_ID=your-soundcloud-client-id
   ```

4. **Run the development server**:
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`
   API documentation (Swagger UI) will be at `http://localhost:8000/docs`

## Project Structure

- `app/main.py` - FastAPI app initialization
- `app/models.py` - Database models (SQLAlchemy)
- `app/schemas.py` - Request/response validation (Pydantic)
- `app/database.py` - Database connection
- `app/auth.py` - Authentication utilities
- `app/api/` - API route handlers
- `app/services/` - External API integrations

