/**
 * Property-Based Tests for Google OAuth Frontend Authentication
 * 
 * Feature: google-oauth-authentication
 * Property 7: Frontend Authentication State
 * 
 * **Validates: Requirements 4.2, 4.3, 4.4, 4.5, 6.5**
 * 
 * For any successful Google OAuth authentication, the frontend authentication 
 * store must be updated with user information and JWT token, and the UI must 
 * reflect the authenticated state immediately.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { renderHook, act } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import * as fc from 'fast-check';
import useAuthStore from '../store/authStore';
import * as authService from '../services/authService';
import LoginForm from '../components/auth/LoginForm';
import GoogleCallbackPage from '../pages/GoogleCallbackPage';

// Mock the authService
vi.mock('../services/authService', () => ({
  getGoogleAuthUrl: vi.fn(),
  googleCallback: vi.fn(),
  getCurrentUser: vi.fn(),
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.localStorage = localStorageMock;

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.sessionStorage = sessionStorageMock;

// Mock window.location
delete window.location;
window.location = { href: '' };

// Mock URLSearchParams for callback page testing
const mockSearchParams = new Map();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useSearchParams: () => [mockSearchParams],
    useNavigate: () => vi.fn(),
  };
});

describe('Property 7: Frontend Authentication State', () => {
  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    sessionStorageMock.getItem.mockReturnValue(null);
    
    // Reset the store
    useAuthStore.setState({
      user: null,
      token: null,
      loading: false,
      error: null,
    });
  });

  it('should initiate Google OAuth flow with proper state management', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.record({
          authorization_url: fc.webUrl(),
          state: fc.string({ minLength: 10, maxLength: 50 }),
        }),
        async (mockResponse) => {
          // Mock the API response
          authService.getGoogleAuthUrl.mockResolvedValue({
            data: mockResponse,
          });

          const { result } = renderHook(() => useAuthStore());

          await act(async () => {
            await result.current.loginWithGoogle();
          });

          // Verify state was stored in sessionStorage
          expect(sessionStorageMock.setItem).toHaveBeenCalledWith(
            'google_oauth_state',
            mockResponse.state
          );

          // Verify redirect was initiated
          expect(window.location.href).toBe(mockResponse.authorization_url);
        }
      ),
      { numRuns: 50 }
    );
  });

  it('should handle Google OAuth callback and update authentication state', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.record({
          code: fc.string({ minLength: 10, maxLength: 100 }),
          state: fc.string({ minLength: 10, maxLength: 50 }),
          access_token: fc.string({ minLength: 20, maxLength: 200 }),
          user: fc.record({
            id: fc.integer({ min: 1, max: 10000 }),
            email: fc.emailAddress(),
            username: fc.string({ minLength: 3, maxLength: 20 }),
            display_name: fc.string({ minLength: 1, maxLength: 50 }),
          }),
        }),
        async (testData) => {
          // Mock sessionStorage to return the matching state
          sessionStorageMock.getItem.mockReturnValue(testData.state);

          // Mock API responses
          authService.googleCallback.mockResolvedValue({
            data: { access_token: testData.access_token },
          });
          authService.getCurrentUser.mockResolvedValue({
            data: testData.user,
          });

          const { result } = renderHook(() => useAuthStore());

          await act(async () => {
            const response = await result.current.handleGoogleCallback(
              testData.code,
              testData.state
            );
            expect(response.success).toBe(true);
          });

          // Verify authentication state was updated
          expect(result.current.token).toBe(testData.access_token);
          expect(result.current.user).toEqual(testData.user);
          expect(result.current.isAuthenticated()).toBe(true);
          expect(result.current.loading).toBe(false);
          expect(result.current.error).toBe(null);

          // Verify data was stored in localStorage
          expect(localStorageMock.setItem).toHaveBeenCalledWith(
            'token',
            testData.access_token
          );
          expect(localStorageMock.setItem).toHaveBeenCalledWith(
            'user',
            JSON.stringify(testData.user)
          );

          // Verify state was cleared from sessionStorage
          expect(sessionStorageMock.removeItem).toHaveBeenCalledWith(
            'google_oauth_state'
          );
        }
      ),
      { numRuns: 50 }
    );
  });

  it('should reject authentication with invalid state parameter', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.record({
          code: fc.string({ minLength: 10, maxLength: 100 }),
          validState: fc.string({ minLength: 10, maxLength: 50 }),
          invalidState: fc.string({ minLength: 10, maxLength: 50 }),
        }).filter(data => data.validState !== data.invalidState),
        async (testData) => {
          // Mock sessionStorage to return different state than callback
          sessionStorageMock.getItem.mockReturnValue(testData.validState);

          const { result } = renderHook(() => useAuthStore());

          await act(async () => {
            const response = await result.current.handleGoogleCallback(
              testData.code,
              testData.invalidState
            );
            expect(response.success).toBe(false);
            expect(response.error).toContain('Invalid state parameter');
          });

          // Verify authentication state was not updated
          expect(result.current.token).toBe(null);
          expect(result.current.user).toBe(null);
          expect(result.current.isAuthenticated()).toBe(false);
          expect(result.current.error).toContain('Invalid state parameter');

          // Verify state was cleared even on error
          expect(sessionStorageMock.removeItem).toHaveBeenCalledWith(
            'google_oauth_state'
          );
        }
      ),
      { numRuns: 50 }
    );
  });

  it('should handle API errors gracefully and provide user feedback', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.record({
          errorMessage: fc.string({ minLength: 5, maxLength: 100 }),
          httpStatus: fc.integer({ min: 400, max: 599 }),
        }),
        async (testData) => {
          // Mock API to throw error
          const apiError = new Error(testData.errorMessage);
          apiError.response = {
            data: { detail: testData.errorMessage },
            status: testData.httpStatus,
          };
          authService.getGoogleAuthUrl.mockRejectedValue(apiError);

          const { result } = renderHook(() => useAuthStore());

          await act(async () => {
            const response = await result.current.loginWithGoogle();
            expect(response.success).toBe(false);
            expect(response.error).toBe(testData.errorMessage);
          });

          // Verify error state was set
          expect(result.current.error).toBe(testData.errorMessage);
          expect(result.current.loading).toBe(false);
          expect(result.current.isAuthenticated()).toBe(false);
        }
      ),
      { numRuns: 50 }
    );
  });

  it('should maintain authentication state consistency across operations', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.record({
          initialUser: fc.record({
            id: fc.integer({ min: 1, max: 10000 }),
            email: fc.emailAddress(),
            username: fc.string({ minLength: 3, maxLength: 20 }),
          }),
          initialToken: fc.string({ minLength: 20, maxLength: 200 }),
        }),
        async (testData) => {
          // Set initial authenticated state
          useAuthStore.setState({
            user: testData.initialUser,
            token: testData.initialToken,
            loading: false,
            error: null,
          });

          const { result } = renderHook(() => useAuthStore());

          // Verify initial state
          expect(result.current.isAuthenticated()).toBe(true);
          expect(result.current.user).toEqual(testData.initialUser);
          expect(result.current.token).toBe(testData.initialToken);

          // Test logout clears state
          act(() => {
            result.current.logout();
          });

          expect(result.current.isAuthenticated()).toBe(false);
          expect(result.current.user).toBe(null);
          expect(result.current.token).toBe(null);
          expect(result.current.error).toBe(null);
        }
      ),
      { numRuns: 50 }
    );
  });
});

describe('Integration Tests: Complete Google OAuth Flow', () => {
  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    sessionStorageMock.getItem.mockReturnValue(null);
    mockSearchParams.clear();
    
    // Reset the store
    useAuthStore.setState({
      user: null,
      token: null,
      loading: false,
      error: null,
    });
  });

  it('should complete OAuth flow from button click to authentication', async () => {
    const mockAuthUrl = 'https://accounts.google.com/oauth/authorize?client_id=test';
    const mockState = 'test-state-123';
    const mockCode = 'test-auth-code';
    const mockToken = 'jwt-token-123';
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      username: 'testuser',
      display_name: 'Test User',
    };

    // Mock API responses
    authService.getGoogleAuthUrl.mockResolvedValue({
      data: { authorization_url: mockAuthUrl, state: mockState },
    });
    authService.googleCallback.mockResolvedValue({
      data: { access_token: mockToken },
    });
    authService.getCurrentUser.mockResolvedValue({
      data: mockUser,
    });

    // Render login form
    render(
      <BrowserRouter>
        <LoginForm />
      </BrowserRouter>
    );

    // Find and click Google sign-in button
    const googleButton = screen.getByText('Continue with Google');
    expect(googleButton).toBeInTheDocument();

    fireEvent.click(googleButton);

    // Verify OAuth initiation
    await waitFor(() => {
      expect(authService.getGoogleAuthUrl).toHaveBeenCalled();
      expect(sessionStorageMock.setItem).toHaveBeenCalledWith('google_oauth_state', mockState);
      expect(window.location.href).toBe(mockAuthUrl);
    });

    // Simulate callback with authorization code
    mockSearchParams.set('code', mockCode);
    mockSearchParams.set('state', mockState);
    sessionStorageMock.getItem.mockReturnValue(mockState);

    // Render callback page
    render(
      <BrowserRouter>
        <GoogleCallbackPage />
      </BrowserRouter>
    );

    // Verify callback processing
    await waitFor(() => {
      expect(authService.googleCallback).toHaveBeenCalledWith(mockCode, mockState);
      expect(authService.getCurrentUser).toHaveBeenCalled();
    });

    // Verify final authentication state
    const { result } = renderHook(() => useAuthStore());
    await waitFor(() => {
      expect(result.current.isAuthenticated()).toBe(true);
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.token).toBe(mockToken);
    });
  });

  it('should handle OAuth error scenarios with user feedback', async () => {
    // Test OAuth error from Google
    mockSearchParams.set('error', 'access_denied');
    mockSearchParams.set('error_description', 'User denied access');

    render(
      <BrowserRouter>
        <GoogleCallbackPage />
      </BrowserRouter>
    );

    // Verify error is displayed
    await waitFor(() => {
      expect(screen.getByText(/OAuth Error: User denied access/)).toBeInTheDocument();
    });

    // Test missing parameters
    mockSearchParams.clear();
    mockSearchParams.set('code', 'test-code');
    // Missing state parameter

    render(
      <BrowserRouter>
        <GoogleCallbackPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Missing required parameters: state/)).toBeInTheDocument();
    });
  });

  it('should handle account linking and creation scenarios', async () => {
    const existingUserEmail = 'existing@example.com';
    const newUserEmail = 'new@example.com';

    // Test account linking scenario
    const linkingUser = {
      id: 1,
      email: existingUserEmail,
      username: 'existinguser',
      display_name: 'Existing User',
      google_user_id: 'google123',
    };

    authService.getGoogleAuthUrl.mockResolvedValue({
      data: { authorization_url: 'https://google.com/auth', state: 'state1' },
    });
    authService.googleCallback.mockResolvedValue({
      data: { access_token: 'token1' },
    });
    authService.getCurrentUser.mockResolvedValue({
      data: linkingUser,
    });

    const { result } = renderHook(() => useAuthStore());

    // Simulate OAuth flow for account linking
    await act(async () => {
      await result.current.loginWithGoogle();
    });

    sessionStorageMock.getItem.mockReturnValue('state1');
    await act(async () => {
      const response = await result.current.handleGoogleCallback('code1', 'state1');
      expect(response.success).toBe(true);
    });

    expect(result.current.user.email).toBe(existingUserEmail);
    expect(result.current.user.google_user_id).toBe('google123');

    // Test new account creation scenario
    const newUser = {
      id: 2,
      email: newUserEmail,
      username: 'newuser',
      display_name: 'New User',
      google_user_id: 'google456',
    };

    authService.getGoogleAuthUrl.mockResolvedValue({
      data: { authorization_url: 'https://google.com/auth', state: 'state2' },
    });
    authService.googleCallback.mockResolvedValue({
      data: { access_token: 'token2' },
    });
    authService.getCurrentUser.mockResolvedValue({
      data: newUser,
    });

    // Reset store for new user test
    useAuthStore.setState({
      user: null,
      token: null,
      loading: false,
      error: null,
    });

    await act(async () => {
      await result.current.loginWithGoogle();
    });

    sessionStorageMock.getItem.mockReturnValue('state2');
    await act(async () => {
      const response = await result.current.handleGoogleCallback('code2', 'state2');
      expect(response.success).toBe(true);
    });

    expect(result.current.user.email).toBe(newUserEmail);
    expect(result.current.user.google_user_id).toBe('google456');
  });

  it('should handle network failures and API errors gracefully', async () => {
    // Test network failure during OAuth initiation
    authService.getGoogleAuthUrl.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useAuthStore());

    await act(async () => {
      const response = await result.current.loginWithGoogle();
      expect(response.success).toBe(false);
      expect(response.error).toBe('Failed to initiate Google login');
    });

    expect(result.current.error).toBe('Failed to initiate Google login');
    expect(result.current.isAuthenticated()).toBe(false);

    // Test API error during callback
    const apiError = new Error('API Error');
    apiError.response = {
      data: { detail: 'Invalid authorization code' },
      status: 400,
    };
    authService.googleCallback.mockRejectedValue(apiError);

    sessionStorageMock.getItem.mockReturnValue('valid-state');

    await act(async () => {
      const response = await result.current.handleGoogleCallback('invalid-code', 'valid-state');
      expect(response.success).toBe(false);
      expect(response.error).toBe('Invalid authorization code');
    });

    expect(result.current.error).toBe('Invalid authorization code');
    expect(result.current.isAuthenticated()).toBe(false);
  });
});