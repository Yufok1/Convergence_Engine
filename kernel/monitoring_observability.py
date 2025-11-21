"""
Monitoring and Observability - Phase 5.3 Implementation

This module implements the comprehensive monitoring systems that serve as the Djinn Kernel's
real-time sensory apparatus. It provides tracking of Golden Signals, real-time calculation
of the Reflection Index, and predictive alerting for insight into the health and stability
of the living sovereign civilization.

Key Features:
- Golden Signals monitoring (Latency, Traffic, Errors, Saturation)
- Reflection Index real-time calculation and tracking
- Predictive alerting and anomaly detection
- System health dashboards and metrics collection
- Performance monitoring and resource utilization tracking
- Sovereign stability monitoring and early warning systems
"""

import time
import math
import hashlib
import threading
import asyncio
import json
import statistics
from typing import Dict, List, Any, Optional, Tuple, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime, timedelta
from collections import defaultdict, deque
import heapq

from deployment_procedures import DeploymentOrchestrator, DeploymentStatus
from infrastructure_architecture import InfrastructureArchitecture, DeploymentEnvironment
from policy_safety_systems import PolicySafetyManager, SafetyLevel
from enhanced_synchrony_protocol import EnhancedSynchronyProtocol
from instruction_interpretation_layer import InstructionInterpretationLayer
from codex_amendment_system import CodexAmendmentSystem
from arbitration_stack import ProductionArbitrationStack
from synchrony_phase_lock_protocol import ProductionSynchronySystem
from advanced_trait_engine import AdvancedTraitEngine
from utm_kernel_design import UTMKernel
from event_driven_coordination import DjinnEventBus
from violation_pressure_calculation import ViolationMonitor


class MetricType(Enum):
    """Types of metrics collected"""
    GOLDEN_SIGNAL = "golden_signal"          # Core golden signals
    REFLECTION_INDEX = "reflection_index"    # Reflection index metrics
    SYSTEM_HEALTH = "system_health"          # System health metrics
    PERFORMANCE = "performance"              # Performance metrics
    RESOURCE_UTILIZATION = "resource_utilization"  # Resource usage
    SOVEREIGN_STABILITY = "sovereign_stability"    # Sovereign stability
    PREDICTIVE = "predictive"                # Predictive metrics
    CUSTOM = "custom"                        # Custom application metrics


class AlertSeverity(Enum):
    """Severity levels for alerts"""
    INFO = "info"                            # Informational
    WARNING = "warning"                      # Warning condition
    CRITICAL = "critical"                    # Critical condition
    EMERGENCY = "emergency"                  # Emergency requiring immediate action


class AlertStatus(Enum):
    """Status of alerts"""
    ACTIVE = "active"                        # Alert is active
    ACKNOWLEDGED = "acknowledged"            # Alert acknowledged
    RESOLVED = "resolved"                    # Alert resolved
    SUPPRESSED = "suppressed"                # Alert suppressed


class MonitoringLevel(Enum):
    """Monitoring detail levels"""
    BASIC = "basic"                          # Basic monitoring
    STANDARD = "standard"                    # Standard monitoring
    DETAILED = "detailed"                    # Detailed monitoring
    VERBOSE = "verbose"                      # Verbose monitoring
    DEBUG = "debug"                          # Debug level monitoring


@dataclass
class GoldenSignals:
    """Core golden signals for system monitoring"""
    latency_p50: float = 0.0                # 50th percentile latency (ms)
    latency_p95: float = 0.0                # 95th percentile latency (ms)
    latency_p99: float = 0.0                # 99th percentile latency (ms)
    traffic_rate: float = 0.0               # Requests per second
    error_rate: float = 0.0                 # Error rate percentage
    saturation_cpu: float = 0.0             # CPU saturation percentage
    saturation_memory: float = 0.0          # Memory saturation percentage
    saturation_storage: float = 0.0         # Storage saturation percentage
    saturation_network: float = 0.0         # Network saturation percentage
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ReflectionIndex:
    """Real-time reflection index calculation"""
    stability_score: float = 1.0            # System stability score (0-1)
    coherence_score: float = 1.0            # System coherence score (0-1)
    sovereignty_score: float = 1.0          # Sovereignty integrity score (0-1)
    evolution_rate: float = 0.0             # Rate of lawful evolution
    emergence_factor: float = 0.0           # Emergence complexity factor
    convergence_index: float = 1.0          # Trait convergence index
    violation_pressure: float = 0.0         # Current violation pressure
    entropy_level: float = 0.0              # System entropy level
    composite_index: float = 1.0            # Composite reflection index
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SystemHealthMetrics:
    """System health and performance metrics"""
    uptime_seconds: float = 0.0             # System uptime in seconds
    component_health: Dict[str, float] = field(default_factory=dict)  # Component health scores
    service_availability: Dict[str, float] = field(default_factory=dict)  # Service availability
    resource_utilization: Dict[str, float] = field(default_factory=dict)  # Resource usage
    throughput_metrics: Dict[str, float] = field(default_factory=dict)    # Throughput metrics
    response_times: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))  # Response times
    error_counts: Dict[str, int] = field(default_factory=dict)  # Error counts
    warning_counts: Dict[str, int] = field(default_factory=dict)  # Warning counts
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Alert:
    """System alert definition"""
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    severity: AlertSeverity = AlertSeverity.INFO
    status: AlertStatus = AlertStatus.ACTIVE
    metric_type: MetricType = MetricType.SYSTEM_HEALTH
    threshold_value: float = 0.0
    current_value: float = 0.0
    component: str = ""
    service: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    escalation_count: int = 0
    suppression_duration: Optional[timedelta] = None


@dataclass
class MetricThreshold:
    """Metric threshold configuration"""
    metric_name: str = ""
    metric_type: MetricType = MetricType.SYSTEM_HEALTH
    warning_threshold: float = 0.0
    critical_threshold: float = 0.0
    emergency_threshold: float = 0.0
    comparison_operator: str = ">"           # >, <, >=, <=, ==, !=
    window_duration: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    evaluation_frequency: timedelta = field(default_factory=lambda: timedelta(seconds=30))
    enabled: bool = True


@dataclass
class Dashboard:
    """Monitoring dashboard configuration"""
    dashboard_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    panels: List[Dict[str, Any]] = field(default_factory=list)
    refresh_interval: timedelta = field(default_factory=lambda: timedelta(seconds=30))
    time_range: timedelta = field(default_factory=lambda: timedelta(hours=1))
    auto_refresh: bool = True
    public: bool = False
    tags: List[str] = field(default_factory=list)


class GoldenSignalsCollector:
    """Collector for Golden Signals metrics"""
    
    def __init__(self, collection_interval: timedelta = timedelta(seconds=10)):
        self.collection_interval = collection_interval
        self.signals_history: deque = deque(maxlen=1000)
        self.current_signals = GoldenSignals()
        self.latency_samples: deque = deque(maxlen=1000)
        self.traffic_samples: deque = deque(maxlen=100)
        self.error_samples: deque = deque(maxlen=100)
        self.saturation_samples: Dict[str, deque] = {
            'cpu': deque(maxlen=100),
            'memory': deque(maxlen=100),
            'storage': deque(maxlen=100),
            'network': deque(maxlen=100)
        }
        
        self.collecting = True
        self.collector_thread = threading.Thread(target=self._collect_signals, daemon=True)
        self.collector_thread.start()
    
    def record_latency(self, latency_ms: float) -> None:
        """Record a latency sample"""
        self.latency_samples.append(latency_ms)
    
    def record_request(self) -> None:
        """Record a request for traffic calculation"""
        current_time = time.time()
        self.traffic_samples.append(current_time)
    
    def record_error(self) -> None:
        """Record an error for error rate calculation"""
        current_time = time.time()
        self.error_samples.append(current_time)
    
    def record_saturation(self, resource_type: str, saturation_percent: float) -> None:
        """Record resource saturation"""
        if resource_type in self.saturation_samples:
            self.saturation_samples[resource_type].append(saturation_percent)
    
    def _collect_signals(self) -> None:
        """Background collection of golden signals"""
        while self.collecting:
            try:
                # Calculate latency percentiles
                if self.latency_samples:
                    sorted_latencies = sorted(self.latency_samples)
                    self.current_signals.latency_p50 = self._percentile(sorted_latencies, 50)
                    self.current_signals.latency_p95 = self._percentile(sorted_latencies, 95)
                    self.current_signals.latency_p99 = self._percentile(sorted_latencies, 99)
                
                # Calculate traffic rate (requests per second)
                current_time = time.time()
                recent_requests = [t for t in self.traffic_samples if current_time - t <= 60]
                self.current_signals.traffic_rate = len(recent_requests) / 60.0
                
                # Calculate error rate
                recent_errors = [t for t in self.error_samples if current_time - t <= 60]
                recent_total = len(recent_requests)
                if recent_total > 0:
                    self.current_signals.error_rate = (len(recent_errors) / recent_total) * 100
                else:
                    self.current_signals.error_rate = 0.0
                
                # Calculate saturation averages
                if self.saturation_samples['cpu']:
                    self.current_signals.saturation_cpu = statistics.mean(self.saturation_samples['cpu'])
                if self.saturation_samples['memory']:
                    self.current_signals.saturation_memory = statistics.mean(self.saturation_samples['memory'])
                if self.saturation_samples['storage']:
                    self.current_signals.saturation_storage = statistics.mean(self.saturation_samples['storage'])
                if self.saturation_samples['network']:
                    self.current_signals.saturation_network = statistics.mean(self.saturation_samples['network'])
                
                # Update timestamp and add to history
                self.current_signals.timestamp = datetime.utcnow()
                self.signals_history.append(self.current_signals)
                
                time.sleep(self.collection_interval.total_seconds())
                
            except Exception as e:
                print(f"Golden signals collection error: {e}")
                time.sleep(5)
    
    def _percentile(self, sorted_data: List[float], percentile: int) -> float:
        """Calculate percentile from sorted data"""
        if not sorted_data:
            return 0.0
        
        index = (percentile / 100.0) * (len(sorted_data) - 1)
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def get_current_signals(self) -> GoldenSignals:
        """Get current golden signals"""
        return self.current_signals
    
    def get_signals_history(self, duration: timedelta = timedelta(hours=1)) -> List[GoldenSignals]:
        """Get golden signals history"""
        cutoff_time = datetime.utcnow() - duration
        return [s for s in self.signals_history if s.timestamp >= cutoff_time]


class ReflectionIndexCalculator:
    """Calculator for real-time Reflection Index"""
    
    def __init__(self, calculation_interval: timedelta = timedelta(seconds=30)):
        self.calculation_interval = calculation_interval
        self.index_history: deque = deque(maxlen=1000)
        self.current_index = ReflectionIndex()
        
        # Component references (will be injected)
        self.trait_engine: Optional[AdvancedTraitEngine] = None
        self.arbitration_stack: Optional[ProductionArbitrationStack] = None
        self.synchrony_system: Optional[ProductionSynchronySystem] = None
        self.violation_monitor: Optional[ViolationMonitor] = None
        self.collapsemap_engine: Optional[Any] = None
        
        self.calculating = True
        self.calculator_thread = threading.Thread(target=self._calculate_index, daemon=True)
        self.calculator_thread.start()
    
    def set_component_references(self, trait_engine: AdvancedTraitEngine,
                                arbitration_stack: ProductionArbitrationStack,
                                synchrony_system: ProductionSynchronySystem,
                                violation_monitor: ViolationMonitor,
                                collapsemap_engine: Any) -> None:
        """Set references to core components for index calculation"""
        self.trait_engine = trait_engine
        self.arbitration_stack = arbitration_stack
        self.synchrony_system = synchrony_system
        self.violation_monitor = violation_monitor
        self.collapsemap_engine = collapsemap_engine
    
    def _calculate_index(self) -> None:
        """Background calculation of reflection index"""
        while self.calculating:
            try:
                # Calculate stability score
                self.current_index.stability_score = self._calculate_stability_score()
                
                # Calculate coherence score
                self.current_index.coherence_score = self._calculate_coherence_score()
                
                # Calculate sovereignty score
                self.current_index.sovereignty_score = self._calculate_sovereignty_score()
                
                # Calculate evolution rate
                self.current_index.evolution_rate = self._calculate_evolution_rate()
                
                # Calculate emergence factor
                self.current_index.emergence_factor = self._calculate_emergence_factor()
                
                # Calculate convergence index
                self.current_index.convergence_index = self._calculate_convergence_index()
                
                # Get violation pressure
                self.current_index.violation_pressure = self._get_violation_pressure()
                
                # Calculate entropy level
                self.current_index.entropy_level = self._calculate_entropy_level()
                
                # Calculate composite index
                self.current_index.composite_index = self._calculate_composite_index()
                
                # Update timestamp and add to history
                self.current_index.timestamp = datetime.utcnow()
                self.index_history.append(self.current_index)
                
                time.sleep(self.calculation_interval.total_seconds())
                
            except Exception as e:
                print(f"Reflection index calculation error: {e}")
                time.sleep(10)
    
    def _calculate_stability_score(self) -> float:
        """Calculate system stability score"""
        try:
            # Base stability
            base_stability = 1.0
            
            # Factor in violation pressure
            if self.violation_monitor:
                vp = self.violation_monitor.get_current_violation_pressure()
                base_stability *= max(0.0, 1.0 - (vp / 100.0))
            
            # Factor in synchrony health
            if self.synchrony_system:
                metrics = self.synchrony_system.get_synchrony_metrics()
                if 'temporal_drift_active' in metrics and metrics['temporal_drift_active']:
                    base_stability *= 0.95
            
            return max(0.0, min(1.0, base_stability))
        except Exception:
            return 0.8  # Conservative fallback
    
    def _calculate_coherence_score(self) -> float:
        """Calculate system coherence score"""
        try:
            # Base coherence
            base_coherence = 1.0
            
            # Factor in trait system coherence
            if self.trait_engine:
                # Simplified coherence based on trait system health
                base_coherence = 0.95  # Assume good coherence
            
            return max(0.0, min(1.0, base_coherence))
        except Exception:
            return 0.9  # Conservative fallback
    
    def _calculate_sovereignty_score(self) -> float:
        """Calculate sovereignty integrity score"""
        try:
            # Base sovereignty
            base_sovereignty = 1.0
            
            # Factor in arbitration stack health
            if self.arbitration_stack:
                # Simplified sovereignty based on arbitration health
                base_sovereignty = 0.98  # Assume strong sovereignty
            
            return max(0.0, min(1.0, base_sovereignty))
        except Exception:
            return 0.95  # Conservative fallback
    
    def _calculate_evolution_rate(self) -> float:
        """Calculate rate of lawful evolution"""
        try:
            # Simplified evolution rate calculation
            return 0.02  # 2% evolution rate
        except Exception:
            return 0.0
    
    def _calculate_emergence_factor(self) -> float:
        """Calculate emergence complexity factor"""
        try:
            # Simplified emergence factor
            return 0.15  # 15% emergence factor
        except Exception:
            return 0.0
    
    def _calculate_convergence_index(self) -> float:
        """Calculate trait convergence index"""
        try:
            # Base convergence
            base_convergence = 1.0
            
            if self.trait_engine:
                # Simplified convergence based on trait engine state
                base_convergence = 0.96  # Assume good convergence
            
            return max(0.0, min(1.0, base_convergence))
        except Exception:
            return 0.9  # Conservative fallback
    
    def _get_violation_pressure(self) -> float:
        """Get current violation pressure"""
        try:
            if self.violation_monitor:
                return self.violation_monitor.get_current_violation_pressure()
            return 0.0
        except Exception:
            return 0.0
    
    def _calculate_entropy_level(self) -> float:
        """Calculate system entropy level"""
        try:
            if self.collapsemap_engine:
                # Get entropy from collapse map engine
                metrics = self.collapsemap_engine.get_engine_metrics()
                return metrics.get('total_system_entropy', 0.0)
            return 0.1  # Low baseline entropy
        except Exception:
            return 0.1
    
    def _calculate_composite_index(self) -> float:
        """Calculate composite reflection index"""
        try:
            # Weighted composite calculation
            weights = {
                'stability': 0.3,
                'coherence': 0.2,
                'sovereignty': 0.25,
                'convergence': 0.15,
                'entropy_penalty': 0.1
            }
            
            composite = (
                self.current_index.stability_score * weights['stability'] +
                self.current_index.coherence_score * weights['coherence'] +
                self.current_index.sovereignty_score * weights['sovereignty'] +
                self.current_index.convergence_index * weights['convergence'] -
                self.current_index.entropy_level * weights['entropy_penalty']
            )
            
            return max(0.0, min(1.0, composite))
        except Exception:
            return 0.8  # Conservative fallback
    
    def get_current_index(self) -> ReflectionIndex:
        """Get current reflection index"""
        return self.current_index
    
    def get_index_history(self, duration: timedelta = timedelta(hours=1)) -> List[ReflectionIndex]:
        """Get reflection index history"""
        cutoff_time = datetime.utcnow() - duration
        return [idx for idx in self.index_history if idx.timestamp >= cutoff_time]


class PredictiveAlerting:
    """Predictive alerting and anomaly detection system"""
    
    def __init__(self, evaluation_interval: timedelta = timedelta(seconds=30)):
        self.evaluation_interval = evaluation_interval
        self.thresholds: Dict[str, MetricThreshold] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        
        # Anomaly detection state
        self.metric_baselines: Dict[str, deque] = defaultdict(lambda: deque(maxlen=288))  # 24 hours of 5-min samples
        self.anomaly_scores: Dict[str, float] = {}
        
        self.alerting_active = True
        self.alerting_thread = threading.Thread(target=self._evaluate_alerts, daemon=True)
        self.alerting_thread.start()
    
    def add_threshold(self, threshold: MetricThreshold) -> None:
        """Add a metric threshold"""
        self.thresholds[threshold.metric_name] = threshold
    
    def remove_threshold(self, metric_name: str) -> None:
        """Remove a metric threshold"""
        if metric_name in self.thresholds:
            del self.thresholds[metric_name]
    
    def update_metric_value(self, metric_name: str, value: float, 
                           metric_type: MetricType = MetricType.CUSTOM) -> None:
        """Update a metric value for alerting evaluation"""
        # Store baseline for anomaly detection
        self.metric_baselines[metric_name].append(value)
        
        # Calculate anomaly score
        self._calculate_anomaly_score(metric_name, value)
        
        # Evaluate thresholds
        if metric_name in self.thresholds:
            self._evaluate_threshold(metric_name, value, metric_type)
    
    def _calculate_anomaly_score(self, metric_name: str, current_value: float) -> None:
        """Calculate anomaly score for a metric"""
        baseline = self.metric_baselines[metric_name]
        if len(baseline) < 10:  # Need sufficient history
            self.anomaly_scores[metric_name] = 0.0
            return
        
        try:
            mean_value = statistics.mean(baseline)
            std_value = statistics.stdev(baseline) if len(baseline) > 1 else 0.0
            
            if std_value == 0:
                self.anomaly_scores[metric_name] = 0.0
                return
            
            # Z-score based anomaly detection
            z_score = abs(current_value - mean_value) / std_value
            self.anomaly_scores[metric_name] = min(1.0, z_score / 3.0)  # Normalize to 0-1
            
            # Generate anomaly alert if score is high
            if z_score > 3.0:  # 3 standard deviations
                self._create_anomaly_alert(metric_name, current_value, z_score)
        
        except Exception as e:
            print(f"Anomaly calculation error for {metric_name}: {e}")
            self.anomaly_scores[metric_name] = 0.0
    
    def _evaluate_threshold(self, metric_name: str, value: float, metric_type: MetricType) -> None:
        """Evaluate threshold for a metric"""
        threshold = self.thresholds[metric_name]
        if not threshold.enabled:
            return
        
        severity = None
        if self._compare_value(value, threshold.emergency_threshold, threshold.comparison_operator):
            severity = AlertSeverity.EMERGENCY
        elif self._compare_value(value, threshold.critical_threshold, threshold.comparison_operator):
            severity = AlertSeverity.CRITICAL
        elif self._compare_value(value, threshold.warning_threshold, threshold.comparison_operator):
            severity = AlertSeverity.WARNING
        
        if severity:
            self._create_threshold_alert(metric_name, value, threshold, severity, metric_type)
        else:
            # Check if we should resolve existing alerts
            self._resolve_threshold_alerts(metric_name)
    
    def _compare_value(self, value: float, threshold: float, operator: str) -> bool:
        """Compare value against threshold using operator"""
        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return value == threshold
        elif operator == "!=":
            return value != threshold
        return False
    
    def _create_threshold_alert(self, metric_name: str, value: float, 
                               threshold: MetricThreshold, severity: AlertSeverity,
                               metric_type: MetricType) -> None:
        """Create a threshold-based alert"""
        alert_key = f"threshold_{metric_name}_{severity.value}"
        
        if alert_key in self.active_alerts:
            # Update existing alert
            alert = self.active_alerts[alert_key]
            alert.current_value = value
            alert.escalation_count += 1
        else:
            # Create new alert
            alert = Alert(
                title=f"{metric_name.title()} {severity.value.title()}",
                description=f"Metric {metric_name} has crossed {severity.value} threshold",
                severity=severity,
                metric_type=metric_type,
                threshold_value=getattr(threshold, f"{severity.value}_threshold"),
                current_value=value,
                component="monitoring",
                service="threshold_monitoring",
                tags={"metric": metric_name, "type": "threshold"}
            )
            self.active_alerts[alert_key] = alert
            self.alert_history.append(alert)
    
    def _create_anomaly_alert(self, metric_name: str, value: float, z_score: float) -> None:
        """Create an anomaly detection alert"""
        alert_key = f"anomaly_{metric_name}"
        
        if alert_key not in self.active_alerts:
            alert = Alert(
                title=f"{metric_name.title()} Anomaly Detected",
                description=f"Metric {metric_name} shows anomalous behavior (Z-score: {z_score:.2f})",
                severity=AlertSeverity.WARNING,
                metric_type=MetricType.PREDICTIVE,
                threshold_value=3.0,  # 3 sigma threshold
                current_value=z_score,
                component="monitoring",
                service="anomaly_detection",
                tags={"metric": metric_name, "type": "anomaly", "z_score": str(z_score)}
            )
            self.active_alerts[alert_key] = alert
            self.alert_history.append(alert)
    
    def _resolve_threshold_alerts(self, metric_name: str) -> None:
        """Resolve threshold alerts for a metric"""
        alerts_to_resolve = []
        for alert_key, alert in self.active_alerts.items():
            if alert_key.startswith(f"threshold_{metric_name}_") and alert.status == AlertStatus.ACTIVE:
                alerts_to_resolve.append(alert_key)
        
        for alert_key in alerts_to_resolve:
            alert = self.active_alerts[alert_key]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            del self.active_alerts[alert_key]
    
    def _evaluate_alerts(self) -> None:
        """Background alert evaluation"""
        while self.alerting_active:
            try:
                # Evaluate alert escalations and suppressions
                current_time = datetime.utcnow()
                
                for alert in list(self.active_alerts.values()):
                    # Check for suppression expiry
                    if (alert.suppression_duration and 
                        alert.created_at + alert.suppression_duration <= current_time):
                        alert.suppression_duration = None
                        alert.status = AlertStatus.ACTIVE
                
                time.sleep(self.evaluation_interval.total_seconds())
                
            except Exception as e:
                print(f"Alert evaluation error: {e}")
                time.sleep(10)
    
    def acknowledge_alert(self, alert_id: str, acknowledger: str = "system") -> bool:
        """Acknowledge an alert"""
        for alert in self.active_alerts.values():
            if alert.alert_id == alert_id:
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.utcnow()
                alert.tags["acknowledger"] = acknowledger
                return True
        return False
    
    def suppress_alert(self, alert_id: str, duration: timedelta) -> bool:
        """Suppress an alert for a duration"""
        for alert in self.active_alerts.values():
            if alert.alert_id == alert_id:
                alert.status = AlertStatus.SUPPRESSED
                alert.suppression_duration = duration
                return True
        return False
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get active alerts, optionally filtered by severity"""
        alerts = list(self.active_alerts.values())
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return sorted(alerts, key=lambda a: a.created_at, reverse=True)
    
    def get_alert_history(self, duration: timedelta = timedelta(hours=24)) -> List[Alert]:
        """Get alert history"""
        cutoff_time = datetime.utcnow() - duration
        return [a for a in self.alert_history if a.created_at >= cutoff_time]


class SystemHealthMonitor:
    """System health and performance monitoring"""
    
    def __init__(self, monitoring_interval: timedelta = timedelta(seconds=30)):
        self.monitoring_interval = monitoring_interval
        self.health_history: deque = deque(maxlen=1000)
        self.current_health = SystemHealthMetrics()
        self.start_time = datetime.utcnow()
        
        # Component references
        self.deployment_orchestrator: Optional[DeploymentOrchestrator] = None
        self.infrastructure: Optional[InfrastructureArchitecture] = None
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_health, daemon=True)
        self.monitor_thread.start()
    
    def set_component_references(self, deployment_orchestrator: DeploymentOrchestrator,
                                infrastructure: InfrastructureArchitecture) -> None:
        """Set references to core components"""
        self.deployment_orchestrator = deployment_orchestrator
        self.infrastructure = infrastructure
    
    def record_response_time(self, service: str, response_time_ms: float) -> None:
        """Record response time for a service"""
        self.current_health.response_times[service].append(response_time_ms)
        # Keep only recent samples
        if len(self.current_health.response_times[service]) > 100:
            self.current_health.response_times[service] = self.current_health.response_times[service][-100:]
    
    def record_error(self, component: str) -> None:
        """Record an error for a component"""
        self.current_health.error_counts[component] = self.current_health.error_counts.get(component, 0) + 1
    
    def record_warning(self, component: str) -> None:
        """Record a warning for a component"""
        self.current_health.warning_counts[component] = self.current_health.warning_counts.get(component, 0) + 1
    
    def _monitor_health(self) -> None:
        """Background health monitoring"""
        while self.monitoring_active:
            try:
                # Update uptime
                self.current_health.uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
                
                # Update component health
                self._update_component_health()
                
                # Update service availability
                self._update_service_availability()
                
                # Update resource utilization
                self._update_resource_utilization()
                
                # Update throughput metrics
                self._update_throughput_metrics()
                
                # Update timestamp and add to history
                self.current_health.timestamp = datetime.utcnow()
                self.health_history.append(self.current_health)
                
                time.sleep(self.monitoring_interval.total_seconds())
                
            except Exception as e:
                print(f"Health monitoring error: {e}")
                time.sleep(10)
    
    def _update_component_health(self) -> None:
        """Update component health scores"""
        # Base health scores for core components
        components = [
            "utm_kernel", "trait_engine", "event_bus", "violation_monitor",
            "arbitration_stack", "synchrony_system", "collapsemap_engine",
            "forbidden_zone_manager", "sovereign_imitation", "codex_amendment",
            "instruction_layer", "enhanced_synchrony", "policy_safety"
        ]
        
        for component in components:
            # Calculate health based on error rates
            error_count = self.current_health.error_counts.get(component, 0)
            warning_count = self.current_health.warning_counts.get(component, 0)
            
            # Simple health calculation
            base_health = 1.0
            base_health -= min(0.5, error_count * 0.1)    # Errors reduce health
            base_health -= min(0.2, warning_count * 0.02) # Warnings reduce health slightly
            
            self.current_health.component_health[component] = max(0.0, base_health)
    
    def _update_service_availability(self) -> None:
        """Update service availability metrics"""
        services = [
            "monitoring", "deployment", "arbitration", "synchrony",
            "trait_processing", "instruction_interpretation", "policy_enforcement"
        ]
        
        for service in services:
            # Simplified availability calculation
            error_count = sum(count for comp, count in self.current_health.error_counts.items() 
                            if service in comp)
            availability = max(0.0, 1.0 - min(0.3, error_count * 0.05))
            self.current_health.service_availability[service] = availability
    
    def _update_resource_utilization(self) -> None:
        """Update resource utilization metrics"""
        # Simulated resource utilization
        import random
        self.current_health.resource_utilization.update({
            "cpu_percent": random.uniform(20, 80),
            "memory_percent": random.uniform(30, 70),
            "storage_percent": random.uniform(10, 50),
            "network_utilization": random.uniform(5, 40)
        })
    
    def _update_throughput_metrics(self) -> None:
        """Update throughput metrics"""
        # Simulated throughput metrics
        import random
        self.current_health.throughput_metrics.update({
            "requests_per_second": random.uniform(50, 200),
            "operations_per_second": random.uniform(100, 500),
            "events_per_second": random.uniform(20, 100),
            "convergence_operations_per_minute": random.uniform(5, 20)
        })
    
    def get_current_health(self) -> SystemHealthMetrics:
        """Get current system health"""
        return self.current_health
    
    def get_health_history(self, duration: timedelta = timedelta(hours=1)) -> List[SystemHealthMetrics]:
        """Get system health history"""
        cutoff_time = datetime.utcnow() - duration
        return [h for h in self.health_history if h.timestamp >= cutoff_time]
    
    def get_system_summary(self) -> Dict[str, Any]:
        """Get system health summary"""
        return {
            "uptime_hours": self.current_health.uptime_seconds / 3600,
            "overall_health": statistics.mean(self.current_health.component_health.values()) if self.current_health.component_health else 1.0,
            "average_availability": statistics.mean(self.current_health.service_availability.values()) if self.current_health.service_availability else 1.0,
            "total_errors": sum(self.current_health.error_counts.values()),
            "total_warnings": sum(self.current_health.warning_counts.values()),
            "resource_utilization": self.current_health.resource_utilization,
            "throughput_metrics": self.current_health.throughput_metrics
        }


class MonitoringObservability:
    """Main monitoring and observability system"""
    
    def __init__(self, monitoring_level: MonitoringLevel = MonitoringLevel.STANDARD):
        self.monitoring_level = monitoring_level
        
        # Core monitoring components
        self.golden_signals = GoldenSignalsCollector()
        self.reflection_index = ReflectionIndexCalculator()
        self.predictive_alerting = PredictiveAlerting()
        self.system_health = SystemHealthMonitor()
        
        # Dashboards
        self.dashboards: Dict[str, Dashboard] = {}
        
        # System state
        self.monitoring_active = True
        self.start_time = datetime.utcnow()
        
        # Initialize default thresholds
        self._initialize_default_thresholds()
        
        # Initialize default dashboards
        self._initialize_default_dashboards()
    
    def set_component_references(self, deployment_orchestrator: DeploymentOrchestrator,
                                infrastructure: InfrastructureArchitecture,
                                trait_engine: AdvancedTraitEngine,
                                arbitration_stack: ProductionArbitrationStack,
                                synchrony_system: ProductionSynchronySystem,
                                violation_monitor: ViolationMonitor,
                                collapsemap_engine: Any) -> None:
        """Set references to core system components"""
        
        # Set references for reflection index calculator
        self.reflection_index.set_component_references(
            trait_engine, arbitration_stack, synchrony_system, violation_monitor, collapsemap_engine
        )
        
        # Set references for system health monitor
        self.system_health.set_component_references(deployment_orchestrator, infrastructure)
    
    def _initialize_default_thresholds(self) -> None:
        """Initialize default monitoring thresholds"""
        
        # Golden signals thresholds
        self.predictive_alerting.add_threshold(MetricThreshold(
            metric_name="latency_p95",
            metric_type=MetricType.GOLDEN_SIGNAL,
            warning_threshold=500.0,      # 500ms
            critical_threshold=1000.0,    # 1s
            emergency_threshold=2000.0,   # 2s
            comparison_operator=">"
        ))
        
        self.predictive_alerting.add_threshold(MetricThreshold(
            metric_name="error_rate",
            metric_type=MetricType.GOLDEN_SIGNAL,
            warning_threshold=1.0,        # 1%
            critical_threshold=5.0,       # 5%
            emergency_threshold=10.0,     # 10%
            comparison_operator=">"
        ))
        
        self.predictive_alerting.add_threshold(MetricThreshold(
            metric_name="saturation_cpu",
            metric_type=MetricType.GOLDEN_SIGNAL,
            warning_threshold=70.0,       # 70%
            critical_threshold=85.0,      # 85%
            emergency_threshold=95.0,     # 95%
            comparison_operator=">"
        ))
        
        # Reflection index thresholds
        self.predictive_alerting.add_threshold(MetricThreshold(
            metric_name="stability_score",
            metric_type=MetricType.REFLECTION_INDEX,
            warning_threshold=0.8,        # 80%
            critical_threshold=0.7,       # 70%
            emergency_threshold=0.5,      # 50%
            comparison_operator="<"
        ))
        
        self.predictive_alerting.add_threshold(MetricThreshold(
            metric_name="composite_index",
            metric_type=MetricType.REFLECTION_INDEX,
            warning_threshold=0.85,       # 85%
            critical_threshold=0.75,      # 75%
            emergency_threshold=0.6,      # 60%
            comparison_operator="<"
        ))
        
        self.predictive_alerting.add_threshold(MetricThreshold(
            metric_name="violation_pressure",
            metric_type=MetricType.REFLECTION_INDEX,
            warning_threshold=20.0,       # 20%
            critical_threshold=40.0,      # 40%
            emergency_threshold=60.0,     # 60%
            comparison_operator=">"
        ))
    
    def _initialize_default_dashboards(self) -> None:
        """Initialize default monitoring dashboards"""
        
        # Golden Signals Dashboard
        golden_signals_dashboard = Dashboard(
            name="Golden Signals",
            description="Core golden signals monitoring dashboard",
            panels=[
                {
                    "title": "Latency Percentiles",
                    "type": "line_chart",
                    "metrics": ["latency_p50", "latency_p95", "latency_p99"],
                    "unit": "ms"
                },
                {
                    "title": "Traffic Rate",
                    "type": "line_chart",
                    "metrics": ["traffic_rate"],
                    "unit": "rps"
                },
                {
                    "title": "Error Rate",
                    "type": "line_chart",
                    "metrics": ["error_rate"],
                    "unit": "%"
                },
                {
                    "title": "Resource Saturation",
                    "type": "line_chart",
                    "metrics": ["saturation_cpu", "saturation_memory", "saturation_storage", "saturation_network"],
                    "unit": "%"
                }
            ],
            tags=["golden_signals", "core"]
        )
        self.dashboards[golden_signals_dashboard.dashboard_id] = golden_signals_dashboard
        
        # Reflection Index Dashboard
        reflection_dashboard = Dashboard(
            name="Reflection Index",
            description="Real-time reflection index monitoring",
            panels=[
                {
                    "title": "Composite Reflection Index",
                    "type": "gauge",
                    "metrics": ["composite_index"],
                    "unit": "index"
                },
                {
                    "title": "Core Scores",
                    "type": "line_chart",
                    "metrics": ["stability_score", "coherence_score", "sovereignty_score"],
                    "unit": "score"
                },
                {
                    "title": "Evolution Metrics",
                    "type": "line_chart",
                    "metrics": ["evolution_rate", "emergence_factor", "convergence_index"],
                    "unit": "rate"
                },
                {
                    "title": "System Pressure",
                    "type": "line_chart",
                    "metrics": ["violation_pressure", "entropy_level"],
                    "unit": "pressure"
                }
            ],
            tags=["reflection_index", "sovereignty"]
        )
        self.dashboards[reflection_dashboard.dashboard_id] = reflection_dashboard
        
        # System Health Dashboard
        health_dashboard = Dashboard(
            name="System Health",
            description="Overall system health and performance monitoring",
            panels=[
                {
                    "title": "Component Health",
                    "type": "heatmap",
                    "metrics": ["component_health"],
                    "unit": "health"
                },
                {
                    "title": "Service Availability",
                    "type": "bar_chart",
                    "metrics": ["service_availability"],
                    "unit": "%"
                },
                {
                    "title": "Resource Utilization",
                    "type": "line_chart",
                    "metrics": ["cpu_percent", "memory_percent", "storage_percent"],
                    "unit": "%"
                },
                {
                    "title": "Throughput",
                    "type": "line_chart",
                    "metrics": ["requests_per_second", "operations_per_second"],
                    "unit": "ops"
                }
            ],
            tags=["health", "performance"]
        )
        self.dashboards[health_dashboard.dashboard_id] = health_dashboard
    
    def update_metrics(self) -> None:
        """Update all monitoring metrics"""
        try:
            # Update golden signals in alerting system
            current_signals = self.golden_signals.get_current_signals()
            self.predictive_alerting.update_metric_value("latency_p50", current_signals.latency_p50, MetricType.GOLDEN_SIGNAL)
            self.predictive_alerting.update_metric_value("latency_p95", current_signals.latency_p95, MetricType.GOLDEN_SIGNAL)
            self.predictive_alerting.update_metric_value("latency_p99", current_signals.latency_p99, MetricType.GOLDEN_SIGNAL)
            self.predictive_alerting.update_metric_value("traffic_rate", current_signals.traffic_rate, MetricType.GOLDEN_SIGNAL)
            self.predictive_alerting.update_metric_value("error_rate", current_signals.error_rate, MetricType.GOLDEN_SIGNAL)
            self.predictive_alerting.update_metric_value("saturation_cpu", current_signals.saturation_cpu, MetricType.GOLDEN_SIGNAL)
            self.predictive_alerting.update_metric_value("saturation_memory", current_signals.saturation_memory, MetricType.GOLDEN_SIGNAL)
            self.predictive_alerting.update_metric_value("saturation_storage", current_signals.saturation_storage, MetricType.GOLDEN_SIGNAL)
            self.predictive_alerting.update_metric_value("saturation_network", current_signals.saturation_network, MetricType.GOLDEN_SIGNAL)
            
            # Update reflection index in alerting system
            current_index = self.reflection_index.get_current_index()
            self.predictive_alerting.update_metric_value("stability_score", current_index.stability_score, MetricType.REFLECTION_INDEX)
            self.predictive_alerting.update_metric_value("coherence_score", current_index.coherence_score, MetricType.REFLECTION_INDEX)
            self.predictive_alerting.update_metric_value("sovereignty_score", current_index.sovereignty_score, MetricType.REFLECTION_INDEX)
            self.predictive_alerting.update_metric_value("composite_index", current_index.composite_index, MetricType.REFLECTION_INDEX)
            self.predictive_alerting.update_metric_value("violation_pressure", current_index.violation_pressure, MetricType.REFLECTION_INDEX)
            self.predictive_alerting.update_metric_value("entropy_level", current_index.entropy_level, MetricType.REFLECTION_INDEX)
            
        except Exception as e:
            print(f"Metrics update error: {e}")
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get comprehensive monitoring summary"""
        return {
            "monitoring_level": self.monitoring_level.value,
            "uptime_hours": (datetime.utcnow() - self.start_time).total_seconds() / 3600,
            "golden_signals": {
                "current": self.golden_signals.get_current_signals().__dict__,
                "history_count": len(self.golden_signals.signals_history)
            },
            "reflection_index": {
                "current": self.reflection_index.get_current_index().__dict__,
                "history_count": len(self.reflection_index.index_history)
            },
            "alerting": {
                "active_alerts": len(self.predictive_alerting.get_active_alerts()),
                "total_thresholds": len(self.predictive_alerting.thresholds),
                "alert_history": len(self.predictive_alerting.alert_history)
            },
            "system_health": self.system_health.get_system_summary(),
            "dashboards": {
                "total_dashboards": len(self.dashboards),
                "dashboard_names": [d.name for d in self.dashboards.values()]
            }
        }
    
    def get_dashboard_data(self, dashboard_id: str, time_range: timedelta = timedelta(hours=1)) -> Dict[str, Any]:
        """Get data for a specific dashboard"""
        if dashboard_id not in self.dashboards:
            return {}
        
        dashboard = self.dashboards[dashboard_id]
        
        # Get relevant data based on dashboard type
        data = {
            "dashboard": dashboard.__dict__,
            "timestamp": datetime.utcnow().isoformat(),
            "panels": []
        }
        
        for panel in dashboard.panels:
            panel_data = {
                "title": panel["title"],
                "type": panel["type"],
                "unit": panel.get("unit", ""),
                "data": []
            }
            
            # Get metric data based on panel metrics
            for metric in panel["metrics"]:
                if metric.startswith("latency_") or metric == "traffic_rate" or metric == "error_rate" or metric.startswith("saturation_"):
                    # Golden signals data
                    history = self.golden_signals.get_signals_history(time_range)
                    panel_data["data"].append({
                        "metric": metric,
                        "values": [(h.timestamp.isoformat(), getattr(h, metric, 0)) for h in history]
                    })
                elif metric in ["stability_score", "coherence_score", "sovereignty_score", "composite_index", "violation_pressure", "entropy_level"]:
                    # Reflection index data
                    history = self.reflection_index.get_index_history(time_range)
                    panel_data["data"].append({
                        "metric": metric,
                        "values": [(h.timestamp.isoformat(), getattr(h, metric, 0)) for h in history]
                    })
                elif metric in ["component_health", "service_availability", "cpu_percent", "memory_percent"]:
                    # System health data
                    history = self.system_health.get_health_history(time_range)
                    if metric == "component_health":
                        # Special handling for component health
                        if history:
                            latest_health = history[-1]
                            panel_data["data"].append({
                                "metric": metric,
                                "values": [(comp, health) for comp, health in latest_health.component_health.items()]
                            })
                    elif metric == "service_availability":
                        if history:
                            latest_health = history[-1]
                            panel_data["data"].append({
                                "metric": metric,
                                "values": [(service, avail) for service, avail in latest_health.service_availability.items()]
                            })
                    else:
                        panel_data["data"].append({
                            "metric": metric,
                            "values": [(h.timestamp.isoformat(), h.resource_utilization.get(metric, 0)) for h in history]
                        })
            
            data["panels"].append(panel_data)
        
        return data
    
    def shutdown(self) -> None:
        """Shutdown monitoring system"""
        self.monitoring_active = False
        self.golden_signals.collecting = False
        self.reflection_index.calculating = False
        self.predictive_alerting.alerting_active = False
        self.system_health.monitoring_active = False


# Example usage and testing
if __name__ == "__main__":
    # This would be used in the main kernel initialization
    print("Monitoring and Observability - Phase 5.3 Implementation")
    print("Comprehensive monitoring systems with Golden Signals, Reflection Index, and predictive alerting")
