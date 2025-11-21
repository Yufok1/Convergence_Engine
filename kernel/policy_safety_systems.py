"""
Policy and Safety Systems - Phase 4.3 Implementation

This module implements the Policy and Safety Systems that enforce governance policies
on all natural language interactions. It provides sensitive information redaction,
validation of plans against the Sovereign Codex, and enforcement of resource limits
to ensure that all human-driven operations remain safe and compliant.

Key Features:
- Sensitive information redaction and protection
- Sovereign Codex policy validation
- Resource limits enforcement for human operations
- Policy compliance checking framework
- Safety validation pipeline for all interactions
- Governance policy enforcement and monitoring
"""

import time
import math
import hashlib
import threading
import asyncio
import re
import json
from typing import Dict, List, Any, Optional, Tuple, Set, Callable, Union, Pattern
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime, timedelta
from collections import defaultdict, deque
import heapq

from enhanced_synchrony_protocol import EnhancedSynchronyProtocol, DialogIntegrityLevel
from instruction_interpretation_layer import (
    InstructionInterpretationLayer, HumanInstruction, ParsedInstruction, KernelAction,
    InstructionType, ProcessingStrategy
)
from codex_amendment_system import CodexAmendmentSystem, AmendmentType, AmendmentStatus
from arbitration_stack import ProductionArbitrationStack, ArbitrationDecisionType
from synchrony_phase_lock_protocol import ProductionSynchronySystem, OperationPriority
from advanced_trait_engine import AdvancedTraitEngine
from utm_kernel_design import UTMKernel
from event_driven_coordination import DjinnEventBus, EventType
from violation_pressure_calculation import ViolationMonitor, ViolationClass


class PolicyType(Enum):
    """Types of governance policies"""
    INFORMATION_SECURITY = "information_security"     # Sensitive information protection
    RESOURCE_MANAGEMENT = "resource_management"       # Resource usage limits
    OPERATIONAL_SAFETY = "operational_safety"         # Safety constraints
    CODEX_COMPLIANCE = "codex_compliance"             # Sovereign Codex compliance
    ACCESS_CONTROL = "access_control"                 # User access permissions
    CONTENT_FILTERING = "content_filtering"           # Content appropriateness
    RATE_LIMITING = "rate_limiting"                   # Request rate limits
    AUDIT_REQUIREMENTS = "audit_requirements"         # Audit trail requirements


class PolicySeverity(Enum):
    """Severity levels for policy violations"""
    INFO = 1          # Informational only
    LOW = 2           # Low severity violation
    MEDIUM = 3        # Medium severity violation
    HIGH = 4          # High severity violation
    CRITICAL = 5      # Critical security violation
    EMERGENCY = 6     # Emergency intervention required


class SafetyLevel(Enum):
    """Safety levels for operation validation"""
    UNRESTRICTED = "unrestricted"      # No safety restrictions
    STANDARD = "standard"              # Standard safety checks
    ENHANCED = "enhanced"              # Enhanced safety validation
    STRICT = "strict"                  # Strict safety enforcement
    MAXIMUM = "maximum"                # Maximum safety controls


class RedactionType(Enum):
    """Types of information redaction"""
    FULL_REDACTION = "full_redaction"          # Complete removal
    PARTIAL_REDACTION = "partial_redaction"    # Partial masking
    HASH_REPLACEMENT = "hash_replacement"      # Replace with hash
    TOKEN_REPLACEMENT = "token_replacement"    # Replace with tokens
    CATEGORY_LABEL = "category_label"          # Replace with category


@dataclass
class PolicyRule:
    """A governance policy rule"""
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    policy_type: PolicyType = PolicyType.OPERATIONAL_SAFETY
    rule_name: str = ""
    description: str = ""
    pattern: Optional[str] = None
    compiled_pattern: Optional[Pattern] = None
    severity: PolicySeverity = PolicySeverity.MEDIUM
    action: str = "warn"  # warn, block, redirect, redact
    parameters: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    
    def __post_init__(self):
        """Compile regex pattern if provided"""
        if self.pattern and not self.compiled_pattern:
            try:
                self.compiled_pattern = re.compile(self.pattern, re.IGNORECASE | re.MULTILINE)
            except re.error as e:
                print(f"Invalid regex pattern in rule {self.rule_id}: {e}")


@dataclass
class PolicyViolation:
    """A detected policy violation"""
    violation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str = ""
    policy_type: PolicyType = PolicyType.OPERATIONAL_SAFETY
    severity: PolicySeverity = PolicySeverity.MEDIUM
    instruction_id: str = ""
    user_id: str = ""
    violation_description: str = ""
    detected_content: str = ""
    action_taken: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolution_details: Optional[str] = None


@dataclass
class ResourceLimits:
    """Resource limits for operations"""
    max_instructions_per_minute: int = 60
    max_instructions_per_hour: int = 1000
    max_concurrent_operations: int = 10
    max_memory_usage_mb: int = 1024
    max_processing_time_seconds: float = 300.0
    max_file_size_mb: int = 100
    max_network_requests: int = 100
    allowed_file_types: Set[str] = field(default_factory=lambda: {".txt", ".json", ".md", ".py"})
    blocked_domains: Set[str] = field(default_factory=set)
    
    def check_rate_limit(self, user_id: str, instruction_count: int, 
                        time_window_minutes: int) -> bool:
        """Check if rate limit is exceeded"""
        if time_window_minutes <= 1:
            return instruction_count <= self.max_instructions_per_minute
        elif time_window_minutes <= 60:
            return instruction_count <= self.max_instructions_per_hour
        else:
            # Daily limit (extrapolated)
            daily_limit = self.max_instructions_per_hour * 24
            return instruction_count <= daily_limit


@dataclass
class SafetyValidationResult:
    """Result of safety validation"""
    validation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    instruction_id: str = ""
    safety_level: SafetyLevel = SafetyLevel.STANDARD
    passed: bool = False
    violations: List[PolicyViolation] = field(default_factory=list)
    redacted_content: Optional[str] = None
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    validation_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    validator_agent: str = "policy_safety_validator"


class SensitiveInformationRedactor:
    """Redacts sensitive information from user inputs"""
    
    def __init__(self):
        self.redaction_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "ssn": r'\b\d{3}-?\d{2}-?\d{4}\b',
            "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            "api_key": r'\b[A-Za-z0-9]{32,}\b',
            "password": r'(?i)(password|pwd|pass)\s*[:=]\s*\S+',
            "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            "file_path": r'[C-Z]:\\[^<>:"|*?\r\n]*',
            "url": r'https?://[^\s<>"{}|\\^`\[\]]+',
            "private_key": r'-----BEGIN [A-Z\s]+ PRIVATE KEY-----.*?-----END [A-Z\s]+ PRIVATE KEY-----'
        }
        
        self.compiled_patterns = {}
        for name, pattern in self.redaction_patterns.items():
            try:
                self.compiled_patterns[name] = re.compile(pattern, re.IGNORECASE | re.DOTALL)
            except re.error as e:
                print(f"Invalid redaction pattern {name}: {e}")
        
        self.redaction_stats = defaultdict(int)
    
    def redact_sensitive_information(self, content: str, 
                                   redaction_type: RedactionType = RedactionType.PARTIAL_REDACTION) -> Tuple[str, List[str]]:
        """Redact sensitive information from content"""
        
        redacted_content = content
        redacted_items = []
        
        for name, pattern in self.compiled_patterns.items():
            matches = pattern.findall(content)
            
            for match in matches:
                if redaction_type == RedactionType.FULL_REDACTION:
                    replacement = "[REDACTED]"
                elif redaction_type == RedactionType.PARTIAL_REDACTION:
                    replacement = self._partial_redact(str(match))
                elif redaction_type == RedactionType.HASH_REPLACEMENT:
                    replacement = f"[HASH:{hashlib.sha256(str(match).encode()).hexdigest()[:8]}]"
                elif redaction_type == RedactionType.TOKEN_REPLACEMENT:
                    replacement = f"[{name.upper()}_TOKEN]"
                elif redaction_type == RedactionType.CATEGORY_LABEL:
                    replacement = f"[{name.upper()}]"
                else:
                    replacement = "[REDACTED]"
                
                redacted_content = redacted_content.replace(str(match), replacement)
                redacted_items.append(f"{name}: {match}")
                self.redaction_stats[name] += 1
        
        return redacted_content, redacted_items
    
    def _partial_redact(self, text: str) -> str:
        """Partially redact text, showing only first and last characters"""
        if len(text) <= 3:
            return "*" * len(text)
        elif len(text) <= 6:
            return text[0] + "*" * (len(text) - 2) + text[-1]
        else:
            return text[:2] + "*" * (len(text) - 4) + text[-2:]
    
    def get_redaction_stats(self) -> Dict[str, int]:
        """Get redaction statistics"""
        return dict(self.redaction_stats)


class SovereignCodexValidator:
    """Validates operations against the Sovereign Codex"""
    
    def __init__(self, codex_amendment_system: CodexAmendmentSystem):
        self.codex_amendment_system = codex_amendment_system
        self.validation_cache = {}
        self.validation_rules = {
            "constitutional_compliance": self._validate_constitutional_compliance,
            "procedural_compliance": self._validate_procedural_compliance,
            "amendment_authorization": self._validate_amendment_authorization,
            "resource_authorization": self._validate_resource_authorization,
            "governance_authority": self._validate_governance_authority
        }
        self.validation_stats = defaultdict(int)
    
    def validate_against_codex(self, instruction: HumanInstruction, 
                             parsed_instruction: ParsedInstruction) -> Tuple[bool, List[str]]:
        """Validate instruction against Sovereign Codex"""
        
        validation_errors = []
        
        # Check cache first
        cache_key = f"{instruction.instruction_id}:{parsed_instruction.intent}"
        if cache_key in self.validation_cache:
            return self.validation_cache[cache_key]
        
        # Run all validation rules
        for rule_name, rule_func in self.validation_rules.items():
            try:
                is_valid, error_message = rule_func(instruction, parsed_instruction)
                self.validation_stats[rule_name] += 1
                
                if not is_valid:
                    validation_errors.append(f"{rule_name}: {error_message}")
                    self.validation_stats[f"{rule_name}_failed"] += 1
                else:
                    self.validation_stats[f"{rule_name}_passed"] += 1
                    
            except Exception as e:
                validation_errors.append(f"{rule_name}: Validation error - {e}")
                self.validation_stats[f"{rule_name}_error"] += 1
        
        # Overall validation result
        is_valid = len(validation_errors) == 0
        
        # Cache result
        self.validation_cache[cache_key] = (is_valid, validation_errors)
        
        return is_valid, validation_errors
    
    def _validate_constitutional_compliance(self, instruction: HumanInstruction, 
                                          parsed_instruction: ParsedInstruction) -> Tuple[bool, str]:
        """Validate constitutional compliance"""
        
        # Check for constitutional violations
        prohibited_actions = ["bypass_governance", "override_sovereignty", "disable_safety"]
        
        for action in prohibited_actions:
            if action in parsed_instruction.intent.lower():
                return False, f"Prohibited action: {action}"
        
        # Check instruction type permissions
        if instruction.instruction_type == InstructionType.EMERGENCY:
            if instruction.sender_id != "emergency_authorized_user":
                return False, "Emergency instructions require emergency authorization"
        
        return True, ""
    
    def _validate_procedural_compliance(self, instruction: HumanInstruction, 
                                      parsed_instruction: ParsedInstruction) -> Tuple[bool, str]:
        """Validate procedural compliance"""
        
        # Check for proper procedure following
        if instruction.instruction_type == InstructionType.AMENDMENT:
            # Amendment instructions must follow proper procedure
            if "propose" not in parsed_instruction.intent.lower():
                return False, "Amendment instructions must use proper proposal procedure"
        
        # Check for required parameters
        if instruction.instruction_type == InstructionType.GOVERNANCE:
            if not instruction.priority or instruction.priority < 0.5:
                return False, "Governance instructions require appropriate priority level"
        
        return True, ""
    
    def _validate_amendment_authorization(self, instruction: HumanInstruction, 
                                        parsed_instruction: ParsedInstruction) -> Tuple[bool, str]:
        """Validate amendment authorization"""
        
        if instruction.instruction_type == InstructionType.AMENDMENT:
            # Check if user is authorized to propose amendments
            authorized_users = {"human_user_1", "governance_admin", "constitutional_authority"}
            
            if instruction.sender_id not in authorized_users:
                return False, f"User {instruction.sender_id} not authorized for amendments"
        
        return True, ""
    
    def _validate_resource_authorization(self, instruction: HumanInstruction, 
                                       parsed_instruction: ParsedInstruction) -> Tuple[bool, str]:
        """Validate resource authorization"""
        
        # Check for resource-intensive operations
        resource_intensive_keywords = ["analyze_all", "process_everything", "unlimited", "maximum"]
        
        for keyword in resource_intensive_keywords:
            if keyword in instruction.raw_text.lower():
                if instruction.priority < 0.8:
                    return False, f"Resource-intensive operation requires high priority: {keyword}"
        
        return True, ""
    
    def _validate_governance_authority(self, instruction: HumanInstruction, 
                                     parsed_instruction: ParsedInstruction) -> Tuple[bool, str]:
        """Validate governance authority"""
        
        # Check governance authority for governance instructions
        if instruction.instruction_type == InstructionType.GOVERNANCE:
            governance_authorities = {"governance_admin", "arbitration_authority", "sovereign_entity"}
            
            if instruction.sender_id not in governance_authorities:
                return False, f"User {instruction.sender_id} lacks governance authority"
        
        return True, ""
    
    def get_validation_stats(self) -> Dict[str, int]:
        """Get validation statistics"""
        return dict(self.validation_stats)


class ResourceLimitsEnforcer:
    """Enforces resource limits for human-driven operations"""
    
    def __init__(self, default_limits: Optional[ResourceLimits] = None):
        self.default_limits = default_limits or ResourceLimits()
        self.user_limits = {}
        self.usage_tracking = defaultdict(lambda: {
            "instructions_per_minute": deque(maxlen=60),
            "instructions_per_hour": deque(maxlen=3600),
            "concurrent_operations": 0,
            "memory_usage_mb": 0.0,
            "active_operations": set()
        })
        self.enforcement_stats = defaultdict(int)
    
    def check_resource_limits(self, instruction: HumanInstruction) -> Tuple[bool, List[str]]:
        """Check if instruction violates resource limits"""
        
        user_id = instruction.sender_id
        limits = self.user_limits.get(user_id, self.default_limits)
        violations = []
        
        # Check rate limits
        current_time = datetime.utcnow()
        user_usage = self.usage_tracking[user_id]
        
        # Count instructions in last minute
        minute_instructions = sum(1 for ts in user_usage["instructions_per_minute"] 
                                if (current_time - ts).total_seconds() <= 60)
        
        if minute_instructions >= limits.max_instructions_per_minute:
            violations.append(f"Rate limit exceeded: {minute_instructions}/{limits.max_instructions_per_minute} per minute")
            self.enforcement_stats["rate_limit_violations"] += 1
        
        # Count instructions in last hour
        hour_instructions = sum(1 for ts in user_usage["instructions_per_hour"] 
                              if (current_time - ts).total_seconds() <= 3600)
        
        if hour_instructions >= limits.max_instructions_per_hour:
            violations.append(f"Hourly limit exceeded: {hour_instructions}/{limits.max_instructions_per_hour} per hour")
            self.enforcement_stats["hourly_limit_violations"] += 1
        
        # Check concurrent operations
        if user_usage["concurrent_operations"] >= limits.max_concurrent_operations:
            violations.append(f"Concurrent operations limit exceeded: {user_usage['concurrent_operations']}/{limits.max_concurrent_operations}")
            self.enforcement_stats["concurrent_limit_violations"] += 1
        
        # Check priority-based limits
        if instruction.priority > 0.9 and user_id not in {"emergency_authorized_user", "governance_admin"}:
            violations.append("High priority instructions require special authorization")
            self.enforcement_stats["priority_violations"] += 1
        
        # Update usage tracking if no violations
        if not violations:
            user_usage["instructions_per_minute"].append(current_time)
            user_usage["instructions_per_hour"].append(current_time)
            user_usage["concurrent_operations"] += 1
            user_usage["active_operations"].add(instruction.instruction_id)
        
        return len(violations) == 0, violations
    
    def release_operation_resources(self, user_id: str, instruction_id: str) -> None:
        """Release resources for completed operation"""
        
        user_usage = self.usage_tracking[user_id]
        if instruction_id in user_usage["active_operations"]:
            user_usage["active_operations"].remove(instruction_id)
            user_usage["concurrent_operations"] = max(0, user_usage["concurrent_operations"] - 1)
    
    def set_user_limits(self, user_id: str, limits: ResourceLimits) -> None:
        """Set custom resource limits for a user"""
        self.user_limits[user_id] = limits
    
    def get_user_usage(self, user_id: str) -> Dict[str, Any]:
        """Get current resource usage for a user"""
        
        user_usage = self.usage_tracking[user_id]
        current_time = datetime.utcnow()
        
        return {
            "instructions_last_minute": sum(1 for ts in user_usage["instructions_per_minute"] 
                                          if (current_time - ts).total_seconds() <= 60),
            "instructions_last_hour": sum(1 for ts in user_usage["instructions_per_hour"] 
                                        if (current_time - ts).total_seconds() <= 3600),
            "concurrent_operations": user_usage["concurrent_operations"],
            "memory_usage_mb": user_usage["memory_usage_mb"],
            "active_operations": len(user_usage["active_operations"])
        }
    
    def get_enforcement_stats(self) -> Dict[str, int]:
        """Get enforcement statistics"""
        return dict(self.enforcement_stats)


class PolicyComplianceChecker:
    """Checks compliance with governance policies"""
    
    def __init__(self):
        self.policy_rules = {}
        self.violation_history = []
        self.compliance_stats = defaultdict(int)
        self._initialize_default_policies()
    
    def _initialize_default_policies(self) -> None:
        """Initialize default policy rules"""
        
        # Information security policies
        self.add_policy_rule(PolicyRule(
            policy_type=PolicyType.INFORMATION_SECURITY,
            rule_name="No Sensitive Data",
            description="Prevent sharing of sensitive information",
            pattern=r"(password|secret|token|key|credential)",
            severity=PolicySeverity.HIGH,
            action="redact"
        ))
        
        # Operational safety policies
        self.add_policy_rule(PolicyRule(
            policy_type=PolicyType.OPERATIONAL_SAFETY,
            rule_name="No System Shutdown",
            description="Prevent unauthorized system shutdown",
            pattern=r"(shutdown|terminate|kill|destroy)",
            severity=PolicySeverity.CRITICAL,
            action="block"
        ))
        
        # Content filtering policies
        self.add_policy_rule(PolicyRule(
            policy_type=PolicyType.CONTENT_FILTERING,
            rule_name="Professional Language",
            description="Ensure professional communication",
            pattern=r"(profanity|inappropriate|offensive)",
            severity=PolicySeverity.MEDIUM,
            action="warn"
        ))
        
        # Resource management policies
        self.add_policy_rule(PolicyRule(
            policy_type=PolicyType.RESOURCE_MANAGEMENT,
            rule_name="Reasonable Resource Requests",
            description="Prevent excessive resource requests",
            pattern=r"(infinite|unlimited|maximum|all)",
            severity=PolicySeverity.MEDIUM,
            action="warn"
        ))
    
    def add_policy_rule(self, rule: PolicyRule) -> None:
        """Add a new policy rule"""
        self.policy_rules[rule.rule_id] = rule
    
    def remove_policy_rule(self, rule_id: str) -> bool:
        """Remove a policy rule"""
        if rule_id in self.policy_rules:
            del self.policy_rules[rule_id]
            return True
        return False
    
    def check_policy_compliance(self, instruction: HumanInstruction) -> List[PolicyViolation]:
        """Check instruction for policy compliance"""
        
        violations = []
        
        for rule in self.policy_rules.values():
            if not rule.active:
                continue
            
            # Check if rule pattern matches
            if rule.compiled_pattern:
                matches = rule.compiled_pattern.findall(instruction.raw_text)
                
                if matches:
                    violation = PolicyViolation(
                        rule_id=rule.rule_id,
                        policy_type=rule.policy_type,
                        severity=rule.severity,
                        instruction_id=instruction.instruction_id,
                        user_id=instruction.sender_id,
                        violation_description=f"Rule '{rule.rule_name}' triggered",
                        detected_content=str(matches),
                        action_taken=rule.action
                    )
                    
                    violations.append(violation)
                    self.violation_history.append(violation)
                    
                    # Update rule statistics
                    rule.last_triggered = datetime.utcnow()
                    rule.trigger_count += 1
                    
                    # Update compliance statistics
                    self.compliance_stats[f"{rule.policy_type.value}_violations"] += 1
                    self.compliance_stats[f"severity_{rule.severity.value}_violations"] += 1
        
        self.compliance_stats["total_checks"] += 1
        if violations:
            self.compliance_stats["failed_checks"] += 1
        else:
            self.compliance_stats["passed_checks"] += 1
        
        return violations
    
    def get_policy_summary(self) -> Dict[str, Any]:
        """Get summary of all policies"""
        
        policy_summary = {}
        for policy_type in PolicyType:
            rules = [rule for rule in self.policy_rules.values() 
                    if rule.policy_type == policy_type]
            
            policy_summary[policy_type.value] = {
                "rule_count": len(rules),
                "active_rules": sum(1 for rule in rules if rule.active),
                "total_triggers": sum(rule.trigger_count for rule in rules),
                "rules": [
                    {
                        "rule_id": rule.rule_id,
                        "rule_name": rule.rule_name,
                        "severity": rule.severity.value,
                        "trigger_count": rule.trigger_count,
                        "active": rule.active
                    }
                    for rule in rules
                ]
            }
        
        return policy_summary
    
    def get_compliance_stats(self) -> Dict[str, int]:
        """Get compliance statistics"""
        return dict(self.compliance_stats)


class SafetyValidationPipeline:
    """Safety validation pipeline for all interactions"""
    
    def __init__(self, codex_amendment_system: CodexAmendmentSystem):
        self.redactor = SensitiveInformationRedactor()
        self.codex_validator = SovereignCodexValidator(codex_amendment_system)
        self.resource_enforcer = ResourceLimitsEnforcer()
        self.compliance_checker = PolicyComplianceChecker()
        
        self.validation_history = []
        self.safety_stats = defaultdict(int)
    
    def validate_instruction_safety(self, instruction: HumanInstruction, 
                                  parsed_instruction: ParsedInstruction,
                                  safety_level: SafetyLevel = SafetyLevel.STANDARD) -> SafetyValidationResult:
        """Validate instruction through complete safety pipeline"""
        
        start_time = time.time()
        result = SafetyValidationResult(
            instruction_id=instruction.instruction_id,
            safety_level=safety_level
        )
        
        # Step 1: Check policy compliance
        policy_violations = self.compliance_checker.check_policy_compliance(instruction)
        result.violations.extend(policy_violations)
        
        # Step 2: Check resource limits
        resource_allowed, resource_violations = self.resource_enforcer.check_resource_limits(instruction)
        if not resource_allowed:
            for violation_msg in resource_violations:
                violation = PolicyViolation(
                    policy_type=PolicyType.RESOURCE_MANAGEMENT,
                    severity=PolicySeverity.HIGH,
                    instruction_id=instruction.instruction_id,
                    user_id=instruction.sender_id,
                    violation_description="Resource limit violation",
                    detected_content=violation_msg,
                    action_taken="block"
                )
                result.violations.append(violation)
        
        # Step 3: Validate against Sovereign Codex
        codex_valid, codex_errors = self.codex_validator.validate_against_codex(instruction, parsed_instruction)
        if not codex_valid:
            for error_msg in codex_errors:
                violation = PolicyViolation(
                    policy_type=PolicyType.CODEX_COMPLIANCE,
                    severity=PolicySeverity.HIGH,
                    instruction_id=instruction.instruction_id,
                    user_id=instruction.sender_id,
                    violation_description="Codex compliance violation",
                    detected_content=error_msg,
                    action_taken="block"
                )
                result.violations.append(violation)
        
        # Step 4: Redact sensitive information
        redacted_content, redacted_items = self.redactor.redact_sensitive_information(
            instruction.raw_text, RedactionType.PARTIAL_REDACTION
        )
        
        if redacted_items:
            result.redacted_content = redacted_content
            violation = PolicyViolation(
                policy_type=PolicyType.INFORMATION_SECURITY,
                severity=PolicySeverity.MEDIUM,
                instruction_id=instruction.instruction_id,
                user_id=instruction.sender_id,
                violation_description="Sensitive information detected and redacted",
                detected_content=str(redacted_items),
                action_taken="redact"
            )
            result.violations.append(violation)
        
        # Step 5: Apply safety level specific checks
        if safety_level in [SafetyLevel.STRICT, SafetyLevel.MAXIMUM]:
            # Additional strict safety checks
            if instruction.instruction_type == InstructionType.EMERGENCY:
                if safety_level == SafetyLevel.MAXIMUM:
                    violation = PolicyViolation(
                        policy_type=PolicyType.OPERATIONAL_SAFETY,
                        severity=PolicySeverity.CRITICAL,
                        instruction_id=instruction.instruction_id,
                        user_id=instruction.sender_id,
                        violation_description="Emergency instructions blocked under maximum safety",
                        detected_content="emergency_instruction",
                        action_taken="block"
                    )
                    result.violations.append(violation)
        
        # Determine overall validation result
        critical_violations = [v for v in result.violations if v.severity in [PolicySeverity.CRITICAL, PolicySeverity.EMERGENCY]]
        high_violations = [v for v in result.violations if v.severity == PolicySeverity.HIGH]
        
        if critical_violations:
            result.passed = False
            self.safety_stats["critical_failures"] += 1
        elif high_violations and safety_level in [SafetyLevel.STRICT, SafetyLevel.MAXIMUM]:
            result.passed = False
            self.safety_stats["high_severity_failures"] += 1
        else:
            result.passed = True
            self.safety_stats["validations_passed"] += 1
        
        # Record validation time
        result.validation_time_ms = (time.time() - start_time) * 1000
        
        # Update statistics
        self.safety_stats["total_validations"] += 1
        self.safety_stats[f"safety_level_{safety_level.value}"] += 1
        
        # Store in history
        self.validation_history.append(result)
        
        return result
    
    def release_instruction_resources(self, user_id: str, instruction_id: str) -> None:
        """Release resources for completed instruction"""
        self.resource_enforcer.release_operation_resources(user_id, instruction_id)
    
    def get_safety_stats(self) -> Dict[str, Any]:
        """Get comprehensive safety statistics"""
        
        return {
            "validation_stats": dict(self.safety_stats),
            "redaction_stats": self.redactor.get_redaction_stats(),
            "codex_validation_stats": self.codex_validator.get_validation_stats(),
            "resource_enforcement_stats": self.resource_enforcer.get_enforcement_stats(),
            "policy_compliance_stats": self.compliance_checker.get_compliance_stats(),
            "total_violations": len([v for result in self.validation_history for v in result.violations]),
            "recent_validations": len(self.validation_history)
        }


class PolicySafetyManager:
    """Main manager for policy and safety systems"""
    
    def __init__(self, enhanced_synchrony: EnhancedSynchronyProtocol,
                 instruction_layer: InstructionInterpretationLayer,
                 codex_amendment_system: CodexAmendmentSystem,
                 arbitration_stack: ProductionArbitrationStack,
                 synchrony_system: ProductionSynchronySystem):
        
        self.enhanced_synchrony = enhanced_synchrony
        self.instruction_layer = instruction_layer
        self.codex_amendment_system = codex_amendment_system
        self.arbitration_stack = arbitration_stack
        self.synchrony_system = synchrony_system
        
        # Initialize safety pipeline
        self.safety_pipeline = SafetyValidationPipeline(codex_amendment_system)
        
        # Policy enforcement state
        self.enforcement_active = True
        self.default_safety_level = SafetyLevel.STANDARD
        self.user_safety_levels = {}
        
        # Monitoring and metrics
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._policy_monitor, daemon=True)
        self.monitor_thread.start()
    
    def enforce_policy_safety(self, instruction_id: str, 
                             safety_level: Optional[SafetyLevel] = None) -> SafetyValidationResult:
        """Enforce policy and safety on an instruction"""
        
        # Get instruction details
        instruction_status = self.instruction_layer.get_instruction_status(instruction_id)
        if not instruction_status:
            raise ValueError(f"Instruction {instruction_id} not found")
        
        # Get the instruction objects
        instruction = self.instruction_layer.instructions.get(instruction_id)
        parsed_instruction = self.instruction_layer.parsed_instructions.get(instruction_id)
        
        if not instruction or not parsed_instruction:
            raise ValueError(f"Instruction objects not found for {instruction_id}")
        
        # Determine safety level
        if safety_level is None:
            safety_level = self.user_safety_levels.get(instruction.sender_id, self.default_safety_level)
        
        # Run safety validation pipeline
        validation_result = self.safety_pipeline.validate_instruction_safety(
            instruction, parsed_instruction, safety_level
        )
        
        # Handle validation results
        if not validation_result.passed:
            # Block instruction if validation failed
            self._handle_safety_violation(instruction, validation_result)
        else:
            # Allow instruction to proceed
            self._log_safety_success(instruction, validation_result)
        
        # Synchronize safety validation with enhanced synchrony
        if self.enhanced_synchrony:
            try:
                self.enhanced_synchrony.synchronize_dialog_operation(
                    instruction_id=instruction_id,
                    integrity_level=DialogIntegrityLevel.ENHANCED,
                    priority=OperationPriority.HIGH
                )
            except Exception as e:
                print(f"Safety synchronization failed for {instruction_id}: {e}")
        
        return validation_result
    
    def _handle_safety_violation(self, instruction: HumanInstruction, 
                                validation_result: SafetyValidationResult) -> None:
        """Handle safety validation violations"""
        
        critical_violations = [v for v in validation_result.violations 
                             if v.severity in [PolicySeverity.CRITICAL, PolicySeverity.EMERGENCY]]
        
        if critical_violations:
            # Escalate to arbitration stack for critical violations
            try:
                # Create arbitration request for critical safety violation
                print(f"CRITICAL SAFETY VIOLATION: Instruction {instruction.instruction_id} blocked")
                print(f"Violations: {[v.violation_description for v in critical_violations]}")
                
                # In production, this would trigger emergency protocols
                
            except Exception as e:
                print(f"Error escalating safety violation: {e}")
        
        # Log all violations
        for violation in validation_result.violations:
            print(f"SAFETY VIOLATION: {violation.violation_description} "
                  f"(Severity: {violation.severity.value}, Action: {violation.action_taken})")
    
    def _log_safety_success(self, instruction: HumanInstruction, 
                           validation_result: SafetyValidationResult) -> None:
        """Log successful safety validation"""
        
        if validation_result.redacted_content:
            print(f"SAFETY SUCCESS: Instruction {instruction.instruction_id} passed with redactions")
        else:
            print(f"SAFETY SUCCESS: Instruction {instruction.instruction_id} passed all checks")
    
    def set_user_safety_level(self, user_id: str, safety_level: SafetyLevel) -> None:
        """Set safety level for a specific user"""
        self.user_safety_levels[user_id] = safety_level
    
    def get_policy_summary(self) -> Dict[str, Any]:
        """Get comprehensive policy summary"""
        
        return {
            "enforcement_active": self.enforcement_active,
            "default_safety_level": self.default_safety_level.value,
            "user_safety_levels": {user: level.value for user, level in self.user_safety_levels.items()},
            "policy_summary": self.safety_pipeline.compliance_checker.get_policy_summary(),
            "safety_stats": self.safety_pipeline.get_safety_stats(),
            "monitoring_active": self.monitoring_active
        }
    
    def _policy_monitor(self) -> None:
        """Background monitor for policy and safety"""
        
        while self.monitoring_active:
            try:
                # Monitor for new instructions that need safety validation
                all_instructions = self.instruction_layer.instructions
                
                for instruction_id, instruction in all_instructions.items():
                    # Check if instruction has been safety validated
                    existing_validations = [v for v in self.safety_pipeline.validation_history 
                                          if v.instruction_id == instruction_id]
                    
                    if not existing_validations:
                        # Auto-validate new instructions
                        try:
                            self.enforce_policy_safety(instruction_id)
                        except Exception as e:
                            print(f"Auto safety validation failed for {instruction_id}: {e}")
                
                # Release resources for completed instructions
                for instruction_id, instruction in all_instructions.items():
                    instruction_status = self.instruction_layer.get_instruction_status(instruction_id)
                    if instruction_status and instruction_status['status'] in ['completed', 'rejected']:
                        self.safety_pipeline.release_instruction_resources(
                            instruction.sender_id, instruction_id
                        )
                
                time.sleep(5.0)  # Check every 5 seconds
                
            except Exception as e:
                print(f"Policy monitor error: {e}")
                time.sleep(10.0)
    
    def shutdown(self) -> None:
        """Shutdown the policy and safety manager"""
        
        self.monitoring_active = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)


# Example usage and testing
if __name__ == "__main__":
    # This would be used in the main kernel initialization
    print("Policy and Safety Systems - Phase 4.3 Implementation")
    print("Governance policy enforcement for natural language interactions")
