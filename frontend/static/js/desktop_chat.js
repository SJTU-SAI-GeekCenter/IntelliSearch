// User data injected from template (defined in HTML)
let USER_DATA = window.USER_DATA || {
    avatarColor: '#6366f1',
    displayNameInitial: 'U'
};

let chatMessages, chatForm, messageInput, sendBtn, processIndicator, useToolsCheckbox;
let sessionsList, refreshSessionsBtn, newChatBtn;
let isStreaming = false;
let currentSessionId = null;
let currentAbortController = null;

/**
 * Initialize desktop chat
 */
function initDesktopChat() {
    // Get DOM elements
    chatMessages = document.getElementById('chat-messages');
    chatForm = document.getElementById('chat-form');
    messageInput = document.getElementById('message-input');
    sendBtn = document.getElementById('send-btn');
    processIndicator = document.getElementById('process-indicator');
    useToolsCheckbox = document.getElementById('use-tools');
    sessionsList = document.getElementById('sessions-list');
    refreshSessionsBtn = document.getElementById('refresh-sessions-btn');
    newChatBtn = document.getElementById('new-chat-btn');

    // Apply avatar colors from data attributes
    applyAvatarColors();

    // Load sessions list
    loadSessionsList();

    // Load chat history when page loads
    loadChatHistory();

    // Initialize event handlers
    initTextareaAutoResize();
    initEnterKeyHandler();
    initFormSubmitHandler();
    initSessionHandlers();
}

// ============================================================================
// Session Management
// ============================================================================

/**
 * Initialize session-related event handlers
 */
function initSessionHandlers() {
    // Refresh sessions button
    if (refreshSessionsBtn) {
        refreshSessionsBtn.addEventListener('click', () => {
            loadSessionsList();
        });
    }

    // New chat button - intercept to prevent full page reload
    if (newChatBtn) {
        newChatBtn.addEventListener('click', (e) => {
            e.preventDefault();
            createNewSession();
        });
    }
}

/**
 * Load sessions list from server
 */
async function loadSessionsList() {
    if (!sessionsList) return;

    try {
        const response = await fetch('/api/sessions');
        if (!response.ok) throw new Error('Failed to load sessions');

        const sessions = await response.json();

        // Get current session ID from the page (session_id display)
        const sessionIdDisplay = document.querySelector('.session-id');
        if (sessionIdDisplay && !currentSessionId) {
            // Extract full session ID from sessions list
            const currentSessionFromList = sessions.find(s =>
                sessionIdDisplay.textContent.includes(s.session_id.substring(0, 8))
            );
            if (currentSessionFromList) {
                currentSessionId = currentSessionFromList.session_id;
            }
        }

        renderSessionsList(sessions);
    } catch (error) {
        console.error('Failed to load sessions:', error);
        sessionsList.innerHTML = '<div class="empty-sessions">Failed to load sessions</div>';
    }
}

/**
 * Render sessions list
 */
function renderSessionsList(sessions) {
    if (!sessionsList) return;

    if (sessions.length === 0) {
        sessionsList.innerHTML = '<div class="empty-sessions">No recent chats</div>';
        return;
    }

    sessionsList.innerHTML = '';

    sessions.forEach(session => {
        const sessionItem = createSessionItem(session);

        // Highlight current session
        if (session.session_id === currentSessionId) {
            sessionItem.classList.add('active');
        }

        sessionsList.appendChild(sessionItem);
    });
}

/**
 * Create a session item element
 */
function createSessionItem(session) {
    const div = document.createElement('div');
    div.className = 'session-item';
    div.dataset.sessionId = session.session_id;

    // Format date
    const date = new Date(session.updated_at);
    const dateStr = formatDate(date);

    div.innerHTML = `
        <svg class="session-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <div class="session-content">
            <div class="session-title" title="${escapeHtml(session.title)}">${escapeHtml(session.title)}</div>
            <div class="session-meta">
                <span>${session.message_count} messages</span>
                <span>•</span>
                <span>${dateStr}</span>
            </div>
        </div>
        <div class="session-actions">
            <button class="session-action-btn rename" title="Rename" onclick="event.stopPropagation(); renameSessionPrompt('${session.session_id}')">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
            </button>
            <button class="session-action-btn delete" title="Delete" onclick="event.stopPropagation(); deleteSessionConfirm('${session.session_id}')">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
            </button>
        </div>
    `;

    // Click to switch session
    div.addEventListener('click', () => switchSession(session.session_id));

    return div;
}

/**
 * Switch to a different session
 */
async function switchSession(sessionId) {
    if (sessionId === currentSessionId) return;

    try {
        const response = await fetch('/api/sessions/switch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });

        if (!response.ok) throw new Error('Failed to switch session');

        currentSessionId = sessionId;

        // Clear current messages
        chatMessages.innerHTML = '<div class="welcome-message"><div class="welcome-icon"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg></div><h2>Loading...</h2></div>';

        // Reload history for new session
        await loadChatHistory();

        // Refresh sessions list to update active state
        await loadSessionsList();

        // Update session ID display
        const sessionIdDisplay = document.querySelector('.session-id');
        if (sessionIdDisplay) {
            sessionIdDisplay.textContent = sessionId.substring(0, 8) + '...';
        }
    } catch (error) {
        console.error('Failed to switch session:', error);
        alert('Failed to switch session. Please try again.');
    }
}

/**
 * Create a new session
 */
async function createNewSession() {
    try {
        // Navigate to new chat endpoint which creates new session
        window.location.href = '/chat/new';
    } catch (error) {
        console.error('Failed to create new session:', error);
    }
}

/**
 * Prompt user to rename a session
 */
async function renameSessionPrompt(sessionId) {
    const session = sessionsList.querySelector(`[data-session-id="${sessionId}"]`);
    if (!session) return;

    const currentTitle = session.querySelector('.session-title').textContent;
    const newTitle = prompt('Enter new title:', currentTitle);

    if (newTitle === null || newTitle.trim() === '') return;

    try {
        const response = await fetch('/api/sessions/rename', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                title: newTitle.trim()
            })
        });

        if (!response.ok) throw new Error('Failed to rename session');

        // Reload sessions list
        await loadSessionsList();
    } catch (error) {
        console.error('Failed to rename session:', error);
        alert('Failed to rename session. Please try again.');
    }
}

/**
 * Confirm and delete a session
 */
async function deleteSessionConfirm(sessionId) {
    if (!confirm('Are you sure you want to delete this chat? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`/api/sessions/delete?session_id=${sessionId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to delete session');
        }

        // Reload sessions list
        await loadSessionsList();
    } catch (error) {
        console.error('Failed to delete session:', error);
        alert(error.message || 'Failed to delete session. Please try again.');
    }
}

/**
 * Format date relative to now
 */
function formatDate(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString();
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Make functions globally available for onclick handlers
window.renameSessionPrompt = renameSessionPrompt;
window.deleteSessionConfirm = deleteSessionConfirm;

/**
 * Apply avatar colors from data attributes
 */
function applyAvatarColors() {
    const avatarElements = document.querySelectorAll('.avatar[data-avatar-color]');
    avatarElements.forEach(avatar => {
        const color = avatar.getAttribute('data-avatar-color');
        if (color) {
            avatar.style.background = color;
        }
    });
}

/**
 * Load chat history on page load
 */
async function loadChatHistory() {
    try {
        const response = await fetch('/api/user/history');
        if (!response.ok) return;

        const logs = await response.json();

        if (logs.length === 0) return;

        // Remove welcome message if exists
        const welcomeMsg = chatMessages.querySelector('.welcome-message');
        if (welcomeMsg) welcomeMsg.remove();

        // Display each message in order
        for (const log of logs) {
            if (log.role === 'user') {
                createMessage('user', log.content);
            } else if (log.role === 'assistant') {
                // Parse and display assistant response (may contain tool calls)
                parseAndDisplayFinalResponse(log.content);
            }
        }

        scrollToBottom();
    } catch (error) {
        console.error('Failed to load chat history:', error);
    }
}

/**
 * Auto-resize textarea
 */
function initTextareaAutoResize() {
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 200) + 'px';
    });
}

/**
 * Handle Enter key for message submission
 */
function initEnterKeyHandler() {
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!isStreaming && this.value.trim()) {
                chatForm.dispatchEvent(new Event('submit'));
            }
        }
    });
}

/**
 * Send quick prompt (global function for onclick handlers)
 */
window.sendQuickPrompt = function(text) {
    messageInput.value = text;
    chatForm.dispatchEvent(new Event('submit'));
};

/**
 * Create message element
 */
function createMessage(role, content) {
    const welcomeMsg = chatMessages.querySelector('.welcome-message');
    if (welcomeMsg) welcomeMsg.remove();

    const msgDiv = document.createElement('div');
    msgDiv.className = `message message-${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';

    if (role === 'user') {
        avatar.style.background = USER_DATA.avatarColor || '#6366f1';
        avatar.textContent = USER_DATA.displayNameInitial || 'U';
    } else {
        avatar.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>';
    }

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content markdown-content';

    if (role === 'user') {
        contentDiv.textContent = content;
    } else {
        contentDiv.innerHTML = renderMarkdown(content);
        renderLatex(contentDiv);
    }

    msgDiv.appendChild(avatar);
    msgDiv.appendChild(contentDiv);
    chatMessages.appendChild(msgDiv);

    // Return the message element for tool cards to reference
    if (role === 'assistant') {
        return msgDiv;
    }
    return contentDiv;
}

/**
 * Create expandable tool card as a message
 */
function createToolCard(toolCall) {
    // Create message container
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message message-tool';

    // Create content div with tool card
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const card = document.createElement('div');
    card.className = 'tool-card';

    const isSuccess = toolCall.success !== false;
    const statusIcon = isSuccess
        ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="tool-status-success">
             <polyline points="20 6 9 17 4 12"/>
           </svg>`
        : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="tool-status-error">
             <circle cx="12" cy="12" r="10"/>
             <line x1="12" y1="8" x2="12" y2="12"/>
             <line x1="12" y1="16" x2="12.01" y2="16"/>
           </svg>`;

    // Format arguments for display
    const argsText = JSON.stringify(toolCall.arguments || {}, null, 2);

    // Truncate result if too long
    let resultText = toolCall.result || '';
    const maxLength = 500;
    if (resultText.length > maxLength) {
        resultText = resultText.substring(0, maxLength) + '...';
    }

    card.innerHTML = `
        <div class="tool-card-header" onclick="toggleToolCard(this)">
            <div class="tool-card-title">
                <div class="tool-icon-small">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
                    </svg>
                </div>
                <span class="tool-name">${toolCall.name}</span>
                ${statusIcon}
            </div>
            <svg class="tool-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6 9 12 15 18 9"/>
            </svg>
        </div>
        <div class="tool-card-content" style="display: none;">
            <div class="tool-section">
                <div class="tool-section-title">Arguments</div>
                <pre class="tool-code">${argsText}</pre>
            </div>
            <div class="tool-section">
                <div class="tool-section-title">Result</div>
                <pre class="tool-code result-content">${resultText}</pre>
            </div>
        </div>
    `;

    contentDiv.appendChild(card);
    msgDiv.appendChild(contentDiv);
    chatMessages.appendChild(msgDiv);

    return card;
}

/**
 * Toggle tool card expansion (global function for onclick handlers)
 */
window.toggleToolCard = function(header) {
    const content = header.nextElementSibling;
    const chevron = header.querySelector('.tool-chevron');

    if (content.style.display === 'none') {
        content.style.display = 'block';
        chevron.style.transform = 'rotate(180deg)';
    } else {
        content.style.display = 'none';
        chevron.style.transform = 'rotate(0deg)';
    }
}

/**
 * Parse and display final response cards
 */
function parseAndDisplayFinalResponse(content) {
    // Extract final_response and tool_tracing sections
    const finalResponseMatch = content.match(/<final_response>([\s\S]*?)<\/final_response>/);
    const toolTracingMatch = content.match(/<tool_tracing>([\s\S]*?)<\/tool_tracing>/);

    // Display final response card
    if (finalResponseMatch) {
        const responseContent = finalResponseMatch[1].trim();
        createFinalResponseCard(responseContent);
    } else {
        // If no tags found, display entire content as response
        createFinalResponseCard(content.trim());
    }

    // Display tool tracing card
    if (toolTracingMatch) {
        const tracingContent = toolTracingMatch[1].trim();
        createToolTracingCard(tracingContent);
    }

    scrollToBottom();
}

/**
 * Create final response card
 */
function createFinalResponseCard(content) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message message-tool';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const card = document.createElement('div');
    card.className = 'response-card';

    card.innerHTML = `
        <div class="response-card-header">
            <div class="response-card-title">
                <div class="response-icon-small">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
                    </svg>
                </div>
                <span class="response-name">Final Response</span>
            </div>
        </div>
        <div class="response-card-content markdown-content">
            ${renderMarkdown(content)}
        </div>
    `;

    contentDiv.appendChild(card);
    msgDiv.appendChild(contentDiv);
    chatMessages.appendChild(msgDiv);

    // Render LaTeX
    const markdownContent = card.querySelector('.markdown-content');
    renderLatex(markdownContent);
}

/**
 * Create tool tracing card
 */
function createToolTracingCard(content) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message message-tool';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const card = document.createElement('div');
    card.className = 'tracing-card';

    card.innerHTML = `
        <div class="tracing-card-header">
            <div class="tracing-card-title">
                <div class="tracing-icon-small">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                    </svg>
                </div>
                <span class="tracing-name">Tool Tracing</span>
            </div>
        </div>
        <div class="tracing-card-content markdown-content">
            ${renderMarkdown(content)}
        </div>
    `;

    contentDiv.appendChild(card);
    msgDiv.appendChild(contentDiv);
    chatMessages.appendChild(msgDiv);

    // Render LaTeX
    const markdownContent = card.querySelector('.markdown-content');
    renderLatex(markdownContent);
}

/**
 * Create error card
 */
function createErrorCard(errorMessage) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message message-tool';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const card = document.createElement('div');
    card.className = 'error-card';

    card.innerHTML = `
        <div class="error-card-header">
            <div class="error-card-title">
                <div class="error-icon-small">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="8" x2="12" y2="12"/>
                        <line x1="12" y1="16" x2="12.01" y2="16"/>
                    </svg>
                </div>
                <span class="error-name">Error</span>
            </div>
        </div>
        <div class="error-card-content">
            ${errorMessage}
        </div>
    `;

    contentDiv.appendChild(card);
    msgDiv.appendChild(contentDiv);
    chatMessages.appendChild(msgDiv);

    scrollToBottom();
}

/**
 * Update send button state
 */
function updateSendButtonState() {
    if (isStreaming) {
        sendBtn.classList.add('stop-btn');
        sendBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" stroke="none">
                <rect x="6" y="6" width="12" height="12"/>
            </svg>
        `;
    } else {
        sendBtn.classList.remove('stop-btn');
        sendBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
        `;
    }
}

/**
 * Stop current streaming request
 */
function stopStreaming() {
    if (currentAbortController) {
        currentAbortController.abort();
        currentAbortController = null;
    }
}

/**
 * Handle form submission
 */
function initFormSubmitHandler() {
    // Handle send/stop button clicks
    sendBtn.addEventListener('click', async function(e) {
        if (isStreaming) {
            e.preventDefault();
            stopStreaming();
            return;
        }
    });

    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const message = messageInput.value.trim();
        if (!message || isStreaming) return;

        isStreaming = true;
        currentAbortController = new AbortController();
        updateSendButtonState();
        messageInput.value = '';
        messageInput.style.height = 'auto';

        // Add user message
        createMessage('user', message);
        scrollToBottom();

        // Show process indicator
        processIndicator.classList.add('visible');
        processIndicator.querySelector('.process-text').textContent = 'Thinking...';

        // Don't create assistant message bubble anymore
        // We'll display final response as cards instead
        let fullContent = '';
        let currentToolCard = null;

        try {
            const response = await fetch('/api/chat/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    use_tools: useToolsCheckbox.checked
                }),
                signal: currentAbortController.signal
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);

                        if (data === '[DONE]') {
                            processIndicator.classList.remove('visible');
                            // Parse and display final response cards
                            if (fullContent.trim()) {
                                parseAndDisplayFinalResponse(fullContent);
                            }
                            continue;
                        }

                        try {
                            const event = JSON.parse(data);

                            console.log('Event type:', event.type, event);

                            if (event.type === 'content') {
                                if (currentToolCard) {
                                    currentToolCard = null;
                                }
                                // Accumulate content
                                fullContent += event.content;
                            } else if (event.type === 'tool_call_start') {
                                processIndicator.querySelector('.process-text').textContent =
                                    `Using ${event.tool_call.name}...`;
                                // Create tool card
                                currentToolCard = createToolCard(event.tool_call);
                                scrollToBottom();
                            } else if (event.type === 'tool_result') {
                                if (currentToolCard) {
                                    // Update the tool card with the actual result
                                    const resultPre = currentToolCard.querySelector('.result-content');
                                    if (resultPre) {
                                        // Truncate result if too long
                                        let resultText = event.tool_call.result || '';
                                        const maxLength = 500;
                                        if (resultText.length > maxLength) {
                                            resultText = resultText.substring(0, maxLength) + '...';
                                        }
                                        resultPre.textContent = resultText;
                                    }
                                    currentToolCard = null;
                                }
                                processIndicator.querySelector('.process-text').textContent = 'Processing results...';
                            } else if (event.type === 'error') {
                                // Show error as a card
                                createErrorCard(event.error);
                            }
                        } catch (err) {
                            console.error('Parse error:', err, 'Data:', data);
                        }
                    }
                }
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('Stream stopped by user');
                // Show stopped message
                const stoppedDiv = document.createElement('div');
                stoppedDiv.className = 'message message-system';
                stoppedDiv.innerHTML = '<div class="message-content"><em>Response stopped by user</em></div>';
                chatMessages.appendChild(stoppedDiv);
                scrollToBottom();
            } else {
                console.error('Stream error:', error);
                createErrorCard('Connection error. Please try again.');
            }
        } finally {
            isStreaming = false;
            currentAbortController = null;
            updateSendButtonState();
            processIndicator.classList.remove('visible');
            messageInput.focus();

            // Refresh sessions list after sending message
            loadSessionsList();
        }
    });
}

/**
 * Scroll chat to bottom
 */
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Run initialization when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDesktopChat);
} else {
    initDesktopChat();
}
