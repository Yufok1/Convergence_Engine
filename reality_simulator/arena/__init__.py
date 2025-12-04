"""
🎮 PROTON GAME ARENA
Arena module - Apprentice Adept inspired competition system.

The arena provides fair, gamified competition between organisms using the
game selection system from Piers Anthony's Apprentice Adept series.

The selection process itself is a meta-game that teaches:
- Self-awareness (knowing own strengths)
- Opponent modeling (theory of mind)  
- Strategic communication (language negotiation)
- Categorical reasoning (grid navigation)
- Trade-off analysis (every choice has consequences)

Usage:
    from reality_simulator.arena import ProtonGameArena, quick_battle
    
    arena = ProtonGameArena()
    arena.display_grid()  # Show available games
    
    result = quick_battle(organism_a, organism_b, bridge_a, bridge_b)
"""

from .proton_game import (
    # Core classes
    ProtonGameArena,
    GameDefinition,
    SelectionState,
    BattleResult,
    
    # Enums
    ChallengeType,
    ResourceType,
    GameDifficulty,
    
    # Data
    GAME_GRID,
    
    # Convenience functions
    create_arena,
    quick_battle
)

__all__ = [
    # Core classes
    'ProtonGameArena',
    'GameDefinition',
    'SelectionState',
    'BattleResult',
    
    # Enums
    'ChallengeType',
    'ResourceType',
    'GameDifficulty',
    
    
    # Data
    'GAME_GRID',
    
    # Convenience functions
    'create_arena',
    'quick_battle',
    
    # Live organism adapter
    'LiveOrganismAdapter',
    'create_adapter',
    'create_adapter_pair'
]

# Import live organism adapter
try:
    from .live_organism_adapter import (
        LiveOrganismAdapter,
        create_adapter,
        create_adapter_pair
    )
except ImportError:
    # Graceful degradation if not available
    LiveOrganismAdapter = None
    create_adapter = None
    create_adapter_pair = None
