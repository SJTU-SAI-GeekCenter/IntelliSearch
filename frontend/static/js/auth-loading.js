/**
 * Authentication Page Loading Animation
 * @fileoverview Controls the loading animation for login and register pages
 */

class AuthLoadingAnimation {
    constructor() {
        this.overlay = null;
        this.isLoading = false;
        this.loadingDuration = 2000; // 2 seconds
    }

    /**
     * Initialize the loading animation
     */
    init() {
        this.createLoadingOverlay();
        this.startLoadingAnimation();
    }

    /**
     * Create the loading overlay DOM elements
     */
    createLoadingOverlay() {
        // Create overlay container
        this.overlay = document.createElement('div');
        this.overlay.className = 'auth-loading-overlay';
        this.overlay.innerHTML = `
            <div class="auth-loading-content">
                <div class="auth-logo-container">
                    <img class="auth-loading-logo" src="/static/assets/sai-square.jpg" alt="IntelliSearch Logo" />
                    <div class="auth-logo-glow"></div>
                </div>
                <h1 class="auth-loading-title">IntelliSearch</h1>
                <div class="auth-loading-subtitle">正在加载安全认证系统...</div>
                <div class="auth-loading-dots">
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
        const authContainer = document.querySelector('.auth-container');
        if (authContainer) {
            authContainer.style.opacity = '0';
            authContainer.style.transform = 'translateY(20px)';
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
        const authContainer = document.querySelector('.auth-container');
        if (authContainer) {
            authContainer.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out';
            authContainer.style.opacity = '1';
            authContainer.style.transform = 'translateY(0)';

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
let authLoading = null;

/**
 * Initialize auth loading animation when DOM is ready
 */
function initAuthLoading() {
    // Only initialize on auth pages
    if (!document.body.classList.contains('auth-page')) {
        return;
    }

    authLoading = new AuthLoadingAnimation();
    authLoading.init();
}

// Auto-initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAuthLoading);
} else {
    initAuthLoading();
}

// Export for external use
window.AuthLoading = {
    init: initAuthLoading,
    stop: () => {
        if (authLoading) {
            authLoading.stop();
        }
    },
    instance: () => authLoading
};