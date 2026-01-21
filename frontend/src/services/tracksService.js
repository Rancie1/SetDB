/**
 * Tracks service functions.
 * 
 * Handles all track tag-related API calls.
 */

import api from './api';

export const getSetTracks = async (setId) => {
  return api.get(`/sets/${setId}/tracks`);
};

export const addTrackTag = async (setId, trackData) => {
  return api.post(`/sets/${setId}/tracks`, trackData);
};

export const updateTrackTag = async (setId, trackId, trackData) => {
  return api.put(`/sets/${setId}/tracks/${trackId}`, trackData);
};

export const removeTrackTag = async (setId, trackId) => {
  return api.delete(`/sets/${setId}/tracks/${trackId}`);
};

export const searchSoundCloud = async (query, limit = 10) => {
  return api.get(`/tracks/search/soundcloud`, {
    params: { query, limit },
  });
};

export const searchSpotify = async (query, limit = 10) => {
  return api.get(`/tracks/search/spotify`, {
    params: { query, limit },
  });
};

export const searchTracks = async (query, platform = 'all', limit = 10) => {
  return api.get(`/tracks/search`, {
    params: { query, platform, limit },
  });
};

export const resolveTrackUrl = async (url) => {
  return api.get(`/tracks/resolve-url`, {
    params: { url },
  });
};

export const confirmTrack = async (setId, trackId, confirmationData) => {
  return api.post(`/sets/${setId}/tracks/${trackId}/confirm`, confirmationData);
};

export const removeTrackConfirmation = async (setId, trackId) => {
  return api.delete(`/sets/${setId}/tracks/${trackId}/confirm`);
};

export const setTopTrack = async (setId, trackId, order) => {
  return api.post(`/sets/${setId}/tracks/${trackId}/set-top`, null, {
    params: { order },
  });
};

export const unsetTopTrack = async (setId, trackId) => {
  return api.delete(`/sets/${setId}/tracks/${trackId}/unset-top`);
};

export const discoverTracks = async (filters = {}, page = 1, limit = 20) => {
  const params = {
    page,
    limit,
    ...filters,
  };
  return api.get('/tracks', { params });
};
