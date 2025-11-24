/**
 * Configuration constants and settings for the AI Chat Application
 * @fileoverview Central configuration management
 */

// Application Configuration
export const CONFIG = {
  // Storage keys
  STORAGE_KEYS: {CHATS: 'xj_ai_chats_v1', SETTINGS: 'xj_ai_settings_v1'},

  // Default settings
  DEFAULT_SETTINGS: {
    fontSize: 14,
    responseSpeed: 'normal',
    typewriter: true,
    sound: false,
    autoSave: true
  },

  // Backend configuration
  BACKEND_URL: 'http://localhost:8000',

  // Animation timing
  ANIMATION: {
    LOADING_DURATION: 2500,
    FADE_DURATION: 800,
    TYPING_DELAY: 30,
    THINKING_DELAY: 1000
  },

  // UI Constants
  UI: {
    MAX_SIDEBAR_WIDTH: 280,
    MESSAGE_MAX_WIDTH: 70,
    PARTICLE_COUNT: 50,
    CANVAS_REFRESH_RATE: 60
  }
};

// Application state management
export class AppState {
  constructor() {
    this.chats = [];
    this.currentChatId = null;
    this.settings = {...CONFIG.DEFAULT_SETTINGS};
    this.isTypewriterEnabled = true;
    this.isLoading = false;
  }

  /**
   * Get the currently active chat
   * @returns {Object|null} Current chat object or null
   */
  getCurrentChat() {
    return this.chats.find(chat => chat.id === this.currentChatId);
  }

  /**
   * Update application settings
   * @param {Object} newSettings - New settings to merge
   */
  updateSettings(newSettings) {
    this.settings = {...this.settings, ...newSettings};
    this.isTypewriterEnabled = this.settings.typewriter;
  }
}

// Global application instance
export const appState = new AppState();