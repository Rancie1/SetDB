# SoundCloud OAuth Troubleshooting Guide

## Common Error: 403 Forbidden

If you're getting a `403 (Forbidden)` error when trying to log in with SoundCloud, it means SoundCloud is rejecting your authorization request. This happens **before** the callback reaches your backend.

## Step-by-Step Fix

### 1. Verify SoundCloud Developer Portal Settings

1. **Go to**: https://developers.soundcloud.com/
2. **Sign in** with your SoundCloud account
3. **Click on your application** (or create one if you haven't)
4. **Check these settings:**

#### Redirect URI (CRITICAL - Must Match Exactly)

Your redirect URI in SoundCloud **must match exactly** what's in your backend `.env`:

```
http://localhost:5173/auth/soundcloud/callback
```

**Common mistakes:**
- ❌ `http://localhost:5173/auth/soundcloud/callback/` (trailing slash)
- ❌ `http://localhost:3000/auth/soundcloud/callback` (wrong port)
- ❌ `https://localhost:5173/auth/soundcloud/callback` (https instead of http)
- ✅ `http://localhost:5173/auth/soundcloud/callback` (correct)

#### Client ID

- Verify the Client ID in SoundCloud matches what's in your `.env` file
- It should start with: `bOiu3j0laW...` (based on your config)

#### Application Status

- Make sure your application is **active/approved**
- Some SoundCloud apps require manual approval

### 2. Check Your Backend Configuration

Run the verification script:

```bash
cd backend
source venv/bin/activate
python scripts/verify_soundcloud_oauth.py
```

This will show you:
- ✅ What's configured correctly
- ❌ What's missing
- ⚠️  Potential issues

### 3. Test the Authorization URL

When you click "Login with SoundCloud", check your browser's Network tab:

1. Open Developer Tools (F12)
2. Go to Network tab
3. Click "Login with SoundCloud"
4. Look for the request to `soundcloud.com/connect`
5. Check the `redirect_uri` parameter in the URL

It should be URL-encoded and look like:
```
https://soundcloud.com/connect?client_id=...&redirect_uri=http%3A%2F%2Flocalhost%3A5173%2Fauth%2Fsoundcloud%2Fcallback&...
```

### 4. Common Issues and Solutions

#### Issue: Redirect URI Mismatch

**Symptom**: 403 error immediately when clicking login

**Solution**: 
- Go to SoundCloud developer portal
- Copy the exact redirect URI from your `.env` file
- Paste it into SoundCloud's redirect URI field
- Make sure there are NO trailing slashes
- Save and wait a few minutes for changes to propagate

#### Issue: Application Not Approved

**Symptom**: 403 error, but redirect URI matches

**Solution**:
- Check if SoundCloud requires manual approval
- You may need to email SoundCloud support
- Some apps are auto-approved, others require review

#### Issue: Wrong Port Number

**Symptom**: Works sometimes, fails other times

**Solution**:
- Make sure your frontend is running on port 5173 (Vite default)
- Or update both `.env` and SoundCloud portal to match your actual port
- Check `package.json` or `vite.config.js` for port configuration

#### Issue: Client ID Mismatch

**Symptom**: 403 error, redirect URI is correct

**Solution**:
- Verify Client ID in SoundCloud portal matches your `.env`
- Regenerate Client ID/Secret if needed
- Make sure you're using the correct app's credentials

### 5. Debug Steps

#### Check Backend Logs

When you click "Login with SoundCloud", check your backend terminal. You should see:

```
INFO: Generating SoundCloud OAuth URL with redirect_uri: http://localhost:5173/auth/soundcloud/callback
INFO: Generated SoundCloud authorization URL: https://soundcloud.com/connect?client_id=...&redirect_uri=...
```

#### Check Browser Console

Open browser DevTools (F12) → Console tab. Look for:
- Any JavaScript errors
- Network errors (especially the 403)
- The actual redirect URI being used

#### Test Redirect URI Manually

Try visiting this URL directly (replace with your actual client_id):

```
https://soundcloud.com/connect?client_id=YOUR_CLIENT_ID&redirect_uri=http%3A%2F%2Flocalhost%3A5173%2Fauth%2Fsoundcloud%2Fcallback&response_type=code&scope=non-expiring
```

If this works, the issue is elsewhere. If it fails with 403, the redirect URI is definitely wrong.

### 6. Still Not Working?

If you've verified everything above and it's still not working:

1. **Double-check SoundCloud Portal**:
   - Log out and back in
   - Refresh the page
   - Check if there are multiple apps (maybe you're editing the wrong one)

2. **Try a Different Redirect URI**:
   - Sometimes SoundCloud is picky about localhost
   - Try: `http://127.0.0.1:5173/auth/soundcloud/callback`
   - Update both `.env` and SoundCloud portal

3. **Check SoundCloud Status**:
   - SoundCloud's OAuth service might be down
   - Check their status page or try again later

4. **Contact SoundCloud Support**:
   - If nothing works, email SoundCloud support
   - Include your Client ID and redirect URI
   - Ask them to verify your app configuration

## Quick Checklist

Before asking for help, verify:

- [ ] Redirect URI in SoundCloud portal matches `.env` exactly (no trailing slash)
- [ ] Client ID in SoundCloud matches `.env`
- [ ] Application is active/approved in SoundCloud
- [ ] Frontend is running on the correct port (5173)
- [ ] Backend `.env` file has all three variables set
- [ ] Backend server has been restarted after changing `.env`
- [ ] No typos in redirect URI (localhost vs 127.0.0.1, http vs https)

## Need More Help?

If you've checked everything and it's still not working:

1. Run the verification script and share the output
2. Check backend logs when clicking login
3. Check browser console for errors
4. Share the exact error message you're seeing
