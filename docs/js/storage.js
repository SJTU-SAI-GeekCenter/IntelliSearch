/**
 * Storage management for the AI Chat Application
 * @fileoverview LocalStorage operations and data persistence
 */

import { CONFIG } from './config.js';
import { appState } from './config.js';
import { generateRandomId } from './utils.js';

/**
 * Save chats to localStorage
 */
export function saveChats() {
    try {
        localStorage.setItem(CONFIG.STORAGE_KEYS.CHATS, JSON.stringify(appState.chats));
    } catch (error) {
        console.error('Failed to save chats:', error);
    }
}

/**
 * Load chats from localStorage
 * @returns {Array} Array of chat objects
 */
export function loadChats() {
    try {
        const saved = localStorage.getItem(CONFIG.STORAGE_KEYS.CHATS);
        return saved ? JSON.parse(saved) : [];
    } catch (error) {
        console.error('Failed to load chats:', error);
        return [];
    }
}

/**
 * Save settings to localStorage
 */
export function saveSettings() {
    try {
        localStorage.setItem(CONFIG.STORAGE_KEYS.SETTINGS, JSON.stringify(appState.settings));
    } catch (error) {
        console.error('Failed to save settings:', error);
    }
}

/**
 * Load settings from localStorage
 * @returns {Object} Settings object
 */
export function loadSettings() {
    try {
        const saved = localStorage.getItem(CONFIG.STORAGE_KEYS.SETTINGS);
        return saved ? JSON.parse(saved) : { ...CONFIG.DEFAULT_SETTINGS };
    } catch (error) {
        console.error('Failed to load settings:', error);
        return { ...CONFIG.DEFAULT_SETTINGS };
    }
}

/**
 * Calculate storage usage
 * @returns {string} Formatted storage size
 */
export function getStorageUsage() {
    let totalSize = 0;
    try {
        const data = localStorage.getItem(CONFIG.STORAGE_KEYS.CHATS);
        if (data) {
            totalSize = new Blob([data]).size;
        }
    } catch (error) {
        console.error('Failed to calculate storage usage:', error);
    }

    return totalSize > 1024 ?
        `${(totalSize / 1024).toFixed(2)} KB` :
        `${totalSize} B`;
}

/**
 * Clear all application data from localStorage
 */
export function clearAllData() {
    try {
        localStorage.removeItem(CONFIG.STORAGE_KEYS.CHATS);
        localStorage.removeItem(CONFIG.STORAGE_KEYS.SETTINGS);
    } catch (error) {
        console.error('Failed to clear data:', error);
    }
}

/**
 * Export chat data as JSON
 * @param {Object} chat - Chat object to export
 * @returns {string} JSON string of the chat
 */
export function exportChat(chat) {
    const exportData = {
        title: chat.name,
        messages: chat.messages,
        exportDate: new Date().toISOString(),
        totalMessages: chat.messages.length,
        version: '1.0'
    };
    return JSON.stringify(exportData, null, 2);
}

/**
 * Import chat data from JSON
 * @param {string} json - JSON string of chat data
 * @returns {Object|null} Imported chat object or null if invalid
 */
export function importChat(json) {
    try {
        const data = JSON.parse(json);

        // Validate data structure
        if (!data.title || !Array.isArray(data.messages)) {
            throw new Error('Invalid chat data format');
        }

        return {
            id: generateRandomId(),
            name: data.title,
            messages: data.messages.filter(msg =>
                msg.role === 'user' || msg.role === 'assistant' || msg.role === 'system'
            )
        };
    } catch (error) {
        console.error('Failed to import chat:', error);
        return null;
    }
}

/**
 * Get storage statistics
 * @returns {Object} Storage statistics
 */
export function getStorageStats() {
    const chatData = localStorage.getItem(CONFIG.STORAGE_KEYS.CHATS);
    const settingsData = localStorage.getItem(CONFIG.STORAGE_KEYS.SETTINGS);

    return {
        chatSize: chatData ? new Blob([chatData]).size : 0,
        settingsSize: settingsData ? new Blob([settingsData]).size : 0,
        totalSize: (chatData ? new Blob([chatData]).size : 0) +
                  (settingsData ? new Blob([settingsData]).size : 0),
        chatCount: appState.chats.length,
        totalMessages: appState.chats.reduce((sum, chat) => sum + chat.messages.length, 0)
    };
}