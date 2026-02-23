/**
 * Spotify OAuth callback page.
 * 
 * Handles the redirect from Spotify after user authorization.
 * Extracts the authorization code and state, then exchanges them for a token.
 */

import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import useAuthStore from '../store/authStore';

const SpotifyCallbackPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { handleSpotifyCallback, error, isAuthenticated } = useAuthStore();
  const [status, setStatus] = useState('Processing...');
  const [debugInfo, setDebugInfo] = useState('');
  const [hasProcessed, setHasProcessed] = useState(false);

  useEffect(() => {
    if (hasProcessed) return;
    setHasProcessed(true);
    
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const errorParam = searchParams.get('error');
    const errorDescription = searchParams.get('error_description');
    
    const params = {
      code: code ? 'present' : 'missing',
      state: state ? 'present' : 'missing',
      error: errorParam || 'none',
      errorDescription: errorDescription || 'none',
      fullUrl: window.location.href
    };
    setDebugInfo(JSON.stringify(params, null, 2));
    console.log('Spotify Callback Params:', params);

    if (errorParam) {
      const errorMsg = errorDescription || errorParam;
      setStatus(`OAuth Error: ${errorMsg}`);
      console.error('Spotify OAuth Error:', errorParam, errorDescription);
      setTimeout(() => navigate('/login'), 3000);
      return;
    }

    if (!code || !state) {
      const missing = [];
      if (!code) missing.push('code');
      if (!state) missing.push('state');
      setStatus(`Missing required parameters: ${missing.join(', ')}`);
      console.error('Missing parameters:', { code: !!code, state: !!state });
      setTimeout(() => navigate('/login'), 3000);
      return;
    }

    const completeLogin = async () => {
      try {
        setStatus('Completing login...');
        console.log('Calling handleSpotifyCallback with:', { code: code.substring(0, 10) + '...', state });
        const result = await handleSpotifyCallback(code, state);
        
        if (result.success || isAuthenticated()) {
          setStatus('Login successful! Redirecting...');
          setTimeout(() => navigate('/', { replace: true }), 500);
        } else {
          setStatus(`Login failed: ${result.error || 'Unknown error'}`);
          console.error('Login failed:', result);
          setTimeout(() => navigate('/login', { replace: true }), 3000);
        }
      } catch (err) {
        if (isAuthenticated()) {
          setStatus('Login successful! Redirecting...');
          setTimeout(() => navigate('/', { replace: true }), 500);
          return;
        }
        
        const errorMsg = err.message || 'An unexpected error occurred';
        setStatus(`Error: ${errorMsg}`);
        console.error('Exception in completeLogin:', err);
        setTimeout(() => navigate('/login', { replace: true }), 3000);
      }
    };

    completeLogin();
  }, [searchParams, navigate, handleSpotifyCallback, hasProcessed, isAuthenticated]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
        <div className="mb-4">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
        </div>
        <h2 className="text-xl font-semibold text-gray-800 mb-2">Spotify Login</h2>
        <p className="text-gray-600 mb-4">{status}</p>
        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            <p className="font-semibold">Error:</p>
            <p>{error}</p>
          </div>
        )}
        {process.env.NODE_ENV === 'development' && debugInfo && (
          <details className="mt-4 text-left">
            <summary className="cursor-pointer text-sm text-gray-500">Debug Info</summary>
            <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-auto max-h-40">
              {debugInfo}
            </pre>
          </details>
        )}
      </div>
    </div>
  );
};

export default SpotifyCallbackPage;
