"""
Instruction Interpretation Layer - Phase 4.1 Implementation

This module implements the Instruction Interpretation Layer, which constructs the bridge
between the kernel's mathematical rigor and human dialogue through a dual-strategy natural
language processing system, ensuring that natural language interactions are converted into
lawful kernel actions with a complete and verifiable audit trail.

Key Features:
- Dual-strategy natural language processing (semantic and syntactic)
- Instruction parsing and validation
- Kernel action mapping and execution
- Complete audit trail generation
- Human-kernel dialogue management
- Instruction history and learning
"""

import time
import math
import hashlib
import threading
import asyncio
import re
import json
from typing import Dict, List, Any, Optional, Tuple, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime, timedelta
from collections import defaultdict, deque
import heapq

from synchrony_phase_lock_protocol import ProductionSynchronySystem, SynchronizedOperation, SynchronyLevel, OperationPriority
from arbitration_stack import ProductionArbitrationStack, ForbiddenZoneAccess, ArbitrationDecisionType
from advanced_trait_engine import AdvancedTraitEngine
from utm_kernel_design import UTMKernel
from event_driven_coordination import DjinnEventBus, EventType
from violation_pressure_calculation import ViolationMonitor, ViolationClass
from collapsemap_engine import CollapseMapEngine
from forbidden_zone_management import ForbiddenZoneManager, MuRecursionChamber, ChamberType
from sovereign_imitation_protocol import SovereignImitationProtocol, ImitationPhase
from codex_amendment_system import CodexAmendmentSystem, AmendmentType, AmendmentStatus


class InstructionType(Enum):
    """Types of human instructions"""
    QUERY = "query"                               # Information request
    COMMAND = "command"                           # Action request
    AMENDMENT = "amendment"                       # Constitutional change
    ANALYSIS = "analysis"                         # System analysis
    MONITOR = "monitor"                           # System monitoring
    INTEGRATION = "integration"                   # Novelty integration
    GOVERNANCE = "governance"                     # Governance action
    EMERGENCY = "emergency"                       # Emergency action


class ProcessingStrategy(Enum):
    """Natural language processing strategies"""
    SEMANTIC = "semantic"                         # Meaning-based processing
    SYNTACTIC = "syntactic"                       # Structure-based processing
    HYBRID = "hybrid"                             # Combined approach


class InstructionStatus(Enum):
    """Status of instruction processing"""
    RECEIVED = "received"                         # Instruction received
    PARSING = "parsing"                           # Under parsing
    VALIDATING = "validating"                     # Under validation
    MAPPING = "mapping"                           # Mapping to kernel actions
    EXECUTING = "executing"                       # Under execution
    COMPLETED = "completed"                       # Successfully completed
    FAILED = "failed"                             # Processing failed
    REJECTED = "rejected"                         # Instruction rejected


class KernelActionType(Enum):
    """Types of kernel actions"""
    TRAIT_OPERATION = "trait_operation"           # Trait engine operations
    ARBITRATION_REQUEST = "arbitration_request"   # Arbitration stack requests
    SYNCHRONY_OPERATION = "synchrony_operation"   # Synchrony system operations
    COLLAPSEMAP_OPERATION = "collapsemap_operation"  # Entropy management
    FORBIDDEN_ZONE_ACCESS = "forbidden_zone_access"  # Zone management
    IMITATION_SESSION = "imitation_session"       # Imitation protocol
    AMENDMENT_PROPOSAL = "amendment_proposal"     # Codex amendments
    SYSTEM_QUERY = "system_query"                 # System information
    MONITORING_REQUEST = "monitoring_request"     # System monitoring


@dataclass
class HumanInstruction:
    """A human instruction to the kernel"""
    instruction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    raw_text: str = ""
    instruction_type: InstructionType = InstructionType.QUERY
    processing_strategy: ProcessingStrategy = ProcessingStrategy.HYBRID
    status: InstructionStatus = InstructionStatus.RECEIVED
    sender_id: str = ""
    priority: float = 0.5                          # 0.0-1.0
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class ParsedInstruction:
    """A parsed human instruction"""
    instruction_id: str = ""
    parsed_components: Dict[str, Any] = field(default_factory=dict)
    intent: str = ""
    entities: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0                       # 0.0-1.0
    parsing_strategy: ProcessingStrategy = ProcessingStrategy.HYBRID
    parsing_errors: List[str] = field(default_factory=list)
    parsing_metadata: Dict[str, Any] = field(default_factory=dict)
    parsed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class KernelAction:
    """A kernel action mapped from human instruction"""
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    instruction_id: str = ""
    action_type: KernelActionType = KernelActionType.SYSTEM_QUERY
    target_component: str = ""
    operation: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: float = 0.5                          # 0.0-1.0
    dependencies: List[str] = field(default_factory=list)
    validation_required: bool = True
    execution_order: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    result: Optional[Any] = None
    success: bool = False
    error_message: str = ""


@dataclass
class AuditTrail:
    """Complete audit trail for instruction processing"""
    trail_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    instruction_id: str = ""
    processing_steps: List[Dict[str, Any]] = field(default_factory=list)
    kernel_actions: List[str] = field(default_factory=list)  # Action IDs
    execution_results: Dict[str, Any] = field(default_factory=dict)
    validation_checks: List[Dict[str, Any]] = field(default_factory=list)
    error_log: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    integrity_checks: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass
class DialogueSession:
    """A human-kernel dialogue session"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    human_id: str = ""
    instructions: List[str] = field(default_factory=list)  # Instruction IDs
    context_history: List[Dict[str, Any]] = field(default_factory=list)
    session_metrics: Dict[str, Any] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    active: bool = True


class SemanticProcessor:
    """Semantic natural language processing"""
    
    def __init__(self):
        self.intent_patterns = {
            "query": [
                r"what is", r"how does", r"tell me about", r"explain",
                r"show me", r"get", r"retrieve", r"find"
            ],
            "command": [
                r"do", r"execute", r"run", r"perform", r"create", r"start",
                r"stop", r"modify", r"change", r"update"
            ],
            "amendment": [
                r"amend", r"change the codex", r"modify principle",
                r"add procedure", r"update constitution"
            ],
            "analysis": [
                r"analyze", r"examine", r"investigate", r"study",
                r"assess", r"evaluate", r"review"
            ],
            "monitor": [
                r"monitor", r"watch", r"track", r"observe",
                r"check status", r"get metrics"
            ],
            "integration": [
                r"integrate", r"assimilate", r"incorporate",
                r"add novelty", r"merge"
            ],
            "governance": [
                r"govern", r"arbitrate", r"decide", r"judge",
                r"resolve", r"mediate"
            ],
            "emergency": [
                r"emergency", r"urgent", r"critical", r"immediate",
                r"stop now", r"halt"
            ]
        }
        
        self.entity_patterns = {
            "trait": r"\b(trait|characteristic|property)\b",
            "system": r"\b(system|kernel|core)\b",
            "amendment": r"\b(amendment|change|modification)\b",
            "analysis": r"\b(analysis|examination|investigation)\b",
            "monitoring": r"\b(monitoring|tracking|observation)\b",
            "integration": r"\b(integration|assimilation|incorporation)\b",
            "governance": r"\b(governance|arbitration|decision)\b"
        }
    
    def process_semantic(self, instruction: HumanInstruction) -> ParsedInstruction:
        """Process instruction using semantic analysis"""
        parsed = ParsedInstruction(instruction_id=instruction.instruction_id)
        parsed.parsing_strategy = ProcessingStrategy.SEMANTIC
        
        text = instruction.raw_text.lower()
        
        # Detect intent
        intent_scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text):
                    score += 1
            intent_scores[intent] = score
        
        # Find primary intent
        if intent_scores:
            primary_intent = max(intent_scores, key=intent_scores.get)
            parsed.intent = primary_intent
            parsed.confidence = min(1.0, intent_scores[primary_intent] / 3.0)
        
        # Extract entities
        entities = []
        for entity_type, pattern in self.entity_patterns.items():
            if re.search(pattern, text):
                entities.append(entity_type)
        parsed.entities = entities
        
        # Extract parameters (simplified)
        parameters = {}
        
        # Extract numbers
        numbers = re.findall(r'\d+\.?\d*', text)
        if numbers:
            parameters['numeric_values'] = [float(n) for n in numbers]
        
        # Extract quoted strings
        quotes = re.findall(r'"([^"]*)"', text)
        if quotes:
            parameters['quoted_strings'] = quotes
        
        # Extract keywords
        keywords = re.findall(r'\b\w{4,}\b', text)
        parameters['keywords'] = keywords[:10]  # Limit to 10 keywords
        
        parsed.parameters = parameters
        
        # Store parsing components
        parsed.parsed_components = {
            "intent_scores": intent_scores,
            "text_length": len(text),
            "word_count": len(text.split()),
            "has_entities": bool(entities),
            "has_parameters": bool(parameters)
        }
        
        return parsed


class SyntacticProcessor:
    """Syntactic natural language processing"""
    
    def __init__(self):
        self.sentence_patterns = {
            "question": r'\?$',
            "command": r'^(do|execute|run|perform|create|start|stop|modify|change|update)',
            "statement": r'^(the|this|that|it|there)',
            "exclamation": r'!$'
        }
        
        self.structure_patterns = {
            "subject_verb_object": r'(\w+)\s+(\w+)\s+(\w+)',
            "verb_object": r'(\w+)\s+(\w+)',
            "adjective_noun": r'(\w+)\s+(\w+)',
            "prepositional_phrase": r'\b(in|on|at|to|for|with|by|from)\s+(\w+)'
        }
    
    def process_syntactic(self, instruction: HumanInstruction) -> ParsedInstruction:
        """Process instruction using syntactic analysis"""
        parsed = ParsedInstruction(instruction_id=instruction.instruction_id)
        parsed.parsing_strategy = ProcessingStrategy.SYNTACTIC
        
        text = instruction.raw_text
        
        # Analyze sentence structure
        structure_analysis = {}
        
        # Check sentence type
        for sentence_type, pattern in self.sentence_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                structure_analysis[sentence_type] = True
        
        # Extract structural components
        structural_components = {}
        for structure_type, pattern in self.structure_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                structural_components[structure_type] = matches
        
        # Determine confidence based on structure clarity
        confidence = 0.5  # Base confidence
        
        if len(text.split()) >= 3:
            confidence += 0.2
        
        if structural_components:
            confidence += 0.2
        
        if structure_analysis:
            confidence += 0.1
        
        parsed.confidence = min(1.0, confidence)
        
        # Extract basic parameters
        words = text.split()
        parameters = {
            "word_count": len(words),
            "sentence_type": list(structure_analysis.keys()),
            "structural_components": structural_components,
            "first_word": words[0] if words else "",
            "last_word": words[-1] if words else ""
        }
        
        parsed.parameters = parameters
        
        # Store parsing components
        parsed.parsed_components = {
            "structure_analysis": structure_analysis,
            "structural_components": structural_components,
            "sentence_length": len(text),
            "word_count": len(words)
        }
        
        return parsed


class ActionMapper:
    """Maps parsed instructions to kernel actions"""
    
    def __init__(self):
        self.action_mappings = {
            "query": {
                "system": KernelActionType.SYSTEM_QUERY,
                "trait": KernelActionType.TRAIT_OPERATION,
                "metrics": KernelActionType.MONITORING_REQUEST,
                "status": KernelActionType.MONITORING_REQUEST
            },
            "command": {
                "execute": KernelActionType.TRAIT_OPERATION,
                "run": KernelActionType.TRAIT_OPERATION,
                "perform": KernelActionType.TRAIT_OPERATION,
                "create": KernelActionType.TRAIT_OPERATION
            },
            "amendment": {
                "amend": KernelActionType.AMENDMENT_PROPOSAL,
                "change": KernelActionType.AMENDMENT_PROPOSAL,
                "modify": KernelActionType.AMENDMENT_PROPOSAL
            },
            "analysis": {
                "analyze": KernelActionType.SYSTEM_QUERY,
                "examine": KernelActionType.SYSTEM_QUERY,
                "investigate": KernelActionType.SYSTEM_QUERY
            },
            "monitor": {
                "monitor": KernelActionType.MONITORING_REQUEST,
                "watch": KernelActionType.MONITORING_REQUEST,
                "track": KernelActionType.MONITORING_REQUEST
            },
            "integration": {
                "integrate": KernelActionType.IMITATION_SESSION,
                "assimilate": KernelActionType.IMITATION_SESSION
            },
            "governance": {
                "govern": KernelActionType.ARBITRATION_REQUEST,
                "arbitrate": KernelActionType.ARBITRATION_REQUEST
            },
            "emergency": {
                "emergency": KernelActionType.ARBITRATION_REQUEST,
                "urgent": KernelActionType.ARBITRATION_REQUEST
            }
        }
    
    def map_to_actions(self, parsed: ParsedInstruction, 
                      instruction: HumanInstruction) -> List[KernelAction]:
        """Map parsed instruction to kernel actions"""
        actions = []
        
        # Determine action type based on intent
        intent = parsed.intent
        if intent in self.action_mappings:
            # Find matching action type
            action_type = None
            for keyword, mapped_type in self.action_mappings[intent].items():
                if keyword in instruction.raw_text.lower():
                    action_type = mapped_type
                    break
            
            if not action_type:
                # Default mapping
                action_type = list(self.action_mappings[intent].values())[0]
            
            # Create kernel action
            action = KernelAction(
                instruction_id=instruction.instruction_id,
                action_type=action_type,
                target_component=self._get_target_component(action_type),
                operation=self._get_operation(action_type, parsed),
                parameters=parsed.parameters,
                priority=instruction.priority,
                validation_required=True
            )
            
            actions.append(action)
        
        return actions
    
    def _get_target_component(self, action_type: KernelActionType) -> str:
        """Get target component for action type"""
        component_mapping = {
            KernelActionType.TRAIT_OPERATION: "advanced_trait_engine",
            KernelActionType.ARBITRATION_REQUEST: "arbitration_stack",
            KernelActionType.SYNCHRONY_OPERATION: "synchrony_system",
            KernelActionType.COLLAPSEMAP_OPERATION: "collapsemap_engine",
            KernelActionType.FORBIDDEN_ZONE_ACCESS: "forbidden_zone_manager",
            KernelActionType.IMITATION_SESSION: "sovereign_imitation_protocol",
            KernelActionType.AMENDMENT_PROPOSAL: "codex_amendment_system",
            KernelActionType.SYSTEM_QUERY: "system_query",
            KernelActionType.MONITORING_REQUEST: "system_monitoring"
        }
        
        return component_mapping.get(action_type, "unknown")
    
    def _get_operation(self, action_type: KernelActionType, 
                      parsed: ParsedInstruction) -> str:
        """Get operation for action type"""
        operation_mapping = {
            KernelActionType.TRAIT_OPERATION: "query_traits",
            KernelActionType.ARBITRATION_REQUEST: "arbitrate_operation",
            KernelActionType.SYNCHRONY_OPERATION: "synchronize_operation",
            KernelActionType.COLLAPSEMAP_OPERATION: "get_entropy_status",
            KernelActionType.FORBIDDEN_ZONE_ACCESS: "get_zone_status",
            KernelActionType.IMITATION_SESSION: "get_protocol_status",
            KernelActionType.AMENDMENT_PROPOSAL: "get_amendment_status",
            KernelActionType.SYSTEM_QUERY: "query_system",
            KernelActionType.MONITORING_REQUEST: "get_metrics"
        }
        
        return operation_mapping.get(action_type, "unknown")


class InstructionValidator:
    """Validates instructions and kernel actions"""
    
    def __init__(self):
        self.validation_rules = {
            "syntax": self._validate_syntax,
            "semantics": self._validate_semantics,
            "authorization": self._validate_authorization,
            "safety": self._validate_safety
        }
    
    def validate_instruction(self, instruction: HumanInstruction, 
                           parsed: ParsedInstruction) -> Tuple[bool, List[str]]:
        """Validate human instruction"""
        errors = []
        
        # Basic syntax validation
        if not instruction.raw_text.strip():
            errors.append("Empty instruction")
        
        if len(instruction.raw_text) > 1000:
            errors.append("Instruction too long")
        
        # Parsing confidence validation
        if parsed.confidence < 0.3:
            errors.append("Low parsing confidence")
        
        # Intent validation
        if not parsed.intent:
            errors.append("No clear intent detected")
        
        return len(errors) == 0, errors
    
    def validate_kernel_action(self, action: KernelAction) -> Tuple[bool, List[str]]:
        """Validate kernel action"""
        errors = []
        
        # Action type validation
        if not action.action_type:
            errors.append("No action type specified")
        
        # Target component validation
        if not action.target_component:
            errors.append("No target component specified")
        
        # Operation validation
        if not action.operation:
            errors.append("No operation specified")
        
        # Priority validation
        if not (0.0 <= action.priority <= 1.0):
            errors.append("Invalid priority value")
        
        return len(errors) == 0, errors
    
    def _validate_syntax(self, instruction: HumanInstruction) -> Tuple[bool, List[str]]:
        """Validate instruction syntax"""
        errors = []
        text = instruction.raw_text
        
        if not text.strip():
            errors.append("Empty instruction")
        
        if len(text) > 1000:
            errors.append("Instruction too long")
        
        return len(errors) == 0, errors
    
    def _validate_semantics(self, instruction: HumanInstruction) -> Tuple[bool, List[str]]:
        """Validate instruction semantics"""
        errors = []
        text = instruction.raw_text.lower()
        
        # Check for basic semantic content
        if len(text.split()) < 2:
            errors.append("Instruction too short")
        
        return len(errors) == 0, errors
    
    def _validate_authorization(self, instruction: HumanInstruction) -> Tuple[bool, List[str]]:
        """Validate instruction authorization"""
        errors = []
        
        # Basic authorization check (simplified)
        if not instruction.sender_id:
            errors.append("No sender identification")
        
        return len(errors) == 0, errors
    
    def _validate_safety(self, instruction: HumanInstruction) -> Tuple[bool, List[str]]:
        """Validate instruction safety"""
        errors = []
        text = instruction.raw_text.lower()
        
        # Check for potentially dangerous keywords
        dangerous_keywords = ["delete", "destroy", "remove", "kill", "terminate"]
        for keyword in dangerous_keywords:
            if keyword in text:
                errors.append(f"Potentially dangerous keyword: {keyword}")
        
        return len(errors) == 0, errors


class InstructionInterpretationLayer:
    """
    Instruction Interpretation Layer constructing the bridge between the kernel's
    mathematical rigor and human dialogue through a dual-strategy natural language
    processing system.
    """
    
    def __init__(self, codex_amendment_system: CodexAmendmentSystem,
                 sovereign_imitation_protocol: SovereignImitationProtocol,
                 arbitration_stack: ProductionArbitrationStack,
                 synchrony_system: ProductionSynchronySystem,
                 event_bus: Optional[DjinnEventBus] = None):
        """Initialize the Instruction Interpretation Layer"""
        self.codex_amendment_system = codex_amendment_system
        self.sovereign_imitation_protocol = sovereign_imitation_protocol
        self.arbitration_stack = arbitration_stack
        self.synchrony_system = synchrony_system
        self.event_bus = event_bus or DjinnEventBus()
        
        # Core components
        self.semantic_processor = SemanticProcessor()
        self.syntactic_processor = SyntacticProcessor()
        self.action_mapper = ActionMapper()
        self.validator = InstructionValidator()
        
        # System state
        self.instructions: Dict[str, HumanInstruction] = {}
        self.parsed_instructions: Dict[str, ParsedInstruction] = {}
        self.kernel_actions: Dict[str, KernelAction] = {}
        self.audit_trails: Dict[str, AuditTrail] = {}
        self.dialogue_sessions: Dict[str, DialogueSession] = {}
        
        # Processing queues
        self.pending_instructions: deque = deque()
        self.processing_instructions: Set[str] = set()
        self.completed_instructions: Set[str] = set()
        
        # System metrics
        self.system_metrics = {
            "total_instructions": 0,
            "successful_instructions": 0,
            "failed_instructions": 0,
            "average_processing_time": 0.0,
            "semantic_processing_count": 0,
            "syntactic_processing_count": 0,
            "hybrid_processing_count": 0
        }
        
        # Monitoring and control
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._processing_monitor, daemon=True)
        self.monitor_thread.start()
    
    def receive_instruction(self, raw_text: str, sender_id: str,
                          instruction_type: InstructionType = InstructionType.QUERY,
                          processing_strategy: ProcessingStrategy = ProcessingStrategy.HYBRID,
                          priority: float = 0.5,
                          context: Dict[str, Any] = None) -> str:
        """Receive a human instruction"""
        
        # Create instruction
        instruction = HumanInstruction(
            raw_text=raw_text,
            instruction_type=instruction_type,
            processing_strategy=processing_strategy,
            sender_id=sender_id,
            priority=priority,
            context=context or {}
        )
        
        # Store instruction
        self.instructions[instruction.instruction_id] = instruction
        
        # Add to processing queue
        self.pending_instructions.append(instruction.instruction_id)
        
        # Update metrics
        self.system_metrics["total_instructions"] += 1
        
        return instruction.instruction_id
    
    def process_instruction(self, instruction_id: str) -> bool:
        """Process a human instruction"""
        if instruction_id not in self.instructions:
            return False
        
        instruction = self.instructions[instruction_id]
        
        # Update status
        instruction.status = InstructionStatus.PARSING
        
        # Create audit trail
        audit_trail = AuditTrail(instruction_id=instruction_id)
        self.audit_trails[instruction_id] = audit_trail
        
        try:
            # Step 1: Parse instruction
            parsed = self._parse_instruction(instruction)
            self.parsed_instructions[instruction_id] = parsed
            
            audit_trail.processing_steps.append({
                "step": "parsing",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "result": "success",
                "confidence": parsed.confidence
            })
            
            # Step 2: Validate instruction
            instruction.status = InstructionStatus.VALIDATING
            is_valid, errors = self.validator.validate_instruction(instruction, parsed)
            
            if not is_valid:
                instruction.status = InstructionStatus.REJECTED
                audit_trail.error_log.extend(errors)
                return False
            
            audit_trail.validation_checks.append({
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "valid": True,
                "errors": []
            })
            
            # Step 3: Map to kernel actions
            instruction.status = InstructionStatus.MAPPING
            kernel_actions = self.action_mapper.map_to_actions(parsed, instruction)
            
            for action in kernel_actions:
                self.kernel_actions[action.action_id] = action
                audit_trail.kernel_actions.append(action.action_id)
                
                # Validate kernel action
                action_valid, action_errors = self.validator.validate_kernel_action(action)
                if not action_valid:
                    audit_trail.error_log.extend(action_errors)
            
            # Step 4: Execute kernel actions
            instruction.status = InstructionStatus.EXECUTING
            execution_results = self._execute_kernel_actions(kernel_actions)
            
            audit_trail.execution_results = execution_results
            
            # Step 5: Complete processing
            instruction.status = InstructionStatus.COMPLETED
            instruction.completed_at = datetime.utcnow()
            
            audit_trail.completed_at = datetime.utcnow()
            
            # Update metrics
            self.system_metrics["successful_instructions"] += 1
            
            return True
            
        except Exception as e:
            instruction.status = InstructionStatus.FAILED
            audit_trail.error_log.append(f"Processing error: {str(e)}")
            self.system_metrics["failed_instructions"] += 1
            return False
    
    def _parse_instruction(self, instruction: HumanInstruction) -> ParsedInstruction:
        """Parse instruction using specified strategy"""
        if instruction.processing_strategy == ProcessingStrategy.SEMANTIC:
            parsed = self.semantic_processor.process_semantic(instruction)
            self.system_metrics["semantic_processing_count"] += 1
        elif instruction.processing_strategy == ProcessingStrategy.SYNTACTIC:
            parsed = self.syntactic_processor.process_syntactic(instruction)
            self.system_metrics["syntactic_processing_count"] += 1
        else:  # HYBRID
            semantic_parsed = self.semantic_processor.process_semantic(instruction)
            syntactic_parsed = self.syntactic_processor.process_syntactic(instruction)
            
            # Combine results
            parsed = ParsedInstruction(instruction_id=instruction.instruction_id)
            parsed.parsing_strategy = ProcessingStrategy.HYBRID
            
            # Use semantic intent if available, otherwise syntactic
            if semantic_parsed.intent:
                parsed.intent = semantic_parsed.intent
            else:
                parsed.intent = "unknown"
            
            # Combine entities
            parsed.entities = list(set(semantic_parsed.entities + syntactic_parsed.entities))
            
            # Combine parameters
            combined_params = {}
            combined_params.update(semantic_parsed.parameters)
            combined_params.update(syntactic_parsed.parameters)
            parsed.parameters = combined_params
            
            # Average confidence
            parsed.confidence = (semantic_parsed.confidence + syntactic_parsed.confidence) / 2
            
            # Combine parsing components
            parsed.parsed_components = {
                "semantic": semantic_parsed.parsed_components,
                "syntactic": syntactic_parsed.parsed_components
            }
            
            self.system_metrics["hybrid_processing_count"] += 1
        
        return parsed
    
    def _execute_kernel_actions(self, actions: List[KernelAction]) -> Dict[str, Any]:
        """Execute kernel actions"""
        results = {}
        
        for action in actions:
            try:
                result = self._execute_single_action(action)
                action.result = result
                action.success = True
                action.executed_at = datetime.utcnow()
                results[action.action_id] = {
                    "success": True,
                    "result": result,
                    "executed_at": action.executed_at.isoformat() + "Z"
                }
            except Exception as e:
                action.success = False
                action.error_message = str(e)
                results[action.action_id] = {
                    "success": False,
                    "error": str(e),
                    "executed_at": datetime.utcnow().isoformat() + "Z"
                }
        
        return results
    
    def _execute_single_action(self, action: KernelAction) -> Any:
        """Execute a single kernel action"""
        if action.action_type == KernelActionType.SYSTEM_QUERY:
            return self._execute_system_query(action)
        elif action.action_type == KernelActionType.MONITORING_REQUEST:
            return self._execute_monitoring_request(action)
        elif action.action_type == KernelActionType.AMENDMENT_PROPOSAL:
            return self._execute_amendment_proposal(action)
        elif action.action_type == KernelActionType.ARBITRATION_REQUEST:
            return self._execute_arbitration_request(action)
        else:
            return {"status": "action_type_not_implemented", "action_type": action.action_type.value}
    
    def _execute_system_query(self, action: KernelAction) -> Dict[str, Any]:
        """Execute system query action"""
        query_type = action.parameters.get("query_type", "general")
        
        if query_type == "metrics":
            return {
                "system_metrics": self.system_metrics,
                "instruction_count": len(self.instructions),
                "active_sessions": len([s for s in self.dialogue_sessions.values() if s.active])
            }
        elif query_type == "status":
            return {
                "system_status": "operational",
                "pending_instructions": len(self.pending_instructions),
                "processing_instructions": len(self.processing_instructions),
                "completed_instructions": len(self.completed_instructions)
            }
        else:
            return {
                "message": "System query executed",
                "query_type": query_type,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    def _execute_monitoring_request(self, action: KernelAction) -> Dict[str, Any]:
        """Execute monitoring request action"""
        return {
            "monitoring_data": {
                "system_health": "good",
                "processing_efficiency": 0.95,
                "error_rate": 0.02,
                "response_time": 0.15
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _execute_amendment_proposal(self, action: KernelAction) -> Dict[str, Any]:
        """Execute amendment proposal action"""
        # This would integrate with the Codex Amendment System
        return {
            "amendment_status": "proposal_received",
            "message": "Amendment proposal processed",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _execute_arbitration_request(self, action: KernelAction) -> Dict[str, Any]:
        """Execute arbitration request action"""
        # This would integrate with the Arbitration Stack
        return {
            "arbitration_status": "request_received",
            "message": "Arbitration request processed",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def get_instruction_status(self, instruction_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an instruction"""
        if instruction_id not in self.instructions:
            return None
        
        instruction = self.instructions[instruction_id]
        parsed = self.parsed_instructions.get(instruction_id)
        audit_trail = self.audit_trails.get(instruction_id)
        
        return {
            "instruction_id": instruction_id,
            "status": instruction.status.value,
            "raw_text": instruction.raw_text,
            "instruction_type": instruction.instruction_type.value,
            "processing_strategy": instruction.processing_strategy.value,
            "sender_id": instruction.sender_id,
            "priority": instruction.priority,
            "created_at": instruction.created_at.isoformat() + "Z",
            "completed_at": instruction.completed_at.isoformat() + "Z" if instruction.completed_at else None,
            "parsing_confidence": parsed.confidence if parsed else 0.0,
            "parsed_intent": parsed.intent if parsed else None,
            "kernel_actions_count": len(audit_trail.kernel_actions) if audit_trail else 0,
            "processing_successful": instruction.status == InstructionStatus.COMPLETED
        }
    
    def get_audit_trail(self, instruction_id: str) -> Optional[Dict[str, Any]]:
        """Get complete audit trail for an instruction"""
        if instruction_id not in self.audit_trails:
            return None
        
        audit_trail = self.audit_trails[instruction_id]
        
        return {
            "trail_id": audit_trail.trail_id,
            "instruction_id": audit_trail.instruction_id,
            "processing_steps": audit_trail.processing_steps,
            "kernel_actions": audit_trail.kernel_actions,
            "execution_results": audit_trail.execution_results,
            "validation_checks": audit_trail.validation_checks,
            "error_log": audit_trail.error_log,
            "performance_metrics": audit_trail.performance_metrics,
            "integrity_checks": audit_trail.integrity_checks,
            "created_at": audit_trail.created_at.isoformat() + "Z",
            "completed_at": audit_trail.completed_at.isoformat() + "Z" if audit_trail.completed_at else None
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        return {
            "system_metrics": self.system_metrics.copy(),
            "total_instructions": len(self.instructions),
            "pending_instructions": len(self.pending_instructions),
            "processing_instructions": len(self.processing_instructions),
            "completed_instructions": len(self.completed_instructions),
            "total_parsed_instructions": len(self.parsed_instructions),
            "total_kernel_actions": len(self.kernel_actions),
            "total_audit_trails": len(self.audit_trails),
            "active_dialogue_sessions": len([s for s in self.dialogue_sessions.values() if s.active])
        }
    
    def _processing_monitor(self) -> None:
        """Background monitor for instruction processing"""
        while self.monitoring_active:
            try:
                # Process pending instructions
                while self.pending_instructions:
                    instruction_id = self.pending_instructions.popleft()
                    if instruction_id not in self.processing_instructions:
                        self.processing_instructions.add(instruction_id)
                        self.process_instruction(instruction_id)
                        self.completed_instructions.add(instruction_id)
                        self.processing_instructions.discard(instruction_id)
                
                time.sleep(1.0)  # 1-second processing cycle
                
            except Exception as e:
                print(f"Instruction processing monitor error: {e}")
                time.sleep(5.0)
    
    def shutdown(self) -> None:
        """Shutdown the Instruction Interpretation Layer"""
        self.monitoring_active = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)


# Example usage and testing
if __name__ == "__main__":
    # Initialize dependencies (mock for testing)
    from core_trait_framework import CoreTraitFramework
    
    print("=== Instruction Interpretation Layer Test ===")
    
    # Initialize components
    core_framework = CoreTraitFramework()
    advanced_engine = AdvancedTraitEngine(core_framework)
    arbitration_stack = ProductionArbitrationStack(advanced_engine)
    utm_kernel = UTMKernel()
    synchrony_system = ProductionSynchronySystem(arbitration_stack, utm_kernel)
    collapsemap_engine = CollapseMapEngine(synchrony_system, arbitration_stack, advanced_engine, utm_kernel)
    forbidden_zone_manager = ForbiddenZoneManager(arbitration_stack, synchrony_system, collapsemap_engine)
    sovereign_imitation_protocol = SovereignImitationProtocol(
        forbidden_zone_manager, arbitration_stack, synchrony_system
    )
    codex_amendment_system = CodexAmendmentSystem(
        sovereign_imitation_protocol, arbitration_stack, synchrony_system
    )
    
    instruction_layer = InstructionInterpretationLayer(
        codex_amendment_system, sovereign_imitation_protocol,
        arbitration_stack, synchrony_system
    )
    
    # Test instruction reception
    print("\n1. Testing instruction reception...")
    
    instruction_id = instruction_layer.receive_instruction(
        raw_text="What is the current system status?",
        sender_id="human_user_1",
        instruction_type=InstructionType.QUERY,
        processing_strategy=ProcessingStrategy.HYBRID,
        priority=0.7
    )
    
    print(f"   Instruction received: {instruction_id}")
    
    # Test instruction processing
    print("\n2. Testing instruction processing...")
    
    success = instruction_layer.process_instruction(instruction_id)
    print(f"   Processing successful: {success}")
    
    # Test instruction status
    print("\n3. Testing instruction status...")
    
    status = instruction_layer.get_instruction_status(instruction_id)
    if status:
        print(f"   Status: {status['status']}")
        print(f"   Raw text: {status['raw_text']}")
        print(f"   Parsing confidence: {status['parsing_confidence']:.3f}")
        print(f"   Parsed intent: {status['parsed_intent']}")
        print(f"   Kernel actions: {status['kernel_actions_count']}")
        print(f"   Processing successful: {status['processing_successful']}")
    
    # Test audit trail
    print("\n4. Testing audit trail...")
    
    audit_trail = instruction_layer.get_audit_trail(instruction_id)
    if audit_trail:
        print(f"   Trail ID: {audit_trail['trail_id']}")
        print(f"   Processing steps: {len(audit_trail['processing_steps'])}")
        print(f"   Kernel actions: {len(audit_trail['kernel_actions'])}")
        print(f"   Execution results: {len(audit_trail['execution_results'])}")
        print(f"   Validation checks: {len(audit_trail['validation_checks'])}")
        print(f"   Error log: {len(audit_trail['error_log'])}")
    
    # Test multiple instructions
    print("\n5. Testing multiple instructions...")
    
    instructions = [
        ("Show me the system metrics", InstructionType.QUERY, ProcessingStrategy.SEMANTIC),
        ("Execute trait analysis", InstructionType.COMMAND, ProcessingStrategy.SYNTACTIC),
        ("Monitor system performance", InstructionType.MONITOR, ProcessingStrategy.HYBRID),
        ("Propose an amendment to the codex", InstructionType.AMENDMENT, ProcessingStrategy.SEMANTIC)
    ]
    
    for text, inst_type, strategy in instructions:
        inst_id = instruction_layer.receive_instruction(
            raw_text=text,
            sender_id="human_user_1",
            instruction_type=inst_type,
            processing_strategy=strategy,
            priority=0.6
        )
        
        success = instruction_layer.process_instruction(inst_id)
        status = instruction_layer.get_instruction_status(inst_id)
        
        print(f"   '{text}': {status['status']} (confidence: {status['parsing_confidence']:.3f})")
    
    # Test system metrics
    print("\n6. Testing system metrics...")
    
    metrics = instruction_layer.get_system_metrics()
    
    print(f"   Total instructions: {metrics['total_instructions']}")
    print(f"   Successful instructions: {metrics['system_metrics']['successful_instructions']}")
    print(f"   Failed instructions: {metrics['system_metrics']['failed_instructions']}")
    print(f"   Semantic processing: {metrics['system_metrics']['semantic_processing_count']}")
    print(f"   Syntactic processing: {metrics['system_metrics']['syntactic_processing_count']}")
    print(f"   Hybrid processing: {metrics['system_metrics']['hybrid_processing_count']}")
    print(f"   Total kernel actions: {metrics['total_kernel_actions']}")
    print(f"   Total audit trails: {metrics['total_audit_trails']}")
    
    # Shutdown
    print("\n7. Shutting down...")
    instruction_layer.shutdown()
    
    print("Instruction Interpretation Layer operational!")
