/**
 * Reviews service functions.
 * 
 * Handles all review-related API calls.
 */

import api from './api';

export const getUserReviews = async (userId, page = 1, limit = 20) => {
  return api.get(`/reviews/users/${userId}`, { params: { page, limit } });
};

export const getSetReviews = async (setId, page = 1, limit = 20) => {
  return api.get(`/reviews/sets/${setId}`, {
    params: { page, limit }
  });
};

export const getReview = async (reviewId) => {
  return api.get(`/reviews/${reviewId}`);
};

export const createReview = async (reviewData) => {
  return api.post('/reviews', reviewData);
};

export const updateReview = async (reviewId, reviewData) => {
  return api.put(`/reviews/${reviewId}`, reviewData);
};

export const deleteReview = async (reviewId) => {
  return api.delete(`/reviews/${reviewId}`);
};
