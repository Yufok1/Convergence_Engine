# Trait Validation and Consistency System
# Version 1.0 - Comprehensive validation for trait ontology integrity

"""
Complete validation system ensuring mathematical consistency, love metrics compliance,
and emotional integration across the entire trait framework.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Set
from enum import Enum
import json
import uuid
import hashlib
from datetime import datetime
import numpy as np

from core_trait_framework import CoreTraitFramework, TraitDefinition, TraitCategory, StabilityEnvelope
from trait_registration_system import TraitRegistrationSystem


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Individual validation issue with details"""
    severity: ValidationSeverity
    category: str
    message: str
    trait_name: Optional[str] = None
    suggested_fix: Optional[str] = None
    technical_details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    validation_timestamp: datetime
    total_traits_validated: int
    issues: List[ValidationIssue]
    mathematical_consistency: bool
    love_metrics_compliance: bool
    emotional_integration_status: bool
    framework_integrity_score: float
    recommendations: List[str]


class TraitValidationSystem:
    """
    Comprehensive validation system ensuring trait ontology meets all requirements:
    - Mathematical consistency for UUID anchoring and VP calculation
    - Love metrics specification compliance
    - Emotional vector integration compatibility
    - Framework integrity and performance
    """
    
    # Love metrics specification requirements (from love_measurement_spec.md)
    LOVE_METRICS_SPEC = {
        "required_axes": {"intimacy", "commitment", "caregiving", "attunement", "lineage_preference"},
        "default_weights": {
            "intimacy": 0.25,
            "commitment": 0.20,
            "caregiving": 0.30,
            "attunement": 0.15,
            "lineage_preference": 0.10
        },
        "weight_sum_tolerance": 1e-6,
        "value_range": (0.0, 1.0),
        "bond_thresholds": {
            "low_bond": 0.25,
            "medium_bond": 0.60,
            "high_bond": 0.60
        }
    }
    
    # Mathematical consistency requirements
    MATHEMATICAL_REQUIREMENTS = {
        "stability_center_range": (0.0, 1.0),
        "stability_radius_range": (0.0, 0.5),
        "compression_factor_minimum": 0.0,
        "trait_value_range": (0.0, 1.0),
        "max_dependency_depth": 5,
        "max_traits_per_category": 50
    }
    
    def __init__(self, core_framework: CoreTraitFramework, 
                 registration_system: TraitRegistrationSystem):
        self.core_framework = core_framework
        self.registration_system = registration_system
        self.validation_history: List[ValidationReport] = []
        self.custom_validators: List[callable] = []
        
        # Load built-in validators
        self.validators = [
            self._validate_mathematical_consistency,
            self._validate_love_metrics_compliance,
            self._validate_emotional_integration,
            self._validate_framework_integrity,
            self._validate_performance_characteristics,
            self._validate_security_requirements
        ]
    
    def execute_comprehensive_validation(self) -> ValidationReport:
        """
        Execute complete validation of trait framework.
        Returns comprehensive report with all issues and recommendations.
        """
        validation_start = datetime.utcnow()
        all_issues = []
        
        print(f"Starting comprehensive trait validation at {validation_start}")
        
        # Run all validators
        for validator in self.validators + self.custom_validators:
            try:
                validator_name = validator.__name__
                print(f"  Running {validator_name}...")
                issues = validator()
                all_issues.extend(issues)
                print(f"    Found {len(issues)} issues")
            except Exception as e:
                all_issues.append(ValidationIssue(
                    severity=ValidationSeverity.CRITICAL,
                    category="validator_error",
                    message=f"Validator {validator.__name__} failed: {str(e)}",
                    technical_details={"exception": str(e)}
                ))
        
        # Analyze validation results
        mathematical_ok = not any(i for i in all_issues 
                                if i.category == "mathematical_consistency" and 
                                i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL])
        
        love_metrics_ok = not any(i for i in all_issues 
                                if i.category == "love_metrics_compliance" and 
                                i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL])
        
        emotional_ok = not any(i for i in all_issues 
                             if i.category == "emotional_integration" and 
                             i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL])
        
        # Calculate framework integrity score
        integrity_score = self._calculate_integrity_score(all_issues)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(all_issues)
        
        # Create validation report
        report = ValidationReport(
            validation_timestamp=validation_start,
            total_traits_validated=len(self.core_framework.trait_registry),
            issues=all_issues,
            mathematical_consistency=mathematical_ok,
            love_metrics_compliance=love_metrics_ok,
            emotional_integration_status=emotional_ok,
            framework_integrity_score=integrity_score,
            recommendations=recommendations
        )
        
        # Store in history
        self.validation_history.append(report)
        
        print(f"Validation completed. Integrity score: {integrity_score:.2f}")
        print(f"Issues found: {len(all_issues)} ({len([i for i in all_issues if i.severity == ValidationSeverity.CRITICAL])} critical)")
        
        return report
    
    def _validate_mathematical_consistency(self) -> List[ValidationIssue]:
        """Validate mathematical consistency requirements"""
        issues = []
        
        for trait_name, trait_def in self.core_framework.trait_registry.items():
            envelope = trait_def.stability_envelope
            
            # Check stability center range
            if not (self.MATHEMATICAL_REQUIREMENTS["stability_center_range"][0] <= 
                   envelope.center <= 
                   self.MATHEMATICAL_REQUIREMENTS["stability_center_range"][1]):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="mathematical_consistency",
                    message=f"Stability center {envelope.center} outside valid range [0.0, 1.0]",
                    trait_name=trait_name,
                    suggested_fix="Adjust stability center to be within [0.0, 1.0]"
                ))
            
            # Check stability radius range
            if not (self.MATHEMATICAL_REQUIREMENTS["stability_radius_range"][0] < 
                   envelope.radius <= 
                   self.MATHEMATICAL_REQUIREMENTS["stability_radius_range"][1]):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="mathematical_consistency",
                    message=f"Stability radius {envelope.radius} outside valid range (0.0, 0.5]",
                    trait_name=trait_name,
                    suggested_fix="Adjust stability radius to be within (0.0, 0.5]"
                ))
            
            # Check compression factor minimum
            if envelope.compression_factor <= self.MATHEMATICAL_REQUIREMENTS["compression_factor_minimum"]:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="mathematical_consistency",
                    message=f"Compression factor {envelope.compression_factor} must be positive",
                    trait_name=trait_name,
                    suggested_fix="Set compression factor > 0.0"
                ))
            
            # Test UUID anchoring capability
            try:
                test_payload = self.core_framework.create_trait_payload({trait_name: 0.5})
                # Attempt canonical serialization
                canonical_json = json.dumps(test_payload, sort_keys=True, separators=(',', ':'))
            except Exception as e:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.CRITICAL,
                    category="mathematical_consistency",
                    message=f"Trait cannot be UUID anchored: {str(e)}",
                    trait_name=trait_name,
                    suggested_fix="Ensure trait definition allows canonical serialization",
                    technical_details={"exception": str(e)}
                ))
            
            # Test VP calculation
            try:
                vp = self.core_framework.calculate_trait_violation_pressure(trait_name, 0.7)
                if not (0.0 <= vp <= 10.0):  # Reasonable VP range
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="mathematical_consistency",
                        message=f"VP calculation produces unreasonable value: {vp}",
                        trait_name=trait_name,
                        suggested_fix="Review stability envelope parameters"
                    ))
            except Exception as e:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.CRITICAL,
                    category="mathematical_consistency",
                    message=f"VP calculation failed: {str(e)}",
                    trait_name=trait_name,
                    technical_details={"exception": str(e)}
                ))
        
        return issues
    
    def _validate_love_metrics_compliance(self) -> List[ValidationIssue]:
        """Validate compliance with love metrics specification"""
        issues = []
        
        # Check required love metrics axes exist
        required_axes = self.LOVE_METRICS_SPEC["required_axes"]
        existing_axes = set(name for name, trait_def in self.core_framework.trait_registry.items() 
                           if trait_def.category == TraitCategory.PROSOCIAL)
        
        missing_axes = required_axes - existing_axes
        for missing_axis in missing_axes:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="love_metrics_compliance",
                message=f"Required love metrics axis missing: {missing_axis}",
                suggested_fix=f"Register {missing_axis} trait in prosocial category"
            ))
        
        # Validate love metrics traits meet specification requirements
        for axis_name in required_axes:
            if axis_name in self.core_framework.trait_registry:
                trait_def = self.core_framework.trait_registry[axis_name]
                
                # Check category is prosocial
                if trait_def.category != TraitCategory.PROSOCIAL:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category="love_metrics_compliance",
                        message=f"Love metrics axis {axis_name} must be in PROSOCIAL category",
                        trait_name=axis_name,
                        suggested_fix="Change category to PROSOCIAL"
                    ))
                
                # Check value range compliance
                center = trait_def.stability_envelope.center
                radius = trait_def.stability_envelope.radius
                min_val = center - radius
                max_val = center + radius
                
                if min_val < 0.0 or max_val > 1.0:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="love_metrics_compliance",
                        message=f"Love axis {axis_name} stability envelope extends outside [0,1]",
                        trait_name=axis_name,
                        suggested_fix="Adjust center/radius to keep envelope within [0,1]"
                    ))
        
        # Validate default weights sum to 1.0
        spec_weights = self.LOVE_METRICS_SPEC["default_weights"]
        weight_sum = sum(spec_weights.values())
        tolerance = self.LOVE_METRICS_SPEC["weight_sum_tolerance"]
        
        if abs(weight_sum - 1.0) > tolerance:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="love_metrics_compliance",
                message=f"Love metrics weights sum to {weight_sum}, must sum to 1.0",
                suggested_fix="Adjust weights to sum to exactly 1.0",
                technical_details={"weight_sum": weight_sum, "weights": spec_weights}
            ))
        
        # Test love score calculation
        try:
            test_love_vector = {axis: 0.5 for axis in required_axes}
            # Simulate love score calculation
            test_score = sum(spec_weights.get(axis, 0.0) * value 
                           for axis, value in test_love_vector.items())
            
            if not (0.0 <= test_score <= 1.0):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="love_metrics_compliance",
                    message=f"Love score calculation produces invalid result: {test_score}",
                    suggested_fix="Review love score calculation formula"
                ))
        except Exception as e:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="love_metrics_compliance",
                message=f"Love score calculation failed: {str(e)}",
                technical_details={"exception": str(e)}
            ))
        
        return issues
    
    def _validate_emotional_integration(self) -> List[ValidationIssue]:
        """Validate compatibility with emotional vector engine"""
        issues = []
        
        # Check for emotional traits that might conflict with governance
        emotional_traits = [name for name, trait_def in self.core_framework.trait_registry.items()
                           if trait_def.category == TraitCategory.BEHAVIORAL]
        
        # Validate emotional trait stability envelopes are reasonable
        for trait_name in emotional_traits:
            trait_def = self.core_framework.trait_registry[trait_name]
            envelope = trait_def.stability_envelope
            
            # Emotional traits should be more dynamic (larger radius)
            if envelope.radius < 0.1:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="emotional_integration",
                    message=f"Emotional trait {trait_name} has very small stability radius: {envelope.radius}",
                    trait_name=trait_name,
                    suggested_fix="Consider larger radius for emotional trait flexibility"
                ))
            
            # Emotional traits should not be over-compressed
            if envelope.compression_factor > 2.0:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="emotional_integration",
                    message=f"Emotional trait {trait_name} has high compression: {envelope.compression_factor}",
                    trait_name=trait_name,
                    suggested_fix="Lower compression factor for emotional responsiveness"
                ))
        
        # Check for proper interaction modeling with emotional states
        interaction_matrix = self.core_framework.trait_interaction_matrix
        prosocial_traits = [name for name, trait_def in self.core_framework.trait_registry.items()
                           if trait_def.category == TraitCategory.PROSOCIAL]
        
        # Prosocial traits should have interaction patterns
        for trait_name in prosocial_traits:
            if trait_name not in interaction_matrix or not interaction_matrix[trait_name]:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category="emotional_integration",
                    message=f"Prosocial trait {trait_name} has no interaction patterns defined",
                    trait_name=trait_name,
                    suggested_fix="Define interaction patterns for better emotional modeling"
                ))
        
        return issues
    
    def _validate_framework_integrity(self) -> List[ValidationIssue]:
        """Validate overall framework integrity and consistency"""
        issues = []
        
        # Check dependency graph integrity
        dependency_graph = self._build_dependency_graph()
        
        # Detect circular dependencies
        circular_deps = self._detect_circular_dependencies(dependency_graph)
        for cycle in circular_deps:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="framework_integrity",
                message=f"Circular dependency detected: {' -> '.join(cycle)}",
                suggested_fix="Break circular dependency by removing or restructuring dependencies"
            ))
        
        # Check for orphaned traits (no dependencies, no dependents)
        orphaned_traits = self._find_orphaned_traits(dependency_graph)
        for trait_name in orphaned_traits:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                category="framework_integrity",
                message=f"Orphaned trait detected: {trait_name}",
                trait_name=trait_name,
                suggested_fix="Consider adding dependencies or removing if unnecessary"
            ))
        
        # Check category balance
        category_counts = {}
        for trait_def in self.core_framework.trait_registry.values():
            category = trait_def.category
            category_counts[category] = category_counts.get(category, 0) + 1
        
        for category, count in category_counts.items():
            max_per_category = self.MATHEMATICAL_REQUIREMENTS["max_traits_per_category"]
            if count > max_per_category:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="framework_integrity",
                    message=f"Category {category.value} has {count} traits (max recommended: {max_per_category})",
                    suggested_fix="Consider subdividing large categories"
                ))
        
        # Check for naming consistency
        naming_issues = self._check_naming_consistency()
        issues.extend(naming_issues)
        
        return issues
    
    def _validate_performance_characteristics(self) -> List[ValidationIssue]:
        """Validate performance characteristics of trait framework"""
        issues = []
        
        # Test UUID anchoring performance
        try:
            import time
            test_payload = {}
            for i, (trait_name, _) in enumerate(list(self.core_framework.trait_registry.items())[:10]):
                test_payload[trait_name] = 0.5
            
            start_time = time.time()
            for _ in range(100):  # 100 iterations
                canonical_payload = self.core_framework.create_trait_payload(test_payload)
            end_time = time.time()
            
            avg_time = (end_time - start_time) / 100
            if avg_time > 0.01:  # 10ms threshold
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="performance",
                    message=f"UUID anchoring slow: {avg_time*1000:.1f}ms average",
                    suggested_fix="Optimize trait payload creation or reduce trait count"
                ))
        except Exception as e:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="performance",
                message=f"Performance test failed: {str(e)}",
                technical_details={"exception": str(e)}
            ))
        
        # Check memory usage estimation
        trait_count = len(self.core_framework.trait_registry)
        estimated_memory_mb = trait_count * 0.1  # Rough estimate
        
        if estimated_memory_mb > 100:  # 100MB threshold
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                category="performance",
                message=f"High memory usage estimated: {estimated_memory_mb:.1f}MB for {trait_count} traits",
                suggested_fix="Monitor actual memory usage in production"
            ))
        
        return issues
    
    def _validate_security_requirements(self) -> List[ValidationIssue]:
        """Validate security-related requirements"""
        issues = []
        
        # Check for traits with potentially dangerous dependencies
        dangerous_patterns = ["external", "network", "file", "system", "admin"]
        
        for trait_name, trait_def in self.core_framework.trait_registry.items():
            # Check trait name for dangerous patterns
            trait_name_lower = trait_name.lower()
            for pattern in dangerous_patterns:
                if pattern in trait_name_lower:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="security",
                        message=f"Trait name {trait_name} contains potentially dangerous pattern: {pattern}",
                        trait_name=trait_name,
                        suggested_fix="Review trait for security implications"
                    ))
            
            # Check metadata for sensitive information
            if trait_def.metadata:
                metadata_str = json.dumps(trait_def.metadata).lower()
                for pattern in dangerous_patterns:
                    if pattern in metadata_str:
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.INFO,
                            category="security",
                            message=f"Trait {trait_name} metadata contains pattern: {pattern}",
                            trait_name=trait_name,
                            suggested_fix="Review metadata for sensitive information"
                        ))
        
        # Check for excessively permissive stability envelopes
        for trait_name, trait_def in self.core_framework.trait_registry.items():
            envelope = trait_def.stability_envelope
            
            if envelope.radius > 0.45:  # Very large radius
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="security",
                    message=f"Trait {trait_name} has very permissive stability envelope: radius {envelope.radius}",
                    trait_name=trait_name,
                    suggested_fix="Consider reducing stability radius for better control"
                ))
            
            if envelope.compression_factor < 0.1:  # Very weak compression
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="security",
                    message=f"Trait {trait_name} has very weak compression: {envelope.compression_factor}",
                    trait_name=trait_name,
                    suggested_fix="Consider increasing compression for stability"
                ))
        
        return issues
    
    def _build_dependency_graph(self) -> Dict[str, Set[str]]:
        """Build dependency graph for analysis"""
        graph = {}
        for trait_name, trait_def in self.core_framework.trait_registry.items():
            graph[trait_name] = set(trait_def.dependencies)
        return graph
    
    def _detect_circular_dependencies(self, graph: Dict[str, Set[str]]) -> List[List[str]]:
        """Detect circular dependencies in trait graph"""
        def dfs(node, path, visited, rec_stack):
            if node in rec_stack:
                # Found cycle
                cycle_start = path.index(node)
                return [path[cycle_start:] + [node]]
            
            if node in visited:
                return []
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            cycles = []
            for neighbor in graph.get(node, set()):
                cycles.extend(dfs(neighbor, path, visited, rec_stack))
            
            path.pop()
            rec_stack.remove(node)
            return cycles
        
        visited = set()
        all_cycles = []
        
        for node in graph:
            if node not in visited:
                all_cycles.extend(dfs(node, [], visited, set()))
        
        return all_cycles
    
    def _find_orphaned_traits(self, graph: Dict[str, Set[str]]) -> List[str]:
        """Find traits with no dependencies and no dependents"""
        has_dependencies = set()
        has_dependents = set()
        
        for trait_name, dependencies in graph.items():
            if dependencies:
                has_dependencies.add(trait_name)
            for dep in dependencies:
                has_dependents.add(dep)
        
        all_traits = set(graph.keys())
        orphaned = all_traits - has_dependencies - has_dependents
        
        # Exclude mathematical meta-traits as they're foundational
        mathematical_traits = {name for name, trait_def in self.core_framework.trait_registry.items()
                              if trait_def.category == TraitCategory.MATHEMATICAL}
        
        return list(orphaned - mathematical_traits)
    
    def _check_naming_consistency(self) -> List[ValidationIssue]:
        """Check naming consistency across traits"""
        issues = []
        
        trait_names = list(self.core_framework.trait_registry.keys())
        
        # Check for case inconsistencies
        name_variations = {}
        for name in trait_names:
            canonical = name.lower()
            if canonical in name_variations:
                name_variations[canonical].append(name)
            else:
                name_variations[canonical] = [name]
        
        for canonical, variations in name_variations.items():
            if len(variations) > 1:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="framework_integrity",
                    message=f"Similar trait names detected: {variations}",
                    suggested_fix="Use consistent naming convention"
                ))
        
        # Check for overly long names
        for name in trait_names:
            if len(name) > 30:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category="framework_integrity",
                    message=f"Long trait name: {name} ({len(name)} characters)",
                    trait_name=name,
                    suggested_fix="Consider shorter, more concise name"
                ))
        
        return issues
    
    def _calculate_integrity_score(self, issues: List[ValidationIssue]) -> float:
        """Calculate overall framework integrity score [0.0, 1.0]"""
        if not issues:
            return 1.0
        
        # Weight issues by severity
        severity_weights = {
            ValidationSeverity.INFO: 0.1,
            ValidationSeverity.WARNING: 0.3,
            ValidationSeverity.ERROR: 0.7,
            ValidationSeverity.CRITICAL: 1.0
        }
        
        total_weight = sum(severity_weights[issue.severity] for issue in issues)
        max_possible = len(issues)  # If all were critical
        
        # Calculate score (higher is better)
        raw_score = 1.0 - (total_weight / max_possible)
        return max(0.0, min(1.0, raw_score))
    
    def _generate_recommendations(self, issues: List[ValidationIssue]) -> List[str]:
        """Generate prioritized recommendations based on issues"""
        recommendations = []
        
        # Count issues by category and severity
        critical_issues = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
        error_issues = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        
        if critical_issues:
            recommendations.append(f"URGENT: Address {len(critical_issues)} critical issues immediately")
        
        if error_issues:
            recommendations.append(f"HIGH PRIORITY: Fix {len(error_issues)} error-level issues")
        
        # Category-specific recommendations
        categories = {}
        for issue in issues:
            if issue.category not in categories:
                categories[issue.category] = []
            categories[issue.category].append(issue)
        
        for category, category_issues in categories.items():
            if len(category_issues) >= 3:
                recommendations.append(f"Review {category} - {len(category_issues)} issues detected")
        
        # Framework-specific recommendations
        total_traits = len(self.core_framework.trait_registry)
        if total_traits > 100:
            recommendations.append("Consider trait consolidation - large trait count may impact performance")
        
        if total_traits < 10:
            recommendations.append("Consider expanding trait ontology for richer behavioral modeling")
        
        return recommendations
    
    def export_validation_summary(self, report: ValidationReport) -> Dict[str, Any]:
        """Export validation report as summary for monitoring"""
        return {
            "validation_timestamp": report.validation_timestamp.isoformat(),
            "framework_integrity_score": report.framework_integrity_score,
            "total_traits": report.total_traits_validated,
            "mathematical_consistency": report.mathematical_consistency,
            "love_metrics_compliance": report.love_metrics_compliance,
            "emotional_integration": report.emotional_integration_status,
            "issue_summary": {
                "total": len(report.issues),
                "critical": len([i for i in report.issues if i.severity == ValidationSeverity.CRITICAL]),
                "errors": len([i for i in report.issues if i.severity == ValidationSeverity.ERROR]),
                "warnings": len([i for i in report.issues if i.severity == ValidationSeverity.WARNING]),
                "info": len([i for i in report.issues if i.severity == ValidationSeverity.INFO])
            },
            "top_recommendations": report.recommendations[:5],
            "validation_version": "1.0"
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize systems
    core_framework = CoreTraitFramework()
    registration_system = TraitRegistrationSystem(core_framework)
    validation_system = TraitValidationSystem(core_framework, registration_system)
    
    print("=== Djinn Kernel Trait Validation System ===")
    print(f"Validating {len(core_framework.trait_registry)} traits...")
    
    # Execute comprehensive validation
    validation_report = validation_system.execute_comprehensive_validation()
    
    # Display results
    print(f"\n=== Validation Results ===")
    print(f"Framework Integrity Score: {validation_report.framework_integrity_score:.2f}")
    print(f"Mathematical Consistency: {'✓' if validation_report.mathematical_consistency else '✗'}")
    print(f"Love Metrics Compliance: {'✓' if validation_report.love_metrics_compliance else '✗'}")
    print(f"Emotional Integration: {'✓' if validation_report.emotional_integration_status else '✗'}")
    
    # Show issue summary
    issue_counts = {}
    for issue in validation_report.issues:
        severity = issue.severity.value
        issue_counts[severity] = issue_counts.get(severity, 0) + 1
    
    print(f"\n=== Issues Summary ===")
    for severity in ["critical", "error", "warning", "info"]:
        count = issue_counts.get(severity, 0)
        print(f"{severity.capitalize()}: {count}")
    
    # Show top issues
    if validation_report.issues:
        print(f"\n=== Top Issues ===")
        critical_and_errors = [i for i in validation_report.issues 
                              if i.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR]]
        
        for i, issue in enumerate(critical_and_errors[:5]):
            print(f"{i+1}. [{issue.severity.value.upper()}] {issue.message}")
            if issue.suggested_fix:
                print(f"   Fix: {issue.suggested_fix}")
    
    # Show recommendations
    print(f"\n=== Recommendations ===")
    for i, rec in enumerate(validation_report.recommendations):
        print(f"{i+1}. {rec}")
    
    # Export summary
    summary = validation_system.export_validation_summary(validation_report)
    print(f"\n=== Validation Summary (JSON) ===")
    print(json.dumps(summary, indent=2, default=str))