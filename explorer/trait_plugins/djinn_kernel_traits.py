"""
Trait Hub Plugin: Djinn Kernel Integration
Maps Djinn Kernel trait metrics to Explorer trait format
"""

TRAIT_MAP = {
    # Violation Pressure Traits
    'violation_pressure': ('VP', 'Trait divergence from stability centers (VP < 0.25 = VP0, lawful)'),
    'total_vp': ('Total VP', 'Total violation pressure across all traits'),
    'vp_classification': ('VP Class', 'VP classification: VP0-VP4'),
    
    # Trait Convergence Traits
    'trait_convergence': ('Convergence', 'Trait stabilization progress (0.0-1.0)'),
    'convergence_success': ('Convergence Success', 'Success rate of trait convergence'),
    'trait_divergence': ('Divergence', 'Trait divergence from stability (high = unstable)'),
    
    # Stability Envelope Traits
    'stability_envelope_deviation': ('Envelope Dev', 'Deviation from stability envelope center'),
    'completion_pressure': ('Completion', 'Identity completion pressure'),
    'convergence_stability': ('Convergence Stability', 'Stability of trait convergence process'),
    'reflection_index': ('Reflection Index', 'System self-reflection capability'),
    
    # Identity Traits
    'uuid_anchored': ('UUID Anchored', 'Whether identity is anchored via UUID'),
    'identity_completion': ('Identity Completion', 'Identity completion status'),
    
    # System Health Traits
    'system_health': ('System Health', 'Overall Djinn Kernel system health (0.0-1.0)'),
    'temporal_isolation_active': ('Temporal Isolation', 'Whether temporal isolation is active'),
    'forbidden_zone_active': ('Forbidden Zone', 'Whether forbidden zone operations are active')
}

