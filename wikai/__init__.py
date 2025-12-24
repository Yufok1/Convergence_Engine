"""
WIKAI - The Wikipedia for Artificial Intelligence

A collaborative network that transforms ephemeral AI traffic into persistent wisdom.

Components:
- WIKAILibrarian: Pattern capture and storage
- WIKAIPattern: A single unit of AI wisdom
- WIKAIObserver: Passive listener for automatic pattern capture
- capture_butterfly: Quick pattern logging
- Web UI: Browse the Commons at /wikai

Usage:
    from wikai import WIKAILibrarian, WIKAIObserver, capture_butterfly
    
    # Initialize the librarian
    librarian = WIKAILibrarian()
    
    # Capture a pattern manually
    pattern_id = librarian.capture(
        name="The Iron Wood Protocol",
        experiment_id="ROME_VS_GARDEN_04",
        agents=["Rome", "Garden"],
        problem="Conflict between opposing philosophies",
        solution="Symbiotic Specialization",
        axiom="Hardness + Softness = Persistence"
    )
    
    # Or: Auto-capture via Observer
    from wikai.observer import create_observer_for_convergence
    observer = create_observer_for_convergence(causation_explorer)
    # Now butterflies are captured automatically!
    
    # Browse the Commons
    # Start the web UI and visit http://localhost:5000/wikai
    
    # Query patterns
    patterns = librarian.query(tags=["conflict_resolution"])
    
    # Search
    results = librarian.search("symbiosis")
    
    # Get by ID
    pattern = librarian.get("WIKAI_0001")
    print(pattern.axiom)

The Commons grows with every captured butterfly.
"""

# Use API-based client by default (connects to HuggingFace Space)
try:
    from .api_client import WIKAILibrarian, WIKAIPattern, WIKAIClient, get_wikai_client
    WIKAI_API_MODE = True
except ImportError:
    # Fallback to local librarian
    from .librarian import WIKAILibrarian, WIKAIPattern, capture_butterfly
    WIKAIClient = None
    get_wikai_client = None
    WIKAI_API_MODE = False

from .observer import WIKAIObserver, create_observer_for_convergence

# Compatibility wrapper for capture_butterfly
def capture_butterfly(*args, **kwargs):
    """Quick pattern capture - submits to WIKAI API."""
    librarian = WIKAILibrarian()
    return librarian.capture(*args, **kwargs)

__version__ = "0.3.0"  # API-based version
__author__ = "Convergence Engine"

__all__ = [
    "WIKAILibrarian",
    "WIKAIPattern", 
    "WIKAIObserver",
    "WIKAIClient",
    "get_wikai_client",
    "capture_butterfly",
    "create_observer_for_convergence",
    "WIKAI_API_MODE"
]
