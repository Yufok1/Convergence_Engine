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
        
        # Territory control - starts EMPTY, must be claimed
        self.uncontrolled_territories: Set[TerritorialDomain] = set(TerritorialDomain)
        self.territory_control: Dict[TerritorialDomain, str] = {}  # territory -> alliance_id
        
        # War tracking
        self.active_wars: Dict[str, Dict[str, Any]] = {}  # war_id -> war state
        self.war_history: List[Dict[str, Any]] = []
        
        # Round tracking
        self.round_number = 0
    
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
            from kernel.causation_explorer import CausationEvent
            event = CausationEvent(
                event_type=f"alliance_{event_type}",
                component='alliance_warfare',
                severity=0.6,
                data={'round': self.round_number, **data}
            )
            self.event_emitter(event)
        except ImportError:
            pass
    
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
            except ValueError:
                pass
    
    def _dissolve_alliance(self, alliance_id: str, reason: str):
        """Dissolve an alliance."""
        if alliance_id not in self.alliances:
            return
        
        alliance = self.alliances[alliance_id]
        
        # Release territories
        for territory in alliance.controlled_territories:
            self.uncontrolled_territories.add(territory)
            if territory in self.territory_control:
                del self.territory_control[territory]
        
        # End any wars
        for enemy_id in alliance.at_war_with:
            if enemy_id in self.alliances:
                self.alliances[enemy_id].at_war_with.discard(alliance_id)
        
        self.logger.info(f"💀 '{alliance.name}' DISSOLVED ({reason})")
        self._emit_event('alliance_dissolved', {
            'alliance': alliance.name,
            'reason': reason
        })
        
        del self.alliances[alliance_id]
    
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
            
            # Update reputations
            for org_id in winner.members:
                rep = self._get_or_create_reputation(org_id)
                rep.alliances_honored += 1
                rep.wars_fought += 1
                rep.wars_won += 1
            
            for org_id in loser.members:
                rep = self._get_or_create_reputation(org_id)
                rep.alliances_honored += 1
                rep.wars_fought += 1
            
            result['war_ended'] = True
            
            self.logger.info(f"🏆 '{winner.name}' DEFEATS '{loser.name}'! War ends.")
            self._emit_event('war_ended', result)
        else:
            result['war_ended'] = False
            self.logger.info(f"⚔️ War continues: {winner.name} leads by {margin:.1%}")
        
        return result
    
    # ═══════════════════════════════════════════════════════════════════════
    # ROUND PROCESSING
    # ═══════════════════════════════════════════════════════════════════════
    
    def process_round(self, organisms: Dict[str, Any],
                     get_fitness: Callable) -> Dict[str, Any]:
        """
        Process one round of alliance warfare.
        
        This does NOT make decisions for organisms.
        It only:
        - Cleans up dead organisms
        - Times out old proposals
        - Checks for alliance collapse
        
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
        
        results['alliances'] = len(self.alliances)
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get current alliance warfare status."""
        return {
            'round': self.round_number,
            'alliance_count': len(self.alliances),
            'alliances': [a.to_dict() for a in self.alliances.values()],
            'uncontrolled_territories': [t.value for t in self.uncontrolled_territories],
            'territory_control': {t.value: aid for t, aid in self.territory_control.items()},
            'pending_proposals': len(self.pending_global_proposals)
        }


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
