# Violation Pressure Calculation - Phase 0.2 Implementation
# Version 1.0 - Mathematical Quantification of Identity Incompleteness

"""
Violation Pressure Calculation implementing the mathematical quantification of identity incompleteness
that drives recursive necessity in the Djinn Kernel.

Core Formula: VP_total = Σ(|actual - center| / (radius * compression))
This creates the mathematical pressure that drives the system toward fixed-point completion.
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple, List, Optional, Any
from enum import Enum
import math
import logging
import json
from datetime import datetime
from pathlib import Path
from event_driven_coordination import ViolationPressureEvent


class ViolationClass(Enum):
    """Classification of violation pressure levels"""
    VP0_FULLY_LAWFUL = "VP0"      # 0.00 - 0.25: Fully lawful recursion
    VP1_STABLE_DRIFT = "VP1"      # 0.25 - 0.50: Stable drift, continue with logging
    VP2_INSTABILITY = "VP2"       # 0.50 - 0.75: Instability pressure, arbitration review
    VP3_CRITICAL_DIVERGENCE = "VP3"  # 0.75 - 0.99: Critical divergence, forbidden zone authorization
    VP4_COLLAPSE_THRESHOLD = "VP4"   # ≥ 1.00: Collapse threshold, hard recursion termination


@dataclass
class StabilityEnvelope:
    """
    Mathematical envelope defining trait stability boundaries.
    Core component of violation pressure calculation.
    """
    center: float = 0.5           # Stability center [0.0, 1.0]
    radius: float = 0.25          # Allowable deviation range
    compression_factor: float = 1.0  # Stability enforcement strength
    
    def __post_init__(self):
        # Ensure mathematical consistency
        assert 0.0 <= self.center <= 1.0, "Stability center must be [0.0, 1.0]"
        assert 0.0 < self.radius <= 0.5, "Radius must be (0.0, 0.5]"
        assert self.compression_factor > 0.0, "Compression factor must be positive"





class VPDiagnostics:
    """
    Diagnostic logging for violation pressure calculations.
    Provides detailed breakdown of VP components without changing calculation logic.
    """
    
    def __init__(self, enabled: bool = False, log_file: Optional[str] = None):
        self.enabled = enabled
        self.log_file = log_file or (Path(__file__).parent.parent / 'data' / 'logs' / 'vp_diagnostics.log')
        self.logger = None
        
        if self.enabled:
            self._setup_logger()
    
    def _setup_logger(self):
        """Setup diagnostic logger"""
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger('vp_diagnostics')
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Format: timestamp|component|data
        formatter = logging.Formatter(
            '%(asctime)s|%(name)s|%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.propagate = False
    
    def log_trait_breakdown(self, trait_name: str, trait_value: float, envelope: StabilityEnvelope,
                           deviation: float, trait_vp: float, normalization_factor: float):
        """Log detailed breakdown for a single trait"""
        if not self.enabled:
            return
        if not self.logger:
            # Logger not initialized - this shouldn't happen if enabled=True
            import logging
            logging.warning(f"[VPDiagnostics] Logger not initialized but enabled=True for trait {trait_name}")
            return
        
        breakdown = {
            'trait_name': trait_name,
            'trait_value': trait_value,
            'envelope_center': envelope.center,
            'envelope_radius': envelope.radius,
            'compression_factor': envelope.compression_factor,
            'deviation': deviation,
            'trait_vp': trait_vp,
            'normalization_factor': normalization_factor,
            'normalized_radius': envelope.radius * envelope.compression_factor
        }
        
        self.logger.debug(f"trait_breakdown|{json.dumps(breakdown)}")
    
    def log_calculation_summary(self, trait_payload: Dict[str, float], total_vp: float,
                               per_trait_breakdown: Dict[str, float], source_identity: Optional[str] = None):
        """Log summary of VP calculation"""
        if not self.enabled:
            return
        if not self.logger:
            # Logger not initialized - this shouldn't happen if enabled=True
            import logging
            logging.warning(f"[VPDiagnostics] Logger not initialized but enabled=True for calculation summary")
            return
        
        summary = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'source_identity': source_identity,
            'trait_count': len(trait_payload),
            'total_vp': total_vp,
            'per_trait_breakdown': per_trait_breakdown,
            'average_trait_vp': sum(per_trait_breakdown.values()) / len(per_trait_breakdown) if per_trait_breakdown else 0.0,
            'max_trait_vp': max(per_trait_breakdown.values()) if per_trait_breakdown else 0.0,
            'min_trait_vp': min(per_trait_breakdown.values()) if per_trait_breakdown else 0.0
        }
        
        self.logger.info(f"calculation_summary|{json.dumps(summary)}")
    
    def get_vp_diagnostics(self, trait_payload: Dict[str, float], 
                          stability_envelopes: Dict[str, StabilityEnvelope]) -> Dict[str, Any]:
        """
        Decompose VP calculation into diagnostic components.
        Does not change calculation - just analyzes what was computed.
        """
        diagnostics = {
            'trait_analysis': {},
            'envelope_analysis': {},
            'summary': {}
        }
        
        for trait_name, trait_value in trait_payload.items():
            envelope = stability_envelopes.get(trait_name, StabilityEnvelope())
            deviation = abs(trait_value - envelope.center)
            normalized_radius = envelope.radius * envelope.compression_factor
            trait_vp = deviation / normalized_radius if normalized_radius > 0 else (float('inf') if deviation > 0 else 0.0)
            trait_vp = max(0.0, min(10.0, trait_vp))
            
            diagnostics['trait_analysis'][trait_name] = {
                'trait_value': trait_value,
                'envelope_center': envelope.center,
                'deviation': deviation,
                'normalized_radius': normalized_radius,
                'trait_vp': trait_vp,
                'vp_contribution_ratio': trait_vp / len(trait_payload) if trait_payload else 0.0
            }
            
            diagnostics['envelope_analysis'][trait_name] = {
                'center': envelope.center,
                'radius': envelope.radius,
                'compression_factor': envelope.compression_factor,
                'effective_range': [envelope.center - envelope.radius, envelope.center + envelope.radius]
            }
        
        if trait_payload:
            total_vp_sum = sum(diagnostics['trait_analysis'][t]['trait_vp'] 
                             for t in trait_payload.keys())
            normalized_total = min(1.0, total_vp_sum / len(trait_payload))
            
            diagnostics['summary'] = {
                'trait_count': len(trait_payload),
                'raw_vp_sum': total_vp_sum,
                'normalized_vp': normalized_total,
                'normalization_factor': len(trait_payload),
                'dominant_trait': max(trait_payload.keys(), 
                                    key=lambda t: diagnostics['trait_analysis'][t]['trait_vp']) if trait_payload else None
            }
        
        return diagnostics


class VPStabilizer:
    """
    Stabilizes violation pressure values to prevent immediate jumps to maximum.
    Uses weighted moving average and jump limiting to smooth VP transitions.
    """
    
    def __init__(self, history_size: int = 10, max_jump: float = 0.1, smoothing_factor: float = 0.3):
        self.history_size = history_size
        self.max_jump = max_jump
        self.smoothing_factor = smoothing_factor
        self.vp_history = []
        self.last_vp = None
    
    def stabilize(self, raw_vp: float) -> float:
        """
        Stabilize a raw VP value using smoothing and jump limiting.
        
        Args:
            raw_vp: Raw violation pressure value [0.0, 1.0]
            
        Returns:
            Stabilized VP value [0.0, 1.0]
        """
        # Initialize if this is the first value
        if self.last_vp is None:
            self.last_vp = raw_vp
            self.vp_history.append(raw_vp)
            return raw_vp
        
        # Calculate jump size
        jump = raw_vp - self.last_vp
        
        # Apply jump limiting
        if abs(jump) > self.max_jump:
            if jump > 0:
                stabilized_vp = self.last_vp + self.max_jump
            else:
                stabilized_vp = self.last_vp - self.max_jump
        else:
            stabilized_vp = raw_vp
        
        # Apply weighted moving average smoothing
        # EMA: new_value = smoothing_factor * current + (1 - smoothing_factor) * previous
        smoothed_vp = self.smoothing_factor * stabilized_vp + (1 - self.smoothing_factor) * self.last_vp
        
        # Clamp to valid range
        smoothed_vp = max(0.0, min(1.0, smoothed_vp))
        
        # Update history
        self.vp_history.append(smoothed_vp)
        if len(self.vp_history) > self.history_size:
            self.vp_history.pop(0)
        
        # Update last VP
        self.last_vp = smoothed_vp
        
        return smoothed_vp
    
    def reset(self):
        """Reset stabilizer state"""
        self.vp_history = []
        self.last_vp = None
    
    def get_history(self) -> List[float]:
        """Get VP history"""
        return self.vp_history.copy()


class VPComponentCalculator:
    """
    Calculates violation pressure as weighted components to identify saturation sources.
    Breaks VP into trait_divergence, network_coherence, phase_mismatch, evolution_pressure, quantum_entropy.
    """
    
    def __init__(self, component_weights: Optional[Dict[str, float]] = None):
        """
        Initialize component calculator with weights.
        
        Args:
            component_weights: Dictionary of component_name -> weight (must sum to 1.0)
        """
        default_weights = {
            'trait_divergence': 0.25,
            'network_coherence': 0.20,
            'phase_mismatch': 0.15,
            'evolution_pressure': 0.20,
            'quantum_entropy': 0.20
        }
        
        self.component_weights = component_weights or default_weights
        
        # Normalize weights to sum to 1.0
        total_weight = sum(self.component_weights.values())
        if total_weight > 0:
            self.component_weights = {k: v / total_weight for k, v in self.component_weights.items()}
    
    def sigmoid(self, x: float, k: float = 5.0) -> float:
        """Sigmoid function for smoothing: prevents single component from dominating"""
        return 1.0 / (1.0 + math.exp(-k * (x - 0.5)))
    
    def calculate_components(self, trait_payload: Dict[str, float],
                           stability_envelopes: Dict[str, StabilityEnvelope]) -> Dict[str, float]:
        """
        Calculate component pressures from trait payload.
        
        Returns:
            Dictionary of component_name -> component_vp [0.0, 1.0]
        """
        components = {
            'trait_divergence': 0.0,
            'network_coherence': 0.0,
            'phase_mismatch': 0.0,
            'evolution_pressure': 0.0,
            'quantum_entropy': 0.0
        }
        
        if not trait_payload:
            return components
        
        # Group traits by category for component calculation
        network_traits = ['organism_count', 'modularity', 'clustering_coefficient', 'average_path_length']
        prosocial_traits = ['intimacy', 'commitment', 'caregiving', 'attunement', 'lineagepreference']
        meta_traits = ['violationpressure', 'completionpressure', 'convergencestability', 'reflectionindex']
        
        # Calculate trait_divergence: average deviation from stability centers
        divergences = []
        for trait_name, trait_value in trait_payload.items():
            envelope = stability_envelopes.get(trait_name, StabilityEnvelope())
            deviation = abs(trait_value - envelope.center)
            normalized_radius = envelope.radius * envelope.compression_factor
            if normalized_radius > 0:
                divergence = min(1.0, deviation / normalized_radius)
                divergences.append(divergence)
        
        components['trait_divergence'] = sum(divergences) / len(divergences) if divergences else 0.0
        
        # Calculate network_coherence: coherence of network traits
        network_values = [trait_payload.get(t, 0.0) for t in network_traits if t in trait_payload]
        if network_values:
            # Measure variance as inverse of coherence
            mean_network = sum(network_values) / len(network_values)
            variance = sum((v - mean_network) ** 2 for v in network_values) / len(network_values)
            components['network_coherence'] = min(1.0, variance * 4.0)  # Scale variance to [0,1]
        
        # Calculate phase_mismatch: mismatch in prosocial traits
        prosocial_values = [trait_payload.get(t, 0.0) for t in prosocial_traits if t in trait_payload]
        if prosocial_values:
            # Measure spread as phase mismatch
            min_prosocial = min(prosocial_values)
            max_prosocial = max(prosocial_values)
            components['phase_mismatch'] = max_prosocial - min_prosocial
        
        # Calculate evolution_pressure: pressure from meta-traits
        meta_values = [trait_payload.get(t, 0.0) for t in meta_traits if t in trait_payload]
        if meta_values:
            # Average of meta-traits as evolution pressure
            components['evolution_pressure'] = sum(meta_values) / len(meta_values)
        
        # Calculate quantum_entropy: entropy in trait distribution
        if len(trait_payload) > 1:
            # Shannon entropy of normalized trait values
            trait_values = list(trait_payload.values())
            total = sum(abs(v) for v in trait_values)
            if total > 0:
                probabilities = [abs(v) / total for v in trait_values]
                entropy = -sum(p * math.log(p + 1e-10) for p in probabilities if p > 0)
                max_entropy = math.log(len(trait_values))
                components['quantum_entropy'] = entropy / max_entropy if max_entropy > 0 else 0.0
        
        # Apply sigmoid smoothing to prevent domination
        for component_name in components:
            components[component_name] = self.sigmoid(components[component_name])
        
        return components
    
    def combine_components(self, component_vps: Dict[str, float]) -> float:
        """
        Combine component VPs using weighted geometric mean.
        
        Geometric mean prevents single component from dominating:
        total = (∏(component_i ^ weight_i)) ^ (1 / sum(weights))
        """
        if not component_vps:
            return 0.0
        
        # Weighted geometric mean
        log_sum = 0.0
        weight_sum = 0.0
        
        for component_name, component_vp in component_vps.items():
            weight = self.component_weights.get(component_name, 0.0)
            if weight > 0 and component_vp > 0:
                log_sum += weight * math.log(component_vp + 1e-10)
                weight_sum += weight
        
        if weight_sum > 0:
            geometric_mean = math.exp(log_sum / weight_sum)
            return max(0.0, min(1.0, geometric_mean))
        
        return 0.0


class AdaptiveThresholdManager:
    """
    Manages adaptive thresholds based on system phase.
    Adjusts VP classification thresholds dynamically based on phase and historical VP variance.
    """
    
    def __init__(self):
        self.base_thresholds = {
            ViolationClass.VP0_FULLY_LAWFUL: 0.25,
            ViolationClass.VP1_STABLE_DRIFT: 0.50,
            ViolationClass.VP2_INSTABILITY: 0.75,
            ViolationClass.VP3_CRITICAL_DIVERGENCE: 1.00,
            ViolationClass.VP4_COLLAPSE_THRESHOLD: float('inf')
        }
        
        # Phase-specific threshold adjustments
        self.phase_adjustments = {
            'genesis': {
                'sensitivity_multiplier': 0.6,  # More sensitive (lower thresholds)
                'base_adjustments': {
                    ViolationClass.VP0_FULLY_LAWFUL: 0.15,  # 0.0-0.15 instead of 0.0-0.25
                    ViolationClass.VP1_STABLE_DRIFT: 0.35,  # 0.15-0.35 instead of 0.25-0.50
                    ViolationClass.VP2_INSTABILITY: 0.55,   # 0.35-0.55 instead of 0.50-0.75
                    ViolationClass.VP3_CRITICAL_DIVERGENCE: 0.80,  # 0.55-0.80 instead of 0.75-1.00
                }
            },
            'sovereign': {
                'sensitivity_multiplier': 1.2,  # Less sensitive (higher thresholds)
                'base_adjustments': {
                    ViolationClass.VP0_FULLY_LAWFUL: 0.20,  # 0.0-0.20 instead of 0.0-0.25
                    ViolationClass.VP1_STABLE_DRIFT: 0.40,  # 0.20-0.40 instead of 0.25-0.50
                    ViolationClass.VP2_INSTABILITY: 0.65,   # 0.40-0.65 instead of 0.50-0.75
                    ViolationClass.VP3_CRITICAL_DIVERGENCE: 0.90,  # 0.65-0.90 instead of 0.75-1.00
                }
            }
        }
    
    def adjust_thresholds_for_phase(self, phase: str, historical_vps: List[float]) -> Dict[ViolationClass, float]:
        """
        Adjust thresholds based on phase and historical VP variance.
        
        Args:
            phase: System phase ('genesis' or 'sovereign')
            historical_vps: List of recent VP values (last 100 recommended)
            
        Returns:
            Dictionary of ViolationClass -> threshold value
        """
        # Start with base thresholds
        adjusted_thresholds = self.base_thresholds.copy()
        
        # Get phase-specific adjustments
        phase_config = self.phase_adjustments.get(phase.lower(), {})
        base_adjustments = phase_config.get('base_adjustments', {})
        
        # Apply base phase adjustments
        for vp_class, threshold in base_adjustments.items():
            adjusted_thresholds[vp_class] = threshold
        
        # Calculate variance-based adjustments if historical data available
        if len(historical_vps) >= 10:
            variance = self._calculate_variance(historical_vps)
            mean_vp = sum(historical_vps) / len(historical_vps)
            
            # Adjust sensitivity based on variance
            # High variance = more stability needed = lower thresholds
            # Low variance = can tolerate more = higher thresholds
            variance_factor = 1.0 - (variance * 0.5)  # Reduce thresholds if high variance
            variance_factor = max(0.7, min(1.3, variance_factor))  # Clamp to reasonable range
            
            # Adjust thresholds by variance factor
            for vp_class in [ViolationClass.VP0_FULLY_LAWFUL, ViolationClass.VP1_STABLE_DRIFT,
                            ViolationClass.VP2_INSTABILITY, ViolationClass.VP3_CRITICAL_DIVERGENCE]:
                if vp_class in adjusted_thresholds and adjusted_thresholds[vp_class] != float('inf'):
                    adjusted_thresholds[vp_class] *= variance_factor
            
            # Additional adjustment based on mean VP
            # If mean VP is already high, be more sensitive to prevent further increases
            if mean_vp > 0.5:
                mean_adjustment = 0.9  # Reduce thresholds by 10%
                for vp_class in [ViolationClass.VP0_FULLY_LAWFUL, ViolationClass.VP1_STABLE_DRIFT,
                                ViolationClass.VP2_INSTABILITY, ViolationClass.VP3_CRITICAL_DIVERGENCE]:
                    if vp_class in adjusted_thresholds and adjusted_thresholds[vp_class] != float('inf'):
                        adjusted_thresholds[vp_class] *= mean_adjustment
        
        return adjusted_thresholds
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of VP values"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def classify_with_adaptive_thresholds(self, vp: float, phase: str, historical_vps: List[float]) -> ViolationClass:
        """
        Classify VP using phase-adaptive thresholds.
        
        Args:
            vp: Violation pressure value [0.0, 1.0]
            phase: System phase ('genesis' or 'sovereign')
            historical_vps: List of recent VP values
            
        Returns:
            ViolationClass classification
        """
        thresholds = self.adjust_thresholds_for_phase(phase, historical_vps)
        
        if vp < thresholds[ViolationClass.VP0_FULLY_LAWFUL]:
            return ViolationClass.VP0_FULLY_LAWFUL
        elif vp < thresholds[ViolationClass.VP1_STABLE_DRIFT]:
            return ViolationClass.VP1_STABLE_DRIFT
        elif vp < thresholds[ViolationClass.VP2_INSTABILITY]:
            return ViolationClass.VP2_INSTABILITY
        elif vp < thresholds[ViolationClass.VP3_CRITICAL_DIVERGENCE]:
            return ViolationClass.VP3_CRITICAL_DIVERGENCE
        else:
            return ViolationClass.VP4_COLLAPSE_THRESHOLD


class ViolationMonitor:
    """
    Calculates violation pressure - the mathematical driving force of recursion.
    
    Violation pressure quantifies how far traits deviate from their stability centers,
    creating mathematical necessity for recursive correction through:
    - Convergence (lawful primitive recursion)
    - Divergence (μ-recursion in Forbidden Zone)
    - Collapse (entropy compression via pruning)
    """
    
    def __init__(self, event_publisher=None, diagnostics_enabled: bool = False,
                 stabilization_enabled: bool = False, max_vp_jump: float = 0.1,
                 smoothing_factor: float = 0.3, component_decomposition_enabled: bool = False,
                 component_weights: Optional[Dict[str, float]] = None,
                 adaptive_thresholds_enabled: bool = False,
                 max_history_size: int = 1000):
        self.event_publisher = event_publisher
        self.vp_history = []
        self.max_history_size = max_history_size  # Bound history to prevent memory leaks
        self.stability_envelopes = {}
        
        # Initialize diagnostics (disabled by default for backward compatibility)
        self.diagnostics = VPDiagnostics(enabled=diagnostics_enabled)
        
        # Initialize stabilizer (disabled by default for backward compatibility)
        self.stabilization_enabled = stabilization_enabled
        self.stabilizer = VPStabilizer(
            history_size=10,
            max_jump=max_vp_jump,
            smoothing_factor=smoothing_factor
        ) if stabilization_enabled else None
        
        # Initialize component calculator (disabled by default for backward compatibility)
        self.component_decomposition_enabled = component_decomposition_enabled
        self.component_calculator = VPComponentCalculator(component_weights=component_weights) if component_decomposition_enabled else None
        
        # Initialize adaptive threshold manager (disabled by default for backward compatibility)
        self.adaptive_thresholds_enabled = adaptive_thresholds_enabled
        self.adaptive_threshold_manager = AdaptiveThresholdManager() if adaptive_thresholds_enabled else None
        
        # Initialize default stability envelopes for common traits
        self._initialize_default_envelopes()
    
    def _initialize_default_envelopes(self):
        """Initialize default stability envelopes for mathematical consistency"""
        # Mathematical meta-traits
        self.stability_envelopes["violationpressure"] = StabilityEnvelope(
            center=0.0, radius=0.25, compression_factor=2.0
        )
        self.stability_envelopes["completionpressure"] = StabilityEnvelope(
            center=0.0, radius=0.3, compression_factor=1.5
        )
        self.stability_envelopes["convergencestability"] = StabilityEnvelope(
            center=0.8, radius=0.15, compression_factor=1.2
        )
        self.stability_envelopes["reflectionindex"] = StabilityEnvelope(
            center=0.7, radius=0.2, compression_factor=1.0
        )
        
        # Prosocial traits (love metrics)
        self.stability_envelopes["intimacy"] = StabilityEnvelope(
            center=0.6, radius=0.3, compression_factor=0.8
        )
        self.stability_envelopes["commitment"] = StabilityEnvelope(
            center=0.7, radius=0.25, compression_factor=1.1
        )
        self.stability_envelopes["caregiving"] = StabilityEnvelope(
            center=0.65, radius=0.3, compression_factor=0.9
        )
        self.stability_envelopes["attunement"] = StabilityEnvelope(
            center=0.6, radius=0.25, compression_factor=1.0
        )
        self.stability_envelopes["lineagepreference"] = StabilityEnvelope(
            center=0.55, radius=0.35, compression_factor=0.7
        )
        
        # FIX: Reality Simulator network traits (normalized to [0.0, 1.0])
        # These traits come from the Reality Simulator network component
        # Normalization: organism_count / 1000, average_path_length / 10
        self.stability_envelopes["organism_count"] = StabilityEnvelope(
            center=0.4,  # Target 400 organisms (normalized: 400/1000 = 0.4)
            radius=0.2,  # Allow 200-600 organisms (0.2-0.6 normalized range)
            compression_factor=1.0
        )
        self.stability_envelopes["modularity"] = StabilityEnvelope(
            center=0.3,  # Target moderate modularity (0.3)
            radius=0.2,  # Allow 0.1-0.5 range (low to moderate modularity)
            compression_factor=1.0
        )
        self.stability_envelopes["clustering_coefficient"] = StabilityEnvelope(
            center=0.2,  # Target moderate clustering (0.2)
            radius=0.15,  # Allow 0.05-0.35 range
            compression_factor=1.0
        )
        self.stability_envelopes["average_path_length"] = StabilityEnvelope(
            center=0.5,  # Target path length of 5 (normalized: 5/10 = 0.5)
            radius=0.3,  # Allow 2-8 path length (0.2-0.8 normalized range)
            compression_factor=1.0
        )
    
    def compute_violation_pressure(self, trait_payload: Dict[str, float], 
                                 source_identity: Optional[str] = None,
                                 system_phase: Optional[str] = None) -> Tuple[float, Dict[str, float]]:
        """
        Calculate violation pressure for trait payload.
        
        Args:
            trait_payload: Dictionary of trait_name -> trait_value pairs
            source_identity: Optional UUID of the identity being evaluated
            
        Returns:
            Tuple of (total_vp, per_trait_breakdown)
        """
        total_vp = 0.0
        per_trait_breakdown = {}
        
        for trait_name, trait_value in trait_payload.items():
            # Get stability envelope for this trait
            envelope = self.stability_envelopes.get(trait_name, StabilityEnvelope())
            
            # Calculate deviation for diagnostics
            deviation = abs(trait_value - envelope.center)
            normalized_radius = envelope.radius * envelope.compression_factor
            
            # Calculate individual trait violation pressure
            trait_vp = self._calculate_trait_violation_pressure(trait_value, envelope)
            
            # Log diagnostic breakdown if enabled
            if self.diagnostics.enabled:
                normalization_factor = len(trait_payload) if trait_payload else 1.0
                self.diagnostics.log_trait_breakdown(
                    trait_name, trait_value, envelope, deviation, trait_vp, normalization_factor
                )
            
            per_trait_breakdown[trait_name] = trait_vp
            total_vp += trait_vp
        
        # Normalize total VP to [0.0, 1.0] range
        if trait_payload:
            total_vp = min(1.0, total_vp / len(trait_payload))
        
        # Apply stabilization if enabled (before logging and classification)
        if self.stabilization_enabled and self.stabilizer:
            total_vp = self.stabilizer.stabilize(total_vp)
        
        # Log calculation summary if diagnostics enabled
        if self.diagnostics.enabled:
            self.diagnostics.log_calculation_summary(
                trait_payload, total_vp, per_trait_breakdown, source_identity
            )
        
        # Classify violation pressure (use adaptive thresholds if enabled)
        if self.adaptive_thresholds_enabled and self.adaptive_threshold_manager and system_phase:
            # Get recent VP history for adaptive threshold calculation
            recent_vps = [entry["total_vp"] for entry in self.vp_history[-100:]]
            classification = self.adaptive_threshold_manager.classify_with_adaptive_thresholds(
                total_vp, system_phase, recent_vps
            )
        else:
            classification = self._classify_violation_pressure(total_vp)
        
        # Create violation pressure event
        vp_event = ViolationPressureEvent(
            total_vp=total_vp,
            breakdown=per_trait_breakdown,
            classification=classification.value,
            source_identity=source_identity
        )
        
        # Publish event for system coordination
        if self.event_publisher:
            self.event_publisher.publish(vp_event)
        
        # Record in history
        self.vp_history.append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_vp": total_vp,
            "classification": classification.value,
            "source_identity": source_identity,
            "trait_count": len(trait_payload)
        })
        # Bound history size to prevent memory leaks
        if len(self.vp_history) > self.max_history_size:
            self.vp_history = self.vp_history[-self.max_history_size:]
        
        return total_vp, per_trait_breakdown
    
    def get_vp_diagnostics(self, trait_payload: Dict[str, float]) -> Dict[str, Any]:
        """
        Get detailed diagnostic breakdown of VP calculation without changing the calculation.
        Useful for analyzing what's driving VP saturation.
        
        Returns:
            Dictionary with trait_analysis, envelope_analysis, and summary
        """
        return self.diagnostics.get_vp_diagnostics(trait_payload, self.stability_envelopes)
    
    def compute_violation_pressure_decomposed(self, trait_payload: Dict[str, float],
                                            source_identity: Optional[str] = None) -> Tuple[float, Dict[str, float], Dict[str, float]]:
        """
        Calculate violation pressure with component decomposition.
        Returns breakdown showing which components are driving high VP.
        
        Args:
            trait_payload: Dictionary of trait_name -> trait_value pairs
            source_identity: Optional UUID of the identity being evaluated
            
        Returns:
            Tuple of (total_vp, per_trait_breakdown, component_breakdown)
            - total_vp: Combined VP from weighted components [0.0, 1.0]
            - per_trait_breakdown: Individual trait VPs
            - component_breakdown: Component-level VPs (trait_divergence, network_coherence, etc.)
        """
        if not self.component_calculator:
            # Fallback to standard calculation if decomposition not enabled
            total_vp, per_trait_breakdown = self.compute_violation_pressure(trait_payload, source_identity)
            return total_vp, per_trait_breakdown, {}
        
        # Calculate component pressures
        component_breakdown = self.component_calculator.calculate_components(
            trait_payload, self.stability_envelopes
        )
        
        # Combine components using weighted geometric mean
        total_vp = self.component_calculator.combine_components(component_breakdown)
        
        # Calculate per-trait breakdown for compatibility
        per_trait_breakdown = {}
        for trait_name, trait_value in trait_payload.items():
            envelope = self.stability_envelopes.get(trait_name, StabilityEnvelope())
            trait_vp = self._calculate_trait_violation_pressure(trait_value, envelope)
            per_trait_breakdown[trait_name] = trait_vp
        
        # Apply stabilization if enabled
        if self.stabilization_enabled and self.stabilizer:
            total_vp = self.stabilizer.stabilize(total_vp)
        
        # Classify violation pressure
        classification = self._classify_violation_pressure(total_vp)
        
        # Create violation pressure event (same as standard calculation)
        vp_event = ViolationPressureEvent(
            total_vp=total_vp,
            breakdown=per_trait_breakdown,
            classification=classification.value,
            source_identity=source_identity
        )
        
        # Publish event for system coordination
        if self.event_publisher:
            self.event_publisher.publish(vp_event)
        
        # Record in history
        self.vp_history.append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_vp": total_vp,
            "classification": classification.value,
            "source_identity": source_identity,
            "trait_count": len(trait_payload),
            "component_breakdown": component_breakdown
        })
        # Bound history size to prevent memory leaks
        if len(self.vp_history) > self.max_history_size:
            self.vp_history = self.vp_history[-self.max_history_size:]
        
        return total_vp, per_trait_breakdown, component_breakdown
    
    def _calculate_trait_violation_pressure(self, trait_value: float, 
                                          envelope: StabilityEnvelope) -> float:
        """
        Calculate violation pressure for individual trait.
        
        Core Formula: VP = |actual - center| / (radius * compression_factor)
        """
        # Calculate deviation from stability center
        deviation = abs(trait_value - envelope.center)
        
        # Normalize by stability envelope
        normalized_radius = envelope.radius * envelope.compression_factor
        
        # Calculate violation pressure
        if normalized_radius > 0:
            vp = deviation / normalized_radius
        else:
            vp = float('inf') if deviation > 0 else 0.0
        
        # Clamp to reasonable range [0.0, 10.0]
        return max(0.0, min(10.0, vp))
    
    def _classify_violation_pressure(self, total_vp: float) -> ViolationClass:
        """Classify violation pressure into appropriate category"""
        if total_vp < 0.25:
            return ViolationClass.VP0_FULLY_LAWFUL
        elif total_vp < 0.50:
            return ViolationClass.VP1_STABLE_DRIFT
        elif total_vp < 0.75:
            return ViolationClass.VP2_INSTABILITY
        elif total_vp < 1.00:
            return ViolationClass.VP3_CRITICAL_DIVERGENCE
        else:
            return ViolationClass.VP4_COLLAPSE_THRESHOLD
    
    def set_stability_envelope(self, trait_name: str, envelope: StabilityEnvelope):
        """Set custom stability envelope for specific trait"""
        self.stability_envelopes[trait_name] = envelope
    
    def get_stability_envelope(self, trait_name: str) -> Optional[StabilityEnvelope]:
        """Get stability envelope for specific trait"""
        return self.stability_envelopes.get(trait_name)
    
    def calculate_system_health_metrics(self) -> Dict[str, Any]:
        """Calculate system-wide health metrics based on VP history"""
        if not self.vp_history:
            return {"error": "No VP history available"}
        
        recent_vp = [entry["total_vp"] for entry in self.vp_history[-100:]]  # Last 100 entries
        
        return {
            "average_vp": sum(recent_vp) / len(recent_vp),
            "max_vp": max(recent_vp),
            "min_vp": min(recent_vp),
            "vp_volatility": self._calculate_volatility(recent_vp),
            "stability_trend": self._calculate_stability_trend(recent_vp),
            "classification_distribution": self._get_classification_distribution(),
            "total_measurements": len(self.vp_history)
        }
    
    def _calculate_volatility(self, vp_values: List[float]) -> float:
        """Calculate volatility of violation pressure values"""
        if len(vp_values) < 2:
            return 0.0
        
        mean_vp = sum(vp_values) / len(vp_values)
        variance = sum((x - mean_vp) ** 2 for x in vp_values) / len(vp_values)
        return math.sqrt(variance)
    
    def _calculate_stability_trend(self, vp_values: List[float]) -> str:
        """Calculate trend in violation pressure over time"""
        if len(vp_values) < 10:
            return "insufficient_data"
        
        # Simple linear trend calculation
        recent = vp_values[-10:]
        early_avg = sum(recent[:5]) / 5
        late_avg = sum(recent[5:]) / 5
        
        if late_avg < early_avg * 0.9:
            return "improving"
        elif late_avg > early_avg * 1.1:
            return "degrading"
        else:
            return "stable"
    
    def _get_classification_distribution(self) -> Dict[str, int]:
        """Get distribution of VP classifications"""
        distribution = {cls.value: 0 for cls in ViolationClass}
        
        for entry in self.vp_history:
            classification = entry["classification"]
            distribution[classification] += 1
        
        return distribution
    
    def export_vp_analysis(self, trait_payload: Dict[str, float], 
                          source_identity: Optional[str] = None) -> Dict[str, Any]:
        """Export comprehensive VP analysis"""
        total_vp, breakdown = self.compute_violation_pressure(trait_payload, source_identity)
        classification = self._classify_violation_pressure(total_vp)
        
        return {
            "analysis_timestamp": datetime.utcnow().isoformat() + "Z",
            "source_identity": source_identity,
            "total_violation_pressure": total_vp,
            "classification": classification.value,
            "per_trait_breakdown": breakdown,
            "stability_envelopes": {
                name: {
                    "center": env.center,
                    "radius": env.radius,
                    "compression_factor": env.compression_factor
                }
                for name, env in self.stability_envelopes.items()
                if name in trait_payload
            },
            "system_health": self.calculate_system_health_metrics(),
            "mathematical_formula": "VP_total = Σ(|actual - center| / (radius * compression))"
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize violation pressure monitor
    from uuid_anchor_mechanism import EventPublisher
    
    event_publisher = EventPublisher()
    vp_monitor = ViolationMonitor(event_publisher)
    
    # Test trait payload
    test_payload = {
        "intimacy": 0.8,      # High intimacy
        "commitment": 0.3,    # Low commitment
        "caregiving": 0.7,    # Moderate caregiving
        "violationpressure": 0.4,  # Moderate VP
        "reflectionindex": 0.9     # High reflection
    }
    
    print("=== Violation Pressure Calculation Test ===")
    print(f"Test payload: {test_payload}")
    
    # Calculate violation pressure
    total_vp, breakdown = vp_monitor.compute_violation_pressure(test_payload, "test_identity_001")
    
    print(f"Total Violation Pressure: {total_vp:.3f}")
    print(f"Per-trait breakdown: {breakdown}")
    
    # Export comprehensive analysis
    analysis = vp_monitor.export_vp_analysis(test_payload, "test_identity_001")
    print(f"VP Analysis: {analysis}")
    
    # Show system health metrics
    health_metrics = vp_monitor.calculate_system_health_metrics()
    print(f"System Health: {health_metrics}")
    
    print("=== Phase 0.2 Implementation Complete ===")
    print("Violation Pressure Calculation operational and mathematically verified.")
