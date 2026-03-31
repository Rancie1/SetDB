/**
 * Events service functions.
 * 
 * Handles all event-related API calls.
 */

import api from './api';

export const getEvents = async (filters = {}, page = 1, limit = 20) => {
  const params = {
    page,
    limit,
    ...filters,
  };
  return api.get('/events', { params });
};

export const getEvent = async (id) => {
  return api.get(`/events/${id}`);
};

export const createEvent = async (eventData) => {
  return api.post('/events', eventData);
};

export const updateEvent = async (id, eventData) => {
  return api.put(`/events/${id}`, eventData);
};

export const deleteEvent = async (id) => {
  return api.delete(`/events/${id}`);
};

export const getEventLinkedSets = async (eventId, page = 1, limit = 20) => {
  return api.get(`/events/${eventId}/linked-sets`, { params: { page, limit } });
};

export const linkSetToEvent = async (eventId, setId) => {
  return api.post(`/events/${eventId}/link-set/${setId}`);
};

export const unlinkSetFromEvent = async (eventId, setId) => {
  return api.delete(`/events/${eventId}/link-set/${setId}`);
};

export const confirmEvent = async (eventId) => {
  return api.post(`/events/${eventId}/confirm`);
};

export const unconfirmEvent = async (eventId) => {
  return api.delete(`/events/${eventId}/confirm`);
};

export const createEventFromSet = async (setId, eventData = {}) => {
  return api.post(`/events/create-from-set/${setId}`, eventData);
};

export const getUserConfirmedEvents = async (userId, page = 1, limit = 20) => {
  return api.get(`/events/users/${userId}/confirmed`, {
    params: { page, limit },
  });
};

// Discovery — Search (no auth required)
export const searchRAEvents = (keyword, location, dateFrom, dateTo, page = 1, limit = 20) =>
  api.get('/events/search/ra', { params: { keyword, location, date_from: dateFrom, date_to: dateTo, page, limit } });

export const searchTicketmasterEvents = (keyword, city, countryCode, page = 0, limit = 20) =>
  api.get('/events/search/ticketmaster', { params: { keyword, city, country_code: countryCode, page, limit } });

export const searchSkiddleEvents = (keyword, lat, lng, radius = 10, dateFrom, dateTo, limit = 20, offset = 0) =>
  api.get('/events/search/skiddle', { params: { keyword, lat, lng, radius, date_from: dateFrom, date_to: dateTo, limit, offset } });

// Discovery — Import (auth required)
export const importRAEvent = (raId, raEventId) => api.post('/events/import/ra', { ra_id: raId, ra_event_id: raEventId || raId });

export const importTicketmasterEvent = (tmId) => api.post('/events/import/ticketmaster', { ticketmaster_id: tmId });

export const importSkiddleEvent = (skiddleId) => api.post('/events/import/skiddle', { skiddle_id: skiddleId });
