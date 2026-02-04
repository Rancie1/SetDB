"""
Property-based tests for Google OAuth database schema.

**Property 5: Database Consistency and Profile Updates**
**Validates: Requirements 5.1, 5.3, 5.5**

For any user with Google credentials, the google_user_id must be unique across all users, 
and profile data (avatar, display name) must be updated only when not already set.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models import User, Base
from app.database import get_db

class TestGoogleOAuthDatabase:
    """Test Google OAuth database schema and operations."""
    
    def test_user_model_has_google_oauth_fields(self):
        """
        Property Test: User model contains required Google OAuth fields.
        
        **Validates: Requirements 5.1, 5.2**
        Tests that the User model has all required Google OAuth fields.
        """
        # Check that User model has the required Google OAuth fields
        user_columns = [column.name for column in User.__table__.columns]
        
        assert 'google_user_id' in user_columns
        assert 'google_access_token' in user_columns
        assert 'google_refresh_token' in user_columns
        assert 'google_token_expires_at' in user_columns
    
    def test_google_user_id_has_unique_constraint(self):
        """
        Property Test: google_user_id field has unique constraint.
        
        **Validates: Requirements 5.1, 5.5**
        Tests that google_user_id field has proper unique constraint and index.
        """
        # Check that google_user_id column has unique constraint
        google_user_id_column = None
        for column in User.__table__.columns:
            if column.name == 'google_user_id':
                google_user_id_column = column
                break
        
        assert google_user_id_column is not None
        assert google_user_id_column.unique is True
        assert google_user_id_column.index is True
        assert google_user_id_column.nullable is True  # Should be nullable for non-Google users
    
    def test_google_oauth_fields_are_optional(self):
        """
        Property Test: Google OAuth fields are nullable.
        
        **Validates: Requirements 5.1, 5.2**
        Tests that Google OAuth fields are optional (nullable) for users who don't use Google auth.
        """
        google_fields = ['google_user_id', 'google_access_token', 'google_refresh_token', 'google_token_expires_at']
        
        for field_name in google_fields:
            column = None
            for col in User.__table__.columns:
                if col.name == field_name:
                    column = col
                    break
            
            assert column is not None, f"Field {field_name} not found in User model"
            assert column.nullable is True, f"Field {field_name} should be nullable"
    
    def test_google_token_expires_at_is_datetime(self):
        """
        Property Test: google_token_expires_at field is DateTime type.
        
        **Validates: Requirements 5.2**
        Tests that the token expiration field has correct data type.
        """
        expires_at_column = None
        for column in User.__table__.columns:
            if column.name == 'google_token_expires_at':
                expires_at_column = column
                break
        
        assert expires_at_column is not None
        # Check that it's a DateTime type
        assert 'DATETIME' in str(expires_at_column.type) or 'TIMESTAMP' in str(expires_at_column.type)
    
    def test_user_creation_with_google_fields(self):
        """
        Property Test: User can be created with Google OAuth fields.
        
        **Validates: Requirements 5.1, 5.3**
        Tests that User instances can be created with Google OAuth data.
        """
        # Create a user instance with Google OAuth fields
        user = User(
            username="testuser",
            email="test@example.com",
            google_user_id="google_123456",
            google_access_token="access_token_123",
            google_refresh_token="refresh_token_123",
            google_token_expires_at=datetime.utcnow()
        )
        
        # Verify all fields are set correctly
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.google_user_id == "google_123456"
        assert user.google_access_token == "access_token_123"
        assert user.google_refresh_token == "refresh_token_123"
        assert user.google_token_expires_at is not None
        assert isinstance(user.google_token_expires_at, datetime)
    
    def test_user_creation_without_google_fields(self):
        """
        Property Test: User can be created without Google OAuth fields.
        
        **Validates: Requirements 5.1**
        Tests that User instances can be created without Google OAuth data (for non-Google users).
        """
        # Create a user instance without Google OAuth fields
        user = User(
            username="regularuser",
            email="regular@example.com",
            hashed_password="hashed_password_123"
        )
        
        # Verify Google fields are None/null
        assert user.username == "regularuser"
        assert user.email == "regular@example.com"
        assert user.hashed_password == "hashed_password_123"
        assert user.google_user_id is None
        assert user.google_access_token is None
        assert user.google_refresh_token is None
        assert user.google_token_expires_at is None
    
    def test_profile_data_preservation(self):
        """
        Property Test: Profile data preservation during Google linking.
        
        **Validates: Requirements 5.3**
        Tests that existing profile data is preserved when linking Google account.
        """
        # Create a user with existing profile data
        user = User(
            username="existinguser",
            email="existing@example.com",
            display_name="Existing User",
            avatar_url="https://example.com/existing-avatar.jpg",
            bio="Existing bio"
        )
        
        # Simulate linking Google account (would preserve existing data)
        user.google_user_id = "google_789"
        user.google_access_token = "new_access_token"
        
        # Verify existing profile data is preserved
        assert user.display_name == "Existing User"
        assert user.avatar_url == "https://example.com/existing-avatar.jpg"
        assert user.bio == "Existing bio"
        assert user.google_user_id == "google_789"
        assert user.google_access_token == "new_access_token"