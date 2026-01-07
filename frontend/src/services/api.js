/**
 * Axios instance with interceptors for JWT authentication.
 * 
 * This sets up the base API client that all service functions will use.
 * It automatically adds the JWT token to requests and handles errors.
 */

import axios from 'axios';
import { API_URL } from '../utils/constants';

// Create axios instance with base URL
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add JWT token to all requests
api.interceptors.request.use(
  (config) => {
    // Get token from localStorage (set by auth store)
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor: Handle errors globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 (unauthorized) - token expired or invalid
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    
    // Return error for component-level handling
    return Promise.reject(error);
  }
);

export default api;


