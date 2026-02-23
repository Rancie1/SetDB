import api from './api';

export const listArtists = async (query = '', page = 1, limit = 20) => {
  const params = { page, limit };
  if (query) params.query = query;
  return api.get('/artists', { params });
};

export const getArtist = async (artistId) => {
  return api.get(`/artists/${artistId}`);
};

export const getArtistByName = async (name) => {
  return api.get(`/artists/by-name/${encodeURIComponent(name)}`);
};

export const updateArtist = async (artistId, data) => {
  return api.put(`/artists/${artistId}`, data);
};
