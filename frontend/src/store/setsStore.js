/**
 * Sets store using Zustand.
 * 
 * Manages DJ sets state, fetching, and filtering.
 */

import { create } from 'zustand';
import * as setsService from '../services/setsService';

const useSetsStore = create((set, get) => ({
  // State
  sets: [],
  currentSet: null,
  filters: {
    search: '',
    source_type: null,
    dj_name: null,
    sort: 'created_at',
  },
  pagination: {
    page: 1,
    limit: 20,
    total: 0,
    pages: 0,
  },
  loading: false,
  error: null,

  // Actions
  fetchSets: async (filters = {}, page = 1, limit = 20) => {
    set({ loading: true, error: null });
    try {
      const mergedFilters = { ...get().filters, ...filters };
      const response = await setsService.getSets(mergedFilters, page, limit);
      const { items, total, pages } = response.data;
      
      set({
        sets: items,
        filters: mergedFilters,
        pagination: {
          page,
          limit,
          total,
          pages,
        },
        loading: false,
        error: null,
      });
    } catch (error) {
      set({
        loading: false,
        error: error.response?.data?.detail || 'Failed to fetch sets',
      });
    }
  },

  fetchSet: async (id) => {
    set({ loading: true, error: null });
    try {
      const response = await setsService.getSet(id);
      set({
        currentSet: response.data,
        loading: false,
        error: null,
      });
    } catch (error) {
      set({
        loading: false,
        error: error.response?.data?.detail || 'Failed to fetch set',
      });
    }
  },

  importSet: async (url, markAsLive = false) => {
    set({ loading: true, error: null });
    try {
      const response = await setsService.importSet(url, markAsLive);
      // Refresh sets list after import (or events list if marked as live)
      if (markAsLive) {
        // If marked as live, it will appear in sets (since live sets appear on discover page)
        await get().fetchSets();
      } else {
        await get().fetchSets();
      }
      set({
        loading: false,
        error: null,
      });
      return { success: true, data: response.data };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to import set';
      set({
        loading: false,
        error: errorMessage,
      });
      return { success: false, error: errorMessage };
    }
  },

  clearError: () => {
    set({ error: null });
  },

  clearCurrentSet: () => {
    set({ currentSet: null });
  },
}));

export default useSetsStore;


