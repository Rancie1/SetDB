/**
 * UI store using Zustand.
 * 
 * Manages UI state like modals, notifications, and theme.
 */

import { create } from 'zustand';

const useUIStore = create((set) => ({
  // State
  theme: 'light',
  sidebarOpen: false,
  modalOpen: false,
  currentModal: null,
  notifications: [],

  // Actions
  toggleTheme: () => {
    set((state) => ({
      theme: state.theme === 'light' ? 'dark' : 'light',
    }));
  },

  openModal: (modalName) => {
    set({
      modalOpen: true,
      currentModal: modalName,
    });
  },

  closeModal: () => {
    set({
      modalOpen: false,
      currentModal: null,
    });
  },

  showNotification: (message, type = 'info') => {
    const id = Date.now();
    const notification = { id, message, type };
    
    set((state) => ({
      notifications: [...state.notifications, notification],
    }));

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      set((state) => ({
        notifications: state.notifications.filter((n) => n.id !== id),
      }));
    }, 5000);

    return id;
  },

  dismissNotification: (id) => {
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    }));
  },
}));

export default useUIStore;


