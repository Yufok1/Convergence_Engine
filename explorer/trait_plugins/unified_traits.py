"""
Trait Hub Plugin: Unified Three-System Traits
Maps combined traits from Reality Simulator + Djinn Kernel + Explorer
"""

TRAIT_MAP = {
    # Unified Phase Transition Traits
    'transition_proximity': ('Transition Proximity', 'How close to chaos→precision transition (0.0-1.0)'),
    'phase': ('Phase', 'Current phase: chaos or precision'),
    'system_alignment': ('System Alignment', 'How aligned all three systems are (0.0-1.0)'),
    'transition_ready': ('Transition Ready', 'Whether any system is ready for transition'),
    
    # Unified Exploration Traits
    'total_exploration': ('Total Exploration', 'Normalized exploration across all systems (0.0-1.0)'),
    'reality_sim_explorations': ('Reality Sim Explorations', 'Organisms explored in Reality Simulator'),
    'explorer_explorations': ('Explorer Explorations', 'VP calculations in Explorer'),
    'djinn_kernel_explorations': ('Djinn Kernel Explorations', 'Trait explorations in Djinn Kernel'),
    'exploration_to_precision_ratio': ('Exploration Ratio', 'Conversion factor: 500:50 = 10:1'),
    
    # Unified Coordination Traits
    'coordination_health': ('Coordination Health', 'Health of three-system coordination (0.0-1.0)'),
    'sync_status': ('Sync Status', 'Synchronization status: synchronized, partial, or unsynchronized'),
    'all_systems_active': ('All Systems Active', 'Whether all three systems are active'),
    'active_systems': ('Active Systems', 'Number of active systems (0-3)'),
    
    # Unified VP Traits
    'unified_vp': ('Unified VP', 'Combined violation pressure across all systems'),
    'reality_sim_vp': ('Reality Sim VP', 'VP from network metrics'),
    'explorer_vp': ('Explorer VP', 'VP from module operations'),
    'djinn_kernel_vp': ('Djinn Kernel VP', 'VP from trait divergence'),
    
    # Unified Stability Traits
    'unified_stability': ('Unified Stability', 'Combined stability across all systems'),
    'network_stability': ('Network Stability', 'Stability from Reality Simulator'),
    'module_stability': ('Module Stability', 'Stability from Explorer'),
    'trait_stability': ('Trait Stability', 'Stability from Djinn Kernel')
}

