/**
 * Ratings service functions.
 * 
 * Handles all rating-related API calls.
 */

import api from './api';

export const createRating = async (ratingData) => {
  return api.post('/ratings', ratingData);
};

export const updateRating = async (ratingId, ratingData) => {
  return api.put(`/ratings/${ratingId}`, ratingData);
};

export const deleteRating = async (ratingId) => {
  return api.delete(`/ratings/${ratingId}`);
};

export const getSetRatingStats = async (setId) => {
  return api.get(`/ratings/sets/${setId}/stats`);
};

export const getMyRating = async (setId) => {
  return api.get(`/ratings/sets/${setId}/my-rating`);
};
