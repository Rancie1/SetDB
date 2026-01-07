# SoundCloud API Setup Guide

## Overview

To get full SoundCloud API access (for publish dates, duration, etc.), you need to register an application and get API credentials.

## Step 1: Register Your Application

1. **Go to SoundCloud Developers**: https://developers.soundcloud.com/
2. **Sign in** with your SoundCloud account (or create one if needed)
3. **Request API Access**:
   - SoundCloud requires you to email them for API access
   - See `/SOUNDCLOUD_API_EMAIL_TEMPLATE.md` for email template
   - Required information:
     - **App Name**: SetDB
     - **Description/Use Case**: DJ set tracking and cataloging platform
     - **Redirect URI**: `http://localhost:8000/api/auth/soundcloud/callback`
   
   **Note:** You may need to register on their developer portal first, then email them with the above information.

## Step 2: Get Your Credentials

After emailing SoundCloud and getting approval, you'll receive:
- **Client ID**: A public identifier for your app
- **Client Secret**: A private key (if using OAuth - keep this secret!)

**Note:** The approval process may take a few days. You can still use the app with oEmbed API (limited features) while waiting.

## Step 3: Add to Your .env File

Add these to your `backend/.env` file:

```env
SOUNDCLOUD_CLIENT_ID=your_client_id_here
SOUNDCLOUD_CLIENT_SECRET=your_client_secret_here
```

## Step 4: Using the API

### Public Resources (No OAuth Required)

For public tracks, you can use the **Client Credentials Flow** or just use the Client ID directly:

```python
# Simple approach - just use client_id
track_url = "https://soundcloud.com/user/track"
api_url = f"https://api.soundcloud.com/resolve?url={track_url}&client_id={CLIENT_ID}"
```

### What You Can Get

With full API access, you can get:
- ✅ **Publish date** (`created_at` field)
- ✅ **Duration** (`duration` in milliseconds)
- ✅ **Play count**
- ✅ **Like count**
- ✅ **Genre/Tags**
- ✅ **Full user information**
- ✅ **Waveform data**

## API Endpoints

### Resolve URL to Track
```
GET https://api.soundcloud.com/resolve?url={track_url}&client_id={CLIENT_ID}
```

### Get Track by ID
```
GET https://api.soundcloud.com/tracks/{track_id}?client_id={CLIENT_ID}
```

### Example Response
```json
{
  "id": 123456789,
  "created_at": "2024-01-15T10:30:00Z",
  "duration": 3600000,  // milliseconds
  "title": "Track Title",
  "description": "Track description",
  "genre": "Electronic",
  "tag_list": "techno, house",
  "permalink_url": "https://soundcloud.com/user/track",
  "artwork_url": "https://...",
  "user": {
    "id": 12345,
    "username": "djname",
    "full_name": "DJ Name"
  },
  "playback_count": 1000,
  "likes_count": 50
}
```

## Authentication Options

### Option 1: Client ID Only (Simplest)
- ✅ Works for public tracks
- ✅ No OAuth setup needed
- ✅ Good for read-only access
- ❌ Limited to public data

### Option 2: OAuth 2.1 (Full Access)
- ✅ Access to user's private tracks
- ✅ Can perform actions (like, repost)
- ❌ More complex setup
- ❌ Requires user authorization

**For Deckd, Option 1 (Client ID only) is sufficient** since we're just importing public tracks.

## Rate Limits

SoundCloud has rate limits:
- **Unauthenticated**: ~15,000 requests/day
- **Authenticated**: Higher limits

For importing sets, this should be plenty.

## Testing

Once you have your Client ID, test it:

```bash
curl "https://api.soundcloud.com/resolve?url=https://soundcloud.com/user/track&client_id=YOUR_CLIENT_ID"
```

## Next Steps

1. Register your app at https://developers.soundcloud.com/
2. Get your Client ID
3. Add it to `.env`
4. The updated service will automatically use it!

