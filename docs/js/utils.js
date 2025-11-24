/**
 * Utility functions for the AI Chat Application
 * @fileoverview Common utility functions and helpers
 */

import { CONFIG } from './config.js';

/**
 * Generate a random ID using crypto API or fallback
 * @returns {string} Random unique ID
 */
export function generateRandomId() {
    if (window.crypto && crypto.randomUUID) {
        return crypto.randomUUID();
    }
    return 'id_' + Math.random().toString(36).slice(2) + Date.now().toString(36);
}

/**
 * Escape HTML special characters to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
export function escapeHtml(text) {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

/**
 * Simple markdown renderer for basic formatting
 * @param {string} text - Text to render as markdown
 * @returns {string} HTML representation of markdown
 */
export function renderMarkdown(text) {
    if (!text) return '';

    // Code blocks ```
    text = text.replace(/```([\s\S]*?)```/g, (_, code) => {
        return '<pre><code>' + escapeHtml(code) + '</code></pre>';
    });

    // Inline code
    text = text.replace(/`([^`]+)`/g, (_, code) => {
        return '<code>' + escapeHtml(code) + '</code>';
    });

    // Paragraphs
    const parts = text.split(/\n{2,}/).map(p =>
        '<p>' + p.replace(/\n/g, '<br/>') + '</p>'
    );

    return parts.join('');
}

/**
 * Join URL parts safely
 * @param {string} base - Base URL
 * @param {string} path - Path to join
 * @returns {string} Joined URL
 */
export function joinUrl(base, path) {
    if (!base) return path;
    return base.replace(/\/$/, '') + path;
}

/**
 * Auto-resize textarea based on content
 * @param {HTMLTextAreaElement} textarea - Textarea to resize
 */
export function autosize(textarea) {
    const resize = function () {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(240, textarea.scrollHeight) + 'px';
    };

    textarea.addEventListener('input', resize);
    resize();
}

/**
 * Debounce function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
export function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle function calls
 * @param {Function} func - Function to throttle
 * @param {number} limit - Limit in milliseconds
 * @returns {Function} Throttled function
 */
export function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Format file size for human readable display
 * @param {number} bytes - Size in bytes
 * @returns {string} Formatted size string
 */
export function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Check if browser supports a feature
 * @param {string} feature - Feature to check
 * @returns {boolean} Whether feature is supported
 */
export function isSupported(feature) {
    switch (feature) {
        case 'webSpeech':
            return 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
        case 'webShare':
            return 'share' in navigator;
        case 'clipboard':
            return 'clipboard' in navigator;
        default:
            return false;
    }
}

/**
 * Copy text to clipboard with fallback
 * @param {string} text - Text to copy
 * @returns {Promise<boolean>} Success status
 */
export async function copyToClipboard(text) {
    try {
        if (isSupported('clipboard')) {
            await navigator.clipboard.writeText(text);
            return true;
        } else {
            // Fallback for older browsers
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            const success = document.execCommand('copy');
            document.body.removeChild(textarea);
            return success;
        }
    } catch (err) {
        console.error('Failed to copy text:', err);
        return false;
    }
}