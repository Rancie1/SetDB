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

export const confirmTrack = async (setId, trackId, confirmationData) => {
  return api.post(`/sets/${setId}/tracks/${trackId}/confirm`, confirmationData);
};

export const removeTrackConfirmation = async (setId, trackId) => {
  return api.delete(`/sets/${setId}/tracks/${trackId}/confirm`);
};
