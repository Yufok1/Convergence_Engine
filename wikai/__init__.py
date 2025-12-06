"""
WIKAI - The Wikipedia for Artificial Intelligence

A collaborative network that transforms ephemeral AI traffic into persistent wisdom.

Components:
- WIKAILibrarian: Pattern capture and storage
- WIKAIPattern: A single unit of AI wisdom
- WIKAIObserver: Passive listener for automatic pattern capture
- capture_butterfly: Quick pattern logging

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
    
    # Query patterns
    patterns = librarian.query(tags=["conflict_resolution"])
    
    # Search
    results = librarian.search("symbiosis")
    
    # Get by ID
    pattern = librarian.get("WIKAI_0001")
    print(pattern.axiom)

The Commons grows with every captured butterfly.
"""

from .librarian import WIKAILibrarian, WIKAIPattern, capture_butterfly
from .observer import WIKAIObserver, create_observer_for_convergence

__version__ = "0.1.0"
__author__ = "Convergence Engine"

__all__ = [
    "WIKAILibrarian",
    "WIKAIPattern", 
    "WIKAIObserver",
    "capture_butterfly",
    "create_observer_for_convergence"
]
