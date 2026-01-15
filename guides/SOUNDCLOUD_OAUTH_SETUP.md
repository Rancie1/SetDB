# SoundCloud OAuth Login Setup

This guide explains how to set up SoundCloud OAuth login for your SetDB application.

## Overview

SoundCloud OAuth allows users to log in with their SoundCloud accounts instead of creating a separate SetDB account. This provides:
- **Easier onboarding**: Users don't need to create another account
- **Profile sync**: Automatically imports avatar and display name from SoundCloud
- **Future features**: Can access user's SoundCloud playlists, likes, etc.

## Setup Steps

### 1. Register Your Application with SoundCloud

1. Go to [SoundCloud Developers](https://developers.soundcloud.com/)
2. Sign in with your SoundCloud account
3. Click "Register a new application"
4. Fill in the application details:
   - **Application name**: SetDB (or your app name)
   - **Website**: Your app's URL (e.g., `http://localhost:5173` for development)
   - **Redirect URI**: `http://localhost:5173/auth/soundcloud/callback` (for development)
     - For production, use your actual domain: `https://yourdomain.com/auth/soundcloud/callback`
5. Save the application
6. Copy your **Client ID** and **Client Secret**

### 2. Update Environment Variables

Add these to your `backend/.env` file:

```env
SOUNDCLOUD_CLIENT_ID=your_client_id_here
SOUNDCLOUD_CLIENT_SECRET=your_client_secret_here
SOUNDCLOUD_REDIRECT_URI=http://localhost:5173/auth/soundcloud/callback
```

**Important**: 
- For production, update `SOUNDCLOUD_REDIRECT_URI` to your production URL
- The redirect URI must match exactly what you registered with SoundCloud

### 3. Create Database Migration

Run this to add the new OAuth fields to the User table:

```bash
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "Add SoundCloud OAuth fields to users"
alembic upgrade head
```

### 4. Frontend Integration

The backend provides two endpoints:

#### Get Authorization URL
```
GET /api/auth/soundcloud/authorize
```

Returns:
```json
{
  "authorization_url": "https://soundcloud.com/connect?...",
  "state": "csrf_token_here"
}
```

#### Handle Callback
```
POST /api/auth/soundcloud/callback
Body: {
  "code": "authorization_code",
  "state": "csrf_token_from_step_1"
}
```

Returns:
```json
{
  "access_token": "jwt_token_for_setdb",
  "token_type": "bearer"
}
```

### 5. Frontend Flow

1. User clicks "Login with SoundCloud"
2. Frontend calls `GET /api/auth/soundcloud/authorize`
3. Store the `state` token (in sessionStorage or memory)
4. Redirect user to `authorization_url`
5. User authorizes on SoundCloud
6. SoundCloud redirects to your `redirect_uri` with `code` and `state` query params
7. Frontend extracts `code` and sends it (with stored `state`) to `POST /api/auth/soundcloud/callback`
8. Backend returns JWT token
9. Frontend stores token and logs user in

## How It Works

1. **Authorization Code Flow**: Standard OAuth2 flow for user authentication
2. **User Creation**: If user doesn't exist, creates account automatically
3. **Token Storage**: Stores SoundCloud access/refresh tokens for future API calls
4. **JWT Token**: Returns SetDB JWT token for app authentication

## Security Notes

- **State Parameter**: Always verify the `state` parameter to prevent CSRF attacks
- **HTTPS**: Use HTTPS in production (required by SoundCloud)
- **Token Storage**: In production, encrypt SoundCloud tokens before storing
- **Redirect URI**: Must match exactly what's registered with SoundCloud

## Testing

1. Start your backend: `uvicorn app.main:app --reload`
2. Start your frontend: `npm run dev`
3. Click "Login with SoundCloud"
4. You should be redirected to SoundCloud
5. After authorization, you'll be redirected back and logged in

## Troubleshooting

**"Invalid redirect_uri"**
- Check that `SOUNDCLOUD_REDIRECT_URI` matches exactly what's registered with SoundCloud
- Make sure there are no trailing slashes or extra characters

**"Invalid client_id"**
- Verify `SOUNDCLOUD_CLIENT_ID` is correct in your `.env` file

**"Failed to exchange code for token"**
- Check that `SOUNDCLOUD_CLIENT_SECRET` is correct
- Make sure the redirect URI matches

**"Failed to fetch user info"**
- The access token might be invalid
- Check backend logs for detailed error messages
