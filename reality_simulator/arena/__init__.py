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
    DRONE_WARFARE_GAMES,
    ASYMMETRIC_PAIRINGS,
    CONTINUOUS_ACTION_ENVS,
    
    # Helper functions
    is_discrete_game,
    get_discrete_games,
    
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
    'DRONE_WARFARE_GAMES',
    'ASYMMETRIC_PAIRINGS',
    'CONTINUOUS_ACTION_ENVS',
    
    # Helper functions
    'is_discrete_game',
    'get_discrete_games',
    
    # Convenience functions
    'create_arena',
    'quick_battle',
    
    # Live organism adapter
    'LiveOrganismAdapter',
    'create_adapter',
    'create_adapter_pair',
    
    # Real Gym runner
    'GymRunner',
    'get_gym_runner',
    'run_organism_in_gym',
    'GYM_AVAILABLE',
    
    # Drone warfare system
    'OrganismDroneAdapter',
    'DroneState',
    'DroneAction',
    'SingleDroneArena',
    'PYFLYT_AVAILABLE',
    'SwarmBattle',
    'BattleConfig',
    'BattleStatistics',
    'BattleOutcome',
    'run_alliance_battle',
    'DroneWarfareArena',
    'WarfareConfig',
    'create_drone_warfare_arena',
    
    # JSBSim Quadcopter physics (no C++ needed)
    'QuadcopterFDM',
    'QuadcopterEnv', 
    'MultiQuadcopterEnv',
    'QuadcopterConfig',
    'QuadcopterState',
    'QUADCOPTER_FDM_AVAILABLE',
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

# Import REAL gym runner
try:
    from .gym_runner import (
        GymRunner,
        get_gym_runner,
        run_organism_in_gym,
        GYM_AVAILABLE
    )
except ImportError:
    GymRunner = None
    get_gym_runner = None
    run_organism_in_gym = None
    GYM_AVAILABLE = False

# Import JSBSim quadcopter physics (no C++ required!)
try:
    from .jsbsim_quadcopter import (
        QuadcopterFDM,
        QuadcopterEnv,
        MultiQuadcopterEnv,
        QuadcopterConfig,
        QuadcopterState,
        JSBSIM_AVAILABLE as QUADCOPTER_FDM_AVAILABLE
    )
except ImportError:
    QuadcopterFDM = None
    QuadcopterEnv = None
    MultiQuadcopterEnv = None
    QuadcopterConfig = None
    QuadcopterState = None
    QUADCOPTER_FDM_AVAILABLE = False

# Import drone warfare system
try:
    from .drone_adapter import (
        OrganismDroneAdapter,
        DroneState,
        DroneAction,
        SingleDroneArena,
        PYFLYT_AVAILABLE,
        QUADCOPTER_FDM_AVAILABLE as _QUAD_AVAIL  # Re-check from adapter
    )
    from .swarm_battle import (
        SwarmBattle,
        BattleConfig,
        BattleStatistics,
        BattleOutcome,
        run_alliance_battle
    )
    from .drone_warfare import (
        DroneWarfareArena,
        WarfareConfig,
        create_drone_warfare_arena
    )
except ImportError as e:
    # Graceful degradation if PyFlyt not installed
    OrganismDroneAdapter = None
    DroneState = None
    DroneAction = None
    SingleDroneArena = None
    PYFLYT_AVAILABLE = False
    SwarmBattle = None
    BattleConfig = None
    BattleStatistics = None
    BattleOutcome = None
    run_alliance_battle = None
    DroneWarfareArena = None
    WarfareConfig = None
    create_drone_warfare_arena = None
