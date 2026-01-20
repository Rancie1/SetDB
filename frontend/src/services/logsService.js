/**
 * Logs service functions.
 * 
 * Handles all log-related API calls (marking sets as seen).
 */

import api from './api';

export const logSet = async (setId, watchedDate) => {
  return api.post('/logs', {
    set_id: setId,
    watched_date: watchedDate || new Date().toISOString().split('T')[0], // Default to today
  });
};

export const updateLog = async (logId, watchedDate) => {
  return api.put(`/logs/${logId}`, {
    watched_date: watchedDate,
  });
};

export const deleteLog = async (logId) => {
  return api.delete(`/logs/${logId}`);
};

export const getUserTopSets = async (userId) => {
  return api.get(`/logs/users/${userId}/top-sets`);
};

export const setTopSet = async (logId, order) => {
  return api.post(`/logs/${logId}/set-top`, null, {
    params: { order },
  });
};

export const unsetTopSet = async (logId) => {
  return api.delete(`/logs/${logId}/unset-top`);
};

export const getUserLogs = async (userId, page = 1, limit = 20, sourceType = null) => {
  const params = { page, limit };
  if (sourceType) {
    params.source_type = sourceType;
  }
  return api.get(`/logs/users/${userId}`, { params });
};

export const getSetLog = async (setId) => {
  // Note: There's no direct endpoint to get a log for a specific set
  // We'll need to check if the user has logged this set via their user logs
  // For now, this is a placeholder
  return null;
};
