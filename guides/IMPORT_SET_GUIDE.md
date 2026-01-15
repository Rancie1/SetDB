# How to Import DJ Sets Using the API

This guide explains how to import DJ sets from YouTube or SoundCloud using the SetDB API.

## API Endpoints

There are two import endpoints:

1. **YouTube Import**: `POST /api/sets/import/youtube`
2. **SoundCloud Import**: `POST /api/sets/import/soundcloud`

Both endpoints require:
- **Authentication**: You must be logged in (JWT token required)
- **Request Body**: JSON with a `url` field

## Request Format

### Request Body Schema

```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

or

```json
{
  "url": "https://soundcloud.com/artist/track-name"
}
```

## Using cURL

### 1. First, log in to get your JWT token:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

This returns a response like:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Import from YouTube:

```bash
curl -X POST http://localhost:8000/api/sets/import/youtube \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  }'
```

### 3. Import from SoundCloud:

```bash
curl -X POST http://localhost:8000/api/sets/import/soundcloud \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "url": "https://soundcloud.com/artist/track-name"
  }'
```

## Using the Frontend

The frontend already has an import form on the Discover page. Simply:

1. Navigate to `/discover` (or click "Discover" in the navigation)
2. Paste a YouTube or SoundCloud URL in the import form
3. Click "Import Set"

The form automatically detects the platform and calls the correct endpoint.

## Response Format

On success, you'll receive a `201 Created` response with the imported set:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "DJ Set Title",
  "dj_name": "Artist Name",
  "source_type": "youtube",
  "source_url": "https://www.youtube.com/watch?v=...",
  "description": "Set description...",
  "thumbnail_url": "https://i.ytimg.com/vi/.../maxresdefault.jpg",
  "duration_minutes": 120,
  "event_name": null,
  "event_date": null,
  "venue_location": null,
  "extra_metadata": {
    "video_id": "...",
    "channel_name": "...",
    "published_at": "2024-01-01T00:00:00Z"
  },
  "created_by_id": "user-uuid-here",
  "created_at": "2024-01-06T12:00:00Z",
  "updated_at": "2024-01-06T12:00:00Z"
}
```

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```
**Solution**: Make sure you're logged in and include the JWT token in the Authorization header.

### 400 Bad Request
```json
{
  "detail": "Invalid URL format"
}
```
**Solution**: Check that the URL is a valid YouTube or SoundCloud URL.

### 500 Internal Server Error
```json
{
  "detail": "Failed to import from YouTube: Video not found"
}
```
**Solution**: The video/track might be private, deleted, or the API credentials might be missing/incorrect.

## Supported URL Formats

### YouTube
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/embed/VIDEO_ID`

### SoundCloud
- `https://soundcloud.com/artist/track-name`
- `https://soundcloud.com/artist/track-name?si=...` (with query params)

## What Gets Imported?

### From YouTube:
- Title (video title)
- DJ Name (channel name)
- Description (video description)
- Thumbnail URL
- Duration (in minutes)
- Publish date (stored in `extra_metadata`)
- Video ID and channel info (stored in `extra_metadata`)

### From SoundCloud:
- Title (track title)
- DJ Name (artist/uploader name)
- Description (track description)
- Thumbnail URL (artwork)
- Duration (if available via API)
- Publish date (if available via API, stored in `extra_metadata`)
- Track metadata (stored in `extra_metadata`)

**Note**: For SoundCloud, duration and publish date are only available if you have a `SOUNDCLOUD_CLIENT_ID` configured in your `.env` file. Without it, the API falls back to oEmbed which provides limited information.

## Testing with the API Docs

FastAPI automatically generates interactive API documentation:

1. Start your backend server: `cd backend && uvicorn app.main:app --reload`
2. Open your browser to: `http://localhost:8000/docs`
3. Find the `/api/sets/import/youtube` or `/api/sets/import/soundcloud` endpoint
4. Click "Try it out"
5. Click "Authorize" and enter your JWT token (format: `Bearer YOUR_TOKEN`)
6. Enter a URL in the request body
7. Click "Execute"

This is the easiest way to test the import functionality!

## Example: Complete Import Flow

```bash
# 1. Register a new user (if needed)
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'

# 2. Login
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }' | jq -r '.access_token')

# 3. Import a YouTube set
curl -X POST http://localhost:8000/api/sets/import/youtube \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  }' | jq

# 4. Import a SoundCloud set
curl -X POST http://localhost:8000/api/sets/import/soundcloud \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "url": "https://soundcloud.com/artist/track-name"
  }' | jq
```

## Troubleshooting

### "Failed to import from YouTube: API key not configured"
- Add `YOUTUBE_API_KEY=your_key_here` to `backend/.env`
- Restart the backend server

### "Failed to import from SoundCloud: Track not found"
- Check that the URL is correct and the track is public
- Verify your `SOUNDCLOUD_CLIENT_ID` is set in `backend/.env` (optional but recommended)

### "Not authenticated" error
- Make sure you're including the JWT token: `Authorization: Bearer YOUR_TOKEN`
- Check that your token hasn't expired (default: 24 hours)
- Log in again to get a new token

### Import works but some fields are missing
- For YouTube: Make sure `YOUTUBE_API_KEY` is configured
- For SoundCloud: Make sure `SOUNDCLOUD_CLIENT_ID` is configured for full metadata
- Some tracks/videos might not have all metadata available

