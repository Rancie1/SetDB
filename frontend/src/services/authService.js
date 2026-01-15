/**
 * Authentication service functions.
 * 
 * Handles all authentication-related API calls.
 */

import api from './api';

export const login = async (email, password) => {
  // FastAPI OAuth2PasswordRequestForm expects form data
  const formData = new FormData();
  formData.append('username', email); // Can be email or username
  formData.append('password', password);
  
  return api.post('/auth/login', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const register = async (userData) => {
  return api.post('/auth/register', userData);
};

export const getCurrentUser = async () => {
  return api.get('/auth/me');
};

export const updateProfile = async (userData) => {
  return api.put('/users/me', userData);
};

export const getSoundCloudAuthUrl = async () => {
  return api.get('/auth/soundcloud/authorize');
};

export const soundCloudCallback = async (code, state) => {
  return api.post('/auth/soundcloud/callback', null, {
    params: { code, state },
  });
};


