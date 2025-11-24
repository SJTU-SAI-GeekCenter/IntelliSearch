/**
 * Animation and visual effects for the AI Chat Application
 * @fileoverview Particle background, loading animations, and visual effects
 */

import {CONFIG} from './config.js';

/**
 * Initialize all animations and effects
 */
export function initializeAnimations() {
  startLoadingAnimation();
  initParticlesBackground();
  initAnimationsCSS();
}

/**
 * Start the loading animation sequence
 */
function startLoadingAnimation() {
  const loadingOverlay = document.getElementById('loading-overlay');
  const app = document.getElementById('app');

  if (!loadingOverlay || !app) return;

  // Hide main app initially
  app.classList.add('app-hidden');

  // Show main app after loading duration
  setTimeout(() => {
    loadingOverlay.classList.add('fade-out');
    app.classList.remove('app-hidden');
    app.classList.add('app-visible');

    // Remove loading overlay completely
    setTimeout(() => {
      loadingOverlay.style.display = 'none';
    }, 800);
  }, CONFIG.ANIMATION.LOADING_DURATION);
}

/**
 * Initialize particle background system
 */
function initParticlesBackground() {
  const canvas = document.getElementById('particles-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  let particles = [];
  let animationId = null;
  let mouseX = 0;
  let mouseY = 0;

  // Set canvas size
  function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);

  // Particle class
  class Particle {
    constructor() {
      this.reset();
    }

    reset() {
      this.x = Math.random() * canvas.width;
      this.y = Math.random() * canvas.height;
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

      // Boundary detection and bounce
      if (this.x < 0 || this.x > canvas.width) {
        this.speedX *= -1;
      }
      if (this.y < 0 || this.y > canvas.height) {
        this.speedY *= -1;
      }

      // Keep particles within bounds
      this.x = Math.max(0, Math.min(canvas.width, this.x));
      this.y = Math.max(0, Math.min(canvas.height, this.y));
    }

    draw() {
      const pulsedOpacity = this.opacity + Math.sin(this.pulsePhase) * 0.1;
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(127, 255, 212, ${pulsedOpacity})`;
      ctx.fill();
    }

    applyMouseRepulsion() {
      const dx = this.x - mouseX;
      const dy = this.y - mouseY;
      const distance = Math.sqrt(dx * dx + dy * dy);

      if (distance < 100) {
        const force = (100 - distance) / 100;
        this.x += dx * force * 0.02;
        this.y += dy * force * 0.02;
      }
    }
  }

  // Create particles
  function createParticles() {
    const particleCount =
        Math.min(50, Math.floor((canvas.width * canvas.height) / 15000));
    particles = [];
    for (let i = 0; i < particleCount; i++) {
      particles.push(new Particle());
    }
  }

  // Draw connections between nearby particles
  function connectParticles() {
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle =
              `rgba(127, 255, 212, ${0.1 * (1 - distance / 120)})`;
          ctx.stroke();
        }
      }
    }
  }

  // Animation loop
  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    particles.forEach(particle => {
      particle.update();
      particle.applyMouseRepulsion();
      particle.draw();
    });

    connectParticles();
    animationId = requestAnimationFrame(animate);
  }

  // Mouse interaction
  canvas.addEventListener('mousemove', (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
  });

  // Start particle system
  createParticles();
  animate();

  // Handle window resize
  window.addEventListener('resize', () => {
    resizeCanvas();
    createParticles();
  });
}

/**
 * Initialize animation CSS styles
 */
function initAnimationsCSS() {
  // Add custom CSS animations if not already present
  if (document.getElementById('custom-animations')) return;

  const style = document.createElement('style');
  style.id = 'custom-animations';
  style.textContent = `
        /* Thinking dots animation */
        @keyframes thinkingDotPulse {
            0%, 80%, 100% {
                transform: translateY(0) scale(1);
                opacity: 0.4;
            }
            40% {
                transform: translateY(-8px) scale(1.2);
                opacity: 1;
            }
        }

        .thinking-indicator {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 10px 0;
        }

        .thinking-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: var(--primary);
            border-radius: 50%;
            margin: 0 2px;
            animation: thinkingDotPulse 1.4s ease-in-out infinite;
            box-shadow: 0 0 10px rgba(127, 255, 212, 0.5);
        }

        .thinking-dot:nth-child(1) { animation-delay: 0s; }
        .thinking-dot:nth-child(2) { animation-delay: 0.2s; }
        .thinking-dot:nth-child(3) { animation-delay: 0.4s; }

        /* Ripple animation */
        @keyframes ripple {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }

        /* Slide down animation */
        @keyframes slideDown {
            to {
                opacity: 0;
                transform: translate(-50%, 10px);
            }
        }

        /* Message slide in animation */
        @keyframes messageSlideIn {
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .msg {
            opacity: 0;
            transform: translateY(20px);
            animation: messageSlideIn 0.5s ease-out forwards;
        }

        .msg:nth-child(even) {
            animation-delay: 0.1s;
        }

        /* Bubble shimmer effect */
        @keyframes bubbleShimmer {
            0% {
                transform: translateX(-100%) translateY(-100%) rotate(45deg);
                opacity: 0;
            }
            50% {
                opacity: 1;
            }
            100% {
                transform: translateX(100%) translateY(100%) rotate(45deg);
                opacity: 0;
            }
        }

        /* Notification pulse animation */
        @keyframes notificationPulse {
            0%, 100% {
                transform: scale(1);
                opacity: 1;
            }
            50% {
                transform: scale(1.2);
                opacity: 0.8;
            }
        }

        /* Loading spinner animation */
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Progress bar animation */
        @keyframes progressFill {
            from { width: 0%; }
            to { width: 100%; }
        }

        /* Status pulse animation */
        @keyframes statusPulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        /* Glow animation */
        @keyframes glowPulse {
            0%, 100% { opacity: 0.4; }
            50% { opacity: 0.8; }
        }

        /* Floating animation */
        @keyframes aiFloat {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-3px); }
        }
    `;

  document.head.appendChild(style);
}

/**
 * Create a progress bar animation
 * @param {HTMLElement} container - Container element
 * @param {number} duration - Animation duration in milliseconds
 * @param {Function} callback - Completion callback
 */
export function createProgressBar(container, duration, callback) {
  const progressBar = document.createElement('div');
  progressBar.className = 'progress-bar';

  const progressFill = document.createElement('div');
  progressFill.className = 'progress-fill';
  progressFill.style.transition = `width ${duration}ms ease-in-out`;

  progressBar.appendChild(progressFill);
  container.appendChild(progressBar);

  // Trigger animation
  setTimeout(() => {
    progressFill.style.width = '100%';
  }, 50);

  // Complete callback
  setTimeout(() => {
    if (callback) callback();
    progressBar.remove();
  }, duration + 100);
}

/**
 * Animate number counting
 * @param {HTMLElement} element - Element to update
 * @param {number} start - Starting number
 * @param {number} end - Ending number
 * @param {number} duration - Animation duration in milliseconds
 */
export function animateNumber(element, start, end, duration) {
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
 * Create a staggered animation for multiple elements
 * @param {NodeList} elements - Elements to animate
 * @param {string} animationClass - CSS class for animation
 * @param {number} stagger - Delay between each element in milliseconds
 */
export function staggeredAnimation(elements, animationClass, stagger = 100) {
  elements.forEach((element, index) => {
    setTimeout(() => {
      element.classList.add(animationClass);
    }, index * stagger);
  });
}

/**
 * Fade in element with animation
 * @param {HTMLElement} element - Element to fade in
 * @param {number} duration - Animation duration in milliseconds
 */
export function fadeIn(element, duration = 300) {
  element.style.opacity = '0';
  element.style.display = 'block';

  const startTime = performance.now();

  function animate(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);

    element.style.opacity = progress;

    if (progress < 1) {
      requestAnimationFrame(animate);
    }
  }

  requestAnimationFrame(animate);
}

/**
 * Fade out element with animation
 * @param {HTMLElement} element - Element to fade out
 * @param {number} duration - Animation duration in milliseconds
 * @param {Function} callback - Completion callback
 */
export function fadeOut(element, duration = 300, callback) {
  const startTime = performance.now();

  function animate(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);

    element.style.opacity = 1 - progress;

    if (progress < 1) {
      requestAnimationFrame(animate);
    } else {
      element.style.display = 'none';
      if (callback) callback();
    }
  }

  requestAnimationFrame(animate);
}