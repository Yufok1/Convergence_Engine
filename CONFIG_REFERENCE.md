# Configuration Reference – Butterfly System

**Last Updated:** 2025-12-03

This document mirrors `config.json` so you can keep the file itself machine-valid (no inline comments) while still knowing what each knob does. Open `config.json` side-by-side with this reference.

> **Editing tip:** Because the config is pure JSON, keep comments out of the file. Instead, jot notes in this guide or create git commit messages that highlight why a tweak was made.

---

## Top-Level Sections

| Section | Purpose |
|---------|---------|
| `agency` | Autonomous agent decision parameters |
| `causation_detection` | Real-time causation graph settings |
| `evolution` | Genetic algorithm parameters |
| `feedback` | Closed-loop mutation/edge tuning |
| `health_monitor` | System health classification |
| `highlander` | Survival tournament + Alliance Warfare |
| `lattice` | Micro lattice simulation |
| `logging` | State dump intervals |
| `meta_cognitive` | Self-tuning brain |
| `network` | Graph limits and precision |
| `neural` | Brain + language model + training |
| `quantum` | Quantum subsystem heuristics |
| `ray` | Distributed computing (Ray) |
| `rendering` | Visualization settings |
| `scikit` | Classical ML analytics |
| `simulation` | Global runtime settings |
| `vp_monitoring` | Violation Pressure dashboards |

---

## `agency`

Autonomous agent decision parameters.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `confidence_threshold` | float | 0.0001 | Minimum statistical confidence before the agent acts autonomously |
| `decision_precision` | float | 1e-05 | Decimal precision for decision comparisons (smaller = more sensitive) |
| `initial_mode` | string | "manual_only" | Startup autonomy mode (`manual_only`, `assisted`, `autonomous`) |
| `learning_rate_resolution` | float | 1e-06 | Step size when tuning adaptive learning rates |
| `performance_tracking_precision` | float | 0.0001 | Decimal precision for KPI logging |

---

## `causation_detection`

Controls the real-time causation explorer graph.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Master toggle for causation detection |
| `correlation_threshold` | float | 0.45 | Minimum correlation before an edge is drawn |
| `direct_causation_time_window` | float | 2.0 | Minutes to look back for direct causal events |
| `phase_transition_time_window` | float | 2.5 | Minutes to look back for phase transitions |
| `recent_events_window` | int | 150 | Number of recent events kept in memory |
| `enable_bidirectional_causations` | bool | true | Enable bidirectional causal links |
| `enable_language_causations` | bool | true | Enable language system causation links |
| `enable_ml_causations` | bool | true | Enable ML analysis causation links |
| `enable_neural_causations` | bool | true | Enable neural system causation links |
| `enable_neural_decision_causations` | bool | true | Enable neural decision event links |
| `enable_neural_training_causations` | bool | true | Enable neural training event links |
| `enable_phase_transition_causations` | bool | true | Enable phase transition causation links |

### `causation_detection.thresholds`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `clustering_coefficient.collapse` | float | 0.5 | Clustering threshold for collapse detection |
| `clustering_coefficient.direction` | string | "above" | Direction for threshold trigger |
| `modularity.collapse` | float | 0.3 | Modularity threshold for collapse detection |
| `modularity.direction` | string | "below" | Direction for threshold trigger |
| `organism_count.collapse` | int | 500 | Organism count threshold |
| `organism_count.direction` | string | "above" | Direction for threshold trigger |
| `violation_pressure.vp0-3` | float | 0.25-0.99 | VP band thresholds |
| `vp_calculations.transition` | int | 50 | VP calculation transition threshold |

---

## `evolution`

Genetic algorithm and mutation settings.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `adaptation_sensitivity` | float | 0.002 | Responsiveness of adaptation heuristics |
| `fitness_precision` | float | 1e-07 | Decimal precision for fitness comparisons |
| `genotype_length` | int | 48 | Length of binary genome per organism |
| `max_generations` | int | 1500 | Hard stop for evolution runs |
| `mutation_rate.initial` | float | 0.045 | Initial mutation rate |
| `mutation_rate_precision` | float | 0.001 | Tuning precision for mutation rate |
| `population_size` | int | 200 | Base population per generation |

### `evolution.diversity_guard`

Anti-clone guardrails to prevent population collapse.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable diversity protection |
| `frequency_threshold` | float | 0.1 | Threshold for frequency-based penalties |
| `hash_similarity_threshold` | float | 0.92 | Similarity threshold for clone detection |
| `penalty` | float | 0.05 | Fitness penalty for clones |

---

## `feedback`

Closed-loop controllers for mutation/new-edge tuning.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable feedback system |
| `interval_frames` | int | 10 | How frequently feedback checks run |
| `hysteresis_checks` | int | 3 | Confirmations before change is accepted |
| `rate_limit_frames` | int | 60 | Cool-down between adjustments |

### `feedback.knobs`

Each knob has `initial`, `min`, `max`, `step` for adaptive sliders.

| Knob | Initial | Min | Max | Step |
|------|---------|-----|-----|------|
| `clustering_bias` | 1.5 | 0.3 | 1.6 | 0.05 |
| `mutation_rate` | 0.04 | 0.002 | 0.06 | 0.001 |
| `new_edge_rate` | 2.5 | 0.2 | 6.0 | 0.1 |
| `quantum_pruning` | 0.45 | 0.0 | 1.0 | 0.05 |

---

## `health_monitor`

System health classification and monitoring.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable health monitoring |
| `history_size` | int | 100 | Samples retained for moving averages |
| `critical_threshold` | float | 0.25 | Health below this = CRITICAL |
| `warning_threshold` | float | 0.45 | Health below this = WARNING |
| `healthy_threshold` | float | 0.65 | Health above this = HEALTHY |
| `weight_adaptability` | float | 0.2 | Weight for adaptability component |
| `weight_coherence` | float | 0.3 | Weight for coherence component |
| `weight_diversity` | float | 0.25 | Weight for diversity component |
| `weight_lawfulness` | float | 0.15 | Weight for lawfulness component |
| `weight_sustainability` | float | 0.1 | Weight for sustainability component |

---

## `highlander`

Tournament survival system with Alliance Warfare.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable Highlander Protocol |
| `competition_intensity` | float | 0.8 | Battle difficulty (0-1) |
| `chaos_factor` | float | 0.4 | Random event probability |
| `population_size` | int | 100 | Initial population |
| `max_population` | int | 30 | Maximum organisms |
| `min_population` | int | 5 | Minimum before germination |
| `mutation_rate` | float | 0.15 | Mutation rate for offspring |
| `germination_rate` | float | 0.1 | Probability capsules respawn |
| `max_capsules` | int | 10 | Champion checkpoint capacity |
| `max_genetic_samples` | int | 100 | Genetic sample vault capacity |
| `max_battle_rounds` | int | 50 | Maximum rounds per battle |
| `rounds_per_cycle` | int | 2 | Battle rounds per cycle |
| `survival_threshold` | float | 0.5 | Minimum fitness to survive |
| `predation_enabled` | bool | true | Enable predator-prey dynamics |

### `highlander.alliance_warfare` ⭐

Collective warfare for existential dominance.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable alliance system |
| `min_alliance_size` | int | 3 | Minimum organisms for alliance |
| `max_alliance_size` | int | 10 | Maximum organisms per alliance |
| `max_alliances` | int | 1000 | Maximum concurrent alliances |
| `max_confederations` | int | 50 | Maximum super-alliances |
| `war_frequency` | float | 0.3 | War probability each cycle |
| `war_declaration_threshold` | float | 0.4 | Threshold for war declaration |
| `existential_war_threshold` | float | 0.8 | Threshold for total annihilation |
| `confederation_war_threshold` | float | 0.7 | Vote ratio for mega-war |
| `betrayal_chance` | float | 0.05 | Probability of alliance betrayal |

### `highlander.extreme_mode`

Override settings for EXTREME difficulty.

| Key | Value | Description |
|-----|-------|-------------|
| `competition_intensity` | 1.0 | Maximum pressure |
| `survival_threshold` | 0.8 | Very high survival bar |
| `max_population` | 20 | Small arena |
| `min_population` | 2 | Near extinction allowed |
| `germination_rate` | 0.05 | Rare respawns |

---

## `lattice`

Micro lattice simulation constants.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `particles` | int | 500 | Number of lattice particles |
| `entropy_sensitivity` | float | 5e-05 | Noise level for entropy adjustments |
| `interaction_precision` | float | 0.0001 | Decimal precision for interactions |
| `prune_threshold` | float | 0.0 | Minimum weight before pruning |
| `stability_tolerance` | float | 0.0005 | Acceptable deviation before rebalancing |

---

## `logging`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `shared_state_dump_interval` | int | 300 | Seconds between state snapshots |

---

## `meta_cognitive`

Self-tuning brain for autonomous optimization.

### `meta_cognitive.self_tuning`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable autonomous tuning |
| `mode` | string | "autonomous" | Tuning authority level |
| `min_confidence_threshold` | float | 0.6 | Confidence needed for updates |
| `tuning_interval_frames` | int | 20 | Frames between tuning cycles |

### `meta_cognitive.self_tuning.performance_targets`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `max_anomaly_ratio` | float | 0.2 | Maximum acceptable anomalies |
| `min_cluster_diversity` | int | 3 | Minimum cluster count |
| `min_fitness_std` | float | 0.05 | Minimum fitness variance |

### `meta_cognitive.self_tuning.safe_parameters`

Array of config paths the tuner may modify. See config.json for full list.

---

## `network`

Graph limits for organism interaction network.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `max_organisms` | int | 500 | Hard cap on organism count |
| `max_connections` | int | 1000000 | Hard cap on edge count |
| `resource_pool` | int | 550 | Total shared resources |
| `connection_strength_resolution` | float | 5e-06 | Decimal precision for edge weights |
| `resource_flow_precision` | float | 0.0001 | Decimal precision for resource flow |
| `stability_precision` | float | 1e-07 | Decimal precision for stability |
| `emergence_sensitivity` | float | 1e-06 | Sensitivity for emergence detection |

---

## `neural`

Brain + language system configuration.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Master toggle for neural system |
| `device` | string | "cuda" | PyTorch device (`cuda`, `cpu`, `mps`) |

### `neural.brain`

DQN architecture settings.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `input_dim` | int | 24 | Input feature dimensions |
| `hidden_dim` | int | 64 | Hidden layer size |
| `output_dim` | int | 6 | Action space size |
| `activation` | string | "relu" | Activation function |
| `dropout` | float | 0.1 | Dropout rate |
| `vocab_size` | int | 50000 | Vocabulary size for language head |

### `neural.training`

DQN training hyperparameters.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable training |
| `learning_rate` | float | 0.008 | DQN learning rate |
| `batch_size` | int | 64 | Training batch size |
| `gamma` | float | 0.995 | Discount factor |
| `epsilon_start` | float | 0.8 | Initial exploration rate |
| `epsilon_end` | float | 0.01 | Final exploration rate |
| `epsilon_decay` | float | 0.985 | Epsilon decay per step |
| `memory_size` | int | 20000 | Replay buffer size |
| `update_frequency` | int | 1 | Steps between updates |
| `language_reward_scaling` | float | 0.25 | Language reward weight |

### `neural.training.lr_scheduler` ⭐

Learning rate scheduler settings.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable LR scheduling |
| `type` | string | "step" | Scheduler type (`step`, `exponential`, `plateau`) |
| `step_size` | int | 100 | Steps between LR decay (step scheduler) |
| `gamma` | float | 0.95 | LR decay factor |
| `min_lr` | float | 1e-6 | Minimum learning rate |

### `neural.training.early_stopping` ⭐

Early stopping to prevent overfitting.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable early stopping |
| `patience` | int | 50 | Steps without improvement before stop |
| `min_delta` | float | 1e-4 | Minimum loss change for improvement |

### `neural.inheritance`

Brain inheritance during reproduction.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable Lamarckian inheritance |
| `crossover_rate` | float | 0.9 | Two-parent crossover probability |
| `mutation_rate` | float | 0.2 | Brain weight mutation rate |

### `neural.rewards`

Reward shaping values.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `fitness_improvement` | float | 3.5 | Reward for fitness gain |
| `connection_success` | float | 2.5 | Reward for successful connection |
| `connection_failure` | float | -0.2 | Penalty for failed connection |
| `survival` | float | 1.5 | Reward for surviving |
| `resource_gain` | float | 1.0 | Reward for resource gain |
| `resource_loss` | float | -0.3 | Penalty for resource loss |

### `neural.vp_aware_planning`

VP-driven planning boosts.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable VP-aware planning |
| `low_threshold` | float | 0.25 | VP threshold for base boost |
| `high_threshold` | float | 0.45 | VP threshold for strong boost |
| `base_boost` | float | 0.2 | Base planning boost |
| `strong_boost` | float | 0.3 | Strong planning boost |

### `neural.language_model`

Language model configuration.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable language model |

#### `neural.language_model.attention`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable attention mechanism |
| `attention_dim` | int | 32 | Attention dimension |
| `num_heads` | int | 4 | Number of attention heads |

#### `neural.language_model.vocabulary`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `max_size` | int | 50000 | Maximum vocabulary size |
| `special_tokens` | array | [...] | PAD, UNK, START, END, VP_GATE |

#### `neural.language_model.generation`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `max_length` | int | 32 | Maximum generated sequence length |
| `temperature` | float | 1.2 | Sampling temperature |
| `vp_gate_threshold` | float | 0.5 | VP threshold for generation gating |

#### `neural.language_model.training`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `alpha` | float | 0.8 | DQN loss weight |
| `beta` | float | 0.1 | Language loss weight |
| `gamma` | float | 0.1 | Concept loss weight |
| `vp_temperature_scale` | bool | true | Scale temperature by VP |

#### `neural.language_model.relationship_learning`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable relationship learning |
| `quality_evaluation.coherent_threshold` | float | 0.5 | Min coherence for success |
| `quality_evaluation.garbled_threshold` | float | 0.2 | Max coherence for failure |
| `quality_evaluation.unk_ratio_threshold` | float | 0.3 | Max UNK token ratio |
| `semantic_guidance.enabled` | bool | true | Enable semantic guidance |
| `semantic_guidance.semantic_boost` | float | 0.2 | Logit boost for related words |

#### `neural.language_model.curriculum`

ML-quality-aware curriculum learning.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable curriculum |
| `ml_quality.enabled` | bool | true | Use ML quality for gating |
| `ml_quality.min_sequence_length` | int | 8 | Minimum sequence length |
| `ml_quality.max_sequence_length` | int | 64 | Maximum sequence length |

#### `neural.language_model.knowledge_web`

Semantic knowledge web settings.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable knowledge web |
| `max_concepts` | int | 500 | Maximum concepts tracked |
| `embedding_dim` | int | 64 | Concept embedding dimension |

#### `neural.language_model.teacher`

Language teacher configuration.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable language teacher |
| `vocab_size` | int | 50000 | Teacher vocabulary size |
| `embedding_dim` | int | 64 | Teacher embedding dimension |
| `min_confidence` | float | 0.3 | Minimum teaching confidence |
| `teaching_frequency` | int | 1 | Teaching frequency |
| `use_knowledge_web` | bool | true | Use knowledge web for teaching |
| `use_semantic_embeddings` | bool | true | Use semantic embeddings |

### `neural.concept_system`

Concept lattice training.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable concept system |
| `embed_dim` | int | 64 | Concept embedding dimension |
| `num_key_compositions` | int | 15 | Key compositions count |
| `concept_loss_weight` | float | 0.1 | Concept loss weight |
| `utility_update_alpha` | float | 0.1 | Utility update rate |

### `neural.optimization`

PyTorch optimization flags.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `use_compile` | bool | false | Enable torch.compile |
| `compile_mode` | string | "reduce-overhead" | Compile mode |
| `use_scripted_inference` | bool | false | Use TorchScript |
| `reuse_optimizers` | bool | true | Reuse Adam optimizers |

### `neural.initialization`

Determinism controls.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `deterministic` | bool | false | Enable deterministic mode |
| `seed` | int/null | null | Random seed |

---

## `quantum`

Quantum subsystem heuristics.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `initial_states` | int | 80 | Number of quantum seeds |
| `entanglement_sensitivity` | float | 2.5e-06 | Entanglement sensitivity |
| `probability_precision` | float | 1e-06 | Probability precision |
| `superposition_tolerance` | float | 0.0005 | Superposition tolerance |
| `prune_check_interval` | int | 40 | Frames between pruning |

### `quantum.fitness_weights`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `entanglement` | float | 0.3 | Entanglement contribution |
| `entropy` | float | 0.2 | Entropy contribution |
| `measurements` | float | 0.25 | Measurement contribution |
| `superposition` | float | 0.25 | Superposition contribution |

### `quantum.performance_thresholds`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `fitness_std_threshold` | float | 0.3 | Fitness std threshold |
| `iteration_time_ms` | int | 10 | Max iteration time |
| `memory_percentage` | float | 5.0 | Max memory percentage |
| `min_fitness_to_keep` | float | 0.1 | Minimum fitness to keep |

---

## `ray`

Distributed execution with Ray.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable Ray backend |
| `num_cpus` | int | 4 | CPU allocation |
| `num_gpus` | int | 1 | GPU allocation |
| `object_store_memory` | int/null | null | Object store size |
| `actor_pool_size` | int | 2 | Max concurrent actors |
| `batch_inference_size` | int | 32 | Batch size for inference |
| `parallelization_threshold` | int | 100 | Min organisms for parallelism |
| `training_threshold` | int | 16 | Min trainable for parallel training |
| `fallback_on_error` | bool | true | Fall back to sequential on errors |
| `logging_level` | string | "warning" | Ray logging verbosity |

### `ray.memory_management`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `cleanup_on_organism_death` | bool | true | Clean up dead organism refs |
| `max_object_refs` | int | 100 | Max objects in store |
| `actor_pool_lru_eviction` | bool | true | LRU eviction for actors |

### `ray.state_synchronization`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `consistency_model` | string | "sequential" | Consistency model |
| `max_state_age_ms` | int | 100 | Max state staleness |
| `snapshot_strategy` | string | "breath_cycle" | When to sync state |

---

## `rendering`

Visualization settings.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enable_visualizations` | bool | true | Enable UI |
| `text_interface` | bool | true | Enable text overlay |
| `mode` | string | "god" | Camera mode |
| `resolution` | array | [1280, 720] | Output resolution |
| `frame_rate` | int | 15 | Target FPS |
| `render_quality` | string | "low" | Quality preset |
| `performance_monitoring` | bool | false | Show perf overlay |
| `metric_display_precision` | int | 6 | Metric decimal places |
| `visualization_update_precision` | float | 0.001 | Update precision |

---

## `scikit`

Classical ML analytics with scikit-learn.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable scikit-learn system |

### `scikit.clustering`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable clustering |
| `algorithm` | string | "hdbscan" | Algorithm (hdbscan, kmeans, dbscan) |
| `min_cluster_size` | int | 3 | Minimum cluster size |
| `min_samples` | int | 1 | Minimum samples |
| `use_neural_embeddings` | bool | true | Use neural embeddings |

### `scikit.anomaly_detection`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable anomaly detection |
| `algorithm` | string | "isolation_forest" | Algorithm |
| `contamination` | float | 0.15 | Expected outlier proportion |
| `n_estimators` | int | 400 | Number of trees |

### `scikit.dimensionality_reduction`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable dim reduction |
| `algorithm` | string | "pca" | Algorithm (pca, tsne, umap) |
| `n_components` | int | 3 | Output dimensions |

### `scikit.concept_tracking`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable concept tracking |
| `persistence_threshold` | int | 3 | Generations for persistence |
| `stale_threshold` | int | 10 | Generations until stale |

---

## `simulation`

Global runtime settings.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `log_level` | string | "INFO" | Logging verbosity |
| `max_runtime` | float | 3600.0 | Seconds before auto-stop |
| `save_interval` | float | 60.0 | Seconds between saves |
| `target_fps` | int | 3 | Target simulation FPS |
| `time_resolution_ms` | float | 1.0 | Base time slice |
| `measurement_precision` | int | 4 | Diagnostic decimal places |
| `performance_sampling_rate` | int | 200 | Performance sample rate |

---

## `vp_monitoring`

Violation Pressure monitoring and stabilization.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `diagnostics_enabled` | bool | true | Enable VP diagnostics |
| `adaptive_thresholds_enabled` | bool | true | Enable adaptive thresholds |
| `component_decomposition_enabled` | bool | true | Enable component breakdown |
| `stabilization_enabled` | bool | true | Enable VP stabilization |

### `vp_monitoring.adaptive_response`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `high_vp_threshold` | float | 0.85 | High VP trigger |
| `streak_threshold` | int | 3 | Streak before response |

### `vp_monitoring.component_weights`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `trait_divergence` | float | 0.15 | Trait divergence weight |
| `network_coherence` | float | 0.15 | Network coherence weight |
| `phase_mismatch` | float | 0.1 | Phase mismatch weight |
| `evolution_pressure` | float | 0.15 | Evolution pressure weight |
| `quantum_entropy` | float | 0.15 | Quantum entropy weight |

### `vp_monitoring.stabilization`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable smoothing |
| `smoothing_factor` | float | 0.25 | EMA smoothing factor |
| `history_size` | int | 15 | History for smoothing |
| `max_jump` | float | 0.1 | Maximum VP change per tick |

---

## Working With the Reference

1. **Split your editor:** `config.json` on the left, this file on the right
2. **Use find (`Ctrl/Cmd+F`)** to jump to section names
3. **Adjust values in `config.json`** and add notes here if needed
4. **Use CRA commands** to hot-reload config changes:
   ```json
   [[CONFIG_UPDATE: {"reason": "Increase learning rate", "correlation_id": "lr-test", "patch": [{"op": "replace", "path": "/neural/training/learning_rate", "value": 0.01}]}]]
   ```

---

## Quick Reference: Common Tuning Scenarios

### High VP / System Stress
- Increase `vp_monitoring.stabilization.smoothing_factor` (0.3-0.5)
- Lower `causation_detection.correlation_threshold` (0.3-0.4)
- Reduce `highlander.competition_intensity` (0.5-0.6)

### Low Diversity / Cloning
- Increase `evolution.diversity_guard.penalty` (0.1-0.2)
- Lower `evolution.diversity_guard.hash_similarity_threshold` (0.85-0.90)
- Increase `evolution.mutation_rate.initial` (0.06-0.08)

### Slow Learning
- Increase `neural.training.learning_rate` (0.01-0.02)
- Decrease `neural.training.epsilon_decay` (0.99-0.995)
- Increase `neural.training.batch_size` (128)

### Memory Issues
- Reduce `neural.training.memory_size` (10000)
- Lower `network.max_organisms` (300)
- Enable `ray.memory_management.cleanup_on_organism_death`

### Performance Issues
- Set `rendering.render_quality` to "low"
- Reduce `rendering.frame_rate` (10)
- Disable `neural.optimization.use_compile`
- Increase `ray.parallelization_threshold` (200)
