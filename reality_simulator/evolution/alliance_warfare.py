"""
⚔️🪐 ALLIANCE WARFARE SYSTEM - ORGANISM AGENCY VERSION
=======================================================

NO AUTOMATION. ORGANISMS DECIDE EVERYTHING.

Every alliance action requires an organism to:
1. PROPOSE it using their neural network
2. Have other organisms ACCEPT or REJECT it
3. EARN their position through decisions, not clustering

No auto-generated names. No fitness tier sorting. No random war triggers.
Organisms choose to form alliances, choose to go to war, choose to betray.

Author: Convergence Engine Team
Created: 2024
Rewritten: 2024-12 - Removed all automation, added true organism agency
"""

import numpy as np
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable, Set
from enum import Enum
from collections import defaultdict


class TerritorialDomain(Enum):
    """Territories organisms fight to control."""
    FITNESS_LANDSCAPE = "fitness_landscape"
    KNOWLEDGE_DOMAIN = "knowledge_domain"
    GERMINATION_TERRITORY = "germination_territory"
    ORBITAL_ZONE = "orbital_zone"
    EMERGENCE_MOMENTUM = "emergence_momentum"
    EXISTENTIAL_OWNERSHIP = "existential_ownership"


class AllianceRole(Enum):
    """Roles within an alliance - earned, not assigned."""
    FOUNDER = "founder"        # Created the alliance
    MEMBER = "member"          # Accepted invitation
    WARCHIEF = "warchief"      # Won leadership challenge
    DIPLOMAT = "diplomat"      # Handles alliance proposals
    BETRAYER = "betrayer"      # Marked as traitor (left mid-war)


class ProposalType(Enum):
    """Types of proposals organisms can make."""
    ALLIANCE_INVITE = "alliance_invite"      # Invite to join alliance
    WAR_DECLARATION = "war_declaration"      # Propose war against target
    PEACE_OFFER = "peace_offer"              # Offer peace to enemy
    BETRAY_ALLIANCE = "betray_alliance"      # Leave/sabotage current alliance
    LEADERSHIP_CHALLENGE = "leadership_challenge"  # Challenge for warchief
    TERRITORY_CLAIM = "territory_claim"      # Claim unclaimed territory
    # CONFEDERATION (Super-Alliance) proposal types
    CONFEDERATION_CREATE = "confederation_create"  # Create a super-alliance
    CONFEDERATION_INVITE = "confederation_invite"  # Invite alliance to confederation
    CONFEDERATION_WAR = "confederation_war"        # Mega-war between confederations
    CONFEDERATION_MERGE = "confederation_merge"    # Merge confederations into mega-confederation


@dataclass
class AllianceProposal:
    """A proposal made by an organism - requires acceptance."""
    proposal_id: str
    proposal_type: ProposalType
    proposer_id: str
    target_id: Optional[str]  # Target organism or alliance
    timestamp: float = field(default_factory=time.time)
    
    # Voting
    votes_for: Set[str] = field(default_factory=set)
    votes_against: Set[str] = field(default_factory=set)
    
    # Resolution
    resolved: bool = False
    accepted: bool = False
    resolution_time: Optional[float] = None
    
    # Context for decision-making
    context: Dict[str, Any] = field(default_factory=dict)
    
    def get_vote_ratio(self) -> float:
        """Get ratio of for votes to total votes."""
        total = len(self.votes_for) + len(self.votes_against)
        if total == 0:
            return 0.0
        return len(self.votes_for) / total


@dataclass 
class OrganismReputation:
    """Track an organism's reputation - earned through actions."""
    organism_id: str
    
    # Trust metrics - earned through behavior
    alliances_honored: int = 0      # Stayed loyal during wars
    alliances_betrayed: int = 0     # Left/sabotaged mid-war
    wars_fought: int = 0
    wars_won: int = 0
    proposals_made: int = 0
    proposals_accepted: int = 0     # Others accepted their proposals
    
    # Relationship tracking
    allies_history: List[str] = field(default_factory=list)  # Past allies
    enemies_history: List[str] = field(default_factory=list)  # Past enemies
    betrayed_by: Set[str] = field(default_factory=set)  # Who betrayed them
    betrayed_whom: Set[str] = field(default_factory=set)  # Who they betrayed
    
    def get_trust_score(self) -> float:
        """Calculate trust score based on history."""
        if self.alliances_honored + self.alliances_betrayed == 0:
            return 0.5  # Neutral - no history
        
        loyalty_ratio = self.alliances_honored / (self.alliances_honored + self.alliances_betrayed + 1)
        
        # Success rate also matters
        success_ratio = 0.5
        if self.proposals_made > 0:
            success_ratio = self.proposals_accepted / self.proposals_made
        
        return (loyalty_ratio * 0.7) + (success_ratio * 0.3)
    
    def get_threat_level(self) -> float:
        """How dangerous is this organism?"""
        if self.wars_fought == 0:
            return 0.3  # Unknown threat
        
        win_rate = self.wars_won / self.wars_fought
        betrayal_factor = 1.0 + (self.alliances_betrayed * 0.2)
        
        return min(1.0, win_rate * betrayal_factor)


@dataclass
class PlanetaryAlliance:
    """
    An alliance formed through organism decisions.
    
    No auto-generated names. The founder names it.
    No auto-membership. Every member chose to join.
    """
    alliance_id: str
    name: str  # Set by FOUNDER organism, not generated
    founder_id: str  # The organism that created it
    
    # Membership - every member CHOSE to be here
    members: Dict[str, AllianceRole] = field(default_factory=dict)
    
    # Leadership - earned through challenge, not assigned
    warchief_id: Optional[str] = None
    
    # Pending proposals that need votes
    pending_proposals: List[AllianceProposal] = field(default_factory=list)
    
    # Territory - claimed through proposals, not assigned
    controlled_territories: Set[TerritorialDomain] = field(default_factory=set)
    
    # War state
    at_war_with: Set[str] = field(default_factory=set)  # Alliance IDs
    wars_declared: int = 0
    wars_won: int = 0
    wars_lost: int = 0
    
    # Betrayal tracking
    betrayers: Set[str] = field(default_factory=set)  # Organism IDs who betrayed
    
    formation_time: float = field(default_factory=time.time)
    
    def add_member(self, organism_id: str, role: AllianceRole = AllianceRole.MEMBER):
        """Add a member who CHOSE to join."""
        self.members[organism_id] = role
        if role == AllianceRole.FOUNDER and self.warchief_id is None:
            self.warchief_id = organism_id
    
    def remove_member(self, organism_id: str, is_betrayal: bool = False):
        """Remove a member."""
        if organism_id in self.members:
            del self.members[organism_id]
            if is_betrayal:
                self.betrayers.add(organism_id)
        
        # If warchief left, no warchief until someone challenges
        if organism_id == self.warchief_id:
            self.warchief_id = None
    
    def get_war_power(self, get_organism_fitness: Callable) -> float:
        """Calculate war power from member fitness."""
        if not self.members:
            return 0.0
        
        total_fitness = 0.0
        for org_id in self.members:
            try:
                fitness = get_organism_fitness(org_id)
                total_fitness += fitness
            except:
                pass
        
        # Bonuses for earned achievements
        territory_bonus = len(self.controlled_territories) * 0.1
        experience_bonus = min(0.5, self.wars_won * 0.1)
        
        # Penalty for betrayals (low morale)
        betrayal_penalty = len(self.betrayers) * 0.05
        
        return max(0.1, total_fitness + territory_bonus + experience_bonus - betrayal_penalty)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alliance_id': self.alliance_id,
            'name': self.name,
            'founder_id': self.founder_id,
            'warchief_id': self.warchief_id,
            'members': {k: v.value for k, v in self.members.items()},
            'member_count': len(self.members),
            'controlled_territories': [t.value for t in self.controlled_territories],
            'at_war_with': list(self.at_war_with),
            'wars_won': self.wars_won,
            'wars_lost': self.wars_lost,
            'betrayers': list(self.betrayers),
            'pending_proposals': len(self.pending_proposals)
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 📜 ALLIANCE HISTORY - THE COLLECTIVE MEMORY OF CIVILIZATIONS
# ═══════════════════════════════════════════════════════════════════════════════
# 
# This is NOT a recursive causation engine. This is KNOWLEDGE ACCUMULATION.
# 
# Individual Organism: action → result → memory (personal experience)
#                      ↓
# Alliance:           shared_memory → collective_wisdom → better decisions
#                      ↓
# Confederation:      alliance_histories → patterns emerge → civilization strategy
#                      ↓
# Empire/Hegemony:    ALL histories → causal laws → predictive power
#
# Organisms CONTRIBUTE their experiences. Alliance GRANTS wisdom back.
# This is literally how human civilization works.
# ═══════════════════════════════════════════════════════════════════════════════


class HistoricalEventType(Enum):
    """Types of events worth recording in alliance history."""
    # Founding moments
    ALLIANCE_FOUNDED = "alliance_founded"
    MEMBER_JOINED = "member_joined"
    MEMBER_LEFT = "member_left"
    
    # Leadership
    WARCHIEF_CHALLENGED = "warchief_challenged"
    WARCHIEF_CHANGED = "warchief_changed"
    
    # Warfare
    WAR_DECLARED = "war_declared"
    WAR_WON = "war_won"
    WAR_LOST = "war_lost"
    BATTLE_FOUGHT = "battle_fought"
    
    # Diplomacy
    PEACE_PROPOSED = "peace_proposed"
    PEACE_ACCEPTED = "peace_accepted"
    PEACE_REJECTED = "peace_rejected"
    TREATY_EXPIRED = "treaty_expired"
    
    # Betrayal
    MEMBER_BETRAYED = "member_betrayed"
    ALLIANCE_SABOTAGED = "alliance_sabotaged"
    
    # Dissolution
    DISSOLUTION = "dissolution"
    
    # Territory
    TERRITORY_CLAIMED = "territory_claimed"
    TERRITORY_LOST = "territory_lost"
    
    # Confederation
    JOINED_CONFEDERATION = "joined_confederation"
    LEFT_CONFEDERATION = "left_confederation"
    CONFEDERATION_ELEVATED = "confederation_elevated"
    
    # Illumination
    ILLUMINATION_UNLOCKED = "illumination_unlocked"
    
    # Organism legends
    ORGANISM_HEROIC_ACT = "organism_heroic_act"
    ORGANISM_CATASTROPHIC_FAILURE = "organism_catastrophic_failure"
    ORGANISM_DEATH = "organism_death"


@dataclass
class HistoricalEvent:
    """A single recorded event in alliance history."""
    event_id: str
    event_type: HistoricalEventType
    timestamp: float
    round_number: int
    
    # Who was involved
    primary_organism_id: Optional[str] = None  # Main actor
    secondary_organism_id: Optional[str] = None  # Target/opponent
    alliance_id: Optional[str] = None
    enemy_alliance_id: Optional[str] = None
    
    # What happened
    description: str = ""  # Human-readable summary
    outcome: str = ""  # "success", "failure", "neutral"
    
    # Metrics at the time
    alliance_strength: float = 0.0
    member_count: int = 0
    vp_at_time: float = 0.0
    
    # Causation links - what led to this, what it caused
    caused_by_event_id: Optional[str] = None
    resulted_in_event_ids: List[str] = field(default_factory=list)
    
    # Extracted lesson (if any)
    lesson_learned: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp,
            'round': self.round_number,
            'primary_organism': self.primary_organism_id,
            'secondary_organism': self.secondary_organism_id,
            'description': self.description,
            'outcome': self.outcome,
            'lesson': self.lesson_learned
        }


@dataclass
class CausalPattern:
    """An extracted cause→effect pattern from historical analysis."""
    pattern_id: str
    
    # The pattern itself
    cause: str  # e.g., "war_during_high_vp"
    effect: str  # e.g., "member_loss"
    
    # Confidence from historical evidence
    occurrences: int = 0
    confidence: float = 0.0  # 0.0 to 1.0
    
    # When this pattern applies
    conditions: Dict[str, Any] = field(default_factory=dict)  # e.g., {"vp_threshold": 0.7}
    
    # Example events that support this pattern
    supporting_events: List[str] = field(default_factory=list)  # event_ids
    
    # Human-readable wisdom
    wisdom_text: str = ""  # e.g., "War during high VP leads to 40% member loss"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'pattern_id': self.pattern_id,
            'cause': self.cause,
            'effect': self.effect,
            'confidence': self.confidence,
            'occurrences': self.occurrences,
            'wisdom': self.wisdom_text
        }


@dataclass
class LegendaryOrganism:
    """Record of an organism who achieved legendary status."""
    organism_id: str
    name: Optional[str] = None  # If they had a name
    
    # Their story
    role: str = ""  # "founder", "warchief", "hero", "betrayer", "martyr"
    achievements: List[str] = field(default_factory=list)
    failures: List[str] = field(default_factory=list)
    
    # Key stats at peak
    peak_fitness: float = 0.0
    battles_won: int = 0
    battles_lost: int = 0
    
    # How they're remembered
    legacy: str = ""  # "Founded the alliance during darkest hour"
    lesson: str = ""  # "Trust must be earned, not assumed"
    
    # Timeline
    joined_round: int = 0
    death_round: Optional[int] = None
    cause_of_death: Optional[str] = None


@dataclass
class AllianceHistory:
    """
    📜 THE COLLECTIVE MEMORY OF A CIVILIZATION
    
    This is where organisms CONTRIBUTE their experiences and
    the alliance EXTRACTS wisdom to share with all members.
    
    This is NOT a recursive causation engine - it's knowledge accumulation.
    Like human civilization's history books, oral traditions, and laws.
    """
    alliance_id: str
    alliance_name: str
    
    # ═══════════════════════════════════════════════════════════════════════
    # RECORDED EVENTS - The raw historical record
    # ═══════════════════════════════════════════════════════════════════════
    events: List[HistoricalEvent] = field(default_factory=list)
    events_by_type: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    events_by_organism: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    
    # ═══════════════════════════════════════════════════════════════════════
    # EXTRACTED PATTERNS - What the alliance LEARNED
    # ═══════════════════════════════════════════════════════════════════════
    causal_patterns: Dict[str, CausalPattern] = field(default_factory=dict)
    
    # ═══════════════════════════════════════════════════════════════════════
    # WISDOM RULES - Codified cause→effect knowledge
    # ═══════════════════════════════════════════════════════════════════════
    wisdom_rules: List[str] = field(default_factory=list)
    # e.g., ["When VP > 0.7, prioritize cooperation over war"]
    #       ["Betrayers should be excluded from future alliances"]
    #       ["Peace with equals preserves strength for true enemies"]
    
    # ═══════════════════════════════════════════════════════════════════════
    # LEGENDARY ORGANISMS - Heroes, villains, and lessons
    # ═══════════════════════════════════════════════════════════════════════
    legends: Dict[str, LegendaryOrganism] = field(default_factory=dict)
    
    # ═══════════════════════════════════════════════════════════════════════
    # AGGREGATE STATISTICS - Summary of alliance journey
    # ═══════════════════════════════════════════════════════════════════════
    total_wars: int = 0
    wars_won: int = 0
    wars_lost: int = 0
    total_members_ever: int = 0
    total_betrayals: int = 0
    total_peace_treaties: int = 0
    highest_member_count: int = 0
    lowest_vp_survived: float = 1.0
    
    # When history started
    founding_round: int = 0
    founding_timestamp: float = field(default_factory=time.time)
    
    def record_event(self, event: HistoricalEvent) -> str:
        """
        Record an event in alliance history.
        
        Organisms CONTRIBUTE their experiences through this.
        Returns the event_id.
        """
        self.events.append(event)
        self.events_by_type[event.event_type.value].append(event.event_id)
        
        if event.primary_organism_id:
            self.events_by_organism[event.primary_organism_id].append(event.event_id)
        if event.secondary_organism_id:
            self.events_by_organism[event.secondary_organism_id].append(event.event_id)
        
        # Update aggregate stats
        if event.event_type == HistoricalEventType.WAR_DECLARED:
            self.total_wars += 1
        elif event.event_type == HistoricalEventType.WAR_WON:
            self.wars_won += 1
        elif event.event_type == HistoricalEventType.WAR_LOST:
            self.wars_lost += 1
        elif event.event_type == HistoricalEventType.MEMBER_JOINED:
            self.total_members_ever += 1
        elif event.event_type == HistoricalEventType.MEMBER_BETRAYED:
            self.total_betrayals += 1
        elif event.event_type == HistoricalEventType.PEACE_ACCEPTED:
            self.total_peace_treaties += 1
        
        if event.member_count > self.highest_member_count:
            self.highest_member_count = event.member_count
        if event.vp_at_time < self.lowest_vp_survived and event.vp_at_time > 0:
            self.lowest_vp_survived = event.vp_at_time
        
        return event.event_id
    
    def get_recent_events(self, limit: int = 20) -> List[HistoricalEvent]:
        """Get most recent events."""
        return self.events[-limit:]
    
    def get_events_of_type(self, event_type: HistoricalEventType, limit: int = 50) -> List[HistoricalEvent]:
        """Get events of a specific type."""
        event_ids = self.events_by_type.get(event_type.value, [])[-limit:]
        return [e for e in self.events if e.event_id in event_ids]
    
    def get_organism_history(self, organism_id: str) -> List[HistoricalEvent]:
        """Get all events involving a specific organism."""
        event_ids = self.events_by_organism.get(organism_id, [])
        return [e for e in self.events if e.event_id in event_ids]
    
    def extract_pattern(self, cause: str, effect: str, 
                        supporting_events: List[str],
                        conditions: Dict[str, Any] = None) -> CausalPattern:
        """
        Extract a causal pattern from historical evidence.
        
        This is how alliances LEARN from their history.
        """
        pattern_id = f"pattern_{cause}_{effect}_{int(time.time())}"
        
        # Calculate confidence based on evidence
        occurrences = len(supporting_events)
        confidence = min(0.95, 0.3 + (occurrences * 0.1))
        
        # Generate wisdom text
        wisdom_text = f"{cause.replace('_', ' ').title()} tends to cause {effect.replace('_', ' ')}"
        if conditions:
            cond_str = ', '.join(f"{k}={v}" for k, v in conditions.items())
            wisdom_text += f" (when {cond_str})"
        
        pattern = CausalPattern(
            pattern_id=pattern_id,
            cause=cause,
            effect=effect,
            occurrences=occurrences,
            confidence=confidence,
            conditions=conditions or {},
            supporting_events=supporting_events,
            wisdom_text=wisdom_text
        )
        
        self.causal_patterns[pattern_id] = pattern
        
        # Auto-generate wisdom rule if confidence is high enough
        if confidence >= 0.7:
            rule = f"[Confidence {confidence:.0%}] {wisdom_text}"
            if rule not in self.wisdom_rules:
                self.wisdom_rules.append(rule)
        
        return pattern
    
    def add_legend(self, organism_id: str, role: str, 
                   achievements: List[str], legacy: str) -> LegendaryOrganism:
        """
        Record an organism as legendary - for better or worse.
        
        Heroes inspire. Villains warn. Both teach.
        """
        legend = LegendaryOrganism(
            organism_id=organism_id,
            role=role,
            achievements=achievements,
            legacy=legacy
        )
        self.legends[organism_id] = legend
        return legend
    
    def get_wisdom_for_situation(self, situation: Dict[str, Any]) -> List[str]:
        """
        Query alliance wisdom for a given situation.
        
        This is how organisms ACCESS collective knowledge.
        
        Args:
            situation: Dict describing current situation
                       e.g., {"vp": 0.8, "at_war": True, "member_count": 5}
        
        Returns:
            List of relevant wisdom rules
        """
        relevant_wisdom = []
        
        vp = situation.get('vp', 0.5)
        at_war = situation.get('at_war', False)
        member_count = situation.get('member_count', 0)
        
        # Check each pattern for relevance
        for pattern in self.causal_patterns.values():
            if pattern.confidence < 0.5:
                continue  # Only share confident patterns
            
            conditions = pattern.conditions
            is_relevant = True
            
            # Check if conditions match
            if 'vp_threshold' in conditions:
                if vp < conditions['vp_threshold']:
                    is_relevant = False
            if 'requires_war' in conditions:
                if conditions['requires_war'] != at_war:
                    is_relevant = False
            if 'min_members' in conditions:
                if member_count < conditions['min_members']:
                    is_relevant = False
            
            if is_relevant:
                relevant_wisdom.append(pattern.wisdom_text)
        
        # Add general wisdom rules
        relevant_wisdom.extend(self.wisdom_rules[:5])  # Top 5 general rules
        
        return relevant_wisdom
    
    def get_historical_summary(self) -> Dict[str, Any]:
        """Get a summary of alliance history for display/analysis."""
        return {
            'alliance_id': self.alliance_id,
            'alliance_name': self.alliance_name,
            'total_events': len(self.events),
            'total_wars': self.total_wars,
            'wars_won': self.wars_won,
            'wars_lost': self.wars_lost,
            'win_rate': self.wars_won / self.total_wars if self.total_wars > 0 else 0,
            'total_members_ever': self.total_members_ever,
            'total_betrayals': self.total_betrayals,
            'betrayal_rate': self.total_betrayals / self.total_members_ever if self.total_members_ever > 0 else 0,
            'total_peace_treaties': self.total_peace_treaties,
            'highest_member_count': self.highest_member_count,
            'lowest_vp_survived': self.lowest_vp_survived,
            'patterns_extracted': len(self.causal_patterns),
            'wisdom_rules': len(self.wisdom_rules),
            'legends_recorded': len(self.legends),
            'founding_round': self.founding_round
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage/transmission."""
        return {
            **self.get_historical_summary(),
            'recent_events': [e.to_dict() for e in self.get_recent_events(10)],
            'top_patterns': [p.to_dict() for p in list(self.causal_patterns.values())[:10]],
            'wisdom_rules': self.wisdom_rules[:20],
            'legends': {k: {'role': v.role, 'legacy': v.legacy} for k, v in self.legends.items()}
        }
    
    def prune_old_events(self, max_events: int = 500) -> int:
        """
        🧹 MEMORY LEAK FIX: Prune old events to prevent unbounded growth.
        
        Keeps the most recent events and maintains index integrity.
        Patterns and wisdom are preserved as they represent learned knowledge.
        
        Args:
            max_events: Maximum number of events to keep
            
        Returns:
            Number of events pruned
        """
        if len(self.events) <= max_events:
            return 0
        
        # Keep most recent events
        events_to_remove = len(self.events) - max_events
        removed_events = self.events[:events_to_remove]
        self.events = self.events[events_to_remove:]
        
        # Update indices - remove references to pruned events
        removed_ids = {e.event_id for e in removed_events}
        
        for event_type in self.events_by_type:
            self.events_by_type[event_type] = [
                eid for eid in self.events_by_type[event_type]
                if eid not in removed_ids
            ]

        for organism_id in self.events_by_organism:
            self.events_by_organism[organism_id] = [
                eid for eid in self.events_by_organism[organism_id]
                if eid not in removed_ids
            ]

        # Clean up empty index entries to prevent stale references
        self.events_by_type = {
            k: v for k, v in self.events_by_type.items() if v
        }
        self.events_by_organism = {
            k: v for k, v in self.events_by_organism.items() if v
        }
        
        return events_to_remove


class ConfederationTier(Enum):
    """
    Tiers of super-alliances - emergent hierarchy.
    
    What determines each tier:
    - CONFEDERATION: Alliances with compatible IDEOLOGIES (similar knowledge domains)
    - EMPIRE: Confederations that control TERRITORY together
    - HEGEMONY: Empires that dominate through CULTURAL consensus (shared vocabulary)
    """
    CONFEDERATION = 1  # Alliance of Alliances - ideological alignment
    EMPIRE = 2         # Confederation of Confederations - territorial dominance
    HEGEMONY = 3       # Empire of Empires - cultural/linguistic supremacy


@dataclass
class Confederation:
    """
    A Super-Alliance: Alliances that ally with each other.
    
    WHAT DETERMINES CONFEDERATION FORMATION:
    1. Shared Enemies - alliances at war with same target
    2. Knowledge Domain Overlap - similar concepts in their territories  
    3. Reputation Trust - alliances with honorable track records
    4. Mutual Benefit - combined war power > individual
    
    WHAT DETERMINES MEGA-CONFEDERATIONS (EMPIRES):
    1. Territorial Control - confederations controlling complementary domains
    2. War Victory - confederations that won wars together
    3. Semantic Alignment - shared vocabulary/concepts across all members
    4. Economic Interdependence - resource flow between confederations
    
    No automation. Alliance warchiefs must PROPOSE and VOTE.
    """
    # Required fields (no defaults) - must come first
    confederation_id: str
    name: str  # Named by founding alliance warchief
    founding_alliance_id: str  # The alliance that created this
    
    # Optional/default fields
    tier: ConfederationTier = ConfederationTier.CONFEDERATION
    
    # Member alliances - each CHOSE to join via warchief vote
    member_alliances: Dict[str, float] = field(default_factory=dict)  # alliance_id -> join_time
    
    # Leadership - the alliance whose warchief leads the confederation
    supreme_alliance_id: Optional[str] = None
    
    # Shared ideology/knowledge
    shared_knowledge_domains: Set[TerritorialDomain] = field(default_factory=set)
    
    # Higher-tier membership
    parent_confederation_id: Optional[str] = None  # If part of Empire/Hegemony
    child_confederations: Set[str] = field(default_factory=set)  # If this IS an Empire/Hegemony
    
    # Confederation-level wars
    at_war_with_confederations: Set[str] = field(default_factory=set)
    confederation_wars_won: int = 0
    confederation_wars_lost: int = 0
    
    # Alliance betrayals at confederation level
    betrayer_alliances: Set[str] = field(default_factory=set)
    
    formation_time: float = field(default_factory=time.time)
    
    def get_total_organisms(self, get_alliance: Callable) -> int:
        """Count all organisms across all member alliances."""
        total = 0
        for alliance_id in self.member_alliances:
            try:
                alliance = get_alliance(alliance_id)
                if alliance:
                    total += len(alliance.members)
            except:
                pass
        return total
    
    def get_confederation_power(self, get_alliance: Callable, 
                                 get_organism_fitness: Callable) -> float:
        """Calculate combined power of all member alliances."""
        total_power = 0.0
        for alliance_id in self.member_alliances:
            try:
                alliance = get_alliance(alliance_id)
                if alliance:
                    total_power += alliance.get_war_power(get_organism_fitness)
            except:
                pass
        
        # Tier bonus - higher tiers are stronger
        tier_multiplier = 1.0 + (self.tier.value * 0.2)
        
        # Cohesion bonus - shared domains strengthen bonds
        cohesion_bonus = len(self.shared_knowledge_domains) * 0.1
        
        # Child confederation bonus (for Empires/Hegemonies)
        hierarchy_bonus = len(self.child_confederations) * 0.15
        
        return total_power * tier_multiplier + cohesion_bonus + hierarchy_bonus
    
    def can_elevate_tier(self, get_alliance: Callable) -> Tuple[bool, str]:
        """
        Check if this confederation can become higher tier.
        
        CONFEDERATION -> EMPIRE requires:
        - 3+ member alliances
        - Control 2+ different territory types
        - Won at least 1 confederation war
        
        EMPIRE -> HEGEMONY requires:
        - 2+ child confederations
        - Control 4+ different territories
        - Won 3+ confederation wars
        """
        if self.tier == ConfederationTier.CONFEDERATION:
            if len(self.member_alliances) < 3:
                return False, "Need 3+ alliances"
            if len(self.shared_knowledge_domains) < 2:
                return False, "Need 2+ shared knowledge domains"
            if self.confederation_wars_won < 1:
                return False, "Need 1+ confederation war victory"
            return True, "Ready to become EMPIRE"
            
        elif self.tier == ConfederationTier.EMPIRE:
            if len(self.child_confederations) < 2:
                return False, "Need 2+ child confederations"
            if len(self.shared_knowledge_domains) < 4:
                return False, "Need 4+ shared knowledge domains"
            if self.confederation_wars_won < 3:
                return False, "Need 3+ confederation war victories"
            return True, "Ready to become HEGEMONY"
            
        else:
            return False, "Already at maximum tier (HEGEMONY)"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'confederation_id': self.confederation_id,
            'name': self.name,
            'tier': self.tier.name,
            'founding_alliance_id': self.founding_alliance_id,
            'supreme_alliance_id': self.supreme_alliance_id,
            'member_alliances': list(self.member_alliances.keys()),
            'member_count': len(self.member_alliances),
            'shared_knowledge_domains': [d.value for d in self.shared_knowledge_domains],
            'parent_confederation': self.parent_confederation_id,
            'child_confederations': list(self.child_confederations),
            'at_war_with': list(self.at_war_with_confederations),
            'wars_won': self.confederation_wars_won,
            'wars_lost': self.confederation_wars_lost,
            'betrayer_alliances': list(self.betrayer_alliances)
        }


class AllianceWarfareSystem:
    """
    Alliance Warfare with FULL ORGANISM AGENCY.
    
    Nothing happens automatically. Every action requires:
    1. An organism to PROPOSE it
    2. Other organisms to DECIDE on it
    3. Consequences that affect organism reputation
    """
    
    def __init__(self, highlander_protocol=None, config: Optional[Dict] = None,
                 event_emitter: Optional[Callable] = None):
        self.highlander_protocol = highlander_protocol
        self.config = config or {}
        self.event_emitter = event_emitter
        
        # Neural organism registry for feedback loops (injected from UnifiedSystem)
        self._neural_organisms: Optional[Dict[str, Any]] = None
        
        # Logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not any(isinstance(h, logging.StreamHandler) for h in self.logger.handlers):
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('[ALLIANCE] %(message)s'))
            self.logger.addHandler(handler)
            self.logger.propagate = False
        
        # Configuration
        self.min_alliance_size = self.config.get('min_alliance_size', 3)
        self.max_alliances = self.config.get('max_alliances', 10)
        self.vote_threshold = self.config.get('vote_threshold', 0.5)  # 50% to pass
        self.proposal_timeout = self.config.get('proposal_timeout', 10)  # rounds
        
        # State - nothing auto-populated
        self.alliances: Dict[str, PlanetaryAlliance] = {}
        self.organism_reputations: Dict[str, OrganismReputation] = {}
        self.pending_global_proposals: List[AllianceProposal] = []  # Cross-alliance proposals
        
        # CONFEDERATION (Super-Alliance) State
        self.confederations: Dict[str, Confederation] = {}  # confederation_id -> Confederation
        self.alliance_to_confederation: Dict[str, str] = {}  # alliance_id -> confederation_id
        
        # Territory control - starts EMPTY, must be claimed
        self.uncontrolled_territories: Set[TerritorialDomain] = set(TerritorialDomain)
        self.territory_control: Dict[TerritorialDomain, str] = {}  # territory -> alliance_id
        
        # War tracking
        self.active_wars: Dict[str, Dict[str, Any]] = {}  # war_id -> war state
        self.war_history: List[Dict[str, Any]] = []
        
        # Round tracking
        self.round_number = 0
        
        # ═══════════════════════════════════════════════════════════════════════
        # 🔮 ILLUMINATION ENGINE - CIVILIZATION REWARDS
        # ═══════════════════════════════════════════════════════════════════════
        # Organisms CANNOT access causation data by default.
        # They are the STATE itself - they have no external view.
        # But through CIVILIZATION (alliances, treaties, organization),
        # they earn access to the ILLUMINATION ENGINE - causation insights!
        #
        # Capability Tiers:
        # - NONE: No causation access (individuals)
        # - BASIC: See own organism's causal chain (small alliances)
        # - ALLIANCE: See alliance-wide causation (medium alliances)  
        # - CONFEDERATION: Full illumination across confederation
        # - EMPIRE: Deep root cause analysis, impact prediction
        # - HEGEMONY: Complete omniscience - all causation data
        # ═══════════════════════════════════════════════════════════════════════
        self.alliance_capabilities: Dict[str, Set[str]] = {}  # alliance_id -> capabilities
        self.illumination_thresholds = {
            'basic': {'members': 3, 'name': 'Basic Causation'},       # 3+ members
            'alliance': {'members': 5, 'name': 'Alliance Insight'},   # 5+ members  
            'confederation': {'tier': 1, 'name': 'Confederation Vision'},  # Confederation tier
            'empire': {'tier': 2, 'name': 'Imperial Foresight'},      # Empire tier
            'hegemony': {'tier': 3, 'name': 'Hegemonic Omniscience'}  # Hegemony tier
        }
        
        # ═══════════════════════════════════════════════════════════════════════
        # 📜 ALLIANCE HISTORY - COLLECTIVE MEMORY OF CIVILIZATIONS
        # ═══════════════════════════════════════════════════════════════════════
        # This is where organisms CONTRIBUTE their experiences and
        # the alliance EXTRACTS wisdom to share with all members.
        # 
        # NOT recursive causation engines - KNOWLEDGE ACCUMULATION.
        # Like human civilization's history books, oral traditions, and laws.
        # ═══════════════════════════════════════════════════════════════════════
        self.alliance_histories: Dict[str, AllianceHistory] = {}  # alliance_id -> history
    
    def set_neural_organisms(self, organisms: Dict[str, Any]):
        """
        Inject neural organisms registry for feedback loops.
        Called by UnifiedSystem after initialization.
        """
        self._neural_organisms = organisms
    
    def _get_neural_organism(self, organism_id: str):
        """Get neural organism for feedback, if available."""
        if self._neural_organisms:
            return self._neural_organisms.get(organism_id)
        return None
    
    def _record_neural_feedback(self, organism_id: str, event_type: str, success: bool):
        """
        Record alliance event to neural organism for learning.
        Closes the alliance → neural feedback loop.
        """
        neural_org = self._get_neural_organism(organism_id)
        if neural_org and hasattr(neural_org, 'record_alliance_event'):
            try:
                neural_org.record_alliance_event(event_type, success)
            except Exception as e:
                self.logger.debug(f"Neural feedback failed for {organism_id}: {e}")
    
    def _get_or_create_reputation(self, organism_id: str) -> OrganismReputation:
        """Get reputation, create if doesn't exist."""
        if organism_id not in self.organism_reputations:
            self.organism_reputations[organism_id] = OrganismReputation(organism_id=organism_id)
        return self.organism_reputations[organism_id]
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit causation event."""
        if not self.event_emitter:
            return
        try:
            from causation_explorer import Event
            event = Event(
                timestamp=time.time(),
                event_type=f"alliance_{event_type}",
                component='alliance_warfare',
                data={'round': self.round_number, **data}
            )
            self.event_emitter(event)
        except ImportError:
            pass
    
    # ═══════════════════════════════════════════════════════════════════════
    # 📜 ALLIANCE HISTORY - COLLECTIVE MEMORY SYSTEM
    # ═══════════════════════════════════════════════════════════════════════
    
    def _get_or_create_history(self, alliance_id: str) -> Optional[AllianceHistory]:
        """Get alliance history, create if doesn't exist."""
        if alliance_id not in self.alliances:
            return None
        
        if alliance_id not in self.alliance_histories:
            alliance = self.alliances[alliance_id]
            self.alliance_histories[alliance_id] = AllianceHistory(
                alliance_id=alliance_id,
                alliance_name=alliance.name,
                founding_round=self.round_number
            )
        return self.alliance_histories[alliance_id]
    
    def record_historical_event(self, 
                                 alliance_id: str,
                                 event_type: HistoricalEventType,
                                 description: str,
                                 primary_organism_id: Optional[str] = None,
                                 secondary_organism_id: Optional[str] = None,
                                 enemy_alliance_id: Optional[str] = None,
                                 outcome: str = "neutral",
                                 lesson: Optional[str] = None,
                                 caused_by: Optional[str] = None,
                                 vp_value: float = 0.5) -> Optional[str]:
        """
        Record an event in alliance history.
        
        Organisms CONTRIBUTE their experiences through this method.
        The alliance accumulates collective knowledge.
        
        Args:
            alliance_id: The alliance to record for
            event_type: Type of historical event
            description: Human-readable description
            primary_organism_id: Main actor in the event
            secondary_organism_id: Target/opponent
            enemy_alliance_id: If another alliance was involved
            outcome: "success", "failure", or "neutral"
            lesson: Optional lesson learned from this event
            caused_by: Event ID that caused this (causal chain)
            vp_value: VP at the time of the event
            
        Returns:
            Event ID if recorded, None if failed
        """
        history = self._get_or_create_history(alliance_id)
        if not history:
            return None
        
        alliance = self.alliances.get(alliance_id)
        member_count = len(alliance.members) if alliance else 0
        alliance_strength = alliance.get_war_power(lambda x: 0.5) if alliance else 0.0
        
        event_id = f"hist_{alliance_id}_{event_type.value}_{int(time.time()*1000)}"
        
        event = HistoricalEvent(
            event_id=event_id,
            event_type=event_type,
            timestamp=time.time(),
            round_number=self.round_number,
            primary_organism_id=primary_organism_id,
            secondary_organism_id=secondary_organism_id,
            alliance_id=alliance_id,
            enemy_alliance_id=enemy_alliance_id,
            description=description,
            outcome=outcome,
            alliance_strength=alliance_strength,
            member_count=member_count,
            vp_at_time=vp_value,
            caused_by_event_id=caused_by,
            lesson_learned=lesson
        )
        
        history.record_event(event)
        
        # Also emit to CausationExplorer for global visibility
        self._emit_event('historical_record', {
            'event_id': event_id,
            'event_type': event_type.value,
            'alliance': history.alliance_name,
            'description': description,
            'outcome': outcome,
            'lesson': lesson
        })
        
        return event_id
    
    def analyze_and_extract_patterns(self, alliance_id: str) -> List[CausalPattern]:
        """
        Analyze alliance history and extract causal patterns.
        
        This is how alliances LEARN from their collective experience.
        Called periodically or after significant events.
        
        Returns:
            List of newly extracted patterns
        """
        history = self._get_or_create_history(alliance_id)
        if not history or len(history.events) < 5:
            return []  # Not enough history yet
        
        new_patterns = []
        
        # Pattern 1: War during high VP → member loss
        war_events = history.get_events_of_type(HistoricalEventType.WAR_DECLARED)
        high_vp_wars = [e for e in war_events if e.vp_at_time > 0.6]
        
        if len(high_vp_wars) >= 2:
            # Check if wars during high VP led to member loss
            member_losses_after_war = []
            for war in high_vp_wars:
                loss_events = [e for e in history.events 
                              if e.event_type == HistoricalEventType.MEMBER_LEFT
                              and e.round_number > war.round_number
                              and e.round_number < war.round_number + 20]
                if loss_events:
                    member_losses_after_war.append(war.event_id)
            
            if len(member_losses_after_war) >= 2:
                pattern = history.extract_pattern(
                    cause="war_during_high_vp",
                    effect="member_loss",
                    supporting_events=member_losses_after_war,
                    conditions={"vp_threshold": 0.6}
                )
                new_patterns.append(pattern)
        
        # Pattern 2: Peace treaties → stability
        peace_events = history.get_events_of_type(HistoricalEventType.PEACE_ACCEPTED)
        if len(peace_events) >= 2:
            stability_after_peace = []
            for peace in peace_events:
                # Check if member count stayed stable after peace
                later_events = [e for e in history.events
                               if e.round_number > peace.round_number
                               and e.round_number < peace.round_number + 50]
                losses = [e for e in later_events if e.event_type == HistoricalEventType.MEMBER_LEFT]
                if len(losses) < 2:  # Low losses = stability
                    stability_after_peace.append(peace.event_id)
            
            if len(stability_after_peace) >= 2:
                pattern = history.extract_pattern(
                    cause="peace_treaty",
                    effect="member_stability",
                    supporting_events=stability_after_peace,
                    conditions={}
                )
                new_patterns.append(pattern)
        
        # Pattern 3: Betrayal → reputation damage (future recruitment harder)
        betrayal_events = history.get_events_of_type(HistoricalEventType.MEMBER_BETRAYED)
        if betrayal_events:
            pattern = history.extract_pattern(
                cause="member_betrayal",
                effect="trust_erosion",
                supporting_events=[e.event_id for e in betrayal_events],
                conditions={}
            )
            # Add specific wisdom
            if pattern.confidence > 0.5:
                history.wisdom_rules.append(
                    f"⚠️ Betrayal weakens the alliance. {history.total_betrayals} betrayals recorded."
                )
            new_patterns.append(pattern)
        
        # Pattern 4: Cooperation during crisis → survival
        # Look for events during low VP that led to survival
        crisis_events = [e for e in history.events if e.vp_at_time > 0.7]  # High VP = crisis
        if len(crisis_events) >= 3:
            # Did alliance survive the crisis?
            survived_crisis = history.wars_lost < history.total_wars  # Not all wars lost
            if survived_crisis:
                pattern = history.extract_pattern(
                    cause="cooperation_during_crisis",
                    effect="survival",
                    supporting_events=[e.event_id for e in crisis_events[:5]],
                    conditions={"vp_threshold": 0.7}
                )
                history.wisdom_rules.append(
                    "💪 During high VP crises, cooperation is key to survival."
                )
                new_patterns.append(pattern)
        
        return new_patterns
    
    def get_alliance_wisdom(self, alliance_id: str, 
                            current_situation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get wisdom from alliance history relevant to current situation.
        
        This is how organisms ACCESS collective knowledge.
        Higher illumination levels get deeper insights.
        
        Args:
            alliance_id: The alliance to query
            current_situation: Dict describing the current state
                              e.g., {"vp": 0.8, "at_war": True, "member_count": 5}
        
        Returns:
            Dict with relevant wisdom, patterns, and recommendations
        """
        history = self._get_or_create_history(alliance_id)
        if not history:
            return {'error': 'No history found', 'wisdom': []}
        
        # Get alliance illumination level
        capabilities = self.alliance_capabilities.get(alliance_id, set())
        
        result = {
            'alliance': history.alliance_name,
            'total_events': len(history.events),
            'wisdom': [],
            'relevant_patterns': [],
            'legendary_guidance': [],
            'historical_summary': {}
        }
        
        # Basic illumination: Get general wisdom rules
        if 'illumination_basic' in capabilities:
            result['wisdom'] = history.get_wisdom_for_situation(current_situation)
        
        # Alliance illumination: Get relevant patterns
        if 'illumination_alliance' in capabilities:
            for pattern in history.causal_patterns.values():
                if pattern.confidence >= 0.5:
                    result['relevant_patterns'].append({
                        'cause': pattern.cause,
                        'effect': pattern.effect,
                        'confidence': pattern.confidence,
                        'wisdom': pattern.wisdom_text
                    })
        
        # Confederation+ illumination: Access legendary guidance
        if 'illumination_confederation' in capabilities:
            for legend_id, legend in history.legends.items():
                if legend.legacy:
                    result['legendary_guidance'].append({
                        'organism': legend_id,
                        'role': legend.role,
                        'legacy': legend.legacy,
                        'lesson': legend.lesson
                    })
        
        # Empire+ illumination: Full historical analysis
        if 'illumination_empire' in capabilities:
            result['historical_summary'] = history.get_historical_summary()
            # Also trigger pattern extraction
            self.analyze_and_extract_patterns(alliance_id)
        
        return result
    
    def create_legend(self, alliance_id: str, organism_id: str,
                      role: str, achievements: List[str], 
                      legacy: str, lesson: str = "") -> Optional[LegendaryOrganism]:
        """
        Record an organism as legendary in alliance history.
        
        Heroes inspire. Villains warn. Both teach.
        
        Args:
            alliance_id: The alliance to record in
            organism_id: The legendary organism
            role: "founder", "warchief", "hero", "betrayer", "martyr"
            achievements: List of notable achievements
            legacy: How they're remembered
            lesson: What their story teaches
        
        Returns:
            LegendaryOrganism if created
        """
        history = self._get_or_create_history(alliance_id)
        if not history:
            return None
        
        legend = history.add_legend(organism_id, role, achievements, legacy)
        legend.lesson = lesson
        
        # Record the legendary event
        self.record_historical_event(
            alliance_id=alliance_id,
            event_type=HistoricalEventType.ORGANISM_HEROIC_ACT,
            description=f"{organism_id} achieved legendary status as {role}: {legacy}",
            primary_organism_id=organism_id,
            outcome="success",
            lesson=lesson
        )
        
        self.logger.info(f"⭐ LEGEND RECORDED in {history.alliance_name}: {organism_id} - {role}")
        
        return legend

    # ═══════════════════════════════════════════════════════════════════════
    # 🔮 ILLUMINATION ENGINE - CIVILIZATION CAPABILITY SYSTEM
    # ═══════════════════════════════════════════════════════════════════════
    
    def sync_alliance_state(self, alliance_id: str, alliance_data: Dict[str, Any]) -> None:
        """
        Synchronize alliance state from HighlanderProtocol to AllianceWarfareSystem.
        
        Called whenever an alliance is formed, updated, or dissolved in Highlander.
        This ensures AllianceWarfareSystem has current information for stability tracking.
        
        Args:
            alliance_id: Unique alliance identifier
            alliance_data: {
                'members': List[str],           # Organism IDs in alliance
                'formation_round': int,         # When alliance was formed
                'stability_rounds': int,        # How many rounds survived
                'confederation_id': str | None, # If part of confederation
                'war_count': int,              # Wars engaged in
                'betrayal_count': int          # Members who left
            }
        """
        # Ensure alliance object exists
        if alliance_id not in self.alliances:
            members_list = list(alliance_data.get('members', []))
            founder_id = members_list[0] if members_list else 'unknown'
            
            # Create a localized PlanetaryAlliance stub
            # We assume PlanetaryAlliance is defined in this module
            new_alliance = PlanetaryAlliance(
                alliance_id=alliance_id,
                name=f"Alliance {alliance_id[-6:]}",
                founder_id=founder_id
            )
            self.alliances[alliance_id] = new_alliance

        alliance = self.alliances[alliance_id]
        
        # Update members
        # We need to preserve roles if possible, or just reset to MEMBER if new
        sync_members = set(alliance_data.get('members', []))
        
        # Remove old members
        current_members = list(alliance.members.keys())
        for member_id in current_members:
            if member_id not in sync_members:
                del alliance.members[member_id]
        
        # Add new members
        for member_id in sync_members:
            if member_id not in alliance.members:
                alliance.members[member_id] = AllianceRole.MEMBER
        
        # Monkey-patch stability data (PlanetaryAlliance doesn't have stability_rounds field by default)
        alliance.stability_rounds = alliance_data.get('stability_rounds', 0)
        
        # Automatically check and grant illumination based on new state
        self.check_and_grant_illumination(alliance_id)

    def check_and_grant_illumination(self, alliance_id: str) -> List[str]:
        """
        Check if alliance meets thresholds for Illumination Engine access.
        
        Criteria:
        1. **Stability:** Alliance must persist for N rounds.
        2. **Complexity:** Member count and Confederation status.
        
        Returns:
            List of newly granted capabilities
        """
        alliance = self.alliances.get(alliance_id)
        if not alliance:
            return []
        
        capabilities = self.alliance_capabilities.setdefault(alliance_id, set())
        newly_granted = []
        
        # Get data (handling both Dataclass and potential Dict sync)
        member_count = len(alliance.members)
        stability_rounds = getattr(alliance, 'stability_rounds', 0)
        
        # Check confederation tier
        confederation_id = self.alliance_to_confederation.get(alliance_id)
        conf_tier = 0
        if confederation_id:
            conf = self.confederations.get(confederation_id)
            if conf:
                conf_tier = conf.tier.value
        
        # Get config thresholds
        min_size = self.config.get('min_alliance_size', 3)
        basic_stability = self.config.get('illumination_stability_threshold', 5)
        
        # 1. Basic Causation: Min size, Basic stability
        if member_count >= min_size and stability_rounds >= basic_stability and 'illumination_basic' not in capabilities:
            self.unlock_causation_for_alliance(alliance_id, 'illumination_basic')
            newly_granted.append('illumination_basic')
            
        # 2. Alliance Insight: Min size + 2, Basic stability * 2
        if member_count >= (min_size + 2) and stability_rounds >= (basic_stability * 2) and 'illumination_alliance' not in capabilities:
            self.unlock_causation_for_alliance(alliance_id, 'illumination_alliance')
            newly_granted.append('illumination_alliance')

        # 3. Confederation Vision: Tier 1+, Basic stability * 3
        if conf_tier >= 1 and stability_rounds >= (basic_stability * 3) and 'illumination_confederation' not in capabilities:
            self.unlock_causation_for_alliance(alliance_id, 'illumination_confederation')
            newly_granted.append('illumination_confederation')

        # 4. Imperial Foresight: Tier 2+
        if conf_tier >= 2 and 'illumination_empire' not in capabilities:
            self.unlock_causation_for_alliance(alliance_id, 'illumination_empire')
            newly_granted.append('illumination_empire')

        # 5. Hegemonic Omniscience: Tier 3+
        if conf_tier >= 3 and 'illumination_hegemony' not in capabilities:
            self.unlock_causation_for_alliance(alliance_id, 'illumination_hegemony')
            newly_granted.append('illumination_hegemony')
            
        return newly_granted

    def unlock_causation_for_alliance(self, alliance_id: str, illumination_tier: str) -> None:
        """
        Grant Causation Illumination to all members of an alliance.
        
        Args:
            alliance_id: Alliance to grant illumination to
            illumination_tier: Capability string identifier
        """
        if alliance_id not in self.alliances:
            return
            
        alliance = self.alliances[alliance_id]
        capabilities = self.alliance_capabilities.setdefault(alliance_id, set())
        capabilities.add(illumination_tier)
        
        # Map capability to simple tier name for organisms
        tier_map = {
            'illumination_basic': 'basic',
            'illumination_alliance': 'alliance', 
            'illumination_confederation': 'confederation',
            'illumination_empire': 'empire',
            'illumination_hegemony': 'hegemony'
        }
        simple_tier = tier_map.get(illumination_tier, 'basic')
        
        self.logger.info(f"🔮 [{alliance.name}] UNLOCKED: {simple_tier.upper()} Causation (Stability: {getattr(alliance, 'stability_rounds', 0)})")
        
        # Update each organism's illumination level
        # We need to access organisms via HighlanderProtocol
        if self.highlander_protocol:
            for organism_id in alliance.members:
                # We need a way to get the organism object
                # HighlanderProtocol doesn't standardly expose get_organism yet, 
                # but we will add it or access the list directly.
                organism = self._get_organism(organism_id)
                if organism and hasattr(organism, '_illumination_level'):
                    # Only upgrade
                    tier_ranks = {'none': 0, 'basic': 1, 'alliance': 2, 'confederation': 3, 'empire': 4, 'hegemony': 5}
                    current_rank = tier_ranks.get(organism._illumination_level, 0)
                    new_rank = tier_ranks.get(simple_tier, 0)
                    
                    if new_rank > current_rank:
                        organism._illumination_level = simple_tier
                        # Also refresh references just in case
                        if hasattr(organism, 'set_system_references'):
                             organism.set_system_references(
                                 alliance_warfare=self,
                                 causation_explorer=self.event_emitter.__self__ if hasattr(self.event_emitter, '__self__') else None
                             )

        # Emit event to CausationExplorer
        self._emit_event('illumination_unlocked', {
            'alliance': alliance.name,
            'alliance_id': alliance_id,
            'capability': illumination_tier,
            'tier': simple_tier,
            'member_count': len(alliance.members),
            'stability_rounds': getattr(alliance, 'stability_rounds', 0)
        })

    def _get_organism(self, organism_id: str):
        """Retrieve organism by ID from HighlanderProtocol."""
        if self.highlander_protocol:
            # Try method first
            if hasattr(self.highlander_protocol, 'get_organism'):
                return self.highlander_protocol.get_organism(organism_id)
            # Try raw access (fallback)
            if hasattr(self.highlander_protocol, 'active_organisms'):
                 # active_organisms is usually a Set[str], so we can't get the object
                 pass
        return None
    
    def get_organism_illumination_level(self, organism_id: str) -> Dict[str, Any]:
        """
        Get what level of Illumination an organism has access to.
        
        Organisms gain illumination through their alliance's civilization level.
        Solo organisms have NO illumination - they cannot see beyond themselves.
        
        Returns:
            Dict with level, capabilities, and what they can access
        """
        alliance_id = self.get_organism_alliance(organism_id)
        
        if not alliance_id:
            return {
                'level': 'none',
                'level_name': 'Isolated',
                'capabilities': set(),
                'can_see_self': False,
                'can_see_alliance': False,
                'can_see_confederation': False,
                'can_see_root_causes': False,
                'can_predict_impact': False,
                'can_see_all': False,
                'message': 'Join or form an alliance to access the Illumination Engine'
            }
        
        alliance = self.alliances.get(alliance_id)
        capabilities = self.alliance_capabilities.get(alliance_id, set())
        
        # Check and possibly grant new capabilities
        self.check_and_grant_illumination(alliance_id)
        capabilities = self.alliance_capabilities.get(alliance_id, set())
        
        # Determine highest level
        level = 'none'
        level_name = 'No Illumination'
        if 'illumination_hegemony' in capabilities:
            level = 'hegemony'
            level_name = 'Hegemonic Omniscience'
        elif 'illumination_empire' in capabilities:
            level = 'empire'
            level_name = 'Imperial Foresight'
        elif 'illumination_confederation' in capabilities:
            level = 'confederation'
            level_name = 'Confederation Vision'
        elif 'illumination_alliance' in capabilities:
            level = 'alliance'
            level_name = 'Alliance Insight'
        elif 'illumination_basic' in capabilities:
            level = 'basic'
            level_name = 'Basic Causation'
        
        return {
            'level': level,
            'level_name': level_name,
            'alliance_name': alliance.name if alliance else None,
            'alliance_id': alliance_id,
            'capabilities': capabilities,
            'can_see_self': level in ['basic', 'alliance', 'confederation', 'empire', 'hegemony'],
            'can_see_alliance': level in ['alliance', 'confederation', 'empire', 'hegemony'],
            'can_see_confederation': level in ['confederation', 'empire', 'hegemony'],
            'can_see_root_causes': level in ['empire', 'hegemony'],
            'can_predict_impact': level in ['empire', 'hegemony'],
            'can_see_all': level == 'hegemony'
        }
    
    def query_illumination(self, organism_id: str, query_type: str, 
                           target_event_id: Optional[str] = None,
                           causation_explorer=None) -> Dict[str, Any]:
        """
        Query the Illumination Engine with access control.
        
        Organisms can only query what their civilization level permits.
        This is how organisms ACCESS their causation data.
        
        Args:
            organism_id: The organism making the query
            query_type: Type of query ('self', 'alliance', 'root_causes', 'impact', 'all')
            target_event_id: Optional specific event to query
            causation_explorer: The CausationExplorer instance to query
            
        Returns:
            Query results filtered by access level, or error if unauthorized
        """
        illumination = self.get_organism_illumination_level(organism_id)
        
        # Access control
        if illumination['level'] == 'none':
            return {
                'error': 'No Illumination Access',
                'message': 'Form or join an alliance with 3+ members to access causation data',
                'required': 'illumination_basic'
            }
        
        if query_type == 'self' and not illumination['can_see_self']:
            return {'error': 'Insufficient Access', 'required': 'illumination_basic'}
        
        if query_type == 'alliance' and not illumination['can_see_alliance']:
            return {'error': 'Insufficient Access', 'required': 'illumination_alliance'}
        
        if query_type in ['root_causes', 'impact'] and not illumination['can_see_root_causes']:
            return {'error': 'Insufficient Access', 'required': 'illumination_empire'}
        
        if query_type == 'all' and not illumination['can_see_all']:
            return {'error': 'Insufficient Access', 'required': 'illumination_hegemony'}
        
        # Perform query if explorer provided
        if causation_explorer is None:
            return {
                'authorized': True,
                'level': illumination['level'],
                'query_type': query_type,
                'message': 'Query authorized but no CausationExplorer provided'
            }
        
        try:
            if query_type == 'self':
                # Get events for this organism only
                events = causation_explorer.get_events_by_component(f'organism_{organism_id}')
                return {
                    'authorized': True,
                    'level': illumination['level'],
                    'events': events[:50],  # Limit results
                    'total_events': len(events)
                }
            
            elif query_type == 'alliance':
                # Get events for all alliance members
                alliance_id = illumination['alliance_id']
                alliance = self.alliances.get(alliance_id)
                if not alliance:
                    return {'error': 'Alliance not found'}
                
                all_events = []
                for member_id in alliance.members:
                    events = causation_explorer.get_events_by_component(f'organism_{member_id}')
                    all_events.extend(events)
                
                return {
                    'authorized': True,
                    'level': illumination['level'],
                    'alliance': alliance.name,
                    'events': all_events[:100],
                    'total_events': len(all_events)
                }
            
            elif query_type == 'root_causes' and target_event_id:
                # Deep root cause analysis (Empire+ only)
                results = causation_explorer.find_root_causes(target_event_id)
                return {
                    'authorized': True,
                    'level': illumination['level'],
                    **results
                }
            
            elif query_type == 'impact' and target_event_id:
                # Impact analysis (Empire+ only)
                results = causation_explorer.analyze_impact(target_event_id)
                return {
                    'authorized': True,
                    'level': illumination['level'],
                    **results
                }
            
            elif query_type == 'all':
                # Full access (Hegemony only)
                timeline = causation_explorer.get_timeline()
                consequential = causation_explorer.get_most_consequential(limit=20)
                return {
                    'authorized': True,
                    'level': 'hegemony',
                    'level_name': 'Hegemonic Omniscience',
                    'timeline': timeline,
                    'most_consequential': consequential,
                    'message': 'Full causation data access granted'
                }
            
            else:
                return {'error': f'Unknown query type: {query_type}'}
                
        except Exception as e:
            return {'error': str(e), 'query_type': query_type}
    
    def get_civilization_status(self) -> Dict[str, Any]:
        """
        Get overall civilization status across all organisms.
        
        Returns summary of:
        - Total alliances and confederations
        - Illumination levels achieved
        - Civilization milestones
        """
        status = {
            'total_alliances': len(self.alliances),
            'total_confederations': len(self.confederations),
            'total_treaties': len(getattr(self, 'active_treaties', {})),
            'illumination_distribution': {
                'none': 0,
                'basic': 0,
                'alliance': 0,
                'confederation': 0,
                'empire': 0,
                'hegemony': 0
            },
            'civilization_milestones': []
        }
        
        # Count illumination levels
        for alliance_id, caps in self.alliance_capabilities.items():
            if 'illumination_hegemony' in caps:
                status['illumination_distribution']['hegemony'] += 1
            elif 'illumination_empire' in caps:
                status['illumination_distribution']['empire'] += 1
            elif 'illumination_confederation' in caps:
                status['illumination_distribution']['confederation'] += 1
            elif 'illumination_alliance' in caps:
                status['illumination_distribution']['alliance'] += 1
            elif 'illumination_basic' in caps:
                status['illumination_distribution']['basic'] += 1
            else:
                status['illumination_distribution']['none'] += 1
        
        # Check milestones
        if status['total_alliances'] >= 1:
            status['civilization_milestones'].append('First Alliance Formed')
        if any('illumination_basic' in caps for caps in self.alliance_capabilities.values()):
            status['civilization_milestones'].append('First Illumination Unlocked')
        if status['total_confederations'] >= 1:
            status['civilization_milestones'].append('First Confederation Established')
        if status['total_treaties'] >= 1:
            status['civilization_milestones'].append('First Peace Treaty Signed')
        if any('illumination_empire' in caps for caps in self.alliance_capabilities.values()):
            status['civilization_milestones'].append('Empire Level Illumination Achieved')
        if any('illumination_hegemony' in caps for caps in self.alliance_capabilities.values()):
            status['civilization_milestones'].append('Hegemonic Omniscience Attained')
        
        return status

    # ═══════════════════════════════════════════════════════════════════════
    # ORGANISM DECISION INTERFACE
    # These are the actions organisms can CHOOSE to take
    # ═══════════════════════════════════════════════════════════════════════
    
    def organism_create_alliance(self, organism_id: str, alliance_name: str) -> Optional[str]:
        """
        Organism CHOOSES to create a new alliance.
        
        The organism names it themselves. No auto-generation.
        
        Returns:
            Alliance ID if created, None if failed
        """
        # Check if organism is already in an alliance
        current_alliance = self.get_organism_alliance(organism_id)
        if current_alliance:
            self.logger.info(f"⚠️ {organism_id} already in alliance {current_alliance}")
            return None
        
        # Check max alliances
        if len(self.alliances) >= self.max_alliances:
            self.logger.info(f"⚠️ Max alliances reached ({self.max_alliances})")
            return None
        
        # Create alliance with organism's chosen name
        alliance_id = f"alliance_{organism_id}_{int(time.time())}"
        
        alliance = PlanetaryAlliance(
            alliance_id=alliance_id,
            name=alliance_name,  # ORGANISM'S CHOICE, not generated
            founder_id=organism_id
        )
        alliance.add_member(organism_id, AllianceRole.FOUNDER)
        
        self.alliances[alliance_id] = alliance
        
        # Update reputation
        rep = self._get_or_create_reputation(organism_id)
        rep.proposals_made += 1
        rep.proposals_accepted += 1  # Self-accepted
        
        self.logger.info(f"🪐 {organism_id} FOUNDED alliance '{alliance_name}'")
        self._emit_event('founded', {
            'founder': organism_id,
            'alliance_id': alliance_id,
            'name': alliance_name
        })
        
        # 📜 Record to Alliance History - FOUNDING EVENT
        # This is the birth of a civilization - the most important event
        self.record_historical_event(
            alliance_id=alliance_id,
            event_type=HistoricalEventType.ALLIANCE_FOUNDED,
            description=f"Alliance '{alliance_name}' founded by {organism_id}",
            primary_organism_id=organism_id,
            outcome="success",
            lesson="Every great civilization begins with a single organism's vision"
        )
        # Add founder as legendary organism
        history = self._get_or_create_history(alliance_id)
        if history:
            history.add_legend(
                organism_id=organism_id,
                role="Founder",
                achievements=[f"Founded {alliance_name}"],
                legacy=f"Visionary who founded {alliance_name} in round {self.round_number}"
            )
        
        return alliance_id
    
    def organism_propose_invite(self, proposer_id: str, target_id: str) -> Optional[str]:
        """
        Organism CHOOSES to invite another organism to their alliance.
        
        The target must ACCEPT or REJECT.
        
        Returns:
            Proposal ID if created, None if failed
        """
        alliance_id = self.get_organism_alliance(proposer_id)
        if not alliance_id:
            return None
        
        alliance = self.alliances[alliance_id]
        
        # Only warchief or founder can invite
        role = alliance.members.get(proposer_id)
        if role not in [AllianceRole.FOUNDER, AllianceRole.WARCHIEF, AllianceRole.DIPLOMAT]:
            self.logger.info(f"⚠️ {proposer_id} lacks authority to invite")
            return None
        
        # Target must not be in an alliance
        if self.get_organism_alliance(target_id):
            return None
        
        # Create proposal
        proposal_id = f"invite_{proposer_id}_{target_id}_{int(time.time())}"
        proposal = AllianceProposal(
            proposal_id=proposal_id,
            proposal_type=ProposalType.ALLIANCE_INVITE,
            proposer_id=proposer_id,
            target_id=target_id,
            context={'alliance_id': alliance_id, 'alliance_name': alliance.name}
        )
        
        # Add to pending - target organism must respond
        self.pending_global_proposals.append(proposal)
        
        # Update reputation
        rep = self._get_or_create_reputation(proposer_id)
        rep.proposals_made += 1
        
        self.logger.info(f"📨 {proposer_id} invited {target_id} to '{alliance.name}'")
        self._emit_event('invite_proposed', {
            'proposer': proposer_id,
            'target': target_id,
            'alliance': alliance.name
        })
        
        return proposal_id
    
    def organism_respond_to_invite(self, organism_id: str, proposal_id: str, 
                                   accept: bool) -> bool:
        """
        Organism CHOOSES to accept or reject an alliance invitation.
        
        Returns:
            True if response processed
        """
        # Find the proposal
        proposal = None
        for p in self.pending_global_proposals:
            if p.proposal_id == proposal_id and p.target_id == organism_id:
                proposal = p
                break
        
        if not proposal:
            return False
        
        if proposal.resolved:
            return False
        
        proposal.resolved = True
        proposal.accepted = accept
        proposal.resolution_time = time.time()
        
        # Update proposer reputation
        proposer_rep = self._get_or_create_reputation(proposal.proposer_id)
        
        if accept:
            proposer_rep.proposals_accepted += 1
            
            # Add to alliance
            alliance_id = proposal.context.get('alliance_id')
            if alliance_id and alliance_id in self.alliances:
                alliance = self.alliances[alliance_id]
                alliance.add_member(organism_id)
                
                self.logger.info(f"✅ {organism_id} JOINED '{alliance.name}'")
                self._emit_event('member_joined', {
                    'organism': organism_id,
                    'alliance': alliance.name,
                    'invited_by': proposal.proposer_id
                })
                
                # 📜 Record to Alliance History - New Member
                self.record_historical_event(
                    alliance_id=alliance_id,
                    event_type=HistoricalEventType.MEMBER_JOINED,
                    description=f"{organism_id} joined the alliance",
                    primary_organism_id=organism_id,
                    secondary_organism_id=proposal.proposer_id,
                    outcome="success",
                    lesson="The alliance grows stronger through unity"
                )
                
                # 🔮 Check if new member unlocks Illumination Engine capabilities
                newly_granted = self.check_and_grant_illumination(alliance_id)
                if newly_granted:
                    self._emit_event('civilization_progress', {
                        'alliance': alliance.name,
                        'new_capabilities': newly_granted,
                        'trigger': f'{organism_id} joined (member #{len(alliance.members)})'
                    })
                    
                    # 📜 Record civilization progress as historical milestone
                    self.record_historical_event(
                        alliance_id=alliance_id,
                        event_type=HistoricalEventType.MEMBER_JOINED,  # Sub-type - milestone
                        description=f"Civilization milestone: Gained {', '.join(newly_granted)}",
                        primary_organism_id=organism_id,
                        outcome="success",
                        lesson=f"Growth unlocked new capabilities: {', '.join(newly_granted)}"
                    )
        else:
            self.logger.info(f"❌ {organism_id} REJECTED invitation to '{proposal.context.get('alliance_name')}'")
            self._emit_event('invite_rejected', {
                'organism': organism_id,
                'alliance': proposal.context.get('alliance_name'),
                'invited_by': proposal.proposer_id
            })
        
        return True
    
    def organism_propose_war(self, proposer_id: str, target_alliance_id: str) -> Optional[str]:
        """
        Organism CHOOSES to propose war against another alliance.
        
        Alliance members must VOTE on whether to go to war.
        
        Returns:
            Proposal ID if created
        """
        alliance_id = self.get_organism_alliance(proposer_id)
        if not alliance_id:
            return None
        
        alliance = self.alliances[alliance_id]
        
        if target_alliance_id not in self.alliances:
            return None
        
        target = self.alliances[target_alliance_id]
        
        # Already at war?
        if target_alliance_id in alliance.at_war_with:
            return None
        
        # Create war proposal - needs alliance vote
        proposal_id = f"war_{alliance_id}_{target_alliance_id}_{int(time.time())}"
        proposal = AllianceProposal(
            proposal_id=proposal_id,
            proposal_type=ProposalType.WAR_DECLARATION,
            proposer_id=proposer_id,
            target_id=target_alliance_id,
            context={
                'proposer_alliance': alliance_id,
                'target_alliance': target_alliance_id,
                'target_name': target.name
            }
        )
        
        # Proposer automatically votes for
        proposal.votes_for.add(proposer_id)
        
        # Add to alliance pending proposals
        alliance.pending_proposals.append(proposal)
        
        # Update reputation
        rep = self._get_or_create_reputation(proposer_id)
        rep.proposals_made += 1
        
        self.logger.info(f"⚔️ {proposer_id} proposes WAR against '{target.name}' - voting required!")
        self._emit_event('war_proposed', {
            'proposer': proposer_id,
            'alliance': alliance.name,
            'target': target.name
        })
        
        return proposal_id
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🕊️ PEACE & TREATY SYSTEM - Mutual Respect Between Equals
    # NO SURRENDER. NO SUBJUGATION. Only peace between those of equal strength.
    # Treaties are strategic alliances, not submissions.
    # ═══════════════════════════════════════════════════════════════════════
    
    def organism_propose_peace(self, proposer_id: str, enemy_alliance_id: str,
                               terms: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Organism CHOOSES to propose peace with an enemy alliance.
        
        Peace requires BOTH alliances to agree AS EQUALS.
        NO SURRENDER. NO TRIBUTE. Only mutual non-aggression.
        
        Terms can include:
        - non_aggression_duration: How many rounds peace lasts
        - mutual_defense: If True, both defend each other against third parties
        - trade_agreement: Resource exchange rates
        - shared_territory: Jointly controlled zones
        
        NO TRIBUTE. NO SUBJUGATION. Equals only.
        
        Returns:
            Proposal ID if created
        """
        alliance_id = self.get_organism_alliance(proposer_id)
        if not alliance_id:
            return None
        
        alliance = self.alliances[alliance_id]
        
        # Must be at war with target
        if enemy_alliance_id not in alliance.at_war_with:
            self.logger.info(f"⚠️ Cannot propose peace - not at war with target")
            return None
        
        if enemy_alliance_id not in self.alliances:
            return None
        
        enemy = self.alliances[enemy_alliance_id]
        
        # EQUALS ONLY: Check power balance - no peace if one side is vastly weaker
        # This prevents "surrender" - only mutual recognition of strength
        alliance_power = len(alliance.members) + alliance.wars_won
        enemy_power = len(enemy.members) + enemy.wars_won
        power_ratio = min(alliance_power, enemy_power) / max(alliance_power, enemy_power, 1)
        
        if power_ratio < 0.5:
            self.logger.info(f"⚠️ Cannot propose peace - power imbalance too great. Battle must decide.")
            return None
        
        # Set default terms - EQUALS TERMS ONLY
        if terms is None:
            terms = {
                'non_aggression_duration': 50,  # 50 rounds of peace
                'mutual_respect': True,
                'equals_treaty': True  # Flag that this is between equals
            }
        
        # REMOVE any subjugation terms
        terms.pop('tribute', None)
        terms.pop('surrender', None)
        terms.pop('vassalage', None)
        terms['equals_treaty'] = True
        
        # Create peace proposal
        proposal_id = f"peace_{alliance_id}_{enemy_alliance_id}_{int(time.time())}"
        proposal = AllianceProposal(
            proposal_id=proposal_id,
            proposal_type=ProposalType.PEACE_OFFER,
            proposer_id=proposer_id,
            target_id=enemy_alliance_id,
            context={
                'proposer_alliance': alliance_id,
                'proposer_name': alliance.name,
                'target_alliance': enemy_alliance_id,
                'target_name': enemy.name,
                'terms': terms,
                'needs_enemy_acceptance': True
            }
        )
        
        # Proposer votes for
        proposal.votes_for.add(proposer_id)
        
        # Add to BOTH alliances - needs approval from both sides
        alliance.pending_proposals.append(proposal)
        
        # Also add to global proposals so enemy can see and respond
        self.pending_global_proposals.append(proposal)
        
        # Update reputation - peace proposals show wisdom
        rep = self._get_or_create_reputation(proposer_id)
        rep.proposals_made += 1
        
        self.logger.info(f"🕊️ {proposer_id} proposes PEACE with '{enemy.name}' - requires both sides to agree!")
        self._emit_event('peace_proposed', {
            'proposer': proposer_id,
            'alliance': alliance.name,
            'target': enemy.name,
            'terms': terms
        })
        
        return proposal_id
    
    def organism_respond_to_peace(self, organism_id: str, proposal_id: str,
                                  accept: bool) -> bool:
        """
        Organism from ENEMY alliance responds to peace offer.
        
        Peace is only established if:
        1. Proposing alliance voted to accept (majority)
        2. Enemy alliance representative accepts
        
        Returns:
            True if response processed
        """
        # Find the proposal
        proposal = None
        for p in self.pending_global_proposals:
            if p.proposal_id == proposal_id and p.proposal_type == ProposalType.PEACE_OFFER:
                proposal = p
                break
        
        if not proposal:
            return False
        
        # Verify organism is from the target alliance
        organism_alliance = self.get_organism_alliance(organism_id)
        if organism_alliance != proposal.target_id:
            self.logger.info(f"⚠️ {organism_id} cannot respond to peace - not from target alliance")
            return False
        
        if proposal.resolved:
            return False
        
        # Check if organism has authority to negotiate (warchief/founder/diplomat)
        target_alliance = self.alliances.get(proposal.target_id)
        if target_alliance:
            role = target_alliance.members.get(organism_id)
            if role not in [AllianceRole.FOUNDER, AllianceRole.WARCHIEF, AllianceRole.DIPLOMAT]:
                self.logger.info(f"⚠️ {organism_id} lacks authority to negotiate peace")
                return False
        
        proposal.resolved = True
        proposal.accepted = accept
        proposal.resolution_time = time.time()
        
        if accept:
            # PEACE ESTABLISHED
            self._establish_peace(proposal)
            self.logger.info(f"🕊️✅ PEACE ESTABLISHED between '{proposal.context['proposer_name']}' and '{proposal.context['target_name']}'!")
        else:
            self.logger.info(f"🕊️❌ {organism_id} REJECTED peace offer - war continues!")
            self._emit_event('peace_rejected', {
                'rejector': organism_id,
                'proposer_alliance': proposal.context['proposer_name'],
                'target_alliance': proposal.context['target_name']
            })
        
        return True
    
    def _establish_peace(self, proposal: AllianceProposal):
        """
        Establish peace between two alliances based on agreed terms.
        
        Creates a Treaty that binds both alliances.
        """
        proposer_alliance_id = proposal.context['proposer_alliance']
        target_alliance_id = proposal.target_id
        terms = proposal.context.get('terms', {})
        
        proposer = self.alliances.get(proposer_alliance_id)
        target = self.alliances.get(target_alliance_id)
        
        if not proposer or not target:
            return
        
        # End the war
        proposer.at_war_with.discard(target_alliance_id)
        target.at_war_with.discard(proposer_alliance_id)
        
        # Create treaty
        treaty_id = f"treaty_{proposer_alliance_id}_{target_alliance_id}_{int(time.time())}"
        
        # Store treaty in both alliances
        treaty = {
            'treaty_id': treaty_id,
            'parties': [proposer_alliance_id, target_alliance_id],
            'party_names': [proposer.name, target.name],
            'terms': terms,
            'established': time.time(),
            'expires': time.time() + (terms.get('non_aggression_duration', 50) * 60),  # Convert rounds to approx seconds
            'violations': 0
        }
        
        # Store in global treaties
        if not hasattr(self, 'active_treaties'):
            self.active_treaties = {}
        self.active_treaties[treaty_id] = treaty
        
        # Add to alliance peace treaties
        if not hasattr(proposer, 'peace_treaties'):
            proposer.peace_treaties = set()
        if not hasattr(target, 'peace_treaties'):
            target.peace_treaties = set()
        
        proposer.peace_treaties.add(treaty_id)
        target.peace_treaties.add(treaty_id)
        
        # Apply terms
        if terms.get('territory_exchange'):
            # Handle territory exchanges
            for territory_name, from_to in terms['territory_exchange'].items():
                # from_to is (from_alliance, to_alliance)
                pass  # Implement territory transfer
        
        # Update reputations - peace makers gain respect
        for org_id in list(proposer.members.keys()) + list(target.members.keys()):
            rep = self._get_or_create_reputation(org_id)
            if not hasattr(rep, 'peace_treaties_signed'):
                rep.peace_treaties_signed = 0
            rep.peace_treaties_signed += 1
        
        self._emit_event('peace_established', {
            'treaty_id': treaty_id,
            'alliances': [proposer.name, target.name],
            'terms': terms,
            'duration': terms.get('non_aggression_duration', 50)
        })
        
        # 📜 Record to Alliance History - PEACE ESTABLISHED
        # Both alliances learn from this moment of wisdom
        self.record_historical_event(
            alliance_id=proposer_alliance_id,
            event_type=HistoricalEventType.PEACE_ACCEPTED,
            description=f"Peace established with {target.name}",
            primary_organism_id=proposal.proposer_id,
            enemy_alliance_id=target_alliance_id,
            outcome="success",
            lesson=f"Peace brings stability. Treaty terms: {terms.get('non_aggression_duration', 50)} rounds"
        )
        self.record_historical_event(
            alliance_id=target_alliance_id,
            event_type=HistoricalEventType.PEACE_ACCEPTED,
            description=f"Peace established with {proposer.name}",
            enemy_alliance_id=proposer_alliance_id,
            outcome="success",
            lesson=f"Former enemies became partners. Strength in diplomacy."
        )
    
    def check_treaty_violations(self, alliance_id: str, action: str, 
                                target_id: str) -> Optional[str]:
        """
        Check if an action would violate an existing treaty.
        
        Returns:
            Treaty ID if violation would occur, None if action is allowed
        """
        if not hasattr(self, 'active_treaties'):
            return None
        
        if alliance_id not in self.alliances:
            return None
        
        alliance = self.alliances[alliance_id]
        
        # Check if there's an active treaty with the target
        if not hasattr(alliance, 'peace_treaties'):
            return None
        
        for treaty_id in alliance.peace_treaties:
            if treaty_id not in self.active_treaties:
                continue
            
            treaty = self.active_treaties[treaty_id]
            
            # Check if treaty is still active
            if time.time() > treaty.get('expires', 0):
                continue
            
            # Check if target is the other party
            if target_id in treaty['parties']:
                if action in ['war_declaration', 'attack', 'betray']:
                    return treaty_id
        
        return None
    
    def organism_break_treaty(self, organism_id: str, treaty_id: str,
                              reason: str = "strategic_necessity") -> bool:
        """
        Organism CHOOSES to break a treaty.
        
        This has severe reputation consequences but may be strategically necessary.
        
        Returns:
            True if treaty broken
        """
        if not hasattr(self, 'active_treaties'):
            return False
        
        if treaty_id not in self.active_treaties:
            return False
        
        treaty = self.active_treaties[treaty_id]
        
        # Verify organism is from one of the treaty parties
        organism_alliance = self.get_organism_alliance(organism_id)
        if organism_alliance not in treaty['parties']:
            return False
        
        # Get the other party
        other_party_id = [p for p in treaty['parties'] if p != organism_alliance][0]
        other_party = self.alliances.get(other_party_id)
        
        # Break the treaty
        del self.active_treaties[treaty_id]
        
        # Remove from alliances
        breaker_alliance = self.alliances.get(organism_alliance)
        if breaker_alliance and hasattr(breaker_alliance, 'peace_treaties'):
            breaker_alliance.peace_treaties.discard(treaty_id)
        if other_party and hasattr(other_party, 'peace_treaties'):
            other_party.peace_treaties.discard(treaty_id)
        
        # SEVERE reputation penalty
        rep = self._get_or_create_reputation(organism_id)
        if not hasattr(rep, 'treaties_broken'):
            rep.treaties_broken = 0
        rep.treaties_broken += 1
        rep.alliances_betrayed += 1  # Treaty breaking = betrayal
        
        # Mark all members of the other alliance as betrayed
        if other_party:
            for member_id in other_party.members:
                other_rep = self._get_or_create_reputation(member_id)
                other_rep.betrayed_by.add(organism_id)
        
        self.logger.info(f"💔 {organism_id} BROKE TREATY with '{treaty['party_names'][1]}' - {reason}!")
        self._emit_event('treaty_broken', {
            'breaker': organism_id,
            'breaker_alliance': breaker_alliance.name if breaker_alliance else 'unknown',
            'victim_alliance': other_party.name if other_party else 'unknown',
            'reason': reason,
            'treaty_id': treaty_id
        })
        
        # 📜 Record to Alliance History - BETRAYAL
        # This is a dark moment in alliance history
        if organism_alliance:
            self.record_historical_event(
                alliance_id=organism_alliance,
                event_type=HistoricalEventType.MEMBER_BETRAYED,
                description=f"Broke treaty with {other_party.name if other_party else 'unknown'}. Reason: {reason}",
                primary_organism_id=organism_id,
                enemy_alliance_id=other_party_id,
                outcome="neutral",  # Strategic but costly
                lesson="Treaty-breaking has severe consequences. Trust is hard to rebuild."
            )
            # Update betrayal counter in history
            history = self.alliance_histories.get(organism_alliance)
            if history:
                history.total_betrayals += 1
        
        # Record for the victim alliance too
        if other_party_id in self.alliances:
            self.record_historical_event(
                alliance_id=other_party_id,
                event_type=HistoricalEventType.MEMBER_BETRAYED,
                description=f"Treaty broken by {breaker_alliance.name if breaker_alliance else 'unknown'}",
                primary_organism_id=organism_id,
                enemy_alliance_id=organism_alliance,
                outcome="failure",
                lesson=f"Trust was betrayed by {organism_id}. Remember this."
            )
        
        return True
    
    def get_active_treaties(self, alliance_id: str) -> List[Dict[str, Any]]:
        """Get all active treaties for an alliance."""
        if not hasattr(self, 'active_treaties'):
            return []
        
        treaties = []
        for treaty_id, treaty in self.active_treaties.items():
            if alliance_id in treaty['parties']:
                # Check if still active
                if time.time() <= treaty.get('expires', 0):
                    treaties.append(treaty)
        
        return treaties

    def organism_vote_on_proposal(self, organism_id: str, proposal_id: str, 
                                  vote_for: bool) -> bool:
        """
        Organism CHOOSES how to vote on a proposal.
        
        Returns:
            True if vote recorded
        """
        alliance_id = self.get_organism_alliance(organism_id)
        if not alliance_id:
            return False
        
        alliance = self.alliances[alliance_id]
        
        # Find proposal in alliance
        proposal = None
        for p in alliance.pending_proposals:
            if p.proposal_id == proposal_id:
                proposal = p
                break
        
        if not proposal or proposal.resolved:
            return False
        
        # Record vote
        if vote_for:
            proposal.votes_for.add(organism_id)
            proposal.votes_against.discard(organism_id)
        else:
            proposal.votes_against.add(organism_id)
            proposal.votes_for.discard(organism_id)
        
        self.logger.info(f"🗳️ {organism_id} voted {'FOR' if vote_for else 'AGAINST'} proposal {proposal.proposal_type.value}")
        
        # Check if proposal can be resolved
        self._check_proposal_resolution(alliance, proposal)
        
        return True
    
    def organism_betray_alliance(self, organism_id: str, 
                                 sabotage: bool = False) -> bool:
        """
        Organism CHOOSES to betray their alliance.
        
        Can simply leave, or sabotage (if mid-war).
        This permanently marks them as a betrayer.
        
        Returns:
            True if betrayal successful
        """
        alliance_id = self.get_organism_alliance(organism_id)
        if not alliance_id:
            return False
        
        alliance = self.alliances[alliance_id]
        
        # Is alliance at war?
        at_war = len(alliance.at_war_with) > 0
        is_betrayal = at_war  # Leaving during war = betrayal
        
        # Remove from alliance
        alliance.remove_member(organism_id, is_betrayal=is_betrayal)
        
        # Update reputation
        rep = self._get_or_create_reputation(organism_id)
        if is_betrayal:
            rep.alliances_betrayed += 1
            # Mark who they betrayed
            for member_id in alliance.members:
                rep.betrayed_whom.add(member_id)
                other_rep = self._get_or_create_reputation(member_id)
                other_rep.betrayed_by.add(organism_id)
            
            self.logger.info(f"🗡️ {organism_id} BETRAYED '{alliance.name}' during war!")
            self._emit_event('betrayal', {
                'betrayer': organism_id,
                'alliance': alliance.name,
                'sabotage': sabotage
            })
        else:
            self.logger.info(f"👋 {organism_id} left '{alliance.name}'")
            self._emit_event('member_left', {
                'organism': organism_id,
                'alliance': alliance.name
            })
        
        # If sabotage, damage the alliance
        if sabotage and at_war:
            # Reveal alliance info to enemies? Reduce morale? 
            # This could be expanded based on game design
            pass
        
        # Check if alliance collapses
        if len(alliance.members) < self.min_alliance_size:
            self._dissolve_alliance(alliance_id, reason="insufficient_members")
        
        return True
    
    def organism_challenge_leadership(self, challenger_id: str) -> Optional[str]:
        """
        Organism CHOOSES to challenge for alliance leadership.
        
        Alliance members vote on who should lead.
        
        Returns:
            Proposal ID if challenge created
        """
        alliance_id = self.get_organism_alliance(challenger_id)
        if not alliance_id:
            return None
        
        alliance = self.alliances[alliance_id]
        
        # Can't challenge if you're already warchief
        if alliance.warchief_id == challenger_id:
            return None
        
        # Create challenge proposal
        proposal_id = f"challenge_{challenger_id}_{int(time.time())}"
        proposal = AllianceProposal(
            proposal_id=proposal_id,
            proposal_type=ProposalType.LEADERSHIP_CHALLENGE,
            proposer_id=challenger_id,
            target_id=alliance.warchief_id,
            context={'current_leader': alliance.warchief_id}
        )
        
        # Challenger votes for self
        proposal.votes_for.add(challenger_id)
        
        # Current warchief votes against (if exists)
        if alliance.warchief_id:
            proposal.votes_against.add(alliance.warchief_id)
        
        alliance.pending_proposals.append(proposal)
        
        self.logger.info(f"👑 {challenger_id} challenges for leadership of '{alliance.name}'!")
        self._emit_event('leadership_challenge', {
            'challenger': challenger_id,
            'current_leader': alliance.warchief_id,
            'alliance': alliance.name
        })
        
        return proposal_id
    
    def organism_claim_territory(self, organism_id: str, 
                                 territory: TerritorialDomain) -> Optional[str]:
        """
        Organism CHOOSES to claim an uncontrolled territory for their alliance.
        
        Requires alliance vote to commit resources.
        
        Returns:
            Proposal ID if claim created
        """
        alliance_id = self.get_organism_alliance(organism_id)
        if not alliance_id:
            return None
        
        # Territory must be uncontrolled
        if territory not in self.uncontrolled_territories:
            return None
        
        alliance = self.alliances[alliance_id]
        
        # Create claim proposal
        proposal_id = f"claim_{territory.value}_{int(time.time())}"
        proposal = AllianceProposal(
            proposal_id=proposal_id,
            proposal_type=ProposalType.TERRITORY_CLAIM,
            proposer_id=organism_id,
            target_id=None,
            context={'territory': territory.value, 'alliance_id': alliance_id}
        )
        
        proposal.votes_for.add(organism_id)
        alliance.pending_proposals.append(proposal)
        
        self.logger.info(f"🌍 {organism_id} proposes claiming {territory.value} for '{alliance.name}'")
        self._emit_event('territory_claim_proposed', {
            'proposer': organism_id,
            'territory': territory.value,
            'alliance': alliance.name
        })
        
        return proposal_id
    
    # ═══════════════════════════════════════════════════════════════════════
    # CONFEDERATION (SUPER-ALLIANCE) INTERFACE
    # Alliances of Alliances - decided by alliance warchiefs
    # ═══════════════════════════════════════════════════════════════════════
    
    def alliance_create_confederation(self, alliance_id: str, 
                                      confederation_name: str) -> Optional[str]:
        """
        Alliance warchief CHOOSES to create a confederation (super-alliance).
        
        WHAT DETERMINES IF AN ALLIANCE CAN CREATE A CONFEDERATION:
        1. Must have a warchief (earned leadership)
        2. Must not already be in a confederation
        3. Must have won at least 1 war (proven strength)
        
        Returns:
            Confederation ID if created
        """
        if alliance_id not in self.alliances:
            return None
            
        alliance = self.alliances[alliance_id]
        
        # Must have a warchief
        if not alliance.warchief_id:
            self.logger.info(f"⚠️ Alliance '{alliance.name}' needs a warchief to create confederation")
            return None
        
        # Must not already be in a confederation
        if alliance_id in self.alliance_to_confederation:
            self.logger.info(f"⚠️ Alliance '{alliance.name}' already in a confederation")
            return None
        
        # Must have proven themselves (optional but recommended)
        if alliance.wars_won < 1:
            self.logger.info(f"⚠️ Alliance '{alliance.name}' should win a war first (earned, not given)")
        
        # Create confederation
        confederation_id = f"confed_{alliance_id}_{int(time.time())}"
        
        confederation = Confederation(
            confederation_id=confederation_id,
            name=confederation_name,
            founding_alliance_id=alliance_id,
            supreme_alliance_id=alliance_id
        )
        confederation.member_alliances[alliance_id] = time.time()
        
        # Copy alliance's territories as shared domains
        confederation.shared_knowledge_domains = set(alliance.controlled_territories)
        
        self.confederations[confederation_id] = confederation
        self.alliance_to_confederation[alliance_id] = confederation_id
        
        self.logger.info(f"🏛️ Alliance '{alliance.name}' FOUNDED confederation '{confederation_name}'")
        self._emit_event('confederation_founded', {
            'alliance': alliance.name,
            'confederation': confederation_name,
            'founder_warchief': alliance.warchief_id
        })
        
        return confederation_id
    
    def alliance_propose_confederation_invite(self, proposer_alliance_id: str,
                                               target_alliance_id: str) -> Optional[str]:
        """
        Alliance warchief proposes inviting another alliance to their confederation.
        
        WHAT MAKES AN ALLIANCE A GOOD CONFEDERATION CANDIDATE:
        1. Shared enemies (at war with same targets)
        2. Compatible territories (non-overlapping for synergy)
        3. Good reputation (trustworthy history)
        4. Similar power level (no parasites)
        
        The target alliance's warchief must VOTE to accept.
        """
        if proposer_alliance_id not in self.alliances:
            return None
        if target_alliance_id not in self.alliances:
            return None
            
        proposer = self.alliances[proposer_alliance_id]
        target = self.alliances[target_alliance_id]
        
        # Must be in a confederation
        if proposer_alliance_id not in self.alliance_to_confederation:
            return None
        
        # Target must NOT already be in a confederation
        if target_alliance_id in self.alliance_to_confederation:
            self.logger.info(f"⚠️ Alliance '{target.name}' already in a confederation")
            return None
        
        # Only warchief can invite
        if not proposer.warchief_id:
            return None
        
        confederation_id = self.alliance_to_confederation[proposer_alliance_id]
        confederation = self.confederations[confederation_id]
        
        # Create proposal
        proposal_id = f"confed_invite_{target_alliance_id}_{int(time.time())}"
        proposal = AllianceProposal(
            proposal_id=proposal_id,
            proposal_type=ProposalType.CONFEDERATION_INVITE,
            proposer_id=proposer.warchief_id,
            target_id=target_alliance_id,
            context={
                'confederation_id': confederation_id,
                'confederation_name': confederation.name,
                'proposer_alliance': proposer.name,
                'target_alliance': target.name
            }
        )
        
        self.pending_global_proposals.append(proposal)
        
        self.logger.info(f"📨 Alliance '{proposer.name}' invited '{target.name}' to confederation '{confederation.name}'")
        self._emit_event('confederation_invite_proposed', {
            'proposer_alliance': proposer.name,
            'target_alliance': target.name,
            'confederation': confederation.name
        })
        
        return proposal_id
    
    def alliance_respond_to_confederation_invite(self, alliance_id: str, 
                                                  proposal_id: str,
                                                  accept: bool) -> bool:
        """
        Alliance warchief CHOOSES to accept or reject confederation invitation.
        
        FACTORS THAT SHOULD INFLUENCE THIS DECISION:
        1. Is the confederation trustworthy? (betrayal history)
        2. Are we at war with any of their members?
        3. Will joining make us stronger or weaker?
        4. Do they control territories we want?
        """
        # Find proposal
        proposal = None
        for p in self.pending_global_proposals:
            if p.proposal_id == proposal_id and p.target_id == alliance_id:
                proposal = p
                break
        
        if not proposal or proposal.resolved:
            return False
        
        alliance = self.alliances.get(alliance_id)
        if not alliance or not alliance.warchief_id:
            return False
        
        proposal.resolved = True
        proposal.accepted = accept
        proposal.resolution_time = time.time()
        
        if accept:
            confederation_id = proposal.context.get('confederation_id')
            if confederation_id in self.confederations:
                confederation = self.confederations[confederation_id]
                confederation.member_alliances[alliance_id] = time.time()
                self.alliance_to_confederation[alliance_id] = confederation_id
                
                # Merge knowledge domains
                confederation.shared_knowledge_domains.update(alliance.controlled_territories)
                
                self.logger.info(f"✅ Alliance '{alliance.name}' JOINED confederation '{confederation.name}'")
                self._emit_event('alliance_joined_confederation', {
                    'alliance': alliance.name,
                    'confederation': confederation.name,
                    'total_alliances': len(confederation.member_alliances)
                })
                
                # 🔮 Grant Illumination Engine access to ALL member alliances
                # Joining a confederation unlocks higher-tier causation access!
                for member_alliance_id in confederation.member_alliances:
                    newly_granted = self.check_and_grant_illumination(member_alliance_id)
                    if newly_granted:
                        member_alliance = self.alliances.get(member_alliance_id)
                        self._emit_event('civilization_progress', {
                            'alliance': member_alliance.name if member_alliance else member_alliance_id,
                            'confederation': confederation.name,
                            'new_capabilities': newly_granted,
                            'trigger': f'Confederation membership'
                        })
        else:
            self.logger.info(f"❌ Alliance '{alliance.name}' REJECTED confederation invite")
        
        return True
    
    def confederation_propose_war(self, confederation_id: str,
                                   target_confederation_id: str,
                                   proposer_alliance_id: str) -> Optional[str]:
        """
        An alliance warchief proposes confederation-level war (MEGA WAR).
        
        WHAT JUSTIFIES CONFEDERATION WAR:
        1. Territory disputes (overlapping domain claims)
        2. Ideology conflict (incompatible knowledge bases)
        3. Defensive pact (ally confederation was attacked)
        4. Dominance push (attempting to become EMPIRE tier)
        
        ALL member alliance warchiefs must vote.
        """
        if confederation_id not in self.confederations:
            return None
        if target_confederation_id not in self.confederations:
            return None
        if proposer_alliance_id not in self.alliances:
            return None
            
        confederation = self.confederations[confederation_id]
        target = self.confederations[target_confederation_id]
        proposer = self.alliances[proposer_alliance_id]
        
        # Proposer must be in this confederation
        if proposer_alliance_id not in confederation.member_alliances:
            return None
        
        # Must be warchief
        if not proposer.warchief_id:
            return None
        
        # Already at war?
        if target_confederation_id in confederation.at_war_with_confederations:
            return None
        
        # Create mega-war proposal
        proposal_id = f"confed_war_{confederation_id}_{target_confederation_id}_{int(time.time())}"
        proposal = AllianceProposal(
            proposal_id=proposal_id,
            proposal_type=ProposalType.CONFEDERATION_WAR,
            proposer_id=proposer.warchief_id,
            target_id=target_confederation_id,
            context={
                'our_confederation': confederation.name,
                'target_confederation': target.name,
                'proposer_alliance': proposer.name
            }
        )
        
        # Proposer votes yes
        proposal.votes_for.add(proposer_alliance_id)
        
        self.pending_global_proposals.append(proposal)
        
        self.logger.info(f"⚔️🌍 MEGA-WAR PROPOSED: '{confederation.name}' vs '{target.name}'")
        self._emit_event('confederation_war_proposed', {
            'attacker_confederation': confederation.name,
            'defender_confederation': target.name,
            'proposer_alliance': proposer.name
        })
        
        return proposal_id
    
    def alliance_vote_confederation_war(self, alliance_id: str, proposal_id: str,
                                         vote_yes: bool) -> bool:
        """Alliance warchief votes on confederation war proposal."""
        proposal = None
        for p in self.pending_global_proposals:
            if p.proposal_id == proposal_id and p.proposal_type == ProposalType.CONFEDERATION_WAR:
                proposal = p
                break
        
        if not proposal or proposal.resolved:
            return False
        
        alliance = self.alliances.get(alliance_id)
        if not alliance or not alliance.warchief_id:
            return False
        
        # Must be member of the proposing confederation
        confederation_id = self.alliance_to_confederation.get(alliance_id)
        if not confederation_id:
            return False
        
        if vote_yes:
            proposal.votes_for.add(alliance_id)
            proposal.votes_against.discard(alliance_id)
        else:
            proposal.votes_against.add(alliance_id)
            proposal.votes_for.discard(alliance_id)
        
        # Check if vote is complete (all member alliances voted)
        confederation = self.confederations.get(confederation_id)
        if confederation:
            total_members = len(confederation.member_alliances)
            total_votes = len(proposal.votes_for) + len(proposal.votes_against)
            
            if total_votes >= total_members:
                # Resolve the vote
                vote_ratio = proposal.get_vote_ratio()
                proposal.resolved = True
                proposal.accepted = vote_ratio > 0.5  # Simple majority
                proposal.resolution_time = time.time()
                
                if proposal.accepted:
                    target_id = proposal.target_id
                    confederation.at_war_with_confederations.add(target_id)
                    
                    # Target confederation is also at war with us
                    if target_id in self.confederations:
                        self.confederations[target_id].at_war_with_confederations.add(confederation_id)
                    
                    self.logger.info(f"⚔️🌍 MEGA-WAR DECLARED: '{confederation.name}' vs '{self.confederations.get(target_id, {}).name}'")
                    self._emit_event('confederation_war_declared', {
                        'attacker': confederation.name,
                        'defender': self.confederations.get(target_id, Confederation("","","")).name,
                        'vote_ratio': vote_ratio
                    })
                else:
                    self.logger.info(f"🕊️ Confederation war proposal REJECTED (vote ratio: {vote_ratio:.2f})")
        
        return True
    
    def confederation_merge(self, confederation_id: str, target_confederation_id: str,
                            new_tier_name: str) -> Optional[str]:
        """
        Merge two confederations into a higher tier (EMPIRE or HEGEMONY).
        
        WHAT DETERMINES MEGA-ALLIANCE FORMATION:
        1. Victory Together - won confederation war as allies
        2. Complementary Domains - non-overlapping territories
        3. Mutual Trust - no betrayal history between them
        4. Combined Dominance - together control majority of a domain
        
        Both confederation supreme alliances must agree.
        """
        if confederation_id not in self.confederations:
            return None
        if target_confederation_id not in self.confederations:
            return None
            
        c1 = self.confederations[confederation_id]
        c2 = self.confederations[target_confederation_id]
        
        # Cannot merge if at war
        if target_confederation_id in c1.at_war_with_confederations:
            return None
        
        # Determine new tier
        max_tier = max(c1.tier.value, c2.tier.value)
        new_tier = ConfederationTier(min(max_tier + 1, 3))  # Cap at HEGEMONY
        
        # Create the mega-confederation
        mega_id = f"mega_{new_tier.name.lower()}_{int(time.time())}"
        
        mega = Confederation(
            confederation_id=mega_id,
            name=new_tier_name,
            tier=new_tier,
            founding_alliance_id=c1.founding_alliance_id,
            supreme_alliance_id=c1.supreme_alliance_id  # Original founder leads
        )
        
        # Add both as children
        mega.child_confederations.add(confederation_id)
        mega.child_confederations.add(target_confederation_id)
        
        # Set parent references
        c1.parent_confederation_id = mega_id
        c2.parent_confederation_id = mega_id
        
        # Merge all member alliances
        for alliance_id in c1.member_alliances:
            mega.member_alliances[alliance_id] = time.time()
        for alliance_id in c2.member_alliances:
            mega.member_alliances[alliance_id] = time.time()
        
        # Combine knowledge domains
        mega.shared_knowledge_domains = c1.shared_knowledge_domains | c2.shared_knowledge_domains
        
        # Combine war records
        mega.confederation_wars_won = c1.confederation_wars_won + c2.confederation_wars_won
        mega.confederation_wars_lost = c1.confederation_wars_lost + c2.confederation_wars_lost
        
        self.confederations[mega_id] = mega
        
        self.logger.info(f"🏛️👑 {new_tier.name} FORMED: '{new_tier_name}' ({len(mega.member_alliances)} alliances)")
        self._emit_event('mega_confederation_formed', {
            'name': new_tier_name,
            'tier': new_tier.name,
            'member_count': len(mega.member_alliances),
            'child_confederations': [c1.name, c2.name]
        })
        
        return mega_id
    
    def get_confederation_status(self, confederation_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a confederation."""
        if confederation_id not in self.confederations:
            return None
            
        c = self.confederations[confederation_id]
        
        # Calculate combined power
        def get_alliance(aid):
            return self.alliances.get(aid)
        
        def get_fitness(oid):
            for alliance in self.alliances.values():
                if oid in alliance.members:
                    return self._get_or_create_reputation(oid).get_trust_score()
            return 0.5
        
        status = c.to_dict()
        status['total_organisms'] = c.get_total_organisms(get_alliance)
        status['combined_power'] = c.get_confederation_power(get_alliance, get_fitness)
        
        can_elevate, reason = c.can_elevate_tier(get_alliance)
        status['can_elevate'] = can_elevate
        status['elevation_status'] = reason
        
        return status

    # ═══════════════════════════════════════════════════════════════════════
    # NEURAL ORGANISM DECISION INTEGRATION
    # These methods ask organisms to make decisions using their brains
    # ═══════════════════════════════════════════════════════════════════════
    
    def process_organism_alliance_decisions(self, organism, network_state: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Have an organism make alliance decisions using its neural network.
        
        This is the CORE integration - the organism's brain decides.
        
        Args:
            organism: NeuralOrganism instance (must have evaluate_alliance_decision method)
            network_state: Current network state for context
            
        Returns:
            Dict of actions taken and their results
        """
        results = {
            'organism_id': organism.species_id,
            'decisions_made': [],
            'actions_taken': []
        }
        
        # Get decision context
        context = self.get_alliance_decision_context(organism.species_id)
        
        # Check if organism has neural decision capability
        if not hasattr(organism, 'evaluate_alliance_decision'):
            return results  # No neural decision making available
        
        # Build trust history for context
        rep = self._get_or_create_reputation(organism.species_id)
        trust_history = {}
        for other_id, other_rep in self.organism_reputations.items():
            if other_id != organism.species_id:
                trust_history[other_id] = {
                    'trust_score': other_rep.get_trust_score(),
                    'threat_level': other_rep.get_threat_level(),
                    'betrayed_me': organism.species_id in other_rep.betrayed_whom
                }
        
        # === PENDING INVITE DECISIONS ===
        for invite in context.get('pending_invites', []):
            proposer_id = invite.get('from')
            proposal_id = invite.get('proposal_id')
            
            decision_context = {
                'target_id': proposer_id,
                'target_fitness': self.organism_reputations.get(proposer_id, OrganismReputation(proposer_id)).get_trust_score(),
                'alliance_name': invite.get('alliance_name'),
                'trust_history': trust_history,
                'betrayal_count': len(rep.betrayed_by),
                'threat_level': trust_history.get(proposer_id, {}).get('threat_level', 0.5)
            }
            
            decision, confidence, reasoning = organism.evaluate_alliance_decision(
                'accept_alliance', decision_context, network_state
            )
            
            results['decisions_made'].append({
                'type': 'accept_alliance',
                'decision': decision,
                'confidence': confidence,
                'reasoning': reasoning
            })
            
            # Execute the decision
            self.organism_respond_to_invite(organism.species_id, proposal_id, decision)
            if decision:
                results['actions_taken'].append(f"Joined alliance '{invite.get('alliance_name')}'")
        
        # === PENDING VOTE DECISIONS ===
        for vote in context.get('pending_votes', []):
            proposal_id = vote.get('proposal_id')
            proposal_type = vote.get('type')
            
            # Determine appropriate decision type
            if proposal_type == 'war_declaration':
                decision_type = 'vote_war'
            elif proposal_type == 'leadership_challenge':
                decision_type = 'challenge_leader'
            else:
                decision_type = 'vote_war'  # Generic vote
            
            decision_context = {
                'proposal_type': proposal_type,
                'proposer_id': vote.get('proposer'),
                'current_ratio': vote.get('current_ratio'),
                'trust_history': trust_history,
                'threat_level': 0.5,  # Could be enhanced with target-specific threat
                'war_risk': 0.4  # Base risk for voting
            }
            
            decision, confidence, reasoning = organism.evaluate_alliance_decision(
                decision_type, decision_context, network_state
            )
            
            results['decisions_made'].append({
                'type': decision_type,
                'decision': decision,
                'confidence': confidence,
                'reasoning': reasoning
            })
            
            # Execute vote
            self.organism_vote_on_proposal(organism.species_id, proposal_id, decision)
            results['actions_taken'].append(f"Voted {'FOR' if decision else 'AGAINST'} {proposal_type}")
        
        # === PROACTIVE DECISIONS (if in alliance) ===
        if context.get('in_alliance'):
            alliance_info = context.get('alliance_info', {})
            
            # Should I betray?
            if alliance_info.get('at_war'):
                betrayal_context = {
                    'target_id': None,
                    'alliance_strength': alliance_info.get('member_count', 1) / 10.0,
                    'trust_history': trust_history,
                    'threat_level': 0.6,  # At war = higher threat
                    'betrayal_count': len(rep.betrayed_by)
                }
                
                decision, confidence, reasoning = organism.evaluate_alliance_decision(
                    'betray_alliance', betrayal_context, network_state
                )
                
                if decision and confidence > 0.7:  # High confidence threshold for betrayal
                    results['decisions_made'].append({
                        'type': 'betray_alliance',
                        'decision': True,
                        'confidence': confidence,
                        'reasoning': reasoning
                    })
                    self.organism_betray_alliance(organism.species_id)
                    results['actions_taken'].append("BETRAYED alliance!")
            
            # Should I challenge leadership?
            if not alliance_info.get('is_warchief') and 'challenge_leadership' in context.get('available_actions', []):
                challenge_context = {
                    'target_id': alliance_info.get('warchief_id'),
                    'leader_fitness': 0.5,  # Would need actual fitness
                    'trust_history': trust_history,
                    'threat_level': 0.3
                }
                
                decision, confidence, reasoning = organism.evaluate_alliance_decision(
                    'challenge_leader', challenge_context, network_state
                )
                
                if decision and confidence > 0.6:
                    results['decisions_made'].append({
                        'type': 'challenge_leader',
                        'decision': True,
                        'confidence': confidence,
                        'reasoning': reasoning
                    })
                    self.organism_challenge_leadership(organism.species_id)
                    results['actions_taken'].append("Challenged for leadership!")
        
        # === ALLIANCE CREATION (if not in alliance) ===
        elif not context.get('in_alliance') and len(context.get('pending_invites', [])) == 0:
            # Consider creating own alliance
            if len(self.alliances) < self.max_alliances:
                create_context = {
                    'target_id': None,
                    'trust_history': trust_history,
                    'threat_level': 0.3,
                    'opportunity_score': organism.fitness
                }
                
                decision, confidence, reasoning = organism.evaluate_alliance_decision(
                    'propose_alliance', create_context, network_state
                )
                
                if decision and confidence > 0.5:
                    # Generate a name based on organism's identity
                    # In a full system, organism would choose/generate name
                    alliance_name = f"Dominion_{organism.species_id[:8]}"
                    
                    results['decisions_made'].append({
                        'type': 'create_alliance',
                        'decision': True,
                        'confidence': confidence,
                        'reasoning': reasoning
                    })
                    alliance_id = self.organism_create_alliance(organism.species_id, alliance_name)
                    if alliance_id:
                        results['actions_taken'].append(f"Founded alliance '{alliance_name}'!")
        
        return results
    
    def get_alliance_decision_context(self, organism_id: str) -> Dict[str, Any]:
        """
        Get context for organism neural network to make alliance decisions.
        
        This provides the information organisms need to DECIDE, not to automate.
        """
        context = {
            'organism_id': organism_id,
            'in_alliance': False,
            'alliance_info': None,
            'pending_invites': [],
            'pending_votes': [],
            'available_actions': [],
            'other_alliances': [],
            'uncontrolled_territories': [t.value for t in self.uncontrolled_territories],
            'reputation': None,
            'potential_allies': [],
            'potential_enemies': []
        }
        
        # Get organism reputation
        rep = self._get_or_create_reputation(organism_id)
        context['reputation'] = {
            'trust_score': rep.get_trust_score(),
            'threat_level': rep.get_threat_level(),
            'alliances_honored': rep.alliances_honored,
            'alliances_betrayed': rep.alliances_betrayed,
            'betrayed_by': list(rep.betrayed_by)
        }
        
        # Check current alliance status
        alliance_id = self.get_organism_alliance(organism_id)
        if alliance_id:
            context['in_alliance'] = True
            alliance = self.alliances[alliance_id]
            context['alliance_info'] = {
                'name': alliance.name,
                'role': alliance.members.get(organism_id, AllianceRole.MEMBER).value,
                'member_count': len(alliance.members),
                'at_war': len(alliance.at_war_with) > 0,
                'war_targets': list(alliance.at_war_with),
                'territories': [t.value for t in alliance.controlled_territories],
                'is_warchief': alliance.warchief_id == organism_id
            }
            
            # Pending votes in alliance
            for proposal in alliance.pending_proposals:
                if not proposal.resolved and organism_id not in proposal.votes_for and organism_id not in proposal.votes_against:
                    context['pending_votes'].append({
                        'proposal_id': proposal.proposal_id,
                        'type': proposal.proposal_type.value,
                        'proposer': proposal.proposer_id,
                        'current_ratio': proposal.get_vote_ratio()
                    })
            
            # Available actions for allied organism
            context['available_actions'] = ['vote', 'betray']
            if alliance.members.get(organism_id) in [AllianceRole.FOUNDER, AllianceRole.WARCHIEF]:
                context['available_actions'].extend(['invite', 'propose_war', 'claim_territory'])
            if alliance.warchief_id != organism_id:
                context['available_actions'].append('challenge_leadership')
        else:
            # Available actions for unallied organism
            context['available_actions'] = ['create_alliance', 'accept_invite', 'reject_invite']
            
            # Check pending invites for this organism
            for proposal in self.pending_global_proposals:
                if (proposal.target_id == organism_id and 
                    proposal.proposal_type == ProposalType.ALLIANCE_INVITE and
                    not proposal.resolved):
                    context['pending_invites'].append({
                        'proposal_id': proposal.proposal_id,
                        'from': proposal.proposer_id,
                        'alliance_name': proposal.context.get('alliance_name'),
                        'alliance_id': proposal.context.get('alliance_id')
                    })
        
        # Info about other alliances (for decision making)
        for aid, alliance in self.alliances.items():
            if aid != alliance_id:
                context['other_alliances'].append({
                    'alliance_id': aid,
                    'name': alliance.name,
                    'member_count': len(alliance.members),
                    'at_war_with_us': alliance_id in alliance.at_war_with if alliance_id else False,
                    'territories': len(alliance.controlled_territories)
                })
        
        return context
    
    def get_organism_alliance(self, organism_id: str) -> Optional[str]:
        """Get alliance ID for an organism, if any."""
        for alliance_id, alliance in self.alliances.items():
            if organism_id in alliance.members:
                return alliance_id
        return None
    
    # ═══════════════════════════════════════════════════════════════════════
    # PROPOSAL RESOLUTION (based on organism votes)
    # ═══════════════════════════════════════════════════════════════════════
    
    def _check_proposal_resolution(self, alliance: PlanetaryAlliance, 
                                   proposal: AllianceProposal):
        """Check if proposal has enough votes to resolve."""
        total_members = len(alliance.members)
        total_votes = len(proposal.votes_for) + len(proposal.votes_against)
        
        # Need at least half to have voted
        if total_votes < total_members * 0.5:
            return
        
        vote_ratio = proposal.get_vote_ratio()
        
        if vote_ratio >= self.vote_threshold:
            self._execute_proposal(alliance, proposal, accepted=True)
        elif (1 - vote_ratio) >= self.vote_threshold:
            self._execute_proposal(alliance, proposal, accepted=False)
    
    def _execute_proposal(self, alliance: PlanetaryAlliance, 
                         proposal: AllianceProposal, accepted: bool):
        """Execute a resolved proposal."""
        proposal.resolved = True
        proposal.accepted = accepted
        proposal.resolution_time = time.time()
        
        if not accepted:
            self.logger.info(f"❌ Proposal {proposal.proposal_type.value} REJECTED by '{alliance.name}'")
            return
        
        if proposal.proposal_type == ProposalType.WAR_DECLARATION:
            target_id = proposal.target_id
            if target_id in self.alliances:
                target = self.alliances[target_id]
                alliance.at_war_with.add(target_id)
                target.at_war_with.add(alliance.alliance_id)
                alliance.wars_declared += 1
                
                self.logger.info(f"⚔️ '{alliance.name}' DECLARES WAR on '{target.name}'!")
                self._emit_event('war_declared', {
                    'attacker': alliance.name,
                    'defender': target.name
                })
                
                # 📜 Record to Alliance History - War Declared
                self.record_historical_event(
                    alliance_id=alliance.alliance_id,
                    event_type=HistoricalEventType.WAR_DECLARED,
                    description=f"Declared war against {target.name}",
                    primary_organism_id=proposal.proposer_id,
                    enemy_alliance_id=target_id,
                    outcome="neutral",
                    lesson=f"Alliance chose aggression. Target: {target.name}"
                )
                # Also record for defender's history
                self.record_historical_event(
                    alliance_id=target_id,
                    event_type=HistoricalEventType.WAR_DECLARED,
                    description=f"War declared by {alliance.name}",
                    primary_organism_id=proposal.proposer_id,
                    enemy_alliance_id=alliance.alliance_id,
                    outcome="neutral",
                    lesson=f"Alliance was attacked. Aggressor: {alliance.name}"
                )
        
        elif proposal.proposal_type == ProposalType.LEADERSHIP_CHALLENGE:
            old_leader = alliance.warchief_id
            alliance.warchief_id = proposal.proposer_id
            alliance.members[proposal.proposer_id] = AllianceRole.WARCHIEF
            if old_leader and old_leader in alliance.members:
                alliance.members[old_leader] = AllianceRole.MEMBER
            
            self.logger.info(f"👑 {proposal.proposer_id} becomes WARCHIEF of '{alliance.name}'!")
            self._emit_event('new_warchief', {
                'new_leader': proposal.proposer_id,
                'old_leader': old_leader,
                'alliance': alliance.name
            })
            
            # 📜 Record to Alliance History - Leadership Change
            self.record_historical_event(
                alliance_id=alliance.alliance_id,
                event_type=HistoricalEventType.LEADERSHIP_CHANGE,
                description=f"{proposal.proposer_id} became Warchief, replacing {old_leader or 'vacant'}",
                primary_organism_id=proposal.proposer_id,
                secondary_organism_id=old_leader,
                outcome="success",
                lesson="Leadership transitions shape alliance direction"
            )
        
        elif proposal.proposal_type == ProposalType.TERRITORY_CLAIM:
            territory_value = proposal.context.get('territory')
            try:
                territory = TerritorialDomain(territory_value)
                if territory in self.uncontrolled_territories:
                    self.uncontrolled_territories.discard(territory)
                    alliance.controlled_territories.add(territory)
                    self.territory_control[territory] = alliance.alliance_id
                    
                    self.logger.info(f"🌍 '{alliance.name}' claims {territory.value}!")
                    self._emit_event('territory_claimed', {
                        'alliance': alliance.name,
                        'territory': territory.value
                    })
                    
                    # 📜 Record to Alliance History - Territory Claimed
                    self.record_historical_event(
                        alliance_id=alliance.alliance_id,
                        event_type=HistoricalEventType.TERRITORY_GAINED,
                        description=f"Claimed territory: {territory.value}",
                        primary_organism_id=proposal.proposer_id,
                        outcome="success",
                        lesson=f"Expansion into {territory.value} - new resources and responsibilities"
                    )
            except ValueError:
                pass
    
    def _dissolve_alliance(self, alliance_id: str, reason: str):
        """Dissolve an alliance."""
        if alliance_id not in self.alliances:
            return
        
        alliance = self.alliances[alliance_id]
        alliance_name = alliance.name  # Save before deletion
        
        # 📜 Record final entry in Alliance History before dissolution
        history = self.alliance_histories.get(alliance_id)
        if history:
            self.record_historical_event(
                alliance_id=alliance_id,
                event_type=HistoricalEventType.DISSOLUTION,
                description=f"Alliance '{alliance_name}' dissolved. Reason: {reason}",
                outcome="failure",
                lesson=f"The end came due to: {reason}. Remember what was learned."
            )
            # The history itself is preserved - future organisms might study it
        
        # Release territories
        for territory in alliance.controlled_territories:
            self.uncontrolled_territories.add(territory)
            if territory in self.territory_control:
                del self.territory_control[territory]
        
        # End any wars
        for enemy_id in alliance.at_war_with:
            if enemy_id in self.alliances:
                self.alliances[enemy_id].at_war_with.discard(alliance_id)
        
        self.logger.info(f"💀 '{alliance_name}' DISSOLVED ({reason})")
        self._emit_event('alliance_dissolved', {
            'alliance': alliance_name,
            'reason': reason
        })
        
        del self.alliances[alliance_id]
        # NOTE: We keep alliance_histories[alliance_id] - civilizations can study dead empires!
    
    # ═══════════════════════════════════════════════════════════════════════
    # WAR RESOLUTION (based on organism participation)
    # ═══════════════════════════════════════════════════════════════════════
    
    def resolve_war_round(self, alliance_id: str, enemy_id: str,
                         get_organism_fitness: Callable,
                         participating_organisms: Dict[str, bool]) -> Optional[Dict[str, Any]]:
        """
        Resolve one round of war between alliances.
        
        participating_organisms maps organism_id -> whether they're fighting
        (organisms CHOOSE whether to participate)
        """
        if alliance_id not in self.alliances or enemy_id not in self.alliances:
            return None
        
        alliance = self.alliances[alliance_id]
        enemy = self.alliances[enemy_id]
        
        if enemy_id not in alliance.at_war_with:
            return None
        
        # Calculate power from organisms who CHOSE to fight
        alliance_power = 0.0
        enemy_power = 0.0
        
        alliance_fighters = []
        enemy_fighters = []
        
        for org_id in alliance.members:
            if participating_organisms.get(org_id, False):
                try:
                    alliance_power += get_organism_fitness(org_id)
                    alliance_fighters.append(org_id)
                except:
                    pass
        
        for org_id in enemy.members:
            if participating_organisms.get(org_id, False):
                try:
                    enemy_power += get_organism_fitness(org_id)
                    enemy_fighters.append(org_id)
                except:
                    pass
        
        # No one fighting = stalemate
        if not alliance_fighters and not enemy_fighters:
            return {'result': 'stalemate', 'reason': 'no_combatants'}
        
        # Determine winner
        if alliance_power > enemy_power:
            winner, loser = alliance, enemy
            winner_power, loser_power = alliance_power, enemy_power
        else:
            winner, loser = enemy, alliance
            winner_power, loser_power = enemy_power, alliance_power
        
        margin = abs(alliance_power - enemy_power) / max(alliance_power + enemy_power, 0.1)
        
        result = {
            'winner': winner.name,
            'loser': loser.name,
            'winner_power': winner_power,
            'loser_power': loser_power,
            'margin': margin,
            'alliance_fighters': len(alliance_fighters),
            'enemy_fighters': len(enemy_fighters)
        }
        
        # Decisive victory ends war
        if margin > 0.5:
            # War ends
            alliance.at_war_with.discard(enemy_id)
            enemy.at_war_with.discard(alliance_id)
            
            winner.wars_won += 1
            loser.wars_lost += 1
            
            # Winner takes a territory from loser (if any)
            if loser.controlled_territories:
                stolen = loser.controlled_territories.pop()
                winner.controlled_territories.add(stolen)
                self.territory_control[stolen] = winner.alliance_id
                result['territory_stolen'] = stolen.value
            
            # Update reputations AND neural feedback
            for org_id in winner.members:
                rep = self._get_or_create_reputation(org_id)
                rep.alliances_honored += 1
                rep.wars_fought += 1
                rep.wars_won += 1
                # 🧠 NEURAL FEEDBACK: War victory → positive reinforcement
                self._record_neural_feedback(org_id, "war_won", True)
            
            for org_id in loser.members:
                rep = self._get_or_create_reputation(org_id)
                rep.alliances_honored += 1
                rep.wars_fought += 1
                # 🧠 NEURAL FEEDBACK: War defeat → negative reinforcement  
                self._record_neural_feedback(org_id, "war_lost", False)
            
            result['war_ended'] = True
            
            self.logger.info(f"🏆 '{winner.name}' DEFEATS '{loser.name}'! War ends.")
            self._emit_event('war_ended', result)
            
            # 📜 Record to Alliance History - WAR ENDED
            # This is a pivotal moment for both alliances
            self.record_historical_event(
                alliance_id=winner.alliance_id,
                event_type=HistoricalEventType.WAR_WON,
                description=f"Victory over {loser.name}! Margin: {margin:.1%}",
                enemy_alliance_id=loser.alliance_id,
                outcome="success",
                lesson=f"Victory came through strength ({winner_power:.1f} vs {loser_power:.1f})"
            )
            # Update win/loss counters
            winner_history = self.alliance_histories.get(winner.alliance_id)
            if winner_history:
                winner_history.wars_won += 1
                winner_history.total_wars += 1
                # Add legendary warriors
                for fighter_id in (alliance_fighters if winner == alliance else enemy_fighters):
                    winner_history.add_legend(
                        organism_id=fighter_id,
                        role="War Hero",
                        achievements=[f"Fought in decisive victory against {loser.name}"],
                        legacy=f"Warrior who helped secure victory with margin {margin:.1%} in round {self.round_number}"
                    )
            
            self.record_historical_event(
                alliance_id=loser.alliance_id,
                event_type=HistoricalEventType.WAR_LOST,
                description=f"Defeat by {winner.name}. Margin: {margin:.1%}",
                enemy_alliance_id=winner.alliance_id,
                outcome="failure",
                lesson=f"Defeat teaches humility. Power was {loser_power:.1f} vs {winner_power:.1f}"
            )
            loser_history = self.alliance_histories.get(loser.alliance_id)
            if loser_history:
                loser_history.wars_lost += 1
                loser_history.total_wars += 1
            
            # Record territory loss
            if result.get('territory_stolen'):
                self.record_historical_event(
                    alliance_id=loser.alliance_id,
                    event_type=HistoricalEventType.TERRITORY_LOST,
                    description=f"Lost territory {result['territory_stolen']} to {winner.name}",
                    enemy_alliance_id=winner.alliance_id,
                    outcome="failure",
                    lesson="Territory lost in war. The cost of defeat."
                )
        else:
            result['war_ended'] = False
            self.logger.info(f"⚔️ War continues: {winner.name} leads by {margin:.1%}")
        
        return result
    
    # ═══════════════════════════════════════════════════════════════════════
    # ROUND PROCESSING
    # ═══════════════════════════════════════════════════════════════════════
    
    def process_round(self, organisms: Dict[str, Any],
                     get_fitness: Callable,
                     causation_explorer: Optional[Any] = None) -> Dict[str, Any]:
        """
        Process one round of alliance warfare.
        
        This does NOT make decisions for organisms.
        It only:
        - Cleans up dead organisms
        - Times out old proposals
        - Checks for alliance collapse
        - Wires system references for Illumination Engine
        
        All actual decisions come from organisms.
        """
        self.round_number += 1
        
        results = {
            'round': self.round_number,
            'alliances': len(self.alliances),
            'proposals_timed_out': 0,
            'alliances_dissolved': 0
        }
        
        # Clean up dead organisms from alliances
        for alliance in list(self.alliances.values()):
            dead_members = [m for m in alliance.members if m not in organisms]
            for dead in dead_members:
                alliance.remove_member(dead)
            
            # Check for collapse
            if len(alliance.members) < self.min_alliance_size:
                self._dissolve_alliance(alliance.alliance_id, "insufficient_members")
                results['alliances_dissolved'] += 1
        
        # Time out old proposals
        current_time = time.time()
        for alliance in self.alliances.values():
            for proposal in alliance.pending_proposals:
                if not proposal.resolved:
                    age = current_time - proposal.timestamp
                    if age > self.proposal_timeout * 60:  # timeout in minutes
                        proposal.resolved = True
                        proposal.accepted = False
                        results['proposals_timed_out'] += 1
        
        # Clean up global proposals
        self.pending_global_proposals = [
            p for p in self.pending_global_proposals 
            if not p.resolved and (current_time - p.timestamp) < self.proposal_timeout * 60
        ]
        
        # 🧹 MEMORY LEAK FIX: Prune alliance histories periodically (every 100 rounds)
        if self.round_number % 100 == 0:
            events_pruned = 0
            for history in self.alliance_histories.values():
                events_pruned += history.prune_old_events(max_events=500)
            if events_pruned > 0:
                self.logger.info(f"🧹 Pruned {events_pruned} old history events")
            results['events_pruned'] = events_pruned
        
        # Sync confederation state to organisms for ML feature extraction
        # Also wires system references for Illumination Engine
        self.sync_organism_confederation_state(organisms, causation_explorer=causation_explorer)
        
        results['alliances'] = len(self.alliances)
        results['confederations'] = len(self.confederations)
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get current alliance warfare status."""
        return {
            'round': self.round_number,
            'alliance_count': len(self.alliances),
            'alliances': [a.to_dict() for a in self.alliances.values()],
            'uncontrolled_territories': [t.value for t in self.uncontrolled_territories],
            'territory_control': {t.value: aid for t, aid in self.territory_control.items()},
            'pending_proposals': len(self.pending_global_proposals),
            # Confederation (Super-Alliance) status
            'confederation_count': len(self.confederations),
            'confederations': [c.to_dict() for c in self.confederations.values()],
            'confederation_tiers': {
                'CONFEDERATION': sum(1 for c in self.confederations.values() if c.tier == ConfederationTier.CONFEDERATION),
                'EMPIRE': sum(1 for c in self.confederations.values() if c.tier == ConfederationTier.EMPIRE),
                'HEGEMONY': sum(1 for c in self.confederations.values() if c.tier == ConfederationTier.HEGEMONY)
            }
        }
    
    def sync_organism_confederation_state(self, organisms: Dict[str, Any],
                                          causation_explorer: Optional[Any] = None):
        """
        Sync confederation state to organism attributes for ML feature extraction.
        
        Updates each organism with:
        - alliance_id: Their current alliance
        - confederation_tier: 0=none, 1=confederation, 2=empire, 3=hegemony
        - confederation_wars_participated: Count of mega-wars they've been in
        - cross_alliance_connections: Connections to organisms in other alliances
        - system_references: Wire AllianceWarfareSystem and CausationExplorer for Illumination Engine
        """
        for org_id, org in organisms.items():
            # Find organism's alliance
            alliance_id = self.get_organism_alliance(org_id)
            
            if hasattr(org, 'alliance_id'):
                org.alliance_id = alliance_id
            
            # 🔮 ILLUMINATION ENGINE WIRING
            # Wire system references so organisms can access Alliance Wisdom
            if hasattr(org, 'set_system_references'):
                try:
                    # Only pass causation_explorer if it's not None to avoid issues
                    if causation_explorer is not None:
                        org.set_system_references(
                            alliance_warfare=self,
                            causation_explorer=causation_explorer
                        )
                    else:
                        org.set_system_references(alliance_warfare=self)
                except Exception:
                    pass  # Graceful degradation - not all organisms support this
            
            # Determine confederation tier
            tier = 0
            if alliance_id and alliance_id in self.alliance_to_confederation:
                confed_id = self.alliance_to_confederation[alliance_id]
                if confed_id in self.confederations:
                    confed = self.confederations[confed_id]
                    tier = confed.tier.value
                    
                    # Check if part of higher tier (parent confederation)
                    if confed.parent_confederation_id:
                        parent = self.confederations.get(confed.parent_confederation_id)
                        if parent:
                            tier = max(tier, parent.tier.value)
            
            if hasattr(org, 'confederation_tier'):
                org.confederation_tier = tier
            
            # Count cross-alliance connections (organisms in other alliances this one connects to)
            cross_connections = 0
            if hasattr(org, 'connections'):
                for conn_id in org.connections:
                    conn_alliance = self.get_organism_alliance(conn_id)
                    if conn_alliance and conn_alliance != alliance_id:
                        cross_connections += 1
            
            if hasattr(org, 'cross_alliance_connections'):
                org.cross_alliance_connections = cross_connections


# ═══════════════════════════════════════════════════════════════════════
# INTEGRATION
# ═══════════════════════════════════════════════════════════════════════

def integrate_alliance_warfare_with_highlander(
    highlander_protocol,
    alliance_system: Optional[AllianceWarfareSystem] = None,
    config: Optional[Dict] = None
) -> AllianceWarfareSystem:
    """
    Integrate Alliance Warfare with Highlander Protocol.
    
    Alliance decisions are made BY organisms, not FOR them.
    """
    if alliance_system is None:
        alliance_system = AllianceWarfareSystem(
            highlander_protocol=highlander_protocol,
            config=config,
            event_emitter=highlander_protocol.event_emitter if highlander_protocol else None
        )
    
    if highlander_protocol:
        highlander_protocol.alliance_warfare = alliance_system
    
    return alliance_system
