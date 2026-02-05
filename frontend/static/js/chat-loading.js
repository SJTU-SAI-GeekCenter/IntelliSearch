/**
 * Chat Loading Animation Controller
 * @fileoverview Controls the loading animation for new chat sessions
 */

class ChatLoadingAnimation {
    constructor() {
        this.overlay = null;
        this.isLoading = false;
        this.loadingDuration = 2000; // 2 seconds
    }

    /**
     * Initialize the loading animation
     * @param {string} title - Loading title text
     * @param {string} subtitle - Loading subtitle text
     */
    init(title = "IntelliSearch", subtitle = "正在创建新的智能对话...") {
        this.createLoadingOverlay(title, subtitle);
        this.startLoadingAnimation();
    }

    /**
     * Create the loading overlay DOM elements
     */
    createLoadingOverlay(title, subtitle) {
        // Create overlay container
        this.overlay = document.createElement('div');
        this.overlay.className = 'chat-loading-overlay';
        this.overlay.innerHTML = `
            <div class="chat-loading-content">
                <div class="chat-logo-container">
                    <img class="chat-loading-logo" src="/static/assets/sai-square.jpg" alt="IntelliSearch Logo" />
                    <div class="chat-logo-glow"></div>
                </div>
                <h1 class="chat-loading-title">${title}</h1>
                <div class="chat-loading-subtitle">${subtitle}</div>
                <div class="chat-loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;

        // Add to body
        document.body.appendChild(this.overlay);
    }

    /**
     * Start the loading animation sequence
     */
    startLoadingAnimation() {
        this.isLoading = true;

        // Hide main content initially
        const chatLayout = document.querySelector('.chat-layout');
        if (chatLayout) {
            chatLayout.style.opacity = '0';
            chatLayout.style.transform = 'translateY(20px)';
        }

        // Start the fade out animation after duration
        setTimeout(() => {
            this.hideLoadingAnimation();
        }, this.loadingDuration);
    }

    /**
     * Hide the loading animation and show main content
     */
    hideLoadingAnimation() {
        if (!this.overlay) return;

        // Add fade out class
        this.overlay.classList.add('fade-out');

        // Show main content with animation
        const chatLayout = document.querySelector('.chat-layout');
        if (chatLayout) {
            chatLayout.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out';
            chatLayout.style.opacity = '1';
            chatLayout.style.transform = 'translateY(0)';

            // Add loaded class to body for future reference
            document.body.classList.add('loaded');
        }

        // Remove overlay after animation completes
        setTimeout(() => {
            if (this.overlay && this.overlay.parentNode) {
                this.overlay.parentNode.removeChild(this.overlay);
                this.overlay = null;
            }
            this.isLoading = false;
        }, 500);
    }

    /**
     * Force stop the loading animation
     */
    stop() {
        if (this.isLoading) {
            this.hideLoadingAnimation();
        }
    }
}

// Global instance
let chatLoading = null;

/**
 * Initialize chat loading animation when DOM is ready and requested
 * @param {boolean} showLoading - Whether to show loading animation
 * @param {string} title - Optional custom title
 * @param {string} subtitle - Optional custom subtitle
 */
function initChatLoading(showLoading = false, title = "IntelliSearch", subtitle = "正在创建新的智能对话...") {
    // Only initialize on chat pages
    if (!document.body.classList.contains('desktop-chat') && !document.body.classList.contains('mobile-chat')) {
        return;
    }

    if (!showLoading) {
        // Just mark as loaded without showing animation
        document.body.classList.add('loaded');
        const chatLayout = document.querySelector('.chat-layout');
        if (chatLayout) {
            chatLayout.style.opacity = '1';
            chatLayout.style.transform = 'translateY(0)';
        }
        return;
    }

    chatLoading = new ChatLoadingAnimation();
    chatLoading.init(title, subtitle);
}

/**
 * Check URL parameters to determine if loading animation should be shown
 */
function checkLoadingAnimation() {
    const urlParams = new URLSearchParams(window.location.search);
    const showLoading = urlParams.get('loading') === 'true';
    const title = urlParams.get('title') || 'IntelliSearch';
    const subtitle = urlParams.get('subtitle') || '正在创建新的智能对话...';

    initChatLoading(showLoading, title, subtitle);
}

// Auto-initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', checkLoadingAnimation);
} else {
    checkLoadingAnimation();
}

// Export for external use
window.ChatLoading = {
    init: initChatLoading,
    stop: () => {
        if (chatLoading) {
            chatLoading.stop();
        }
    },
    instance: () => chatLoading
};