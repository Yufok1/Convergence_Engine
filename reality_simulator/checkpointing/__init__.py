"""
Checkpointing submodule - Organism state preservation

Contains:
- OrganismCapsule: Complete organism state capture for resurrection/analysis
- CapsuleManager: Management of capsule lifecycle
"""

from .organism_capsule import (
    OrganismCapsule,
    OrganismCapsuleManager,
    CapsuleVersion
)

# Alias for backward compatibility
CapsuleManager = OrganismCapsuleManager

__all__ = [
    'OrganismCapsule',
    'OrganismCapsuleManager',
    'CapsuleManager',
    'CapsuleVersion'
]
