/**
 * Standalone Tracks service functions.
 * 
 * Handles all independent track-related API calls.
 */

import api from './api';

export const createTrack = async (trackData) => {
  return api.post('/tracks', trackData);
};

export const getTrack = async (trackId) => {
  return api.get(`/tracks/${trackId}`);
};

export const linkTrackToSet = async (trackId, linkData) => {
  return api.post(`/tracks/${trackId}/link-to-set`, linkData);
};

export const unlinkTrackFromSet = async (trackId, setId) => {
  return api.delete(`/tracks/${trackId}/link-to-set/${setId}`);
};

export const getTrackLinkedSets = async (trackId) => {
  return api.get(`/tracks/${trackId}/linked-sets`);
};

export const setTopTrack = async (trackId, order) => {
  return api.post(`/tracks/${trackId}/set-top`, null, {
    params: { order },
  });
};

export const unsetTopTrack = async (trackId) => {
  return api.delete(`/tracks/${trackId}/unset-top`);
};
