/**
 * Particle Background System for IntelliSearch
 * @fileoverview Interactive particle background with green theme matching docs version
 */

class ParticleSystem {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.particles = [];
        this.animationId = null;
        this.mouseX = 0;
        this.mouseY = 0;
        this.isInitialized = false;
    }

    /**
     * Initialize the particle system
     */
    init() {
        if (this.isInitialized) return;

        this.canvas = document.createElement('canvas');
        this.canvas.id = 'particles-canvas';
        this.canvas.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: -1;
            opacity: 0.6;
        `;

        document.body.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');

        if (!this.ctx) {
            console.warn('Failed to get 2D context for particle system');
            return;
        }

        this.setupCanvas();
        this.createParticles();
        this.setupEventListeners();
        this.animate();
        this.isInitialized = true;
    }

    /**
     * Setup canvas dimensions
     */
    setupCanvas() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    /**
     * Create particle instances
     */
    createParticles() {
        const particleCount = Math.min(50, Math.floor((this.canvas.width * this.canvas.height) / 15000));
        this.particles = [];

        for (let i = 0; i < particleCount; i++) {
            this.particles.push(new Particle(this.canvas));
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Window resize
        window.addEventListener('resize', () => {
            this.setupCanvas();
            this.createParticles();
        });

        // Mouse movement
        document.addEventListener('mousemove', (e) => {
            this.mouseX = e.clientX;
            this.mouseY = e.clientY;
        });

        // Touch support
        document.addEventListener('touchmove', (e) => {
            if (e.touches.length > 0) {
                this.mouseX = e.touches[0].clientX;
                this.mouseY = e.touches[0].clientY;
            }
        });
    }

    /**
     * Animation loop
     */
    animate() {
        if (!this.ctx) return;

        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        this.particles.forEach(particle => {
            particle.update(this.mouseX, this.mouseY);
            particle.draw(this.ctx);
        });

        this.connectParticles();
        this.animationId = requestAnimationFrame(() => this.animate());
    }

    /**
     * Draw connections between nearby particles
     */
    connectParticles() {
        for (let i = 0; i < this.particles.length; i++) {
            for (let j = i + 1; j < this.particles.length; j++) {
                const dx = this.particles[i].x - this.particles[j].x;
                const dy = this.particles[i].y - this.particles[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < 120) {
                    this.ctx.beginPath();
                    this.ctx.moveTo(this.particles[i].x, this.particles[i].y);
                    this.ctx.lineTo(this.particles[j].x, this.particles[j].y);
                    this.ctx.strokeStyle = `rgba(127, 255, 212, ${0.1 * (1 - distance / 120)})`;
                    this.ctx.stroke();
                }
            }
        }
    }

    /**
     * Clean up resources
     */
    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.parentNode.removeChild(this.canvas);
        }
        this.isInitialized = false;
    }
}

/**
 * Individual particle class
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

    update(mouseX, mouseY) {
        this.x += this.speedX;
        this.y += this.speedY;
        this.pulsePhase += this.pulseSpeed;

        // Boundary detection and bounce
        if (this.x < 0 || this.x > this.canvas.width) {
            this.speedX *= -1;
        }
        if (this.y < 0 || this.y > this.canvas.height) {
            this.speedY *= -1;
        }

        // Keep particles within bounds
        this.x = Math.max(0, Math.min(this.canvas.width, this.x));
        this.y = Math.max(0, Math.min(this.canvas.height, this.y));

        // Mouse repulsion effect
        this.applyMouseRepulsion(mouseX, mouseY);
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

// Global particle system instance
let particleSystem = null;

/**
 * Initialize particle system when DOM is ready
 */
function initParticleSystem() {
    if (particleSystem) {
        particleSystem.destroy();
    }
    particleSystem = new ParticleSystem();
    particleSystem.init();
}

/**
 * Clean up particle system
 */
function destroyParticleSystem() {
    if (particleSystem) {
        particleSystem.destroy();
        particleSystem = null;
    }
}

// Auto-initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initParticleSystem);
} else {
    initParticleSystem();
}

// Clean up on page unload
window.addEventListener('beforeunload', destroyParticleSystem);

// Export for external use
window.ParticleSystem = {
    init: initParticleSystem,
    destroy: destroyParticleSystem,
    instance: () => particleSystem
};