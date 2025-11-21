"""
CollapseMap Engine - Phase 2.4 Implementation

This module implements the entropy management service that monitors bloom pressure,
calculates collapse pathways, and executes controlled entropy compression to ensure
the kernel's long-term viability and prevent complexity accumulation.

Key Features:
- Bloom pressure monitoring and quantification
- Collapse pathway calculation and optimization
- Controlled entropy compression algorithms
- Complexity pruning and system optimization
- Entropy state tracking and prediction
- Collapse event coordination and execution
"""

import time
import math
import hashlib
import threading
from typing import Dict, List, Any, Optional, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
from datetime import datetime, timedelta
from collections import defaultdict, deque
import heapq

from synchrony_phase_lock_protocol import ProductionSynchronySystem, SynchronizedOperation, SynchronyLevel, OperationPriority
from arbitration_stack import ProductionArbitrationStack
from advanced_trait_engine import AdvancedTraitEngine
from utm_kernel_design import UTMKernel
from event_driven_coordination import DjinnEventBus, EventType
from violation_pressure_calculation import ViolationMonitor, ViolationClass


class EntropyState(Enum):
    """States of entropy within the system"""
    STABLE = "stable"                     # Low entropy, stable state
    ACCUMULATING = "accumulating"         # Entropy increasing
    BLOOMING = "blooming"                 # High entropy, bloom pressure
    COLLAPSING = "collapsing"             # Active collapse in progress
    COMPRESSING = "compressing"           # Entropy compression active
    CRITICAL = "critical"                 # Critical entropy levels


class CollapseType(Enum):
    """Types of collapse operations"""
    SOFT_COLLAPSE = "soft_collapse"       # Gentle complexity reduction
    HARD_COLLAPSE = "hard_collapse"       # Aggressive pruning
    EMERGENCY_COLLAPSE = "emergency_collapse"  # Critical system rescue
    PREDICTIVE_COLLAPSE = "predictive_collapse"  # Proactive optimization


class CompressionStrategy(Enum):
    """Strategies for entropy compression"""
    CONSERVATIVE = "conservative"         # Minimal impact compression
    BALANCED = "balanced"                 # Moderate compression
    AGGRESSIVE = "aggressive"             # High-impact compression
    EMERGENCY = "emergency"               # Emergency compression


@dataclass
class BloomPressureMetrics:
    """Metrics for monitoring bloom pressure"""
    current_pressure: float = 0.0
    pressure_threshold: float = 0.7
    pressure_history: deque = field(default_factory=lambda: deque(maxlen=100))
    pressure_trend: float = 0.0
    last_update: datetime = field(default_factory=datetime.utcnow)
    
    def update_pressure(self, new_pressure: float) -> None:
        """Update bloom pressure and calculate trend"""
        self.current_pressure = new_pressure
        self.pressure_history.append(new_pressure)
        self.last_update = datetime.utcnow()
        
        # Calculate trend over last 10 measurements
        if len(self.pressure_history) >= 10:
            recent = list(self.pressure_history)[-10:]
            self.pressure_trend = (recent[-1] - recent[0]) / len(recent)
    
    def is_blooming(self) -> bool:
        """Check if system is in bloom state"""
        return self.current_pressure >= self.pressure_threshold
    
    def get_pressure_velocity(self) -> float:
        """Get rate of pressure change"""
        if len(self.pressure_history) < 2:
            return 0.0
        return self.pressure_trend


@dataclass
class EntropyNode:
    """A node in the entropy map representing a complexity source"""
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    entropy_value: float = 0.0
    complexity_score: float = 0.0
    stability_factor: float = 1.0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    collapse_priority: float = 0.0
    compression_resistance: float = 0.0
    
    def calculate_entropy_contribution(self) -> float:
        """Calculate this node's contribution to system entropy"""
        time_factor = 1.0 / (1.0 + (datetime.utcnow() - self.last_accessed).total_seconds() / 3600)
        return self.entropy_value * self.complexity_score * time_factor * (1.0 / self.stability_factor)


@dataclass
class CollapsePathway:
    """A calculated pathway for entropy collapse"""
    pathway_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    collapse_type: CollapseType = CollapseType.SOFT_COLLAPSE
    target_nodes: List[str] = field(default_factory=list)
    estimated_entropy_reduction: float = 0.0
    complexity_impact: float = 0.0
    execution_risk: float = 0.0
    priority_score: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    execution_order: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def calculate_priority_score(self) -> float:
        """Calculate overall priority score for this pathway"""
        # Higher entropy reduction and lower risk = higher priority
        efficiency = self.estimated_entropy_reduction / max(self.execution_risk, 0.1)
        return efficiency * (1.0 - self.complexity_impact)


@dataclass
class CompressionEvent:
    """An entropy compression event"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    compression_strategy: CompressionStrategy = CompressionStrategy.BALANCED
    target_entropy_reduction: float = 0.0
    actual_entropy_reduction: float = 0.0
    affected_nodes: List[str] = field(default_factory=list)
    compression_metrics: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    success: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)


class EntropyMap:
    """Maps and tracks entropy sources throughout the system"""
    
    def __init__(self):
        self.nodes: Dict[str, EntropyNode] = {}
        self.connections: Dict[str, Set[str]] = defaultdict(set)
        self.entropy_history = deque(maxlen=1000)
        self.last_calculation: Optional[datetime] = None
        
    def add_node(self, node: EntropyNode) -> None:
        """Add a node to the entropy map"""
        self.nodes[node.node_id] = node
        
        # Update connections
        for dep_id in node.dependencies:
            if dep_id in self.nodes:
                self.connections[dep_id].add(node.node_id)
    
    def remove_node(self, node_id: str) -> bool:
        """Remove a node from the entropy map"""
        if node_id not in self.nodes:
            return False
        
        node = self.nodes[node_id]
        
        # Remove connections
        for dep_id in node.dependencies:
            if dep_id in self.connections:
                self.connections[dep_id].discard(node_id)
        
        # Remove from dependents
        for dependent_id in node.dependents:
            if dependent_id in self.nodes:
                self.nodes[dependent_id].dependencies.discard(node_id)
        
        del self.nodes[node_id]
        return True
    
    def calculate_total_entropy(self) -> float:
        """Calculate total system entropy"""
        total_entropy = 0.0
        
        for node in self.nodes.values():
            total_entropy += node.calculate_entropy_contribution()
        
        # Add connection complexity
        connection_entropy = len(self.connections) * 0.1
        total_entropy += connection_entropy
        
        self.entropy_history.append(total_entropy)
        self.last_calculation = datetime.utcnow()
        
        return total_entropy
    
    def get_high_entropy_nodes(self, threshold: float = 0.5) -> List[EntropyNode]:
        """Get nodes with high entropy values"""
        return [
            node for node in self.nodes.values()
            if node.calculate_entropy_contribution() > threshold
        ]
    
    def get_isolated_nodes(self) -> List[EntropyNode]:
        """Get nodes with no dependencies or dependents"""
        return [
            node for node in self.nodes.values()
            if not node.dependencies and not node.dependents
        ]
    
    def calculate_entropy_trend(self) -> float:
        """Calculate entropy trend over time"""
        if len(self.entropy_history) < 10:
            return 0.0
        
        recent = list(self.entropy_history)[-10:]
        return (recent[-1] - recent[0]) / len(recent)


class CollapsePathwayCalculator:
    """Calculates optimal collapse pathways for entropy reduction"""
    
    def __init__(self, entropy_map: EntropyMap):
        self.entropy_map = entropy_map
        self.pathway_cache = {}
        self.calculation_history = []
        
    def calculate_collapse_pathways(self, target_reduction: float,
                                   collapse_type: CollapseType) -> List[CollapsePathway]:
        """Calculate multiple collapse pathways for given target"""
        
        pathways = []
        
        if collapse_type == CollapseType.SOFT_COLLAPSE:
            pathways.extend(self._calculate_soft_collapse_pathways(target_reduction))
        elif collapse_type == CollapseType.HARD_COLLAPSE:
            pathways.extend(self._calculate_hard_collapse_pathways(target_reduction))
        elif collapse_type == CollapseType.EMERGENCY_COLLAPSE:
            pathways.extend(self._calculate_emergency_collapse_pathways(target_reduction))
        elif collapse_type == CollapseType.PREDICTIVE_COLLAPSE:
            pathways.extend(self._calculate_predictive_collapse_pathways(target_reduction))
        
        # Sort by priority score
        pathways.sort(key=lambda p: p.calculate_priority_score(), reverse=True)
        
        return pathways
    
    def _calculate_soft_collapse_pathways(self, target_reduction: float) -> List[CollapsePathway]:
        """Calculate gentle collapse pathways"""
        pathways = []
        
        # Target isolated nodes first
        isolated_nodes = self.entropy_map.get_isolated_nodes()
        if isolated_nodes:
            pathway = CollapsePathway(
                collapse_type=CollapseType.SOFT_COLLAPSE,
                target_nodes=[node.node_id for node in isolated_nodes[:3]],
                estimated_entropy_reduction=sum(node.calculate_entropy_contribution() for node in isolated_nodes[:3]),
                complexity_impact=0.1,
                execution_risk=0.1
            )
            pathway.calculate_priority_score()
            pathways.append(pathway)
        
        # Target low-stability nodes
        low_stability_nodes = [
            node for node in self.entropy_map.nodes.values()
            if node.stability_factor < 0.5
        ]
        
        if low_stability_nodes:
            pathway = CollapsePathway(
                collapse_type=CollapseType.SOFT_COLLAPSE,
                target_nodes=[node.node_id for node in low_stability_nodes[:2]],
                estimated_entropy_reduction=sum(node.calculate_entropy_contribution() for node in low_stability_nodes[:2]),
                complexity_impact=0.2,
                execution_risk=0.2
            )
            pathway.calculate_priority_score()
            pathways.append(pathway)
        
        return pathways
    
    def _calculate_hard_collapse_pathways(self, target_reduction: float) -> List[CollapsePathway]:
        """Calculate aggressive collapse pathways"""
        pathways = []
        
        # Target high-entropy nodes regardless of dependencies
        high_entropy_nodes = self.entropy_map.get_high_entropy_nodes(0.7)
        
        if high_entropy_nodes:
            pathway = CollapsePathway(
                collapse_type=CollapseType.HARD_COLLAPSE,
                target_nodes=[node.node_id for node in high_entropy_nodes[:5]],
                estimated_entropy_reduction=sum(node.calculate_entropy_contribution() for node in high_entropy_nodes[:5]),
                complexity_impact=0.5,
                execution_risk=0.4
            )
            pathway.calculate_priority_score()
            pathways.append(pathway)
        
        return pathways
    
    def _calculate_emergency_collapse_pathways(self, target_reduction: float) -> List[CollapsePathway]:
        """Calculate emergency collapse pathways"""
        pathways = []
        
        # Target all high-entropy nodes
        all_nodes = list(self.entropy_map.nodes.values())
        all_nodes.sort(key=lambda n: n.calculate_entropy_contribution(), reverse=True)
        
        pathway = CollapsePathway(
            collapse_type=CollapseType.EMERGENCY_COLLAPSE,
            target_nodes=[node.node_id for node in all_nodes[:10]],
            estimated_entropy_reduction=sum(node.calculate_entropy_contribution() for node in all_nodes[:10]),
            complexity_impact=0.8,
            execution_risk=0.7
        )
        pathway.calculate_priority_score()
        pathways.append(pathway)
        
        return pathways
    
    def _calculate_predictive_collapse_pathways(self, target_reduction: float) -> List[CollapsePathway]:
        """Calculate predictive collapse pathways based on trends"""
        pathways = []
        
        # Analyze entropy trends to predict future high-entropy nodes
        trend = self.entropy_map.calculate_entropy_trend()
        
        if trend > 0.1:  # Increasing entropy trend
            # Target nodes that are likely to become problematic
            growing_nodes = [
                node for node in self.entropy_map.nodes.values()
                if node.access_count > 10 and node.stability_factor < 0.7
            ]
            
            if growing_nodes:
                pathway = CollapsePathway(
                    collapse_type=CollapseType.PREDICTIVE_COLLAPSE,
                    target_nodes=[node.node_id for node in growing_nodes[:3]],
                    estimated_entropy_reduction=sum(node.calculate_entropy_contribution() for node in growing_nodes[:3]) * 0.5,
                    complexity_impact=0.3,
                    execution_risk=0.2
                )
                pathway.calculate_priority_score()
                pathways.append(pathway)
        
        return pathways


class EntropyCompressor:
    """Executes controlled entropy compression operations"""
    
    def __init__(self, entropy_map: EntropyMap, synchrony_system: ProductionSynchronySystem):
        self.entropy_map = entropy_map
        self.synchrony_system = synchrony_system
        self.compression_history = []
        self.active_compressions = {}
        
    def execute_compression(self, pathway: CollapsePathway,
                          strategy: CompressionStrategy) -> CompressionEvent:
        """Execute entropy compression based on pathway and strategy"""
        
        start_time = time.time()
        event = CompressionEvent(
            compression_strategy=strategy,
            target_entropy_reduction=pathway.estimated_entropy_reduction
        )
        
        try:
            # Create synchronized operation for compression
            compression_operation = SynchronizedOperation(
                operation_type="entropy_compression",
                operation_data={
                    "pathway_id": pathway.pathway_id,
                    "target_nodes": pathway.target_nodes,
                    "strategy": strategy.value,
                    "estimated_reduction": pathway.estimated_entropy_reduction
                },
                priority=OperationPriority.HIGH if strategy == CompressionStrategy.EMERGENCY else OperationPriority.NORMAL,
                synchrony_level=SynchronyLevel.ENHANCED,
                source_agent="collapsemap_engine"
            )
            
            # Submit for synchronized execution
            operation_id = self.synchrony_system.submit_synchronized_operation(compression_operation)
            
            # Register readiness
            if compression_operation.phase_gate:
                self.synchrony_system.register_participant_ready(
                    compression_operation.phase_gate.gate_id,
                    "collapsemap_engine",
                    compression_operation.calculate_operation_hash()
                )
            
            # Execute compression based on strategy
            actual_reduction = self._apply_compression_strategy(pathway, strategy)
            
            # Update event
            event.actual_entropy_reduction = actual_reduction
            event.affected_nodes = pathway.target_nodes
            event.execution_time = time.time() - start_time
            event.success = actual_reduction > 0
            
            # Record compression metrics
            event.compression_metrics = {
                "strategy_effectiveness": actual_reduction / pathway.estimated_entropy_reduction if pathway.estimated_entropy_reduction > 0 else 0,
                "nodes_compressed": len(pathway.target_nodes),
                "compression_efficiency": actual_reduction / event.execution_time if event.execution_time > 0 else 0
            }
            
        except Exception as e:
            event.success = False
            event.compression_metrics["error"] = str(e)
        
        # Record event
        self.compression_history.append(event)
        
        return event
    
    def _apply_compression_strategy(self, pathway: CollapsePathway,
                                  strategy: CompressionStrategy) -> float:
        """Apply specific compression strategy to pathway"""
        
        total_reduction = 0.0
        
        for node_id in pathway.target_nodes:
            if node_id not in self.entropy_map.nodes:
                continue
            
            node = self.entropy_map.nodes[node_id]
            original_entropy = node.calculate_entropy_contribution()
            
            if strategy == CompressionStrategy.CONSERVATIVE:
                # Gentle entropy reduction
                reduction_factor = 0.2
                node.entropy_value *= (1.0 - reduction_factor)
                node.complexity_score *= 0.9
                
            elif strategy == CompressionStrategy.BALANCED:
                # Moderate entropy reduction
                reduction_factor = 0.4
                node.entropy_value *= (1.0 - reduction_factor)
                node.complexity_score *= 0.8
                
            elif strategy == CompressionStrategy.AGGRESSIVE:
                # High entropy reduction
                reduction_factor = 0.6
                node.entropy_value *= (1.0 - reduction_factor)
                node.complexity_score *= 0.7
                
            elif strategy == CompressionStrategy.EMERGENCY:
                # Emergency entropy reduction
                reduction_factor = 0.8
                node.entropy_value *= (1.0 - reduction_factor)
                node.complexity_score *= 0.5
                
                # Remove node if entropy becomes very low
                if node.calculate_entropy_contribution() < 0.1:
                    self.entropy_map.remove_node(node_id)
                    total_reduction += original_entropy
                    continue
            
            new_entropy = node.calculate_entropy_contribution()
            total_reduction += (original_entropy - new_entropy)
        
        return total_reduction


class CollapseMapEngine:
    """
    CollapseMap Engine implementing entropy management, bloom pressure monitoring,
    collapse pathway calculation, and controlled entropy compression.
    """
    
    def __init__(self, synchrony_system: ProductionSynchronySystem,
                 arbitration_stack: ProductionArbitrationStack,
                 advanced_engine: AdvancedTraitEngine,
                 utm_kernel: UTMKernel,
                 event_bus: Optional[DjinnEventBus] = None):
        """Initialize the CollapseMap Engine"""
        self.synchrony_system = synchrony_system
        self.arbitration_stack = arbitration_stack
        self.advanced_engine = advanced_engine
        self.utm_kernel = utm_kernel
        self.event_bus = event_bus or DjinnEventBus()
        
        # Core components
        self.entropy_map = EntropyMap()
        self.bloom_metrics = BloomPressureMetrics()
        self.pathway_calculator = CollapsePathwayCalculator(self.entropy_map)
        self.entropy_compressor = EntropyCompressor(self.entropy_map, self.synchrony_system)
        
        # Engine state
        self.current_entropy_state = EntropyState.STABLE
        self.entropy_thresholds = {
            EntropyState.STABLE: 0.3,
            EntropyState.ACCUMULATING: 0.5,
            EntropyState.BLOOMING: 0.7,
            EntropyState.COLLAPSING: 0.8,
            EntropyState.CRITICAL: 0.9
        }
        
        # Monitoring and control
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._entropy_monitor, daemon=True)
        self.monitor_thread.start()
        
        # Statistics
        self.engine_metrics = {
            "total_compressions": 0,
            "total_entropy_reduction": 0.0,
            "bloom_events": 0,
            "collapse_events": 0,
            "last_entropy_calculation": None
        }
    
    def register_entropy_source(self, name: str, entropy_value: float,
                              complexity_score: float, dependencies: List[str] = None) -> str:
        """Register a new entropy source in the map"""
        
        node = EntropyNode(
            name=name,
            entropy_value=entropy_value,
            complexity_score=complexity_score,
            dependencies=set(dependencies or [])
        )
        
        self.entropy_map.add_node(node)
        return node.node_id
    
    def update_entropy_source(self, node_id: str, entropy_value: float = None,
                            complexity_score: float = None) -> bool:
        """Update an existing entropy source"""
        
        if node_id not in self.entropy_map.nodes:
            return False
        
        node = self.entropy_map.nodes[node_id]
        
        if entropy_value is not None:
            node.entropy_value = entropy_value
        
        if complexity_score is not None:
            node.complexity_score = complexity_score
        
        node.last_accessed = datetime.utcnow()
        node.access_count += 1
        
        return True
    
    def calculate_bloom_pressure(self) -> float:
        """Calculate current bloom pressure based on system state"""
        
        # Calculate total system entropy
        total_entropy = self.entropy_map.calculate_total_entropy()
        
        # Calculate entropy trend
        entropy_trend = self.entropy_map.calculate_entropy_trend()
        
        # Calculate complexity factor
        complexity_factor = len(self.entropy_map.nodes) / 100.0  # Normalize to 0-1
        
        # Calculate bloom pressure
        base_pressure = total_entropy / 10.0  # Normalize entropy
        trend_pressure = max(0, entropy_trend) * 2.0  # Amplify positive trends
        complexity_pressure = complexity_factor * 0.3
        
        bloom_pressure = min(1.0, base_pressure + trend_pressure + complexity_pressure)
        
        # Update bloom metrics
        self.bloom_metrics.update_pressure(bloom_pressure)
        
        return bloom_pressure
    
    def determine_entropy_state(self) -> EntropyState:
        """Determine current entropy state based on metrics"""
        
        bloom_pressure = self.calculate_bloom_pressure()
        total_entropy = self.entropy_map.calculate_total_entropy()
        
        # Determine state based on thresholds
        if bloom_pressure >= self.entropy_thresholds[EntropyState.CRITICAL]:
            return EntropyState.CRITICAL
        elif bloom_pressure >= self.entropy_thresholds[EntropyState.COLLAPSING]:
            return EntropyState.COLLAPSING
        elif bloom_pressure >= self.entropy_thresholds[EntropyState.BLOOMING]:
            return EntropyState.BLOOMING
        elif bloom_pressure >= self.entropy_thresholds[EntropyState.ACCUMULATING]:
            return EntropyState.ACCUMULATING
        else:
            return EntropyState.STABLE
    
    def calculate_collapse_pathways(self, target_reduction: float = None,
                                  collapse_type: CollapseType = None) -> List[CollapsePathway]:
        """Calculate collapse pathways for current entropy state"""
        
        current_state = self.determine_entropy_state()
        total_entropy = self.entropy_map.calculate_total_entropy()
        
        # Determine target reduction if not specified
        if target_reduction is None:
            if current_state == EntropyState.CRITICAL:
                target_reduction = total_entropy * 0.5
            elif current_state == EntropyState.COLLAPSING:
                target_reduction = total_entropy * 0.3
            elif current_state == EntropyState.BLOOMING:
                target_reduction = total_entropy * 0.2
            else:
                target_reduction = total_entropy * 0.1
        
        # Determine collapse type if not specified
        if collapse_type is None:
            if current_state == EntropyState.CRITICAL:
                collapse_type = CollapseType.EMERGENCY_COLLAPSE
            elif current_state == EntropyState.COLLAPSING:
                collapse_type = CollapseType.HARD_COLLAPSE
            elif current_state == EntropyState.BLOOMING:
                collapse_type = CollapseType.SOFT_COLLAPSE
            else:
                collapse_type = CollapseType.PREDICTIVE_COLLAPSE
        
        return self.pathway_calculator.calculate_collapse_pathways(target_reduction, collapse_type)
    
    def execute_collapse(self, pathway: CollapsePathway,
                        strategy: CompressionStrategy = None) -> CompressionEvent:
        """Execute a collapse pathway"""
        
        # Determine strategy if not specified
        if strategy is None:
            if pathway.collapse_type == CollapseType.EMERGENCY_COLLAPSE:
                strategy = CompressionStrategy.EMERGENCY
            elif pathway.collapse_type == CollapseType.HARD_COLLAPSE:
                strategy = CompressionStrategy.AGGRESSIVE
            elif pathway.collapse_type == CollapseType.SOFT_COLLAPSE:
                strategy = CompressionStrategy.BALANCED
            else:
                strategy = CompressionStrategy.CONSERVATIVE
        
        # Execute compression
        event = self.entropy_compressor.execute_compression(pathway, strategy)
        
        # Update metrics
        if event.success:
            self.engine_metrics["total_compressions"] += 1
            self.engine_metrics["total_entropy_reduction"] += event.actual_entropy_reduction
            self.engine_metrics["collapse_events"] += 1
        
        return event
    
    def auto_collapse(self) -> Optional[CompressionEvent]:
        """Automatically execute collapse if needed"""
        
        current_state = self.determine_entropy_state()
        
        # Only auto-collapse if in critical states
        if current_state in [EntropyState.CRITICAL, EntropyState.COLLAPSING]:
            
            # Calculate pathways
            pathways = self.calculate_collapse_pathways()
            
            if pathways:
                # Execute highest priority pathway
                best_pathway = pathways[0]
                return self.execute_collapse(best_pathway)
        
        return None
    
    def _entropy_monitor(self) -> None:
        """Background monitor for entropy management"""
        
        while self.monitoring_active:
            try:
                # Calculate current state
                current_state = self.determine_entropy_state()
                
                # Update state if changed
                if current_state != self.current_entropy_state:
                    self.current_entropy_state = current_state
                    
                    # Trigger bloom event if entering bloom state
                    if current_state == EntropyState.BLOOMING:
                        self.engine_metrics["bloom_events"] += 1
                
                # Auto-collapse if needed
                if current_state in [EntropyState.CRITICAL, EntropyState.COLLAPSING]:
                    self.auto_collapse()
                
                # Update metrics
                self.engine_metrics["last_entropy_calculation"] = datetime.utcnow()
                
                time.sleep(5.0)  # 5-second monitoring cycle
                
            except Exception as e:
                print(f"Entropy monitor error: {e}")
                time.sleep(10.0)
    
    def get_engine_metrics(self) -> Dict[str, Any]:
        """Get comprehensive engine metrics"""
        
        current_entropy = self.entropy_map.calculate_total_entropy()
        bloom_pressure = self.calculate_bloom_pressure()
        current_state = self.determine_entropy_state()
        
        return {
            "current_entropy_state": current_state.value,
            "total_system_entropy": current_entropy,
            "bloom_pressure": bloom_pressure,
            "entropy_trend": self.entropy_map.calculate_entropy_trend(),
            "active_nodes": len(self.entropy_map.nodes),
            "engine_metrics": self.engine_metrics.copy(),
            "bloom_metrics": {
                "current_pressure": self.bloom_metrics.current_pressure,
                "pressure_trend": self.bloom_metrics.pressure_trend,
                "is_blooming": self.bloom_metrics.is_blooming()
            },
            "compression_history_size": len(self.entropy_compressor.compression_history),
            "last_compression": (
                self.entropy_compressor.compression_history[-1].timestamp.isoformat() + "Z"
                if self.entropy_compressor.compression_history
                else None
            )
        }
    
    def export_entropy_map(self) -> Dict[str, Any]:
        """Export complete entropy map state"""
        
        return {
            "nodes": {
                node_id: {
                    "name": node.name,
                    "entropy_value": node.entropy_value,
                    "complexity_score": node.complexity_score,
                    "stability_factor": node.stability_factor,
                    "access_count": node.access_count,
                    "dependencies": list(node.dependencies),
                    "dependents": list(node.dependents),
                    "last_accessed": node.last_accessed.isoformat() + "Z"
                } for node_id, node in self.entropy_map.nodes.items()
            },
            "connections": {
                node_id: list(dependents)
                for node_id, dependents in self.entropy_map.connections.items()
            },
            "entropy_history": list(self.entropy_map.entropy_history),
            "total_entropy": self.entropy_map.calculate_total_entropy()
        }
    
    def shutdown(self) -> None:
        """Shutdown the CollapseMap Engine"""
        self.monitoring_active = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)


# Example usage and testing
if __name__ == "__main__":
    # Initialize dependencies (mock for testing)
    from core_trait_framework import CoreTraitFramework
    
    print("=== CollapseMap Engine Test ===")
    
    # Initialize components
    core_framework = CoreTraitFramework()
    advanced_engine = AdvancedTraitEngine(core_framework)
    arbitration_stack = ProductionArbitrationStack(advanced_engine)
    utm_kernel = UTMKernel()
    synchrony_system = ProductionSynchronySystem(arbitration_stack, utm_kernel)
    
    collapsemap_engine = CollapseMapEngine(
        synchrony_system, arbitration_stack, advanced_engine, utm_kernel
    )
    
    # Register some entropy sources
    print("\n1. Registering entropy sources...")
    
    node1_id = collapsemap_engine.register_entropy_source(
        "high_complexity_trait", 0.8, 0.9
    )
    node2_id = collapsemap_engine.register_entropy_source(
        "unstable_identity", 0.6, 0.7
    )
    node3_id = collapsemap_engine.register_entropy_source(
        "isolated_component", 0.4, 0.5
    )
    
    print(f"   Registered nodes: {node1_id}, {node2_id}, {node3_id}")
    
    # Calculate initial metrics
    print("\n2. Calculating initial metrics...")
    
    initial_entropy = collapsemap_engine.entropy_map.calculate_total_entropy()
    initial_pressure = collapsemap_engine.calculate_bloom_pressure()
    initial_state = collapsemap_engine.determine_entropy_state()
    
    print(f"   Initial entropy: {initial_entropy:.3f}")
    print(f"   Bloom pressure: {initial_pressure:.3f}")
    print(f"   Entropy state: {initial_state.value}")
    
    # Calculate collapse pathways
    print("\n3. Calculating collapse pathways...")
    
    pathways = collapsemap_engine.calculate_collapse_pathways()
    
    print(f"   Found {len(pathways)} collapse pathways")
    
    for i, pathway in enumerate(pathways[:3]):  # Show first 3
        print(f"   Pathway {i+1}: {pathway.collapse_type.value}")
        print(f"     Target nodes: {len(pathway.target_nodes)}")
        print(f"     Estimated reduction: {pathway.estimated_entropy_reduction:.3f}")
        print(f"     Priority score: {pathway.calculate_priority_score():.3f}")
    
    # Execute a collapse
    if pathways:
        print("\n4. Executing collapse...")
        
        event = collapsemap_engine.execute_collapse(pathways[0])
        
        print(f"   Compression event: {event.event_id}")
        print(f"   Strategy: {event.compression_strategy.value}")
        print(f"   Success: {event.success}")
        print(f"   Actual reduction: {event.actual_entropy_reduction:.3f}")
        print(f"   Execution time: {event.execution_time:.3f}s")
    
    # Get final metrics
    print("\n5. Final metrics...")
    
    final_metrics = collapsemap_engine.get_engine_metrics()
    
    print(f"   Current state: {final_metrics['current_entropy_state']}")
    print(f"   Total entropy: {final_metrics['total_system_entropy']:.3f}")
    print(f"   Bloom pressure: {final_metrics['bloom_pressure']:.3f}")
    print(f"   Total compressions: {final_metrics['engine_metrics']['total_compressions']}")
    print(f"   Total reduction: {final_metrics['engine_metrics']['total_entropy_reduction']:.3f}")
    
    # Shutdown
    print("\n6. Shutting down...")
    collapsemap_engine.shutdown()
    
    print("CollapseMap Engine operational!")
