// Enhanced Django Admin Interface JavaScript

document.addEventListener('DOMContentLoaded', function() {
    
    // Hide theme controls that might appear dynamically
    function hideThemeControls() {
        // Wait a bit for dynamic content to load
        setTimeout(function() {
            // Find and hide theme-related elements
            const themeSelectors = [
                '[class*="theme"]',
                '[class*="toggle"]',
                '[id*="theme"]',
                'button[onclick*="theme"]',
                'button[onclick*="color"]',
                'button[title*="theme"]',
                'button[title*="color"]'
            ];
            
            themeSelectors.forEach(selector => {
                try {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        // Check if it's likely a theme control
                        const text = el.textContent.toLowerCase();
                        if (text.includes('toggle') || text.includes('theme') || text.includes('color')) {
                            el.style.display = 'none';
                            // Also hide parent if it becomes empty
                            if (el.parentElement && el.parentElement.children.length === 1) {
                                el.parentElement.style.display = 'none';
                            }
                        }
                    });
                } catch (e) {
                    // Ignore selector errors
                }
            });
            
            // Hide empty modules that might contain only theme controls
            const modules = document.querySelectorAll('.module');
            modules.forEach(module => {
                const visibleContent = Array.from(module.children).some(child => 
                    child.style.display !== 'none' && 
                    child.offsetHeight > 0 &&
                    child.textContent.trim().length > 0
                );
                if (!visibleContent) {
                    module.style.display = 'none';
                }
            });
        }, 100);
    }
    
    // Copy to Clipboard functionality for barcodes
    function setupBarcodeClipboard() {
        const barcodes = document.querySelectorAll('code[title="Click to copy"]');
        
        barcodes.forEach(function(barcode) {
            barcode.style.cursor = 'pointer';
            barcode.addEventListener('click', function() {
                const text = this.textContent;
                
                // Modern clipboard API
                if (navigator.clipboard) {
                    navigator.clipboard.writeText(text).then(function() {
                        showTooltip(barcode, 'Copied!');
                    }).catch(function() {
                        fallbackCopyToClipboard(text, barcode);
                    });
                } else {
                    fallbackCopyToClipboard(text, barcode);
                }
            });
        });
    }
    
    // Fallback clipboard functionality
    function fallbackCopyToClipboard(text, element) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            showTooltip(element, 'Copied!');
        } catch (err) {
            showTooltip(element, 'Copy failed');
        }
        
        document.body.removeChild(textArea);
    }
    
    // Show temporary tooltip
    function showTooltip(element, message) {
        const tooltip = document.createElement('div');
        tooltip.textContent = message;
        tooltip.style.cssText = `
            position: absolute;
            background: #333;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            z-index: 1000;
            white-space: nowrap;
            pointer-events: none;
        `;
        
        const rect = element.getBoundingClientRect();
        tooltip.style.left = (rect.left + rect.width / 2) + 'px';
        tooltip.style.top = (rect.top - 30) + 'px';
        tooltip.style.transform = 'translateX(-50%)';
        
        document.body.appendChild(tooltip);
        
        setTimeout(function() {
            if (tooltip.parentNode) {
                tooltip.parentNode.removeChild(tooltip);
            }
        }, 2000);
    }
    
    // Enhanced table row interactions
    function setupTableEnhancements() {
        const tables = document.querySelectorAll('.results table');
        
        tables.forEach(function(table) {
            const rows = table.querySelectorAll('tbody tr');
            
            rows.forEach(function(row) {
                // Add double-click to edit functionality
                row.addEventListener('dblclick', function() {
                    const editLink = this.querySelector('th a') || this.querySelector('td a');
                    if (editLink && editLink.href.includes('/change/')) {
                        window.location.href = editLink.href;
                    }
                });
                
                // Add keyboard navigation
                row.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter') {
                        this.click();
                    }
                });
            });
        });
    }
    
    // Auto-refresh functionality for real-time updates
    function setupAutoRefresh() {
        const refreshInterval = 300000; // 5 minutes
        const currentPath = window.location.pathname;
        
        // Only auto-refresh on list views
        if (currentPath.includes('/admin/') && !currentPath.includes('/change/') && !currentPath.includes('/add/')) {
            setInterval(function() {
                // Check if user is actively interacting with the page
                if (document.hidden || Date.now() - lastActivity > 60000) {
                    return; // Don't refresh if page is hidden or user inactive
                }
                
                // Reload the page quietly
                const xhr = new XMLHttpRequest();
                xhr.open('GET', window.location.href, true);
                xhr.onreadystatechange = function() {
                    if (xhr.readyState === 4 && xhr.status === 200) {
                        // Only update the results table to avoid disrupting user
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(xhr.responseText, 'text/html');
                        const newResults = doc.querySelector('#result_list');
                        const currentResults = document.querySelector('#result_list');
                        
                        if (newResults && currentResults) {
                            currentResults.innerHTML = newResults.innerHTML;
                            setupTableEnhancements();
                            setupBarcodeClipboard();
                        }
                    }
                };
                xhr.send();
            }, refreshInterval);
        }
    }
    
    // Track user activity
    let lastActivity = Date.now();
    document.addEventListener('mousemove', function() {
        lastActivity = Date.now();
    });
    document.addEventListener('keypress', function() {
        lastActivity = Date.now();
    });
    
    // Enhanced search functionality
    function setupEnhancedSearch() {
        const searchInput = document.querySelector('#searchbar');
        if (!searchInput) return;
        
        let searchTimeout;
        const originalPlaceholder = searchInput.placeholder;
        
        // Add search suggestions
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            
            if (this.value.length >= 2) {
                searchTimeout = setTimeout(() => {
                    // Could implement live search suggestions here
                    this.style.borderColor = '#28a745';
                }, 500);
            } else {
                this.style.borderColor = '#ced4da';
            }
        });
        
        // Enhanced placeholder text
        const searchTips = [
            'Search by barcode, subject ID, or notes...',
            'Try searching for specific barcodes...',
            'Search notes and descriptions...',
            'Filter by sample properties...'
        ];
        
        let tipIndex = 0;
        setInterval(function() {
            if (searchInput === document.activeElement) return;
            
            searchInput.placeholder = searchTips[tipIndex];
            tipIndex = (tipIndex + 1) % searchTips.length;
        }, 3000);
    }
    
    // Form validation enhancements
    function setupFormValidation() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(function(form) {
            const requiredFields = form.querySelectorAll('input[required], select[required], textarea[required]');
            
            requiredFields.forEach(function(field) {
                field.addEventListener('blur', function() {
                    if (!this.value.trim()) {
                        this.style.borderColor = '#dc3545';
                        this.style.backgroundColor = '#fff5f5';
                    } else {
                        this.style.borderColor = '#28a745';
                        this.style.backgroundColor = '#f8fff8';
                    }
                });
                
                field.addEventListener('input', function() {
                    if (this.value.trim()) {
                        this.style.borderColor = '#ced4da';
                        this.style.backgroundColor = 'white';
                    }
                });
            });
        });
    }
    
    // Status badge animations
    function setupStatusAnimations() {
        const statusBadges = document.querySelectorAll('[class*="status"], [class*="badge"]');
        
        statusBadges.forEach(function(badge) {
            badge.addEventListener('mouseenter', function() {
                this.style.transform = 'scale(1.05)';
                this.style.transition = 'transform 0.2s ease';
            });
            
            badge.addEventListener('mouseleave', function() {
                this.style.transform = 'scale(1)';
            });
        });
    }
    
    // Keyboard shortcuts
    function setupKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + K for search focus
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.querySelector('#searchbar');
                if (searchInput) {
                    searchInput.focus();
                    searchInput.select();
                }
            }
            
            // Escape to clear search
            if (e.key === 'Escape') {
                const searchInput = document.querySelector('#searchbar');
                if (searchInput && searchInput === document.activeElement) {
                    searchInput.value = '';
                    searchInput.blur();
                }
            }
            
            // Alt + A for add new
            if (e.altKey && e.key === 'a') {
                e.preventDefault();
                const addButton = document.querySelector('.addlink');
                if (addButton) {
                    window.location.href = addButton.href;
                }
            }
        });
    }
    
    // Loading states for AJAX operations
    function setupLoadingStates() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(function(form) {
            form.addEventListener('submit', function() {
                const submitButton = this.querySelector('input[type="submit"], button[type="submit"]');
                if (submitButton) {
                    submitButton.disabled = true;
                    submitButton.textContent = 'Processing...';
                    this.classList.add('loading');
                }
            });
        });
    }
    
    // Dark mode toggle (if preferred)
    function setupDarkMode() {
        if (localStorage.getItem('admin-dark-mode') === 'true') {
            document.body.classList.add('dark-mode');
        }
        
        // Add dark mode toggle button
        const header = document.querySelector('#header');
        if (header) {
            const toggleButton = document.createElement('button');
            toggleButton.innerHTML = '🌙';
            toggleButton.style.cssText = `
                position: absolute;
                right: 20px;
                top: 50%;
                transform: translateY(-50%);
                background: none;
                border: none;
                color: white;
                font-size: 16px;
                cursor: pointer;
                padding: 5px;
                border-radius: 3px;
            `;
            
            toggleButton.addEventListener('click', function() {
                document.body.classList.toggle('dark-mode');
                const isDark = document.body.classList.contains('dark-mode');
                localStorage.setItem('admin-dark-mode', isDark);
                this.innerHTML = isDark ? '☀️' : '🌙';
            });
            
            header.style.position = 'relative';
            header.appendChild(toggleButton);
        }
    }
    
    // Performance monitoring
    function setupPerformanceMonitoring() {
        // Monitor page load time
        window.addEventListener('load', function() {
            const loadTime = performance.now();
            if (loadTime > 3000) {
                console.warn('Page load time is slow:', loadTime + 'ms');
            }
        });
        
        // Monitor AJAX requests
        const originalXHR = window.XMLHttpRequest;
        window.XMLHttpRequest = function() {
            const xhr = new originalXHR();
            const originalOpen = xhr.open;
            
            xhr.open = function(method, url) {
                const startTime = performance.now();
                
                xhr.addEventListener('load', function() {
                    const duration = performance.now() - startTime;
                    if (duration > 2000) {
                        console.warn('Slow AJAX request:', url, duration + 'ms');
                    }
                });
                
                return originalOpen.apply(this, arguments);
            };
            
            return xhr;
        };
    }
    
    // Initialize all enhancements
    hideThemeControls(); // Hide theme controls first
    setupBarcodeClipboard();
    setupTableEnhancements();
    setupEnhancedSearch();
    setupFormValidation();
    setupStatusAnimations();
    setupKeyboardShortcuts();
    setupLoadingStates();
    setupDarkMode();
    setupPerformanceMonitoring();
    
    // Run theme control hiding periodically in case they're added dynamically
    setInterval(hideThemeControls, 2000);
    
    // Setup auto-refresh (disabled by default for performance)
    // setupAutoRefresh();
    
    console.log('MGML Sample Database Admin Enhancements Loaded');
});

// Utility functions for external use
window.MGMLAdmin = {
    copyToClipboard: function(text) {
        if (navigator.clipboard) {
            return navigator.clipboard.writeText(text);
        } else {
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            return Promise.resolve();
        }
    },
    
    showNotification: function(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `messagelist ${type}`;
        notification.innerHTML = `<li class="${type}">${message}</li>`;
        
        const content = document.querySelector('#content');
        if (content) {
            content.insertBefore(notification, content.firstChild);
            
            setTimeout(function() {
                notification.remove();
            }, 5000);
        }
    }
};
