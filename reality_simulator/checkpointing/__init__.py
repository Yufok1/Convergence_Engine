"""
Checkpointing submodule - Organism state preservation

Contains:
- OrganismCapsule: Complete organism state capture for resurrection/analysis
- CapsuleManager: Management of capsule lifecycle
"""

from .organism_capsule import (
    OrganismCapsule,
    CapsuleManager,
    CapsuleVersion
)

__all__ = [
    'OrganismCapsule',
    'CapsuleManager',
    'CapsuleVersion'
]
