/**
 * Track Ratings service functions.
 * 
 * Handles all track rating-related API calls.
 */

import api from './api';

export const createTrackRating = async (trackId, rating) => {
  return api.post(`/tracks/${trackId}/ratings`, {
    track_id: trackId,
    rating,
  });
};

export const updateTrackRating = async (trackId, ratingId, rating) => {
  return api.put(`/tracks/${trackId}/ratings/${ratingId}`, { rating });
};

export const deleteTrackRating = async (trackId, ratingId) => {
  return api.delete(`/tracks/${trackId}/ratings/${ratingId}`);
};

export const getTrackRatingStats = async (trackId) => {
  return api.get(`/tracks/${trackId}/ratings/stats`);
};
