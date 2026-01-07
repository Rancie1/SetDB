/**
 * Users service functions.
 * 
 * Handles all user-related API calls.
 */

import api from './api';

export const getUser = async (id) => {
  return api.get(`/users/${id}`);
};

export const getUserStats = async (id) => {
  return api.get(`/users/${id}/stats`);
};

export const updateProfile = async (userData) => {
  return api.put('/users/me', userData);
};

export const followUser = async (userId) => {
  return api.post(`/users/${userId}/follow`);
};

export const unfollowUser = async (userId) => {
  return api.delete(`/users/${userId}/follow`);
};

export const getUserFeed = async (page = 1, limit = 20) => {
  return api.get('/users/me/feed', {
    params: { page, limit },
  });
};

export const getUserLogs = async (userId, page = 1, limit = 20) => {
  return api.get(`/logs/users/${userId}`, {
    params: { page, limit },
  });
};


