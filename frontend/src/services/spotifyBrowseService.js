/**
 * Spotify Browse service functions.
 * 
 * Handles API calls for browsing Spotify's catalog:
 * genres, recommendations, new releases, and artist top tracks.
 */

import api from './api';

export const getGenres = async () => {
  return api.get('/spotify/browse/genres');
};

export const getRecommendations = async ({ seedTracks, seedArtists, seedGenres, limit = 20 } = {}) => {
  const params = { limit };
  if (seedTracks) params.seed_tracks = seedTracks;
  if (seedArtists) params.seed_artists = seedArtists;
  if (seedGenres) params.seed_genres = seedGenres;
  return api.get('/spotify/browse/recommendations', { params });
};

export const getNewReleases = async (limit = 20, offset = 0) => {
  return api.get('/spotify/browse/new-releases', { params: { limit, offset } });
};

export const getArtistTopTracks = async (artistId) => {
  return api.get(`/spotify/browse/artist/${artistId}/top-tracks`);
};

export const getSpotifyTrack = async (trackId) => {
  return api.get(`/spotify/browse/track/${trackId}`);
};
