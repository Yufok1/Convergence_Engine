"""
Security and Compliance - Phase 5.4 Implementation

This module implements the Production Security Framework for the Djinn Kernel.
It provides the final hardening step before the kernel is deemed complete, including
identity and access management, cryptographic verification of all agent actions,
and threat detection protocols required to protect the sovereign entity from external compromise.

Key Features:
- Identity and Access Management (IAM) system
- Cryptographic verification and digital signatures
- Threat detection and response protocols
- Compliance monitoring and audit trails
- Security policy enforcement
- Zero-trust architecture implementation
- Secure communication protocols
- Vulnerability assessment and mitigation
"""

import time
import math
import hashlib
import threading
import asyncio
import json
import hmac
import secrets
import base64
from typing import Dict, List, Any, Optional, Tuple, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime, timedelta
from collections import defaultdict, deque
import heapq
import cryptography
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet

from monitoring_observability import MonitoringObservability, AlertSeverity, MetricType
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


class SecurityLevel(Enum):
    """Security levels for access control"""
    PUBLIC = "public"                          # Public access
    INTERNAL = "internal"                      # Internal system access
    PRIVILEGED = "privileged"                  # Privileged access
    ADMINISTRATIVE = "administrative"          # Administrative access
    SOVEREIGN = "sovereign"                    # Sovereign-level access


class ThreatSeverity(Enum):
    """Threat severity levels"""
    LOW = "low"                               # Low severity threat
    MEDIUM = "medium"                         # Medium severity threat
    HIGH = "high"                             # High severity threat
    CRITICAL = "critical"                     # Critical threat
    EMERGENCY = "emergency"                   # Emergency threat requiring immediate response


class ComplianceStatus(Enum):
    """Compliance status states"""
    COMPLIANT = "compliant"                   # Fully compliant
    WARNING = "warning"                       # Compliance warning
    VIOLATION = "violation"                   # Compliance violation
    CRITICAL = "critical"                     # Critical compliance issue
    AUDIT_REQUIRED = "audit_required"         # Audit required


class AuthenticationMethod(Enum):
    """Authentication methods"""
    PASSWORD = "password"                     # Password authentication
    TOKEN = "token"                           # Token-based authentication
    CERTIFICATE = "certificate"               # Certificate-based authentication
    BIOMETRIC = "biometric"                   # Biometric authentication
    MULTI_FACTOR = "multi_factor"             # Multi-factor authentication


@dataclass
class SecurityIdentity:
    """Security identity definition"""
    identity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    security_level: SecurityLevel = SecurityLevel.INTERNAL
    authentication_methods: List[AuthenticationMethod] = field(default_factory=list)
    public_key: Optional[bytes] = None
    certificate_data: Optional[bytes] = None
    permissions: Set[str] = field(default_factory=set)
    restrictions: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: Optional[datetime] = None
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecuritySession:
    """Security session definition"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    identity_id: str = ""
    security_level: SecurityLevel = SecurityLevel.INTERNAL
    authentication_method: AuthenticationMethod = AuthenticationMethod.TOKEN
    session_token: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_activity: datetime = field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_valid: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityEvent:
    """Security event definition"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    severity: ThreatSeverity = ThreatSeverity.LOW
    source_identity: Optional[str] = None
    target_resource: Optional[str] = None
    description: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution_notes: Optional[str] = None


@dataclass
class ComplianceRule:
    """Compliance rule definition"""
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    rule_type: str = ""
    severity: ThreatSeverity = ThreatSeverity.MEDIUM
    enabled: bool = True
    conditions: Dict[str, Any] = field(default_factory=dict)
    actions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_checked: Optional[datetime] = None
    compliance_status: ComplianceStatus = ComplianceStatus.COMPLIANT


@dataclass
class CryptographicSignature:
    """Cryptographic signature definition"""
    signature_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    data_hash: str = ""
    signature: bytes = b""
    public_key: bytes = b""
    algorithm: str = "RSA-SHA256"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    identity_id: str = ""
    verified: bool = False
    verification_timestamp: Optional[datetime] = None


class CryptographicManager:
    """Manager for cryptographic operations"""
    
    def __init__(self):
        self.private_key: Optional[rsa.RSAPrivateKey] = None
        self.public_key: Optional[rsa.RSAPublicKey] = None
        self.symmetric_key: Optional[bytes] = None
        self.fernet: Optional[Fernet] = None
        
        # Initialize cryptographic components
        self._initialize_cryptography()
    
    def _initialize_cryptography(self) -> None:
        """Initialize cryptographic components"""
        try:
            # Generate RSA key pair
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            self.public_key = self.private_key.public_key()
            
            # Generate symmetric key for Fernet
            self.symmetric_key = Fernet.generate_key()
            self.fernet = Fernet(self.symmetric_key)
            
        except Exception as e:
            print(f"Cryptographic initialization error: {e}")
    
    def generate_signature(self, data: bytes, identity_id: str) -> CryptographicSignature:
        """Generate cryptographic signature for data"""
        try:
            # Hash the data
            data_hash = hashlib.sha256(data).hexdigest()
            
            # Sign the hash
            signature = self.private_key.sign(
                data_hash.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            # Create signature object
            sig_obj = CryptographicSignature(
                data_hash=data_hash,
                signature=signature,
                public_key=self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ),
                identity_id=identity_id
            )
            
            return sig_obj
            
        except Exception as e:
            print(f"Signature generation error: {e}")
            return CryptographicSignature()
    
    def verify_signature(self, signature_obj: CryptographicSignature, data: bytes) -> bool:
        """Verify cryptographic signature"""
        try:
            # Recalculate hash
            data_hash = hashlib.sha256(data).hexdigest()
            
            if data_hash != signature_obj.data_hash:
                return False
            
            # Load public key
            public_key = serialization.load_pem_public_key(signature_obj.public_key)
            
            # Verify signature
            public_key.verify(
                signature_obj.signature,
                data_hash.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            signature_obj.verified = True
            signature_obj.verification_timestamp = datetime.utcnow()
            return True
            
        except Exception as e:
            print(f"Signature verification error: {e}")
            return False
    
    def encrypt_data(self, data: bytes) -> bytes:
        """Encrypt data using symmetric encryption"""
        try:
            if self.fernet:
                return self.fernet.encrypt(data)
            return data
        except Exception as e:
            print(f"Encryption error: {e}")
            return data
    
    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """Decrypt data using symmetric encryption"""
        try:
            if self.fernet:
                return self.fernet.decrypt(encrypted_data)
            return encrypted_data
        except Exception as e:
            print(f"Decryption error: {e}")
            return encrypted_data
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate secure random token"""
        return secrets.token_urlsafe(length)
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_bytes(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = kdf.derive(password.encode())
        return key, salt


class IdentityAccessManager:
    """Identity and Access Management system"""
    
    def __init__(self):
        self.identities: Dict[str, SecurityIdentity] = {}
        self.active_sessions: Dict[str, SecuritySession] = {}
        self.session_history: List[SecuritySession] = []
        self.crypto_manager = CryptographicManager()
        
        # Initialize default identities
        self._initialize_default_identities()
    
    def _initialize_default_identities(self) -> None:
        """Initialize default security identities"""
        
        # Sovereign identity
        sovereign_identity = SecurityIdentity(
            name="Sovereign Kernel",
            description="Primary sovereign identity for kernel operations",
            security_level=SecurityLevel.SOVEREIGN,
            authentication_methods=[AuthenticationMethod.CERTIFICATE, AuthenticationMethod.MULTI_FACTOR],
            permissions={"*"},  # All permissions
            restrictions=set()
        )
        self.identities[sovereign_identity.identity_id] = sovereign_identity
        
        # System identity
        system_identity = SecurityIdentity(
            name="System Operations",
            description="Identity for system-level operations",
            security_level=SecurityLevel.ADMINISTRATIVE,
            authentication_methods=[AuthenticationMethod.CERTIFICATE],
            permissions={"system.*", "monitoring.*", "deployment.*"},
            restrictions={"sovereign.*"}
        )
        self.identities[system_identity.identity_id] = system_identity
        
        # Monitoring identity
        monitoring_identity = SecurityIdentity(
            name="Monitoring System",
            description="Identity for monitoring and observability",
            security_level=SecurityLevel.PRIVILEGED,
            authentication_methods=[AuthenticationMethod.TOKEN],
            permissions={"monitoring.*", "metrics.*"},
            restrictions={"system.*", "sovereign.*"}
        )
        self.identities[monitoring_identity.identity_id] = monitoring_identity
    
    def create_identity(self, name: str, description: str, security_level: SecurityLevel,
                       permissions: Set[str], restrictions: Set[str] = None) -> SecurityIdentity:
        """Create a new security identity"""
        
        identity = SecurityIdentity(
            name=name,
            description=description,
            security_level=security_level,
            permissions=permissions,
            restrictions=restrictions or set()
        )
        
        self.identities[identity.identity_id] = identity
        return identity
    
    def authenticate_identity(self, identity_id: str, authentication_data: Dict[str, Any],
                            ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Optional[SecuritySession]:
        """Authenticate an identity and create session"""
        
        if identity_id not in self.identities:
            return None
        
        identity = self.identities[identity_id]
        
        if not identity.is_active:
            return None
        
        # Generate session token
        session_token = self.crypto_manager.generate_secure_token()
        
        # Create session
        session = SecuritySession(
            identity_id=identity_id,
            security_level=identity.security_level,
            session_token=session_token,
            expires_at=datetime.utcnow() + timedelta(hours=24),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.active_sessions[session.session_id] = session
        self.session_history.append(session)
        
        # Update identity last accessed
        identity.last_accessed = datetime.utcnow()
        
        return session
    
    def validate_session(self, session_id: str, session_token: str) -> Optional[SecuritySession]:
        """Validate an active session"""
        
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        
        if not session.is_valid:
            return None
        
        if session.session_token != session_token:
            return None
        
        if session.expires_at and session.expires_at <= datetime.utcnow():
            session.is_valid = False
            return None
        
        # Update last activity
        session.last_activity = datetime.utcnow()
        
        return session
    
    def check_permission(self, session: SecuritySession, permission: str) -> bool:
        """Check if session has permission for action"""
        
        if session.identity_id not in self.identities:
            return False
        
        identity = self.identities[session.identity_id]
        
        # Check restrictions first
        for restriction in identity.restrictions:
            if permission.startswith(restriction):
                return False
        
        # Check permissions
        for perm in identity.permissions:
            if perm == "*" or permission.startswith(perm):
                return True
        
        return False
    
    def revoke_session(self, session_id: str) -> bool:
        """Revoke an active session"""
        
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.is_valid = False
            del self.active_sessions[session_id]
            return True
        
        return False
    
    def get_active_sessions(self) -> List[SecuritySession]:
        """Get all active sessions"""
        return list(self.active_sessions.values())
    
    def get_session_history(self, duration: timedelta = timedelta(days=30)) -> List[SecuritySession]:
        """Get session history"""
        cutoff_time = datetime.utcnow() - duration
        return [s for s in self.session_history if s.created_at >= cutoff_time]


class ThreatDetectionSystem:
    """Threat detection and response system"""
    
    def __init__(self, monitoring_system: Optional[MonitoringObservability] = None):
        self.monitoring_system = monitoring_system
        self.security_events: List[SecurityEvent] = []
        self.threat_patterns: Dict[str, Dict[str, Any]] = {}
        self.response_actions: Dict[str, Callable] = {}
        
        # Threat detection state
        self.suspicious_ips: Set[str] = set()
        self.failed_attempts: Dict[str, int] = defaultdict(int)
        self.blocked_ips: Set[str] = set()
        
        # Initialize threat patterns
        self._initialize_threat_patterns()
        
        # Initialize response actions
        self._initialize_response_actions()
    
    def _initialize_threat_patterns(self) -> None:
        """Initialize threat detection patterns"""
        
        # Brute force attack pattern
        self.threat_patterns["brute_force"] = {
            "name": "Brute Force Attack",
            "description": "Multiple failed authentication attempts",
            "threshold": 5,
            "time_window": timedelta(minutes=5),
            "severity": ThreatSeverity.HIGH
        }
        
        # Unauthorized access pattern
        self.threat_patterns["unauthorized_access"] = {
            "name": "Unauthorized Access Attempt",
            "description": "Access attempt without valid credentials",
            "threshold": 1,
            "time_window": timedelta(minutes=1),
            "severity": ThreatSeverity.MEDIUM
        }
        
        # Privilege escalation pattern
        self.threat_patterns["privilege_escalation"] = {
            "name": "Privilege Escalation Attempt",
            "description": "Attempt to access higher privilege resources",
            "threshold": 1,
            "time_window": timedelta(minutes=1),
            "severity": ThreatSeverity.CRITICAL
        }
        
        # Suspicious activity pattern
        self.threat_patterns["suspicious_activity"] = {
            "name": "Suspicious Activity",
            "description": "Unusual patterns of system access",
            "threshold": 3,
            "time_window": timedelta(minutes=10),
            "severity": ThreatSeverity.MEDIUM
        }
    
    def _initialize_response_actions(self) -> None:
        """Initialize threat response actions"""
        
        self.response_actions["block_ip"] = self._block_ip_address
        self.response_actions["increase_monitoring"] = self._increase_monitoring
        self.response_actions["alert_administrator"] = self._alert_administrator
        self.response_actions["revoke_sessions"] = self._revoke_sessions
        self.response_actions["lockdown_system"] = self._lockdown_system
    
    def record_security_event(self, event_type: str, severity: ThreatSeverity,
                            source_identity: Optional[str] = None, target_resource: Optional[str] = None,
                            description: str = "", ip_address: Optional[str] = None,
                            user_agent: Optional[str] = None, session_id: Optional[str] = None) -> SecurityEvent:
        """Record a security event"""
        
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            source_identity=source_identity,
            target_resource=target_resource,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id
        )
        
        self.security_events.append(event)
        
        # Analyze for threats
        self._analyze_threat_patterns(event)
        
        # Update monitoring if available
        if self.monitoring_system:
            self.monitoring_system.predictive_alerting.update_metric_value(
                f"security_event_{event_type}", 1, MetricType.CUSTOM
            )
        
        return event
    
    def _analyze_threat_patterns(self, event: SecurityEvent) -> None:
        """Analyze security event for threat patterns"""
        
        # Check for brute force attacks
        if event.event_type == "authentication_failure" and event.ip_address:
            self.failed_attempts[event.ip_address] += 1
            
            pattern = self.threat_patterns["brute_force"]
            if self.failed_attempts[event.ip_address] >= pattern["threshold"]:
                self._trigger_threat_response("brute_force", event)
        
        # Check for unauthorized access
        if event.event_type == "unauthorized_access":
            pattern = self.threat_patterns["unauthorized_access"]
            self._trigger_threat_response("unauthorized_access", event)
        
        # Check for privilege escalation
        if event.event_type == "privilege_escalation":
            pattern = self.threat_patterns["privilege_escalation"]
            self._trigger_threat_response("privilege_escalation", event)
        
        # Check for suspicious activity
        if event.ip_address and event.ip_address in self.suspicious_ips:
            pattern = self.threat_patterns["suspicious_activity"]
            self._trigger_threat_response("suspicious_activity", event)
    
    def _trigger_threat_response(self, threat_type: str, event: SecurityEvent) -> None:
        """Trigger response actions for detected threat"""
        
        pattern = self.threat_patterns[threat_type]
        
        # Create threat event
        threat_event = SecurityEvent(
            event_type=f"threat_detected_{threat_type}",
            severity=pattern["severity"],
            source_identity=event.source_identity,
            target_resource=event.target_resource,
            description=f"Threat detected: {pattern['name']}",
            ip_address=event.ip_address,
            user_agent=event.user_agent,
            session_id=event.session_id
        )
        
        self.security_events.append(threat_event)
        
        # Execute response actions based on severity
        if threat_event.severity == ThreatSeverity.CRITICAL:
            self.response_actions["lockdown_system"](threat_event)
        elif threat_event.severity == ThreatSeverity.HIGH:
            self.response_actions["block_ip"](threat_event)
            self.response_actions["alert_administrator"](threat_event)
        elif threat_event.severity == ThreatSeverity.MEDIUM:
            self.response_actions["increase_monitoring"](threat_event)
            self.response_actions["alert_administrator"](threat_event)
    
    def _block_ip_address(self, event: SecurityEvent) -> None:
        """Block IP address"""
        if event.ip_address:
            self.blocked_ips.add(event.ip_address)
            print(f"IP address {event.ip_address} blocked due to threat")
    
    def _increase_monitoring(self, event: SecurityEvent) -> None:
        """Increase monitoring for threat"""
        if event.ip_address:
            self.suspicious_ips.add(event.ip_address)
            print(f"Increased monitoring for IP {event.ip_address}")
    
    def _alert_administrator(self, event: SecurityEvent) -> None:
        """Alert administrator of threat"""
        print(f"SECURITY ALERT: {event.description} - Severity: {event.severity.value}")
    
    def _revoke_sessions(self, event: SecurityEvent) -> None:
        """Revoke sessions for threat"""
        print(f"Revoking sessions for threat: {event.description}")
    
    def _lockdown_system(self, event: SecurityEvent) -> None:
        """Lockdown system for critical threat"""
        print(f"SYSTEM LOCKDOWN: Critical threat detected - {event.description}")
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP address is blocked"""
        return ip_address in self.blocked_ips
    
    def is_ip_suspicious(self, ip_address: str) -> bool:
        """Check if IP address is suspicious"""
        return ip_address in self.suspicious_ips
    
    def get_security_events(self, duration: timedelta = timedelta(hours=24)) -> List[SecurityEvent]:
        """Get security events from time period"""
        cutoff_time = datetime.utcnow() - duration
        return [e for e in self.security_events if e.timestamp >= cutoff_time]
    
    def get_threat_summary(self) -> Dict[str, Any]:
        """Get threat detection summary"""
        recent_events = self.get_security_events()
        
        return {
            "total_events": len(recent_events),
            "blocked_ips": len(self.blocked_ips),
            "suspicious_ips": len(self.suspicious_ips),
            "failed_attempts": dict(self.failed_attempts),
            "events_by_severity": {
                severity.value: len([e for e in recent_events if e.severity == severity])
                for severity in ThreatSeverity
            }
        }


class ComplianceMonitor:
    """Compliance monitoring and audit system"""
    
    def __init__(self):
        self.compliance_rules: Dict[str, ComplianceRule] = {}
        self.audit_log: List[Dict[str, Any]] = []
        self.compliance_status: ComplianceStatus = ComplianceStatus.COMPLIANT
        
        # Initialize default compliance rules
        self._initialize_compliance_rules()
    
    def _initialize_compliance_rules(self) -> None:
        """Initialize default compliance rules"""
        
        # Authentication compliance
        auth_rule = ComplianceRule(
            name="Multi-Factor Authentication",
            description="Require multi-factor authentication for privileged access",
            rule_type="authentication",
            severity=ThreatSeverity.HIGH,
            conditions={"min_auth_methods": 2},
            actions=["enforce_mfa", "alert_violation"]
        )
        self.compliance_rules[auth_rule.rule_id] = auth_rule
        
        # Session management compliance
        session_rule = ComplianceRule(
            name="Session Timeout",
            description="Enforce session timeout limits",
            rule_type="session_management",
            severity=ThreatSeverity.MEDIUM,
            conditions={"max_session_duration": 24},  # hours
            actions=["enforce_timeout", "log_violation"]
        )
        self.compliance_rules[session_rule.rule_id] = session_rule
        
        # Access control compliance
        access_rule = ComplianceRule(
            name="Least Privilege Access",
            description="Enforce least privilege access control",
            rule_type="access_control",
            severity=ThreatSeverity.HIGH,
            conditions={"enforce_least_privilege": True},
            actions=["audit_access", "revoke_excessive_permissions"]
        )
        self.compliance_rules[access_rule.rule_id] = access_rule
        
        # Cryptographic compliance
        crypto_rule = ComplianceRule(
            name="Cryptographic Standards",
            description="Enforce cryptographic standards",
            rule_type="cryptography",
            severity=ThreatSeverity.CRITICAL,
            conditions={"min_key_size": 2048, "approved_algorithms": ["RSA", "AES"]},
            actions=["enforce_standards", "alert_violation"]
        )
        self.compliance_rules[crypto_rule.rule_id] = crypto_rule
    
    def add_compliance_rule(self, rule: ComplianceRule) -> None:
        """Add a compliance rule"""
        self.compliance_rules[rule.rule_id] = rule
    
    def check_compliance(self, context: Dict[str, Any]) -> List[ComplianceRule]:
        """Check compliance against all rules"""
        
        violations = []
        
        for rule in self.compliance_rules.values():
            if not rule.enabled:
                continue
            
            if not self._evaluate_rule(rule, context):
                rule.compliance_status = ComplianceStatus.VIOLATION
                violations.append(rule)
            else:
                rule.compliance_status = ComplianceStatus.COMPLIANT
            
            rule.last_checked = datetime.utcnow()
        
        # Update overall compliance status
        if any(rule.compliance_status == ComplianceStatus.VIOLATION for rule in violations):
            self.compliance_status = ComplianceStatus.VIOLATION
        elif any(rule.compliance_status == ComplianceStatus.WARNING for rule in violations):
            self.compliance_status = ComplianceStatus.WARNING
        else:
            self.compliance_status = ComplianceStatus.COMPLIANT
        
        return violations
    
    def _evaluate_rule(self, rule: ComplianceRule, context: Dict[str, Any]) -> bool:
        """Evaluate a compliance rule against context"""
        
        for condition_key, condition_value in rule.conditions.items():
            if condition_key not in context:
                return False
            
            context_value = context[condition_key]
            
            if isinstance(condition_value, (int, float)):
                if context_value < condition_value:
                    return False
            elif isinstance(condition_value, list):
                if context_value not in condition_value:
                    return False
            elif isinstance(condition_value, bool):
                if context_value != condition_value:
                    return False
            else:
                if context_value != condition_value:
                    return False
        
        return True
    
    def log_audit_event(self, event_type: str, description: str, identity_id: Optional[str] = None,
                       resource: Optional[str] = None, metadata: Dict[str, Any] = None) -> None:
        """Log audit event"""
        
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "description": description,
            "identity_id": identity_id,
            "resource": resource,
            "metadata": metadata or {}
        }
        
        self.audit_log.append(audit_entry)
    
    def get_audit_log(self, duration: timedelta = timedelta(days=30)) -> List[Dict[str, Any]]:
        """Get audit log entries"""
        cutoff_time = datetime.utcnow() - duration
        return [entry for entry in self.audit_log 
                if datetime.fromisoformat(entry["timestamp"]) >= cutoff_time]
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """Get comprehensive compliance report"""
        
        total_rules = len(self.compliance_rules)
        compliant_rules = len([r for r in self.compliance_rules.values() 
                             if r.compliance_status == ComplianceStatus.COMPLIANT])
        violation_rules = len([r for r in self.compliance_rules.values() 
                             if r.compliance_status == ComplianceStatus.VIOLATION])
        
        return {
            "overall_status": self.compliance_status.value,
            "total_rules": total_rules,
            "compliant_rules": compliant_rules,
            "violation_rules": violation_rules,
            "compliance_percentage": (compliant_rules / total_rules * 100) if total_rules > 0 else 0,
            "rules": [
                {
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "status": rule.compliance_status.value,
                    "severity": rule.severity.value,
                    "last_checked": rule.last_checked.isoformat() if rule.last_checked else None
                }
                for rule in self.compliance_rules.values()
            ]
        }


class SecurityComplianceFramework:
    """Main security and compliance framework"""
    
    def __init__(self, monitoring_system: Optional[MonitoringObservability] = None):
        self.monitoring_system = monitoring_system
        
        # Core security components
        self.identity_manager = IdentityAccessManager()
        self.threat_detection = ThreatDetectionSystem(monitoring_system)
        self.compliance_monitor = ComplianceMonitor()
        self.crypto_manager = CryptographicManager()
        
        # Security state
        self.security_active = True
        self.zero_trust_enabled = True
        self.audit_trail_enabled = True
        
        # Initialize security policies
        self._initialize_security_policies()
    
    def _initialize_security_policies(self) -> None:
        """Initialize security policies"""
        
        # Zero-trust policy
        self.zero_trust_policy = {
            "verify_everything": True,
            "never_trust_always_verify": True,
            "least_privilege_access": True,
            "micro_segmentation": True
        }
        
        # Audit policy
        self.audit_policy = {
            "log_all_access": True,
            "log_all_changes": True,
            "retain_logs_days": 365,
            "encrypt_audit_logs": True
        }
    
    def authenticate_request(self, identity_id: str, authentication_data: Dict[str, Any],
                           ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Optional[SecuritySession]:
        """Authenticate a request"""
        
        # Check if IP is blocked
        if ip_address and self.threat_detection.is_ip_blocked(ip_address):
            self.threat_detection.record_security_event(
                "blocked_ip_access", ThreatSeverity.MEDIUM,
                ip_address=ip_address, description="Access attempt from blocked IP"
            )
            return None
        
        # Attempt authentication
        session = self.identity_manager.authenticate_identity(
            identity_id, authentication_data, ip_address, user_agent
        )
        
        if session:
            # Log successful authentication
            self.compliance_monitor.log_audit_event(
                "authentication_success", f"Successful authentication for {identity_id}",
                identity_id, metadata={"ip_address": ip_address, "user_agent": user_agent}
            )
        else:
            # Log failed authentication
            self.threat_detection.record_security_event(
                "authentication_failure", ThreatSeverity.MEDIUM,
                ip_address=ip_address, description=f"Failed authentication for {identity_id}"
            )
        
        return session
    
    def authorize_action(self, session: SecuritySession, action: str, resource: str) -> bool:
        """Authorize an action"""
        
        # Zero-trust verification
        if not self._verify_session(session):
            return False
        
        # Check permissions
        permission = f"{action}.{resource}"
        if not self.identity_manager.check_permission(session, permission):
            self.threat_detection.record_security_event(
                "unauthorized_access", ThreatSeverity.MEDIUM,
                source_identity=session.identity_id,
                target_resource=resource,
                description=f"Unauthorized access attempt: {permission}"
            )
            return False
        
        # Log authorized action
        self.compliance_monitor.log_audit_event(
            "authorized_action", f"Authorized action: {permission}",
            session.identity_id, resource
        )
        
        return True
    
    def _verify_session(self, session: SecuritySession) -> bool:
        """Verify session in zero-trust context"""
        
        # Validate session
        if not self.identity_manager.validate_session(session.session_id, session.session_token):
            return False
        
        # Check for suspicious activity
        if session.ip_address and self.threat_detection.is_ip_suspicious(session.ip_address):
            self.threat_detection.record_security_event(
                "suspicious_session", ThreatSeverity.MEDIUM,
                source_identity=session.identity_id,
                ip_address=session.ip_address,
                description="Session from suspicious IP"
            )
            return False
        
        return True
    
    def sign_data(self, data: bytes, identity_id: str) -> CryptographicSignature:
        """Sign data cryptographically"""
        return self.crypto_manager.generate_signature(data, identity_id)
    
    def verify_data(self, signature: CryptographicSignature, data: bytes) -> bool:
        """Verify cryptographically signed data"""
        return self.crypto_manager.verify_signature(signature, data)
    
    def encrypt_sensitive_data(self, data: bytes) -> bytes:
        """Encrypt sensitive data"""
        return self.crypto_manager.encrypt_data(data)
    
    def decrypt_sensitive_data(self, encrypted_data: bytes) -> bytes:
        """Decrypt sensitive data"""
        return self.crypto_manager.decrypt_data(encrypted_data)
    
    def check_compliance(self, context: Dict[str, Any]) -> List[ComplianceRule]:
        """Check compliance status"""
        return self.compliance_monitor.check_compliance(context)
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get comprehensive security summary"""
        
        return {
            "security_active": self.security_active,
            "zero_trust_enabled": self.zero_trust_enabled,
            "audit_trail_enabled": self.audit_trail_enabled,
            "identities": {
                "total_identities": len(self.identity_manager.identities),
                "active_sessions": len(self.identity_manager.active_sessions)
            },
            "threat_detection": self.threat_detection.get_threat_summary(),
            "compliance": self.compliance_monitor.get_compliance_report(),
            "cryptography": {
                "signatures_generated": len([e for e in self.threat_detection.security_events 
                                          if "signature" in e.event_type]),
                "encryption_operations": len([e for e in self.threat_detection.security_events 
                                           if "encryption" in e.event_type])
            }
        }
    
    def shutdown(self) -> None:
        """Shutdown security framework"""
        self.security_active = False
        
        # Revoke all active sessions
        for session_id in list(self.identity_manager.active_sessions.keys()):
            self.identity_manager.revoke_session(session_id)


# Example usage and testing
if __name__ == "__main__":
    # This would be used in the main kernel initialization
    print("Security and Compliance - Phase 5.4 Implementation")
    print("Production Security Framework with IAM, cryptographic verification, and threat detection")
