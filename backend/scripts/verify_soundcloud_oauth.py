#!/usr/bin/env python3
"""
Script to verify SoundCloud OAuth configuration.

This helps troubleshoot OAuth setup issues by checking:
- Environment variables are set
- Redirect URI format is correct
- Configuration matches expected values
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings

def verify_config():
    """Verify SoundCloud OAuth configuration."""
    print("=" * 60)
    print("SoundCloud OAuth Configuration Verification")
    print("=" * 60)
    print()
    
    # Check Client ID
    client_id = settings.SOUNDCLOUD_CLIENT_ID
    if client_id:
        print(f"✅ SOUNDCLOUD_CLIENT_ID: {client_id[:10]}...{client_id[-5:]}")
    else:
        print("❌ SOUNDCLOUD_CLIENT_ID: NOT SET")
        print("   Add this to your backend/.env file")
    
    # Check Client Secret
    client_secret = settings.SOUNDCLOUD_CLIENT_SECRET
    if client_secret:
        print(f"✅ SOUNDCLOUD_CLIENT_SECRET: {client_secret[:5]}...{client_secret[-3:]}")
    else:
        print("❌ SOUNDCLOUD_CLIENT_SECRET: NOT SET")
        print("   Add this to your backend/.env file")
    
    # Check Redirect URI
    redirect_uri = settings.SOUNDCLOUD_REDIRECT_URI
    if redirect_uri:
        print(f"✅ SOUNDCLOUD_REDIRECT_URI: {redirect_uri}")
        
        # Validate format
        if not redirect_uri.startswith(('http://', 'https://')):
            print("   ⚠️  WARNING: Redirect URI should start with http:// or https://")
        
        if redirect_uri.endswith('/'):
            print("   ⚠️  WARNING: Redirect URI should NOT end with a trailing slash")
            print(f"   Suggested: {redirect_uri.rstrip('/')}")
        
        # Check if it matches expected pattern
        expected_patterns = [
            'http://localhost:5173/auth/soundcloud/callback',
            'http://localhost:3000/auth/soundcloud/callback',
            'https://',
        ]
        
        matches_pattern = any(
            redirect_uri.startswith(pattern) or redirect_uri == pattern.rstrip('/')
            for pattern in expected_patterns
        )
        
        if not matches_pattern and not redirect_uri.startswith('https://'):
            print("   ⚠️  WARNING: Redirect URI doesn't match common patterns")
    else:
        print("❌ SOUNDCLOUD_REDIRECT_URI: NOT SET")
        print("   Add this to your backend/.env file")
        print("   Example: SOUNDCLOUD_REDIRECT_URI=http://localhost:5173/auth/soundcloud/callback")
    
    print()
    print("=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print()
    print("1. Go to https://developers.soundcloud.com/")
    print("2. Sign in and find your application")
    print("3. Verify the Redirect URI matches EXACTLY:")
    print(f"   {redirect_uri or 'NOT SET'}")
    print()
    print("   Common issues:")
    print("   - Trailing slash mismatch (one has /, other doesn't)")
    print("   - Port number mismatch (5173 vs 3000)")
    print("   - http:// vs https:// mismatch")
    print("   - Case sensitivity (though URLs are usually case-insensitive)")
    print()
    print("4. Verify the Client ID matches:")
    print(f"   {client_id[:10] if client_id else 'NOT SET'}...")
    print()
    print("5. Make sure your application is approved/active")
    print()
    print("=" * 60)

if __name__ == "__main__":
    verify_config()
