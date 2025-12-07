"""
WIKAI Observer - The Passive Listener

This module watches the Convergence Engine event stream and automatically
captures patterns worthy of the Commons.

The Observer answers three questions:
1. WHAT IS THE SIGNAL? - When does something become WIKAI-worthy?
2. WHAT IS THE HANDSHAKE? - How do we detect and capture?
3. WHAT GETS RECORDED? - What metadata matters?

Integration:
    from wikai.observer import WIKAIObserver
    
    # In unified_entry.py, after causation_explorer is created:
    observer = WIKAIObserver(causation_explorer, librarian)
    observer.start_watching()

The butterflies don't know they're being studied. They just fly.
WIKAI quietly records every time they discover something true.
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)

# Import the Librarian (will be available when installed as package)
try:
    from .librarian import WIKAILibrarian, WIKAIPattern
except ImportError:
    from wikai.librarian import WIKAILibrarian, WIKAIPattern


class PatternCandidate:
    """
    A potential pattern being observed before capture.
    
    Patterns must demonstrate stability before being committed to the Commons.
    This prevents capturing noise - only genuine convergence gets recorded.
    """
    
    def __init__(
        self,
        signature: str,
        first_seen: datetime,
        trigger_event: Dict[str, Any]
    ):
        self.signature = signature  # Hash of the pattern's key features
        self.first_seen = first_seen
        self.last_seen = first_seen
        self.trigger_event = trigger_event
        self.supporting_events: List[Dict[str, Any]] = []
        self.stability_readings: List[float] = []
        self.fitness_readings: List[float] = []
        self.observation_count = 1
        
        # Extracted features
        self.dominant_tokens: List[str] = []
        self.emergent_tokens: List[str] = []
        self.reasoning_chain: List[str] = []
        self.agents_involved: List[str] = []
        
    def add_observation(self, event: Dict[str, Any], stability: float, fitness: float):
        """Record another observation of this pattern."""
        self.last_seen = datetime.utcnow()
        self.supporting_events.append(event)
        self.stability_readings.append(stability)
        self.fitness_readings.append(fitness)
        self.observation_count += 1
    
    @property
    def duration_seconds(self) -> float:
        """How long has this pattern been observed?"""
        return (self.last_seen - self.first_seen).total_seconds()
    
    @property
    def avg_stability(self) -> float:
        """Average stability score across observations."""
        return sum(self.stability_readings) / len(self.stability_readings) if self.stability_readings else 0.0
    
    @property
    def avg_fitness(self) -> float:
        """Average fitness across observations."""
        return sum(self.fitness_readings) / len(self.fitness_readings) if self.fitness_readings else 0.0
    
    @property
    def fitness_delta(self) -> float:
        """Change in fitness from first to last observation."""
        if len(self.fitness_readings) < 2:
            return 0.0
        return self.fitness_readings[-1] - self.fitness_readings[0]
    
    def is_mature(
        self,
        min_observations: int = 3,
        min_duration_seconds: float = 30.0,
        min_stability: float = 0.7
    ) -> bool:
        """
        Has this pattern demonstrated enough stability to capture?
        
        A pattern is mature when it:
        - Has been observed multiple times
        - Has persisted for a minimum duration
        - Shows consistent stability above threshold
        """
        return (
            self.observation_count >= min_observations and
            self.duration_seconds >= min_duration_seconds and
            self.avg_stability >= min_stability
        )


class WIKAIObserver:
    """
    The Observer - watches the event stream for WIKAI-worthy patterns.
    
    This is a passive listener that hooks into the CausationExplorer's
    event stream. It watches for specific signals that indicate a
    pattern has emerged worth capturing.
    
    Capture Triggers:
    1. CONVERGENCE: High fitness delta + high stability
    2. EMERGENCE: Novel tokens appearing in organism vocabulary
    3. SYNTHESIS: Dialectical resolution (thesis + antithesis → new state)
    4. ALLIANCE: Successful cooperation between previously hostile agents
    
    The Observer doesn't intervene. It just records.
    """
    
    def __init__(
        self,
        causation_explorer: Optional[Any] = None,
        librarian: Optional[WIKAILibrarian] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the Observer.
        
        Args:
            causation_explorer: The CausationExplorer to watch
            librarian: The Librarian to capture patterns to
            config: Observer configuration
        """
        self.causation_explorer = causation_explorer
        self.librarian = librarian or WIKAILibrarian()
        
        # Configuration with defaults
        config = config or {}
        self.config = {
            # Capture thresholds
            'min_fitness_delta': config.get('min_fitness_delta', 0.3),
            'min_stability_score': config.get('min_stability_score', 0.85),
            'min_observations': config.get('min_observations', 3),
            'min_duration_seconds': config.get('min_duration_seconds', 30.0),
            
            # Event types to watch
            'watch_event_types': config.get('watch_event_types', [
                'highlander_champion',
                'alliance_formed',
                'alliance_war_resolved',
                'concept_emergence',
                'health_state_change',
                'neural_training',
                'phenotype_emergence',
                'organism_communication',
                'confederation_founded',
                'mega_confederation_formed',
            ]),
            
            # Polling interval (seconds)
            'poll_interval': config.get('poll_interval', 5.0),
            
            # Auto-validation threshold
            'auto_validate_replication': config.get('auto_validate_replication', 3),
        }
        
        # Pattern candidates being observed
        self._candidates: Dict[str, PatternCandidate] = {}
        self._candidates_lock = threading.Lock()
        
        # Captured pattern signatures (to avoid duplicates)
        self._captured_signatures: set = set()
        
        # Event buffer for analysis
        self._recent_events: List[Dict[str, Any]] = []
        self._events_lock = threading.Lock()
        
        # Observer state
        self._watching = False
        self._watch_thread: Optional[threading.Thread] = None
        self._last_event_count = 0
        
        # Metrics
        self.metrics = {
            'events_processed': 0,
            'candidates_created': 0,
            'patterns_captured': 0,
            'patterns_validated': 0,
        }
        
        logger.info(f"🦋 WIKAI Observer initialized (watching {len(self.config['watch_event_types'])} event types)")
    
    def _send_debug_log(self, message: str, log_type: str = 'info'):
        """Send a debug log entry to the web UI."""
        try:
            from wikai.web_ui import add_debug_log
            add_debug_log(message, log_type)
        except ImportError:
            pass  # Web UI not loaded
        except Exception:
            pass  # Non-critical
    
    def start_watching(self):
        """Start the observer in a background thread."""
        if self._watching:
            return
        
        self._watching = True
        self._watch_thread = threading.Thread(
            target=self._watch_loop,
            daemon=True,
            name="WIKAI-Observer"
        )
        self._watch_thread.start()
        logger.info("🦋 WIKAI Observer started watching")
    
    def stop_watching(self):
        """Stop the observer."""
        self._watching = False
        if self._watch_thread:
            self._watch_thread.join(timeout=5.0)
        logger.info("🦋 WIKAI Observer stopped")
    
    def _watch_loop(self):
        """Main observation loop - polls for new events."""
        loop_count = 0
        while self._watching:
            try:
                self._process_new_events()
                self._evaluate_candidates()
                
                # Periodic status update every ~60 seconds (60 loops at 1s interval)
                loop_count += 1
                if loop_count % 60 == 0:
                    print(f"[WIKAI] 👁️ Observer status: {self.metrics['events_processed']} events | {len(self._candidates)} candidates | {self.metrics['patterns_captured']} captured")
                    
            except Exception as e:
                logger.error(f"🦋 WIKAI Observer error: {e}")
            
            time.sleep(self.config['poll_interval'])
    
    def _process_new_events(self):
        """Check for new events from the CausationExplorer."""
        if not self.causation_explorer:
            return
        
        try:
            # Get current event count
            current_count = len(self.causation_explorer.events)
            
            if current_count <= self._last_event_count:
                return  # No new events
            
            # Get new events
            all_events = list(self.causation_explorer.events.values())
            new_events = all_events[self._last_event_count:]
            self._last_event_count = current_count
            
            # Process each new event
            for event in new_events:
                self._analyze_event(event)
                self.metrics['events_processed'] += 1
            
            # Send debug update to web UI periodically
            if self.metrics['events_processed'] % 50 == 0:
                self._send_debug_log(f"Processed {self.metrics['events_processed']} events, {len(self._candidates)} candidates", 'info')
                
        except Exception as e:
            logger.error(f"🦋 Error processing events: {e}")
    
    def _analyze_event(self, event: Any):
        """
        Analyze a single event for WIKAI-worthiness.
        
        This is where we answer: "What is the signal?"
        """
        event_type = getattr(event, 'event_type', None)
        if not event_type:
            return
        
        # Only watch configured event types
        if event_type not in self.config['watch_event_types']:
            return
        
        event_data = event.to_dict() if hasattr(event, 'to_dict') else vars(event)
        
        # Extract key metrics
        stability = self._extract_stability(event_data)
        fitness = self._extract_fitness(event_data)
        tokens = self._extract_tokens(event_data)
        
        # Send event to debug log
        self._send_debug_log(f"[{event_type}] stab={stability:.2f} fit={fitness:.2f}", 'event')
        
        # Generate pattern signature (unique identifier for this type of pattern)
        signature = self._generate_signature(event_type, tokens)
        
        with self._candidates_lock:
            if signature in self._candidates:
                # Existing candidate - add observation
                self._candidates[signature].add_observation(event_data, stability, fitness)
                cand = self._candidates[signature]
                self._send_debug_log(f"Candidate updated: {signature[:15]}... obs={cand.observation_count} stab={cand.avg_stability:.2f}", 'candidate')
            else:
                # New candidate - start observing
                candidate = PatternCandidate(
                    signature=signature,
                    first_seen=datetime.utcnow(),
                    trigger_event=event_data
                )
                candidate.dominant_tokens = tokens.get('dominant', [])
                candidate.emergent_tokens = tokens.get('emergent', [])
                candidate.add_observation(event_data, stability, fitness)
                
                self._candidates[signature] = candidate
                self.metrics['candidates_created'] += 1
                
                logger.debug(f"🦋 New pattern candidate: {signature[:20]}... ({event_type})")
    
    def _evaluate_candidates(self):
        """Evaluate candidates and capture mature patterns."""
        with self._candidates_lock:
            signatures_to_remove = []
            
            for signature, candidate in self._candidates.items():
                # Skip already captured
                if signature in self._captured_signatures:
                    signatures_to_remove.append(signature)
                    continue
                
                # Check if mature enough to capture
                if candidate.is_mature(
                    min_observations=self.config['min_observations'],
                    min_duration_seconds=self.config['min_duration_seconds'],
                    min_stability=self.config['min_stability_score']
                ):
                    # Check fitness delta threshold
                    if candidate.fitness_delta >= self.config['min_fitness_delta'] or \
                       candidate.avg_stability >= 0.9:  # Very stable patterns always capture
                        
                        self._capture_pattern(candidate)
                        self._captured_signatures.add(signature)
                        signatures_to_remove.append(signature)
                
                # Clean up stale candidates (not seen in 5 minutes)
                elif candidate.duration_seconds > 300 and candidate.observation_count < 2:
                    signatures_to_remove.append(signature)
            
            # Remove processed/stale candidates
            for sig in signatures_to_remove:
                del self._candidates[sig]
    
    def _capture_pattern(self, candidate: PatternCandidate):
        """
        Capture a mature pattern to the Commons.
        
        This is where we answer: "What gets recorded?"
        """
        try:
            # Generate name from tokens
            name = self._generate_pattern_name(candidate)
            
            # Extract problem/solution/axiom from events
            problem, solution, axiom = self._extract_wisdom(candidate)
            
            # Build reasoning chain from supporting events
            reasoning_chain = self._build_reasoning_chain(candidate)
            
            # Capture to librarian
            pattern_id = self.librarian.capture(
                name=name,
                experiment_id=f"convergence_auto_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                agents=candidate.agents_involved or ["convergence_engine"],
                problem=problem,
                solution=solution,
                axiom=axiom,
                reasoning_chain=reasoning_chain,
                tokens={
                    'dominant_tokens': candidate.dominant_tokens,
                    'emergent_tokens': candidate.emergent_tokens
                },
                mechanism={
                    'synthesis': {
                        'stability_score': candidate.avg_stability,
                        'fitness_delta': candidate.fitness_delta
                    }
                },
                metrics={
                    'state_delta': candidate.fitness_delta,
                    'cycles_to_convergence': candidate.observation_count,
                    'avg_stability': candidate.avg_stability,
                    'avg_fitness': candidate.avg_fitness,
                    'duration_seconds': candidate.duration_seconds
                },
                tags=self._generate_tags(candidate),
                observer_agent="wikai_observer",
                source_project="convergence_engine"
            )
            
            self.metrics['patterns_captured'] += 1
            
            # LOUD announcement so you don't miss it!
            print("\n" + "=" * 60)
            print(f"📸 WIKAI CAPTURE! Pattern #{self.metrics['patterns_captured']}")
            print(f"   ID:    {pattern_id}")
            print(f"   Name:  {name}")
            print(f"   Axiom: \"{axiom}\"")
            print(f"   Stability: {candidate.avg_stability:.2f} | Fitness Δ: {candidate.fitness_delta:.2f}")
            print("=" * 60 + "\n")
            
            logger.info(f"🦋 WIKAI Captured: {pattern_id} - {name}")
            
            # Send to debug log
            self._send_debug_log(f"🎉 CAPTURED: {pattern_id} - {name}", 'capture')
            
            # Notify web UI feed
            try:
                from wikai.web_ui import notify_capture
                notify_capture(pattern_id, name, axiom)
            except ImportError:
                pass  # Web UI not loaded
            except Exception:
                pass  # Non-critical
            
            return pattern_id
            
        except Exception as e:
            logger.error(f"🦋 Failed to capture pattern: {e}")
            return None
    
    # ═══════════════════════════════════════════════════════════════════════════
    # EXTRACTION HELPERS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _extract_stability(self, event_data: Dict[str, Any]) -> float:
        """Extract stability score from event data."""
        # Try common stability field names
        for key in ['stability_score', 'stability', 'health', 'coherence', 
                    'synthesis_score', 'convergence_score']:
            if key in event_data.get('data', {}):
                val = event_data['data'][key]
                if isinstance(val, (int, float)):
                    return float(val)
        
        # Default moderate stability for observed events
        return 0.5
    
    def _extract_fitness(self, event_data: Dict[str, Any]) -> float:
        """Extract fitness from event data."""
        data = event_data.get('data', {})
        
        for key in ['fitness', 'avg_fitness', 'best_fitness', 'collective_fitness',
                    'winner_fitness', 'champion_fitness']:
            if key in data:
                val = data[key]
                if isinstance(val, (int, float)):
                    return float(val)
        
        return 0.0
    
    def _extract_tokens(self, event_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract dominant and emergent tokens from event data."""
        data = event_data.get('data', {})
        tokens = {'dominant': [], 'emergent': []}
        
        # Look for token-related fields
        for key in ['tokens', 'words', 'vocabulary', 'concepts']:
            if key in data and isinstance(data[key], list):
                tokens['dominant'].extend(data[key][:5])
        
        # Emergent tokens from synthesis/novel fields
        for key in ['emergent_tokens', 'novel_concepts', 'new_words', 'synthesis']:
            if key in data and isinstance(data[key], list):
                tokens['emergent'].extend(data[key][:3])
        
        # Add event type as implicit token
        event_type = event_data.get('event_type', '')
        if event_type:
            tokens['dominant'].append(event_type.replace('_', ' '))
        
        return tokens
    
    def _generate_signature(self, event_type: str, tokens: Dict[str, List[str]]) -> str:
        """Generate a unique signature for this pattern type."""
        import hashlib
        
        # Combine event type and sorted tokens
        key_parts = [event_type] + sorted(tokens.get('dominant', []))[:3]
        key_string = '|'.join(key_parts)
        
        return hashlib.md5(key_string.encode()).hexdigest()[:16]
    
    def _generate_pattern_name(self, candidate: PatternCandidate) -> str:
        """Generate a human-readable name for the pattern."""
        event_type = candidate.trigger_event.get('event_type', 'unknown')
        
        # Use emergent tokens if available
        if candidate.emergent_tokens:
            token_part = ' '.join(candidate.emergent_tokens[:2]).title()
            return f"The {token_part} Protocol"
        
        # Use dominant tokens
        if candidate.dominant_tokens:
            token_part = ' '.join(candidate.dominant_tokens[:2]).title()
            return f"The {token_part} Pattern"
        
        # Fallback to event type
        type_words = event_type.replace('_', ' ').title()
        return f"The {type_words} Protocol"
    
    def _extract_wisdom(self, candidate: PatternCandidate) -> tuple:
        """Extract problem/solution/axiom from candidate."""
        event_type = candidate.trigger_event.get('event_type', '')
        data = candidate.trigger_event.get('data', {})
        
        # Default extractions based on event type
        if 'alliance' in event_type:
            problem = "Conflict between separate agents"
            solution = "Alliance formation for mutual benefit"
            axiom = "Unity amplifies individual strength"
        elif 'champion' in event_type:
            problem = "Competition for dominance"
            solution = "Survival of the most adapted"
            axiom = "Excellence emerges from challenge"
        elif 'concept' in event_type:
            problem = "Pattern recognition in complex data"
            solution = "Concept crystallization through repetition"
            axiom = "Meaning emerges from consistent observation"
        elif 'confederation' in event_type:
            problem = "Scaling cooperation beyond local alliances"
            solution = "Hierarchical super-structures emerge"
            axiom = "Networks of networks create civilizations"
        else:
            problem = f"Challenge observed in {event_type}"
            solution = f"Resolution achieved with stability {candidate.avg_stability:.2f}"
            axiom = "Stable patterns propagate; unstable patterns dissolve"
        
        return problem, solution, axiom
    
    def _build_reasoning_chain(self, candidate: PatternCandidate) -> List[str]:
        """Build reasoning chain from candidate's observations."""
        chain = []
        
        # Add trigger event
        trigger_type = candidate.trigger_event.get('event_type', 'unknown')
        chain.append(f"Trigger: {trigger_type} observed")
        
        # Add observation summary
        chain.append(f"Pattern observed {candidate.observation_count} times over {candidate.duration_seconds:.1f}s")
        
        # Add stability trend
        if len(candidate.stability_readings) > 1:
            trend = "increasing" if candidate.stability_readings[-1] > candidate.stability_readings[0] else "stable"
            chain.append(f"Stability {trend}: {candidate.stability_readings[0]:.2f} → {candidate.stability_readings[-1]:.2f}")
        
        # Add fitness delta
        if candidate.fitness_delta != 0:
            direction = "improved" if candidate.fitness_delta > 0 else "adjusted"
            chain.append(f"Fitness {direction} by {abs(candidate.fitness_delta):.3f}")
        
        # Add conclusion
        chain.append(f"Pattern crystallized with avg stability {candidate.avg_stability:.2f}")
        
        return chain
    
    def _generate_tags(self, candidate: PatternCandidate) -> List[str]:
        """Generate tags for the captured pattern."""
        tags = []
        
        # Add event type as tag
        event_type = candidate.trigger_event.get('event_type', '')
        if event_type:
            tags.append(event_type)
        
        # Add stability-based tags
        if candidate.avg_stability >= 0.9:
            tags.append('highly_stable')
        elif candidate.avg_stability >= 0.7:
            tags.append('stable')
        
        # Add fitness-based tags
        if candidate.fitness_delta > 0.5:
            tags.append('high_fitness_gain')
        elif candidate.fitness_delta > 0.2:
            tags.append('fitness_improvement')
        
        # Add convergence tags
        if candidate.observation_count >= 5:
            tags.append('well_observed')
        
        # Add source tag
        tags.append('auto_captured')
        tags.append('convergence_engine')
        
        return tags
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_candidates(self) -> List[Dict[str, Any]]:
        """Get current pattern candidates being observed."""
        with self._candidates_lock:
            return [
                {
                    'signature': c.signature,
                    'event_type': c.trigger_event.get('event_type'),
                    'observations': c.observation_count,
                    'avg_stability': c.avg_stability,
                    'fitness_delta': c.fitness_delta,
                    'duration': c.duration_seconds,
                    'is_mature': c.is_mature(
                        self.config['min_observations'],
                        self.config['min_duration_seconds'],
                        self.config['min_stability_score']
                    )
                }
                for c in self._candidates.values()
            ]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get observer metrics."""
        return {
            **self.metrics,
            'active_candidates': len(self._candidates),
            'captured_signatures': len(self._captured_signatures),
            'is_watching': self._watching,
            'config': self.config
        }
    
    def force_capture(self, signature: str) -> Optional[str]:
        """Force capture of a specific candidate (for manual intervention)."""
        with self._candidates_lock:
            if signature not in self._candidates:
                return None
            
            candidate = self._candidates[signature]
            pattern_id = self._capture_pattern(candidate)
            
            if pattern_id:
                self._captured_signatures.add(signature)
                del self._candidates[signature]
            
            return pattern_id
    
    def __repr__(self):
        return f"<WIKAIObserver: {self.metrics['patterns_captured']} captured, {len(self._candidates)} candidates>"


# Convenience function to wire observer to unified_entry
def create_observer_for_convergence(
    causation_explorer: Any,
    librarian: Optional[WIKAILibrarian] = None,
    fitness_delta_threshold: float = 0.15,
    stability_threshold: float = 0.85,
    cycle_threshold: int = 20
) -> WIKAIObserver:
    """
    Create and start a WIKAI Observer for the Convergence Engine.
    
    Args:
        causation_explorer: The CausationExplorer instance to watch
        librarian: Optional WIKAILibrarian (creates one if not provided)
        fitness_delta_threshold: Minimum fitness improvement to trigger capture
        stability_threshold: Minimum stability score to trigger capture
        cycle_threshold: Minimum cycles/observations before capture
    
    Usage in unified_entry.py:
        from wikai.observer import create_observer_for_convergence
        
        # After causation_explorer is created:
        wikai_observer = create_observer_for_convergence(self.causation_explorer)
    """
    # Create observer with custom thresholds
    observer = WIKAIObserver(
        causation_explorer=causation_explorer,
        librarian=librarian
    )
    
    # Override thresholds if specified
    observer.config['min_fitness_delta'] = fitness_delta_threshold
    observer.config['min_stability_score'] = stability_threshold
    observer.config['min_observations'] = max(3, cycle_threshold // 5)  # Scale down for observations
    
    observer.start_watching()
    return observer


if __name__ == "__main__":
    # Demo/test mode
    print("🦋 WIKAI Observer - Passive Listener for AI Patterns")
    print("=" * 50)
    
    observer = WIKAIObserver()
    print(f"Configuration: {observer.config}")
    print(f"Watching event types: {observer.config['watch_event_types']}")
    print("\nTo integrate with Convergence Engine:")
    print("  from wikai.observer import create_observer_for_convergence")
    print("  observer = create_observer_for_convergence(causation_explorer)")
