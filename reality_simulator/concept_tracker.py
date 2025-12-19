"""
ConceptTracker - Semantic Naming for Behavioral Phenotypes

Tracks cluster persistence and promotes stable clusters to named concepts.
This is Quick Win #2 for enhancing the system's capacity for understanding.

A cluster becomes a "concept" after persisting for N consecutive cycles.
Concepts are auto-tagged with semantic names based on organism properties.

Examples of concept names:
- "explorers" - high movement, moderate fitness
- "settlers" - low movement, stable resources
- "cooperators" - high connections, moderate fitness
- "loners" - low connections, variable fitness
- "thrivers" - high fitness, high resources
- "strugglers" - low fitness, low resources
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any, Callable
import time
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class Concept:
    """A stable behavioral phenotype with semantic meaning"""
    concept_id: str  # "explorers", "settlers", "cooperators", etc.
    first_seen: float  # timestamp
    last_seen: float
    cluster_history: List[Tuple[float, int]] = field(default_factory=list)  # [(timestamp, cluster_id)]
    population_history: List[Tuple[float, int]] = field(default_factory=list)  # [(timestamp, count)]
    parent_concept: Optional[str] = None
    child_concepts: List[str] = field(default_factory=list)
    properties: Dict[str, float] = field(default_factory=dict)  # avg fitness, connections, etc.
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            'concept_id': self.concept_id,
            'first_seen': self.first_seen,
            'last_seen': self.last_seen,
            'cluster_history': self.cluster_history[-10:],  # Last 10 entries to avoid bloat
            'population_history': self.population_history[-10:],
            'parent_concept': self.parent_concept,
            'child_concepts': self.child_concepts,
            'properties': self.properties,
            'lifespan': self.last_seen - self.first_seen,
            'persistence': len(self.cluster_history)
        }


class ConceptTracker:
    """
    Tracks cluster persistence and promotes stable clusters to concepts.
    
    A cluster becomes a concept after existing for N consecutive cycles.
    Concepts are auto-tagged with semantic names based on organism properties.
    
    This enables the system to develop semantic understanding of behavioral
    patterns, forming the foundation for higher-order reasoning about
    population dynamics.
    """
    
    # Semantic naming thresholds
    HIGH_FITNESS = 0.7
    MED_FITNESS = 0.4
    HIGH_RESOURCES = 0.7
    LOW_RESOURCES = 0.3
    HIGH_CONNECTIONS = 5  # Average connections threshold
    LOW_CONNECTIONS = 2
    
    def __init__(self, 
                 persistence_threshold: int = 3,
                 stale_threshold: float = 10.0,
                 enabled: bool = True):
        """
        Args:
            persistence_threshold: Number of cycles a cluster must persist to become a concept
            stale_threshold: Time after which unseen clusters are pruned
            enabled: Enable/disable concept tracking
        """
        self.persistence_threshold = persistence_threshold
        self.stale_threshold = stale_threshold
        self.enabled = enabled
        
        # Cluster tracking
        self.cluster_history: Dict[int, List[Tuple[float, int]]] = {}  # cluster_id → [(timestamp, size)]
        self.cluster_last_seen: Dict[int, float] = {}  # cluster_id → timestamp
        
        # Concept registry
        self.concepts: Dict[str, Concept] = {}  # concept_id → Concept
        self.cluster_to_concept: Dict[int, str] = {}  # cluster_id → concept_id (current mapping)
        
        # Concept naming counter (for uniqueness)
        self.concept_counter: Dict[str, int] = {}  # base_name → count
        
        # Event emitter callback (will be set by MLAnalyzer or main)
        self.event_emitter: Optional[Callable[[Dict[str, Any]], None]] = None
        
        # SEMANTIC CONVERGENCE: ContextMemory for feeding phenotype names to vocabulary
        self.context_memory: Optional[Any] = None
        
        # Statistics
        self.total_concepts_created = 0
        self.total_concepts_extinct = 0
        
        logger.info(f"[ConceptTracker] Initialized (persistence={persistence_threshold}, enabled={enabled})")
    
    def update(self,
               cluster_labels: np.ndarray,
               cluster_sizes: Dict[int, int],
               organisms: Dict[str, Any],
               timestamp: Optional[float] = None) -> Dict[int, str]:
        """
        Update cluster tracking and promote stable clusters to concepts.
        
        Args:
            cluster_labels: Cluster assignment for each organism (numpy array)
            cluster_sizes: {cluster_id: count}
            organisms: Dict of organism objects for property extraction
            timestamp: Current timestamp (defaults to time.time())
            
        Returns:
            Dict mapping cluster_id → concept_id (for clusters that have become concepts)
        """
        if not self.enabled:
            return {}
        
        if timestamp is None:
            timestamp = time.time()
        
        concept_tags = {}
        
        # Track cluster persistence
        for cluster_id, size in cluster_sizes.items():
            if cluster_id == -1:  # Skip noise cluster (HDBSCAN)
                continue
            
            # Update history
            if cluster_id not in self.cluster_history:
                self.cluster_history[cluster_id] = []
            
            self.cluster_history[cluster_id].append((timestamp, size))
            self.cluster_last_seen[cluster_id] = timestamp
            
            # Check if cluster should be promoted to concept
            persistence = len(self.cluster_history[cluster_id])
            
            if persistence >= self.persistence_threshold:
                # Cluster is stable - promote or update concept
                if cluster_id in self.cluster_to_concept:
                    # Concept already exists - update it
                    concept_id = self.cluster_to_concept[cluster_id]
                    self._update_concept(concept_id, cluster_id, size, organisms, cluster_labels, timestamp)
                else:
                    # New concept - create it
                    concept_id = self._create_concept(cluster_id, size, organisms, cluster_labels, timestamp)
                    self.cluster_to_concept[cluster_id] = concept_id
                
                concept_tags[cluster_id] = concept_id
        
        # Prune stale clusters (not seen recently)
        self._prune_stale_clusters(timestamp)
        
        return concept_tags
    
    def _create_concept(self,
                        cluster_id: int,
                        size: int,
                        organisms: Dict[str, Any],
                        cluster_labels: np.ndarray,
                        timestamp: float) -> str:
        """Create new concept from stable cluster"""
        # Extract cluster organisms
        cluster_organism_ids = self._get_cluster_organisms(cluster_id, cluster_labels, organisms)
        
        # Auto-tag concept based on properties
        base_name = self._auto_tag_cluster(cluster_organism_ids, organisms)
        
        # Make unique by appending counter if needed
        if base_name in self.concept_counter:
            self.concept_counter[base_name] += 1
            concept_id = f"{base_name}_{self.concept_counter[base_name]}"
        else:
            self.concept_counter[base_name] = 1
            concept_id = base_name
        
        # Calculate properties
        properties = self._calculate_cluster_properties(cluster_organism_ids, organisms)
        
        # Create concept
        concept = Concept(
            concept_id=concept_id,
            first_seen=timestamp,
            last_seen=timestamp,
            cluster_history=[(timestamp, cluster_id)],
            population_history=[(timestamp, size)],
            properties=properties
        )
        
        self.concepts[concept_id] = concept
        self.total_concepts_created += 1
        
        # SEMANTIC CONVERGENCE: Feed phenotype name to language vocabulary
        # GROUNDED MODE: Skip concept linking - organisms earn vocabulary through mastery, not concept emergence
        grounded_mode_enabled = False
        if self.context_memory is not None and hasattr(self.context_memory, 'config'):
            config = getattr(self.context_memory, 'config', {})
            if config:
                lang_config = config.get('language', {})
                grounded_config = lang_config.get('grounded', {})
                grounded_mode_enabled = grounded_config.get('enabled', False)
        
        if self.context_memory is not None and not grounded_mode_enabled:
            try:
                # Register concept name (e.g., "social_thrivers") as language anchor
                for org_id in cluster_organism_ids[:10]:  # Limit to avoid flooding
                    # Convert organism ID to int hash if needed
                    org_id_int = hash(org_id) if isinstance(org_id, str) else org_id
                    # Try to get organism embedding for semantic differentiation
                    org_embedding = None
                    if org_id in organisms:  # Fixed: was 'all_organisms', should be 'organisms'
                        org = organisms[org_id]
                        if hasattr(org, 'get_language_embedding'):
                            try:
                                org_embedding = org.get_language_embedding(self.context_memory)
                            except Exception:
                                pass
                    self.context_memory.link_word_to_node(concept_id, org_id_int, None, organism_embedding=org_embedding)
                    # Also link component words (e.g., "social", "thrivers")
                    for word in concept_id.replace('_', ' ').split():
                        if len(word) > 2:  # Skip very short fragments
                            self.context_memory.link_word_to_node(word, org_id_int, None, organism_embedding=org_embedding)
                logger.debug(f"[ConceptTracker] Linked phenotype '{concept_id}' to language anchors")
            except Exception as e:
                logger.warning(f"[ConceptTracker] Failed to link concept to language: {e}")
        
        # Emit concept emergence event
        self._emit_concept_event("concept_emergence", concept)
        
        logger.info(f"[ConceptTracker] 🌱 New concept emerged: '{concept_id}' (cluster {cluster_id}, pop={size})")
        
        return concept_id
    
    def _update_concept(self,
                        concept_id: str,
                        cluster_id: int,
                        size: int,
                        organisms: Dict[str, Any],
                        cluster_labels: np.ndarray,
                        timestamp: float):
        """Update existing concept"""
        concept = self.concepts[concept_id]
        concept.last_seen = timestamp
        concept.cluster_history.append((timestamp, cluster_id))
        concept.population_history.append((timestamp, size))
        
        # Update properties
        cluster_organism_ids = self._get_cluster_organisms(cluster_id, cluster_labels, organisms)
        concept.properties = self._calculate_cluster_properties(cluster_organism_ids, organisms)
    
    def _auto_tag_cluster(self, cluster_organism_ids: List[str], all_organisms: Dict[str, Any]) -> str:
        """
        Auto-tag cluster with semantic name based on organism properties.
        
        Decision tree for concept naming:
        - High fitness + high connections → "social_thrivers"
        - High fitness + low connections → "lone_wolves"
        - Low fitness + high connections → "social_strugglers"
        - Low fitness + low connections → "loners"
        - High resources + low fitness → "hoarders"
        - Low resources + high fitness → "efficient_survivors"
        - High generation age → "elders"
        - Low generation age + high fitness → "prodigies"
        """
        if not cluster_organism_ids:
            return "unknown"
        
        # Calculate average properties
        try:
            avg_fitness = np.mean([getattr(all_organisms[oid], 'fitness', 0.5) for oid in cluster_organism_ids])
            avg_resources = np.mean([getattr(all_organisms[oid], 'resources', 0.5) for oid in cluster_organism_ids])
            
            # Try to get connection count if available
            avg_connections = 0
            try:
                avg_connections = np.mean([len(getattr(all_organisms[oid], 'connections', [])) for oid in cluster_organism_ids])
            except (AttributeError, TypeError):
                avg_connections = 2  # Default to medium
            
            # Try to get generation/age if available
            avg_generation = 0
            try:
                avg_generation = np.mean([getattr(all_organisms[oid], 'generation', 0) for oid in cluster_organism_ids])
            except (AttributeError, TypeError):
                avg_generation = 1  # Default
                
        except Exception as e:
            logger.warning(f"[ConceptTracker] Error calculating properties: {e}")
            return "unclassified"
        
        # Decision tree for semantic naming
        
        # Connection-based modifiers
        is_social = avg_connections >= self.HIGH_CONNECTIONS
        is_solitary = avg_connections <= self.LOW_CONNECTIONS
        
        # Primary classification based on fitness + resources
        if avg_fitness >= self.HIGH_FITNESS:
            if avg_resources >= self.HIGH_RESOURCES:
                return "prosperous" if not is_social else "social_elite"
            elif avg_resources <= self.LOW_RESOURCES:
                return "efficient_survivors"
            else:
                if is_social:
                    return "social_thrivers"
                elif is_solitary:
                    return "lone_wolves"
                else:
                    return "thrivers"
        
        elif avg_fitness >= self.MED_FITNESS:
            if avg_resources >= self.HIGH_RESOURCES:
                return "hoarders"
            elif is_social:
                return "cooperators"
            elif is_solitary:
                return "independents"
            else:
                return "settlers"
        
        else:  # Low fitness
            if avg_resources >= self.HIGH_RESOURCES:
                return "inefficient"
            elif is_social:
                return "social_strugglers"
            elif is_solitary:
                return "loners"
            else:
                return "strugglers"
    
    def _calculate_cluster_properties(self, cluster_organism_ids: List[str], all_organisms: Dict[str, Any]) -> Dict[str, float]:
        """Calculate average properties for cluster"""
        if not cluster_organism_ids:
            return {}
        
        try:
            properties = {
                'avg_fitness': float(np.mean([getattr(all_organisms[oid], 'fitness', 0.5) for oid in cluster_organism_ids])),
                'avg_resources': float(np.mean([getattr(all_organisms[oid], 'resources', 0.5) for oid in cluster_organism_ids])),
                'population': len(cluster_organism_ids)
            }
            
            # Try to add connection stats
            try:
                connections = [len(getattr(all_organisms[oid], 'connections', [])) for oid in cluster_organism_ids]
                properties['avg_connections'] = float(np.mean(connections))
            except (AttributeError, TypeError):
                pass
            
            # Try to add generation stats
            try:
                generations = [getattr(all_organisms[oid], 'generation', 0) for oid in cluster_organism_ids]
                properties['avg_generation'] = float(np.mean(generations))
            except (AttributeError, TypeError):
                pass
            
            return properties
            
        except Exception as e:
            logger.warning(f"[ConceptTracker] Error calculating cluster properties: {e}")
            return {'population': len(cluster_organism_ids)}
    
    def _get_cluster_organisms(self, cluster_id: int, cluster_labels: np.ndarray, organisms: Dict[str, Any]) -> List[str]:
        """Get organism IDs belonging to a cluster"""
        try:
            organism_ids = list(organisms.keys())
            if len(organism_ids) != len(cluster_labels):
                # Mismatch - return empty
                return []
            return [organism_ids[i] for i, label in enumerate(cluster_labels) if label == cluster_id]
        except Exception as e:
            logger.warning(f"[ConceptTracker] Error getting cluster organisms: {e}")
            return []
    
    def _prune_stale_clusters(self, current_timestamp: float):
        """Remove clusters that haven't been seen recently"""
        stale_clusters = [
            cid for cid, last_seen in self.cluster_last_seen.items()
            if current_timestamp - last_seen > self.stale_threshold
        ]
        
        for cluster_id in stale_clusters:
            # Remove from tracking
            if cluster_id in self.cluster_history:
                del self.cluster_history[cluster_id]
            if cluster_id in self.cluster_last_seen:
                del self.cluster_last_seen[cluster_id]
            
            # If cluster had a concept, mark concept as extinct
            if cluster_id in self.cluster_to_concept:
                concept_id = self.cluster_to_concept[cluster_id]
                if concept_id in self.concepts:
                    concept = self.concepts[concept_id]
                    self._emit_concept_event("concept_extinction", concept)
                    self.total_concepts_extinct += 1
                    logger.info(f"[ConceptTracker] 💀 Concept extinct: '{concept_id}' (lifespan={concept.last_seen - concept.first_seen:.1f}s)")
                    # Keep concept in registry for history, but remove mapping
                del self.cluster_to_concept[cluster_id]
    
    def _emit_concept_event(self, event_type: str, concept: Concept):
        """Emit concept event to causation graph.
        
        Event format matches the Event dataclass contract expected by neural_event_emitter:
        - timestamp: float
        - component: str (source system)
        - event_type: str (event name)
        - data: Dict[str, Any] (all payload data)
        """
        if not self.event_emitter:
            return
        
        try:
            # Format matches Event dataclass contract (unified_entry.py)
            event = {
                'timestamp': concept.last_seen,
                'component': 'concept_tracker',
                'event_type': event_type,
                'data': {
                    'concept_id': concept.concept_id,
                    'properties': concept.properties,
                    'persistence': len(concept.cluster_history),
                    'lifespan': concept.last_seen - concept.first_seen
                }
            }
            
            self.event_emitter(event)
        except Exception as e:
            logger.warning(f"[ConceptTracker] Error emitting event: {e}")
    
    def get_concept_summary(self) -> Dict[str, Any]:
        """Get summary of all concepts (active and historical)"""
        active_concepts = {
            cid: c.to_dict() for cid, c in self.concepts.items()
            if cid in self.cluster_to_concept.values()
        }
        
        historical_concepts = {
            cid: c.to_dict() for cid, c in self.concepts.items()
            if cid not in self.cluster_to_concept.values()
        }
        
        return {
            'total_concepts_created': self.total_concepts_created,
            'total_concepts_extinct': self.total_concepts_extinct,
            'active_concepts': len(active_concepts),
            'active': active_concepts,
            'historical': historical_concepts,
            'cluster_mappings': dict(self.cluster_to_concept)
        }
    
    def get_active_concepts(self) -> Dict[str, Concept]:
        """Get currently active concepts only"""
        return {
            cid: self.concepts[cid] 
            for cid in self.cluster_to_concept.values() 
            if cid in self.concepts
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Full state for serialization"""
        return {
            'enabled': self.enabled,
            'persistence_threshold': self.persistence_threshold,
            'stale_threshold': self.stale_threshold,
            'total_concepts_created': self.total_concepts_created,
            'total_concepts_extinct': self.total_concepts_extinct,
            'concepts': {cid: c.to_dict() for cid, c in self.concepts.items()},
            'cluster_to_concept': dict(self.cluster_to_concept)
        }
