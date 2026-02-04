/**
 * Venues service – list, search, create venues (for top 5).
 */

import api from './api';

export const getVenues = async (params = {}) => {
  const { data } = await api.get('/venues', { params });
  return data;
};

export const searchVenues = async (search, page = 1, limit = 20) => {
  const { data } = await api.get('/venues', {
    params: { search: search || undefined, page, limit },
  });
  return data;
};

export const getVenue = async (id) => {
  const { data } = await api.get(`/venues/${id}`);
  return data;
};

export const createVenue = async (payload) => {
  const { data } = await api.post('/venues', payload);
  return data;
};
