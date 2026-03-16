// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// State Management
const state = {
    articles: [],
    filteredArticles: [],
    currentFilter: 'all',
    searchQuery: '',
    isLoading: false
};

// Platform Configuration
const platformConfig = {
    substack: { color: '#FF6719', label: 'Substack', badge: 'S' },
    reddit: { color: '#FF4500', label: 'Reddit', badge: 'R' },
    youtube: { color: '#FF0000', label: 'YouTube', badge: 'Y' },
    twitter: { color: '#1DA1F2', label: 'Twitter/X', badge: 'X' }
};

// DOM Elements
const elements = {
    feedGrid: document.getElementById('feedGrid'),
    loadingSpinner: document.getElementById('loadingSpinner'),
    emptyState: document.getElementById('emptyState'),
    feedSubtitle: document.getElementById('feedSubtitle'),
    searchInput: document.getElementById('searchInput'),
    searchBtn: document.getElementById('searchBtn'),
    refreshBtn: document.getElementById('refreshFeed'),
    filterBtns: document.querySelectorAll('.filter-btn'),
    articleCount: document.getElementById('articleCount'),
    systemStatus: document.getElementById('systemStatus'),
    generateNewsletter: document.getElementById('generateNewsletter'),
    viewLatestNewsletter: document.getElementById('viewLatestNewsletter'),
    newsletterModal: document.getElementById('newsletterModal'),
    closeModal: document.getElementById('closeModal'),
    newsletterContent: document.getElementById('newsletterContent')
};

// Utility Functions
function formatRelativeTime(timestamp) {
    const now = new Date();
    const date = new Date(timestamp);
    const diffMs = now - date;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSecs < 60) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function truncateText(text, maxLength = 280) {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + '...';
}

function capitalizeFirst(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// API Functions
async function fetchFeed() {
    try {
        const response = await fetch(`${API_BASE_URL}/feed/recent?limit=50`);
        if (!response.ok) throw new Error('Failed to fetch feed');
        return await response.json();
    } catch (error) {
        console.error('Error fetching feed:', error);
        throw error;
    }
}

async function searchArticles(query) {
    try {
        const response = await fetch(`${API_BASE_URL}/feed/search?q=${encodeURIComponent(query)}&limit=50`);
        if (!response.ok) throw new Error('Search failed');
        return await response.json();
    } catch (error) {
        console.error('Error searching articles:', error);
        throw error;
    }
}

async function fetchHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (!response.ok) throw new Error('Health check failed');
        return await response.json();
    } catch (error) {
        console.error('Error fetching health:', error);
        return null;
    }
}

async function generateNewsletter() {
    try {
        const response = await fetch(`${API_BASE_URL}/newsletter/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ top_n: 15 })
        });
        if (!response.ok) throw new Error('Newsletter generation failed');
        return await response.json();
    } catch (error) {
        console.error('Error generating newsletter:', error);
        throw error;
    }
}

async function fetchLatestNewsletter() {
    try {
        const response = await fetch(`${API_BASE_URL}/newsletter/latest`);
        if (!response.ok) throw new Error('Failed to fetch newsletter');
        return await response.json();
    } catch (error) {
        console.error('Error fetching newsletter:', error);
        throw error;
    }
}

// Render Functions
function renderFeedCard(article) {
    const platform = platformConfig[article.platform] || platformConfig.substack;
    const hasImage = article.media_link && article.media_link.trim() !== '';
    const content = article.content_text || '';
    const isLongContent = content.length > 280;

    return `
        <article class="feed-card" data-platform="${article.platform}">
            <div class="card-top-bar">
                <div class="card-source">
                    <span class="card-platform-badge" style="background: ${platform.color}">
                        ${platform.badge}
                    </span>
                    <span class="source-name">${capitalizeFirst(article.source_name || 'Unknown')}</span>
                </div>
            </div>
            
            ${hasImage ? `
                <img 
                    src="${article.media_link}" 
                    alt="${article.title || 'Article image'}"
                    class="card-image"
                    onerror="this.style.display='none'"
                    loading="lazy"
                />
            ` : ''}
            
            <div class="card-body">
                <h3 class="card-title">
                    <a href="${article.url || '#'}" target="_blank" rel="noopener noreferrer">
                        ${article.title || 'Untitled'}
                    </a>
                </h3>
                
                ${content ? `
                    <p class="card-content ${isLongContent ? 'truncated' : ''}" id="content-${article.id}">
                        ${isLongContent ? truncateText(content) : content}
                    </p>
                    ${isLongContent ? `
                        <button class="read-more" onclick="toggleContent(${article.id}, ${content.length})">
                            Read More
                        </button>
                    ` : ''}
                ` : ''}
            </div>
            
            <footer class="card-footer">
                <span class="card-timestamp">
                    ${article.timestamp ? formatRelativeTime(article.timestamp) : 'Unknown time'}
                </span>
                <div class="card-actions">
                    <button class="card-action-btn" onclick="copyToClipboard('${article.url || ''}')" title="Copy link">
                        📋
                    </button>
                    <button class="card-action-btn" onclick="shareArticle('${article.title || ''}', '${article.url || ''}')" title="Share">
                        🔗
                    </button>
                </div>
            </footer>
        </article>
    `;
}

function renderNewsletterContent(newsletter) {
    if (!newsletter || !newsletter.content) {
        return '<p>No newsletter content available.</p>';
    }

    const sections = newsletter.content.split('\n\n').filter(s => s.trim());
    let html = '';

    // Executive Summary
    if (newsletter.executive_summary) {
        html += `
            <div class="newsletter-section">
                <h3>📊 Executive Summary</h3>
                <p>${newsletter.executive_summary}</p>
            </div>
        `;
    }

    // Main Content
    html += `
        <div class="newsletter-section">
            <h3>📰 Today's Top Stories</h3>
            ${sections.map(section => `<p>${section}</p>`).join('')}
        </div>
    `;

    // Sources
    if (newsletter.sources && newsletter.sources.length > 0) {
        html += `
            <div class="newsletter-section">
                <h3>🔗 Sources</h3>
                <div class="newsletter-sources">
                    ${newsletter.sources.map(source => {
                        const platform = platformConfig[source.platform] || platformConfig.substack;
                        return `
                            <span class="newsletter-source-tag">
                                <span class="platform-badge" style="background: ${platform.color}">${platform.badge}</span>
                                ${source.source_name}
                            </span>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }

    // Metadata
    html += `
        <div class="newsletter-section" style="margin-top: 32px; padding-top: 20px; border-top: 1px solid var(--border-color);">
            <p style="font-size: 0.85rem; color: var(--text-muted);">
                Generated on ${new Date(newsletter.timestamp).toLocaleString()} • 
                ${newsletter.total_articles || 0} articles analyzed • 
                ${newsletter.top_stories || 0} top stories selected
            </p>
        </div>
    `;

    return html;
}

// Event Handlers
function toggleContent(articleId, fullLength) {
    const contentEl = document.getElementById(`content-${articleId}`);
    const btn = contentEl.nextElementSibling;
    
    if (contentEl.classList.contains('truncated')) {
        contentEl.classList.remove('truncated');
        btn.textContent = 'Show Less';
    } else {
        contentEl.classList.add('truncated');
        btn.textContent = 'Read More';
    }
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Link copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

function shareArticle(title, url) {
    if (navigator.share) {
        navigator.share({ title, url });
    } else {
        copyToClipboard(url);
    }
}

function showToast(message) {
    // Simple toast notification
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: var(--accent-primary);
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        z-index: 2000;
        animation: fadeIn 0.3s ease;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Filter Functions
function filterArticles(platform) {
    state.currentFilter = platform;
    
    // Update active button
    elements.filterBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.platform === platform);
    });
    
    // Filter articles
    if (platform === 'all') {
        state.filteredArticles = [...state.articles];
    } else {
        state.filteredArticles = state.articles.filter(a => a.platform === platform);
    }
    
    // Update subtitle
    if (platform === 'all') {
        elements.feedSubtitle.textContent = 'Latest news from all sources';
    } else {
        elements.feedSubtitle.textContent = `Showing ${platformConfig[platform]?.label || platform} articles`;
    }
    
    renderFeed();
}

function searchArticlesHandler() {
    const query = elements.searchInput.value.trim();
    state.searchQuery = query;
    
    if (query) {
        performSearch(query);
    } else {
        filterArticles(state.currentFilter);
    }
}

async function performSearch(query) {
    setLoading(true);
    try {
        const results = await searchArticles(query);
        state.filteredArticles = results;
        elements.feedSubtitle.textContent = `Search results for "${query}"`;
        renderFeed();
    } catch (error) {
        showToast('Search failed. Please try again.');
    } finally {
        setLoading(false);
    }
}

// Render Functions
function renderFeed() {
    if (state.filteredArticles.length === 0) {
        elements.feedGrid.innerHTML = '';
        elements.emptyState.style.display = 'block';
        elements.loadingSpinner.style.display = 'none';
        return;
    }
    
    elements.emptyState.style.display = 'none';
    elements.feedGrid.innerHTML = state.filteredArticles.map(renderFeedCard).join('');
}

function setLoading(loading) {
    state.isLoading = loading;
    elements.loadingSpinner.style.display = loading ? 'flex' : 'none';
    elements.feedGrid.style.display = loading ? 'none' : 'grid';
}

// Newsletter Modal
function openNewsletterModal() {
    elements.newsletterModal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeNewsletterModal() {
    elements.newsletterModal.classList.remove('active');
    document.body.style.overflow = '';
}

async function handleGenerateNewsletter() {
    openNewsletterModal();
    elements.newsletterContent.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner"></div>
            <p>Generating your personalized newsletter...</p>
            <p style="font-size: 0.85rem; margin-top: 8px; color: var(--text-muted);">
                This may take a minute as AI agents analyze and rank your news
            </p>
        </div>
    `;
    
    try {
        const newsletter = await generateNewsletter();
        elements.newsletterContent.innerHTML = renderNewsletterContent(newsletter);
        showToast('Newsletter generated successfully!');
    } catch (error) {
        elements.newsletterContent.innerHTML = `
            <div class="empty-state">
                <span class="empty-icon">❌</span>
                <h3>Generation Failed</h3>
                <p>${error.message || 'Please try again later.'}</p>
            </div>
        `;
    }
}

async function handleViewLatestNewsletter() {
    openNewsletterModal();
    elements.newsletterContent.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner"></div>
            <p>Loading latest newsletter...</p>
        </div>
    `;
    
    try {
        const newsletter = await fetchLatestNewsletter();
        if (newsletter && newsletter.content) {
            elements.newsletterContent.innerHTML = renderNewsletterContent(newsletter);
        } else {
            elements.newsletterContent.innerHTML = `
                <div class="empty-state">
                    <span class="empty-icon">📭</span>
                    <h3>No Newsletter Found</h3>
                    <p>Generate a new newsletter to get started!</p>
                </div>
            `;
        }
    } catch (error) {
        elements.newsletterContent.innerHTML = `
            <div class="empty-state">
                <span class="empty-icon">❌</span>
                <h3>Failed to Load</h3>
                <p>${error.message || 'Please try again later.'}</p>
            </div>
        `;
    }
}

// Health Check
async function updateHealthStatus() {
    const health = await fetchHealth();
    if (health) {
        elements.articleCount.textContent = health.article_count || health.total_articles || '0';
        elements.systemStatus.textContent = 'Online';
        elements.systemStatus.className = 'stat-value status-ok';
    } else {
        elements.systemStatus.textContent = 'Offline';
        elements.systemStatus.className = 'stat-value status-error';
    }
}

// Initialize App
async function initApp() {
    setLoading(true);
    
    try {
        const articles = await fetchFeed();
        state.articles = articles;
        state.filteredArticles = articles;
        renderFeed();
    } catch (error) {
        elements.feedGrid.innerHTML = '';
        elements.emptyState.style.display = 'block';
        elements.emptyState.querySelector('h3').textContent = 'Failed to load feed';
        elements.emptyState.querySelector('p').textContent = 'Please check if the API server is running.';
    } finally {
        setLoading(false);
    }
    
    // Update health status
    updateHealthStatus();
    
    // Set up periodic health checks
    setInterval(updateHealthStatus, 30000);
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Initialize app
    initApp();
    
    // Filter buttons
    elements.filterBtns.forEach(btn => {
        btn.addEventListener('click', () => filterArticles(btn.dataset.platform));
    });
    
    // Search
    elements.searchBtn.addEventListener('click', searchArticlesHandler);
    elements.searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchArticlesHandler();
    });
    
    // Refresh
    elements.refreshBtn.addEventListener('click', () => {
        initApp();
        showToast('Feed refreshed!');
    });
    
    // Newsletter
    elements.generateNewsletter.addEventListener('click', handleGenerateNewsletter);
    elements.viewLatestNewsletter.addEventListener('click', handleViewLatestNewsletter);
    
    // Modal
    elements.closeModal.addEventListener('click', closeNewsletterModal);
    elements.newsletterModal.addEventListener('click', (e) => {
        if (e.target === elements.newsletterModal) closeNewsletterModal();
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeNewsletterModal();
        if (e.key === '/' && !e.ctrlKey && !e.metaKey) {
            e.preventDefault();
            elements.searchInput.focus();
        }
    });
});

// Make functions available globally for onclick handlers
window.toggleContent = toggleContent;
window.copyToClipboard = copyToClipboard;
window.shareArticle = shareArticle;