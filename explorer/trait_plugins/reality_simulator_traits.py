"""
Trait Hub Plugin: Reality Simulator Integration
Maps Reality Simulator network metrics to Explorer trait format
"""

TRAIT_MAP = {
    # Network Structure Traits
    'organism_count': ('Organism Count', 'Number of organisms in the symbiotic network'),
    'connection_count': ('Connection Count', 'Total connections between organisms'),
    'clustering_coefficient': ('Clustering', 'Network connectivity density (high = tightly connected)'),
    'modularity': ('Modularity', 'Network community structure (low < 0.3 = unified, high = many communities)'),
    'average_path_length': ('Path Length', 'Average steps between any two organisms (low < 3.0 = efficient)'),
    'connectivity': ('Connectivity', 'Overall network connectivity metric'),
    'stability_index': ('Stability', 'Network stability index'),
    
    # Phase Transition Traits
    'collapse_proximity': ('Collapse Proximity', 'How close network is to collapse (0.0-1.0)'),
    'is_collapsed': ('Collapsed', 'Whether network has collapsed (distributed → consolidated)'),
    
    # Network Health Traits
    'network_density': ('Network Density', 'Actual connections / possible connections'),
    'average_degree': ('Average Degree', 'Average connections per organism'),
    'generation': ('Generation', 'Current evolutionary generation')
}

