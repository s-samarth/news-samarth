// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// State Management
const state = {
    articles: [],
    filteredArticles: [],
    currentFilter: 'all',
    searchQuery: '',
    isLoading: false,
    selectedDate: new Date().toISOString().split('T')[0],
    fetchStatus: null
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
    newsletterContent: document.getElementById('newsletterContent'),
    newsletterDate: document.getElementById('newsletterDate'),
    // Fetch status modal
    fetchStatusModal: document.getElementById('fetchStatusModal'),
    closeFetchModal: document.getElementById('closeFetchModal'),
    fetchStatusContent: document.getElementById('fetchStatusContent'),
    fetchStatusActions: document.getElementById('fetchStatusActions'),
    fetchContinue: document.getElementById('fetchContinue'),
    fetchRetry: document.getElementById('fetchRetry'),
    fetchCancel: document.getElementById('fetchCancel')
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

function initDatePicker() {
    const today = new Date();
    const minDate = new Date(today);
    minDate.setDate(minDate.getDate() - 30);

    elements.newsletterDate.max = today.toISOString().split('T')[0];
    elements.newsletterDate.min = minDate.toISOString().split('T')[0];
    elements.newsletterDate.value = today.toISOString().split('T')[0];
    state.selectedDate = elements.newsletterDate.value;
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

async function apiFetchNewsForDate(date) {
    const response = await fetch(`${API_BASE_URL}/newsletter/fetch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date })
    });
    if (!response.ok) throw new Error('Fetch failed');
    return await response.json();
}

async function apiGenerateNewsletter(date, force = false) {
    const response = await fetch(`${API_BASE_URL}/newsletter/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date, force })
    });
    if (!response.ok) throw new Error('Newsletter generation failed');
    return await response.json();
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

function renderNewsletterContent(data) {
    // Handle both new format (from generate endpoint) and legacy format
    const content = data.newsletter || data.content || '';
    if (!content) {
        return '<p>No newsletter content available.</p>';
    }

    const sections = content.split('\n\n').filter(s => s.trim());
    let html = '';

    // Main Content — render markdown-like sections
    html += `
        <div class="newsletter-section">
            ${sections.map(section => {
                // Convert markdown headers
                let s = section;
                s = s.replace(/^### (.+)$/gm, '<h4>$1</h4>');
                s = s.replace(/^## (.+)$/gm, '<h3>$1</h3>');
                s = s.replace(/^# (.+)$/gm, '<h2>$1</h2>');
                s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
                s = s.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank">$1</a>');
                return `<p>${s}</p>`;
            }).join('')}
        </div>
    `;

    // Metadata
    const meta = data.metadata || {};
    if (meta.date || meta.article_count) {
        html += `
            <div class="newsletter-section" style="margin-top: 32px; padding-top: 20px; border-top: 1px solid var(--border-color);">
                <p style="font-size: 0.85rem; color: var(--text-muted);">
                    ${meta.date ? `Date: ${meta.date}` : ''}
                    ${meta.article_count ? ` · ${meta.article_count} articles analyzed` : ''}
                    ${meta.model_used ? ` · Model: ${meta.model_used}` : ''}
                    ${data.cached ? ' · (cached)' : ''}
                </p>
            </div>
        `;
    }

    return html;
}

function renderFetchStatus(result) {
    const platforms = result.platforms || {};
    const statusColors = {
        success: '#10b981',
        failed: '#ef4444',
        partial: '#f59e0b'
    };

    let html = `
        <div class="fetch-status-summary">
            <div class="fetch-status-badge" style="background: ${statusColors[result.overall_status] || '#6b7280'}">
                ${result.overall_status === 'success' ? 'All platforms fetched successfully' :
                  result.overall_status === 'partial' ? 'Some platforms failed' :
                  'All platforms failed'}
            </div>
            <p class="fetch-total">Total articles fetched: <strong>${result.total_articles}</strong></p>
        </div>
        <div class="fetch-platform-list">
    `;

    for (const [platform, info] of Object.entries(platforms)) {
        const pConfig = platformConfig[platform] || { color: '#6b7280', badge: '?', label: platform };
        const statusIcon = info.status === 'success' ? '&#10003;' : '&#10007;';
        const statusColor = info.status === 'success' ? '#10b981' : '#ef4444';

        html += `
            <div class="fetch-platform-row">
                <div class="fetch-platform-info">
                    <span class="platform-badge" style="background: ${pConfig.color}">${pConfig.badge}</span>
                    <span class="fetch-platform-name">${pConfig.label}</span>
                </div>
                <div class="fetch-platform-result">
                    <span style="color: ${statusColor}; font-weight: 600;">${statusIcon} ${info.status}</span>
                    <span class="fetch-platform-count">${info.count} articles</span>
                </div>
                ${info.error ? `<div class="fetch-platform-error">${info.error}</div>` : ''}
                ${info.note ? `<div class="fetch-platform-note">${info.note}</div>` : ''}
            </div>
        `;
    }

    html += '</div>';
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

    elements.filterBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.platform === platform);
    });

    if (platform === 'all') {
        state.filteredArticles = [...state.articles];
    } else {
        state.filteredArticles = state.articles.filter(a => a.platform === platform);
    }

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

// Fetch Status Modal
function openFetchStatusModal() {
    elements.fetchStatusModal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeFetchStatusModal() {
    elements.fetchStatusModal.classList.remove('active');
    elements.fetchStatusActions.style.display = 'none';
    document.body.style.overflow = '';
}

// Two-Phase Newsletter Generation Flow
async function handleGenerateNewsletter() {
    const date = elements.newsletterDate.value;
    if (!date) {
        showToast('Please select a date.');
        return;
    }
    state.selectedDate = date;

    // Phase 1: Try generating (will return cached if exists)
    openNewsletterModal();
    elements.newsletterContent.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner"></div>
            <p>Checking for existing newsletter for ${date}...</p>
        </div>
    `;

    try {
        const result = await apiGenerateNewsletter(date, false);

        if (result.success && result.cached) {
            // Newsletter already exists — show it
            elements.newsletterContent.innerHTML = renderNewsletterContent(result);
            showToast('Loaded cached newsletter.');
            return;
        }

        if (result.success && !result.cached) {
            // Generated on the fly (articles were already in DB)
            elements.newsletterContent.innerHTML = renderNewsletterContent(result);
            showToast('Newsletter generated successfully!');
            return;
        }

        // If generation failed (likely no articles), proceed to fetch phase
        closeNewsletterModal();
    } catch (error) {
        // Generation failed — need to fetch first
        closeNewsletterModal();
    }

    // Phase 2: Fetch news for the date
    await startFetchPhase(date);
}

async function startFetchPhase(date) {
    openFetchStatusModal();
    elements.fetchStatusActions.style.display = 'none';
    elements.fetchStatusContent.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner"></div>
            <p>Fetching news for ${date} from all platforms...</p>
            <p style="font-size: 0.85rem; margin-top: 8px; color: var(--text-muted);">
                This may take a moment as we scrape multiple sources
            </p>
        </div>
    `;

    try {
        const result = await apiFetchNewsForDate(date);
        state.fetchStatus = result;

        // Show status
        elements.fetchStatusContent.innerHTML = renderFetchStatus(result);

        if (result.overall_status === 'success') {
            // Auto-proceed to generation
            closeFetchStatusModal();
            await proceedToGenerate(date);
        } else {
            // Show action buttons for partial/failed
            elements.fetchStatusActions.style.display = 'flex';
        }
    } catch (error) {
        elements.fetchStatusContent.innerHTML = `
            <div class="empty-state">
                <span class="empty-icon">&#10007;</span>
                <h3>Fetch Failed</h3>
                <p>${error.message || 'Could not fetch news. Is the API running?'}</p>
            </div>
        `;
        elements.fetchStatusActions.style.display = 'flex';
    }
}

async function proceedToGenerate(date) {
    openNewsletterModal();
    elements.newsletterContent.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner"></div>
            <p>Generating newsletter for ${date}...</p>
            <p style="font-size: 0.85rem; margin-top: 8px; color: var(--text-muted);">
                AI agents are analyzing and ranking your news
            </p>
        </div>
    `;

    try {
        const result = await apiGenerateNewsletter(date, true);
        if (result.success) {
            elements.newsletterContent.innerHTML = renderNewsletterContent(result);
            showToast('Newsletter generated successfully!');
        } else {
            elements.newsletterContent.innerHTML = `
                <div class="empty-state">
                    <span class="empty-icon">&#10007;</span>
                    <h3>Generation Failed</h3>
                    <p>${result.error || 'Please try again later.'}</p>
                </div>
            `;
        }
    } catch (error) {
        elements.newsletterContent.innerHTML = `
            <div class="empty-state">
                <span class="empty-icon">&#10007;</span>
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
        if (newsletter && newsletter.success) {
            elements.newsletterContent.innerHTML = renderNewsletterContent(newsletter);
        } else {
            elements.newsletterContent.innerHTML = `
                <div class="empty-state">
                    <span class="empty-icon">&#128237;</span>
                    <h3>No Newsletter Found</h3>
                    <p>Generate a new newsletter to get started!</p>
                </div>
            `;
        }
    } catch (error) {
        elements.newsletterContent.innerHTML = `
            <div class="empty-state">
                <span class="empty-icon">&#10007;</span>
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
    initDatePicker();

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

    updateHealthStatus();
    setInterval(updateHealthStatus, 30000);
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
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

    // Newsletter date picker
    elements.newsletterDate.addEventListener('change', (e) => {
        state.selectedDate = e.target.value;
    });

    // Newsletter buttons
    elements.generateNewsletter.addEventListener('click', handleGenerateNewsletter);
    elements.viewLatestNewsletter.addEventListener('click', handleViewLatestNewsletter);

    // Newsletter modal
    elements.closeModal.addEventListener('click', closeNewsletterModal);
    elements.newsletterModal.addEventListener('click', (e) => {
        if (e.target === elements.newsletterModal) closeNewsletterModal();
    });

    // Fetch status modal
    elements.closeFetchModal.addEventListener('click', closeFetchStatusModal);
    elements.fetchStatusModal.addEventListener('click', (e) => {
        if (e.target === elements.fetchStatusModal) closeFetchStatusModal();
    });

    // Fetch status action buttons
    elements.fetchContinue.addEventListener('click', () => {
        closeFetchStatusModal();
        proceedToGenerate(state.selectedDate);
    });

    elements.fetchRetry.addEventListener('click', () => {
        startFetchPhase(state.selectedDate);
    });

    elements.fetchCancel.addEventListener('click', () => {
        closeFetchStatusModal();
        showToast('Operation cancelled.');
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeNewsletterModal();
            closeFetchStatusModal();
        }
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
