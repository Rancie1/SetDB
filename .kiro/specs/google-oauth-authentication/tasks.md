# Implementation Plan: Google OAuth Authentication

## Overview

This implementation plan breaks down the Google OAuth authentication feature into discrete coding tasks. The approach follows the existing SoundCloud OAuth patterns, ensuring consistency with the current authentication system. Tasks are organized to build incrementally, with early validation through testing.

## Tasks

- [x] 1. Set up Google OAuth service and database schema
  - [x] 1.1 Create Google OAuth service module
    - Create `backend/app/services/google_oauth.py` with OAuth 2.0 flow functions
    - Implement authorization URL generation, token exchange, and user info retrieval
    - Follow the same patterns as `soundcloud_oauth.py`
    - _Requirements: 1.1, 1.2, 1.3, 7.1, 7.4, 7.5_
  
  - [x] 1.2 Write property test for OAuth service
    - **Property 1: Complete OAuth Flow**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 3.1, 3.2**
  
  - [x] 1.3 Create database migration for Google OAuth fields
    - Add Google-specific columns to users table: google_user_id, google_access_token, google_refresh_token, google_token_expires_at
    - Create unique index on google_user_id for efficient lookups
    - _Requirements: 5.1, 5.2, 5.5_
  
  - [x] 1.4 Write property test for database schema
    - **Property 5: Database Consistency and Profile Updates**
    - **Validates: Requirements 5.1, 5.3, 5.5**

- [x] 2. Implement backend API endpoints
  - [x] 2.1 Add Google OAuth endpoints to auth router
    - Implement GET `/api/auth/google/authorize` endpoint
    - Implement POST `/api/auth/google/callback` endpoint
    - Follow same response patterns as SoundCloud OAuth endpoints
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  
  - [x] 2.2 Write property test for API endpoints
    - **Property 8: API Response Consistency**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
  
  - [x] 2.3 Implement account creation and linking logic
    - Handle new account creation from Google profile data
    - Implement account linking when email matches existing user
    - Preserve existing user data during linking process
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  
  - [x] 2.4 Write property test for account management
    - **Property 2: Account Creation and Linking**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

- [x] 3. Add security and error handling
  - [x] 3.1 Implement CSRF protection with state parameters
    - Generate unique state tokens for each OAuth request
    - Validate state parameters in callback handler
    - Reject authentication attempts with invalid state
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [x] 3.2 Write property test for state validation
    - **Property 3: State Parameter Security**
    - **Validates: Requirements 3.2, 3.3**
  
  - [x] 3.3 Implement comprehensive error handling
    - Handle configuration errors (missing credentials)
    - Handle OAuth flow errors (invalid codes, API failures)
    - Return user-friendly error messages
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  
  - [x] 3.4 Write property test for error handling
    - **Property 6: Configuration-Based Error Handling**
    - **Validates: Requirements 6.1, 6.2, 6.3, 7.1, 7.3**

- [x] 4. Checkpoint - Backend implementation complete
  - Ensure all backend tests pass, ask the user if questions arise.

- [x] 5. Implement frontend components
  - [x] 5.1 Create Google sign-in button component
    - Create reusable GoogleSignInButton component
    - Follow Google's branding guidelines
    - Handle loading states and click events
    - _Requirements: 4.1, 4.2_
  
  - [x] 5.2 Extend authentication store with Google OAuth methods
    - Add `loginWithGoogle()` method to authStore
    - Add `handleGoogleCallback()` method for processing callbacks
    - Follow same patterns as SoundCloud OAuth methods
    - _Requirements: 4.2, 4.3, 4.4, 4.5_
  
  - [x] 5.3 Write property test for frontend authentication
    - **Property 7: Frontend Authentication State**
    - **Validates: Requirements 4.2, 4.3, 4.4, 4.5, 6.5**
  
  - [x] 5.4 Create Google OAuth callback page
    - Create GoogleCallbackPage component to handle OAuth redirects
    - Extract code and state parameters from URL
    - Process authentication and redirect to intended destination
    - _Requirements: 4.3, 4.4, 4.5_

- [x] 6. Implement secure token management
  - [x] 6.1 Add token storage and refresh logic
    - Store Google tokens securely in database
    - Implement token refresh when access tokens expire
    - Handle token refresh errors gracefully
    - _Requirements: 3.4, 3.5, 5.2_
  
  - [x] 6.2 Write property test for token management
    - **Property 4: Secure Token Management**
    - **Validates: Requirements 3.4, 3.5, 5.1, 5.2**

- [x] 7. Add environment-specific configuration
  - [x] 7.1 Implement configuration validation
    - Validate required Google OAuth environment variables
    - Support localhost URIs in development mode
    - Enforce HTTPS URIs in production mode
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x] 7.2 Write property test for environment configuration
    - **Property 9: Environment-Specific Security**
    - **Validates: Requirements 7.4, 7.5**

- [x] 8. Integration and UI updates
  - [x] 8.1 Add Google sign-in button to login page
    - Integrate GoogleSignInButton into existing login form
    - Position alongside existing SoundCloud and email/password options
    - Ensure consistent styling and user experience
    - _Requirements: 4.1_
  
  - [x] 8.2 Add Google OAuth callback route
    - Add route for `/auth/google/callback` in React Router
    - Wire up GoogleCallbackPage component
    - Handle authentication completion and redirects
    - _Requirements: 4.3, 4.4_
  
  - [x] 8.3 Write integration tests
    - Test complete OAuth flow from button click to authentication
    - Test error scenarios and user feedback
    - Test account linking and creation scenarios

- [x] 9. Final checkpoint - Complete implementation
  - Ensure all tests pass, verify OAuth flow works end-to-end, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- Integration tests ensure the complete OAuth flow works as expected
- Environment variables needed: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI