"""
Evolution submodule - Tournament-based evolutionary systems

Contains:
- HighlanderProtocol: "There can be only one" tournament orchestration
- BattleArena: Organism combat and trait battles
- GerminationPool: New organism spawning with genetic strategies
- AllianceWarfareSystem: Collective warfare for existential dominance
"""

from .highlander_protocol import (
    HighlanderProtocol,
    HighlanderPhase,
    RelationshipType,
    OrganismStats,
    Alliance,
    BattleResult,
    run_tournament
)

from .battle_arena import (
    BattleArena,
    BattleType,
    TraitAdvantage
)

from .germination_pool import (
    GerminationPool,
    GerminationStrategy,
    GeneticMaterial,
    GerminationCandidate,
    integrate_germination_with_highlander
)

from .alliance_warfare import (
    AllianceWarfareSystem,
    PlanetaryAlliance,
    OrganismReputation,
    AllianceProposal,
    TerritorialDomain,
    AllianceRole,
    ProposalType,
    integrate_alliance_warfare_with_highlander,
    # Confederation (Super-Alliance) exports
    Confederation,
    ConfederationTier
)

__all__ = [
    # Highlander Protocol
    'HighlanderProtocol',
    'HighlanderPhase',
    'RelationshipType',
    'OrganismStats',
    'Alliance',
    'BattleResult',
    'run_tournament',
    # Battle Arena
    'BattleArena',
    'BattleType',
    'TraitAdvantage',
    # Germination Pool
    'GerminationPool',
    'GerminationStrategy',
    'GeneticMaterial',
    'GerminationCandidate',
    'integrate_germination_with_highlander',
    # Alliance Warfare
    'AllianceWarfareSystem',
    'PlanetaryAlliance',
    'OrganismReputation',
    'AllianceProposal',
    'TerritorialDomain',
    'AllianceRole',
    'ProposalType',
    'integrate_alliance_warfare_with_highlander',
    # Confederation (Super-Alliance)
    'Confederation',
    'ConfederationTier'
]
