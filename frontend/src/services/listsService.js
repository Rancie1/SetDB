/**
 * Lists service functions.
 * 
 * Handles all list-related API calls.
 */

import api from './api';

export const getLists = async (page = 1, limit = 20, userId = null, isPublic = null) => {
  const params = { page, limit };
  if (userId) params.user_id = userId;
  if (isPublic !== null) params.is_public = isPublic;
  return api.get('/lists', { params });
};

export const getList = async (listId) => {
  return api.get(`/lists/${listId}`);
};

export const createList = async (listData) => {
  return api.post('/lists', listData);
};

export const updateList = async (listId, listData) => {
  return api.put(`/lists/${listId}`, listData);
};

export const deleteList = async (listId) => {
  return api.delete(`/lists/${listId}`);
};

export const addItemToList = async (listId, itemData) => {
  return api.post(`/lists/${listId}/items`, itemData);
};

export const updateListItem = async (listId, itemId, itemData) => {
  return api.put(`/lists/${listId}/items/${itemId}`, itemData);
};

export const removeItemFromList = async (listId, itemId) => {
  return api.delete(`/lists/${listId}/items/${itemId}`);
};
