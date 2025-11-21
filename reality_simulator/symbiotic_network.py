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
from typing import List, Dict, Tuple, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum
import networkx as nx
from collections import defaultdict
import time

# Import context memory system
try:
    from .memory.context_memory import ContextMemory
except ImportError:
    # Fallback for relative import issues
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    memory_dir = os.path.join(current_dir, 'memory')
    if memory_dir not in sys.path:
        sys.path.insert(0, memory_dir)
    from context_memory import ContextMemory

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

        # Community detection (simplified modularity)
        try:
            communities = list(nx.community.greedy_modularity_communities(network_graph))
            self.modularity = len(communities) / len(network_graph)  # Rough approximation
        except (ValueError, ZeroDivisionError, AttributeError) as e:
            # NetworkX may raise ValueError for empty graphs or graphs without communities
            # ZeroDivisionError if network_graph is empty
            # AttributeError if networkx.community is not available
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
                # Resource bonus (diminishing returns)
                resource_bonus = np.log(1 + resources) * 0.1
                organisms[org_id].fitness = min(1.0, organisms[org_id].fitness + resource_bonus)


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
        except:
            # Fallback: connected components
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
                 new_edge_rate: float = 1.0):
        self.network_graph = nx.Graph()
        self.connections: Dict[Tuple[str, str], SymbioticConnection] = {}
        self.organisms: Dict[str, Organism] = {}
        self.language_connections: Set[Tuple[str, str]] = set()  # Track language-related connections

        # NEW: Protected linguistic subgraph with retention policies
        self.language_subgraph = LinguisticSubgraph()

        # Component engines
        self.resource_engine = ResourceFlowEngine(resource_pool_size)
        self.cooperation_engine = CooperationCompetitionEngine()
        self.emergence_engine = EcosystemEmergenceEngine()

        # Network constraints
        self.max_connections_per_organism = max_connections_per_organism
        self.new_edge_rate = new_edge_rate  # Multiplier for connection attempts (0.0 to 2.0)
        # Bias toward triangle closure vs exploration (0.0=random/explore, 1.0=prefer clustering)
        self.clustering_bias: float = 0.5

        # Metrics tracking
        self.metrics = EcosystemMetrics()
        self.generation = 0

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

        # Update network metrics
        self.metrics.update_from_network(self.network_graph, self.organisms)

        # Analyze ecosystem stability
        stability_analysis = self.emergence_engine.analyze_ecosystem_stability(
            self.network_graph, self.metrics
        )

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

        return {
            'generation': self.generation,
            'num_organisms': len(self.organisms),
            'num_connections': len(self.connections),
            'avg_fitness': np.mean([org.fitness for org in self.organisms.values()]),
            'ecosystem_stability': stability_analysis['overall_stability'],
            'emergent_properties': stability_analysis['emergent_properties'],
            'elapsed_seconds': elapsed
        }

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

    def set_clustering_bias(self, bias: float):
        """Set bias toward triangle closure (0.0 = explore, 1.0 = cluster)"""
        self.clustering_bias = float(np.clip(bias, 0.0, 1.0))

    def get_clustering_bias(self) -> float:
        """Get current clustering bias value"""
        return float(self.clustering_bias)


# Utility function for easy network creation
def create_symbiotic_network(organisms: List[Organism] = None,
                           max_connections: int = 5,
                           new_edge_rate: float = 1.0) -> SymbioticNetwork:
    """Create a symbiotic network with optional initial organisms"""
    network = SymbioticNetwork(max_connections_per_organism=max_connections,
                               new_edge_rate=new_edge_rate)

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

