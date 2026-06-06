/**
 * EasiVisi - Theme Toggle & Dark Mode
 * Professional dark mode implementation with smooth transitions
 */

(function () {
    'use strict';

    // Theme management
    const THEME_KEY = 'easivisi-theme';
    const THEME_LIGHT = 'light';
    const THEME_DARK = 'dark';

    /**
     * Get the current theme from localStorage or system preference
     */
    function getCurrentTheme() {
        // Check localStorage first
        const savedTheme = localStorage.getItem(THEME_KEY);
        if (savedTheme) {
            return savedTheme;
        }

        // Check system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return THEME_DARK;
        }

        return THEME_LIGHT;
    }

    /**
     * Apply theme to document
     */
    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(THEME_KEY, theme);

        // Update toggle button icon
        updateToggleIcon(theme);

        // Dispatch custom event for other components
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
    }

    /**
     * Toggle between light and dark themes
     */
    function toggleTheme() {
        const currentTheme = getCurrentTheme();
        const newTheme = currentTheme === THEME_LIGHT ? THEME_DARK : THEME_LIGHT;
        applyTheme(newTheme);
    }

    /**
     * Update toggle button icon
     */
    function updateToggleIcon(theme) {
        const lightIcon = document.getElementById('lightIcon');
        const darkIcon = document.getElementById('darkIcon');

        if (lightIcon && darkIcon) {
            if (theme === THEME_DARK) {
                lightIcon.style.display = 'none';
                darkIcon.style.display = 'inline-block';
            } else {
                lightIcon.style.display = 'inline-block';
                darkIcon.style.display = 'none';
            }
        }
    }

    /**
     * Initialize theme on page load
     */
    function initTheme() {
        const theme = getCurrentTheme();
        applyTheme(theme);
    }

    /**
     * Setup theme toggle button
     */
    function setupToggleButton() {
        const toggleButton = document.getElementById('themeToggle');
        if (toggleButton) {
            toggleButton.addEventListener('click', toggleTheme);
        }
    }

    /**
     * Listen for system theme changes
     */
    function listenForSystemThemeChanges() {
        if (window.matchMedia) {
            const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');

            // Modern browsers
            if (darkModeQuery.addEventListener) {
                darkModeQuery.addEventListener('change', (e) => {
                    // Only auto-switch if user hasn't manually set a preference
                    if (!localStorage.getItem(THEME_KEY)) {
                        applyTheme(e.matches ? THEME_DARK : THEME_LIGHT);
                    }
                });
            }
            // Older browsers
            else if (darkModeQuery.addListener) {
                darkModeQuery.addListener((e) => {
                    if (!localStorage.getItem(THEME_KEY)) {
                        applyTheme(e.matches ? THEME_DARK : THEME_LIGHT);
                    }
                });
            }
        }
    }

    /**
     * Public API
     */
    window.EasiVisiTheme = {
        toggle: toggleTheme,
        setTheme: applyTheme,
        getTheme: getCurrentTheme,
        LIGHT: THEME_LIGHT,
        DARK: THEME_DARK
    };

    // Initialize immediately (before DOMContentLoaded to prevent flash)
    initTheme();

    // Setup after DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setupToggleButton();
            listenForSystemThemeChanges();
        });
    } else {
        setupToggleButton();
        listenForSystemThemeChanges();
    }

})();

/**
 * Enhanced Toast Notification System
 */
window.showToast = function (message, type = 'success', duration = 3000) {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    // Icon mapping
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };

    toast.innerHTML = `
    <i class="fas ${icons[type] || icons.info}"></i>
    <span>${message}</span>
  `;

    // Add to body
    document.body.appendChild(toast);

    // Trigger animation
    requestAnimationFrame(() => {
        toast.classList.add('show');
    });

    // Remove after duration
    setTimeout(() => {
        toast.classList.remove('show');
        toast.classList.add('hide');
        setTimeout(() => toast.remove(), 300);
    }, duration);
};

/**
 * API Call Helper with Error Handling
 */
window.apiCall = async function (url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Request failed');
        }

        return data;
    } catch (error) {
        showToast(error.message, 'error');
        throw error;
    }
};
