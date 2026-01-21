/**
 * Track Reviews service functions.
 * 
 * Handles all track review-related API calls.
 */

import api from './api';

export const getTrackReviews = async (trackId, page = 1, limit = 20) => {
  return api.get(`/tracks/${trackId}/reviews`, {
    params: { page, limit }
  });
};

export const createTrackReview = async (trackId, reviewData) => {
  return api.post(`/tracks/${trackId}/reviews`, {
    track_id: trackId,
    ...reviewData,
  });
};

export const updateTrackReview = async (trackId, reviewId, reviewData) => {
  return api.put(`/tracks/${trackId}/reviews/${reviewId}`, reviewData);
};

export const deleteTrackReview = async (trackId, reviewId) => {
  return api.delete(`/tracks/${trackId}/reviews/${reviewId}`);
};
