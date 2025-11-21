# Trait Registration System
# Version 1.0 - Formal pathway for trait ontology evolution

"""
Trait registration system implementing the Codex Amendment process for trait ontology evolution.
Enables lawful expansion of trait vocabulary while maintaining mathematical consistency.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import uuid
import json
import hashlib
from datetime import datetime, timedelta
from core_trait_framework import TraitDefinition, TraitCategory, StabilityEnvelope, CoreTraitFramework


class AmendmentStatus(Enum):
    """Status of trait amendment proposals"""
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    COMPATIBILITY_ANALYSIS = "compatibility_analysis"
    ARBITRATION_REVIEW = "arbitration_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    INTEGRATED = "integrated"


@dataclass
class TraitAmendmentProposal:
    """
    Formal proposal for adding new trait to the ontology.
    Must pass through complete Codex Amendment process.
    """
    proposal_id: str                           # UUID for proposal tracking
    proposed_trait: TraitDefinition           # Trait definition for integration
    proposer_agent_id: str                    # Agent submitting proposal
    justification: str                        # Rationale for trait addition
    compatibility_analysis: Optional[Dict[str, Any]] = None  # Analysis results
    arbitration_notes: List[str] = field(default_factory=list)  # Review comments
    status: AmendmentStatus = AmendmentStatus.PROPOSED
    created_timestamp: datetime = field(default_factory=datetime.utcnow)
    status_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        # Initialize status history
        if not self.status_history:
            self.status_history.append({
                "status": self.status.value,
                "timestamp": self.created_timestamp.isoformat(),
                "agent": self.proposer_agent_id,
                "notes": "Initial proposal submission"
            })


@dataclass
class CompatibilityAnalysisResult:
    """Results of mathematical compatibility analysis"""
    is_compatible: bool
    mathematical_consistency: bool
    naming_conflicts: List[str]
    dependency_issues: List[str]
    stability_envelope_analysis: Dict[str, Any]
    interaction_impact_assessment: Dict[str, float]
    recommendation: str
    detailed_analysis: Dict[str, Any]


class TraitRegistrationSystem:
    """
    Formal system for trait ontology evolution through Codex Amendment process.
    Maintains mathematical sovereignty while enabling lawful expansion.
    """
    
    def __init__(self, core_framework: CoreTraitFramework):
        self.core_framework = core_framework
        self.active_proposals: Dict[str, TraitAmendmentProposal] = {}
        self.proposal_history: List[TraitAmendmentProposal] = []
        self.amendment_ledger: List[Dict[str, Any]] = []
        
        # Analysis functions for compatibility checking
        self.compatibility_analyzers: List[Callable] = [
            self._analyze_mathematical_consistency,
            self._analyze_naming_compatibility,
            self._analyze_dependency_validity,
            self._analyze_stability_envelope_impact,
            self._analyze_interaction_matrix_impact
        ]
        
        # Arbitration council for governance decisions
        self.arbitration_council: List[str] = [
            "djinn_meta_auditor",
            "djinn_kernel_engineer", 
            "djinn_stability_monitor",
            "djinn_trait_specialist"
        ]
    
    def submit_trait_proposal(self, trait_def: TraitDefinition, 
                            proposer_agent_id: str, 
                            justification: str) -> str:
        """
        Submit new trait proposal for amendment process.
        Returns proposal ID for tracking.
        """
        # Generate proposal UUID
        proposal_data = {
            "trait_name": trait_def.name,
            "proposer": proposer_agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "justification_hash": hashlib.sha256(justification.encode()).hexdigest()
        }
        proposal_id = str(uuid.uuid5(
            uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8'),
            json.dumps(proposal_data, sort_keys=True)
        ))
        
        # Create proposal
        proposal = TraitAmendmentProposal(
            proposal_id=proposal_id,
            proposed_trait=trait_def,
            proposer_agent_id=proposer_agent_id,
            justification=justification
        )
        
        # Register proposal
        self.active_proposals[proposal_id] = proposal
        
        # Initiate review process
        self._advance_proposal_status(proposal_id, AmendmentStatus.UNDER_REVIEW,
                                    "djinn_amendment_system", 
                                    "Proposal submitted for review")
        
        return proposal_id
    
    def execute_compatibility_analysis(self, proposal_id: str) -> CompatibilityAnalysisResult:
        """
        Execute comprehensive compatibility analysis for trait proposal.
        Core component of amendment process.
        """
        proposal = self.active_proposals.get(proposal_id)
        if not proposal:
            raise ValueError(f"Unknown proposal: {proposal_id}")
        
        # Update status
        self._advance_proposal_status(proposal_id, AmendmentStatus.COMPATIBILITY_ANALYSIS,
                                    "djinn_compatibility_analyzer",
                                    "Beginning compatibility analysis")
        
        # Run all compatibility analyzers
        analysis_results = {}
        for analyzer in self.compatibility_analyzers:
            analyzer_name = analyzer.__name__
            try:
                result = analyzer(proposal.proposed_trait)
                analysis_results[analyzer_name] = result
            except Exception as e:
                analysis_results[analyzer_name] = {"error": str(e), "passed": False}
        
        # Synthesize overall compatibility assessment
        compatibility_result = self._synthesize_compatibility_analysis(analysis_results)
        
        # Update proposal with analysis
        proposal.compatibility_analysis = {
            "result": compatibility_result,
            "detailed_analysis": analysis_results,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "analyzer_version": "1.0"
        }
        
        # Advance to arbitration if compatible
        if compatibility_result.is_compatible:
            self._advance_proposal_status(proposal_id, AmendmentStatus.ARBITRATION_REVIEW,
                                        "djinn_compatibility_analyzer",
                                        "Analysis passed - forwarding to arbitration")
        else:
            self._advance_proposal_status(proposal_id, AmendmentStatus.REJECTED,
                                        "djinn_compatibility_analyzer", 
                                        f"Analysis failed: {compatibility_result.recommendation}")
        
        return compatibility_result
    
    def _analyze_mathematical_consistency(self, trait_def: TraitDefinition) -> Dict[str, Any]:
        """Analyze mathematical consistency of proposed trait"""
        consistency_checks = {
            "stability_envelope_valid": True,
            "normalization_valid": True,
            "serialization_valid": True,
            "uuid_anchorable": True
        }
        
        try:
            # Check stability envelope mathematics
            envelope = trait_def.stability_envelope
            if not (0.0 <= envelope.center <= 1.0):
                consistency_checks["stability_envelope_valid"] = False
            if not (0.0 < envelope.radius <= 0.5):
                consistency_checks["stability_envelope_valid"] = False
            if envelope.compression_factor <= 0.0:
                consistency_checks["stability_envelope_valid"] = False
            
            # Test UUID anchoring compatibility
            test_payload = self.core_framework.create_trait_payload({trait_def.name: 0.5})
            consistency_checks["uuid_anchorable"] = True
            
            # Test violation pressure calculation
            vp = self.core_framework.calculate_trait_violation_pressure(trait_def.name, 0.7)
            consistency_checks["vp_calculable"] = True
            
        except Exception as e:
            consistency_checks["error"] = str(e)
            consistency_checks["uuid_anchorable"] = False
        
        return {
            "passed": all(v for k, v in consistency_checks.items() if k != "error"),
            "checks": consistency_checks
        }
    
    def _analyze_naming_compatibility(self, trait_def: TraitDefinition) -> Dict[str, Any]:
        """Analyze naming compatibility with existing traits"""
        conflicts = []
        recommendations = []
        
        # Check for exact name conflicts
        if trait_def.name in self.core_framework.trait_registry:
            conflicts.append(f"Exact name conflict: {trait_def.name}")
        
        # Check for similar names that could cause confusion
        existing_names = set(self.core_framework.trait_registry.keys())
        for existing_name in existing_names:
            # Check for substring conflicts
            if trait_def.name in existing_name or existing_name in trait_def.name:
                conflicts.append(f"Substring conflict with: {existing_name}")
            
            # Check for similar spelling (simple Levenshtein-like check)
            if self._names_too_similar(trait_def.name, existing_name):
                recommendations.append(f"Very similar to existing: {existing_name}")
        
        return {
            "passed": len(conflicts) == 0,
            "conflicts": conflicts,
            "recommendations": recommendations
        }
    
    def _analyze_dependency_validity(self, trait_def: TraitDefinition) -> Dict[str, Any]:
        """Analyze dependency chain validity"""
        dependency_issues = []
        circular_dependencies = []
        
        # Check all dependencies exist
        for dep_name in trait_def.dependencies:
            if dep_name not in self.core_framework.trait_registry:
                dependency_issues.append(f"Unknown dependency: {dep_name}")
        
        # Check for potential circular dependencies
        if self._would_create_circular_dependency(trait_def):
            circular_dependencies.append(f"Would create circular dependency chain")
        
        return {
            "passed": len(dependency_issues) == 0 and len(circular_dependencies) == 0,
            "dependency_issues": dependency_issues,
            "circular_dependencies": circular_dependencies
        }
    
    def _analyze_stability_envelope_impact(self, trait_def: TraitDefinition) -> Dict[str, Any]:
        """Analyze impact of stability envelope on system dynamics"""
        envelope = trait_def.stability_envelope
        
        # Analyze envelope parameters relative to existing traits
        existing_envelopes = [t.stability_envelope for t in self.core_framework.trait_registry.values()]
        
        center_analysis = {
            "center": envelope.center,
            "existing_centers": [e.center for e in existing_envelopes],
            "center_conflict_risk": self._assess_center_conflicts(envelope, existing_envelopes)
        }
        
        radius_analysis = {
            "radius": envelope.radius,
            "existing_radii": [e.radius for e in existing_envelopes],
            "radius_harmony": self._assess_radius_harmony(envelope, existing_envelopes)
        }
        
        compression_analysis = {
            "compression_factor": envelope.compression_factor,
            "stability_impact": self._assess_stability_impact(envelope)
        }
        
        return {
            "passed": True,  # Stability analysis is advisory, not blocking
            "center_analysis": center_analysis,
            "radius_analysis": radius_analysis,
            "compression_analysis": compression_analysis
        }
    
    def _analyze_interaction_matrix_impact(self, trait_def: TraitDefinition) -> Dict[str, Any]:
        """Analyze impact on trait interaction matrix"""
        # Calculate potential interaction strengths with existing traits
        potential_interactions = {}
        
        for existing_trait_name in self.core_framework.trait_registry.keys():
            # Simple heuristic based on category and dependencies
            if trait_def.category == self.core_framework.trait_registry[existing_trait_name].category:
                potential_interactions[existing_trait_name] = 0.3  # Same category = moderate interaction
            
            if existing_trait_name in trait_def.dependencies:
                potential_interactions[existing_trait_name] = 0.6  # Dependency = strong interaction
            
            if trait_def.name in self.core_framework.trait_registry[existing_trait_name].dependencies:
                potential_interactions[existing_trait_name] = -0.4  # Reverse dependency
        
        return {
            "passed": True,  # Interaction analysis is informational
            "potential_interactions": potential_interactions,
            "matrix_expansion_required": len(potential_interactions) > 0
        }
    
    def _synthesize_compatibility_analysis(self, analysis_results: Dict[str, Any]) -> CompatibilityAnalysisResult:
        """Synthesize individual analysis results into overall compatibility assessment"""
        # Check if all critical analyses passed
        critical_analyses = ["_analyze_mathematical_consistency", "_analyze_naming_compatibility", "_analyze_dependency_validity"]
        
        all_critical_passed = all(
            analysis_results.get(analyzer, {}).get("passed", False) 
            for analyzer in critical_analyses
        )
        
        # Collect issues
        naming_conflicts = analysis_results.get("_analyze_naming_compatibility", {}).get("conflicts", [])
        dependency_issues = analysis_results.get("_analyze_dependency_validity", {}).get("dependency_issues", [])
        
        # Calculate mathematical consistency
        math_result = analysis_results.get("_analyze_mathematical_consistency", {})
        mathematical_consistency = math_result.get("passed", False)
        
        # Extract stability and interaction analysis
        stability_analysis = analysis_results.get("_analyze_stability_envelope_impact", {})
        interaction_analysis = analysis_results.get("_analyze_interaction_matrix_impact", {})
        
        # Generate recommendation
        if all_critical_passed:
            recommendation = "APPROVE: Trait meets all compatibility requirements"
        elif not mathematical_consistency:
            recommendation = "REJECT: Mathematical consistency violations detected"
        elif naming_conflicts:
            recommendation = "REJECT: Naming conflicts require resolution"
        elif dependency_issues:
            recommendation = "REJECT: Dependency issues require resolution"
        else:
            recommendation = "REVIEW: Manual review required for edge cases"
        
        return CompatibilityAnalysisResult(
            is_compatible=all_critical_passed,
            mathematical_consistency=mathematical_consistency,
            naming_conflicts=naming_conflicts,
            dependency_issues=dependency_issues,
            stability_envelope_analysis=stability_analysis,
            interaction_impact_assessment=interaction_analysis.get("potential_interactions", {}),
            recommendation=recommendation,
            detailed_analysis=analysis_results
        )
    
    def execute_arbitration_review(self, proposal_id: str, 
                                 reviewing_agent: str, 
                                 decision: str, 
                                 notes: str) -> bool:
        """Execute arbitration council review of trait proposal"""
        proposal = self.active_proposals.get(proposal_id)
        if not proposal or proposal.status != AmendmentStatus.ARBITRATION_REVIEW:
            return False
        
        # Add arbitration notes
        proposal.arbitration_notes.append(f"{reviewing_agent}: {decision} - {notes}")
        
        # For this implementation, single arbitrator can approve/reject
        # In full system, would require council consensus
        if decision.lower() == "approve":
            self._advance_proposal_status(proposal_id, AmendmentStatus.APPROVED,
                                        reviewing_agent, f"Arbitration approved: {notes}")
            return True
        elif decision.lower() == "reject":
            self._advance_proposal_status(proposal_id, AmendmentStatus.REJECTED,
                                        reviewing_agent, f"Arbitration rejected: {notes}")
            return False
        
        return False
    
    def integrate_approved_trait(self, proposal_id: str, integrating_agent: str) -> bool:
        """Integrate approved trait into core framework"""
        proposal = self.active_proposals.get(proposal_id)
        if not proposal or proposal.status != AmendmentStatus.APPROVED:
            return False
        
        # Register trait in core framework
        success = self.core_framework.register_trait(proposal.proposed_trait)
        
        if success:
            # Update proposal status
            self._advance_proposal_status(proposal_id, AmendmentStatus.INTEGRATED,
                                        integrating_agent, "Trait successfully integrated")
            
            # Record in amendment ledger
            self.amendment_ledger.append({
                "proposal_id": proposal_id,
                "trait_name": proposal.proposed_trait.name,
                "integration_timestamp": datetime.utcnow().isoformat(),
                "integrating_agent": integrating_agent,
                "amendment_type": "trait_addition"
            })
            
            # Move to history
            self.proposal_history.append(proposal)
            del self.active_proposals[proposal_id]
            
        return success
    
    def _advance_proposal_status(self, proposal_id: str, new_status: AmendmentStatus,
                                agent_id: str, notes: str):
        """Advance proposal to new status with audit trail"""
        proposal = self.active_proposals.get(proposal_id)
        if not proposal:
            return
        
        # Update status
        proposal.status = new_status
        
        # Add to status history
        proposal.status_history.append({
            "status": new_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent_id,
            "notes": notes
        })
    
    def _names_too_similar(self, name1: str, name2: str, threshold: int = 2) -> bool:
        """Simple string similarity check"""
        if abs(len(name1) - len(name2)) > threshold:
            return False
        
        differences = sum(c1 != c2 for c1, c2 in zip(name1, name2))
        return differences <= threshold
    
    def _would_create_circular_dependency(self, trait_def: TraitDefinition) -> bool:
        """Check if trait would create circular dependency"""
        # Simple check - in full implementation would do graph analysis
        return trait_def.name in trait_def.dependencies
    
    def _assess_center_conflicts(self, envelope: StabilityEnvelope, existing: List[StabilityEnvelope]) -> float:
        """Assess potential conflicts with existing stability centers"""
        if not existing:
            return 0.0
        
        min_distance = min(abs(envelope.center - e.center) for e in existing)
        return max(0.0, 1.0 - (min_distance / 0.5))  # Conflict risk increases as centers get closer
    
    def _assess_radius_harmony(self, envelope: StabilityEnvelope, existing: List[StabilityEnvelope]) -> float:
        """Assess harmony with existing radius values"""
        if not existing:
            return 1.0
        
        avg_radius = sum(e.radius for e in existing) / len(existing)
        radius_difference = abs(envelope.radius - avg_radius)
        return max(0.0, 1.0 - (radius_difference / 0.5))  # Harmony decreases with difference
    
    def _assess_stability_impact(self, envelope: StabilityEnvelope) -> str:
        """Assess stability impact of envelope parameters"""
        if envelope.compression_factor > 2.0:
            return "HIGH_STABILITY: Strong compression may resist necessary evolution"
        elif envelope.compression_factor < 0.5:
            return "LOW_STABILITY: Weak compression may allow excessive drift"
        else:
            return "BALANCED: Compression factor within normal range"
    
    def get_proposal_status(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of trait proposal"""
        proposal = self.active_proposals.get(proposal_id)
        if not proposal:
            # Check history
            for historical_proposal in self.proposal_history:
                if historical_proposal.proposal_id == proposal_id:
                    proposal = historical_proposal
                    break
        
        if not proposal:
            return None
        
        return {
            "proposal_id": proposal.proposal_id,
            "trait_name": proposal.proposed_trait.name,
            "current_status": proposal.status.value,
            "proposer": proposal.proposer_agent_id,
            "created": proposal.created_timestamp.isoformat(),
            "status_history": proposal.status_history,
            "compatibility_analysis": proposal.compatibility_analysis,
            "arbitration_notes": proposal.arbitration_notes
        }
    
    def list_active_proposals(self) -> List[Dict[str, Any]]:
        """List all active proposals"""
        return [
            {
                "proposal_id": proposal.proposal_id,
                "trait_name": proposal.proposed_trait.name,
                "status": proposal.status.value,
                "proposer": proposal.proposer_agent_id,
                "created": proposal.created_timestamp.isoformat()
            }
            for proposal in self.active_proposals.values()
        ]
    
    def export_amendment_ledger(self) -> Dict[str, Any]:
        """Export complete amendment ledger for audit"""
        return {
            "ledger_version": "1.0",
            "total_amendments": len(self.amendment_ledger),
            "active_proposals": len(self.active_proposals),
            "completed_proposals": len(self.proposal_history),
            "amendments": self.amendment_ledger,
            "export_timestamp": datetime.utcnow().isoformat()
        }


# Example usage
if __name__ == "__main__":
    # Initialize systems
    core_framework = CoreTraitFramework()
    registration_system = TraitRegistrationSystem(core_framework)
    
    # Example: Propose new cognitive trait
    cognitive_trait = TraitDefinition(
        name="pattern_recognition",
        category=TraitCategory.COGNITIVE,
        stability_envelope=StabilityEnvelope(center=0.6, radius=0.2, compression_factor=1.1),
        description="Ability to recognize and utilize patterns in information",
        dependencies=["convergencestability"]
    )
    
    # Submit proposal
    proposal_id = registration_system.submit_trait_proposal(
        cognitive_trait,
        "djinn_cognitive_specialist",
        "Pattern recognition is fundamental for intelligent system adaptation"
    )
    
    print(f"Submitted proposal: {proposal_id}")
    
    # Execute compatibility analysis
    analysis_result = registration_system.execute_compatibility_analysis(proposal_id)
    print(f"Compatibility analysis: {analysis_result.recommendation}")
    
    # Execute arbitration (if passed analysis)
    if analysis_result.is_compatible:
        arbitration_success = registration_system.execute_arbitration_review(
            proposal_id,
            "djinn_meta_auditor",
            "approve",
            "Cognitive traits enhance system intelligence capabilities"
        )
        
        if arbitration_success:
            # Integrate trait
            integration_success = registration_system.integrate_approved_trait(
                proposal_id,
                "djinn_integration_agent"
            )
            print(f"Integration successful: {integration_success}")
    
    # Show final status
    final_status = registration_system.get_proposal_status(proposal_id)
    print(f"Final status: {final_status['current_status']}")
    
    # Show updated framework
    print(f"Framework now has {len(core_framework.trait_registry)} traits")