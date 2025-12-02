"""
🌐 SYMBIOTIC NETWORK (Layer 3)

Where organisms form interconnected ecosystems through cooperation and competition.
This is where the tiny AI makes its first strategic decisions.

Features:
- Network graph of organism connections
- Resource flow algorithms (max-flow/min-cost)
- Cooperation vs competition dynamics
- Ecosystem emergence and stability
- AI-guided connection decisions (binary: connect or not)
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Set, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import networkx as nx
from collections import defaultdict
import time
import logging

# Import context memory system
try:
    from reality_simulator.memory.context_memory import ContextMemory
except ImportError:
    # Fallback for relative import issues
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    memory_dir = os.path.join(current_dir, 'memory')
    if memory_dir not in sys.path:
        sys.path.insert(0, memory_dir)
    from context_memory import ContextMemory

# Import ML utilities (optional - graceful degradation if unavailable)
try:
    from reality_simulator.ml_utils import MLAnalyzer, get_ml_analyzer, is_sklearn_available
    ML_UTILS_AVAILABLE = True
except ImportError:
    ML_UTILS_AVAILABLE = False
    MLAnalyzer = None
    get_ml_analyzer = None
    is_sklearn_available = lambda: False

# Import Health Monitor (Quick Win #5)
try:
    from reality_simulator.health_monitor import HealthMonitor, get_health_monitor
    HEALTH_MONITOR_AVAILABLE = True
except ImportError:
    try:
        from health_monitor import HealthMonitor, get_health_monitor
        HEALTH_MONITOR_AVAILABLE = True
    except ImportError:
        HEALTH_MONITOR_AVAILABLE = False
        HealthMonitor = None
        get_health_monitor = None

try:
    from evolution_engine import Organism
except ImportError:
    # Forward declaration for testing
    class Organism:
        pass


class ConnectionType(Enum):
    """Types of symbiotic connections"""
    COOPERATIVE = "cooperative"      # Mutual benefit
    COMPETITIVE = "competitive"      # Resource competition
    PREDATOR_PREY = "predator_prey"  # One benefits, one suffers
    COMMENSAL = "commensal"          # One benefits, no effect on other
    MUTUALISTIC = "mutualistic"      # Strong mutual benefit


@dataclass
class SymbioticConnection:
    """
    A connection between two organisms

    Represents the relationship and resource flow between organisms
    """
    organism_a_id: str
    organism_b_id: str
    connection_type: ConnectionType
    strength: float = 1.0  # Connection strength (0.0 to 1.0)
    resource_flow: float = 0.0  # Net resource transfer (positive = A → B)
    stability: float = 0.5  # Connection stability
    age: int = 0

    def update_stability(self, interaction_outcome: float):
        """Update connection stability based on interaction outcomes"""
        # Stability increases with positive outcomes, decreases with negative
        stability_change = interaction_outcome * 0.1
        self.stability = np.clip(self.stability + stability_change, 0.0, 1.0)
        self.age += 1

    def get_effective_strength(self) -> float:
        """Get effective connection strength (strength × stability)"""
        return self.strength * self.stability


@dataclass
class EcosystemMetrics:
    """
    Metrics describing ecosystem health and dynamics
    """
    connectivity: float = 0.0          # Average connections per organism
    clustering_coefficient: float = 0.0  # Local clustering
    average_path_length: float = 0.0   # Network efficiency
    modularity: float = 0.0           # Community structure strength
    resource_flow_balance: float = 0.0  # Net resource circulation
    species_diversity: float = 0.0    # Fitness diversity
    stability_index: float = 0.0      # Ecosystem stability measure

    def update_from_network(self, network_graph: nx.Graph,
                          organisms: Dict[str, Organism]):
        """Update metrics from current network state"""
        if len(network_graph) == 0:
            return

        # Basic network metrics
        self.connectivity = np.mean([d for n, d in network_graph.degree()])
        self.clustering_coefficient = nx.average_clustering(network_graph)

        if nx.is_connected(network_graph):
            self.average_path_length = nx.average_shortest_path_length(network_graph)
        else:
            # Use largest component for disconnected graphs
            largest_component = max(nx.connected_components(network_graph), key=len)
            subgraph = network_graph.subgraph(largest_component)
            if len(subgraph) > 1:
                self.average_path_length = nx.average_shortest_path_length(subgraph)
            else:
                self.average_path_length = 0.0

        # Community detection and proper modularity calculation
        try:
            communities = list(nx.community.greedy_modularity_communities(network_graph))
            # Use NetworkX's proper modularity calculation instead of len(communities)/len(graph)
            # Modularity measures quality of community structure (0 = random, 1 = perfect separation)
            if len(communities) > 0 and len(network_graph.edges()) > 0:
                self.modularity = nx.algorithms.community.modularity(network_graph, communities)
            else:
                # No edges or no communities - default to 0
                self.modularity = 0.0
        except (ValueError, ZeroDivisionError, AttributeError, nx.NetworkXError) as e:
            # NetworkX may raise ValueError for empty graphs or graphs without communities
            # ZeroDivisionError if network_graph is empty
            # AttributeError if networkx.community is not available
            # NetworkXError for other graph-related issues
            self.modularity = 0.0
            # Log the error for debugging (if logging is available)
            if hasattr(self, '_logger') and self._logger:
                self._logger.warning(f"Failed to calculate modularity: {e}")

        # Resource flow balance (sum of all connection flows)
        total_flow = 0.0
        for edge_data in network_graph.edges(data=True):
            if 'resource_flow' in edge_data[2]:
                total_flow += abs(edge_data[2]['resource_flow'])
        self.resource_flow_balance = total_flow / max(1, len(network_graph.edges()))

        # Species diversity (fitness variance)
        if organisms:
            fitnesses = [org.fitness for org in organisms.values()]
            self.species_diversity = np.std(fitnesses) / (np.mean(fitnesses) + 1e-10)

        # Stability index (combination of metrics)
        stability_factors = [
            self.connectivity / 10.0,  # Normalize
            1.0 - self.average_path_length / 10.0,  # Shorter paths = more stable
            self.modularity,
            1.0 - abs(self.resource_flow_balance - 0.5) * 2,  # Balance around 0.5
            self.species_diversity
        ]
        self.stability_index = np.mean(stability_factors)


class ResourceFlowEngine:
    """
    Manages resource distribution through the symbiotic network

    Uses max-flow algorithms to optimize resource allocation
    """

    def __init__(self, total_resources: float = 100.0):
        self.total_resources = total_resources
        self.resource_distribution: Dict[str, float] = {}

    def calculate_flows(self, network_graph: nx.Graph,
                       organisms: Dict[str, Organism]) -> Dict[Tuple[str, str], float]:
        """
        Calculate resource flows between connected organisms

        Uses simplified max-flow with capacity constraints
        """
        flows = {}

        for edge in network_graph.edges():
            org_a_id, org_b_id = edge
            org_a = organisms.get(org_a_id)
            org_b = organisms.get(org_b_id)

            if org_a and org_b:
                # Calculate flow based on fitness difference and connection strength
                fitness_diff = org_a.fitness - org_b.fitness
                edge_data = network_graph.get_edge_data(org_a_id, org_b_id, {})
                strength = edge_data.get('strength', 1.0)

                # Flow from higher fitness to lower fitness (redistribution)
                base_flow = fitness_diff * strength * 0.1
                # Add some random variation
                flow = base_flow + np.random.normal(0, 0.05)

                flows[(org_a_id, org_b_id)] = flow

        return flows

    def distribute_resources(self, network_graph: nx.Graph,
                           organisms: Dict[str, Organism],
                           flows: Dict[Tuple[str, str], float]) -> Dict[str, float]:
        """
        Distribute resources based on calculated flows

        Ensures minimum survival while rewarding success
        """
        # Start with equal distribution
        base_allocation = self.total_resources / max(1, len(organisms))
        distribution = {org_id: base_allocation for org_id in organisms.keys()}

        # Apply flows
        for (sender_id, receiver_id), flow in flows.items():
            if flow > 0:  # Positive flow = sender loses, receiver gains
                transfer_amount = min(distribution[sender_id] * 0.1, flow)
                distribution[sender_id] -= transfer_amount
                distribution[receiver_id] += transfer_amount
            elif flow < 0:  # Negative flow = receiver loses, sender gains
                transfer_amount = min(distribution[receiver_id] * 0.1, abs(flow))
                distribution[receiver_id] -= transfer_amount
                distribution[sender_id] += transfer_amount

        # Ensure minimum survival (no organism gets zero)
        min_survival = self.total_resources * 0.01  # 1% minimum
        for org_id in distribution:
            if distribution[org_id] < min_survival:
                distribution[org_id] = min_survival

        # Renormalize to total resources
        total_distributed = sum(distribution.values())
        if total_distributed > 0:
            normalization_factor = self.total_resources / total_distributed
            distribution = {k: v * normalization_factor for k, v in distribution.items()}

        return distribution

    def update_organism_fitness(self, organisms: Dict[str, Organism],
                               resource_distribution: Dict[str, float]):
        """Update organism fitness based on resource allocation"""
        for org_id, resources in resource_distribution.items():
            if org_id in organisms:
                organism = organisms[org_id]
                
                # ✅ FIX: Base resource bonus on organism's current fitness
                # This prevents convergence - organisms with different base fitness
                # get proportionally different bonuses
                
                # Resource bonus (diminishing returns)
                base_bonus = np.log(1 + resources) * 0.1
                
                # ✅ FIX: Fitness-dependent scaling (prevents convergence)
                # Lower fitness organisms get slightly larger relative bonus (catch-up mechanism)
                # Higher fitness organisms get slightly smaller relative bonus (prevents runaway)
                fitness_factor = 1.0 - (organism.fitness * 0.2)  # 1.0 at fitness=0, 0.8 at fitness=1.0
                scaled_bonus = base_bonus * fitness_factor
                
                # ✅ FIX: Genetic uniqueness modifier (ensures differentiation)
                if hasattr(organism, 'genotype') and hasattr(organism.genotype, 'get_hash'):
                    genotype_hash = organism.genotype.get_hash()
                    try:
                        hash_int = int(genotype_hash[:4], 16) if len(genotype_hash) >= 4 else hash(genotype_hash)
                    except (ValueError, TypeError):
                        hash_int = hash(genotype_hash) % 10000
                    uniqueness_modifier = 0.95 + ((hash_int % 100) / 1000.0)  # 0.95-1.05 range
                    scaled_bonus *= uniqueness_modifier
                
                organisms[org_id].fitness = min(1.0, organisms[org_id].fitness + scaled_bonus)


class CooperationCompetitionEngine:
    """
    Handles game theory dynamics between organisms

    Models Prisoner's Dilemma and other social dilemmas
    """

    def __init__(self):
        self.payoff_matrix = {
            ('cooperate', 'cooperate'): (3, 3),  # Mutual cooperation
            ('cooperate', 'defect'): (0, 5),    # Sucker vs temptation
            ('defect', 'cooperate'): (5, 0),    # Temptation vs sucker
            ('defect', 'defect'): (1, 1),       # Mutual defection
        }

    def evaluate_interaction(self, org_a: Organism, org_b: Organism,
                            connection: SymbioticConnection) -> Tuple[float, float]:
        """
        Evaluate interaction outcome using game theory

        Returns: (fitness_change_a, fitness_change_b)
        """
        # Determine strategies based on organism traits
        strategy_a = self._determine_strategy(org_a)
        strategy_b = self._determine_strategy(org_b)

        # Get payoffs
        payoff_a, payoff_b = self.payoff_matrix[(strategy_a, strategy_b)]

        # Scale by connection strength
        strength = connection.get_effective_strength()
        payoff_a *= strength
        payoff_b *= strength

        # Convert to fitness changes (normalized)
        fitness_change_a = payoff_a / 10.0  # Scale to reasonable range
        fitness_change_b = payoff_b / 10.0

        # Update connection stability
        avg_payoff = (payoff_a + payoff_b) / 2.0
        connection.update_stability(avg_payoff / 5.0)  # Normalize to 0-1

        return fitness_change_a, fitness_change_b

    def _determine_strategy(self, organism: Organism) -> str:
        """Determine cooperation/defection strategy from organism traits"""
        # Use trait_0 as cooperation tendency (if available)
        if hasattr(organism.phenotype, 'traits') and 'trait_0' in organism.phenotype.traits:
            cooperation_tendency = organism.phenotype.traits['trait_0']
        else:
            # Fallback to fitness
            cooperation_tendency = organism.fitness

        # Threshold for cooperation
        return 'cooperate' if cooperation_tendency > 0.5 else 'defect'

    def find_nash_equilibrium(self, organisms: List[Organism]) -> Optional[Tuple[str, str]]:
        """Find Nash equilibrium in the population strategy space"""
        if len(organisms) < 2:
            return None

        # Simplified: check if current strategies are stable
        strategies = [self._determine_strategy(org) for org in organisms]

        # If everyone cooperates or everyone defects, might be equilibrium
        if all(s == 'cooperate' for s in strategies):
            return ('cooperate', 'cooperate')
        elif all(s == 'defect' for s in strategies):
            return ('defect', 'defect')

        return None


class EcosystemEmergenceEngine:
    """
    Detects and manages emergent ecosystem properties

    Identifies communities, trophic levels, and stability patterns
    """

    def __init__(self):
        self.community_history = []
        self.stability_history = []

    def detect_communities(self, network_graph: nx.Graph) -> List[Set[str]]:
        """
        Detect communities in the network using modularity optimization
        """
        try:
            communities = list(nx.community.greedy_modularity_communities(network_graph))
            return communities
        except Exception as e:
            # Log failure and fallback: connected components
            import logging
            logging.getLogger(__name__).warning(f"Community detection failed: {e}, using connected components fallback")
            return list(nx.connected_components(network_graph))

    def identify_trophic_levels(self, network_graph: nx.Graph,
                              organisms: Dict[str, Organism]) -> Dict[str, int]:
        """
        Identify trophic levels (food chain positions)

        Uses fitness as proxy for trophic position
        """
        levels = {}

        # Sort organisms by fitness (higher fitness = higher trophic level)
        sorted_orgs = sorted(organisms.items(), key=lambda x: x[1].fitness, reverse=True)

        # Assign levels based on fitness quantiles
        n_levels = 3  # Producer, Consumer, Predator
        for i, (org_id, org) in enumerate(sorted_orgs):
            level = min(n_levels - 1, i * n_levels // len(sorted_orgs))
            levels[org_id] = level

        return levels

    def analyze_ecosystem_stability(self, network_graph: nx.Graph,
                                  metrics: EcosystemMetrics) -> Dict[str, Any]:
        """
        Comprehensive ecosystem stability analysis
        """
        stability_factors = {
            'network_resilience': self._calculate_network_resilience(network_graph),
            'diversity_stability': metrics.species_diversity,
            'flow_balance': 1.0 - abs(metrics.resource_flow_balance - 0.5) * 2,
            'connectivity_robustness': metrics.connectivity / 10.0,  # Normalize
            'community_cohesion': metrics.modularity
        }

        overall_stability = np.mean(list(stability_factors.values()))

        self.stability_history.append(overall_stability)

        return {
            'overall_stability': overall_stability,
            'stability_factors': stability_factors,
            'stability_trend': self._calculate_stability_trend(),
            'emergent_properties': self._detect_emergent_properties(network_graph, metrics)
        }

    def _calculate_network_resilience(self, network_graph: nx.Graph) -> float:
        """Calculate network resilience to node removal"""
        if len(network_graph) < 2:
            return 0.0

        # Remove 10% of nodes and measure connectivity loss
        original_components = nx.number_connected_components(network_graph)
        nodes_to_remove = int(len(network_graph) * 0.1)

        if nodes_to_remove > 0:
            nodes_list = list(network_graph.nodes())
            np.random.shuffle(nodes_list)
            nodes_to_remove_list = nodes_list[:nodes_to_remove]

            reduced_graph = network_graph.copy()
            reduced_graph.remove_nodes_from(nodes_to_remove_list)

            remaining_components = nx.number_connected_components(reduced_graph)
            connectivity_loss = (original_components - remaining_components) / original_components

            return 1.0 - connectivity_loss  # Higher = more resilient
        else:
            return 1.0

    def _calculate_stability_trend(self) -> float:
        """Calculate trend in stability over time"""
        if len(self.stability_history) < 2:
            return 0.0

        recent = self.stability_history[-5:]  # Last 5 measurements
        if len(recent) < 2:
            return 0.0

        # Linear trend
        x = np.arange(len(recent))
        slope = np.polyfit(x, recent, 1)[0]
        return slope  # Positive = improving stability

    def _detect_emergent_properties(self, network_graph: nx.Graph,
                                  metrics: EcosystemMetrics) -> List[str]:
        """Detect emergent ecosystem properties"""
        properties = []

        # Small-world property
        if metrics.average_path_length > 0 and metrics.clustering_coefficient > 0.1:
            properties.append("small_world_network")

        # Scale-free network
        degrees = [d for n, d in network_graph.degree()]
        if len(degrees) > 10:
            degree_variance = np.var(degrees)
            if degree_variance > np.mean(degrees):
                properties.append("scale_free_topology")

        # High modularity
        if metrics.modularity > 0.5:
            properties.append("strong_community_structure")

        # High stability
        if metrics.stability_index > 0.7:
            properties.append("stable_ecosystem")

        return properties


    def export_linguistic_data(self) -> Dict[str, Any]:
        """Export linguistic subgraph data for external analysis/visualization"""
        return {
            'subgraph_stats': self.language_subgraph.get_subgraph_stats(),
            'linguistic_edges': [
                {
                    'word_a': edge.word_a,
                    'word_b': edge.word_b,
                    'connector': edge.connector,
                    'strength': edge.strength,
                    'org_a': edge.organism_a_id,
                    'org_b': edge.organism_b_id,
                    'generation': edge.creation_generation
                }
                for edge in self.language_subgraph.linguistic_edges.values()
            ],
            'persistent_edges': list(self.language_subgraph.get_persistent_edges()),
            'semantic_mappings': dict(self.language_subgraph.linguistic_edges.keys())
        }


class LinguisticSubgraph:
    """
    Protected linguistic subgraph that preserves language-embedded connections.

    Stores linguistic edges separately with retention policies, synchronizing
    with the main graph under resource constraints.
    """

    def __init__(self):
        # Linguistic connections: (org_a, org_b) -> LinguisticEdge
        self.linguistic_edges: Dict[Tuple[str, str], LinguisticEdge] = {}

        # Retention policies
        self.retention_policies = {
            'min_lifetime_generations': 10,  # Edges must persist this long minimum
            'priority_boost': 1.5,          # Linguistic edges get priority in pruning
            'sync_interval': 5,             # Sync with main graph every N generations
            'max_subgraph_size': 1000       # Limit subgraph size to prevent bloat
        }

        self.generation = 0
        self.last_sync_generation = 0

    def add_linguistic_edge(self, org_a_id: str, org_b_id: str,
                           word_a: str, word_b: str, connector: str,
                           strength: float = 1.0):
        """Add a linguistic edge to the protected subgraph"""
        edge_key = (org_a_id, org_b_id)

        linguistic_edge = LinguisticEdge(
            organism_a_id=org_a_id,
            organism_b_id=org_b_id,
            word_a=word_a,
            word_b=word_b,
            connector=connector,
            strength=strength,
            creation_generation=self.generation
        )

        self.linguistic_edges[edge_key] = linguistic_edge

        # Prevent subgraph from growing too large
        if len(self.linguistic_edges) > self.retention_policies['max_subgraph_size']:
            self._prune_oldest_edges()

        print(f"[LINGUISTIC SUBGRAPH] Added edge: {word_a} {connector} {word_b} "
              f"({org_a_id} <-> {org_b_id})")

    def synchronize_to_main_graph(self, main_network):
        """
        Synchronize linguistic edges to the main network graph.

        Only adds edges that aren't already present, respecting main graph constraints.
        """
        synced_count = 0
        rejected_count = 0

        for edge_key, linguistic_edge in self.linguistic_edges.items():
            org_a, org_b = edge_key

            # Check if this edge already exists in main graph
            if edge_key not in main_network.connections:
                # Try to add to main graph
                if main_network.add_connection(org_a, org_b,
                                             connection_type=ConnectionType.COOPERATIVE,
                                             strength=linguistic_edge.strength,
                                             is_language_connection=True):
                    synced_count += 1
                else:
                    rejected_count += 1

        if synced_count > 0 or rejected_count > 0:
            print(f"[LINGUISTIC SUBGRAPH] Sync complete: {synced_count} added, {rejected_count} rejected")

        self.last_sync_generation = self.generation

    def get_persistent_edges(self) -> List[Tuple[str, str]]:
        """
        Get linguistic edges that have exceeded minimum lifetime.
        These are protected from pruning.
        """
        persistent_edges = []
        min_lifetime = self.retention_policies['min_lifetime_generations']

        for edge_key, edge in self.linguistic_edges.items():
            if (self.generation - edge.creation_generation) >= min_lifetime:
                persistent_edges.append(edge_key)

        return persistent_edges

    def update_generation(self, new_generation: int):
        """Update generation counter and trigger periodic sync"""
        self.generation = new_generation

        # Periodic sync to main graph
        if (new_generation - self.last_sync_generation) >= self.retention_policies['sync_interval']:
            # Note: sync will be called externally with main_network reference
            pass

    def _prune_oldest_edges(self):
        """Remove oldest edges when subgraph exceeds size limit"""
        if not self.linguistic_edges:
            return

        # Sort by creation generation (oldest first)
        sorted_edges = sorted(self.linguistic_edges.items(),
                            key=lambda x: x[1].creation_generation)

        # Remove oldest 10% or at least 1 edge
        num_to_remove = max(1, len(sorted_edges) // 10)

        for i in range(num_to_remove):
            edge_key, _ = sorted_edges[i]
            del self.linguistic_edges[edge_key]

        print(f"[LINGUISTIC SUBGRAPH] Pruned {num_to_remove} oldest edges to maintain size limit")

    def get_subgraph_stats(self) -> Dict[str, Any]:
        """Get statistics about the linguistic subgraph"""
        if not self.linguistic_edges:
            return {'total_edges': 0, 'avg_strength': 0.0, 'oldest_edge': 0, 'newest_edge': 0}

        strengths = [edge.strength for edge in self.linguistic_edges.values()]
        creation_gens = [edge.creation_generation for edge in self.linguistic_edges.values()]

        return {
            'total_edges': len(self.linguistic_edges),
            'avg_strength': sum(strengths) / len(strengths),
            'oldest_edge': min(creation_gens),
            'newest_edge': max(creation_gens),
            'current_generation': self.generation
        }

    @property
    def edges(self) -> Dict[Tuple[str, str], Dict[str, Any]]:
        """
        Property accessor for edges with metadata (for token embedding exchange).
        
        Returns dict mapping (org_a, org_b) -> edge metadata dict
        """
        result = {}
        for edge_key, edge in self.linguistic_edges.items():
            result[edge_key] = {
                'strength': edge.strength,
                'min_lifetime_generations': self.generation - edge.creation_generation,
                'word_a': edge.word_a,
                'word_b': edge.word_b,
                'connector': edge.connector
            }
        return result

    def remove_organism_edges(self, organism_id: str) -> int:
        """
        Remove all edges associated with a specific organism.
        
        Called during organism death to clean up linguistic subgraph.
        
        Args:
            organism_id: ID of the organism being removed
            
        Returns:
            Number of edges removed
        """
        edges_to_remove = [
            edge_key for edge_key in self.linguistic_edges.keys()
            if organism_id in edge_key
        ]
        
        for edge_key in edges_to_remove:
            del self.linguistic_edges[edge_key]
        
        if edges_to_remove:
            print(f"[LINGUISTIC SUBGRAPH] Removed {len(edges_to_remove)} edges for organism {organism_id}")
        
        return len(edges_to_remove)


@dataclass
class LinguisticEdge:
    """Represents a linguistic connection in the protected subgraph"""
    organism_a_id: str
    organism_b_id: str
    word_a: str
    word_b: str
    connector: str
    strength: float
    creation_generation: int


class SymbioticNetwork:
    """
    Main symbiotic network engine

    Coordinates all aspects of organism interactions and ecosystem dynamics
    """

    def __init__(self, max_connections_per_organism: int = 5,
                 resource_pool_size: float = 100.0,
                 new_edge_rate: float = 1.0,
                 context_memory: Optional[ContextMemory] = None,
                 config: Optional[Dict[str, Any]] = None):
        self.network_graph = nx.Graph()
        self.connections: Dict[Tuple[str, str], SymbioticConnection] = {}
        self.organisms: Dict[str, Organism] = {}
        self.language_connections: Set[Tuple[str, str]] = set()  # Track language-related connections

        # NEW: Protected linguistic subgraph with retention policies
        self.language_subgraph = LinguisticSubgraph()
        
        # Context memory for language anchoring and stability metrics
        # Creates a new instance if none provided (lazy initialization pattern)
        self.context_memory = context_memory if context_memory is not None else ContextMemory()
        
        # Initialize event_emitter attribute (will be wired later by unified_entry.py or reality_simulator/main.py)
        # This ensures word_assignment events can be emitted when words are linked
        if not hasattr(self.context_memory, 'event_emitter'):
            self.context_memory.event_emitter = None
        
        # Store config for language teacher
        self.config = config or {}
        
        # Language Teacher (Phase 1: Behavior-based word mapping)
        self.language_teacher = None
        try:
            from reality_simulator.language.language_teacher import create_language_teacher
            print(f"[SYMBIOTIC_NETWORK] Creating language teacher...")
            self.language_teacher = create_language_teacher(self.config)
            
            if self.language_teacher is None:
                print(f"[SYMBIOTIC_NETWORK] WARNING: create_language_teacher returned None")
            elif not self.language_teacher.enabled:
                print(f"[SYMBIOTIC_NETWORK] Language Teacher created but NOT enabled")
            else:
                print(f"[SYMBIOTIC_NETWORK] Language Teacher enabled (Phase 1: Behavior-based mapping)")
                # Attach language_teacher to context_memory so organisms can access knowledge_web
                # during token generation (fixes semantic guidance not being applied)
                self.context_memory.language_teacher = self.language_teacher
                print(f"[SYMBIOTIC_NETWORK] ✅ language_teacher attached to context_memory")
                
                if hasattr(self.language_teacher, 'knowledge_web') and self.language_teacher.knowledge_web is not None:
                    self.context_memory.knowledge_web = self.language_teacher.knowledge_web
                    concept_count = len(self.language_teacher.knowledge_web.concepts) if hasattr(self.language_teacher.knowledge_web, 'concepts') else 'unknown'
                    print(f"[SYMBIOTIC_NETWORK] ✅ Knowledge web attached to context_memory ({concept_count} concepts)")
                else:
                    print(f"[SYMBIOTIC_NETWORK] ⚠️ language_teacher has no knowledge_web or it is None")
                    if hasattr(self.language_teacher, '__dict__'):
                        print(f"[SYMBIOTIC_NETWORK]    language_teacher attrs: {list(self.language_teacher.__dict__.keys())}")
        except ImportError as e:
            print(f"[SYMBIOTIC_NETWORK] ImportError for language_teacher: {e}")
        except Exception as e:
            print(f"[SYMBIOTIC_NETWORK] Warning: Could not initialize Language Teacher: {e}")
            import traceback
            traceback.print_exc()

        # Component engines
        self.resource_engine = ResourceFlowEngine(resource_pool_size)
        self.cooperation_engine = CooperationCompetitionEngine()
        self.emergence_engine = EcosystemEmergenceEngine()

        # Network constraints
        self.max_connections_per_organism = max_connections_per_organism
        self.new_edge_rate = new_edge_rate  # Multiplier for connection attempts (0.0 to 2.0)
        # Bias toward triangle closure vs exploration (0.0=random/explore, 1.0=prefer clustering)
        self.clustering_bias: float = 0.8  # Increased from 0.5 to 0.8

        # Metrics tracking
        self.metrics = EcosystemMetrics()
        self.generation = 0
        
        # ML Analyzer for population analysis (optional - config-driven)
        self.ml_analyzer: Optional[MLAnalyzer] = None
        self.ml_config: Dict[str, Any] = {}
        self._last_ml_analysis: Dict[str, Any] = {}
        self._previous_cluster_count: int = 0
        self._previous_anomaly_count: int = 0
        
        # Event emitter callback for causation graph integration
        self.ml_event_emitter: Optional[Callable] = None
        
        # Health Monitor for unified ecosystem health scoring (Quick Win #5)
        self.health_monitor: Optional['HealthMonitor'] = None
        self.health_config: Dict[str, Any] = {}
        self._last_health_snapshot: Optional[Any] = None
        
        # External VP data source (from Explorer/Djinn Kernel via unified_entry.py)
        self._external_vp_data: Optional[Dict[str, Any]] = None

    def configure_ml_analyzer(self, config: Dict[str, Any]):
        """
        Configure and enable the ML analyzer for population analysis.
        
        Config structure:
        {
            "enabled": true/false,
            "clustering": {"enabled": true, "algorithm": "hdbscan", ...},
            "anomaly_detection": {"enabled": true, ...},
            "dimensionality_reduction": {"enabled": true, ...}
        }
        """
        self.ml_config = config
        if ML_UTILS_AVAILABLE and config.get('enabled', False):
            self.ml_analyzer = get_ml_analyzer(config)
        elif self.ml_analyzer is not None and not config.get('enabled', False):
            self.ml_analyzer = None
    
    def configure_health_monitor(self, config: Dict[str, Any], event_emitter: Optional[Callable] = None):
        """
        Configure and enable the Health Monitor for unified ecosystem health scoring.
        
        Config structure (Quick Win #5):
        {
            "enabled": true/false,
            "weight_coherence": 0.30,
            "weight_diversity": 0.20,
            "weight_adaptability": 0.20,
            "weight_lawfulness": 0.20,
            "weight_sustainability": 0.10,
            "critical_threshold": 0.3,
            "warning_threshold": 0.5,
            "healthy_threshold": 0.7
        }
        """
        self.health_config = config
        if HEALTH_MONITOR_AVAILABLE and config.get('enabled', True):
            self.health_monitor = HealthMonitor(
                enabled=config.get('enabled', True),
                history_size=config.get('history_size', 100),
                event_emitter=event_emitter or self.ml_event_emitter,
                config=config
            )
        elif self.health_monitor is not None and not config.get('enabled', True):
            self.health_monitor = None
    
    def inject_vp_data(self, vp_total: Optional[float] = None, vp_components: Optional[Dict[str, float]] = None):
        """
        Inject VP data from external source (Explorer/Djinn Kernel).
        
        This allows the unified system to pass VP components from Explorer's sentinel
        to the network for Quick Win #1 (VP-Aware Perception).
        
        Args:
            vp_total: Total violation pressure value
            vp_components: Dict with component breakdown (trait_divergence, network_coherence, etc.)
        """
        self._external_vp_data = {
            'vp_total': vp_total,
            'vp_components': vp_components or {}
        }
    
    def compute_ecosystem_health(self, 
                                  neural_stats: Optional[Dict[str, float]] = None,
                                  vp_components: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Compute unified ecosystem health score.
        
        Aggregates data from network metrics, ML clustering, neural training,
        VP components, and resource/population data into a single health score.
        
        Returns dict with health_score and component breakdown.
        """
        if not HEALTH_MONITOR_AVAILABLE or self.health_monitor is None:
            return {'enabled': False, 'health_score': 0.5, 'reason': 'Health monitor not available'}
        
        # Gather network metrics
        network_metrics = {
            'connectivity': self.metrics.connectivity,
            'clustering_coefficient': self.metrics.clustering_coefficient,
            'modularity': self.metrics.modularity,
            'species_diversity': self.metrics.species_diversity,
        }
        
        # Gather resource data
        resource_data = {
            'resource_pool': getattr(self.resource_engine, 'total_resources', 200.0),
            'initial_resources': 200.0,  # Default initial
            'population': len(self.organisms),
            'target_population': 100,  # Config-driven target
        }
        
        # Get clustering result if available
        clustering_result = None
        if self._last_ml_analysis and self._last_ml_analysis.get('enabled'):
            clustering_result = self._last_ml_analysis.get('clustering')
        
        # Compute health
        snapshot = self.health_monitor.compute_health(
            network_metrics=network_metrics,
            clustering_result=clustering_result,
            neural_stats=neural_stats,
            vp_components=vp_components,
            resource_data=resource_data
        )
        
        self._last_health_snapshot = snapshot
        
        return snapshot.to_dict()
    
    def get_current_health(self) -> float:
        """Get the current ecosystem health score (0.0-1.0)"""
        if self.health_monitor:
            return self.health_monitor.get_current_health()
        return 0.5  # Neutral default
    
    def run_ml_analysis(self, force: bool = False) -> Dict[str, Any]:
        """
        Run ML analysis on current organism population.
        
        Returns analysis results including clustering, anomalies, and dimensionality reduction.
        Emits causation events when significant changes are detected.
        """
        if not ML_UTILS_AVAILABLE or self.ml_analyzer is None:
            return {'enabled': False, 'reason': 'ML analyzer not available or disabled'}
        
        if not self.organisms:
            return {'enabled': True, 'reason': 'No organisms to analyze'}
        
        # Pass context_memory to enable language features in ML analysis
        self._last_ml_analysis = self.ml_analyzer.analyze(
            self.organisms, 
            force=force,
            context_memory=self.context_memory
        )
        
        # Emit causation events for significant ML changes
        if self.ml_event_emitter and self._last_ml_analysis.get('enabled'):
            self._emit_ml_events(self._last_ml_analysis)
        
        return self._last_ml_analysis
    
    def _emit_ml_events(self, analysis: Dict[str, Any]):
        """Emit causation events for significant ML analysis changes"""
        try:
            current_time = time.time()
            
            # Check for cluster count changes
            clustering = analysis.get('clustering', {})
            current_clusters = clustering.get('n_clusters', 0)
            
            # Import Event class for causation graph
            try:
                from causation_explorer import Event
            except ImportError:
                return  # Can't emit without Event class
            
            # Emit events on cluster count changes OR periodically when clusters exist
            if current_clusters > 0:
                cluster_diff = current_clusters - self._previous_cluster_count
                
                # Emit on change OR if this is first detection (previous was 0)
                if self._previous_cluster_count == 0 or abs(cluster_diff) >= 1:
                    event_type = 'phenotype_emergence' if cluster_diff >= 0 else 'cluster_collapse'
                    event = Event(
                        timestamp=current_time,
                        component='ml_analysis',
                        event_type=event_type,
                        data={
                            'previous_clusters': self._previous_cluster_count,
                            'current_clusters': current_clusters,
                            'cluster_change': cluster_diff,
                            'cluster_sizes': clustering.get('cluster_sizes', {}),
                            'algorithm': clustering.get('algorithm', 'unknown'),
                            'generation': self.generation
                        }
                    )
                    if self.ml_event_emitter:
                        self.ml_event_emitter(event)
                
                self._previous_cluster_count = current_clusters
            
            # Check for anomaly spikes
            anomalies = analysis.get('anomalies', {})
            current_anomalies = anomalies.get('anomaly_count', 0)
            if current_anomalies > self._previous_anomaly_count + 2:  # Spike of 3+ anomalies
                try:
                    from causation_explorer import Event
                except ImportError:
                    return
                
                event = Event(
                    timestamp=current_time,
                    component='ml_analysis',
                    event_type='anomaly_spike',
                    data={
                        'previous_anomalies': self._previous_anomaly_count,
                        'current_anomalies': current_anomalies,
                        'anomaly_ratio': anomalies.get('anomaly_ratio', 0.0),
                        'algorithm': anomalies.get('algorithm', 'unknown'),
                        'generation': self.generation
                    }
                )
                self.ml_event_emitter(event)
            
            self._previous_anomaly_count = current_anomalies
            
        except Exception:
            pass  # Don't let event emission break ML analysis
    
    def get_ml_status(self) -> Dict[str, Any]:
        """Get current ML analyzer status"""
        if not ML_UTILS_AVAILABLE:
            return {'available': False, 'reason': 'ml_utils module not available'}
        if self.ml_analyzer is None:
            return {'available': True, 'enabled': False, 'reason': 'ML analyzer not configured'}
        return self.ml_analyzer.get_status()

    def add_organism(self, organism: Organism):
        """Add an organism to the network"""
        org_id = organism.species_id
        self.organisms[org_id] = organism
        self.network_graph.add_node(org_id,
                                  fitness=organism.fitness,
                                  species=organism.species_id)

    def remove_organism(self, organism_id: str):
        """Remove an organism from the network"""
        if organism_id in self.organisms:
            del self.organisms[organism_id]
            self.network_graph.remove_node(organism_id)

            # Remove associated connections
            connections_to_remove = []
            for (a, b), connection in self.connections.items():
                if a == organism_id or b == organism_id:
                    connections_to_remove.append((a, b))

            for conn_key in connections_to_remove:
                del self.connections[conn_key]

    def propose_connection(self, org_a_id: str, org_b_id: str, allow_bypass_limits: bool = False) -> bool:
        """
        AI DECISION POINT: Should these organisms connect?

        This is where the tiny model makes its binary decision.
        For now, returns a simple heuristic. Will be replaced by AI.
        """
        if org_a_id not in self.organisms or org_b_id not in self.organisms:
            return False

        org_a = self.organisms[org_a_id]
        org_b = self.organisms[org_b_id]

        # Check connection limits (unless bypassing for language connections)
        if not allow_bypass_limits:
            current_connections_a = len([(a, b) for (a, b), _ in self.connections.items()
                                       if a == org_a_id or b == org_a_id])
            current_connections_b = len([(a, b) for (a, b), _ in self.connections.items()
                                       if a == org_b_id or b == org_b_id])

            if (current_connections_a >= self.max_connections_per_organism or
                current_connections_b >= self.max_connections_per_organism):
                return False

        # Simple heuristic: Connect if fitness difference is reasonable
        fitness_diff = abs(org_a.fitness - org_b.fitness)
        compatibility = 1.0 - fitness_diff  # Higher compatibility = smaller difference

        # AI DECISION: Binary yes/no based on compatibility
        should_connect = compatibility > 0.3  # Threshold for connection

        return should_connect

    def add_connection(self, org_a_id: str, org_b_id: str,
                      connection_type: ConnectionType = ConnectionType.COOPERATIVE,
                      strength: float = 1.0, is_language_connection: bool = False):
        """Add a connection between organisms

        AUDIT NOTES:
        - Language connections bypass normal limits (good for linguistic embedding)
        - But still subject to pruning if effective_strength < 0.1
        - effective_strength = strength × stability, stability starts at 0.5
        - Linguistic edges can be removed by _prune_weak_connections() every generation
        - No special protection for linguistic connections from evolutionary pruning
        """
        # Allow language connections to bypass normal limits
        bypass_limits = is_language_connection
        if not self.propose_connection(org_a_id, org_b_id, allow_bypass_limits=bypass_limits):
            if is_language_connection:
                print(f"[LANGUAGE DEBUG] Connection rejected between {org_a_id} and {org_b_id}")
            return False

        connection = SymbioticConnection(
            organism_a_id=org_a_id,
            organism_b_id=org_b_id,
            connection_type=connection_type,
            strength=strength
        )

        self.connections[(org_a_id, org_b_id)] = connection

        # Track language connections separately
        if is_language_connection:
            self.language_connections.add((org_a_id, org_b_id))

            # Also add to linguistic subgraph for protection
            # Note: We don't have word/connector info here, so we'll add a basic entry
            # The practice mode will need to update this with full metadata
            self.language_subgraph.add_linguistic_edge(
                org_a_id, org_b_id, "word_a", "word_b", "connects", strength
            )

        # Add to network graph
        self.network_graph.add_edge(org_a_id, org_b_id,
                                  connection_type=connection_type.value,
                                  strength=strength,
                                  resource_flow=0.0,
                                  is_language_connection=is_language_connection)

        return True

    def _attempt_connection_formation(self):
        """Attempt to form new connections between organisms"""
        if len(self.organisms) < 2:
            return  # Need at least 2 organisms

        # Try to form connections each generation, modulated by new_edge_rate
        base_attempts = min(5, len(self.organisms) // 2)  # Scale with population size
        max_attempts = max(1, int(base_attempts * self.new_edge_rate))  # Apply rate multiplier

        for _ in range(max_attempts):
            # Randomly select a source organism
            org_ids = list(self.organisms.keys())
            if len(org_ids) < 2:
                break

            org_a_id = np.random.choice(org_ids)
            # Candidate targets exclude self and already-connected nodes to A
            connected_to_a = set(self.network_graph.neighbors(org_a_id)) if org_a_id in self.network_graph else set()
            remaining_ids = [oid for oid in org_ids if oid != org_a_id and oid not in connected_to_a]
            if not remaining_ids:
                continue

            # If clustering_bias > 0, prefer targets that close triangles with A
            org_b_id = None
            bias = float(self.clustering_bias)
            if bias > 0 and org_a_id in self.network_graph:
                # Compute shared neighbors count (triangle closing potential)
                neighbors_a = set(self.network_graph.neighbors(org_a_id))
                scores = []
                for candidate in remaining_ids:
                    neighbors_c = set(self.network_graph.neighbors(candidate)) if candidate in self.network_graph else set()
                    shared = len(neighbors_a.intersection(neighbors_c))
                    scores.append(shared)

                max_score = max(scores) if scores else 0
                # Blend uniform probability with normalized scores by bias
                if max_score > 0:
                    norm_scores = [s / max_score for s in scores]
                    weights = [(1.0 - bias) * (1.0 / len(remaining_ids)) + bias * ns for ns in norm_scores]
                    # Normalize weights
                    total_w = sum(weights)
                    if total_w > 0:
                        weights = [w / total_w for w in weights]
                        org_b_id = np.random.choice(remaining_ids, p=np.array(weights))

            # Fallback random choice if no bias applied or no structure to exploit
            if org_b_id is None:
                org_b_id = np.random.choice(remaining_ids)

            # NEW: Use agency router for connection decision (if available)
            if hasattr(self, 'agency_router') and self.agency_router:
                org_a = self.organisms[org_a_id]
                org_b = self.organisms[org_b_id]
                
                # Build context for agency decision
                context = {
                    'org_a_id': org_a_id,
                    'org_b_id': org_b_id,
                    'org_a_fitness': org_a.fitness,
                    'org_b_fitness': org_b.fitness,
                    'org_a_connections': len([(a, b) for (a, b), _ in self.connections.items() if a == org_a_id or b == org_a_id]),
                    'org_b_connections': len([(a, b) for (a, b), _ in self.connections.items() if a == org_b_id or b == org_b_id]),
                    'compatibility_score': 1.0 - abs(org_a.fitness - org_b.fitness),
                    'distance': len(nx.shortest_path(self.network_graph, org_a_id, org_b_id)) - 1 if org_a_id in self.network_graph and org_b_id in self.network_graph and nx.has_path(self.network_graph, org_a_id, org_b_id) else float('inf'),
                    'organism_count': len(self.organisms),
                    'connection_count': len(self.network_graph.edges()),
                    'modularity': self.metrics.modularity if hasattr(self.metrics, 'modularity') else 1.0,
                    'clustering_coefficient': self.metrics.clustering_coefficient if hasattr(self.metrics, 'clustering_coefficient') else 0.0,
                    'average_path_length': self.metrics.average_path_length if hasattr(self.metrics, 'average_path_length') else 0.0,
                    'network_stability': self.metrics.ecosystem_stability if hasattr(self.metrics, 'ecosystem_stability') else 0.0
                }
                
                # Agency decides: connect or not
                options = ["connect_immediate", "connect_delayed", "reject"]
                decision = self.agency_router.make_decision("network_connection", context, options)
                
                # Execute decision
                if decision == "connect_immediate" or decision == "connect":
                    if not self.network_graph.has_edge(org_a_id, org_b_id):
                        self.add_connection(org_a_id, org_b_id)
                elif decision == "connect_delayed":
                    # Queue for next cycle (simplified: just skip for now)
                    pass
                # else: "reject" - don't connect
            else:
                # Fallback: Original behavior (try to form connection)
                if not self.network_graph.has_edge(org_a_id, org_b_id):
                    self.add_connection(org_a_id, org_b_id)

    def update_network(self):
        """Update network state for one generation"""
        start_time = time.time()

        # Try to form new connections between organisms
        self._attempt_connection_formation()
        
        # Execute neural organism decisions (for DQN learning)
        # This enables neural organisms to accumulate experiences and learn
        network_state = {
            'generation': self.generation,
            'organism_count': len(self.organisms),
            'connection_count': len(self.network_graph.edges()),
            'modularity': self.metrics.modularity,
            'clustering_coefficient': self.metrics.clustering_coefficient,
            'max_connections_per_organism': self.max_connections_per_organism,
            'resource_pool': getattr(self.resource_engine, 'total_resources', 200.0),
        }
        # Enrich network_state with latest VP metrics if available via Agency Router OR external VP source
        try:
            vp_components_default = {
                'trait_divergence': 0.0,
                'network_coherence': 0.0,
                'quantum_entropy': 0.0,
                'evolution_pressure': 0.0,
                'phase_mismatch': 0.0,
            }
            vp_total = None
            vp_components = None
            
            # Try external VP source first (from Explorer/Djinn Kernel via unified_entry.py)
            if hasattr(self, '_external_vp_data') and self._external_vp_data:
                vp_data = self._external_vp_data
                vp_total = vp_data.get('vp_total')
                vp_components = vp_data.get('vp_components')
                if vp_components:
                    network_state['vp_components'] = {
                        'trait_divergence': float(vp_components.get('trait_divergence', 0.0)),
                        'network_coherence': float(vp_components.get('network_coherence', 0.0)),
                        'quantum_entropy': float(vp_components.get('quantum_entropy', 0.0)),
                        'evolution_pressure': float(vp_components.get('evolution_pressure', 0.0)),
                        'phase_mismatch': float(vp_components.get('phase_mismatch', 0.0)),
                    }
            
            # Fallback to Agency Router if external source not available
            if vp_components is None and hasattr(self, 'agency_router') and self.agency_router and getattr(self.agency_router, 'vp_monitor', None):
                vp_monitor = self.agency_router.vp_monitor
                if hasattr(vp_monitor, 'vp_history') and vp_monitor.vp_history:
                    recent = vp_monitor.vp_history[-1]
                    # Total VP
                    if isinstance(recent, dict):
                        vp_total = recent.get('total_vp', None)
                        # Component breakdown present only when component_decomposition_enabled
                        comp = recent.get('component_breakdown') or {}
                        # Normalize to known keys with defaults
                        vp_components = {
                            'trait_divergence': float(comp.get('trait_divergence', 0.0)),
                            'network_coherence': float(comp.get('network_coherence', 0.0)),
                            'quantum_entropy': float(comp.get('quantum_entropy', 0.0)),
                            'evolution_pressure': float(comp.get('evolution_pressure', 0.0)),
                            'phase_mismatch': float(comp.get('phase_mismatch', 0.0)),
                        }
                        network_state['vp_components'] = vp_components
            
            # Always include keys to keep contracts stable
            if 'vp_components' not in network_state:
                network_state['vp_components'] = vp_components_default
            if vp_total is not None:
                network_state['vp_total'] = float(vp_total)
        except Exception:
            # Never let VP enrichment break simulation; fall back silently
            network_state['vp_components'] = {
                'trait_divergence': 0.0,
                'network_coherence': 0.0,
                'quantum_entropy': 0.0,
                'evolution_pressure': 0.0,
                'phase_mismatch': 0.0,
            }
        
        # Quick Win #5: Add system_health to network_state for organism perception
        try:
            if self.health_monitor is not None:
                # Compute health with available data (neural_stats will be added later if available)
                health_result = self.compute_ecosystem_health(
                    neural_stats=None,  # Neural trainer stats added by main.py if available
                    vp_components=network_state.get('vp_components')
                )
                network_state['system_health'] = health_result.get('health_score', 0.5)
            else:
                network_state['system_health'] = 0.5  # Neutral default
        except Exception:
            network_state['system_health'] = 0.5
        
        # Collect organism actions for batch execution
        organism_actions = {}
        for org_id, organism in self.organisms.items():
            if hasattr(organism, 'decide_action') and hasattr(organism, 'brain') and organism.brain is not None:
                # Get local environment for this organism
                local_env = {
                    'resources': getattr(organism, 'resources', 0.5),
                    'neighbors': len(list(self.network_graph.neighbors(org_id))) if org_id in self.network_graph else 0,
                }
                # Let organism make decision (accumulates experience, decays epsilon)
                try:
                    action = organism.decide_action(
                        local_env=local_env,
                        network_state=network_state,
                        breath_state=None  # Will be set by unified entry if available
                    )
                    organism_actions[org_id] = action
                except Exception:
                    pass  # Don't let neural decision errors crash the simulation
        
        # Execute collected actions
        self._execute_organism_actions(organism_actions, network_state)

        # Calculate resource flows
        flows = self.resource_engine.calculate_flows(self.network_graph, self.organisms)

        # Update connections with flows
        for (org_a, org_b), flow in flows.items():
            if (org_a, org_b) in self.connections:
                self.connections[(org_a, org_b)].resource_flow = flow
                # Update graph
                self.network_graph[org_a][org_b]['resource_flow'] = flow

        # Distribute resources
        resource_distribution = self.resource_engine.distribute_resources(
            self.network_graph, self.organisms, flows
        )

        # Update organism fitness based on resources
        self.resource_engine.update_organism_fitness(self.organisms, resource_distribution)

        # Evaluate cooperation/competition interactions
        for connection in self.connections.values():
            org_a = self.organisms.get(connection.organism_a_id)
            org_b = self.organisms.get(connection.organism_b_id)

            if org_a and org_b:
                fitness_change_a, fitness_change_b = self.cooperation_engine.evaluate_interaction(
                    org_a, org_b, connection
                )

                # Apply fitness changes
                org_a.fitness = np.clip(org_a.fitness + fitness_change_a, 0.0, 1.0)
                org_b.fitness = np.clip(org_b.fitness + fitness_change_b, 0.0, 1.0)

        # ✅ FIX: Fitness diversity preservation
        # Prevent all organisms from converging to same value
        self._preserve_fitness_diversity()

        # Update network metrics
        self.metrics.update_from_network(self.network_graph, self.organisms)

        # Analyze ecosystem stability
        stability_analysis = self.emergence_engine.analyze_ecosystem_stability(
            self.network_graph, self.metrics
        )

        # Apply memory-based selection pressure (penalize unreferenced, boost reference triangles)
        memory_adjustments = self.apply_memory_based_selection_pressure(self.context_memory)
        
        # Language Teacher: Teach organisms words based on behavior and state
        if self.language_teacher is not None:
            try:
                teaching_result = self.language_teacher.teach_network(
                    self.organisms,
                    self.context_memory,
                    self.generation
                )
                # Log teaching stats for monitoring (don't store in undefined result)
                if teaching_result.get('enabled') and teaching_result.get('words_assigned', 0) > 0:
                    logging.debug(f"[LANGUAGE] Taught {teaching_result.get('organisms_taught', 0)} organisms, assigned {teaching_result.get('words_assigned', 0)} words")
            except Exception as e:
                # Don't let language teaching errors break simulation
                logging.warning(f"[SYMBIOTIC_NETWORK] Language teaching error: {e}")
        
        # Log memory stability metrics every 10 generations
        if self.generation % 10 == 0:
            stability_metrics = self.context_memory.get_stability_metrics() if self.context_memory else {}
            logging.debug(f"[SYMBIOTIC_NETWORK] Generation {self.generation}: "
                         f"stability={stability_metrics.get('stability', 0.0):.3f}")
        
        # Run ML analysis (clustering, anomaly detection, dimensionality reduction)
        # Only runs if ML analyzer is configured and enabled
        ml_analysis = None
        if self.ml_analyzer is not None:
            ml_analysis = self.run_ml_analysis()
        
        # Store ML analysis in context_memory for neural system access
        if self.context_memory and ml_analysis and ml_analysis.get('enabled'):
            self.context_memory._ml_analysis_cache = ml_analysis
            
        # Record generation state in context memory for episodic tracking
        self.context_memory.record_generation_state(self.generation, {
            'organism_count': len(self.organisms),
            'connection_count': len(self.connections),
            'avg_fitness': np.mean([org.fitness for org in self.organisms.values()]) if self.organisms else 0.0,
            'memory_adjustments': memory_adjustments
        })

        # Remove weak/unstable connections (with linguistic edge protection)
        self._prune_weak_connections_protected()

        # Update linguistic subgraph generation and sync periodically
        self.language_subgraph.update_generation(self.generation + 1)

        # Periodic sync of linguistic subgraph to main graph
        if (self.generation + 1 - self.language_subgraph.last_sync_generation) >= \
           self.language_subgraph.retention_policies['sync_interval']:
            self.language_subgraph.synchronize_to_main_graph(self)

        self.generation += 1

        elapsed = time.time() - start_time

        result = {
            'generation': self.generation,
            'num_organisms': len(self.organisms),
            'num_connections': len(self.connections),
            'avg_fitness': np.mean([org.fitness for org in self.organisms.values()]),
            'ecosystem_stability': stability_analysis['overall_stability'],
            'emergent_properties': stability_analysis['emergent_properties'],
            'elapsed_seconds': elapsed
        }
        
        # Include ML analysis summary if available
        if ml_analysis and ml_analysis.get('enabled'):
            result['ml_analysis'] = {
                'clustering': ml_analysis.get('clustering'),
                'anomalies': ml_analysis.get('anomalies'),
                'reduction': ml_analysis.get('reduction')
            }
        
        return result
    
    def _preserve_fitness_diversity(self):
        """
        Prevent fitness convergence by maintaining genetic-based differentiation.
        
        If all organisms have very similar fitness, add small genetic-based variations.
        This ensures meaningful selection pressure even after many cycles.
        """
        if len(self.organisms) < 2:
            return
        
        # Calculate fitness variance
        fitnesses = [org.fitness for org in self.organisms.values()]
        fitness_variance = np.var(fitnesses)
        fitness_mean = np.mean(fitnesses)
        
        # If variance is too low (< 0.01), add genetic-based differentiation
        if fitness_variance < 0.01:
            for org_id, organism in self.organisms.items():
                # Get genetic uniqueness factor
                if hasattr(organism, 'genotype') and hasattr(organism.genotype, 'get_hash'):
                    genotype_hash = organism.genotype.get_hash()
                    try:
                        hash_int = int(genotype_hash[:6], 16) if len(genotype_hash) >= 6 else hash(genotype_hash)
                    except (ValueError, TypeError):
                        hash_int = hash(genotype_hash) % 1000000
                    # Create small variation (-0.05 to +0.05) based on genetics
                    genetic_variation = ((hash_int % 1000) / 10000.0) - 0.05
                    
                    # Apply variation (small enough to not disrupt evolution, large enough to differentiate)
                    organism.fitness = np.clip(organism.fitness + genetic_variation, 0.0, 1.0)

    def _execute_organism_actions(self, organism_actions: Dict[str, int], network_state: Dict[str, Any]):
        """
        Execute the actions decided by neural organisms.
        
        Actions:
            0 = move: Try to form new connection with a random non-neighbor
            1 = cooperate: Strengthen connections with neighbors, share resources
            2 = compete: Attempt to gain resources from neighbors
            3 = rest: Do nothing, small fitness recovery
            4 = reproduce: Signal reproductive intent (fitness bonus if high enough)
            5 = isolate: Weaken connections, become more independent
        
        Args:
            organism_actions: Dict mapping organism_id to action index
            network_state: Current network state for context
        """
        for org_id, action in organism_actions.items():
            organism = self.organisms.get(org_id)
            if organism is None:
                continue
            
            try:
                if action == 0:  # MOVE - form new connection
                    self._execute_move_action(org_id, organism)
                elif action == 1:  # COOPERATE - strengthen bonds
                    self._execute_cooperate_action(org_id, organism)
                elif action == 2:  # COMPETE - take resources
                    self._execute_compete_action(org_id, organism)
                elif action == 3:  # REST - recover
                    self._execute_rest_action(org_id, organism)
                elif action == 4:  # REPRODUCE - signal intent
                    self._execute_reproduce_action(org_id, organism)
                elif action == 5:  # ISOLATE - weaken connections
                    self._execute_isolate_action(org_id, organism)
            except Exception:
                pass  # Don't let action execution errors crash simulation
    
    def _execute_move_action(self, org_id: str, organism):
        """Move action: Try to form a new connection with a non-neighbor"""
        if org_id not in self.network_graph:
            return
        
        neighbors = set(self.network_graph.neighbors(org_id))
        non_neighbors = [oid for oid in self.organisms.keys() 
                        if oid != org_id and oid not in neighbors]
        
        if non_neighbors and len(neighbors) < self.max_connections_per_organism:
            target_id = np.random.choice(non_neighbors)
            if not self.network_graph.has_edge(org_id, target_id):
                self.add_connection(org_id, target_id)
    
    def _execute_cooperate_action(self, org_id: str, organism):
        """Cooperate action: Strengthen connections and share resources"""
        if org_id not in self.network_graph:
            return
        
        neighbors = list(self.network_graph.neighbors(org_id))
        for neighbor_id in neighbors:
            edge_key = (org_id, neighbor_id) if (org_id, neighbor_id) in self.connections else (neighbor_id, org_id)
            if edge_key in self.connections:
                # Strengthen the connection
                connection = self.connections[edge_key]
                connection.strength = min(1.0, connection.strength + 0.05)
                connection.stability = min(1.0, connection.stability + 0.02)
                
                # Small resource sharing (boost neighbor fitness slightly)
                neighbor = self.organisms.get(neighbor_id)
                if neighbor and organism.fitness > 0.3:
                    fitness_gift = 0.01
                    organism.fitness = max(0.0, organism.fitness - fitness_gift)
                    neighbor.fitness = min(1.0, neighbor.fitness + fitness_gift)
    
    def _execute_compete_action(self, org_id: str, organism):
        """Compete action: Try to gain resources from neighbors"""
        if org_id not in self.network_graph:
            return
        
        neighbors = list(self.network_graph.neighbors(org_id))
        for neighbor_id in neighbors:
            neighbor = self.organisms.get(neighbor_id)
            if neighbor:
                # Competition based on relative fitness
                if organism.fitness > neighbor.fitness:
                    # Winner takes a small portion
                    gain = 0.02 * (organism.fitness - neighbor.fitness)
                    organism.fitness = min(1.0, organism.fitness + gain)
                    neighbor.fitness = max(0.0, neighbor.fitness - gain)
                else:
                    # Loser loses a bit for trying
                    organism.fitness = max(0.0, organism.fitness - 0.005)
    
    def _execute_rest_action(self, org_id: str, organism):
        """Rest action: Small fitness recovery, do nothing else"""
        # Small passive fitness gain for resting
        organism.fitness = min(1.0, organism.fitness + 0.005)
    
    def _execute_reproduce_action(self, org_id: str, organism):
        """Reproduce action: Signal reproductive intent via fitness boost"""
        # Reproduction intent - if fitness is high enough, get a small boost
        # (actual reproduction handled by evolution engine based on fitness)
        if organism.fitness > 0.6:
            organism.fitness = min(1.0, organism.fitness + 0.01)
            # Mark as wanting to reproduce (for evolution engine to pick up)
            if not hasattr(organism, 'reproduction_intent'):
                organism.reproduction_intent = 0
            organism.reproduction_intent += 1
    
    def _execute_isolate_action(self, org_id: str, organism):
        """Isolate action: Weaken connections, become more independent"""
        if org_id not in self.network_graph:
            return
        
        neighbors = list(self.network_graph.neighbors(org_id))
        for neighbor_id in neighbors:
            edge_key = (org_id, neighbor_id) if (org_id, neighbor_id) in self.connections else (neighbor_id, org_id)
            if edge_key in self.connections:
                # Weaken the connection
                connection = self.connections[edge_key]
                connection.strength = max(0.0, connection.strength - 0.1)
                connection.stability = max(0.0, connection.stability - 0.05)

    def _prune_weak_connections_protected(self):
        """Remove connections that have become too weak, with linguistic edge protection

        AUDIT NOTES:
        - Called every generation in update_network()
        - Removes connections where effective_strength < 0.1
        - But protects linguistic edges that have exceeded minimum lifetime
        - Linguistic subgraph provides backup persistence
        """
        connections_to_remove = []

        # Get protected linguistic edges
        protected_edges = set(self.language_subgraph.get_persistent_edges())

        for (org_a, org_b), connection in self.connections.items():
            edge_key = (org_a, org_b)

            # Check if this is a protected linguistic edge
            if edge_key in protected_edges:
                # Protected edges get a strength boost and are not pruned
                connection.stability = min(1.0, connection.stability *
                                         self.language_subgraph.retention_policies['priority_boost'])
                continue

            # Normal pruning for non-protected edges
            if connection.get_effective_strength() < 0.1:
                connections_to_remove.append((org_a, org_b))

        removed_count = 0
        for org_a, org_b in connections_to_remove:
            del self.connections[(org_a, org_b)]
            if self.network_graph.has_edge(org_a, org_b):
                self.network_graph.remove_edge(org_a, org_b)
            removed_count += 1

        if removed_count > 0:
            print(f"[NETWORK PRUNING] Removed {removed_count} weak connections "
                  f"(protected {len(protected_edges)} linguistic edges)")

    def _prune_weak_connections(self):
        """Legacy method - now calls the protected version"""
        self._prune_weak_connections_protected()

    def apply_memory_based_selection_pressure(self, context_memory: ContextMemory) -> Dict[str, float]:
        """
        Apply selection pressure based on context memory coherence.

        Penalizes unreferenced nodes (selection pressure) and boosts edges that close
        reference triangles (stability mechanisms).

        Args:
            context_memory: The shared context memory instance

        Returns:
            Dictionary of applied adjustments for logging
        """
        adjustments = {
            'unreferenced_penalty_count': 0,
            'reference_triangle_bonus_count': 0,
            'total_penalty_applied': 0.0,
            'total_bonus_applied': 0.0
        }

        # Get stability metrics from memory
        stability_metrics = context_memory.get_stability_metrics()

        # SELECTION PRESSURE: Penalize organisms not referenced in memory
        referenced_nodes = set()
        for word, node_ids in context_memory.language_anchors.items():
            referenced_nodes.update(node_ids)

        for org_id, organism in self.organisms.items():
            if org_id not in referenced_nodes:
                # Apply penalty for unreferenced organisms
                penalty = -0.05 * (1.0 - stability_metrics.get('anchor_density', 0.5))
                organism.fitness = max(0.0, organism.fitness + penalty)
                adjustments['unreferenced_penalty_count'] += 1
                adjustments['total_penalty_applied'] += abs(penalty)

        # STABILIZATION: Boost edges that close reference triangles
        anchor_clusters = context_memory.get_anchor_clusters(min_cluster_size=2)

        for cluster in anchor_clusters:
            cluster_nodes = set(cluster['nodes'])

            # Find edges within this cluster that aren't language-tagged
            for node_a in cluster_nodes:
                for node_b in cluster_nodes:
                    if node_a != node_b and (node_a, node_b) in self.connections:
                        connection = self.connections[(node_a, node_b)]

                        # Boost stability of edges within reference clusters
                        stability_bonus = 0.02 * cluster['size'] / max(len(self.organisms), 1)
                        connection.strength = min(1.0, connection.strength + stability_bonus)
                        adjustments['reference_triangle_bonus_count'] += 1
                        adjustments['total_bonus_applied'] += stability_bonus

        return adjustments

    def log_memory_stability_metrics(self, context_memory: ContextMemory) -> None:
        """
        Log stability metrics from context memory for monitoring.

        Args:
            context_memory: The shared context memory instance
        """
        stability_metrics = context_memory.get_stability_metrics()

        print(f"[MEMORY_STABILITY] Gen {self.generation} - "
              f"Anchor Density: {stability_metrics.get('anchor_density', 0):.3f}, "
              f"Language Coherence: {stability_metrics.get('language_coherence', 0):.3f}, "
              f"Cluster Stability: {stability_metrics.get('cluster_stability', 0):.3f}")

    def get_network_stats(self) -> Dict[str, Any]:
        """Get comprehensive network statistics"""
        return {
            'num_organisms': len(self.organisms),
            'num_connections': len(self.connections),
            'network_density': nx.density(self.network_graph) if len(self.network_graph) > 0 else 0,
            'metrics': self.metrics,
            'communities': self.emergence_engine.detect_communities(self.network_graph),
            'trophic_levels': self.emergence_engine.identify_trophic_levels(
                self.network_graph, self.organisms
            ),
            'linguistic_subgraph': self.language_subgraph.get_subgraph_stats(),
            'linguistic_integration_ratio': self.language_subgraph.get_subgraph_stats().get('total_edges', 0) / max(1, len(self.connections)),
            'generation': self.generation
        }

    def visualize_network(self, figsize=(10, 8)):
        """Create a basic network visualization"""
        try:
            import matplotlib.pyplot as plt

            plt.figure(figsize=figsize)

            # Position nodes using spring layout
            pos = nx.spring_layout(self.network_graph, k=2, iterations=50)

            # Node colors based on fitness
            node_colors = [self.organisms.get(node, Organism(Genotype(genes=np.array([0])))).fitness
                          for node in self.network_graph.nodes()]

            # Edge colors based on connection type
            edge_colors = []
            for edge in self.network_graph.edges():
                edge_data = self.network_graph.get_edge_data(*edge, {})
                conn_type = edge_data.get('connection_type', 'cooperative')
                if conn_type == 'cooperative':
                    edge_colors.append('green')
                elif conn_type == 'competitive':
                    edge_colors.append('red')
                else:
                    edge_colors.append('blue')

            # Draw
            nx.draw_networkx_nodes(self.network_graph, pos,
                                 node_color=node_colors, cmap=plt.cm.viridis,
                                 node_size=300, alpha=0.8)

            nx.draw_networkx_edges(self.network_graph, pos,
                                 edge_color=edge_colors, width=2, alpha=0.6)

            nx.draw_networkx_labels(self.network_graph, pos, font_size=8)

            plt.title(f"Symbiotic Network - Generation {self.generation}")
            plt.colorbar(plt.cm.ScalarMappable(cmap=plt.cm.viridis), label='Fitness')
            plt.axis('off')

            return plt.gcf()

        except ImportError:
            print("Matplotlib not available for visualization")
            return None

    def set_new_edge_rate(self, rate: float):
        """Set the new edge formation rate multiplier"""
        self.new_edge_rate = max(0.0, min(2.0, rate))  # Clamp to reasonable bounds

    def get_new_edge_rate(self) -> float:
        """Get the current new edge formation rate multiplier"""
        return self.new_edge_rate

    def exchange_token_embeddings(self, 
                                   vp_value: Optional[float] = None,
                                   max_exchanges: int = 10) -> Dict[str, Any]:
        """
        Exchange token embeddings between connected organisms for language learning.
        
        This enables organisms to share "communication patterns" across network edges,
        facilitating emergent vocabulary through social learning.
        
        Respects LinguisticSubgraph retention policies:
        - Only exchanges over edges with min_lifetime_generations >= 10
        - VP gating: Higher VP = more selective exchange
        
        Args:
            vp_value: Current VP value for gating exchanges
            max_exchanges: Maximum exchanges per update
            
        Returns:
            Summary of exchanges performed
        """
        exchanges = []
        
        # VP gating - reduce exchanges during high uncertainty
        if vp_value is not None and vp_value > 0.6:
            max_exchanges = max(1, max_exchanges // 3)
        
        # Get eligible language connections from linguistic subgraph
        eligible_edges = []
        for (a, b), edge_data in self.language_subgraph.edges.items():
            # Only use edges with sufficient lifetime
            if edge_data.get('min_lifetime_generations', 0) >= 10:
                if a in self.organisms and b in self.organisms:
                    eligible_edges.append((a, b, edge_data))
        
        # Fallback to regular connections if no linguistic edges
        if not eligible_edges:
            for (a, b) in list(self.language_connections)[:max_exchanges]:
                if a in self.organisms and b in self.organisms:
                    eligible_edges.append((a, b, {'strength': 0.5}))
        
        # Perform token exchanges
        for a_id, b_id, edge_data in eligible_edges[:max_exchanges]:
            org_a = self.organisms[a_id]
            org_b = self.organisms[b_id]
            
            # Exchange token sequences if organisms have them
            if hasattr(org_a, 'token_sequence') and hasattr(org_b, 'token_sequence'):
                # Get recent tokens from both
                tokens_a = list(org_a.token_sequence)[-16:] if org_a.token_sequence else []
                tokens_b = list(org_b.token_sequence)[-16:] if org_b.token_sequence else []
                
                # Cross-pollinate: each organism gets a sample from the other
                if tokens_a and len(org_b.token_sequence) < 128:
                    for t in tokens_a[:4]:  # Exchange up to 4 tokens
                        org_b.token_sequence.append(t)
                
                if tokens_b and len(org_a.token_sequence) < 128:
                    for t in tokens_b[:4]:
                        org_a.token_sequence.append(t)
                
                tokens_exchanged = min(4, len(tokens_a), len(tokens_b))
                exchanges.append({
                    'from': a_id,
                    'to': b_id,
                    'tokens_exchanged': tokens_exchanged,
                    'edge_strength': edge_data.get('strength', 0.5)
                })
                
                # Only emit organism_communication event for very significant exchanges (quality over quantity)
                # Match ML event selectivity - only meaningful communications
                if self.ml_event_emitter and tokens_exchanged > 0:
                    connection_strength = edge_data.get('strength', 0.5)
                    is_linguistic_edge = edge_data.get('min_lifetime_generations', 0) >= 10
                    # Much higher threshold - only emit for very strong linguistic edges with large exchanges
                    if is_linguistic_edge and connection_strength > 0.8 and tokens_exchanged >= 10:
                        try:
                            from causation_explorer import Event
                            event = Event(
                                timestamp=time.time(),
                                component='language',  # FIXED: Changed from 'network' to 'language' for proper causation linking
                                event_type='organism_communication',
                                data={
                                    'organism_a_id': a_id,
                                    'organism_b_id': b_id,
                                    'tokens_exchanged': tokens_exchanged,
                                    'num_organisms': 2,  # Added for causation explanation
                                    'connection_strength': connection_strength,
                                    'vp_value': vp_value,
                                    'is_linguistic_edge': is_linguistic_edge
                                }
                            )
                            self.ml_event_emitter(event)
                        except ImportError:
                            pass  # CausationExplorer not available
        
        return {
            'exchanges_performed': len(exchanges),
            'eligible_edges': len(eligible_edges),
            'vp_gated': vp_value is not None and vp_value > 0.6,
            'details': exchanges if len(exchanges) <= 5 else exchanges[:5]  # Limit for logging
        }

    def cleanup_organism_embeddings(self, organism_id: str) -> None:
        """
        Clean up token embeddings when an organism dies.
        
        Removes any cached embeddings or token sequences associated
        with the deceased organism to prevent memory leaks.
        
        Args:
            organism_id: ID of the organism being removed
        """
        # Remove from linguistic subgraph
        self.language_subgraph.remove_organism_edges(organism_id)
        
        # Remove from language connections tracking
        connections_to_remove = [
            (a, b) for (a, b) in self.language_connections 
            if a == organism_id or b == organism_id
        ]
        for conn in connections_to_remove:
            self.language_connections.discard(conn)

    def set_clustering_bias(self, bias: float):
        """Set bias toward triangle closure (0.0 = explore, 1.0 = cluster)"""
        self.clustering_bias = float(np.clip(bias, 0.0, 1.0))

    def get_clustering_bias(self) -> float:
        """Get current clustering bias value"""
        return float(self.clustering_bias)


# Utility function for easy network creation
def create_symbiotic_network(organisms: List[Organism] = None,
                           max_connections: int = 5,
                           new_edge_rate: float = 1.0,
                           context_memory: Optional[ContextMemory] = None,
                           config: Optional[Dict[str, Any]] = None) -> SymbioticNetwork:
    """Create a symbiotic network with optional initial organisms
    
    Args:
        organisms: Optional list of initial organisms to add to the network
        max_connections: Maximum connections per organism
        new_edge_rate: Multiplier for connection attempt rate (0.0 to 2.0)
        context_memory: Optional ContextMemory instance for language anchoring.
                       If None, a new instance is created automatically.
        config: Optional configuration dictionary for language teacher and other features
    
    Returns:
        Configured SymbioticNetwork instance
    """
    network = SymbioticNetwork(max_connections_per_organism=max_connections,
                               new_edge_rate=new_edge_rate,
                               context_memory=context_memory,
                               config=config)

    if organisms:
        for organism in organisms:
            network.add_organism(organism)

    return network


# Module-level docstring
"""
🌐 SYMBIOTIC NETWORK = WHERE ORGANISMS CONNECT

This module creates the social fabric of the simulation:
- Organisms form connections through AI-guided decisions
- Resources flow through cooperative/competitive dynamics
- Ecosystems emerge with stability and diversity
- AI makes binary "connect or not?" decisions

The network is where individual organisms become a society.
"""

