"""
📊 SYSTEM REPORT - Live Aggregate Intelligence

The inverse of config.json: While config tells the system what to do,
this report tells YOU what IS happening.

This is your currency report - informational wealth, not a data dump.
Dynamic, live, meaningful aggregation of all system outputs.

Usage:
    from system_report import SystemReporter
    reporter = SystemReporter(unified_system)
    report = reporter.generate()  # Returns dict
    reporter.save('report.json')  # Saves timestamped report
    reporter.print_summary()      # Human-readable console output
"""

import json
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict, field
from collections import defaultdict
import statistics


def _format_count(count: int) -> str:
    """Format large numbers for display (shorthand)."""
    if count >= 1_000_000_000:
        return f"{count / 1_000_000_000:.1f}B"
    elif count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    elif count >= 1_000:
        return f"{count / 1_000:.1f}K"
    return str(count)


@dataclass
class PopulationMetrics:
    """Current population state"""
    total_organisms: int = 0
    active_organisms: int = 0
    fallen_organisms: int = 0
    fitness_mean: float = 0.0
    fitness_std: float = 0.0
    fitness_min: float = 0.0
    fitness_max: float = 0.0
    age_mean: float = 0.0
    age_max: int = 0
    generation_mean: float = 0.0
    generation_max: int = 0


@dataclass
class HighlanderMetrics:
    """Tournament/Competition state"""
    phase: str = "unknown"
    round_number: int = 0
    total_battles: int = 0
    battles_this_round: int = 0
    eliminations_total: int = 0
    champions_crowned: int = 0
    predation_enabled: bool = False
    survival_threshold: float = 0.0
    competition_intensity: float = 0.0


@dataclass
class AllianceMetrics:
    """Alliance system state"""
    active_alliances: int = 0
    total_members: int = 0
    largest_alliance_size: int = 0
    confederations: int = 0
    wars_in_progress: int = 0
    alliance_formations_total: int = 0
    dissolutions_total: int = 0
    betrayals_total: int = 0
    # New expanded metrics
    territories_claimed: int = 0
    territories_unclaimed: int = 0
    wars_won_total: int = 0
    wars_lost_total: int = 0
    ultimatums_issued: int = 0
    peace_treaties_signed: int = 0
    legends_recorded: int = 0
    warchief_count: int = 0


@dataclass
class NeuralMetrics:
    """Neural training state"""
    organisms_with_brains: int = 0
    total_training_steps: int = 0
    avg_loss: float = 0.0
    avg_epsilon: float = 0.0
    experience_buffer_total: int = 0
    gym_episodes_total: int = 0
    gym_reward_mean: float = 0.0


@dataclass
class LanguageMetrics:
    """Language/Vocabulary state with mastery tracking"""
    total_vocabulary_words: int = 0
    unique_words_across_pop: int = 0
    avg_vocab_per_organism: float = 0.0
    word_adoptions_total: int = 0
    semantic_associations: int = 0
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🎓 MASTERY LEVEL DISTRIBUTION - THE HEART OF VOCABULARY EVOLUTION
    # ═══════════════════════════════════════════════════════════════════════════
    # Level 0: 6 words (foundation)
    # Level 1: 26 words (specialization begins)
    # Level 2: 76 words (expertise)
    # Level 3: 276 words (mastery)
    # Level 4: unlimited (transcendence)
    # ═══════════════════════════════════════════════════════════════════════════
    mastery_level_0: int = 0  # Foundation (6 words)
    mastery_level_1: int = 0  # Specialized (26 words)
    mastery_level_2: int = 0  # Expert (76 words)
    mastery_level_3: int = 0  # Master (276 words)
    mastery_level_4: int = 0  # Transcendent (unlimited)
    highest_mastery_achieved: int = 0
    avg_mastery_level: float = 0.0
    
    # Progress tracking for organisms working toward next level
    avg_breadth_ratio: float = 0.0  # How diverse is word usage across frames
    avg_depth_ratio: float = 0.0   # How deep is mastery within frames
    avg_experience_progress: float = 0.0  # Progress toward next level's experience req
    
    # Behavioral specialization tracking
    dominant_behaviors: Dict[str, int] = field(default_factory=dict)  # e.g., {'warriors': 5, 'diplomats': 12}


@dataclass
class LanguageGameBridgeMetrics:
    """Language-Game Bridge correlation metrics (meta-brain feedback)"""
    active: bool = False
    source_count: int = 0  # Number of active bridges
    episodes_tracked: int = 0  # Total episodes with vocabulary influence
    win_rate: float = 0.0  # Win rate in tracked episodes
    avg_reward: float = 0.0  # Average reward in tracked episodes
    vocabulary_game_alignment: float = 0.0  # How well vocabulary correlates with success (-1 to 1)
    language_decision_influence: float = 0.0  # How much vocabulary affects decisions (0 to 1)
    concept_diversity: float = 0.0  # Breadth of concepts used (0 to 1)
    unique_concepts_total: int = 0  # Total unique concepts encountered
    bias_strength: float = 0.3  # Current config value
    learning_rate: float = 0.1  # Current config value


@dataclass
class NetworkMetrics:
    """Symbiotic network state"""
    connections: int = 0
    network_density: float = 0.0
    communities: int = 0
    clustering_coefficient: float = 0.0
    stability_index: float = 0.0


@dataclass 
class EventMetrics:
    """Causation event tracking"""
    total_events: int = 0
    events_by_type: Dict[str, int] = field(default_factory=dict)
    events_last_minute: int = 0
    events_last_hour: int = 0


@dataclass
class ResourceMetrics:
    """System resource utilization"""
    ray_enabled: bool = False
    ray_cpus: int = 0
    ray_gpus: int = 0
    gpu_memory_used_mb: float = 0.0
    gpu_memory_total_mb: float = 0.0
    cpu_percent: float = 0.0
    memory_used_gb: float = 0.0
    memory_total_gb: float = 0.0
    memory_percent: float = 0.0
    breath_cycle: int = 0
    breath_depth: float = 0.0
    breath_phase: str = "unknown"
    uptime_seconds: float = 0.0
    thread_count: int = 0


@dataclass
class SystemReport:
    """Complete system report - your informational wealth"""
    timestamp: str = ""
    config_name: str = ""
    
    population: PopulationMetrics = field(default_factory=PopulationMetrics)
    highlander: HighlanderMetrics = field(default_factory=HighlanderMetrics)
    alliances: AllianceMetrics = field(default_factory=AllianceMetrics)
    neural: NeuralMetrics = field(default_factory=NeuralMetrics)
    language: LanguageMetrics = field(default_factory=LanguageMetrics)
    language_game_bridge: LanguageGameBridgeMetrics = field(default_factory=LanguageGameBridgeMetrics)
    network: NetworkMetrics = field(default_factory=NetworkMetrics)
    events: EventMetrics = field(default_factory=EventMetrics)
    resources: ResourceMetrics = field(default_factory=ResourceMetrics)
    
    # Raw data for deep analysis
    top_organisms: List[Dict[str, Any]] = field(default_factory=list)
    recent_events: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class SystemReporter:
    """
    Generates comprehensive system reports from a running UnifiedSystem.
    
    This is your window into what's actually happening - not config,
    but the actual current state of every subsystem.
    """
    
    def __init__(self, unified_system=None):
        """
        Initialize reporter.
        
        Args:
            unified_system: Reference to UnifiedSystem instance
        """
        self.unified_system = unified_system
        self.start_time = time.time()
        self._last_report: Optional[SystemReport] = None
        
    def set_unified_system(self, unified_system):
        """Set/update the unified system reference"""
        self.unified_system = unified_system
        
    def generate(self) -> SystemReport:
        """
        Generate a complete system report.
        
        Returns:
            SystemReport with all current metrics
        """
        report = SystemReport(
            timestamp=datetime.now().isoformat(),
            config_name=self._get_config_name()
        )
        
        # Gather all metrics
        report.population = self._gather_population_metrics()
        report.highlander = self._gather_highlander_metrics()
        report.alliances = self._gather_alliance_metrics()
        report.neural = self._gather_neural_metrics()
        report.language = self._gather_language_metrics()
        report.language_game_bridge = self._gather_language_game_bridge_metrics()
        report.network = self._gather_network_metrics()
        report.events = self._gather_event_metrics()
        report.resources = self._gather_resource_metrics()
        
        # Get top performers and recent activity
        report.top_organisms = self._get_top_organisms(10)
        report.recent_events = self._get_recent_events(20)
        report.warnings = self._check_warnings(report)
        
        self._last_report = report
        return report
    
    def _get_config_name(self) -> str:
        """Get current config file name"""
        if not self.unified_system:
            return "unknown"
        config_path = getattr(self.unified_system, 'config_path', None)
        if config_path:
            return Path(config_path).name
        return "unknown"
    
    def _gather_population_metrics(self) -> PopulationMetrics:
        """Gather population statistics"""
        metrics = PopulationMetrics()
        
        if not self.unified_system:
            return metrics
            
        try:
            organisms = self.unified_system.get_current_organisms()
            if not organisms:
                return metrics
                
            metrics.total_organisms = len(organisms)
            metrics.active_organisms = len(organisms)
            
            # Fitness stats
            fitnesses = []
            ages = []
            generations = []
            
            for org in organisms.values():
                if hasattr(org, 'fitness'):
                    fitnesses.append(org.fitness)
                if hasattr(org, 'age'):
                    ages.append(org.age)
                if hasattr(org, 'generation'):
                    generations.append(org.generation)
            
            if fitnesses:
                metrics.fitness_mean = statistics.mean(fitnesses)
                metrics.fitness_std = statistics.stdev(fitnesses) if len(fitnesses) > 1 else 0.0
                metrics.fitness_min = min(fitnesses)
                metrics.fitness_max = max(fitnesses)
            
            if ages:
                metrics.age_mean = statistics.mean(ages)
                metrics.age_max = max(ages)
            
            if generations:
                metrics.generation_mean = statistics.mean(generations)
                metrics.generation_max = max(generations)
            
            # Get fallen count from highlander
            highlander = getattr(self.unified_system, 'highlander_protocol', None)
            if highlander and hasattr(highlander, 'fallen'):
                metrics.fallen_organisms = len(highlander.fallen)
                
        except Exception as e:
            pass  # Silent fail, return partial metrics
            
        return metrics
    
    def _gather_highlander_metrics(self) -> HighlanderMetrics:
        """Gather tournament/competition statistics"""
        metrics = HighlanderMetrics()
        
        if not self.unified_system:
            return metrics
            
        try:
            highlander = getattr(self.unified_system, 'highlander_protocol', None)
            if not highlander:
                return metrics
            
            status = highlander.get_protocol_status()
            
            metrics.phase = status.get('phase', 'unknown')
            metrics.round_number = status.get('round', 0)
            metrics.total_battles = status.get('total_battles', 0)
            metrics.eliminations_total = status.get('total_fallen', 0)
            metrics.champions_crowned = status.get('champions', 0)
            metrics.predation_enabled = status.get('predation_enabled', False)
            
            config = status.get('config', {})
            metrics.survival_threshold = config.get('survival_threshold', 0.0)
            metrics.competition_intensity = config.get('competition_intensity', 0.0)
            
        except Exception as e:
            pass
            
        return metrics
    
    def _gather_alliance_metrics(self) -> AllianceMetrics:
        """Gather alliance system statistics"""
        metrics = AllianceMetrics()
        
        if not self.unified_system:
            return metrics
            
        try:
            alliance_sys = getattr(self.unified_system, 'alliance_warfare', None)
            if not alliance_sys:
                return metrics
            
            # Count active alliances
            alliances = getattr(alliance_sys, 'alliances', {})
            metrics.active_alliances = len(alliances)
            
            # Count total members and find largest
            total_members = 0
            largest = 0
            for alliance in alliances.values():
                members = getattr(alliance, 'members', set())
                member_count = len(members)
                total_members += member_count
                largest = max(largest, member_count)
            
            metrics.total_members = total_members
            metrics.largest_alliance_size = largest
            
            # Confederations
            confederations = getattr(alliance_sys, 'confederations', {})
            metrics.confederations = len(confederations)
            
            # Wars
            active_wars = getattr(alliance_sys, 'active_wars', {})
            metrics.wars_in_progress = len(active_wars)
            
            # Historical counts from stats if available
            stats = getattr(alliance_sys, 'stats', {})
            metrics.alliance_formations_total = stats.get('alliances_formed', 0)
            metrics.dissolutions_total = stats.get('alliances_dissolved', 0)
            metrics.betrayals_total = stats.get('betrayals', 0)
            
            # Territory metrics
            territory_control = getattr(alliance_sys, 'territory_control', {})
            uncontrolled = getattr(alliance_sys, 'uncontrolled_territories', set())
            metrics.territories_claimed = len(territory_control)
            metrics.territories_unclaimed = len(uncontrolled)
            
            # War history metrics
            war_history = getattr(alliance_sys, 'war_history', [])
            metrics.wars_won_total = sum(1 for w in war_history if w.get('outcome') == 'victory')
            metrics.wars_lost_total = sum(1 for w in war_history if w.get('outcome') == 'defeat')
            
            # Stats from alliance warfare
            metrics.ultimatums_issued = stats.get('ultimatums_issued', 0)
            metrics.peace_treaties_signed = stats.get('peace_treaties', 0)
            
            # Count warchiefs and legends
            warchief_count = 0
            legends_count = 0
            for alliance in alliances.values():
                if getattr(alliance, 'warchief_id', None):
                    warchief_count += 1
            metrics.warchief_count = warchief_count
            
            # Count legends from alliance histories
            alliance_histories = getattr(alliance_sys, 'alliance_histories', {})
            for history in alliance_histories.values():
                legends = getattr(history, 'legends', [])
                legends_count += len(legends)
            metrics.legends_recorded = legends_count
            
        except Exception as e:
            pass
            
        return metrics
    
    def _gather_neural_metrics(self) -> NeuralMetrics:
        """Gather neural training statistics"""
        metrics = NeuralMetrics()
        
        if not self.unified_system:
            return metrics
            
        try:
            organisms = self.unified_system.get_current_organisms()
            
            # Count organisms with neural networks
            brains = 0
            total_exp = 0
            epsilons = []
            
            for org in organisms.values():
                if hasattr(org, 'brain') and org.brain is not None:
                    brains += 1
                if hasattr(org, 'experience_buffer'):
                    total_exp += len(org.experience_buffer)
                if hasattr(org, 'epsilon'):
                    epsilons.append(org.epsilon)
            
            metrics.organisms_with_brains = brains
            metrics.experience_buffer_total = total_exp
            
            if epsilons:
                metrics.avg_epsilon = statistics.mean(epsilons)
            
            # Trainer stats
            reality_sim = getattr(self.unified_system, 'reality_sim', None)
            if reality_sim:
                trainer = getattr(reality_sim, 'neural_trainer', None)
                if trainer:
                    # FIX: Use training_step_count (the actual attribute name in NeuralTrainer)
                    metrics.total_training_steps = getattr(trainer, 'training_step_count', 0)
                    
                    # Get recent loss from autotune_metrics_buffer (where it's actually stored)
                    autotune_buffer = getattr(trainer, 'autotune_metrics_buffer', {})
                    loss_history = autotune_buffer.get('loss_history', [])
                    if loss_history:
                        recent_losses = loss_history[-10:]
                        metrics.avg_loss = statistics.mean(recent_losses)
            
            # Gym stats
            gym_manager = getattr(self.unified_system, 'gym_manager', None)
            if not gym_manager and reality_sim:
                gym_manager = getattr(reality_sim, 'gym_manager', None)
            
            if gym_manager:
                metrics.gym_episodes_total = getattr(gym_manager, 'total_episodes', 0)
                rewards = getattr(gym_manager, 'episode_rewards', [])
                if rewards:
                    metrics.gym_reward_mean = statistics.mean(rewards[-100:])
                    
        except Exception as e:
            pass
            
        return metrics
    
    def _gather_language_metrics(self) -> LanguageMetrics:
        """Gather language/vocabulary statistics"""
        metrics = LanguageMetrics()
        
        if not self.unified_system:
            return metrics
            
        try:
            # Primary source: context_memory.node_word_associations
            # This maps organism_id -> Set[words] they know
            reality_sim = getattr(self.unified_system, 'reality_sim', None)
            if reality_sim:
                network = reality_sim.components.get('network') if hasattr(reality_sim, 'components') else None
                if network:
                    context_mem = getattr(network, 'context_memory', None)
                    if context_mem:
                        # Get node word associations (organism -> words they know)
                        node_assocs = getattr(context_mem, 'node_word_associations', {})
                        all_words = set()
                        total_vocab = 0
                        
                        for org_id, words in node_assocs.items():
                            if isinstance(words, (set, list)):
                                all_words.update(words)
                                total_vocab += len(words)
                        
                        metrics.unique_words_across_pop = len(all_words)
                        metrics.total_vocabulary_words = total_vocab
                        
                        organisms = self.unified_system.get_current_organisms()
                        if organisms:
                            metrics.avg_vocab_per_organism = total_vocab / len(organisms)
                        
                        # Get vocabulary size from shared vocabulary
                        vocab = getattr(context_mem, 'vocabulary', None)
                        if vocab:
                            # Language anchors: word -> organisms using it  
                            language_anchors = getattr(context_mem, 'language_anchors', {})
                            metrics.word_adoptions_total = len(language_anchors)
                            
                            # Semantic associations count
                            metrics.semantic_associations = sum(len(v) for v in language_anchors.values()) if language_anchors else 0
            
            # Fallback: check organism atomic_language.atoms directly
            if metrics.total_vocabulary_words == 0:
                organisms = self.unified_system.get_current_organisms()
                all_words = set()
                total_vocab = 0
                total_associations = 0
                
                for org in organisms.values():
                    # Primary: check atomic_language.atoms (the actual vocabulary)
                    al = getattr(org, 'atomic_language', None)
                    if al and hasattr(al, 'atoms') and al.atoms:
                        words = set(al.atoms.keys())
                        all_words.update(words)
                        total_vocab += len(words)
                        # Count associations (depth metric)
                        for atom in al.atoms.values():
                            assoc = getattr(atom, 'associations', {})
                            if assoc:
                                total_associations += len(assoc)
                    else:
                        # Legacy fallback: org.vocabulary
                        vocab = getattr(org, 'vocabulary', None)
                        if vocab:
                            if isinstance(vocab, dict):
                                words = set(vocab.keys())
                            elif isinstance(vocab, (list, set)):
                                words = set(vocab)
                            else:
                                words = set()
                            all_words.update(words)
                            total_vocab += len(words)
                
                metrics.unique_words_across_pop = len(all_words)
                metrics.total_vocabulary_words = total_vocab
                metrics.semantic_associations = total_associations
                
                if organisms:
                    metrics.avg_vocab_per_organism = total_vocab / len(organisms)
            
            # ═══════════════════════════════════════════════════════════════════════════
            # 🎓 GATHER MASTERY LEVEL DATA - THE HEART OF VOCABULARY EVOLUTION
            # ═══════════════════════════════════════════════════════════════════════════
            organisms = self.unified_system.get_current_organisms()
            if organisms:
                mastery_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
                total_mastery = 0
                breadth_sum = 0.0
                depth_sum = 0.0
                exp_progress_sum = 0.0
                behavior_counts = {}
                valid_count = 0
                
                # Experience thresholds for each level
                exp_thresholds = {0: 25, 1: 100, 2: 500, 3: 2000, 4: float('inf')}
                
                for org_id, org in organisms.items():
                    # Get mastery level from atomic_language system
                    mastery_level = 0
                    breadth = 0.0
                    depth = 0.0
                    exp_count = 0
                    
                    if hasattr(org, 'atomic_language') and org.atomic_language:
                        al = org.atomic_language
                        mastery_level = getattr(al, '_mastery_level', 0)
                        
                        # Get progress metrics if available
                        if hasattr(al, '_calculate_breadth'):
                            try:
                                breadth = al._calculate_breadth()
                            except:
                                pass
                        if hasattr(al, '_calculate_depth'):
                            try:
                                depth = al._calculate_depth()
                            except:
                                pass
                        
                        exp_count = len(getattr(al, 'experience_log', [])) if hasattr(al, 'experience_log') else 0
                        
                        # Get dominant behavior for specialization tracking
                        if hasattr(al, '_get_dominant_actions'):
                            try:
                                dom_actions = al._get_dominant_actions(top_n=1)
                                if dom_actions:
                                    action_names = ['explorer', 'diplomat', 'warrior', 'conserver', 'nurturer', 'hermit']
                                    action_idx = dom_actions[0]
                                    if 0 <= action_idx < len(action_names):
                                        behavior = action_names[action_idx]
                                        behavior_counts[behavior] = behavior_counts.get(behavior, 0) + 1
                            except:
                                pass
                    
                    # Fallback: check _mastery_level attribute directly
                    elif hasattr(org, '_mastery_level'):
                        mastery_level = org._mastery_level
                    
                    # Count mastery levels
                    mastery_level = min(4, max(0, mastery_level))
                    mastery_counts[mastery_level] += 1
                    total_mastery += mastery_level
                    
                    # Accumulate progress metrics
                    breadth_sum += breadth
                    depth_sum += depth
                    
                    # Calculate experience progress toward next level
                    if mastery_level < 4:
                        threshold = exp_thresholds[mastery_level]
                        exp_progress_sum += min(1.0, exp_count / threshold)
                    else:
                        exp_progress_sum += 1.0  # Already at max
                    
                    valid_count += 1
                
                # Set mastery distribution
                metrics.mastery_level_0 = mastery_counts[0]
                metrics.mastery_level_1 = mastery_counts[1]
                metrics.mastery_level_2 = mastery_counts[2]
                metrics.mastery_level_3 = mastery_counts[3]
                metrics.mastery_level_4 = mastery_counts[4]
                
                # Find highest achieved
                for level in [4, 3, 2, 1, 0]:
                    if mastery_counts[level] > 0:
                        metrics.highest_mastery_achieved = level
                        break
                
                # Calculate averages
                if valid_count > 0:
                    metrics.avg_mastery_level = total_mastery / valid_count
                    metrics.avg_breadth_ratio = breadth_sum / valid_count
                    metrics.avg_depth_ratio = depth_sum / valid_count
                    metrics.avg_experience_progress = exp_progress_sum / valid_count
                
                # Set dominant behaviors
                metrics.dominant_behaviors = behavior_counts
                        
        except Exception as e:
            pass
            
        return metrics
    
    def _gather_language_game_bridge_metrics(self) -> LanguageGameBridgeMetrics:
        """
        Gather Language-Game Bridge correlation metrics.
        
        This is the feedback loop for meta-brain tuning:
        - How well is vocabulary influencing game decisions?
        - Are game outcomes correlating with vocabulary usage?
        - Should bias_strength or learning_rate be adjusted?
        """
        metrics = LanguageGameBridgeMetrics()
        
        if not self.unified_system:
            return metrics
        
        try:
            all_bridge_metrics = []
            
            # Get config values for reporting
            config = getattr(self.unified_system, 'config', {})
            if config:
                bridge_config = config.get('neural', {}).get('language_game_bridge', {})
                metrics.bias_strength = bridge_config.get('bias_strength', 0.3)
                metrics.learning_rate = bridge_config.get('learning_rate', 0.1)
            
            # ═══════════════════════════════════════════════════════════════════
            # PRIMARY SOURCE: UnifiedSystem direct attributes
            # Battle Arena and Highlander are stored on unified_system, NOT in
            # reality_sim.components - this was the gap!
            # ═══════════════════════════════════════════════════════════════════
            
            # Check battle_arena on unified_system directly
            battle_arena = getattr(self.unified_system, 'battle_arena', None)
            if battle_arena and hasattr(battle_arena, 'language_bridge') and battle_arena.language_bridge:
                bridge = battle_arena.language_bridge
                if hasattr(bridge, 'get_correlation_metrics'):
                    bridge_data = bridge.get_correlation_metrics()
                    if bridge_data.get('episodes_tracked', 0) > 0:
                        all_bridge_metrics.append(bridge_data)
            
            # Check highlander_protocol on unified_system directly
            highlander = getattr(self.unified_system, 'highlander_protocol', None)
            if highlander and hasattr(highlander, 'language_bridge') and highlander.language_bridge:
                bridge = highlander.language_bridge
                if hasattr(bridge, 'get_correlation_metrics'):
                    bridge_data = bridge.get_correlation_metrics()
                    if bridge_data.get('episodes_tracked', 0) > 0:
                        all_bridge_metrics.append(bridge_data)
            
            # ═══════════════════════════════════════════════════════════════════
            # SECONDARY SOURCE: reality_sim.components (fallback for legacy/other arenas)
            # ═══════════════════════════════════════════════════════════════════
            reality_sim = getattr(self.unified_system, 'reality_sim', None)
            if reality_sim and hasattr(reality_sim, 'components'):
                # Check arenas for language bridges
                for arena_name in ['drone_arena', 'sphere_arena', 'proton_arena']:
                    arena = reality_sim.components.get(arena_name)
                    if arena and hasattr(arena, 'language_bridge') and arena.language_bridge:
                        bridge = arena.language_bridge
                        if hasattr(bridge, 'get_correlation_metrics'):
                            bridge_data = bridge.get_correlation_metrics()
                            if bridge_data.get('episodes_tracked', 0) > 0:
                                all_bridge_metrics.append(bridge_data)
                
                # Check network level
                network = reality_sim.components.get('network')
                if network and hasattr(network, 'language_game_bridge') and network.language_game_bridge:
                    bridge = network.language_game_bridge
                    if hasattr(bridge, 'get_correlation_metrics'):
                        bridge_data = bridge.get_correlation_metrics()
                        if bridge_data.get('episodes_tracked', 0) > 0:
                            all_bridge_metrics.append(bridge_data)
            
            # Aggregate metrics
            if all_bridge_metrics:
                metrics.active = True
                metrics.source_count = len(all_bridge_metrics)
                n = len(all_bridge_metrics)
                
                metrics.episodes_tracked = sum(m.get('episodes_tracked', 0) for m in all_bridge_metrics)
                metrics.win_rate = sum(m.get('win_rate', 0.5) for m in all_bridge_metrics) / n
                metrics.avg_reward = sum(m.get('avg_reward', 0) for m in all_bridge_metrics) / n
                metrics.vocabulary_game_alignment = sum(m.get('vocabulary_game_alignment', 0) for m in all_bridge_metrics) / n
                metrics.language_decision_influence = sum(m.get('language_decision_influence', 0) for m in all_bridge_metrics) / n
                metrics.concept_diversity = sum(m.get('concept_diversity', 0) for m in all_bridge_metrics) / n
                metrics.unique_concepts_total = sum(m.get('unique_concepts_total', 0) for m in all_bridge_metrics)
                
        except Exception as e:
            pass
        
        return metrics
    
    def _gather_network_metrics(self) -> NetworkMetrics:
        """Gather symbiotic network statistics"""
        metrics = NetworkMetrics()
        
        if not self.unified_system:
            return metrics
            
        try:
            reality_sim = getattr(self.unified_system, 'reality_sim', None)
            if not reality_sim:
                return metrics
                
            network = reality_sim.components.get('network') if hasattr(reality_sim, 'components') else None
            if not network:
                return metrics
            
            # Get network stats
            if hasattr(network, 'get_network_stats'):
                stats = network.get_network_stats()
                metrics.connections = stats.get('num_connections', 0)
                metrics.network_density = stats.get('network_density', 0.0)
                
                communities = stats.get('communities', [])
                metrics.communities = len(communities) if communities else 0
            
            # Get ecosystem metrics
            eco_metrics = getattr(network, 'metrics', None)
            if eco_metrics:
                metrics.clustering_coefficient = getattr(eco_metrics, 'clustering_coefficient', 0.0)
                metrics.stability_index = getattr(eco_metrics, 'stability_index', 0.0)
                
        except Exception as e:
            pass
            
        return metrics
    
    def _gather_event_metrics(self) -> EventMetrics:
        """Gather causation event statistics"""
        metrics = EventMetrics()
        
        if not self.unified_system:
            return metrics
            
        try:
            explorer = getattr(self.unified_system, 'causation_explorer', None)
            if not explorer:
                return metrics
            
            events = getattr(explorer, 'events', {})
            metrics.total_events = len(events)
            
            # Count by type
            type_counts = defaultdict(int)
            now = time.time()
            events_last_min = 0
            events_last_hour = 0
            
            for event in events.values():
                event_type = getattr(event, 'event_type', 'unknown')
                type_counts[event_type] += 1
                
                timestamp = getattr(event, 'timestamp', 0)
                age = now - timestamp
                
                if age <= 60:
                    events_last_min += 1
                if age <= 3600:
                    events_last_hour += 1
            
            metrics.events_by_type = dict(type_counts)
            metrics.events_last_minute = events_last_min
            metrics.events_last_hour = events_last_hour
            
        except Exception as e:
            pass
            
        return metrics
    
    def _gather_resource_metrics(self) -> ResourceMetrics:
        """Gather system resource statistics"""
        metrics = ResourceMetrics()
        
        try:
            # Uptime
            metrics.uptime_seconds = time.time() - self.start_time
            
            # System CPU/Memory via psutil
            try:
                import psutil
                metrics.cpu_percent = psutil.cpu_percent(interval=None)
                mem = psutil.virtual_memory()
                metrics.memory_used_gb = mem.used / (1024 ** 3)
                metrics.memory_total_gb = mem.total / (1024 ** 3)
                metrics.memory_percent = mem.percent
                
                # Thread count for current process
                process = psutil.Process()
                metrics.thread_count = process.num_threads()
            except ImportError:
                pass
            
            if not self.unified_system:
                return metrics
            
            # Breath cycle - check multiple sources
            controller = getattr(self.unified_system, 'controller', None)
            if controller and hasattr(controller, 'breath_engine'):
                breath_state = controller.breath_engine.get_breath_state()
                metrics.breath_cycle = breath_state.get('cycle_count', 0)
                metrics.breath_depth = breath_state.get('depth', 0.0)
                metrics.breath_phase = breath_state.get('phase', 'unknown')
            else:
                # Fallback to reality_sim reference
                reality_sim = getattr(self.unified_system, 'reality_sim', None)
                if reality_sim:
                    breath_ref = getattr(reality_sim, 'breath_engine_ref', None)
                    if breath_ref and hasattr(breath_ref, 'get_breath_state'):
                        breath_state = breath_ref.get_breath_state()
                        metrics.breath_cycle = breath_state.get('cycle_count', 0)
                        metrics.breath_depth = breath_state.get('depth', 0.0)
                        metrics.breath_phase = breath_state.get('phase', 'unknown')
            
            # Ray status
            ray_manager = getattr(self.unified_system, 'ray_manager', None)
            if ray_manager:
                metrics.ray_enabled = ray_manager.is_initialized()
                resources = ray_manager.get_resources()
                metrics.ray_cpus = int(resources.get('num_cpus', 0))
                metrics.ray_gpus = int(resources.get('num_gpus', 0))
            
            # GPU memory
            try:
                import torch
                if torch.cuda.is_available():
                    metrics.gpu_memory_used_mb = torch.cuda.memory_allocated() / 1024 / 1024
                    metrics.gpu_memory_total_mb = torch.cuda.get_device_properties(0).total_memory / 1024 / 1024
            except:
                pass
                
        except Exception as e:
            pass
            
        return metrics
    
    def _get_top_organisms(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get top N organisms by fitness"""
        top = []
        
        if not self.unified_system:
            return top
            
        try:
            organisms = self.unified_system.get_current_organisms()
            
            # Sort by fitness
            sorted_orgs = sorted(
                organisms.items(),
                key=lambda x: getattr(x[1], 'fitness', 0),
                reverse=True
            )[:n]
            
            for org_id, org in sorted_orgs:
                # Get vocab size from atomic_language.atoms (the actual vocabulary)
                vocab_size = 0
                al = getattr(org, 'atomic_language', None)
                if al and hasattr(al, 'atoms') and al.atoms:
                    vocab_size = len(al.atoms)
                else:
                    # Legacy fallback
                    vocab_size = len(getattr(org, 'vocabulary', {}))
                
                top.append({
                    'id': org_id[:16] if len(org_id) > 16 else org_id,
                    'fitness': round(getattr(org, 'fitness', 0), 4),
                    'age': getattr(org, 'age', 0),
                    'generation': getattr(org, 'generation', 0),
                    'vocab_size': vocab_size,
                    'experience_count': len(getattr(org, 'experience_buffer', [])),
                })
                
        except Exception as e:
            pass
            
        return top
    
    def _get_recent_events(self, n: int = 20) -> List[Dict[str, Any]]:
        """Get N most recent events"""
        recent = []
        
        if not self.unified_system:
            return recent
            
        try:
            explorer = getattr(self.unified_system, 'causation_explorer', None)
            if not explorer:
                return recent
            
            events = list(getattr(explorer, 'events', {}).values())
            
            # Sort by timestamp descending
            events.sort(key=lambda e: getattr(e, 'timestamp', 0), reverse=True)
            
            for event in events[:n]:
                recent.append({
                    'type': getattr(event, 'event_type', 'unknown'),
                    'component': getattr(event, 'component', 'unknown'),
                    'timestamp': getattr(event, 'timestamp', 0),
                    'age_seconds': round(time.time() - getattr(event, 'timestamp', 0), 1)
                })
                
        except Exception as e:
            pass
            
        return recent
    
    def _check_warnings(self, report: SystemReport) -> List[str]:
        """Check for warning conditions"""
        warnings = []
        
        # Population warnings
        if report.population.active_organisms == 0:
            warnings.append("⚠️ NO ACTIVE ORGANISMS - population extinct!")
        elif report.population.active_organisms < 5:
            warnings.append(f"⚠️ Critical population: only {report.population.active_organisms} organisms")
        
        # Fitness warnings
        if report.population.fitness_max < 0.3:
            warnings.append("⚠️ Low fitness ceiling - organisms struggling")
        
        # Neural warnings
        if report.neural.avg_epsilon > 0.9:
            warnings.append("⚠️ High exploration (ε>0.9) - still in random phase")
        
        # Event warnings
        if report.events.events_last_minute == 0 and report.events.total_events > 0:
            warnings.append("⚠️ No events in last minute - system may be stalled")
        
        # Resource warnings  
        if report.resources.gpu_memory_total_mb > 0:
            usage_pct = report.resources.gpu_memory_used_mb / report.resources.gpu_memory_total_mb
            if usage_pct > 0.9:
                warnings.append(f"⚠️ GPU memory >90% used ({usage_pct*100:.1f}%)")
        
        return warnings
    
    def save(self, filepath: str = None) -> str:
        """
        Save report to JSON file.
        
        Args:
            filepath: Path to save to (default: data/reports/report_<timestamp>.json)
            
        Returns:
            Path to saved file
        """
        if self._last_report is None:
            self.generate()
        
        if filepath is None:
            reports_dir = Path('data/reports')
            reports_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = reports_dir / f'report_{timestamp}.json'
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(self._last_report.to_dict(), f, indent=2, default=str)
        
        return str(filepath)
    
    def print_summary(self, report: SystemReport = None):
        """Print human-readable summary to console"""
        if report is None:
            report = self._last_report or self.generate()
        
        print("\n" + "="*70)
        print("📊 SYSTEM REPORT - " + report.timestamp)
        print("="*70)
        
        # Population
        print(f"\n👥 POPULATION")
        print(f"   Active: {report.population.active_organisms} | Fallen: {report.population.fallen_organisms}")
        print(f"   Fitness: {report.population.fitness_mean:.3f} ± {report.population.fitness_std:.3f} "
              f"[{report.population.fitness_min:.3f} - {report.population.fitness_max:.3f}]")
        print(f"   Age: {report.population.age_mean:.1f} avg, {report.population.age_max} max")
        
        # Highlander
        print(f"\n⚔️ HIGHLANDER ({report.highlander.phase})")
        print(f"   Round: {report.highlander.round_number} | Battles: {report.highlander.total_battles}")
        print(f"   Eliminations: {report.highlander.eliminations_total} | Champions: {report.highlander.champions_crowned}")
        
        # Alliances
        print(f"\n🤝 ALLIANCES")
        print(f"   Active: {report.alliances.active_alliances} | Members: {report.alliances.total_members}")
        print(f"   Largest: {report.alliances.largest_alliance_size} | Wars: {report.alliances.wars_in_progress}")
        print(f"   Confederations: {report.alliances.confederations} | Warchiefs: {report.alliances.warchief_count}")
        print(f"   Territories: {report.alliances.territories_claimed} claimed / {report.alliances.territories_unclaimed} unclaimed")
        print(f"   Wars: {report.alliances.wars_won_total}W / {report.alliances.wars_lost_total}L | Legends: {report.alliances.legends_recorded}")
        
        # Neural
        print(f"\n🧠 NEURAL")
        print(f"   Brains: {report.neural.organisms_with_brains} | Steps: {report.neural.total_training_steps}")
        print(f"   Loss: {report.neural.avg_loss:.4f} | ε: {report.neural.avg_epsilon:.3f}")
        print(f"   Experience: {_format_count(report.neural.experience_buffer_total)} total")
        
        # Language
        print(f"\n📚 LANGUAGE")
        print(f"   Unique Words: {report.language.unique_words_across_pop}")
        print(f"   Avg Vocab: {report.language.avg_vocab_per_organism:.1f} words/organism")
        
        # Network
        print(f"\n🕸️ NETWORK")
        print(f"   Connections: {report.network.connections} | Density: {report.network.network_density:.3f}")
        print(f"   Communities: {report.network.communities} | Stability: {report.network.stability_index:.3f}")
        
        # Events
        print(f"\n📡 EVENTS")
        print(f"   Total: {report.events.total_events} | Last min: {report.events.events_last_minute} | Last hr: {report.events.events_last_hour}")
        top_types = sorted(report.events.events_by_type.items(), key=lambda x: x[1], reverse=True)[:5]
        if top_types:
            print(f"   Top: {', '.join(f'{t}:{c}' for t,c in top_types)}")
        
        # Resources
        print(f"\n💻 RESOURCES")
        print(f"   Breath: {report.resources.breath_cycle} | Uptime: {report.resources.uptime_seconds/60:.1f}m")
        print(f"   Ray: {'✅' if report.resources.ray_enabled else '❌'} | CPUs: {report.resources.ray_cpus} | GPUs: {report.resources.ray_gpus}")
        if report.resources.gpu_memory_total_mb > 0:
            print(f"   GPU Mem: {report.resources.gpu_memory_used_mb:.0f}/{report.resources.gpu_memory_total_mb:.0f} MB")
        
        # Top organisms
        if report.top_organisms:
            print(f"\n🏆 TOP ORGANISMS")
            for i, org in enumerate(report.top_organisms[:5], 1):
                print(f"   {i}. {org['id']} - fit:{org['fitness']:.3f} age:{org['age']} vocab:{org['vocab_size']}")
        
        # Warnings
        if report.warnings:
            print(f"\n⚠️ WARNINGS")
            for w in report.warnings:
                print(f"   {w}")
        
        print("\n" + "="*70)


# ═══════════════════════════════════════════════════════════════════════════════
# LIVE REPORTER - Auto-updates and saves periodically
# ═══════════════════════════════════════════════════════════════════════════════

class LiveReporter:
    """
    Continuously updates report file for external monitoring.
    
    Creates a single 'live_report.json' that updates every N seconds,
    perfect for external tools or dashboard polling.
    
    Also supports feeding report data to ConfigTuner for meta-brain analysis,
    completing the feedback loop: config.json → runtime → live_report → tuning → config.json
    """
    
    def __init__(self, unified_system=None, update_interval: float = 10.0):
        self.reporter = SystemReporter(unified_system)
        self.update_interval = update_interval
        self._running = False
        self._thread = None
        self.report_path = Path('data/live_report.json')
        self._report_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        
    def set_unified_system(self, unified_system):
        """Set the unified system reference"""
        self.reporter.set_unified_system(unified_system)
        
    def add_report_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Add a callback to receive report data on each update.
        
        Used to feed live_report data to ConfigTuner for meta-brain analysis.
        
        Args:
            callback: Function that accepts report_data dict
        """
        self._report_callbacks.append(callback)
        
    def remove_report_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Remove a previously added callback."""
        if callback in self._report_callbacks:
            self._report_callbacks.remove(callback)
        
    def start(self):
        """Start live reporting in background thread"""
        if self._running:
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()
        print(f"[REPORTER] 📊 Live reporting started → {self.report_path}")
        
    def stop(self):
        """Stop live reporting"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        print("[REPORTER] 📊 Live reporting stopped")
        
    def _update_loop(self):
        """Background update loop"""
        while self._running:
            try:
                report = self.reporter.generate()
                report_dict = report.to_dict()
                
                # Save to live report file
                self.report_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.report_path, 'w') as f:
                    json.dump(report_dict, f, indent=2, default=str)
                    
                # Feed to registered callbacks (e.g., ConfigTuner.ingest_live_report)
                for callback in self._report_callbacks:
                    try:
                        callback(report_dict)
                    except Exception:
                        pass  # Silent fail - don't break monitoring loop
                    
            except Exception as e:
                pass  # Silent fail - don't break monitoring
                
            time.sleep(self.update_interval)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='System Report Generator')
    parser.add_argument('--live', action='store_true', help='Start live reporting')
    parser.add_argument('--interval', type=float, default=10.0, help='Update interval for live mode')
    parser.add_argument('--output', type=str, help='Output file path')
    
    args = parser.parse_args()
    
    # For standalone use, try to connect to running system
    print("📊 System Reporter")
    print("   Note: For full metrics, use with UnifiedSystem instance")
    print("   Example: reporter = SystemReporter(unified_system)")
    
    reporter = SystemReporter()
    report = reporter.generate()
    reporter.print_summary()
    
    if args.output:
        path = reporter.save(args.output)
        print(f"\n💾 Saved to: {path}")
