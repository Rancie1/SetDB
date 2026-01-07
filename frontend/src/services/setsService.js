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

export const importSetFromYouTube = async (url) => {
  return api.post('/sets/import/youtube', { url });
};

export const importSetFromSoundCloud = async (url) => {
  return api.post('/sets/import/soundcloud', { url });
};

// Auto-detect platform and import
export const importSet = async (url) => {
  const isYouTube = url.includes('youtube.com') || url.includes('youtu.be');
  const endpoint = isYouTube ? '/sets/import/youtube' : '/sets/import/soundcloud';
  return api.post(endpoint, { url });
};

export const updateSet = async (id, setData) => {
  return api.put(`/sets/${id}`, setData);
};

export const deleteSet = async (id) => {
  return api.delete(`/sets/${id}`);
};


