"""
📚 WIKAI Web UI - The Commons Browser

A web interface for browsing, searching, and exploring the WIKAI Commons.
Watch butterflies get captured in real-time. Browse patterns by tag.
Search for wisdom across all captured discoveries.

"The Library of Alexandria for AI. But this time, it won't burn."
"""

from flask import Blueprint, render_template_string, jsonify, request
from pathlib import Path
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Create Blueprint for WIKAI routes
wikai_bp = Blueprint('wikai', __name__, url_prefix='/wikai')

# ═══════════════════════════════════════════════════════════════════════════════
# WIKAI HTML TEMPLATE
# ═══════════════════════════════════════════════════════════════════════════════

WIKAI_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📚 WIKAI - The Commons</title>
    <style>
        :root {
            --bg-dark: #0d1117;
            --bg-card: #161b22;
            --bg-hover: #21262d;
            --border: #30363d;
            --text-primary: #e6edf3;
            --text-secondary: #8b949e;
            --accent-blue: #58a6ff;
            --accent-green: #3fb950;
            --accent-purple: #a371f7;
            --accent-orange: #d29922;
            --accent-red: #f85149;
            --accent-cyan: #39c5cf;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.5;
        }
        
        /* Header */
        .header {
            background: linear-gradient(135deg, #1a1f35 0%, #0d1117 100%);
            border-bottom: 1px solid var(--border);
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .logo-icon {
            font-size: 2.5em;
        }
        
        .logo-text h1 {
            font-size: 1.8em;
            font-weight: 600;
            background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .logo-text p {
            color: var(--text-secondary);
            font-size: 0.9em;
        }
        
        .stats {
            display: flex;
            gap: 30px;
        }
        
        .stat {
            text-align: center;
        }
        
        .stat-value {
            font-size: 1.8em;
            font-weight: 700;
            color: var(--accent-green);
        }
        
        .stat-label {
            font-size: 0.8em;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Main Layout */
        .main {
            display: grid;
            grid-template-columns: 280px 1fr 350px;
            gap: 0;
            min-height: calc(100vh - 100px);
        }
        
        /* Sidebar */
        .sidebar {
            background: var(--bg-card);
            border-right: 1px solid var(--border);
            padding: 20px;
            overflow-y: auto;
        }
        
        .sidebar h3 {
            color: var(--text-secondary);
            font-size: 0.75em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--border);
        }
        
        .search-box {
            position: relative;
            margin-bottom: 25px;
        }
        
        .search-box input {
            width: 100%;
            padding: 12px 15px 12px 40px;
            background: var(--bg-dark);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 0.95em;
        }
        
        .search-box input:focus {
            outline: none;
            border-color: var(--accent-blue);
            box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.1);
        }
        
        .search-box::before {
            content: "🔍";
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 1em;
        }
        
        .tag-cloud {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 25px;
        }
        
        .tag {
            background: var(--bg-dark);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 6px 14px;
            font-size: 0.85em;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .tag:hover {
            background: var(--bg-hover);
            border-color: var(--accent-blue);
        }
        
        .tag.active {
            background: var(--accent-blue);
            border-color: var(--accent-blue);
            color: white;
        }
        
        .tag-count {
            background: var(--bg-hover);
            border-radius: 10px;
            padding: 2px 8px;
            margin-left: 5px;
            font-size: 0.8em;
        }
        
        /* Pattern List */
        .pattern-list {
            list-style: none;
        }
        
        .pattern-item {
            padding: 12px 15px;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.2s ease;
            margin-bottom: 5px;
            border-left: 3px solid transparent;
        }
        
        .pattern-item:hover {
            background: var(--bg-hover);
        }
        
        .pattern-item.active {
            background: var(--bg-hover);
            border-left-color: var(--accent-purple);
        }
        
        .pattern-item h4 {
            font-size: 0.95em;
            font-weight: 500;
            margin-bottom: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .pattern-item .meta {
            font-size: 0.8em;
            color: var(--text-secondary);
        }
        
        /* Content Area */
        .content {
            padding: 30px 40px;
            overflow-y: auto;
        }
        
        .pattern-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
        }
        
        .pattern-header {
            padding: 25px 30px;
            border-bottom: 1px solid var(--border);
            background: linear-gradient(135deg, rgba(163, 113, 247, 0.1) 0%, transparent 100%);
        }
        
        .pattern-id {
            font-size: 0.8em;
            color: var(--accent-purple);
            font-family: monospace;
            margin-bottom: 8px;
        }
        
        .pattern-title {
            font-size: 1.6em;
            font-weight: 600;
            margin-bottom: 10px;
        }
        
        .pattern-origin {
            display: flex;
            gap: 20px;
            font-size: 0.9em;
            color: var(--text-secondary);
        }
        
        .pattern-body {
            padding: 25px 30px;
        }
        
        .section {
            margin-bottom: 30px;
        }
        
        .section-title {
            font-size: 0.75em;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-secondary);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .axiom-box {
            background: linear-gradient(135deg, rgba(57, 197, 207, 0.15) 0%, rgba(163, 113, 247, 0.15) 100%);
            border: 1px solid var(--accent-cyan);
            border-radius: 8px;
            padding: 20px 25px;
            font-size: 1.2em;
            font-style: italic;
            text-align: center;
            color: var(--accent-cyan);
        }
        
        .abstract {
            color: var(--text-primary);
            line-height: 1.7;
        }
        
        .mechanism-box {
            background: var(--bg-dark);
            border-radius: 8px;
            padding: 20px;
            font-family: monospace;
            font-size: 0.9em;
            white-space: pre-wrap;
            border: 1px solid var(--border);
        }
        
        .reasoning-chain {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .reasoning-step {
            display: flex;
            gap: 15px;
            align-items: flex-start;
        }
        
        .step-number {
            background: var(--accent-purple);
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.85em;
            font-weight: 600;
            flex-shrink: 0;
        }
        
        .step-content {
            flex: 1;
            padding-top: 3px;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
        }
        
        .metric-card {
            background: var(--bg-dark);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }
        
        .metric-value {
            font-size: 1.5em;
            font-weight: 700;
            color: var(--accent-green);
        }
        
        .metric-label {
            font-size: 0.75em;
            color: var(--text-secondary);
            text-transform: uppercase;
            margin-top: 5px;
        }
        
        .pattern-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        
        .pattern-tag {
            background: var(--bg-dark);
            border: 1px solid var(--border);
            border-radius: 15px;
            padding: 5px 12px;
            font-size: 0.85em;
            color: var(--text-secondary);
        }
        
        /* Live Feed */
        .live-feed {
            background: var(--bg-card);
            border-left: 1px solid var(--border);
            padding: 20px;
            overflow-y: auto;
        }
        
        .live-feed h3 {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
            font-size: 0.9em;
        }
        
        .live-indicator {
            width: 8px;
            height: 8px;
            background: var(--accent-green);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }
        
        .feed-item {
            background: var(--bg-dark);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 12px;
            border-left: 3px solid var(--accent-green);
        }
        
        .feed-item.capture {
            border-left-color: var(--accent-purple);
        }
        
        .feed-time {
            font-size: 0.75em;
            color: var(--text-secondary);
            margin-bottom: 5px;
        }
        
        .feed-title {
            font-weight: 500;
            margin-bottom: 5px;
        }
        
        .feed-detail {
            font-size: 0.85em;
            color: var(--text-secondary);
        }
        
        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 60px 40px;
            color: var(--text-secondary);
        }
        
        .empty-state-icon {
            font-size: 4em;
            margin-bottom: 20px;
            opacity: 0.5;
        }
        
        .empty-state h3 {
            font-size: 1.3em;
            color: var(--text-primary);
            margin-bottom: 10px;
        }
        
        /* Responsive */
        @media (max-width: 1200px) {
            .main {
                grid-template-columns: 250px 1fr;
            }
            .live-feed {
                display: none;
            }
        }
        
        @media (max-width: 768px) {
            .main {
                grid-template-columns: 1fr;
            }
            .sidebar {
                display: none;
            }
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="logo">
            <span class="logo-icon">📚</span>
            <div class="logo-text">
                <h1>WIKAI</h1>
                <p>The Wikipedia for Artificial Intelligence</p>
            </div>
        </div>
        <div class="stats">
            <div class="stat">
                <div class="stat-value" id="pattern-count">{{ pattern_count }}</div>
                <div class="stat-label">Patterns</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="axiom-count">{{ axiom_count }}</div>
                <div class="stat-label">Axioms</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="capture-rate">{{ capture_rate }}</div>
                <div class="stat-label">Today</div>
            </div>
        </div>
    </header>
    
    <main class="main">
        <!-- Sidebar -->
        <aside class="sidebar">
            <div class="search-box">
                <input type="text" id="search-input" placeholder="Search patterns...">
            </div>
            
            <h3>🏷️ Tags</h3>
            <div class="tag-cloud" id="tag-cloud">
                {% for tag, count in tags.items() %}
                <span class="tag" data-tag="{{ tag }}">{{ tag }}<span class="tag-count">{{ count }}</span></span>
                {% endfor %}
            </div>
            
            <h3>🦋 Recent Patterns</h3>
            <ul class="pattern-list" id="pattern-list">
                {% for pattern in patterns %}
                <li class="pattern-item" data-id="{{ pattern.id }}">
                    <h4>{{ pattern.name }}</h4>
                    <div class="meta">{{ pattern.id }} · {{ pattern.captured }}</div>
                </li>
                {% endfor %}
            </ul>
        </aside>
        
        <!-- Content -->
        <section class="content" id="content">
            {% if selected_pattern %}
            <div class="pattern-card">
                <div class="pattern-header">
                    <div class="pattern-id">{{ selected_pattern.id }}</div>
                    <h2 class="pattern-title">{{ selected_pattern.name }}</h2>
                    <div class="pattern-origin">
                        <span>🧪 {{ selected_pattern.origin.experiment_id }}</span>
                        <span>🤖 {{ selected_pattern.origin.agents | join(', ') }}</span>
                        <span>📅 {{ selected_pattern.origin.captured }}</span>
                    </div>
                </div>
                <div class="pattern-body">
                    <!-- Axiom -->
                    <div class="section">
                        <h3 class="section-title">💎 Axiom</h3>
                        <div class="axiom-box">"{{ selected_pattern.axiom }}"</div>
                    </div>
                    
                    <!-- Abstract -->
                    <div class="section">
                        <h3 class="section-title">📝 Abstract</h3>
                        <p class="abstract">{{ selected_pattern.abstract }}</p>
                    </div>
                    
                    <!-- Mechanism -->
                    <div class="section">
                        <h3 class="section-title">⚙️ Mechanism</h3>
                        <div class="mechanism-box">{{ selected_pattern.mechanism }}</div>
                    </div>
                    
                    <!-- Reasoning Chain -->
                    {% if selected_pattern.reasoning_chain %}
                    <div class="section">
                        <h3 class="section-title">🔗 Reasoning Chain</h3>
                        <div class="reasoning-chain">
                            {% for step in selected_pattern.reasoning_chain %}
                            <div class="reasoning-step">
                                <span class="step-number">{{ loop.index }}</span>
                                <div class="step-content">{{ step }}</div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                    {% endif %}
                    
                    <!-- Metrics -->
                    {% if selected_pattern.metrics %}
                    <div class="section">
                        <h3 class="section-title">📊 Metrics</h3>
                        <div class="metrics-grid">
                            <div class="metric-card">
                                <div class="metric-value">{{ "%.2f"|format(selected_pattern.metrics.stability_score or 0) }}</div>
                                <div class="metric-label">Stability</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{{ "%.2f"|format(selected_pattern.metrics.fitness_delta or 0) }}</div>
                                <div class="metric-label">Fitness Δ</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">{{ selected_pattern.metrics.convergence_cycles or 0 }}</div>
                                <div class="metric-label">Cycles</div>
                            </div>
                        </div>
                    </div>
                    {% endif %}
                    
                    <!-- Tags -->
                    <div class="section">
                        <h3 class="section-title">🏷️ Tags</h3>
                        <div class="pattern-tags">
                            {% for tag in selected_pattern.tags %}
                            <span class="pattern-tag">{{ tag }}</span>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
            {% else %}
            <div class="empty-state">
                <div class="empty-state-icon">🦋</div>
                <h3>Select a Pattern</h3>
                <p>Choose a pattern from the sidebar to view its details,<br>or wait for butterflies to discover new truths.</p>
            </div>
            {% endif %}
        </section>
        
        <!-- Live Feed -->
        <aside class="live-feed">
            <h3><span class="live-indicator"></span> Live Feed</h3>
            <div id="feed-items">
                <div class="feed-item">
                    <div class="feed-time">Waiting for butterflies...</div>
                    <div class="feed-title">🦋 Observer Active</div>
                    <div class="feed-detail">The WIKAI Observer is watching for convergent patterns.</div>
                </div>
            </div>
        </aside>
    </main>
    
    <script>
        // Pattern selection
        document.querySelectorAll('.pattern-item').forEach(item => {
            item.addEventListener('click', () => {
                const id = item.dataset.id;
                window.location.href = `/wikai?pattern=${id}`;
            });
        });
        
        // Tag filtering
        document.querySelectorAll('.tag').forEach(tag => {
            tag.addEventListener('click', () => {
                const tagName = tag.dataset.tag;
                window.location.href = `/wikai?tag=${tagName}`;
            });
        });
        
        // Search
        const searchInput = document.getElementById('search-input');
        let searchTimeout;
        searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                const query = searchInput.value;
                if (query.length >= 2) {
                    window.location.href = `/wikai?search=${encodeURIComponent(query)}`;
                }
            }, 500);
        });
        
        // Live feed updates via SSE
        const feedItems = document.getElementById('feed-items');
        
        function addFeedItem(data) {
            const item = document.createElement('div');
            item.className = `feed-item ${data.type === 'capture' ? 'capture' : ''}`;
            item.innerHTML = `
                <div class="feed-time">${new Date().toLocaleTimeString()}</div>
                <div class="feed-title">${data.title}</div>
                <div class="feed-detail">${data.detail}</div>
            `;
            feedItems.insertBefore(item, feedItems.firstChild);
            
            // Keep only last 20 items
            while (feedItems.children.length > 20) {
                feedItems.removeChild(feedItems.lastChild);
            }
        }
        
        // Poll for updates every 5 seconds
        setInterval(async () => {
            try {
                const response = await fetch('/wikai/api/feed');
                const data = await response.json();
                if (data.items && data.items.length > 0) {
                    data.items.forEach(item => addFeedItem(item));
                }
            } catch (e) {
                // Silently fail
            }
        }, 5000);
        
        // Update stats periodically
        setInterval(async () => {
            try {
                const response = await fetch('/wikai/api/stats');
                const stats = await response.json();
                document.getElementById('pattern-count').textContent = stats.pattern_count;
                document.getElementById('axiom-count').textContent = stats.axiom_count;
                document.getElementById('capture-rate').textContent = stats.capture_rate;
            } catch (e) {
                // Silently fail
            }
        }, 10000);
    </script>
</body>
</html>
'''


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

def get_librarian():
    """Get or create the WIKAI Librarian instance."""
    from wikai import WIKAILibrarian
    # Use singleton pattern
    if not hasattr(get_librarian, '_instance'):
        get_librarian._instance = WIKAILibrarian()
    return get_librarian._instance


@wikai_bp.route('/')
def wikai_index():
    """Main WIKAI Commons browser."""
    librarian = get_librarian()
    
    # Get query parameters
    pattern_id = request.args.get('pattern')
    tag_filter = request.args.get('tag')
    search_query = request.args.get('search')
    
    # Get all patterns
    if search_query:
        patterns = librarian.search(search_query)
    elif tag_filter:
        patterns = librarian.query(tags=[tag_filter])
    else:
        patterns = librarian.query()
    
    # Sort by capture date (newest first)
    patterns.sort(key=lambda p: p.origin.get('captured', ''), reverse=True)
    
    # Build tag cloud
    tag_counts = {}
    all_patterns = librarian.query()
    for p in all_patterns:
        for tag in p.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    # Sort tags by count
    sorted_tags = dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:15])
    
    # Get selected pattern
    selected_pattern = None
    if pattern_id:
        selected_pattern = librarian.get(pattern_id)
    elif patterns:
        selected_pattern = patterns[0]  # Default to first
    
    # Convert pattern to dict for template
    pattern_dicts = []
    for p in patterns[:50]:  # Limit to 50
        pattern_dicts.append({
            'id': p.id,
            'name': p.name,
            'captured': p.origin.get('captured', 'Unknown')[:10]
        })
    
    selected_dict = None
    if selected_pattern:
        selected_dict = {
            'id': selected_pattern.id,
            'name': selected_pattern.name,
            'origin': selected_pattern.origin,
            'abstract': selected_pattern.abstract,
            'mechanism': selected_pattern.mechanism,
            'reasoning_chain': selected_pattern.reasoning_chain,
            'axiom': selected_pattern.axiom,
            'metrics': selected_pattern.metrics,
            'tags': selected_pattern.tags
        }
    
    # Calculate stats
    pattern_count = len(all_patterns)
    axiom_count = sum(1 for p in all_patterns if p.axiom)
    
    # Today's captures
    today = datetime.now().strftime('%Y-%m-%d')
    today_count = sum(1 for p in all_patterns if p.origin.get('captured', '').startswith(today))
    
    return render_template_string(
        WIKAI_TEMPLATE,
        patterns=pattern_dicts,
        tags=sorted_tags,
        selected_pattern=selected_dict,
        pattern_count=pattern_count,
        axiom_count=axiom_count,
        capture_rate=f"+{today_count}"
    )


@wikai_bp.route('/api/patterns')
def api_patterns():
    """Get all patterns as JSON."""
    librarian = get_librarian()
    
    tag = request.args.get('tag')
    search = request.args.get('search')
    
    if search:
        patterns = librarian.search(search)
    elif tag:
        patterns = librarian.query(tags=[tag])
    else:
        patterns = librarian.query()
    
    return jsonify({
        'count': len(patterns),
        'patterns': [
            {
                'id': p.id,
                'name': p.name,
                'axiom': p.axiom,
                'origin': p.origin,
                'tags': p.tags
            }
            for p in patterns
        ]
    })


@wikai_bp.route('/api/pattern/<pattern_id>')
def api_pattern(pattern_id):
    """Get a specific pattern."""
    librarian = get_librarian()
    pattern = librarian.get(pattern_id)
    
    if not pattern:
        return jsonify({'error': 'Pattern not found'}), 404
    
    return jsonify({
        'id': pattern.id,
        'name': pattern.name,
        'origin': pattern.origin,
        'abstract': pattern.abstract,
        'mechanism': pattern.mechanism,
        'reasoning_chain': pattern.reasoning_chain,
        'axiom': pattern.axiom,
        'tokens': pattern.tokens,
        'metrics': pattern.metrics,
        'tags': pattern.tags
    })


@wikai_bp.route('/api/stats')
def api_stats():
    """Get WIKAI statistics."""
    librarian = get_librarian()
    patterns = librarian.query()
    
    today = datetime.now().strftime('%Y-%m-%d')
    today_count = sum(1 for p in patterns if p.origin.get('captured', '').startswith(today))
    
    return jsonify({
        'pattern_count': len(patterns),
        'axiom_count': sum(1 for p in patterns if p.axiom),
        'capture_rate': f"+{today_count}"
    })


# Feed items buffer (in-memory, for live updates)
_feed_buffer = []
_feed_buffer_max = 100


def add_feed_item(title: str, detail: str, item_type: str = 'event'):
    """Add an item to the live feed buffer."""
    global _feed_buffer
    _feed_buffer.insert(0, {
        'title': title,
        'detail': detail,
        'type': item_type,
        'time': datetime.now().isoformat()
    })
    # Trim buffer
    if len(_feed_buffer) > _feed_buffer_max:
        _feed_buffer = _feed_buffer[:_feed_buffer_max]


@wikai_bp.route('/api/feed')
def api_feed():
    """Get recent feed items."""
    # Get items since last request (simplified: just return last 5)
    return jsonify({
        'items': _feed_buffer[:5]
    })


@wikai_bp.route('/api/search')
def api_search():
    """Search patterns."""
    librarian = get_librarian()
    query = request.args.get('q', '')
    
    if len(query) < 2:
        return jsonify({'error': 'Query too short', 'results': []})
    
    results = librarian.search(query)
    
    return jsonify({
        'query': query,
        'count': len(results),
        'results': [
            {
                'id': p.id,
                'name': p.name,
                'axiom': p.axiom,
                'score': 1.0  # Simple matching doesn't have scores
            }
            for p in results[:20]
        ]
    })


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

def register_wikai_routes(app):
    """Register WIKAI routes with the Flask app."""
    app.register_blueprint(wikai_bp)
    logger.info("[WIKAI] 📚 Web UI routes registered at /wikai")
    return app


def notify_capture(pattern_id: str, pattern_name: str, axiom: str):
    """Notify the feed when a pattern is captured."""
    add_feed_item(
        title=f"📸 Captured: {pattern_name}",
        detail=f"Axiom: \"{axiom}\"" if axiom else f"ID: {pattern_id}",
        item_type='capture'
    )


def notify_observation(event_type: str, details: str):
    """Notify the feed of an observation."""
    add_feed_item(
        title=f"🦋 {event_type}",
        detail=details,
        item_type='observation'
    )
