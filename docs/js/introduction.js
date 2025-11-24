/**
 * Introduction page JavaScript module
 * @fileoverview Landing page animations, interactions, and particle system
 */

import {CONFIG} from './config.js';
import {createRippleEffect} from './ui.js';

/**
 * Animate number counting
 * @param {HTMLElement} element - Element to update
 * @param {number} start - Starting number
 * @param {number} end - Ending number
 * @param {number} duration - Animation duration in milliseconds
 */
function animateNumber(element, start, end, duration) {
  const startTime = performance.now();
  const difference = end - start;

  function updateNumber(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);

    const current = Math.floor(start + difference * progress);
    element.textContent = current.toLocaleString();

    if (progress < 1) {
      requestAnimationFrame(updateNumber);
    }
  }

  requestAnimationFrame(updateNumber);
}

/**
 * Introduction page class
 * @class
 * Manages all introduction page specific functionality
 */
class IntroductionPage {
  constructor() {
    this.particles = [];
    this.animationId = null;
    this.mouseX = 0;
    this.mouseY = 0;
    this.isLoading = true;
    this.statsAnimated = false;
  }

  /**
   * Initialize the introduction page
   * @public
   */
  async initialize() {
    try {
      // Start loading animation
      this.startLoadingAnimation();

      // Initialize particle background
      this.initParticlesBackground();

      // Setup event listeners
      this.setupEventListeners();

      // Initialize scroll animations
      this.initScrollAnimations();

      console.log('Introduction page initialized successfully');
    } catch (error) {
      console.error('Failed to initialize introduction page:', error);
      this.showError('页面初始化失败');
    }
  }

  /**
   * Start the loading animation sequence
   * @private
   */
  startLoadingAnimation() {
    const loadingOverlay = document.getElementById('loading-overlay');
    const app = document.getElementById('introduction-app');

    if (!loadingOverlay || !app) return;

    // Ensure app is hidden initially
    app.classList.add('app-hidden');

    // Show main app after loading duration
    setTimeout(() => {
      loadingOverlay.classList.add('fade-out');
      app.classList.remove('app-hidden');
      app.classList.add('app-visible');

      // Setup stat counters animation
      this.setupStatCounters();

      // Complete loading
      setTimeout(() => {
        loadingOverlay.style.display = 'none';
        this.isLoading = false;
      }, 800);
    }, CONFIG.ANIMATION.LOADING_DURATION);
  }

  /**
   * Initialize particle background system
   * @private
   */
  initParticlesBackground() {
    const canvas = document.getElementById('particles-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    this.resizeCanvas(canvas);
    window.addEventListener('resize', () => this.resizeCanvas(canvas));

    // Create particles
    this.createParticles(canvas);

    // Start animation
    this.animateParticles(ctx);

    // Setup mouse interaction
    this.setupMouseInteraction(canvas);
  }

  /**
   * Resize canvas to window dimensions
   * @param {HTMLCanvasElement} canvas - Canvas element
   * @private
   */
  resizeCanvas(canvas) {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  /**
   * Create particle instances
   * @param {HTMLCanvasElement} canvas - Canvas element
   * @private
   */
  createParticles(canvas) {
    const particleCount =
        Math.min(50, Math.floor((canvas.width * canvas.height) / 15000));

    this.particles = [];
    for (let i = 0; i < particleCount; i++) {
      this.particles.push(new Particle(canvas));
    }
  }

  /**
   * Animate particles
   * @param {CanvasRenderingContext2D} ctx - Canvas context
   * @private
   */
  animateParticles(ctx) {
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);

    // Update and draw particles
    this.particles.forEach(particle => {
      particle.update();
      particle.applyMouseRepulsion(this.mouseX, this.mouseY);
      particle.draw(ctx);
    });

    // Draw connections between nearby particles
    this.drawParticleConnections(ctx);

    // Continue animation
    this.animationId = requestAnimationFrame(() => this.animateParticles(ctx));
  }

  /**
   * Draw connections between particles
   * @param {CanvasRenderingContext2D} ctx - Canvas context
   * @private
   */
  drawParticleConnections(ctx) {
    for (let i = 0; i < this.particles.length; i++) {
      for (let j = i + 1; j < this.particles.length; j++) {
        const dx = this.particles[i].x - this.particles[j].x;
        const dy = this.particles[i].y - this.particles[j].y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < 120) {
          ctx.beginPath();
          ctx.moveTo(this.particles[i].x, this.particles[i].y);
          ctx.lineTo(this.particles[j].x, this.particles[j].y);
          ctx.strokeStyle =
              `rgba(127, 255, 212, ${0.1 * (1 - distance / 120)})`;
          ctx.stroke();
        }
      }
    }
  }

  /**
   * Setup mouse interaction with particles
   * @param {HTMLCanvasElement} canvas - Canvas element
   * @private
   */
  setupMouseInteraction(canvas) {
    canvas.addEventListener('mousemove', (e) => {
      this.mouseX = e.clientX;
      this.mouseY = e.clientY;
    });

    // Touch support for mobile devices
    canvas.addEventListener('touchmove', (e) => {
      if (e.touches.length > 0) {
        this.mouseX = e.touches[0].clientX;
        this.mouseY = e.touches[0].clientY;
      }
    });
  }

  /**
   * Setup event listeners
   * @private
   */
  setupEventListeners() {
    // Learn more button
    const learnMoreBtn = document.getElementById('learn-more');
    if (learnMoreBtn) {
      learnMoreBtn.addEventListener('click', this.handleLearnMore.bind(this));
    }

    // Add ripple effects to buttons
    document.querySelectorAll('.btn.large').forEach(btn => {
      btn.addEventListener('click', function(e) {
        createRippleEffect(e, this);
      });
    });

    // Add hover effects to feature cards
    document.querySelectorAll('.feature-card').forEach(card => {
      card.addEventListener(
          'mouseenter', this.handleFeatureCardHover.bind(this));
      card.addEventListener(
          'mouseleave', this.handleFeatureCardLeave.bind(this));
    });

    // Keyboard navigation
    document.addEventListener('keydown', this.handleKeydown.bind(this));
  }

  /**
   * Initialize scroll-based animations
   * @private
   */
  initScrollAnimations() {
    // Use Intersection Observer for scroll animations
    const observerOptions = {threshold: 0.1, rootMargin: '0px 0px -50px 0px'};

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting && !entry.target.dataset.animated) {
          entry.target.dataset.animated = 'true';
          entry.target.classList.add('animate-in');
        }
      });
    }, observerOptions);

    // Observe stat items
    document.querySelectorAll('.stat-item').forEach(item => {
      observer.observe(item);
    });
  }

  /**
   * Setup animated stat counters
   * @private
   */
  setupStatCounters() {
    const statNumbers = document.querySelectorAll('.stat-number');

    const observerOptions = {threshold: 0.5};

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting && !this.statsAnimated) {
          this.statsAnimated = true;
          this.animateStats(statNumbers);
          observer.disconnect();
        }
      });
    }, observerOptions);

    if (statNumbers.length > 0) {
      observer.observe(statNumbers[0]);
    }
  }

  /**
   * Animate statistic numbers
   * @param {NodeList} statElements - Stat number elements
   * @private
   */
  animateStats(statElements) {
    const stats = [
      {end: 10000, suffix: 'K+', duration: 2000},
      {end: 50000, suffix: 'K+', duration: 2200},
      {end: 99.9, suffix: '%', duration: 1800}
    ];

    statElements.forEach((element, index) => {
      if (stats[index]) {
        const {end, suffix, duration} = stats[index];
        animateNumber(element, 0, end, duration);

        setTimeout(() => {
          element.textContent =
              element.textContent.replace(/\B(?=(\d{3})+(?!\d))/g, ',') +
              suffix;
        }, duration + 100);
      }
    });
  }

  /**
   * Handle learn more button click
   * @param {Event} event - Click event
   * @private
   */
  handleLearnMore(event) {
    event.preventDefault();

    // Show a modal or additional information
    this.showMoreInfo();
  }

  /**
   * Handle feature card hover
   * @param {Event} event - Mouse enter event
   * @private
   */
  handleFeatureCardHover(event) {
    const card = event.currentTarget;
    const icon = card.querySelector('.feature-icon');

    if (icon) {
      icon.style.transform = 'scale(1.2) rotate(5deg)';
    }
  }

  /**
   * Handle feature card leave
   * @param {Event} event - Mouse leave event
   * @private
   */
  handleFeatureCardLeave(event) {
    const card = event.currentTarget;
    const icon = card.querySelector('.feature-icon');

    if (icon) {
      icon.style.transform = 'scale(1) rotate(0deg)';
    }
  }

  /**
   * Handle keyboard navigation
   * @param {KeyboardEvent} event - Keyboard event
   * @private
   */
  handleKeydown(event) {
    // Press Enter or Space on "Learn More" button
    if (event.key === 'Enter' || event.key === ' ') {
      const focusedElement = document.activeElement;
      if (focusedElement && focusedElement.id === 'learn-more') {
        event.preventDefault();
        this.handleLearnMore(event);
      }
    }

    // Press 'G' to go to chat
    if (event.key === 'g' || event.key === 'G') {
      window.location.href = 'index.html';
    }
  }

  /**
   * Show more information modal
   * @private
   */
  showMoreInfo() {
    // Create a simple modal
    const modal = document.createElement('div');
    modal.className = 'info-modal';
    modal.innerHTML = `
            <div class="info-modal-content">
                <h3>关于智搜</h3>
                <p>智搜是SJTU-SAI Geek Center开发的智能对话助手，采用先进的AI技术为您提供精准的搜索和对话体验。</p>
                <ul>
                    <li>🤖 基于大语言模型的智能对话</li>
                    <li>🔍 强大的搜索和信息检索能力</li>
                    <li>💬 自然流畅的多轮对话</li>
                    <li>🎯 精准理解用户意图</li>
                </ul>
                <p>点击"开始对话"来体验智搜的强大功能！</p>
                <button class="btn primary">知道了</button>
            </div>
        `;

    // Add modal styles
    modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;

    document.body.appendChild(modal);

    // Animate in
    setTimeout(() => {
      modal.style.opacity = '1';
    }, 50);

    // Setup close handlers
    const closeBtn = modal.querySelector('.btn');
    const closeModal = () => {
      modal.style.opacity = '0';
      setTimeout(() => {
        document.body.removeChild(modal);
      }, 300);
    };

    closeBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeModal();
      }
    });
  }

  /**
   * Show error message
   * @param {string} message - Error message
   * @private
   */
  showError(message) {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = 'toast error';
    toast.textContent = message;
    toast.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--danger);
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            z-index: 9999;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;

    document.body.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '1';
    }, 50);

    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => {
        if (document.body.contains(toast)) {
          document.body.removeChild(toast);
        }
      }, 300);
    }, 3000);
  }

  /**
   * Cleanup resources
   * @public
   */
  destroy() {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }
    this.particles = [];
  }
}

/**
 * Particle class for background animation
 */
class Particle {
  constructor(canvas) {
    this.canvas = canvas;
    this.reset();
  }

  reset() {
    this.x = Math.random() * this.canvas.width;
    this.y = Math.random() * this.canvas.height;
    this.size = Math.random() * 2 + 0.5;
    this.speedX = (Math.random() - 0.5) * 0.5;
    this.speedY = (Math.random() - 0.5) * 0.5;
    this.opacity = Math.random() * 0.5 + 0.2;
    this.pulseSpeed = Math.random() * 0.02 + 0.01;
    this.pulsePhase = Math.random() * Math.PI * 2;
  }

  update() {
    this.x += this.speedX;
    this.y += this.speedY;
    this.pulsePhase += this.pulseSpeed;

    // Boundary detection
    if (this.x < 0 || this.x > this.canvas.width) {
      this.speedX *= -1;
    }
    if (this.y < 0 || this.y > this.canvas.height) {
      this.speedY *= -1;
    }

    // Keep particles within bounds
    this.x = Math.max(0, Math.min(this.canvas.width, this.x));
    this.y = Math.max(0, Math.min(this.canvas.height, this.y));
  }

  applyMouseRepulsion(mouseX, mouseY) {
    const dx = this.x - mouseX;
    const dy = this.y - mouseY;
    const distance = Math.sqrt(dx * dx + dy * dy);

    if (distance < 100) {
      const force = (100 - distance) / 100;
      this.x += dx * force * 0.02;
      this.y += dy * force * 0.02;
    }
  }

  draw(ctx) {
    const pulsedOpacity = this.opacity + Math.sin(this.pulsePhase) * 0.1;
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(127, 255, 212, ${pulsedOpacity})`;
    ctx.fill();
  }
}

// Initialize introduction page when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  const introductionPage = new IntroductionPage();
  introductionPage.initialize();

  // Make instance available globally for debugging
  window.IntroductionPage = introductionPage;
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  if (window.IntroductionPage) {
    window.IntroductionPage.destroy();
  }
});