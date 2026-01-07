/**
 * Authentication store using Zustand.
 * 
 * Manages user authentication state, login, logout, and token management.
 */

import { create } from 'zustand';
import api from '../services/api';
import * as authService from '../services/authService';

const useAuthStore = create((set, get) => ({
  // State
  user: JSON.parse(localStorage.getItem('user')) || null,
  token: localStorage.getItem('token') || null,
  loading: false,
  error: null,

  // Computed
  isAuthenticated: () => {
    return !!get().token && !!get().user;
  },

  // Actions
  login: async (email, password) => {
    set({ loading: true, error: null });
    try {
      const response = await authService.login(email, password);
      const { access_token } = response.data;
      
      // Get user info
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      const userResponse = await authService.getCurrentUser();
      const user = userResponse.data;
      
      // Store token and user
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      
      set({
        token: access_token,
        user: user,
        loading: false,
        error: null,
      });
      
      return { success: true };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Login failed';
      set({
        loading: false,
        error: errorMessage,
      });
      return { success: false, error: errorMessage };
    }
  },

  register: async (userData) => {
    set({ loading: true, error: null });
    try {
      const response = await authService.register(userData);
      const user = response.data;
      
      set({
        user: user,
        loading: false,
        error: null,
      });
      
      return { success: true, user };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Registration failed';
      set({
        loading: false,
        error: errorMessage,
      });
      return { success: false, error: errorMessage };
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete api.defaults.headers.common['Authorization'];
    set({
      user: null,
      token: null,
      error: null,
    });
  },

  updateUser: (userData) => {
    const updatedUser = { ...get().user, ...userData };
    localStorage.setItem('user', JSON.stringify(updatedUser));
    set({ user: updatedUser });
  },

  checkAuth: async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      return;
    }

    set({ loading: true });
    try {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      const response = await authService.getCurrentUser();
      const user = response.data;
      
      localStorage.setItem('user', JSON.stringify(user));
      set({
        user: user,
        token: token,
        loading: false,
      });
    } catch (error) {
      // Token is invalid, clear it
      get().logout();
      set({ loading: false });
    }
  },

  clearError: () => {
    set({ error: null });
  },
}));

export default useAuthStore;
