/**
 * Sets service functions.
 * 
 * Handles all DJ set-related API calls.
 */

import api from './api';

export const getSets = async (filters = {}, page = 1, limit = 20) => {
  const params = {
    page,
    limit,
    ...filters,
  };
  return api.get('/sets', { params });
};

export const getSet = async (id) => {
  return api.get(`/sets/${id}`);
};

export const createSet = async (setData) => {
  return api.post('/sets', setData);
};

export const importSetFromYouTube = async (url, markAsLive = false) => {
  return api.post('/sets/import/youtube', { url, mark_as_live: markAsLive });
};

export const importSetFromSoundCloud = async (url, markAsLive = false) => {
  return api.post('/sets/import/soundcloud', { url, mark_as_live: markAsLive });
};

// Auto-detect platform and import
export const importSet = async (url, markAsLive = false) => {
  const isYouTube = url.includes('youtube.com') || url.includes('youtu.be');
  const endpoint = isYouTube ? '/sets/import/youtube' : '/sets/import/soundcloud';
  return api.post(endpoint, { url, mark_as_live: markAsLive });
};

export const updateSet = async (id, setData) => {
  return api.put(`/sets/${id}`, setData);
};

export const deleteSet = async (id) => {
  return api.delete(`/sets/${id}`);
};

export const markSetAsLive = async (setId) => {
  return api.post(`/sets/${setId}/mark-as-live`);
};

// Event-related functions moved to eventsService.js
// Use eventsService for all event operations


