"""
NeuralTrainer - Training System for Neural Organisms

Manages DQN training for neural organisms, synchronized with the Breath Engine.

Extended with:
- VP-aware language model training
- Triple-loss system: DQN (action) + Next-token prediction (language) + Concept understanding (RCUS)
- VP temperature scaling for stable training
- Curriculum learning based on VP thresholds
- Compositional concept grounding
- Ray parallel training for large populations (2-3x speedup)
- Mixed precision training (AMP) for 2-3x GPU speedup
"""

import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from contextlib import nullcontext
import time
import logging

logger = logging.getLogger(__name__)

# Ray distributed computing - optional, graceful fallback
RAY_DISTRIBUTED_AVAILABLE = False
try:
    from reality_simulator.distributed import get_ray_manager, RAY_AVAILABLE as _RAY_AVAIL
    RAY_DISTRIBUTED_AVAILABLE = _RAY_AVAIL
    logger.info(f"[NeuralTrainer] Ray distributed available: {RAY_DISTRIBUTED_AVAILABLE}")
except ImportError:
    pass

# Try importing PyTorch
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torch.nn.functional as F
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    torch = None
    nn = None
    optim = None
    F = None

# Use absolute imports to avoid relative import issues
try:
    from .experience import ExperienceBuffer
    from .neural_organism import NeuralOrganism
    from .utils import get_device, get_optimal_amp_dtype
except ImportError:
    # Fallback to absolute imports if relative imports fail
    try:
        from reality_simulator.neural.experience import ExperienceBuffer
        from reality_simulator.neural.neural_organism import NeuralOrganism
        from reality_simulator.neural.utils import get_device, get_optimal_amp_dtype
    except ImportError:
        # Last resort: try direct imports
        import sys
        import os
        neural_path = os.path.join(os.path.dirname(__file__))
        if neural_path not in sys.path:
            sys.path.insert(0, neural_path)
        from experience import ExperienceBuffer
        from neural_organism import NeuralOrganism
        from utils import get_device, get_optimal_amp_dtype

# Import concept system (optional - graceful degradation)
try:
    from .concept_system import ConceptSystem, compute_concept_loss, KEY_COMPOSITIONS, create_concept_system
    CONCEPT_SYSTEM_AVAILABLE = True
except ImportError:
    try:
        from reality_simulator.neural.concept_system import ConceptSystem, compute_concept_loss, KEY_COMPOSITIONS, create_concept_system
        CONCEPT_SYSTEM_AVAILABLE = True
    except ImportError:
        CONCEPT_SYSTEM_AVAILABLE = False
        ConceptSystem = None
        compute_concept_loss = None
        KEY_COMPOSITIONS = None
        create_concept_system = None


class NeuralTrainer:
    """
    Trainer for neural organisms using DQN (Deep Q-Network).
    
    Collects experiences from organisms and performs batched training
    synchronized with the Breath Engine.
    
    Extended with:
    - Language model training (next-token prediction)
    - VP-aware temperature scaling
    - Curriculum learning for sequence lengths
    """
    
    def __init__(self, config: Dict[str, Any], device=None):
        """
        Initialize neural trainer.
        
        Args:
            config: Neural configuration dictionary
            device: PyTorch device (auto-detected if None)
        """
        if not PYTORCH_AVAILABLE:
            raise ImportError("PyTorch is required for NeuralTrainer")
        
        self.config = config
        self.device = device or get_device(config.get('device', 'cpu'))
        
        # Validate architecture config on startup (warns if mismatched)
        try:
            from .utils import validate_architecture_config
            validate_architecture_config({'neural': config}, strict=False)
        except ImportError:
            pass  # Skip validation if import fails
        
        training_config = config.get('training', {})
        self.batch_size = training_config.get('batch_size', 32)
        self._effective_batch_size = self.batch_size  # Will be reduced during early training
        self.learning_rate = training_config.get('learning_rate', 0.005)  # Default matches config.json
        self.gamma = training_config.get('gamma', 0.995)  # Default matches config.json
        self.update_frequency = training_config.get('update_frequency', 1)
        
        rewards_config = config.get('rewards', {})
        self.reward_weights = {
            'fitness_improvement': rewards_config.get('fitness_improvement', 4.5),  # Default matches config.json
            'survival': rewards_config.get('survival', 2.0),  # Default matches config.json
            'connection_success': rewards_config.get('connection_success', 2.5),  # Default matches config.json
            'connection_failure': rewards_config.get('connection_failure', -0.2),
            'resource_gain': rewards_config.get('resource_gain', 1.0),  # Default matches config.json
            'resource_loss': rewards_config.get('resource_loss', -0.3),  # Default matches config.json
        }
        
        # Language model configuration
        language_config = config.get('language_model', {})
        training_config = language_config.get('training', {})
        self.language_model_enabled = language_config.get('enabled', False)
        # AUDIT FIX: Read from training config, ensure alpha+beta+gamma=1.0
        self.rl_loss_weight = training_config.get('alpha', language_config.get('rl_loss_weight', 0.5))  # alpha - default matches config.json
        self.language_loss_weight = training_config.get('beta', language_config.get('language_loss_weight', 0.4))  # beta - default matches config.json
        self.vp_gate_threshold = language_config.get('generation', {}).get('vp_gate_threshold', 0.5)  # default matches config.json
        self.vp_temperature_scaling = training_config.get('vp_temperature_scale', language_config.get('vp_temperature_scaling', True))
        
        # Language entropy bonus - prevents mode collapse to single tokens ("shorten shorten" bug)
        # Similar to action head entropy bonus, encourages exploration in language generation
        self.language_entropy_bonus = training_config.get('entropy_bonus', 0.01)
        self.language_label_smoothing = training_config.get('label_smoothing', 0.1)
        
        # Curriculum learning configuration
        self.curriculum_learning = language_config.get('curriculum_learning', True)
        self.current_sequence_length = language_config.get('start_sequence_length', 8)
        self.curriculum_thresholds = language_config.get('curriculum_thresholds', {
            '8_to_16': {'vp_threshold': 0.5, 'stability_steps': 20},
            '16_to_32': {'vp_threshold': 0.4, 'stability_steps': 30},
            '32_to_128': {'vp_threshold': 0.3, 'stability_steps': 50}
        })
        
        # VP history for curriculum learning decisions
        self.vp_history: List[float] = []
        self.vp_stable_steps = 0
        
        # Training statistics
        self.training_step_count = 0
        self.training_occurred_this_step = False  # Track if training happened in current step
        self.total_loss = 0.0
        self.total_language_loss = 0.0
        self.total_rl_loss = 0.0  # Granular: RL/DQN loss only
        self.total_concept_loss = 0.0  # Granular: Concept loss only
        self.last_training_time = 0.0
        
        # EMA (Exponential Moving Average) for smoother loss tracking
        self.ema_alpha = 0.1  # Smoothing factor (lower = smoother)
        self.ema_loss = None  # EMA of combined loss
        self.ema_rl_loss = None  # EMA of RL loss
        self.ema_language_loss = None  # EMA of language loss
        self.ema_concept_loss = None  # EMA of concept loss
        
        # Track organism fitness history for reward calculation
        self.organism_fitness_history: Dict[str, float] = {}
        
        # Optimization: Reuse optimizers instead of recreating each step
        optimization_config = config.get('optimization', {})
        self.reuse_optimizers = optimization_config.get('reuse_optimizers', True)
        self.optimizers: Dict[int, optim.Optimizer] = {}  # organism_id -> optimizer
        self.schedulers: Dict[int, Any] = {}  # organism_id -> lr_scheduler
        
        # Track training time for performance monitoring
        self.training_times = []  # List of recent training step durations
        
        # ═══════════════════════════════════════════════════════════════════════════
        # LR SCHEDULER & EARLY STOPPING (Phase 3 Training Infrastructure)
        # Improves training stability and prevents overfitting
        # ═══════════════════════════════════════════════════════════════════════════
        lr_scheduler_config = training_config.get('lr_scheduler', {})
        self.lr_scheduler_enabled = lr_scheduler_config.get('enabled', True)
        self.lr_scheduler_type = lr_scheduler_config.get('type', 'cosine')  # Default matches config.json
        self.lr_step_size = lr_scheduler_config.get('step_size', 100)  # Steps between LR decay
        self.lr_gamma = lr_scheduler_config.get('gamma', 0.95)  # LR decay factor
        self.lr_min = lr_scheduler_config.get('min_lr', 0.0001)  # Default matches config.json
        
        early_stopping_config = training_config.get('early_stopping', {})
        self.early_stopping_enabled = early_stopping_config.get('enabled', True)
        self.early_stopping_patience = early_stopping_config.get('patience', 10)  # Default matches config.json
        self.early_stopping_min_delta = early_stopping_config.get('min_delta', 1e-4)  # Min loss change
        self.early_stopping_counter = 0
        self.best_loss = float('inf')
        self.early_stopped = False
        
        # Log optimization status
        import logging
        logger = logging.getLogger(__name__)
        if self.reuse_optimizers:
            logger.info(f"[NEURAL] Optimizations enabled: optimizer reuse")
        if self.lr_scheduler_enabled:
            logger.info(f"[NEURAL] LR scheduler enabled: {self.lr_scheduler_type} (gamma={self.lr_gamma})")
        if self.early_stopping_enabled:
            logger.info(f"[NEURAL] Early stopping enabled: patience={self.early_stopping_patience}")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # EVENT EMITTER & EXTERNAL INTEGRATIONS
        # These are set by main.py or unified_entry.py after initialization
        # ═══════════════════════════════════════════════════════════════════════════
        # Optional event emitter for causation graph visualization
        self.event_emitter = None  # Set by main.py or unified_entry.py
        
        # Integration 2: Neural-ML Symbiosis - ML analysis for language rewards
        self.ml_analysis = None  # Set by main.py when ML analysis is available
        self.context_memory = None  # Set by main.py for vocabulary access
        self.language_reward_scaling = training_config.get('language_reward_scaling', 0.35)  # Default matches config.json
        
        # Track language rewards for ConfigTuner analysis
        self.language_reward_total = 0.0  # Cumulative language rewards per training step
        self.language_reward_count = 0  # Number of language rewards given
        self._last_step_language_reward_total = 0.0  # Store last step's total for metrics
        
        # ═══════════════════════════════════════════════════════════════════════════
        # MISSION 2: AutoTune Integration Buffer
        # Track neural training metrics for AtomicConfigSystem feedback loop
        # ═══════════════════════════════════════════════════════════════════════════
        self.autotune_metrics_buffer = {
            'avg_loss': 0.0,
            'min_loss': float('inf'),
            'max_loss': 0.0,
            'loss_variance': 0.0,
            'loss_history': [],  # Last N losses for trend analysis
            'organisms_trained_total': 0,
            'training_steps_completed': 0,
            'improvement_rate': 0.0,
            'language_loss_total': 0.0,
            'rl_loss_total': 0.0,
            'concept_loss_total': 0.0,  # RCUS concept learning loss
            'avg_training_time_ms': 0.0
        }
        self.autotune_loss_window = 50  # Window size for moving average
        self.atomic_config_system = None  # Set by main.py when available
        
        # ═══════════════════════════════════════════════════════════════════════════
        # RCUS: Concept System Integration
        # Compositional understanding through primitive axioms
        # ═══════════════════════════════════════════════════════════════════════════
        concept_config = config.get('concept_system', {})
        self.concept_system_enabled = concept_config.get('enabled', False) and CONCEPT_SYSTEM_AVAILABLE
        self.concept_loss_weight = concept_config.get('concept_loss_weight', 0.1)  # gamma in triple-loss
        self.concept_system = None  # Shared concept system for all organisms
        self.concept_bridge = None  # GAP FIX C3: Language bridge
        
        if self.concept_system_enabled and CONCEPT_SYSTEM_AVAILABLE:
            try:
                self.concept_system = ConceptSystem(
                    state_dim=config.get('brain', {}).get('input_dim', 27),
                    embed_dim=concept_config.get('embed_dim', 64),
                    device=str(self.device)
                )
                logger.info(f"[NEURAL] Concept system enabled with {len(KEY_COMPOSITIONS)} key compositions")
            except Exception as e:
                logger.warning(f"[NEURAL] Failed to initialize concept system: {e}")
                self.concept_system_enabled = False
        
        # Track concept learning metrics
        self.total_concept_loss = 0.0
        self.concept_compositions_evaluated = 0
        
        # ═══════════════════════════════════════════════════════════════════════════
        # RAY DISTRIBUTED TRAINING
        # Parallel training for large populations (2-3x speedup)
        # ═══════════════════════════════════════════════════════════════════════════
        ray_config = config.get('ray', {})
        self.ray_enabled = ray_config.get('enabled', True) and RAY_DISTRIBUTED_AVAILABLE
        self.ray_training_threshold = ray_config.get('training_threshold', 8)  # Min organisms for parallel
        self.ray_manager = None
        
        if self.ray_enabled:
            try:
                self.ray_manager = get_ray_manager()
                logger.info(f"[NEURAL] Ray parallel training enabled (threshold: {self.ray_training_threshold})")
            except Exception as e:
                logger.warning(f"[NEURAL] Ray initialization failed, using sequential training: {e}")
                self.ray_enabled = False
        
        # ═══════════════════════════════════════════════════════════════════════════
        # MIXED PRECISION TRAINING (AMP)
        # Uses FP16/BF16 for faster computation on supported GPUs (2-3x speedup)
        # Tensor Cores on RTX/Ampere/Ada GPUs get significant benefits
        # Auto-detect: BF16 for Ampere+ (A100, L4, L40, RTX 30xx+), FP16 for older (T4, V100)
        # ═══════════════════════════════════════════════════════════════════════════
        optimization_config = config.get('optimization', {})
        amp_config = optimization_config.get('amp', {})
        self.amp_enabled = amp_config.get('enabled', True) and torch.cuda.is_available()
        self.amp_dtype = get_optimal_amp_dtype(amp_config.get('dtype', 'auto'))
        
        # GradScaler for stable FP16 training (prevents gradient underflow)
        # Note: BF16 doesn't need scaling but GradScaler is still safe to use
        if self.amp_enabled:
            self.grad_scaler = torch.amp.GradScaler('cuda')
            logger.info(f"[NEURAL] Mixed precision (AMP) enabled: {self.amp_dtype}")
        else:
            self.grad_scaler = None
        
        # ═══════════════════════════════════════════════════════════════════════════
        # CHECKPOINT SYSTEM CONFIGURATION
        # Auto-save training state periodically to prevent data loss
        # ═══════════════════════════════════════════════════════════════════════════
        checkpoint_config = config.get('checkpointing', {})
        self.checkpoint_enabled = checkpoint_config.get('enabled', False)
        self.checkpoint_interval_generations = checkpoint_config.get('auto_save_interval_generations', 100)
        self.checkpoint_interval_minutes = checkpoint_config.get('auto_save_interval_minutes', 30)
        self.checkpoint_max_count = checkpoint_config.get('max_checkpoints', 10)
        self.checkpoint_dir = checkpoint_config.get('checkpoint_dir', 'data/neural_checkpoints')
        self.checkpoint_include_buffer = checkpoint_config.get('include_experience_buffer', True)
        self.checkpoint_compression = checkpoint_config.get('compression', True)
        self.checkpoint_auto_resume = checkpoint_config.get('auto_resume', True)
        
        # Checkpoint tracking
        self._last_checkpoint_generation = 0
        self._last_checkpoint_time = time.time()
        self._checkpoint_count = 0
        
        if self.checkpoint_enabled:
            logger.info(f"[NEURAL] Checkpointing enabled: every {self.checkpoint_interval_generations} gens or {self.checkpoint_interval_minutes} mins")
    
    def _get_or_create_scheduler(self, organism_id: int, optimizer: optim.Optimizer) -> Any:
        """
        Get or create LR scheduler for an organism.

        Part of Phase 3 Training Infrastructure improvements.
        """
        if not self.lr_scheduler_enabled:
            return None

        if organism_id not in self.schedulers:
            if self.lr_scheduler_type == 'step':
                self.schedulers[organism_id] = optim.lr_scheduler.StepLR(
                    optimizer,
                    step_size=self.lr_step_size,
                    gamma=self.lr_gamma
                )
            elif self.lr_scheduler_type == 'exponential':
                self.schedulers[organism_id] = optim.lr_scheduler.ExponentialLR(
                    optimizer,
                    gamma=self.lr_gamma
                )
            elif self.lr_scheduler_type == 'plateau':
                self.schedulers[organism_id] = optim.lr_scheduler.ReduceLROnPlateau(
                    optimizer,
                    mode='min',
                    factor=self.lr_gamma,
                    patience=10,
                    min_lr=self.lr_min
                )
            elif self.lr_scheduler_type == 'cosine':
                # CosineAnnealingWarmRestarts - good for boom/bust dynamics
                # T_0 = steps before first restart, T_mult = multiplier for subsequent periods
                warmup_steps = lr_scheduler_config.get('warmup_steps', 100) if hasattr(self, '_lr_scheduler_config') else 100
                self.schedulers[organism_id] = optim.lr_scheduler.CosineAnnealingWarmRestarts(
                    optimizer,
                    T_0=max(self.lr_step_size, 50),  # Use step_size as period
                    T_mult=2,  # Double period after each restart
                    eta_min=self.lr_min
                )
            else:
                # FIXED: Validate lr_scheduler_type and warn about invalid values
                logger.warning(f"[NEURAL] Invalid lr_scheduler_type '{self.lr_scheduler_type}', valid types: 'step', 'exponential', 'plateau', 'cosine'. Using StepLR as fallback.")
                self.schedulers[organism_id] = optim.lr_scheduler.StepLR(
                    optimizer,
                    step_size=self.lr_step_size,
                    gamma=self.lr_gamma
                )

        return self.schedulers.get(organism_id)
    
    def _check_early_stopping(self, avg_loss: float) -> bool:
        """
        Check if training should stop early due to loss plateau.

        Part of Phase 3 Training Infrastructure improvements.

        Returns:
            True if training should stop, False otherwise
        """
        if not self.early_stopping_enabled:
            return False

        # FIXED: Add safeguards for invalid loss values and min_delta
        if not isinstance(avg_loss, (int, float)) or not np.isfinite(avg_loss):
            logger.warning(f"[NEURAL] Invalid avg_loss value: {avg_loss}, skipping early stopping check")
            return False

        if self.early_stopping_min_delta < 0:
            logger.warning(f"[NEURAL] Invalid early_stopping_min_delta: {self.early_stopping_min_delta}, must be >= 0. Using 1e-4 as fallback.")
            self.early_stopping_min_delta = 1e-4

        # FIXED: Ensure best_loss is initialized properly and handle infinity
        if not np.isfinite(self.best_loss):
            self.best_loss = float('inf')

        if avg_loss < self.best_loss - self.early_stopping_min_delta:
            self.best_loss = avg_loss
            self.early_stopping_counter = 0
        else:
            self.early_stopping_counter += 1
            if self.early_stopping_counter >= self.early_stopping_patience:
                logger.info(f"[NEURAL] Early stopping triggered after {self.early_stopping_patience} steps without improvement")
                self.early_stopped = True
                
                # Emit early stopping event for causation graph
                if self.event_emitter:
                    try:
                        from causation_explorer import Event
                        event = Event(
                            timestamp=time.time(),
                            component='neural',
                            event_type='early_stopping_triggered',
                            data={
                                'patience': self.early_stopping_patience,
                                'best_loss': float(self.best_loss),
                                'final_loss': float(avg_loss),
                                'training_step': self.training_step_count,
                                'min_delta': float(self.early_stopping_min_delta)
                            }
                        )
                        self.event_emitter(event)
                    except ImportError:
                        pass
                
                return True

        return False
    
    def reset_early_stopping(self):
        """
        Reset early stopping state to continue training.
        
        Call this when you want to resume training after early stopping
        or after significant changes to the model/data.
        """
        self.early_stopping_counter = 0
        self.best_loss = float('inf')
        self.early_stopped = False
        logger.info("[NEURAL] Early stopping state reset")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ML-AWARE TRAINING: Use scikit-learn analysis to adjust learning
    # Groks identified that ML data wasn't being used to affect neural training
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_ml_adjusted_learning_rate(self, organism_id: str, base_lr: float) -> float:
        """
        Adjust learning rate based on ML analysis of organism status.
        
        Uses:
        - Anomaly status: Anomalies get higher LR (they're exploring novel strategies)
        - Cluster membership: Organisms in small/unstable clusters get higher LR
        - Concept stability: Stable phenotypes get lower LR (preserve what works)
        
        Args:
            organism_id: ID of organism being trained
            base_lr: Base learning rate
            
        Returns:
            Adjusted learning rate
        """
        if self.ml_analysis is None or not self.ml_analysis.get('enabled'):
            return base_lr
        
        lr_multiplier = 1.0
        
        # 1. ANOMALY BOOST: Anomalies are trying novel strategies, train faster
        anomaly_organisms = self.ml_analysis.get('anomaly_organisms', [])
        if organism_id in anomaly_organisms:
            lr_multiplier *= 1.5  # 50% faster learning for anomalies
        
        # 2. SMALL CLUSTER BOOST: Small/unstable clusters need to adapt faster
        cluster_labels = self.ml_analysis.get('cluster_labels', [])
        organism_ids = self.ml_analysis.get('organism_ids', [])  # FIX: organism_ids is a list, not a dict

        # Validate alignment between cluster_labels and organism_ids
        if not organism_ids or len(organism_ids) != len(cluster_labels):
            return base_lr  # Can't apply ML adjustments without proper mapping

        if cluster_labels and organism_id in organism_ids:
            idx = organism_ids.index(organism_id)
            if idx < len(cluster_labels):
                cluster_id = cluster_labels[idx]
                if cluster_id == -1:
                    # Outlier/noise - needs to find its place
                    lr_multiplier *= 1.3
                else:
                    cluster_sizes = self.ml_analysis.get('clustering', {}).get('cluster_sizes', {})
                    cluster_size = cluster_sizes.get(cluster_id, 0)
                    if cluster_size <= 2:
                        # Very small cluster - unstable, train faster
                        lr_multiplier *= 1.2
        
        # 3. CONCEPT STABILITY DAMPENING: Stable phenotypes should learn slower
        concept_tags = self.ml_analysis.get('concept_tags', {})
        if cluster_labels and concept_tags and organism_id in organism_ids:
            idx = organism_ids.index(organism_id)
            if idx < len(cluster_labels):
                cluster_id = cluster_labels[idx]
                if cluster_id in concept_tags:
                    # Part of a named/stable concept - don't disrupt what works
                    lr_multiplier *= 0.8
        
        # Clamp multiplier to reasonable range
        lr_multiplier = np.clip(lr_multiplier, 0.5, 2.0)
        
        return base_lr * lr_multiplier
    
    def sync_from_atomic_config(self) -> Dict[str, Any]:
        """
        INTEGRATION FIX: Sync tunable parameters from AtomicConfigSystem.
        
        This bridges the gap where atoms are tuned but components don't see the changes.
        Call this periodically (e.g., every N training steps) to pull updated values.
        
        Returns:
            Dict of parameters that were updated
        """
        if self.atomic_config_system is None:
            return {}
        
        updated = {}
        
        # Learning rate
        new_lr = self.atomic_config_system.get('learning_rate')
        if new_lr is not None and new_lr != self.learning_rate:
            old_lr = self.learning_rate
            self.learning_rate = new_lr
            updated['learning_rate'] = {'old': old_lr, 'new': new_lr}
            # Invalidate cached optimizers so they get recreated with new LR
            self.optimizers.clear()
            self.schedulers.clear()
        
        # Batch size
        new_batch = self.atomic_config_system.get('batch_size')
        if new_batch is not None and new_batch != self.batch_size:
            old_batch = self.batch_size
            self.batch_size = int(new_batch)
            updated['batch_size'] = {'old': old_batch, 'new': self.batch_size}
        
        # Dropout rate (affects organism brains indirectly)
        new_dropout = self.atomic_config_system.get('dropout_rate')
        if new_dropout is not None:
            updated['dropout_rate'] = {'new': new_dropout, 'note': 'affects new brains'}
        
        # Loss weights
        new_alpha = self.atomic_config_system.get('rl_loss_weight')
        if new_alpha is not None and new_alpha != self.rl_loss_weight:
            old_alpha = self.rl_loss_weight
            self.rl_loss_weight = new_alpha
            updated['rl_loss_weight'] = {'old': old_alpha, 'new': new_alpha}
        
        new_beta = self.atomic_config_system.get('language_loss_weight')
        if new_beta is not None and new_beta != self.language_loss_weight:
            old_beta = self.language_loss_weight
            self.language_loss_weight = new_beta
            updated['language_loss_weight'] = {'old': old_beta, 'new': new_beta}
        
        # Log if anything changed
        if updated and self.training_step_count % 100 == 0:
            logger.info(f"[NEURAL] Synced {len(updated)} params from AtomicConfigSystem: {list(updated.keys())}")
        
        return updated
    
    def activate_language_bridge(self, vocabulary: Any) -> int:
        """
        GAP FIX C3: Activate the concept-language bridge.
        
        Call this after vocabulary is initialized to seed axiom words.
        
        Args:
            vocabulary: Vocabulary object with add_word method
            
        Returns:
            Number of words seeded
        """
        if not self.concept_system_enabled or not self.concept_system:
            return 0
        
        try:
            from .concept_system import ConceptLanguageBridge
            self.concept_bridge = ConceptLanguageBridge(self.concept_system, vocabulary)
            seeded = self.concept_bridge.seed_vocabulary_with_axioms(vocabulary)
            logger.info(f"[NEURAL] Language bridge activated, seeded {seeded} axiom words")
            return seeded
        except Exception as e:
            logger.warning(f"[NEURAL] Failed to activate language bridge: {e}")
            return 0
    
    def _calculate_language_reward(self, organism: NeuralOrganism) -> float:
        """
        Calculate language reward based on ML feature importance.
        
        Integration 2: Neural-ML Symbiosis - rewards organisms for using words
        that predict fitness (identified by ML feature selection).
        
        Args:
            organism: Neural organism with token sequence
            
        Returns:
            Language reward (0.0 if no ML analysis or no important words used)
        """
        if not self.ml_analysis:
            return 0.0
        
        # Extract feature importance from ML analysis
        semantic_analysis = self.ml_analysis.get('semantic_analysis', {})
        feature_importance = semantic_analysis.get('feature_importance', {})
        
        if not feature_importance:
            return 0.0
        
        top_predictive_words = feature_importance.get('top_predictive_words', [])
        if not top_predictive_words:
            return 0.0
        
        # Get organism's generated tokens
        if not hasattr(organism, 'get_token_sequence'):
            return 0.0
        
        token_sequence = organism.get_token_sequence()
        if not token_sequence or len(token_sequence) == 0:
            return 0.0
        
        # Decode tokens to words using vocabulary from context_memory
        if not self.context_memory or not hasattr(self.context_memory, 'vocabulary'):
            return 0.0
        
        vocab = self.context_memory.vocabulary
        if vocab is None:
            return 0.0
        
        # Decode tokens to words (skip special tokens)
        try:
            words = vocab.decode(token_sequence, skip_special=True)
        except Exception:
            # Fallback: try to decode manually
            words = []
            for token_id in token_sequence:
                try:
                    word = vocab.get_word(token_id)
                    # Skip special tokens
                    if word and not (word.startswith('<') and word.endswith('>')):
                        words.append(word)
                except Exception:
                    continue
        
        if not words:
            return 0.0
        
        # Calculate reward: sum importance scores for matching words
        reward = 0.0
        important_word_dict = {item['word']: item['importance_score'] for item in top_predictive_words}
        
        for word in words:
            if word in important_word_dict:
                # Reward proportional to importance, scaled by config
                reward += important_word_dict[word] * self.language_reward_scaling
        
        return reward
    
    def calculate_reward(self, 
                        organism: NeuralOrganism,
                        prev_fitness: float,
                        current_fitness: float,
                        action: int,
                        connection_success: Optional[bool] = None,
                        resource_delta: float = 0.0,
                        vp_value: float = 0.0) -> float:
        """
        Calculate reward for an organism based on various factors.
        
        Integration 2: Now includes language reward from ML feature importance.
        GAP 2 FIX: Now includes VP-aware reward shaping.
        
        Args:
            organism: Neural organism
            prev_fitness: Previous fitness value
            current_fitness: Current fitness value
            action: Action taken
            connection_success: Whether connection attempt succeeded (None = no attempt)
            resource_delta: Change in resources
            vp_value: Current violation pressure (0.0-1.0) for VP-aware reward shaping
            
        Returns:
            Calculated reward (base + language + VP adjustment)
        """
        reward = 0.0
        
        # 1. Fitness improvement
        fitness_delta = current_fitness - prev_fitness
        reward += fitness_delta * self.reward_weights['fitness_improvement']
        
        # 2. Survival (small positive reward for staying alive)
        reward += self.reward_weights['survival']
        
        # 3. Connection success/failure
        if connection_success is not None:
            if connection_success:
                reward += self.reward_weights['connection_success']
            else:
                reward += self.reward_weights['connection_failure']
        
        # 4. Resource gain/loss
        if resource_delta > 0:
            reward += resource_delta * self.reward_weights['resource_gain']
        elif resource_delta < 0:
            reward += abs(resource_delta) * self.reward_weights['resource_loss']
        
        # 5. VP-aware reward shaping (GAP 2 FIX)
        # Penalize high VP as a curriculum signal - organisms should learn to
        # maintain healthy VP levels. High VP indicates system strain.
        if vp_value > 0.7:
            # Strong penalty for dangerously high VP
            vp_penalty = -0.3 * (vp_value - 0.7) / 0.3  # -0.3 at VP=1.0
            reward += vp_penalty
        elif vp_value < 0.2:
            # Small penalty for too-low VP (indicates underexploration)
            vp_penalty = -0.1 * (0.2 - vp_value) / 0.2  # -0.1 at VP=0.0
            reward += vp_penalty
        elif 0.3 <= vp_value <= 0.6:
            # Small bonus for healthy VP range (exploration-exploitation balance)
            vp_bonus = 0.05
            reward += vp_bonus
        
        # 6. Self-perception reward shaping (Features 26-28)
        # Organisms can now FEEL their oscillation and coherence - make this matter
        # Config values from self_perception section (with hardcoded fallbacks)
        sp_config = self.config.get('self_perception', {})
        sp_enabled = sp_config.get('enabled', False)  # Default disabled - requires input_dim >= 28
        
        # Self-perception requires input_dim >= 28 (features 25-27)
        input_dim = self.config.get('neural', {}).get('brain', {}).get('input_dim', 25)
        if sp_enabled and input_dim < 28:
            sp_enabled = False  # Disable if dimensions don't support it
        
        if sp_enabled:
            try:
                state = organism.get_state_features() if hasattr(organism, 'get_state_features') else None
                if state is not None and len(state) >= 28:
                    # Feature 26: oscillation_entropy - penalize high chaos
                    osc_threshold = sp_config.get('oscillation_entropy_threshold', 0.7)
                    osc_penalty = sp_config.get('oscillation_chaos_penalty', -0.1)
                    
                    oscillation_entropy = state[25]
                    if oscillation_entropy > osc_threshold:
                        entropy_penalty = osc_penalty * (oscillation_entropy - osc_threshold) / (1.0 - osc_threshold)
                        reward += entropy_penalty
                    
                    # Feature 27: coherence_frequency - penalize feeling "trapped"
                    coh_threshold = sp_config.get('coherence_frequency_threshold', 0.6)
                    coh_penalty = sp_config.get('coherence_trap_penalty', -0.15)
                    
                    coherence_frequency = state[26]
                    if coherence_frequency > coh_threshold:
                        # High coherence = stuck in loop = bad
                        coherence_penalty = coh_penalty * (coherence_frequency - coh_threshold) / (1.0 - coh_threshold)
                        reward += coherence_penalty
                    elif coherence_frequency < 0.2:
                        # Very low coherence = drifting freely = slight bonus
                        freedom_bonus = 0.03
                        reward += freedom_bonus
                    
                    # Feature 28: attractor_proximity - reward being near known stable configs
                    if len(state) >= 28:
                        prox_near = sp_config.get('proximity_near_threshold', 0.3)
                        prox_near_bonus = sp_config.get('proximity_near_bonus', 0.05)
                        prox_med = sp_config.get('proximity_medium_threshold', 0.6)
                        prox_med_bonus = sp_config.get('proximity_medium_bonus', 0.02)
                        
                        attractor_proximity = state[27]
                        # Low proximity = close to attractor = good (stability)
                        if prox_near < attractor_proximity < prox_med:
                            # Near but not at attractor - exploring basin
                            reward += prox_near_bonus
                        elif attractor_proximity < prox_near:
                            # Very close to attractor - stable but might be stuck
                            reward += prox_med_bonus
            except Exception:
                pass  # Don't break reward calculation if self-perception fails
        
        # Integration 2: Add language reward (if ML analysis available)
        language_reward = self._calculate_language_reward(organism)
        reward += language_reward
        
        # Track language rewards for ConfigTuner
        if language_reward > 0.0:
            self.language_reward_total += language_reward
            self.language_reward_count += 1
        
        # Emit event for language reward (Integration 2: Neural-ML Symbiosis)
        if language_reward > 0.0 and self.event_emitter:
            try:
                from causation_explorer import Event
                event = Event(
                    timestamp=time.time(),
                    component='neural',
                    event_type='neural_language_reward',
                    data={
                        'organism_id': str(id(organism)),
                        'language_reward': float(language_reward),
                        'total_reward': float(reward),
                        'reward_scaling': self.language_reward_scaling,
                        'has_ml_analysis': self.ml_analysis is not None
                    }
                )
                self.event_emitter(event)
            except Exception as e:
                logger.debug(f"Event emission failed (non-critical): {e}")
        
        return reward
    
    def collect_experiences(self,
                           organisms: Dict[str, NeuralOrganism],
                           network_state: Dict[str, Any],
                           breath_state: Optional[Dict[str, Any]] = None):
        """
        Collect experiences from all neural organisms.
        
        Args:
            organisms: Dictionary of organisms (species_id -> NeuralOrganism)
            network_state: Current network state
            breath_state: Breath engine state
        """
        experiences_collected = 0
        skipped_no_brain = 0
        skipped_no_record = 0
        skipped_no_prev_state = 0
        
        for org_id, organism in organisms.items():
            # Use duck typing instead of isinstance() to avoid import issues
            # Check if organism has neural capabilities
            if not (hasattr(organism, 'brain') and organism.brain is not None):
                skipped_no_brain += 1
                continue

            if not hasattr(organism, 'record_experience'):
                skipped_no_record += 1
                continue  # Not a neural organism
            
            # Check if organism has made a decision yet
            if not hasattr(organism, 'prev_state') or organism.prev_state is None:
                skipped_no_prev_state += 1
                continue

            # Get previous fitness
            prev_fitness = self.organism_fitness_history.get(org_id, organism.fitness)
            current_fitness = organism.fitness
            
            # Calculate reward (GAP 2: VP-aware reward shaping)
            vp_value = network_state.get('vp_value', 0.0) if network_state else 0.0
            reward = self.calculate_reward(
                organism=organism,
                prev_fitness=prev_fitness,
                current_fitness=current_fitness,
                action=organism.prev_action if hasattr(organism, 'prev_action') else 0,
                connection_success=None,  # Would need to track this
                resource_delta=0.0,  # Would need to track this
                vp_value=vp_value  # GAP 2 FIX: Pass VP for curriculum learning
            )
            
            # Get next state
            next_state = organism.get_state_features(
                local_env=None,
                network_state=network_state,
                breath_state=breath_state
            )
            
            # Record experience
            organism.record_experience(
                reward=reward,
                next_state=next_state,
                done=False  # Organisms don't "die" in the same way
            )
            experiences_collected += 1
            
            # 🎰 TOKEN TUMBLER: Generate tokens from experience
            # This ensures language training has material from real gameplay
            if hasattr(organism, 'tumble_action_tokens'):
                action = organism.prev_action if hasattr(organism, 'prev_action') else 0
                # Determine context from reward
                if reward > 0.1:
                    ctx = 'success'
                elif reward < -0.1:
                    ctx = 'failure'
                else:
                    ctx = 'step'
                organism.tumble_action_tokens(action=action, reward=reward, context=ctx)

            # Update fitness history
            self.organism_fitness_history[org_id] = current_fitness

        # Log training progress periodically (every 50 steps to avoid spam)
        # ENHANCED: Also log diagnostic info about why experiences might not be collected
        if self.training_step_count % 50 == 0:
            total_orgs = len(organisms)
            if experiences_collected > 0:
                print(f"[NEURAL] Collected {experiences_collected} experiences from {total_orgs} organisms")
            elif total_orgs > 0:
                print(f"[NEURAL] WARNING: No experiences collected from {total_orgs} organisms!")
                print(f"  - Skipped (no brain): {skipped_no_brain}")
                print(f"  - Skipped (no record_experience): {skipped_no_record}")
                print(f"  - Skipped (no prev_state): {skipped_no_prev_state}")
        
        # DEBUG: Log first 10 steps at debug level
        if self.training_step_count <= 10:
            logger.debug(f"[NEURAL DEBUG] Step {self.training_step_count}: orgs={len(organisms)}, collected={experiences_collected}, no_brain={skipped_no_brain}, no_record={skipped_no_record}, no_prev={skipped_no_prev_state}")
        
        # Update autotune buffer_size metric
        total_buffer_size = sum(
            len(org.experience_buffer) for org in organisms.values()
            if hasattr(org, 'experience_buffer') and org.experience_buffer is not None
        )
        self.autotune_metrics_buffer['buffer_size'] = total_buffer_size
        
        # Track whether training occurred this step (for diagnostics)
        self.training_occurred_this_step = False
    
    def _train_organisms_parallel(
        self,
        trainable_organisms: List,
        network_state: Dict[str, Any]
    ) -> Tuple[float, int]:
        """
        Train multiple organisms in parallel using Ray.
        
        This serializes brain weights, sends to Ray workers for parallel
        gradient computation, then applies updated weights back.
        
        Args:
            trainable_organisms: List of organisms with sufficient experiences
            network_state: Current network state (for VP value)
            
        Returns:
            Tuple of (total_loss, num_trained)
        """
        # Mark CUDA graph step boundary for torch.compile()
        if hasattr(torch.compiler, 'cudagraph_mark_step_begin'):
            torch.compiler.cudagraph_mark_step_begin()
            
        from reality_simulator.distributed import train_organisms_batch
        
        # Prepare training tasks
        training_tasks = []
        organism_mapping = []  # Track which organism each task corresponds to
        
        for organism in trainable_organisms:
            try:
                # ?? VETERAN-AWARE BATCH SIZING: Scale batch based on experience buffer size
                # Veterans with large buffers can handle larger batches for better learning
                base_batch_size = getattr(self, '_effective_batch_size', self.batch_size)
                buffer_len = len(organism.experience_buffer) if organism.experience_buffer else 0
                
                # Dynamic scaling: veterans get proportionally larger batches (up to 2x)
                # This prevents underutilization of their rich experience
                if buffer_len > 500:
                    # Elite veteran: can use up to 2x batch size
                    veteran_scale = min(2.0, 1.0 + (buffer_len - 500) / 1000)
                elif buffer_len > 200:
                    # Veteran: can use up to 1.5x batch size
                    veteran_scale = min(1.5, 1.0 + (buffer_len - 200) / 600)
                else:
                    veteran_scale = 1.0
                
                # Apply scaling but cap at buffer size
                batch_size_to_use = min(
                    int(base_batch_size * veteran_scale),
                    buffer_len
                )
                batch_size_to_use = max(1, batch_size_to_use)  # Ensure at least 1
                
                states, actions, rewards, next_states, dones = organism.experience_buffer.sample_batch(
                    batch_size_to_use
                )
                
                # Serialize brain weights
                brain_weights = {k: v.cpu().clone() for k, v in organism.brain.state_dict().items()}
                
                # Create experience batch dict
                experience_batch = {
                    'states': states.tolist() if hasattr(states, 'tolist') else list(states),
                    'actions': actions.tolist() if hasattr(actions, 'tolist') else list(actions),
                    'rewards': rewards.tolist() if hasattr(rewards, 'tolist') else list(rewards),
                    'next_states': next_states.tolist() if hasattr(next_states, 'tolist') else list(next_states),
                    'dones': dones.tolist() if hasattr(dones, 'tolist') else list(dones),
                }
                
                # Language config if applicable
                language_config = None
                if (self.language_model_enabled and 
                    hasattr(organism.brain, 'use_language_head') and 
                    organism.brain.use_language_head and
                    hasattr(organism, 'token_sequence') and 
                    len(organism.token_sequence) >= 2):
                    # ?? VETERAN SEQUENCE SCALING for distributed training
                    if buffer_len > 250:
                        effective_seq_len = min(self.current_sequence_length * 2, len(organism.token_sequence))
                    elif buffer_len > 100:
                        effective_seq_len = min(int(self.current_sequence_length * 1.5), len(organism.token_sequence))
                    else:
                        effective_seq_len = self.current_sequence_length
                    
                    token_seq = list(organism.token_sequence)[-effective_seq_len:]
                    if len(token_seq) >= 2:
                        language_config = {
                            'enabled': True,
                            'token_sequence': token_seq,
                        }
                
                training_tasks.append({
                    'brain_weights': brain_weights,
                    'experience_batch': experience_batch,
                    'language_config': language_config,
                })
                organism_mapping.append(organism)
                
            except Exception as e:
                logger.debug(f"[NEURAL] Failed to prepare training task: {e}")
                continue
        
        if not training_tasks:
            return 0.0, 0
        
        # Build shared training config
        training_config = {
            'learning_rate': self.learning_rate,
            'gamma': self.gamma,
            'rl_loss_weight': self.rl_loss_weight,
            'language_loss_weight': self.language_loss_weight,
            'device': str(self.device),
            'input_dim': self.config.get('brain', {}).get('input_dim', 27),
            'hidden_dim': self.config.get('brain', {}).get('hidden_dim', 64),
            'output_dim': self.config.get('brain', {}).get('output_dim', 6),  # Default matches config.json
            'vocab_size': self.config.get('language_model', {}).get('vocab_size', 20000),  # Default matches config.json
            'use_language_head': self.language_model_enabled,
        }
        
        # Execute parallel training
        results = train_organisms_batch(
            training_tasks,
            training_config,
            use_ray=self.ray_enabled
        )
        
        # Apply results back to organisms
        total_loss = 0.0
        num_trained = 0
        
        for i, result in enumerate(results):
            if result.get('success'):
                organism = organism_mapping[i]
                
                # Load updated weights back into brain
                try:
                    updated_weights = result['updated_weights']
                    # Use strict=False to handle architecture changes gracefully
                    organism.brain.load_state_dict(updated_weights, strict=False)
                    
                    total_loss += result.get('loss', 0.0)
                    self.total_language_loss += result.get('language_loss', 0.0)
                    num_trained += 1
                    
                except Exception as e:
                    logger.debug(f"[NEURAL] Failed to apply training result: {e}")
            else:
                logger.debug(f"[NEURAL] Training task failed: {result.get('error', 'unknown')}")
        
        return total_loss, num_trained
    
    def train_step(self,
                   organisms: Dict[str, NeuralOrganism],
                   network_state: Dict[str, Any],
                   breath_state: Optional[Dict[str, Any]] = None) -> Optional[float]:
        """
        Perform one training step (synchronized with breath cycle).
        
        Args:
            organisms: Dictionary of organisms
            network_state: Current network state
            breath_state: Breath engine state
            
        Returns:
            Average loss, or None if no training occurred
            
        Note:
            - training_step_count increments EVERY call (tracks trainer invocations)
            - training_loss is only returned when actual training occurs (batch_size met)
            - None means no training this step (waiting for experiences or update_frequency)
        """
        if not PYTORCH_AVAILABLE:
            return None
        
        # Collect experiences first
        self.collect_experiences(organisms, network_state, breath_state)
        
        # Increment step count first
        self.training_step_count += 1
        
        # Check if we should train this step - USE BREATH STATE
        # Train during "exhale" phase (breath_depth descending, phase > π)
        should_train = False
        if breath_state and isinstance(breath_state, dict):
            breath_depth = breath_state.get('depth', 0.0)
            breath_phase = breath_state.get('phase', 0.0)
            # Train during exhale phase (π to 2π) when breath is deep enough
            # Exhale = consolidation phase, ideal for learning
            # LOWERED threshold from 0.3 to 0.15 to allow more training opportunities
            training_threshold = 0.15
            if breath_phase > 3.14159 and breath_depth > training_threshold:
                should_train = True
            # FALLBACK: Also train periodically even if breath conditions aren't met
            # This ensures training happens at least every 20 steps
            elif self.training_step_count > 0 and self.training_step_count % 20 == 0:
                should_train = True
        else:
            # Fallback to step counter if no breath state (backward compatibility)
            should_train = (self.training_step_count % self.update_frequency) == 0

        if not should_train:
            return None
        
        # ═══════════════════════════════════════════════════════════════════════════
        # INTEGRATION FIX: Sync from AtomicConfigSystem every 50 steps
        # This closes the gap where atoms are tuned but trainer doesn't see changes
        # ═══════════════════════════════════════════════════════════════════════════
        if self.training_step_count % 50 == 0:
            self.sync_from_atomic_config()
        
        # ═══════════════════════════════════════════════════════════════════════════
        # EARLY TRAINING: Use smaller batch size early on to show loss faster
        # This helps users see that training IS happening
        # ═══════════════════════════════════════════════════════════════════════════
        if self.training_step_count < 100:
            # During warm-up, use smaller batches (min 4) to start showing loss sooner
            self._effective_batch_size = max(4, self.batch_size // 4)
        elif self.training_step_count < 500:
            # Gradually increase batch size
            self._effective_batch_size = max(8, self.batch_size // 2)
        else:
            self._effective_batch_size = self.batch_size
        
        # Check if we have enough experiences to train
        # Find organisms with sufficient experience
        trainable_organisms = []
        for organism in organisms.values():
            # Use duck typing instead of isinstance()
            if (hasattr(organism, 'brain') and organism.brain is not None and
                hasattr(organism, 'experience_buffer') and organism.experience_buffer is not None and
                len(organism.experience_buffer) >= self._effective_batch_size):
                trainable_organisms.append(organism)
        
        if not trainable_organisms:
            return None
        
        # Track training time
        training_start_time = time.time()
        
        # ═══════════════════════════════════════════════════════════════════════════
        # LANGUAGE-ONLY TRAINING: Train organisms with tokens but not enough RL experiences
        # This fixes the bug where language training was blocked by RL batch requirements
        # ═══════════════════════════════════════════════════════════════════════════
        language_only_organisms = [
            org for org in organisms.values()  # FIX: iterate over values(), not keys
            if (hasattr(org, 'token_sequence') and len(org.token_sequence) >= 2 and
                hasattr(org, 'brain') and hasattr(org.brain, 'use_language_head') and 
                org.brain.use_language_head and
                (not hasattr(org, 'experience_buffer') or 
                 org.experience_buffer is None or 
                 len(org.experience_buffer) < self._effective_batch_size))
        ]
        
        for organism in language_only_organisms:
            try:
                # ?? VETERAN SEQUENCE SCALING: Allow veterans to use longer sequences
                # This utilizes their deeper language history for better learning
                buffer_len = len(organism.experience_buffer) if hasattr(organism, 'experience_buffer') and organism.experience_buffer else 0
                
                # Veterans can use longer sequence lengths (up to 2x curriculum length)
                if buffer_len > 250:
                    # Elite: up to 2x sequence length
                    effective_seq_len = min(self.current_sequence_length * 2, len(organism.token_sequence))
                elif buffer_len > 100:
                    # Veteran: up to 1.5x sequence length
                    effective_seq_len = min(int(self.current_sequence_length * 1.5), len(organism.token_sequence))
                else:
                    effective_seq_len = self.current_sequence_length
                
                token_seq = list(organism.token_sequence)[-effective_seq_len:]
                if len(token_seq) >= 2:
                    input_tokens = torch.LongTensor([token_seq[:-1]]).to(self.device)
                    target_tokens = torch.LongTensor([token_seq[1:]]).to(self.device)
                    
                    # FIX: Use actual organism state instead of zeros
                    # The language head maps state → vocabulary, so it needs real state
                    if hasattr(organism, 'get_state_features'):
                        # get_state_features() is the correct method on NeuralOrganism
                        state = organism.get_state_features(
                            local_env=None,
                            network_state=network_state,
                            breath_state=breath_state
                        )
                        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                    else:
                        # Skip non-neural organisms that don't have state features
                        continue
                    
                    organism.brain.train()
                    _, language_logits = organism.brain(state_tensor, return_language_logits=True)
                    
                    if language_logits is not None:
                        if language_logits.dim() == 2:
                            language_logits = language_logits.unsqueeze(1).expand(-1, len(token_seq)-1, -1)
                        
                        vp_value = network_state.get('vp_value', 0.0) if network_state else 0.0
                        # 🧬 Pass organism's curiosity trait to scale entropy bonus
                        curiosity = getattr(organism.phenotype, 'curiosity', 0.5) if hasattr(organism, 'phenotype') else 0.5
                        language_loss = self.calculate_language_loss(language_logits, target_tokens, vp_value, curiosity=curiosity)
                        
                        # Backprop for language-only training
                        optimizer = optim.Adam(organism.brain.parameters(), lr=self.learning_rate * 0.5)
                        optimizer.zero_grad()
                        
                        # ⚡ AMP: Use gradient scaling for mixed precision
                        if self.amp_enabled and self.grad_scaler is not None:
                            self.grad_scaler.scale(language_loss).backward()
                            self.grad_scaler.step(optimizer)
                            self.grad_scaler.update()
                        else:
                            language_loss.backward()
                            optimizer.step()
                        
                        self.total_language_loss += language_loss.item()
            except Exception as e:
                pass  # Skip on error, don't break training loop
        
        # ═══════════════════════════════════════════════════════════════════════════
        # ORGANISM TRAINING: Sequential or Parallel based on Ray config and count
        # ═══════════════════════════════════════════════════════════════════════════
        
        # Mark CUDA graph step boundary to avoid "pending backwards" warning
        # This is needed when using torch.compile() with CUDA graphs
        if hasattr(torch.compiler, 'cudagraph_mark_step_begin'):
            torch.compiler.cudagraph_mark_step_begin()
        
        # Decide whether to use parallel training
        use_parallel = (
            self.ray_enabled and 
            self.ray_manager is not None and
            len(trainable_organisms) >= self.ray_training_threshold
        )
        
        if use_parallel:
            # Use Ray parallel training
            total_loss, num_trained = self._train_organisms_parallel(
                trainable_organisms, network_state
            )
            if num_trained > 0 and self.training_step_count % 50 == 0:
                logger.debug(f"[NEURAL] Ray parallel trained {num_trained} organisms")
        else:
            # Sequential training (original code)
            total_loss = 0.0
            num_trained = 0
            
            for organism in trainable_organisms:
                # Sample batch (use effective batch size for early training)
                batch_size_to_use = getattr(self, '_effective_batch_size', self.batch_size)
                states, actions, rewards, next_states, dones = organism.experience_buffer.sample_batch(
                    batch_size_to_use
                )
                
                # SAFETY: Filter out experiences with invalid actions (0-5 only)
                # This handles legacy data from checkpoints or gym environments with >6 actions
                valid_mask = (actions >= 0) & (actions <= 5)
                if not np.all(valid_mask):
                    invalid_count = np.sum(~valid_mask)
                    logger.warning(f"[NEURAL] Filtered {invalid_count} experiences with invalid actions (>5)")
                    states = states[valid_mask]
                    actions = actions[valid_mask]
                    rewards = rewards[valid_mask]
                    next_states = next_states[valid_mask]
                    dones = dones[valid_mask]
                    if len(actions) < 4:  # Need minimum batch to train
                        continue
                
                # Convert to tensors
                states_tensor = torch.FloatTensor(states).to(self.device)
                actions_tensor = torch.LongTensor(actions).to(self.device)
                rewards_tensor = torch.FloatTensor(rewards).to(self.device)
                next_states_tensor = torch.FloatTensor(next_states).to(self.device)
                dones_tensor = torch.BoolTensor(dones).to(self.device)
                
                # ⚡ AMP: Use autocast for forward passes (2-3x faster on Tensor Core GPUs)
                amp_context = torch.amp.autocast('cuda', dtype=self.amp_dtype) if self.amp_enabled else nullcontext()
                
                with amp_context:
                    # Get current Q values
                    organism.brain.train()  # Set to training mode
                    q_values = organism.brain(states_tensor)
                    q_value = q_values.gather(1, actions_tensor.unsqueeze(1)).squeeze(1)
                    
                    # Get next Q values (no gradient)
                    organism.brain.eval()  # Set to evaluation mode
                    with torch.no_grad():
                        next_q_values = organism.brain(next_states_tensor)
                        next_q_value = next_q_values.max(1)[0]
                
                # Calculate target Q values
                target_q_value = rewards_tensor + (self.gamma * next_q_value * ~dones_tensor)
                
                # Calculate RL loss (Q-learning)
                rl_loss = F.mse_loss(q_value, target_q_value)
                self.total_rl_loss += rl_loss.item()  # Track granular RL loss
                
                # Calculate language loss if enabled and brain has language head
                language_loss = None
                if (self.language_model_enabled and 
                    hasattr(organism.brain, 'use_language_head') and 
                    organism.brain.use_language_head and
                    hasattr(organism, 'token_sequence') and 
                    len(organism.token_sequence) >= 2):
                    
                    # ?? VETERAN SEQUENCE SCALING for single-organism training
                    org_buffer_len = len(organism.experience_buffer) if hasattr(organism, 'experience_buffer') and organism.experience_buffer else 0
                    if org_buffer_len > 250:
                        effective_seq_len = min(self.current_sequence_length * 2, len(organism.token_sequence))
                    elif org_buffer_len > 100:
                        effective_seq_len = min(int(self.current_sequence_length * 1.5), len(organism.token_sequence))
                    else:
                        effective_seq_len = self.current_sequence_length
                    
                    # Get token sequence for next-token prediction
                    token_seq = list(organism.token_sequence)[-effective_seq_len:]
                    if len(token_seq) >= 2:
                        # Prepare input (all but last) and target (all but first)
                        input_tokens = torch.LongTensor([token_seq[:-1]]).to(self.device)
                        target_tokens = torch.LongTensor([token_seq[1:]]).to(self.device)
                        
                        # Get VP value for temperature scaling
                        vp_value = network_state.get('vp_value', 0.0) if network_state else 0.0
                        
                        # Get language logits from brain
                        try:
                            _, language_logits = organism.brain(
                                states_tensor[:1],  # Single sample for language
                                return_language_logits=True
                            )
                            if language_logits is not None:
                                # Expand logits to match sequence length if needed
                                if language_logits.dim() == 2:
                                    language_logits = language_logits.unsqueeze(1).expand(-1, len(token_seq)-1, -1)
                                # 🧬 Pass organism's curiosity trait to scale entropy bonus
                                curiosity = getattr(organism.phenotype, 'curiosity', 0.5) if hasattr(organism, 'phenotype') else 0.5
                                language_loss = self.calculate_language_loss(
                                    language_logits, target_tokens, vp_value, curiosity=curiosity
                                )
                                self.total_language_loss += language_loss.item()
                        except Exception as e:
                            logger.debug(f"Language loss calculation skipped: {e}")
                
                # Calculate concept loss if enabled (RCUS - compositional understanding)
                concept_loss = None
                if (self.concept_system_enabled and 
                    self.concept_system is not None and
                    hasattr(organism.brain, 'use_concept_head') and 
                    organism.brain.use_concept_head):
                    try:
                        # Compute concept loss: concepts should predict rewards
                        concept_loss = compute_concept_loss(
                            self.concept_system,
                            states_tensor,
                            rewards_tensor,
                            KEY_COMPOSITIONS
                        )
                        self.total_concept_loss += concept_loss.item()
                        self.concept_compositions_evaluated += len(KEY_COMPOSITIONS) * len(states_tensor)
                    except Exception as e:
                        logger.debug(f"Concept loss calculation skipped: {e}")
                
                # Combine losses with weighting (triple-loss system)
                # loss = alpha * rl_loss + beta * language_loss + gamma * concept_loss
                loss = self.rl_loss_weight * rl_loss
                if language_loss is not None:
                    loss = loss + self.language_loss_weight * language_loss
                if concept_loss is not None:
                    loss = loss + self.concept_loss_weight * concept_loss
                
                # Backpropagation
                organism.brain.train()
                
                # Optimization: Reuse optimizer if enabled
                # ML-AWARE TRAINING: Adjust learning rate based on ML analysis
                org_id_str = getattr(organism, 'species_id', str(id(organism)))
                adjusted_lr = self.get_ml_adjusted_learning_rate(org_id_str, self.learning_rate)
                
                if self.reuse_optimizers:
                    organism_id = id(organism.brain)
                    if organism_id not in self.optimizers:
                        self.optimizers[organism_id] = optim.Adam(
                            organism.brain.parameters(), 
                            lr=adjusted_lr  # Use ML-adjusted LR
                        )
                    optimizer = self.optimizers[organism_id]
                    # Update LR if it changed due to ML analysis
                    for param_group in optimizer.param_groups:
                        param_group['lr'] = adjusted_lr
                    
                    # 📈 LR SCHEDULER: Get or create scheduler for this organism
                    scheduler = self._get_or_create_scheduler(organism_id, optimizer)
                else:
                    optimizer = optim.Adam(organism.brain.parameters(), lr=adjusted_lr)
                    scheduler = None
                
                optimizer.zero_grad()
                
                # ⚡ AMP: Use gradient scaling for mixed precision training
                if self.amp_enabled and self.grad_scaler is not None:
                    self.grad_scaler.scale(loss).backward()
                    self.grad_scaler.step(optimizer)
                    self.grad_scaler.update()
                else:
                    loss.backward()
                    optimizer.step()
                
                # 📈 LR SCHEDULER: Step the scheduler after optimizer
                if scheduler is not None:
                    old_lr = optimizer.param_groups[0]['lr']
                    if self.lr_scheduler_type == 'plateau':
                        scheduler.step(loss.item())
                    else:
                        scheduler.step()
                    # Enforce minimum learning rate
                    for param_group in optimizer.param_groups:
                        if param_group['lr'] < self.lr_min:
                            param_group['lr'] = self.lr_min
                    new_lr = optimizer.param_groups[0]['lr']
                    
                    # Emit LR adjusted event if learning rate changed
                    if abs(new_lr - old_lr) > 1e-10 and self.event_emitter:
                        try:
                            from causation_explorer import Event
                            event = Event(
                                timestamp=time.time(),
                                component='neural',
                                event_type='lr_adjusted',
                                data={
                                    'organism_id': organism_id,
                                    'old_lr': float(old_lr),
                                    'new_lr': float(new_lr),
                                    'scheduler_type': self.lr_scheduler_type,
                                    'loss': float(loss.item()),
                                    'training_step': self.training_step_count
                                }
                            )
                            self.event_emitter(event)
                        except ImportError:
                            pass
                
                total_loss += loss.item()
                num_trained += 1
        
        # Track training duration
        training_duration = time.time() - training_start_time
        self.training_times.append(training_duration)
        if len(self.training_times) > 100:  # Keep last 100 training times
            self.training_times = self.training_times[-100:]
        
        self.last_training_time = time.time()
        
        if num_trained > 0:
            self.training_occurred_this_step = True
            avg_loss = total_loss / num_trained
            self.total_loss += avg_loss
            
            # Calculate per-component averages for this step
            avg_rl = self.total_rl_loss / max(1, self.training_step_count + 1)
            avg_lang = self.total_language_loss / max(1, self.training_step_count + 1) if self.language_model_enabled else None
            avg_concept = self.total_concept_loss / max(1, self.training_step_count + 1) if self.concept_system_enabled else None
            
            # Update EMA (Exponential Moving Average) for smoother tracking
            alpha = self.ema_alpha
            if self.ema_loss is None:
                self.ema_loss = avg_loss
                self.ema_rl_loss = avg_rl
                self.ema_language_loss = avg_lang
                self.ema_concept_loss = avg_concept
            else:
                self.ema_loss = alpha * avg_loss + (1 - alpha) * self.ema_loss
                self.ema_rl_loss = alpha * avg_rl + (1 - alpha) * self.ema_rl_loss
                if avg_lang is not None:
                    self.ema_language_loss = alpha * avg_lang + (1 - alpha) * (self.ema_language_loss or avg_lang)
                if avg_concept is not None:
                    self.ema_concept_loss = alpha * avg_concept + (1 - alpha) * (self.ema_concept_loss or avg_concept)
            
            # Emit neural training event for visualization
            if self.event_emitter:
                training_stats = self.get_training_stats()
                avg_training_time = np.mean(self.training_times) if self.training_times else 0.0
                event_data = {
                    'training_step': self.training_step_count,
                    'loss': float(avg_loss),
                    'num_organisms_trained': num_trained,
                    'total_organisms': len(organisms),
                    'avg_loss_history': training_stats.get('average_loss', 0.0),
                    'training_time_ms': training_duration * 1000,  # Convert to milliseconds
                    'avg_training_time_ms': avg_training_time * 1000,
                    'optimizations_enabled': {
                        'reuse_optimizers': self.reuse_optimizers,
                        'compiled_brains': num_trained > 0  # Assume compiled if training works
                    },
                    'breath_cycle': breath_state.get('cycle_count', 0) if breath_state else None,
                    'breath_depth': breath_state.get('depth', 0.0) if breath_state else None
                }
                
                try:
                    from causation_explorer import Event
                    event = Event(
                        timestamp=time.time(),
                        component='neural',
                        event_type='neural_training',
                        data=event_data
                    )
                    self.event_emitter(event)
                except ImportError:
                    pass  # CausationExplorer not available
            
            # Store language reward total for this step (before resetting for next step)
            self._last_step_language_reward_total = self.language_reward_total
            
            # Reset language reward tracking for next step (ConfigTuner tracks per-step totals)
            self.language_reward_total = 0.0
            self.language_reward_count = 0
            
            # ═══════════════════════════════════════════════════════════════════════════
            # MISSION 2: Update AutoTune metrics buffer and emit to AtomicConfigSystem
            # ═══════════════════════════════════════════════════════════════════════════
            self._update_autotune_metrics(avg_loss, num_trained, training_duration)
            
            # 🛑 EARLY STOPPING: Check if training should stop due to loss plateau
            if self._check_early_stopping(avg_loss):
                logger.info(f"[NEURAL] Early stopping at step {self.training_step_count}, best loss: {self.best_loss:.6f}")
            
            # Curriculum learning: adjust sequence length based on VP stability
            if self.curriculum_learning and self.language_model_enabled:
                vp_value = network_state.get('vp_value', 0.0) if network_state else 0.0
                self.update_curriculum(vp_value)
            
            return avg_loss
        
        return None
    
    def get_neural_ml_symbiosis_metrics(self) -> Dict[str, Any]:
        """Get Neural-ML Symbiosis metrics for ConfigTuner"""
        return {
            'language_reward_total': self._last_step_language_reward_total,  # Use stored value from last step
            'language_reward_count': self.language_reward_count,
            'curriculum_sequence_length': self.current_sequence_length,
            'language_reward_scaling': self.language_reward_scaling
        }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # MISSION 2: AutoTune Integration Methods
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _update_autotune_metrics(self, avg_loss: float, num_trained: int, training_duration: float):
        """
        Update AutoTune metrics buffer and emit to AtomicConfigSystem.
        
        This enables closed-loop optimization where neural training outcomes
        inform config parameter adjustments.
        
        Args:
            avg_loss: Average loss from this training step
            num_trained: Number of organisms trained
            training_duration: Time taken for training step
        """
        # Update loss history (rolling window)
        self.autotune_metrics_buffer['loss_history'].append(avg_loss)
        if len(self.autotune_metrics_buffer['loss_history']) > self.autotune_loss_window:
            self.autotune_metrics_buffer['loss_history'] = \
                self.autotune_metrics_buffer['loss_history'][-self.autotune_loss_window:]
        
        # Calculate statistics from history
        loss_history = self.autotune_metrics_buffer['loss_history']
        if len(loss_history) >= 2:
            self.autotune_metrics_buffer['avg_loss'] = np.mean(loss_history)
            self.autotune_metrics_buffer['min_loss'] = min(loss_history)
            self.autotune_metrics_buffer['max_loss'] = max(loss_history)
            self.autotune_metrics_buffer['loss_variance'] = float(np.var(loss_history))
            
            # Calculate improvement rate (negative slope = improving)
            recent = loss_history[-10:] if len(loss_history) >= 10 else loss_history
            if len(recent) >= 2:
                x = np.arange(len(recent))
                slope = np.polyfit(x, recent, 1)[0]
                self.autotune_metrics_buffer['improvement_rate'] = -slope  # Positive = improving
        
        # Update counters
        self.autotune_metrics_buffer['organisms_trained_total'] += num_trained
        self.autotune_metrics_buffer['training_steps_completed'] += 1
        self.autotune_metrics_buffer['language_loss_total'] = self.total_language_loss
        self.autotune_metrics_buffer['rl_loss_total'] = self.total_loss
        self.autotune_metrics_buffer['avg_training_time_ms'] = np.mean(self.training_times) * 1000 if self.training_times else 0.0
        
        # Emit to AtomicConfigSystem if available
        if self.atomic_config_system is not None:
            try:
                neural_metrics = {
                    'neural_loss': self.autotune_metrics_buffer['avg_loss'],
                    'neural_improving': self.autotune_metrics_buffer['improvement_rate'] > 0,
                    'loss_variance': self.autotune_metrics_buffer['loss_variance'],
                    'training_step': self.training_step_count,
                    'organisms_trained': num_trained
                }
                # Call tune() method to inform atomic configs
                actions = self.atomic_config_system.tune(neural_metrics, self.training_step_count)
                if actions:
                    logger.debug(f"[NEURAL→AUTOTUNE] Applied {len(actions)} config adjustments based on training metrics")
                
                # GAP 4 FIX: Use propose_action + apply_action with meta-cognitive confirmation
                # Every 10 training steps, attempt a more deliberate tuning proposal
                if self.training_step_count % 10 == 0:
                    proposed = self.atomic_config_system.propose_action(neural_metrics)
                    if proposed is not None:
                        # Record baseline before applying
                        baseline = {
                            'avg_loss': self.autotune_metrics_buffer['avg_loss'],
                            'improvement_rate': self.autotune_metrics_buffer['improvement_rate']
                        }
                        # Apply the action
                        if self.atomic_config_system.apply_action(proposed):
                            # Record as pending for confirmation loop
                            if hasattr(self.atomic_config_system, 'record_pending_action'):
                                self.atomic_config_system.record_pending_action(proposed, baseline)
                            logger.info(f"[NEURAL→META] Applied proposed config: {proposed.get('parameter_path')} "
                                       f"= {proposed.get('proposed_value')}")
                
                # GAP 4 FIX: Confirm any pending actions from previous iterations
                if hasattr(self.atomic_config_system, 'confirm_action_outcome'):
                    current_metrics = {
                        'avg_loss': self.autotune_metrics_buffer['avg_loss'],
                        'improvement_rate': self.autotune_metrics_buffer['improvement_rate']
                    }
                    confirmed = self.atomic_config_system.confirm_action_outcome(current_metrics)
                    if confirmed:
                        logger.debug(f"[NEURAL→META] Confirmed {len(confirmed) if isinstance(confirmed, list) else 1} action(s) outcome")
                        
            except Exception as e:
                logger.debug(f"AutoTune integration error: {e}")
        
        # Emit event for CRA visualization
        if self.event_emitter:
            try:
                from causation_explorer import Event
                event = Event(
                    timestamp=time.time(),
                    component='neural',
                    event_type='neural_autotune_metrics',
                    data={
                        'avg_loss': self.autotune_metrics_buffer['avg_loss'],
                        'improvement_rate': self.autotune_metrics_buffer['improvement_rate'],
                        'loss_variance': self.autotune_metrics_buffer['loss_variance'],
                        'training_steps': self.autotune_metrics_buffer['training_steps_completed'],
                        'organisms_trained_total': self.autotune_metrics_buffer['organisms_trained_total']
                    }
                )
                self.event_emitter(event)
            except Exception as e:
                logger.debug(f"AutoTune event emission failed: {e}")
    
    def get_autotune_metrics(self) -> Dict[str, Any]:
        """
        Get current AutoTune metrics buffer for CRA diagnostics.
        
        Returns:
            Dictionary of neural training metrics for AutoTune integration
        """
        return {
            **self.autotune_metrics_buffer,
            # buffer_size is already set correctly in autotune_metrics_buffer from collect_experiences()
            # loss_history_size is separate from experience buffer_size
            'loss_history_size': len(self.autotune_metrics_buffer['loss_history']),
            'window_size': self.autotune_loss_window,
            'atomic_config_connected': self.atomic_config_system is not None
        }
    
    def get_training_stats(self) -> Dict[str, Any]:
        """
        Get training statistics.
        
        Returns:
            Dictionary of training statistics including granular loss breakdown
        """
        steps = max(1, self.training_step_count)
        stats = {
            'training_steps': self.training_step_count,
            'average_loss': self.total_loss / steps,
            'average_language_loss': self.total_language_loss / steps if self.language_model_enabled else None,
            'average_rl_loss': self.total_rl_loss / steps,  # Granular: RL/DQN loss
            'average_concept_loss': self.total_concept_loss / steps if self.concept_system_enabled else None,
            # EMA smoothed losses (less noisy)
            'ema_loss': self.ema_loss,
            'ema_rl_loss': self.ema_rl_loss,
            'ema_language_loss': self.ema_language_loss if self.language_model_enabled else None,
            'ema_concept_loss': self.ema_concept_loss if self.concept_system_enabled else None,
            'last_training_time': self.last_training_time,
            'organisms_tracked': len(self.organism_fitness_history),
            'language_model_enabled': self.language_model_enabled,
            'current_sequence_length': self.current_sequence_length,
            'vp_stable_steps': self.vp_stable_steps,
            # RCUS concept system stats
            'concept_system_enabled': self.concept_system_enabled,
            'concept_compositions_evaluated': self.concept_compositions_evaluated if self.concept_system_enabled else 0,
        }
        
        # Add useful concept stats if concept system is active
        if self.concept_system_enabled and self.concept_system is not None:
            useful_concepts = self.concept_system.get_useful_concepts(top_k=5)
            stats['top_useful_concepts'] = [
                {'name': name, 'utility': utility, 'use_count': count}
                for name, utility, count in useful_concepts
            ]
        
        return stats
    
    def calculate_language_loss(self,
                                language_logits: 'torch.Tensor',
                                target_tokens: 'torch.Tensor',
                                vp_value: Optional[float] = None,
                                curiosity: Optional[float] = None) -> 'torch.Tensor':
        """
        Calculate next-token prediction loss with VP-aware scaling.
        
        Args:
            language_logits: Predicted logits from language head (batch, seq, vocab)
            target_tokens: Target token IDs (batch, seq)
            vp_value: Current VP value for temperature scaling
            curiosity: Organism's curiosity trait [0-1]. Scales entropy bonus.
                       Higher curiosity = more exploration = more diverse language.
            
        Returns:
            Scaled language loss tensor
        """
        # Apply VP temperature scaling to logits before loss calculation
        if self.vp_temperature_scaling and vp_value is not None and vp_value > 0:
            # Higher VP = lower temperature = more confident predictions
            temperature = 1.0 / (1.0 + vp_value)
            language_logits = language_logits / temperature
        
        # Reshape for cross-entropy: (batch * seq, vocab) and (batch * seq)
        batch_size, seq_len, vocab_size = language_logits.shape
        logits_flat = language_logits.view(-1, vocab_size)
        targets_flat = target_tokens.view(-1)
        
        # ELASTIC VOCAB: Mask out-of-bounds tokens instead of crashing
        # This allows vocabulary to grow beyond neural network's fixed vocab_size
        # Out-of-bounds tokens are set to 0 (ignore_index) so they don't affect loss
        oob_mask = targets_flat >= vocab_size
        if oob_mask.any():
            targets_flat = targets_flat.clone()
            targets_flat[oob_mask] = 0  # Mark as ignore
        
        # Calculate cross-entropy loss with label smoothing (ignores padding tokens with index 0)
        # Label smoothing reduces overconfidence and helps prevent mode collapse
        loss = F.cross_entropy(
            logits_flat, targets_flat, 
            ignore_index=0, 
            label_smoothing=self.language_label_smoothing
        )
        
        # Entropy bonus: encourage exploration in language generation
        # This prevents mode collapse to single tokens ("shorten shorten" bug)
        # Similar to action head's entropy bonus (0.01 coefficient)
        # 🧬 CURIOSITY SCALING: Organism's curiosity gene amplifies entropy bonus
        entropy_value = 0.0
        effective_entropy_bonus = self.language_entropy_bonus
        if curiosity is not None:
            # Curiosity [0-1] scales entropy bonus from 0.5x to 2x base value
            # Low curiosity (0.0) = 0.5x bonus (less exploration)
            # High curiosity (1.0) = 2x bonus (more exploration)  
            curiosity_multiplier = 0.5 + (curiosity * 1.5)  # Range: 0.5 to 2.0
            effective_entropy_bonus = self.language_entropy_bonus * curiosity_multiplier
        
        if effective_entropy_bonus > 0:
            probs = F.softmax(logits_flat, dim=-1)
            # Calculate entropy: -sum(p * log(p)), clamping for numerical stability
            log_probs = torch.log(probs + 1e-9)
            entropy_value = -(probs * log_probs).sum(dim=-1).mean()
            # Subtract entropy bonus (maximize entropy = minimize negative entropy)
            loss = loss - effective_entropy_bonus * entropy_value
        
        # VP gating: if VP > threshold, reduce language loss influence
        if vp_value is not None and vp_value > self.vp_gate_threshold:
            # Scale down language loss when system is unstable
            gate_factor = 1.0 - ((vp_value - self.vp_gate_threshold) / (1.0 - self.vp_gate_threshold))
            gate_factor = max(0.1, gate_factor)  # Never fully zero out
            loss = loss * gate_factor
        
        # Emit neural_language_training event for causation graph
        if self.event_emitter:
            try:
                from causation_explorer import Event
                event = Event(
                    timestamp=time.time(),
                    component='neural',
                    event_type='neural_language_training',
                    data={
                        'vocab_size': vocab_size,
                        'language_loss': float(loss.item()) if hasattr(loss, 'item') else float(loss),
                        'token_sequence_length': seq_len,
                        'batch_size': batch_size,
                        'vp_value': vp_value,
                        'vp_gated': vp_value is not None and vp_value > self.vp_gate_threshold,
                        'current_curriculum_length': self.current_sequence_length,
                        'entropy_bonus': effective_entropy_bonus,
                        'entropy_value': float(entropy_value.item()) if hasattr(entropy_value, 'item') else float(entropy_value),
                        'label_smoothing': self.language_label_smoothing,
                        'curiosity': curiosity
                    }
                )
                self.event_emitter(event)
            except ImportError:
                pass  # CausationExplorer not available
        
        return loss
    
    def adjust_curriculum_from_ml_quality(self, ml_analysis: Optional[Dict[str, Any]]) -> Optional[int]:
        """
        Adjust curriculum (sequence length) based on ML-measured language quality.
        
        Integration 3: Neural-ML Symbiosis - uses population language quality metrics
        to adjust training complexity.
        
        Args:
            ml_analysis: ML analysis results containing quality metrics
            
        Returns:
            New sequence length if adjusted, None otherwise
        """
        if not ml_analysis:
            return None
        
        # Extract quality metrics
        semantic_analysis = ml_analysis.get('semantic_analysis', {})
        if not semantic_analysis:
            return None
        
        quality_metrics = semantic_analysis.get('quality_metrics', {})
        
        if not quality_metrics:
            return None
        
        silhouette_score = quality_metrics.get('silhouette_score', None)
        if silhouette_score is None:
            return None
        
        # Get curriculum config
        language_config = self.config.get('language_model', {})
        curriculum_config = language_config.get('curriculum', {})
        ml_quality_config = curriculum_config.get('ml_quality', {})
        
        if not ml_quality_config.get('enabled', False):
            return None
        
        high_threshold = ml_quality_config.get('high_quality_threshold', 0.6)
        low_threshold = ml_quality_config.get('low_quality_threshold', 0.3)
        step_size = ml_quality_config.get('sequence_length_step', 2)
        min_length = ml_quality_config.get('min_sequence_length', 8)
        max_length = ml_quality_config.get('max_sequence_length', 64)
        
        old_length = self.current_sequence_length
        new_length = old_length
        
        # Adjust based on quality
        if silhouette_score > high_threshold:
            # High quality: increase sequence length
            new_length = min(max_length, old_length + step_size)
        elif silhouette_score < low_threshold:
            # Low quality: decrease sequence length
            new_length = max(min_length, old_length - step_size)
        
        # Only update if changed significantly (prevent oscillation)
        if abs(new_length - old_length) >= step_size:
            self.current_sequence_length = new_length
            
            # Log curriculum change
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[CURRICULUM] Adjusted sequence length: {old_length} → {new_length} "
                       f"(silhouette={silhouette_score:.3f})")
            
            # Emit event for curriculum adjustment (Integration 3: Neural-ML Symbiosis)
            if self.event_emitter:
                try:
                    from causation_explorer import Event
                    event = Event(
                        timestamp=time.time(),
                        component='neural',
                        event_type='neural_curriculum_adjustment',
                        data={
                            'old_sequence_length': int(old_length),
                            'new_sequence_length': int(new_length),
                            'silhouette_score': float(silhouette_score),
                            'adjustment_reason': 'high_quality' if silhouette_score > high_threshold else 'low_quality',
                            'high_threshold': high_threshold,
                            'low_threshold': low_threshold
                        }
                    )
                    self.event_emitter(event)
                except Exception as e:
                    logger.debug(f"Curriculum event emission failed: {e}")
            
            return new_length
        
        return None
    
    def update_curriculum(self, vp_value: float) -> bool:
        """
        Update curriculum learning based on VP stability.
        
        Increases sequence length when VP is stable below thresholds.
        
        Args:
            vp_value: Current VP value
            
        Returns:
            True if sequence length was increased
        """
        if not self.curriculum_learning or not self.language_model_enabled:
            return False
        
        # Track VP history
        self.vp_history.append(vp_value)
        if len(self.vp_history) > 100:
            self.vp_history = self.vp_history[-100:]
        
        # Determine current curriculum stage
        if self.current_sequence_length == 8:
            threshold_key = '8_to_16'
            next_length = 16
        elif self.current_sequence_length == 16:
            threshold_key = '16_to_32'
            next_length = 32
        elif self.current_sequence_length == 32:
            threshold_key = '32_to_128'
            next_length = 128
        else:
            return False  # Already at max
        
        threshold_config = self.curriculum_thresholds.get(threshold_key, {})
        vp_threshold = threshold_config.get('vp_threshold', 0.5)
        stability_steps = threshold_config.get('stability_steps', 20)
        
        # Check if VP is below threshold
        if vp_value < vp_threshold:
            self.vp_stable_steps += 1
        else:
            self.vp_stable_steps = 0  # Reset on threshold breach
        
        # Advance curriculum if stable for required steps
        if self.vp_stable_steps >= stability_steps:
            self.current_sequence_length = next_length
            self.vp_stable_steps = 0  # Reset for next stage
            
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[CURRICULUM] Advanced sequence length: {self.current_sequence_length}")
            
            return True
        
        return False
    
    def apply_vp_temperature_to_logits(self, 
                                        logits: 'torch.Tensor', 
                                        vp_value: float) -> 'torch.Tensor':
        """
        Apply VP-based temperature scaling to language logits.
        
        Higher VP = lower temperature = sharper predictions (more conservative).
        
        Args:
            logits: Raw logits from language head
            vp_value: Current VP value
            
        Returns:
            Temperature-scaled logits
        """
        if vp_value <= 0:
            return logits
        
        # Temperature scaling: T = 1 / (1 + VP)
        # VP=0 → T=1.0 (no change)
        # VP=0.5 → T=0.67 (sharper)
        # VP=1.0 → T=0.5 (very sharp)
        temperature = 1.0 / (1.0 + vp_value)
        
        return logits / temperature

    # =========================================================================
    # 🆕 CHAT-TRIGGERED LEARNING METHODS
    # Close the experience→training→generation loop for Butterfly Chat
    # =========================================================================
    
    def train_from_chat_experiences(self, 
                                    organism: 'NeuralOrganism',
                                    network_state: Optional[Dict[str, Any]] = None) -> Optional[float]:
        """
        Train organism from accumulated chat experiences.
        
        Uses token sequences stored in experience buffer for language model training.
        Called periodically by ButterflyChatRouter to close the learning loop.
        
        Args:
            organism: Neural organism to train
            network_state: Network state for context
            
        Returns:
            Training loss if training occurred, None otherwise
        """
        if not PYTORCH_AVAILABLE:
            return None
        
        # Check if organism has required components
        if not hasattr(organism, 'brain') or organism.brain is None:
            return None
        if not hasattr(organism, 'experience_buffer') or organism.experience_buffer is None:
            return None
        if len(organism.experience_buffer) < 2:
            return None
        
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # GROK SWARM FIX: Use proper seq2seq data from experience buffer instead of token_sequence
            # This fixes the root cause of repetitive outputs - training on proper input→target pairs
            
            # Check if experience buffer has seq2seq data
            if hasattr(organism.experience_buffer, 'has_seq2seq_data') and organism.experience_buffer.has_seq2seq_data(min_count=2):
                # Use proper seq2seq sampling
                _, _, rewards, _, _, input_tokens_list, target_tokens_list, _, vp_values = \
                    organism.experience_buffer.sample_batch_with_seq2seq(min(4, len(organism.experience_buffer)))
                
                # Find the longest input/target pair for training
                best_idx = 0
                best_len = 0
                for i, (inp, tgt) in enumerate(zip(input_tokens_list, target_tokens_list)):
                    if len(inp) > 0 and len(tgt) > 0 and len(inp) + len(tgt) > best_len:
                        best_len = len(inp) + len(tgt)
                        best_idx = i
                
                if best_len >= 2:
                    # Use the best seq2seq pair
                    input_seq = input_tokens_list[best_idx]
                    target_seq = target_tokens_list[best_idx]
                    vp_value = vp_values[best_idx] if vp_values[best_idx] is not None else 0.0
                    
                    # Prepare tensors
                    input_tokens = torch.LongTensor([input_seq]).to(self.device)
                    target_tokens = torch.LongTensor([target_seq]).to(self.device)
                else:
                    # Fall back to token_sequence if no good seq2seq data
                    return self._train_from_token_sequence(organism, network_state)
            else:
                # Fall back to legacy token_sequence method
                return self._train_from_token_sequence(organism, network_state)
            
            # Get VP value for temperature scaling (if not already set from seq2seq)
            if vp_value is None:
                vp_value = network_state.get('vp_value', 0.0) if network_state else 0.0
            
            # Get state features for brain input
            if hasattr(organism, 'get_state_features'):
                state = organism.get_state_features(
                    local_env=None,
                    network_state=network_state,
                    breath_state=None
                )
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            else:
                brain_input_dim = organism.brain.fc1.in_features
                state_tensor = torch.zeros(1, brain_input_dim, device=self.device)
            
            # Forward pass to get language logits
            organism.brain.train()
            
            # ⚡ AMP: Use autocast for forward passes
            amp_context = torch.amp.autocast('cuda', dtype=self.amp_dtype) if self.amp_enabled else nullcontext()
            
            with amp_context:
                if hasattr(organism.brain, 'fc_language'):
                    # Get language head output
                    hidden = torch.relu(organism.brain.fc1(state_tensor))
                    hidden = torch.relu(organism.brain.fc2(hidden))
                    language_logits = organism.brain.fc_language(hidden)
                    
                    # Expand to sequence length (use target_tokens size from seq2seq)
                    seq_len = target_tokens.size(1)
                    language_logits = language_logits.unsqueeze(1).expand(-1, seq_len, -1)
                    
                    # Calculate loss with organism's curiosity
                    # 🧬 Pass organism's curiosity trait to scale entropy bonus
                    curiosity = getattr(organism.phenotype, 'curiosity', 0.5) if hasattr(organism, 'phenotype') else 0.5
                    loss = self.calculate_language_loss(language_logits, target_tokens, vp_value, curiosity=curiosity)
                    
                    # Backpropagation
                    organism_id = id(organism.brain)
                    if self.reuse_optimizers:
                        if organism_id not in self.optimizers:
                            self.optimizers[organism_id] = optim.Adam(
                                organism.brain.parameters(), 
                                lr=self.learning_rate
                            )
                        optimizer = self.optimizers[organism_id]
                    else:
                        optimizer = optim.Adam(organism.brain.parameters(), lr=self.learning_rate)
                    
                    optimizer.zero_grad()
                    
                    # ⚡ AMP: Use gradient scaling for mixed precision
                    if self.amp_enabled and self.grad_scaler is not None:
                        self.grad_scaler.scale(loss).backward()
                        self.grad_scaler.step(optimizer)
                        self.grad_scaler.update()
                    else:
                        loss.backward()
                        optimizer.step()
                    
                    # Emit training event
                    if self.event_emitter:
                        try:
                            from causation_explorer import Event
                            event = Event(
                                timestamp=time.time(),
                                component='neural',
                                event_type='chat_training_complete',
                                data={
                                    'organism_id': getattr(organism, 'species_id', str(organism_id)),
                                    'loss': float(loss.item()),
                                    'sequence_length': len(input_seq) + len(target_seq),  # GROK FIX: was token_seq (undefined)
                                    'vp_value': vp_value
                                }
                            )
                            self.event_emitter(event)
                        except Exception as e:
                            logger.debug(f"Chat training event emission failed: {e}")
                    
                    logger.debug(f"[NEURAL] Chat training loss: {loss.item():.4f}")
                    return loss.item()
            
            return None
            
        except Exception as e:
            logger.debug(f"[NEURAL] Chat training failed: {e}")
            return None
    
    def _train_from_token_sequence(self,
                                   organism: 'NeuralOrganism',
                                   network_state: Optional[Dict[str, Any]] = None) -> Optional[float]:
        """
        LEGACY FALLBACK: Train from organism.token_sequence when no seq2seq data available.
        
        This is the old method that trains on concatenated token history.
        Used only when experience buffer has no proper input_tokens/target_tokens data.
        
        Args:
            organism: Neural organism to train
            network_state: Current network state
            
        Returns:
            Loss value if training occurred, None otherwise
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Get token sequences from organism
        if not hasattr(organism, 'token_sequence') or len(organism.token_sequence) < 4:
            return None
        
        try:
            # Get token sequence for training
            token_seq = list(organism.token_sequence)
            
            # Need at least 4 tokens for meaningful training
            if len(token_seq) < 4:
                return None
            
            # Use last N tokens (curriculum-based length)
            seq_len = min(len(token_seq), self.current_sequence_length)
            token_seq = token_seq[-seq_len:]
            
            # Prepare input/target pairs for next-token prediction (legacy approach)
            input_tokens = torch.LongTensor([token_seq[:-1]]).to(self.device)
            target_tokens = torch.LongTensor([token_seq[1:]]).to(self.device)
            
            # Get VP value for temperature scaling
            vp_value = network_state.get('vp_value', 0.0) if network_state else 0.0
            
            # Get state features for brain input
            if hasattr(organism, 'get_state_features'):
                state = organism.get_state_features(
                    local_env=None,
                    network_state=network_state,
                    breath_state=None
                )
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            else:
                brain_input_dim = organism.brain.fc1.in_features
                state_tensor = torch.zeros(1, brain_input_dim, device=self.device)
            
            # Forward pass to get language logits
            organism.brain.train()
            
            # ⚡ AMP: Use autocast for forward passes
            amp_context = torch.amp.autocast('cuda', dtype=self.amp_dtype) if self.amp_enabled else nullcontext()
            
            with amp_context:
                if hasattr(organism.brain, 'fc_language'):
                    # Get language head output - use get_hidden_state for proper Hopfield routing
                    if hasattr(organism.brain, 'get_hidden_state'):
                        hidden = organism.brain.get_hidden_state(state_tensor, vp_value=vp_value)
                    else:
                        # Fallback for older brains without helper
                        hidden = torch.relu(organism.brain.fc1(state_tensor))
                        hidden = torch.relu(organism.brain.fc2(hidden))
                    language_logits = organism.brain.fc_language(hidden)
                    
                    # Expand to sequence length
                    language_logits = language_logits.unsqueeze(1).expand(-1, len(token_seq)-1, -1)
                    
                    # Calculate loss with organism's curiosity
                    # 🧬 Pass organism's curiosity trait to scale entropy bonus
                    curiosity = getattr(organism.phenotype, 'curiosity', 0.5) if hasattr(organism, 'phenotype') else 0.5
                    loss = self.calculate_language_loss(language_logits, target_tokens, vp_value, curiosity=curiosity)
                    
                    if loss is not None:
                        # Get or create optimizer (inline pattern - no helper method)
                        organism_id = id(organism.brain)
                        if self.reuse_optimizers:
                            if organism_id not in self.optimizers:
                                self.optimizers[organism_id] = optim.Adam(
                                    organism.brain.parameters(),
                                    lr=self.learning_rate
                                )
                            optimizer = self.optimizers[organism_id]
                        else:
                            optimizer = optim.Adam(organism.brain.parameters(), lr=self.learning_rate)
                        
                        optimizer.zero_grad()
                        
                        # ⚡ AMP: Use gradient scaling for mixed precision
                        if self.amp_enabled and self.grad_scaler is not None:
                            self.grad_scaler.scale(loss).backward()
                            self.grad_scaler.unscale_(optimizer)
                            torch.nn.utils.clip_grad_norm_(organism.brain.parameters(), 1.0)
                            self.grad_scaler.step(optimizer)
                            self.grad_scaler.update()
                        else:
                            loss.backward()
                            torch.nn.utils.clip_grad_norm_(organism.brain.parameters(), 1.0)
                            optimizer.step()
                        
                        logger.debug(f"[NEURAL] Legacy token_sequence training loss: {loss.item():.4f}")
                        return loss.item()
            
            return None
            
        except Exception as e:
            logger.debug(f"[NEURAL] Legacy token_sequence training failed: {e}")
            return None
    
    def bootstrap_language_learning(self,
                                    organism: 'NeuralOrganism',
                                    user_tokens: List[int],
                                    network_state: Optional[Dict[str, Any]] = None) -> bool:
        """
        Bootstrap learning for organisms that generated empty responses.
        
        Uses TEMPLATE RESPONSES instead of teacher forcing on user input.
        This teaches organisms proper response patterns rather than echoing.
        
        Based on Claude's supervised learning gap analysis:
        - Problem: Teaching organism to predict user_tokens[i+1] from user_tokens[i]
          causes organism to learn to echo/repeat user input
        - Solution: Use template response patterns that teach appropriate responses
        
        Args:
            organism: Neural organism to bootstrap
            user_tokens: User input tokens (used for context classification)
            network_state: Network state for context
            
        Returns:
            True if bootstrap training occurred
        """
        if not PYTORCH_AVAILABLE:
            return False
        
        if not user_tokens or len(user_tokens) < 1:
            return False
        
        if not hasattr(organism, 'brain') or organism.brain is None:
            return False
        
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Get vocabulary for template tokenization
            vocab = getattr(organism, 'vocabulary', None)
            if vocab is None:
                # Try to get from butterfly chat or use fallback
                if hasattr(organism, 'chat_interface') and organism.chat_interface:
                    vocab = getattr(organism.chat_interface, 'vocabulary', None)
            
            if vocab is None:
                logger.debug("[NEURAL] Bootstrap learning skipped: no vocabulary")
                return False
            
            # Generate template response based on input context
            template_response = self._get_bootstrap_template_response(user_tokens, vocab)
            
            if not template_response or len(template_response) < 2:
                logger.debug("[NEURAL] Bootstrap learning skipped: no valid template")
                return False
            
            # Create proper seq2seq training data:
            # INPUT: user_tokens (what user said)
            # TARGET: template_response (proper response pattern)
            input_tokens = torch.LongTensor([user_tokens]).to(self.device)
            target_tokens = torch.LongTensor([template_response]).to(self.device)
            
            # Get state for brain input
            if hasattr(organism, 'get_state_features'):
                state = organism.get_state_features(
                    local_env=None,
                    network_state=network_state,
                    breath_state=None
                )
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            else:
                brain_input_dim = organism.brain.fc1.in_features
                state_tensor = torch.zeros(1, brain_input_dim, device=self.device)
            
            # Forward pass
            organism.brain.train()
            
            # ⚡ AMP: Use autocast for forward passes
            amp_context = torch.amp.autocast('cuda', dtype=self.amp_dtype) if self.amp_enabled else nullcontext()
            
            with amp_context:
                if hasattr(organism.brain, 'fc_language'):
                    # Use get_hidden_state for proper Hopfield routing
                    if hasattr(organism.brain, 'get_hidden_state'):
                        hidden = organism.brain.get_hidden_state(state_tensor, vp_value=0.0)
                    else:
                        # Fallback for older brains without helper
                        hidden = torch.relu(organism.brain.fc1(state_tensor))
                        hidden = torch.relu(organism.brain.fc2(hidden))
                    language_logits = organism.brain.fc_language(hidden)
                    
                    # Expand to target sequence length
                    target_len = len(template_response)
                    language_logits = language_logits.unsqueeze(1).expand(-1, target_len, -1)
                    
                    # Use higher learning rate for bootstrap (faster learning)
                    bootstrap_lr = self.learning_rate * 2.0
                    
                    # Calculate loss against TEMPLATE response, not user echo
                    # 🧬 Pass organism's curiosity trait to scale entropy bonus
                    curiosity = getattr(organism.phenotype, 'curiosity', 0.5) if hasattr(organism, 'phenotype') else 0.5
                    loss = self.calculate_language_loss(language_logits, target_tokens, vp_value=0.0, curiosity=curiosity)
                    
                    # Backpropagation
                    optimizer = optim.Adam(organism.brain.parameters(), lr=bootstrap_lr)
                    optimizer.zero_grad()
                    
                    # ⚡ AMP: Use gradient scaling for mixed precision
                    if self.amp_enabled and self.grad_scaler is not None:
                        self.grad_scaler.scale(loss).backward()
                        self.grad_scaler.step(optimizer)
                        self.grad_scaler.update()
                    else:
                        loss.backward()
                        optimizer.step()
                    
                    # Store experience with proper input/target separation
                    # This creates a learning signal: "when you see X, say Y"
                    if hasattr(organism, 'experience_buffer') and organism.experience_buffer is not None:
                        state_np = state_tensor.cpu().numpy().flatten()
                        vp_val = network_state.get('vp_value') if network_state else None
                        organism.experience_buffer.add(
                            state=state_np,
                            action=0,
                            reward=0.5,  # Good reward for learning proper response
                            next_state=state_np,
                            done=False,
                            input_tokens=user_tokens,          # What user said
                            target_tokens=template_response,   # Proper response
                            vp_value=vp_val
                        )
                    
                    # Add template to organism's token sequence for vocabulary exposure
                    if hasattr(organism, 'token_sequence'):
                        for token in template_response:
                            organism.token_sequence.append(token)
                    
                    # Emit bootstrap event
                    if self.event_emitter:
                        try:
                            from causation_explorer import Event
                            event = Event(
                                timestamp=time.time(),
                                component='neural',
                                event_type='bootstrap_learning_complete',
                                data={
                                    'organism_id': getattr(organism, 'species_id', str(id(organism))),
                                    'loss': float(loss.item()),
                                    'input_tokens': len(user_tokens),
                                    'template_tokens': len(template_response),
                                    'method': 'template_response'
                                }
                            )
                            self.event_emitter(event)
                        except Exception as e:
                            logger.debug(f"Bootstrap learning event emission failed: {e}")
                    
                    logger.debug(f"[NEURAL] Bootstrap with template: loss={loss.item():.4f}, template_len={len(template_response)}")
                    return True
            
            return False
            
        except Exception as e:
            logger.debug(f"[NEURAL] Bootstrap learning failed: {e}")
            return False
    
    def _get_bootstrap_template_response(self, user_tokens: List[int], vocab) -> List[int]:
        """
        Generate appropriate template response tokens based on input context.
        
        Templates teach organisms proper response patterns instead of echoing.
        This implements Claude's recommendation for structured bootstrap learning.
        
        Categories:
        - Greetings → Greeting responses
        - Questions → Thinking/acknowledgment responses
        - Unknown → Safe generic responses
        """
        import random
        
        # Decode user tokens to analyze intent
        try:
            user_words = []
            for token in user_tokens:
                word = vocab.id_to_token.get(token, '')
                if word:
                    user_words.append(word.lower())
            user_text = ' '.join(user_words)
        except Exception:
            user_text = ""
        
        # Classify intent and select template category
        greeting_words = {'hello', 'hi', 'hey', 'greetings', 'howdy'}
        question_words = {'what', 'how', 'why', 'when', 'where', 'who', 'which', 'could', 'would', 'can'}
        
        is_greeting = any(word in user_words for word in greeting_words)
        is_question = any(word in user_words for word in question_words)
        
        # Template responses by category
        # These teach proper conversational patterns
        templates = {
            'greeting': [
                "Hello there.",
                "Hi! Nice to meet you.",
                "Hello, how are you?",
                "Hey! Welcome.",
                "Greetings friend.",
            ],
            'question': [
                "That is interesting.",
                "I think about that.",
                "Let me consider...",
                "Good question.",
                "I wonder about that too.",
            ],
            'generic': [
                "I understand.",
                "Tell me more.",
                "I see.",
                "That makes sense.",
                "Please continue.",
                "Interesting.",
            ]
        }
        
        # Select appropriate template category
        if is_greeting:
            category = 'greeting'
        elif is_question:
            category = 'question'
        else:
            category = 'generic'
        
        # Pick random template from category
        template_text = random.choice(templates[category])
        
        # Tokenize template
        try:
            template_tokens = vocab.encode(template_text)
            return template_tokens
        except Exception as e:
            logger.debug(f"Template tokenization failed: {e}")
            # Fallback: return a simple known token sequence
            return [1, 2, 3]  # Will depend on vocab, but better than empty

    # ═══════════════════════════════════════════════════════════════════════════
    # CONCEPT SYSTEM PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def save_concept_system(self, path: str):
        """
        Save the concept system state.
        
        Args:
            path: File path to save concept system (e.g., 'saves/concept_system.pt')
        """
        if not self.concept_system_enabled or self.concept_system is None:
            logger.debug("No concept system to save")
            return
        
        try:
            self.concept_system.save_state(path)
            logger.info(f"[NEURAL] Concept system saved to {path}")
        except Exception as e:
            logger.error(f"[NEURAL] Failed to save concept system: {e}")
    
    def load_concept_system(self, path: str):
        """
        Load the concept system state.
        
        Args:
            path: File path to load concept system from
        """
        if not self.concept_system_enabled or self.concept_system is None:
            logger.warning("Concept system not enabled, cannot load")
            return
        
        try:
            self.concept_system.load_state(path)
            logger.info(f"[NEURAL] Concept system loaded from {path}")
        except Exception as e:
            logger.error(f"[NEURAL] Failed to load concept system: {e}")
    
    def get_concept_system_state(self) -> Optional[Dict[str, Any]]:
        """
        Get serializable concept system state for saving.
        
        Returns:
            Dictionary with concept system state, or None if not enabled
        """
        if not self.concept_system_enabled or self.concept_system is None:
            return None
        
        return {
            'concept_utility': dict(self.concept_system.concept_utility),
            'concept_use_count': dict(self.concept_system.concept_use_count),
            'total_concept_loss': self.total_concept_loss,
            'concept_compositions_evaluated': self.concept_compositions_evaluated,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECKPOINT SYSTEM - Save/Load Complete Training State
    # Preserves neural brains, experience buffer, optimizer states across restarts
    # ═══════════════════════════════════════════════════════════════════════════
    
    def save_checkpoint(self, checkpoint_dir: str, organisms: List[Any], 
                       generation: int = 0, metadata: Optional[Dict] = None) -> bool:
        """
        Save complete training state checkpoint.
        
        Saves:
        - All organism neural brain weights
        - Experience buffer (if enabled)
        - Optimizer states (if enabled)
        - Concept system state
        - VP history
        - Training metrics
        - Metadata (generation, timestamp, config)
        
        Args:
            checkpoint_dir: Directory to save checkpoint files
            organisms: List of NeuralOrganism instances
            generation: Current generation number
            metadata: Optional additional metadata
            
        Returns:
            True if checkpoint saved successfully, False otherwise
        """
        import os
        import json
        from datetime import datetime
        
        try:
            os.makedirs(checkpoint_dir, exist_ok=True)
            
            # 1. Save neural brain weights
            brain_states = {}
            for org in organisms:
                if hasattr(org, 'brain') and org.brain is not None:
                    org_id = getattr(org, 'id', id(org))
                    try:
                        brain_states[str(org_id)] = {
                            'state_dict': org.brain.state_dict(),
                            'fitness': getattr(org, 'fitness', 0.0),
                            'age': getattr(org, 'age', 0),
                        }
                    except Exception as e:
                        logger.warning(f"[CHECKPOINT] Failed to save brain for organism {org_id}: {e}")
            
            if brain_states:
                brain_path = os.path.join(checkpoint_dir, 'neural_brains.pt')
                torch.save(brain_states, brain_path)
                logger.info(f"[CHECKPOINT] Saved {len(brain_states)} neural brains")
            
            # 2. Save experience buffer
            experience_data = self._serialize_experience_buffer()
            if experience_data:
                exp_path = os.path.join(checkpoint_dir, 'experience_buffer.pt')
                torch.save(experience_data, exp_path)
                logger.info(f"[CHECKPOINT] Saved experience buffer ({len(experience_data.get('experiences', []))} experiences)")
            
            # 3. Save optimizer states
            if self.optimizers:
                optimizer_states = {}
                for org_id, optimizer in self.optimizers.items():
                    try:
                        optimizer_states[str(org_id)] = optimizer.state_dict()
                    except Exception as e:
                        logger.warning(f"[CHECKPOINT] Failed to save optimizer for {org_id}: {e}")
                
                if optimizer_states:
                    opt_path = os.path.join(checkpoint_dir, 'optimizer_states.pt')
                    torch.save(optimizer_states, opt_path)
                    logger.info(f"[CHECKPOINT] Saved {len(optimizer_states)} optimizer states")
            
            # 4. Save concept system
            if self.concept_system_enabled and self.concept_system is not None:
                concept_path = os.path.join(checkpoint_dir, 'concept_system.pt')
                self.save_concept_system(concept_path)
            
            # 5. Save metadata
            checkpoint_metadata = {
                'timestamp': datetime.now().isoformat(),
                'generation': generation,
                'training_step_count': self.training_step_count,
                'total_loss': float(self.total_loss),
                'total_language_loss': float(self.total_language_loss),
                'organisms_count': len(brain_states),
                'experience_buffer_size': len(experience_data.get('experiences', [])) if experience_data else 0,
                'vp_history_length': len(self.vp_history),
                'current_sequence_length': self.current_sequence_length,
                'early_stopped': self.early_stopped,
                'best_loss': float(self.best_loss) if self.best_loss != float('inf') else None,
                'config': {
                    'batch_size': self.batch_size,
                    'learning_rate': self.learning_rate,
                    'gamma': self.gamma,
                    'input_dim': self.config.get('brain', {}).get('input_dim', 27),
                    'hidden_dim': self.config.get('brain', {}).get('hidden_dim', 64),  # Default matches config.json
                    'output_dim': self.config.get('brain', {}).get('output_dim', 6),
                },
                'autotune_metrics': self.autotune_metrics_buffer.copy(),
            }
            
            if metadata:
                checkpoint_metadata.update(metadata)
            
            # Also save VP history
            checkpoint_metadata['vp_history'] = self.vp_history[-100:]  # Last 100 VP values
            
            # 6. Save AtomicConfigSystem state (learning state)
            if self.atomic_config_system is not None:
                try:
                    atomic_config_state = {}
                    for name, atom in self.atomic_config_system.atoms.items():
                        atomic_config_state[name] = atom.to_dict()
                    
                    atomic_path = os.path.join(checkpoint_dir, 'atomic_config.json')
                    with open(atomic_path, 'w') as f:
                        json.dump(atomic_config_state, f, indent=2)
                    logger.info(f"[CHECKPOINT] Saved AtomicConfigSystem state ({len(atomic_config_state)} atoms)")
                except Exception as e:
                    logger.warning(f"[CHECKPOINT] Failed to save AtomicConfigSystem: {e}")
            
            meta_path = os.path.join(checkpoint_dir, 'metadata.json')
            with open(meta_path, 'w') as f:
                json.dump(checkpoint_metadata, f, indent=2, default=str)
            
            logger.info(f"[CHECKPOINT] Checkpoint saved to {checkpoint_dir} (gen={generation})")
            return True
            
        except Exception as e:
            logger.error(f"[CHECKPOINT] Failed to save checkpoint: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_checkpoint(self, checkpoint_dir: str, organisms: List[Any],
                       strict: bool = False) -> Dict[str, Any]:
        """
        Load complete training state from checkpoint.
        
        Restores:
        - Neural brain weights (matched by organism ID when possible)
        - Experience buffer
        - Optimizer states
        - Concept system state
        - VP history
        - Training metrics
        
        Args:
            checkpoint_dir: Directory containing checkpoint files
            organisms: List of NeuralOrganism instances to restore weights to
            strict: If True, raise errors on architecture mismatch; if False, skip mismatched
            
        Returns:
            Dict with load results: {'success': bool, 'loaded': {...}, 'errors': [...]}
        """
        import os
        import json
        
        result = {
            'success': False,
            'loaded': {
                'brains': 0,
                'experiences': 0,
                'optimizers': 0,
                'concept_system': False,
            },
            'errors': [],
            'warnings': [],
            'metadata': None,
        }
        
        if not os.path.exists(checkpoint_dir):
            result['errors'].append(f"Checkpoint directory not found: {checkpoint_dir}")
            return result
        
        try:
            # 1. Load metadata first (to validate architecture)
            meta_path = os.path.join(checkpoint_dir, 'metadata.json')
            if os.path.exists(meta_path):
                with open(meta_path, 'r') as f:
                    result['metadata'] = json.load(f)
                
                # Check architecture compatibility
                saved_config = result['metadata'].get('config', {})
                current_input_dim = self.config.get('brain', {}).get('input_dim', 27)
                saved_input_dim = saved_config.get('input_dim', 27)
                
                if current_input_dim != saved_input_dim:
                    msg = f"Architecture mismatch: saved input_dim={saved_input_dim}, current={current_input_dim}"
                    if strict:
                        result['errors'].append(msg)
                        return result
                    else:
                        result['warnings'].append(msg + " - some weights may not load correctly")
            
            # 2. Load neural brain weights
            brain_path = os.path.join(checkpoint_dir, 'neural_brains.pt')
            if os.path.exists(brain_path):
                brain_states = torch.load(brain_path, map_location=self.device, weights_only=False)
                
                # Create lookup of organisms by ID
                org_by_id = {}
                for org in organisms:
                    org_id = str(getattr(org, 'id', id(org)))
                    org_by_id[org_id] = org
                
                loaded_brains = 0
                for org_id, brain_data in brain_states.items():
                    if org_id in org_by_id:
                        org = org_by_id[org_id]
                        if hasattr(org, 'brain') and org.brain is not None:
                            try:
                                org.brain.load_state_dict(brain_data['state_dict'], strict=strict)
                                loaded_brains += 1
                            except Exception as e:
                                result['warnings'].append(f"Failed to load brain {org_id}: {e}")
                    else:
                        # Try to load into any organism without a match (for new populations)
                        for org in organisms:
                            if hasattr(org, 'brain') and org.brain is not None:
                                try:
                                    org.brain.load_state_dict(brain_data['state_dict'], strict=False)
                                    loaded_brains += 1
                                    break
                                except:
                                    continue
                
                result['loaded']['brains'] = loaded_brains
                logger.info(f"[CHECKPOINT] Loaded {loaded_brains} neural brains")
            
            # 3. Load experience buffer
            exp_path = os.path.join(checkpoint_dir, 'experience_buffer.pt')
            if os.path.exists(exp_path):
                experience_data = torch.load(exp_path, map_location=self.device, weights_only=False)
                loaded_exp = self._deserialize_experience_buffer(experience_data)
                result['loaded']['experiences'] = loaded_exp
                logger.info(f"[CHECKPOINT] Loaded {loaded_exp} experiences")
            
            # 4. Load optimizer states
            opt_path = os.path.join(checkpoint_dir, 'optimizer_states.pt')
            if os.path.exists(opt_path):
                optimizer_states = torch.load(opt_path, map_location=self.device, weights_only=False)
                loaded_opts = 0
                for org_id_str, opt_state in optimizer_states.items():
                    try:
                        org_id = int(org_id_str)
                        if org_id in self.optimizers:
                            self.optimizers[org_id].load_state_dict(opt_state)
                            loaded_opts += 1
                    except Exception as e:
                        result['warnings'].append(f"Failed to load optimizer {org_id_str}: {e}")
                
                result['loaded']['optimizers'] = loaded_opts
                logger.info(f"[CHECKPOINT] Loaded {loaded_opts} optimizer states")
            
            # 5. Load concept system
            concept_path = os.path.join(checkpoint_dir, 'concept_system.pt')
            if os.path.exists(concept_path) and self.concept_system_enabled:
                try:
                    self.load_concept_system(concept_path)
                    result['loaded']['concept_system'] = True
                except Exception as e:
                    result['warnings'].append(f"Failed to load concept system: {e}")
            
            # 6. Restore training state from metadata
            if result['metadata']:
                meta = result['metadata']
                self.training_step_count = meta.get('training_step_count', 0)
                self.total_loss = meta.get('total_loss', 0.0)
                self.total_language_loss = meta.get('total_language_loss', 0.0)
                self.current_sequence_length = meta.get('current_sequence_length', 8)
                self.early_stopped = meta.get('early_stopped', False)
                if meta.get('best_loss') is not None:
                    self.best_loss = meta.get('best_loss')
                if meta.get('vp_history'):
                    self.vp_history = meta.get('vp_history', [])
                if meta.get('autotune_metrics'):
                    self.autotune_metrics_buffer.update(meta.get('autotune_metrics', {}))
            
            # 7. Load AtomicConfigSystem state
            atomic_path = os.path.join(checkpoint_dir, 'atomic_config.json')
            if os.path.exists(atomic_path) and self.atomic_config_system is not None:
                try:
                    with open(atomic_path, 'r') as f:
                        atomic_config_state = json.load(f)
                    
                    restored_count = 0
                    for name, atom_data in atomic_config_state.items():
                        if name in self.atomic_config_system.atoms:
                            atom = self.atomic_config_system.atoms[name]
                            # Restore learning state (not value - config.json is source of truth)
                            if 'strength' in atom_data:
                                atom.strength = atom_data['strength']
                            if 'stability' in atom_data:
                                atom.stability = atom_data.get('stability', 0.5)
                            if 'update_count' in atom_data:
                                atom.update_count = atom_data.get('update_count', 0)
                            restored_count += 1
                    
                    result['loaded']['atomic_config'] = restored_count
                    logger.info(f"[CHECKPOINT] Restored {restored_count} AtomicConfig atom states")
                except Exception as e:
                    result['warnings'].append(f"Failed to load AtomicConfigSystem: {e}")
            
            result['success'] = True
            logger.info(f"[CHECKPOINT] Checkpoint loaded from {checkpoint_dir}")
            
        except Exception as e:
            result['errors'].append(f"Failed to load checkpoint: {e}")
            import traceback
            traceback.print_exc()
        
        return result
    
    def _serialize_experience_buffer(self) -> Optional[Dict]:
        """
        Serialize experience buffer for saving.
        
        Returns:
            Dictionary with serialized experiences, or None if no organisms
        """
        # Experience buffer is typically stored per-organism in NeuralOrganism
        # We need to collect from self if we have a shared buffer
        # For now, return training metrics that help resume
        return {
            'experiences': [],  # Individual organisms manage their buffers
            'vp_history': self.vp_history[-1000:],  # Save recent VP history
            'training_step_count': self.training_step_count,
            'vp_stable_steps': self.vp_stable_steps,
            'language_reward_total': self.language_reward_total,
            'language_reward_count': self.language_reward_count,
        }
    
    def _deserialize_experience_buffer(self, data: Dict) -> int:
        """
        Restore experience buffer from saved data.
        
        Args:
            data: Serialized experience buffer data
            
        Returns:
            Number of experiences restored
        """
        if not data:
            return 0
        
        # Restore VP history
        if 'vp_history' in data:
            self.vp_history = data['vp_history']
        
        # Restore counters
        if 'vp_stable_steps' in data:
            self.vp_stable_steps = data['vp_stable_steps']
        if 'language_reward_total' in data:
            self.language_reward_total = data['language_reward_total']
        if 'language_reward_count' in data:
            self.language_reward_count = data['language_reward_count']
        
        return len(data.get('experiences', []))
    
    def rotate_checkpoints(self, checkpoint_base_dir: str, max_checkpoints: int = 10):
        """
        Delete old checkpoints to stay within max_checkpoints limit.
        
        Args:
            checkpoint_base_dir: Base directory containing checkpoint folders
            max_checkpoints: Maximum number of checkpoints to keep
        """
        import os
        import shutil
        
        if not os.path.exists(checkpoint_base_dir):
            return
        
        # Find all checkpoint directories (format: checkpoint_YYYYMMDD_HHMMSS)
        checkpoints = []
        for name in os.listdir(checkpoint_base_dir):
            if name.startswith('checkpoint_') and os.path.isdir(os.path.join(checkpoint_base_dir, name)):
                full_path = os.path.join(checkpoint_base_dir, name)
                # Parse timestamp from name for sorting
                try:
                    # checkpoint_YYYYMMDD_HHMMSS
                    timestamp_str = name.replace('checkpoint_', '')
                    checkpoints.append((timestamp_str, full_path))
                except:
                    checkpoints.append((name, full_path))
        
        # Sort by timestamp (oldest first)
        checkpoints.sort(key=lambda x: x[0])
        
        # Delete oldest checkpoints beyond limit
        while len(checkpoints) > max_checkpoints:
            _, oldest_path = checkpoints.pop(0)
            try:
                shutil.rmtree(oldest_path)
                logger.info(f"[CHECKPOINT] Rotated out old checkpoint: {oldest_path}")
            except Exception as e:
                logger.warning(f"[CHECKPOINT] Failed to delete old checkpoint {oldest_path}: {e}")
    
    def get_latest_checkpoint(self, checkpoint_base_dir: str) -> Optional[str]:
        """
        Find the most recent checkpoint directory.
        
        Args:
            checkpoint_base_dir: Base directory containing checkpoint folders
            
        Returns:
            Path to latest checkpoint directory, or None if no checkpoints
        """
        import os
        
        if not os.path.exists(checkpoint_base_dir):
            return None
        
        checkpoints = []
        for name in os.listdir(checkpoint_base_dir):
            if name.startswith('checkpoint_') and os.path.isdir(os.path.join(checkpoint_base_dir, name)):
                full_path = os.path.join(checkpoint_base_dir, name)
                try:
                    timestamp_str = name.replace('checkpoint_', '')
                    checkpoints.append((timestamp_str, full_path))
                except:
                    checkpoints.append((name, full_path))
        
        if not checkpoints:
            return None
        
        # Sort by timestamp (newest last)
        checkpoints.sort(key=lambda x: x[0])
        return checkpoints[-1][1]
    
    def create_checkpoint_name(self) -> str:
        """
        Generate a timestamped checkpoint directory name.
        
        Returns:
            Directory name in format: checkpoint_YYYYMMDD_HHMMSS
        """
        from datetime import datetime
        return f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def should_checkpoint(self, generation: int) -> bool:
        """
        Check if a checkpoint should be saved based on config thresholds.
        
        Args:
            generation: Current generation number
            
        Returns:
            True if checkpoint should be saved
        """
        if not self.checkpoint_enabled:
            return False
        
        # Check generation-based trigger
        if generation - self._last_checkpoint_generation >= self.checkpoint_interval_generations:
            return True
        
        # Check time-based trigger
        elapsed_minutes = (time.time() - self._last_checkpoint_time) / 60.0
        if elapsed_minutes >= self.checkpoint_interval_minutes:
            return True
        
        return False
    
    def maybe_checkpoint(self, organisms: List[Any], generation: int, 
                        metadata: Optional[Dict] = None) -> bool:
        """
        Save checkpoint if thresholds are met.
        
        Convenience method for main loop to call each generation.
        Handles checkpoint creation, rotation, and tracking.
        
        Args:
            organisms: List of NeuralOrganism instances
            generation: Current generation number
            metadata: Optional additional metadata
            
        Returns:
            True if checkpoint was saved, False otherwise
        """
        import os
        
        if not self.should_checkpoint(generation):
            return False
        
        # Create checkpoint directory
        checkpoint_name = self.create_checkpoint_name()
        checkpoint_path = os.path.join(self.checkpoint_dir, checkpoint_name)
        
        # Save checkpoint
        success = self.save_checkpoint(checkpoint_path, organisms, generation, metadata)
        
        if success:
            # Update tracking
            self._last_checkpoint_generation = generation
            self._last_checkpoint_time = time.time()
            self._checkpoint_count += 1
            
            # Rotate old checkpoints
            self.rotate_checkpoints(self.checkpoint_dir, self.checkpoint_max_count)
            
            # Emit checkpoint event
            if self.event_emitter:
                try:
                    from causation_explorer import Event
                    event = Event(
                        timestamp=time.time(),
                        component='neural',
                        event_type='checkpoint_saved',
                        data={
                            'generation': generation,
                            'checkpoint_path': checkpoint_path,
                            'checkpoint_count': self._checkpoint_count,
                            'organisms_count': len(organisms),
                        }
                    )
                    self.event_emitter(event)
                except ImportError:
                    pass
        
        return success
    
    def auto_resume(self, organisms: List[Any]) -> Optional[Dict]:
        """
        Automatically load the latest checkpoint if auto_resume is enabled.
        
        Call this after trainer initialization and before training starts.
        
        Args:
            organisms: List of NeuralOrganism instances to restore weights to
            
        Returns:
            Load result dict if resumed, None if no checkpoint or disabled
        """
        if not self.checkpoint_auto_resume:
            return None
        
        latest = self.get_latest_checkpoint(self.checkpoint_dir)
        if latest is None:
            logger.info("[CHECKPOINT] No checkpoint found for auto-resume")
            return None
        
        logger.info(f"[CHECKPOINT] Auto-resuming from: {latest}")
        result = self.load_checkpoint(latest, organisms, strict=False)
        
        if result['success']:
            logger.info(f"[CHECKPOINT] Auto-resume successful: {result['loaded']}")
            # Update tracking from loaded metadata
            if result['metadata']:
                self._last_checkpoint_generation = result['metadata'].get('generation', 0)
        else:
            logger.warning(f"[CHECKPOINT] Auto-resume failed: {result['errors']}")
        
        return result




