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

export const searchUsers = async (searchQuery, page = 1, limit = 20) => {
  return api.get('/users', {
    params: { search: searchQuery, page, limit },
  });
};

export const getFollowStatus = async (userId) => {
  return api.get(`/users/${userId}/follow-status`);
};

export const getMyFriends = async (page = 1, limit = 20) => {
  return api.get('/users/me/friends', {
    params: { page, limit },
  });
};

export const getUserTopTracks = async (userId) => {
  return api.get(`/users/${userId}/top-tracks`);
};

export const getUserTopEvents = async (userId) => {
  return api.get(`/users/${userId}/top-events`);
};

export const getUserTopVenues = async (userId) => {
  return api.get(`/users/${userId}/top-venues`);
};

export const addTopEvent = async (eventId, order) => {
  return api.post('/users/me/top-events', null, {
    params: { event_id: eventId, order },
  });
};

export const removeTopEvent = async (eventId) => {
  return api.delete(`/users/me/top-events/${eventId}`);
};

export const addTopVenue = async (venueId, order) => {
  return api.post('/users/me/top-venues', null, {
    params: { venue_id: venueId, order },
  });
};

export const removeTopVenue = async (venueId) => {
  return api.delete(`/users/me/top-venues/${venueId}`);
};

export const getActivityFeed = async (page = 1, limit = 20, friendsOnly = false) => {
  return api.get('/users/activity-feed', {
    params: { page, limit, friends_only: friendsOnly },
  });
};


