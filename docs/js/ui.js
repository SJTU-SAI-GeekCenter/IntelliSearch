/**
 * UI components and rendering functionality
 * @fileoverview User interface rendering and DOM manipulation
 */

import { appState } from './config.js';
import { escapeHtml, renderMarkdown, autosize, debounce } from './utils.js';
import { getCurrentChat } from './chat.js';

/**
 * Show a toast notification
 * @param {string} text - Message to display
 * @param {number} duration - Duration in milliseconds (default: 2200)
 */
export function showToast(text, duration = 2200) {
    const toastEl = document.getElementById('toast');
    if (!toastEl) return;

    toastEl.textContent = text;
    toastEl.classList.add('show');
    toastEl.style.animation = 'slideup 0.3s ease-out';

    setTimeout(() => {
        toastEl.classList.remove('show');
        toastEl.style.animation = 'slideDown 0.3s ease-out';
    }, duration);
}

/**
 * Render the chat history sidebar
 */
export function renderHistory() {
    const historyListEl = document.getElementById('history-list');
    if (!historyListEl) return;

    historyListEl.innerHTML = '';

    appState.chats.forEach(chat => {
        const chatEl = createHistoryItem(chat);
        historyListEl.appendChild(chatEl);
    });
}

/**
 * Create a history item element
 * @param {Object} chat - Chat object
 * @returns {HTMLElement} History item element
 */
function createHistoryItem(chat) {
    const item = document.createElement('div');
    item.className = 'history-item';
    if (chat.id === appState.currentChatId) {
        item.classList.add('active');
    }

    item.dataset.id = chat.id;
    item.innerHTML = `<span class="name">${escapeHtml(chat.name)}</span>`;

    return item;
}

/**
 * Render messages for the current chat
 */
export function renderMessages() {
    const messagesEl = document.getElementById('messages');
    const chatTitleEl = document.getElementById('chat-title');

    if (!messagesEl || !chatTitleEl) return;

    const chat = getCurrentChat();
    if (!chat) {
        messagesEl.innerHTML = '<p class="empty-state">No active chat selected</p>';
        chatTitleEl.textContent = 'No Chat Selected';
        return;
    }

    chatTitleEl.textContent = chat.name;
    messagesEl.innerHTML = '';

    chat.messages.forEach(message => {
        const messageEl = createMessageElement(message.role, message.content);
        messagesEl.appendChild(messageEl);
    });

    messagesEl.scrollTop = messagesEl.scrollHeight;
}

/**
 * Create a message element
 * @param {string} role - Message role ('user' | 'assistant' | 'system')
 * @param {string} content - Message content
 * @returns {HTMLElement} Message element
 */
export function createMessageElement(role, content) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `msg ${role}`;

    const avatar = createAvatar(role);
    const bubble = createMessageBubble(role, content);

    // Arrange elements based on role
    if (role === 'assistant') {
        msgDiv.appendChild(avatar);
        msgDiv.appendChild(bubble);
    } else {
        msgDiv.appendChild(bubble);
        msgDiv.appendChild(avatar);
    }

    return msgDiv;
}

/**
 * Create an avatar element
 * @param {string} role - Message role
 * @returns {HTMLElement} Avatar element
 */
function createAvatar(role) {
    const avatar = document.createElement('div');
    avatar.className = 'avatar';

    if (role === 'assistant') {
        avatar.classList.add('ai');
        avatar.textContent = 'AI';
    } else {
        avatar.textContent = '👤';
    }

    return avatar;
}

/**
 * Create a message bubble element
 * @param {string} role - Message role
 * @param {string} content - Message content
 * @returns {HTMLElement} Message bubble element
 */
function createMessageBubble(role, content) {
    const bubble = document.createElement('div');
    bubble.className = 'bubble';

    if (content) {
        bubble.innerHTML = renderMarkdown(content);
    } else {
        bubble.classList.add('typing');
        bubble.innerHTML = createThinkingIndicator();
    }

    return bubble;
}

/**
 * Create a thinking indicator element
 * @returns {string} HTML for thinking indicator
 */
function createThinkingIndicator() {
    return `
        <div class="thinking-indicator">
            <span class="thinking-dot"></span>
            <span class="thinking-dot"></span>
            <span class="thinking-dot"></span>
        </div>
    `;
}

/**
 * Add a message to the UI
 * @param {string} role - Message role
 * @param {string} content - Message content
 * @returns {HTMLElement|null} Message bubble element or null
 */
export function appendMessageUI(role, content) {
    const messagesEl = document.getElementById('messages');
    if (!messagesEl) return null;

    const messageEl = createMessageElement(role, content);
    messagesEl.appendChild(messageEl);

    // Scroll to bottom
    messagesEl.scrollTop = messagesEl.scrollHeight;

    // Return the bubble element for potential updates
    return messageEl.querySelector('.bubble');
}

/**
 * Update an assistant message with new content
 * @param {HTMLElement} bubbleEl - Bubble element to update
 * @param {string} text - New text content
 * @param {boolean} useTypewriter - Whether to use typewriter effect
 */
export function updateAssistantMessage(bubbleEl, text, useTypewriter = false) {
    if (!bubbleEl) return;

    bubbleEl.classList.remove('typing');
    bubbleEl.innerHTML = '';

    if (useTypewriter && appState.isTypewriterEnabled) {
        typewriterEffect(bubbleEl, text, () => {
            bubbleEl.innerHTML = renderMarkdown(text);
            scrollToBottom();
        });
    } else {
        bubbleEl.innerHTML = renderMarkdown(text);
        scrollToBottom();
    }
}

/**
 * Set a bubble element to thinking state
 * @param {HTMLElement} bubbleEl - Bubble element
 * @param {boolean} isThinking - Whether to show thinking state
 */
export function setThinkingState(bubbleEl, isThinking) {
    if (!bubbleEl) return;

    if (isThinking) {
        bubbleEl.innerHTML = createThinkingIndicator();
        bubbleEl.classList.add('typing');
    } else {
        bubbleEl.classList.remove('typing');
        bubbleEl.innerHTML = '';
    }
}

/**
 * Typewriter effect for text animation
 * @param {HTMLElement} element - Element to animate
 * @param {string} text - Text to type
 * @param {Function} callback - Callback function when complete
 */
export function typewriterEffect(element, text, callback) {
    element.textContent = '';
    let index = 0;

    function type() {
        if (index < text.length) {
            element.textContent += text.charAt(index);
            index++;
            setTimeout(type, 30 + Math.random() * 20);
        } else if (callback) {
            callback();
        }
    }

    type();
}

/**
 * Scroll messages to bottom smoothly
 */
export function scrollToBottom() {
    const messagesEl = document.getElementById('messages');
    if (messagesEl) {
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }
}

/**
 * Update chat title in the UI
 * @param {string} title - New chat title
 */
export function updateChatTitle(title) {
    const chatTitleEl = document.getElementById('chat-title');
    if (chatTitleEl) {
        chatTitleEl.textContent = title;
    }
}

/**
 * Toggle settings panel visibility
 * @param {boolean} show - Whether to show the panel
 */
export function toggleSettingsPanel(show) {
    const settingsPanel = document.getElementById('settings-panel');
    if (settingsPanel) {
        if (show) {
            settingsPanel.classList.remove('hidden');
        } else {
            settingsPanel.classList.add('hidden');
        }
    }
}

/**
 * Create a ripple effect on button click
 * @param {Event} event - Click event
 * @param {HTMLElement} element - Element to apply effect to
 */
export function createRippleEffect(event, element) {
    const ripple = document.createElement('span');
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;

    ripple.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        left: ${x}px;
        top: ${y}px;
        background: rgba(127, 255, 212, 0.3);
        border-radius: 50%;
        transform: scale(0);
        animation: ripple 0.6s ease-out;
        pointer-events: none;
    `;

    element.style.position = 'relative';
    element.style.overflow = 'hidden';
    element.appendChild(ripple);

    setTimeout(() => ripple.remove(), 600);
}

/**
 * Initialize UI components and event listeners
 */
export function initializeUI() {
    // Initialize textarea autosize
    const promptEl = document.getElementById('prompt');
    if (promptEl) {
        autosize(promptEl);
    }

    // Add ripple effects to buttons
    document.querySelectorAll('.btn, .icon-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            createRippleEffect(e, this);
        });
    });

    // Initialize tooltips and other UI enhancements
    initializeEnhancements();
}

/**
 * Initialize UI enhancements
 */
function initializeEnhancements() {
    // Add input focus effects
    const promptEl = document.getElementById('prompt');
    if (promptEl) {
        promptEl.addEventListener('input', function() {
            if (this.value.length > 0) {
                this.style.borderColor = 'var(--primary)';
            } else {
                this.style.borderColor = 'var(--border)';
            }
        });
    }

    // Add keyboard shortcuts hint
    setupKeyboardHints();
}

/**
 * Setup keyboard shortcuts and hints
 */
function setupKeyboardHints() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K for new chat
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            document.getElementById('new-chat')?.click();
        }

        // Ctrl/Cmd + / for shortcuts help
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            showKeyboardShortcuts();
        }
    });
}

/**
 * Show keyboard shortcuts modal/hint
 */
function showKeyboardShortcuts() {
    const shortcuts = [
        { key: 'Ctrl/Cmd + K', description: 'New Chat' },
        { key: 'Ctrl/Cmd + /', description: 'Show Shortcuts' },
        { key: 'Enter', description: 'Send Message' },
        { key: 'Shift + Enter', description: 'New Line' }
    ];

    showToast('Keyboard shortcuts: ' + shortcuts.map(s => `${s.key}: ${s.description}`).join(', '));
}