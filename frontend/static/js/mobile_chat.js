// User data injected from template (defined in HTML)
let USER_DATA = window.USER_DATA || {
    avatarColor: '#6366f1',
    displayNameInitial: 'U'
};

let chatMessages, chatForm, messageInput, sendBtn, processBar, useToolsCheckbox;
let menuBtn, mobileMenu, menuOverlay;
let isStreaming = false;

/**
 * Initialize mobile chat
 */
function initMobileChat() {
    // Get DOM elements
    chatMessages = document.getElementById('chat-messages');
    chatForm = document.getElementById('chat-form');
    messageInput = document.getElementById('message-input');
    sendBtn = document.getElementById('send-btn');
    processBar = document.getElementById('process-bar');
    useToolsCheckbox = document.getElementById('use-tools');
    menuBtn = document.getElementById('menu-btn');
    mobileMenu = document.getElementById('mobile-menu');
    menuOverlay = document.getElementById('menu-overlay');

    // Apply avatar colors from data attributes
    applyAvatarColors();

    // Initialize event handlers
    initMenuToggle();
    initTextareaAutoResize();
    initEnterKeyHandler();
    initFormSubmitHandler();
}

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
 * Initialize menu toggle functionality
 */
function initMenuToggle() {
    menuBtn.addEventListener('click', () => {
        mobileMenu.classList.add('open');
        menuOverlay.classList.add('visible');
    });

    menuOverlay.addEventListener('click', () => {
        mobileMenu.classList.remove('open');
        menuOverlay.classList.remove('visible');
    });
}

/**
 * Auto-resize textarea
 */
function initTextareaAutoResize() {
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
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

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    if (role === 'user') {
        contentDiv.textContent = content;
    } else {
        contentDiv.className += ' markdown-content';
        contentDiv.innerHTML = renderMarkdown(content);
        renderLatex(contentDiv);
    }

    if (role === 'assistant') {
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar-mobile';
        avatar.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>';
        msgDiv.appendChild(avatar);
    }

    msgDiv.appendChild(contentDiv);
    chatMessages.appendChild(msgDiv);

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
};

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
 * Handle form submission
 */
function initFormSubmitHandler() {
    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const message = messageInput.value.trim();
        if (!message || isStreaming) return;

        isStreaming = true;
        sendBtn.disabled = true;
        messageInput.value = '';
        messageInput.style.height = 'auto';

        // Add user message
        createMessage('user', message);
        scrollToBottom();

        // Show process bar
        processBar.classList.add('visible');
        processBar.querySelector('.process-text').textContent = 'Thinking...';

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
                })
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
                            processBar.classList.remove('visible');
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
                                processBar.querySelector('.process-text').textContent =
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
                                processBar.querySelector('.process-text').textContent = 'Processing results...';
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
            console.error('Stream error:', error);
            createErrorCard('Connection error. Please try again.');
        } finally {
            isStreaming = false;
            sendBtn.disabled = false;
            processBar.classList.remove('visible');
            messageInput.focus();
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
    document.addEventListener('DOMContentLoaded', initMobileChat);
} else {
    initMobileChat();
}
