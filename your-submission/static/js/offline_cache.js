/**
 * Offline Cache & Underground Tunnel Resilience Controller.
 * Handles localStorage persistence and network status detection.
 */

const STORAGE_KEY = 'rachel_commute_cache';

export const offlineCache = {
  save(data) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch (e) {
      console.warn('LocalStorage save failed:', e);
    }
  },

  load() {
    try {
      const cached = localStorage.getItem(STORAGE_KEY);
      return cached ? JSON.parse(cached) : null;
    } catch (e) {
      console.warn('LocalStorage load failed:', e);
      return null;
    }
  },

  initOfflineListeners(onStatusChange) {
    window.addEventListener('offline', () => onStatusChange(false));
    window.addEventListener('online', () => onStatusChange(true));
  }
};

