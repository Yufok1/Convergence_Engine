# Configuration Reference – Butterfly System

**Last Updated:** 2025-12-16

This document mirrors `config.json` so you can keep the file itself machine-valid (no inline comments) while still knowing what each knob does. Open `config.json` side-by-side with this reference.

> **Editing tip:** Because the config is pure JSON, keep comments out of the file. Instead, jot notes in this guide or create git commit messages that highlight why a tweak was made.

> **Unbounded convention:** For cap fields, `0` means no app-level cap. The host machine, disk, memory, Hugging Face lifecycle, and operating system remain physical limits, but the engine will not self-stop or self-prune because of that cap.

---

## Available Config Files

| Config | Purpose | Population | Target Hardware |
|--------|---------|------------|------------------|
| `config.json` | Default balanced settings | 200 | Auto-detect |
| `config_beastmode_saturation.json` | H100 stress test | 600 | H100 80GB |
| `config_colab_l4.json` | Google Colab L4 GPU | 150 | L4 24GB |
| `config_genesis.json` | Boom/bust from 5 progenitors | 5→800 | Any GPU |

Usage: `python unified_entry.py --config config_genesis.json`

---

## Top-Level Sections

| Section | Purpose |
|---------|---------|
| `agency` | Autonomous agent decision parameters |
| `arena` | Proton Game Arena battle system |
| `attractor_landscape` | Swarm attractor dynamics observatory |
| `causation_detection` | Real-time causation graph settings |
| `evolution` | Genetic algorithm parameters |
| `feedback` | Closed-loop mutation/edge tuning |
| `hardware_governor` | Hardware auto-scaling controls |
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
| `self_perception` | Reward shaping for attractor features |
| `semantic_convergence` | Unified embedding differentiation |
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

## `arena`

Proton Game Arena - Apprentice Adept style gym battles (Piers Anthony + Highlander inspired).

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Master toggle for battle arena |
| `default_battle_type` | string | "PROTON_GAME" | Default battle type |
| `prefer_native_games` | bool | true | Prioritize language/concept games over Gym |
| `proton_game_probability` | float | 1.0 | Fraction of battles using Proton Game (0.0-1.0) |

### `arena.battle_consequences`

What happens to losers and winners.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `fitness_transfer_rate` | float | 1.0 | How much fitness winner takes from loser |
| `resource_transfer_enabled` | bool | true | Enable resource absorption |
| `resource_transfer_rate` | float | 1.0 | Percentage of resources transferred |
| `trait_evolution_enabled` | bool | true | Allow trait changes from battle |
| `trait_bonus_cap` | float | 0.3 | Maximum trait bonus from single battle |

### `arena.game_selection`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `mode` | string | "ai_driven" | How game type is chosen |
| `allow_negotiation` | bool | true | Allow organisms to negotiate game type |
| `negotiation_rounds` | int | 3 | Rounds of negotiation before deadlock |
| `fallback_on_deadlock` | string | "random" | What happens on negotiation failure |

### `arena.grid_weights`

Weighting for different challenge and resource types.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `challenge_types.MENTAL` | float | 1.5 | Weight for mental challenges |
| `challenge_types.PHYSICAL` | float | 0.5 | Weight for physical challenges |
| `challenge_types.ARTS` | float | 2.0 | Weight for creative challenges |
| `challenge_types.CHANCE` | float | 1.0 | Weight for random challenges |
| `resource_types.NAKED` | float | 1.5 | Weight for unaided challenges |
| `resource_types.TOOL` | float | 1.0 | Weight for tool-assisted |
| `resource_types.MACHINE` | float | 1.0 | Weight for machine-assisted |
| `resource_types.ANIMAL` | float | 1.0 | Weight for animal-assisted |

### `arena.tournament`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `default_format` | string | "single_elimination" | Tournament structure |
| `seeding_method` | string | "fitness_based" | How brackets are seeded |
| `round_robin_battles_per_pair` | int | 3 | Battles per pair in round-robin |

---

## `attractor_landscape`

Collective magnetism field observatory for swarm attractor dynamics.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable attractor landscape tracking |
| `window_size` | int | 20 | Snapshot history size |
| `fixed_point_persistence` | int | 5 | Snapshots to confirm stable state |
| `fixed_point_variance_threshold` | float | 0.02 | Max variance for "fixed" point |
| `bifurcation_coherence_threshold` | float | 0.15 | Detect sudden coherence shifts |
| `bifurcation_entropy_threshold` | float | 0.20 | Detect sudden entropy shifts |
| `resonance_similarity_threshold` | float | 0.1 | Threshold for resonance detection |

**Genesis Note:** For small populations, increase `fixed_point_variance_threshold` to 0.03-0.04 as they have inherently more variance.

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
| `max_generations` | int | 0 | Hard stop for evolution runs; `0` = unbounded |
| `mutation_rate.initial` | float | 0.045 | Initial mutation rate |
| `mutation_rate_precision` | float | 0.001 | Tuning precision for mutation rate |
| `population_size` | int | 200 | Base population per generation |

**Genesis Protocol Note:** For 5-progenitor scenarios, set `population_size: 5` and increase `mutation_rate.initial` to 0.08+ to ensure genetic diversity from the small founder pool.

### `evolution.diversity_guard`

Anti-clone guardrails to prevent population collapse. **CRITICAL for small populations.**

| Key | Type | Default | Description | Genesis Value |
|-----|------|---------|-------------|---------------|
| `enabled` | bool | true | Enable diversity protection | true |
| `frequency_threshold` | float | 0.1 | Threshold for frequency-based penalties | 0.25 |
| `hash_similarity_threshold` | float | 0.92 | Similarity threshold for clone detection | 0.75 |
| `penalty` | float | 0.05 | Fitness penalty for clones | 0.12 |

**⚠️ Inbreeding Risk:** With 5 founders, aggressive diversity guard is essential. Lower `hash_similarity_threshold` to 0.75-0.80 to detect inbreeding early.

---

## `feedback`

Closed-loop controllers for mutation/new-edge tuning.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable feedback system |
| `interval_frames` | int | 10 | How frequently feedback checks run |
| `hysteresis_checks` | int | 3 | Confirmations before change is accepted |
| `rate_limit_frames` | int | 60 | Cool-down between adjustments |

**Genesis Note:** For boom/bust dynamics, widen `mutation_rate` range to `min: 0.01, max: 0.15` to allow spikes during bottlenecks.

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

## `hardware_governor`

Controls automatic hardware-based config scaling.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `auto_scale` | bool | true | Enable auto-scaling of config values to hardware |

When `auto_scale` is `false`, Governor will only clamp values to maximum (won't scale UP small configs).

---

## `highlander`

Tournament survival system with Alliance Warfare. Controls the core population dynamics including boom/bust cycles.

| Key | Type | Default | Description | Genesis Value |
|-----|------|---------|-------------|---------------|
| `enabled` | bool | true | Enable Highlander Protocol | true |
| `eval_interval_seconds` | int | 60 | Seconds between tournament evaluations | 45 |
| `competition_intensity` | float | 0.4 | Fraction of population that battles (0-1) | 0.15 |
| `chaos_factor` | float | 0.0 | Battle randomness (0=deterministic, >0.15=upsets) | 0.10 |
| `population_size` | int | 600 | Initial population to spawn | 5 |
| `max_population` | int | 0 | Ceiling before resource collapse; `0` = unbounded | 800 |
| `min_population` | int | 20 | Floor that triggers emergency germination | 3 |
| `mutation_rate` | float | 0.0 | Mutation rate for offspring | 0.05 |
| `germination_rate` | float | 1.0 | Rate of spawning new organisms (higher = faster boom) | 0.8 |
| `max_capsules` | int | 0 | Champion checkpoint capacity; `0` = unbounded | 100 |
| `max_genetic_samples` | int | 0 | Genetic sample vault capacity; `0` = unbounded | 200 |
| `max_battle_rounds` | int | 50 | Maximum rounds per battle | 30 |
| `rounds_per_cycle` | int | 2 | Battle rounds per breath cycle | 3 |
| `survival_threshold` | float | 0.4 | Minimum fitness to survive culling | 0.25 |
| `predation_enabled` | bool | true | High-fitness hunts low-fitness | true |

### Population Dynamics

**Highlander Tournament Flow (per round):**
1. **CULLING**: Remove organisms below `survival_threshold`
2. **COMPETITION**: `competition_intensity` fraction battles
3. **COOPERATION**: Alliance formation/maintenance
4. **PREDATION**: High-fitness hunts low-fitness (if enabled)
5. **GERMINATION**: If below `min_population`, spawn new organisms

**Boom/Bust Triggers:**
- **BOOM**: High `germination_rate` + low `survival_threshold` → exponential growth
- **BUST**: Resource scarcity + high `competition_intensity` → mass extinction
- **RECOVERY**: `min_population` floor triggers emergency germination

### `highlander.alliance_warfare` ⭐

Collective warfare for existential dominance. Small tribes that form, fight, betray, and dissolve.

| Key | Type | Default | Description | Genesis Value |
|-----|------|---------|-------------|---------------|
| `enabled` | bool | true | Enable alliance system | true |
| `min_alliance_size` | int | 2 | Minimum organisms for alliance | 2 |
| `max_alliance_size` | int | 500 | Maximum organisms per alliance | 15 |
| `max_alliances` | int | 9999 | Maximum concurrent alliances | 20 |
| `max_confederations` | int | 9999 | Maximum super-alliances | 5 |
| `war_frequency` | float | 0.5 | War probability each cycle | 0.25 |
| `war_declaration_threshold` | float | 0.6 | Confidence to declare war | 0.5 |
| `existential_war_threshold` | float | 0.8 | Threshold for total annihilation war | 0.7 |
| `confederation_war_threshold` | float | 0.6 | Vote ratio for mega-war | 0.5 |
| `betrayal_chance` | float | 0.0 | Probability of alliance betrayal | 0.03 |
| `illumination_stability_threshold` | int | 5 | Rounds before illumination unlocks | 3 |

**Alliance Benefits:**
- **Survival bonus**: Alliance members get fitness boost for culling
- **Combat bonus**: Up to 100% at 7 members + cohesion + knowledge synergy
- **Concept sharing**: Members share vocabulary freely
- **Collective defense**: Allies avoid fighting each other

**Betrayal Mechanics:**
- Tracks `cooperation_count` vs `defection_count` per organism
- Trust score = `cooperation / (cooperation + defection)`
- Betrayers marked and excluded from future alliances

**Genesis Note:** For small populations, limit `max_alliance_size` to prevent one alliance from dominating. Set `betrayal_chance` > 0 to prevent immortal dynasties.

### `highlander.extreme_mode`

Override settings for EXTREME difficulty. Activates during extinction events.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `competition_intensity` | float | 0.6 | Maximum pressure |
| `survival_threshold` | float | 0.5 | Very high survival bar |
| `max_population` | int | 0 | Small arena; `0` = unbounded |
| `min_population` | int | 3 | Near extinction allowed |
| `germination_rate` | float | 0.5 | Reduced respawns |
| `mutation_rate` | float | 0.12 | Higher mutation for diversity |
| `chaos_factor` | float | 0.15 | More upsets allowed |
| `max_battle_rounds` | int | 10 | Shorter battles |
| `rounds_per_cycle` | int | 3 | More rounds per cycle |
| `predation_enabled` | bool | true | Hunting enabled |

### `highlander.lineage_tracking` (Genesis Protocol)

Track family trees from founder organisms. Essential for preventing inbreeding from small populations.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable lineage tracking |
| `track_ancestry` | bool | true | Track full family tree |
| `founder_bonus` | float | 0.08 | Fitness bonus for founding lineage |
| `genetic_diversity_pressure` | float | 0.1 | Pressure toward diverse mating |
| `inbreeding_penalty` | float | 0.20 | Fitness penalty for inbred offspring |
| `dynasty_bonus` | float | 0.05 | Bonus for long-surviving lineages |
| `max_lineage_depth` | int | 100 | Maximum ancestry depth to track |

### `highlander.boom_bust_dynamics` (Genesis Protocol)

Emergent economic cycles from resource/population feedback.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable boom/bust cycle detection |
| `boom_detection_threshold` | float | 0.7 | Resource abundance = boom |
| `bust_detection_threshold` | float | 0.25 | Resource scarcity = bust |
| `resource_scarcity_multiplier` | float | 1.5 | Competition boost during scarcity |
| `abundance_germination_boost` | float | 2.0 | Germination boost during abundance |
| `scarcity_competition_boost` | float | 1.5 | Competition boost during scarcity |
| `cycle_memory_generations` | int | 20 | Generations to track cycle history |
| `seasonal_amplitude` | float | 0.4 | Resource oscillation amplitude |
| `seasonal_period_generations` | int | 200 | Generations per seasonal cycle |

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
| `shared_state_dump_interval` | int | 30 | Seconds between state snapshots |
| `sample_rate` | int | 5 | Log 1 in N state entries to disk (1=all, 10=10%) |
| `track_lineage` | bool | true | Enable lineage tracking in logs |
| `track_extinctions` | bool | true | Log extinction events |
| `boom_bust_log` | bool | true | Log boom/bust cycle transitions |

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

Graph limits for organism interaction network. Controls resource economics.

| Key | Type | Default | Description | Genesis Value |
|-----|------|---------|-------------|---------------|
| `max_organisms` | int | 0 | Hard cap on organism count; `0` = unbounded | 1000 |
| `max_connections` | int | 0 | Hard cap on per-organism connections; `0` = unbounded | 50000 |
| `resource_pool` | int | 5000 | Total shared ecosystem resources | 1500 |
| `connection_strength_resolution` | float | 5e-06 | Decimal precision for edge weights | 5e-06 |
| `resource_flow_precision` | float | 0.0001 | Decimal precision for resource flow | 0.001 |
| `stability_precision` | float | 1e-07 | Decimal precision for stability | 1e-07 |
| `emergence_sensitivity` | float | 1e-06 | Sensitivity for emergence detection | 1e-06 |

**Resource Economics:**
- `resource_pool` is the total ecosystem carrying capacity
- Lower pool = faster scarcity = triggers bust cycles
- Rule of thumb: Set `resource_pool` ≥ 50 × expected average population
- For Genesis Protocol: 1500 pool supports boom to ~800, then triggers bust

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
| `input_dim` | int | 28 | Input feature dimensions (includes attractor features) |
| `hidden_dim` | int | 192 | Hidden layer size (192 for H100, 64 for smaller) |
| `output_dim` | int | 6 | Action space size |
| `activation` | string | "relu" | Activation function |
| `dropout` | float | 0.1 | Dropout rate (0.15 for small populations) |
| `vocab_size` | int | 25000 | Vocabulary size for language head |
| `attention_dim` | int | 56 | Attention dimension |

### `neural.hopfield`

Modern continuous Hopfield network for iterative thought refinement.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable Hopfield network |
| `patterns` | int | 64 | Number of stored patterns |
| `iterations` | int | 5 | Refinement iterations |
| `beta` | float | 1.0 | Inverse temperature |

### `neural.training`

DQN training hyperparameters.

| Key | Type | Default | Description | Genesis Value |
|-----|------|---------|-------------|---------------|
| `enabled` | bool | true | Enable training | true |
| `learning_rate` | float | 0.002 | DQN learning rate | 0.0015 |
| `batch_size` | int | 256 | Training batch size | 32 |
| `gamma` | float | 0.995 | Discount factor | 0.995 |
| `epsilon_start` | float | 0.8 | Initial exploration rate | 0.85 |
| `epsilon_end` | float | 0.01 | Final exploration rate | 0.02 |
| `epsilon_decay` | float | 0.99 | Epsilon decay per step | 0.992 |
| `memory_size` | int | 50000 | DQN replay buffer cap (per-buffer). Was historically set to 1,000,000,000 (effectively unlimited) — that caused unbounded RAM growth and periodic OOM-driven simulator resets. 50,000 is generous for DQN (typical 10K–100K) and bounds the buffer to ~250MB at ~5KB/experience. | 50000 |
| `update_frequency` | int | 1 | Steps between updates | 1 |
| `language_reward_scaling` | float | 0.4 | Language reward weight | 0.4 |

**⚠️ Genesis Warning:** With 5 organisms, experience accumulates slowly. If `batch_size` > total experiences, training never triggers. Rule: `batch_size` ≤ `population × 10` for first training step.

**⚠️ Memory Warning — `memory_size`:** Setting this to a very large value (`>1,000,000`) effectively makes the replay buffer unbounded. Combined with checkpointing's `include_experience_buffer: true`, this is the primary cause of long-run RAM exhaustion (HF Space at 95.7%, local at 86.6%). If you see periodic generation resets (e.g., gen climbs to 100-130 then drops to 50-90 every 30-60 min), this is almost certainly the cause. Cap at 10K-100K and disable `include_experience_buffer` in checkpoints.

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

## `self_perception`

Reward shaping for attractor landscape features (state features 26-28: oscillation_entropy, coherence_frequency, attractor_proximity).

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Enable self-perception rewards |
| `oscillation_entropy_threshold` | float | 0.7 | Entropy threshold for chaos detection |
| `oscillation_chaos_penalty` | float | -0.1 | Penalty for chaotic oscillations |
| `coherence_frequency_threshold` | float | 0.6 | Coherence threshold for trap detection |
| `coherence_trap_penalty` | float | -0.15 | Penalty for coherence traps |
| `proximity_near_threshold` | float | 0.3 | Near-attractor proximity threshold |
| `proximity_near_bonus` | float | 0.05 | Bonus for being near attractor |
| `proximity_medium_threshold` | float | 0.6 | Medium proximity threshold |
| `proximity_medium_bonus` | float | 0.02 | Bonus for medium proximity |

---

## `semantic_convergence`

Unifies 6 semantic systems for word embedding differentiation. Enables words used by differently-tuned organisms to occupy different regions of embedding space.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Master toggle for semantic convergence |
| `use_learned_embeddings` | bool | true | Use nn.Embedding for learned word representations |
| `embedding_dim` | int | 64 | Dimension for learned embeddings (matches OrganismBrain.fc2) |
| `organism_embedding_alpha` | float | 0.15 | EMA blending factor (0.1 = 90% keep, 10% new from organism) |
| `concept_system_alpha` | float | 0.1 | Alpha for ConceptSystem axiom embeddings |
| `knowledge_web_influence_interval` | int | 10 | Generations between KnowledgeWeb semantic influence passes |
| `phenotype_to_vocabulary` | bool | true | Auto-register phenotype names ("social_thrivers") as vocabulary |

**Data Flow:**
1. `organism.brain.fc2` (64-dim) → extracted via `get_language_embedding()`
2. → `ContextMemory.update_word_embedding_from_organism()` (EMA blend)
3. → `word_embedding` collective pool influences all organisms' `generate_tokens()`

**Related Systems:** See `CRA_CAPABILITIES.md` Semantic Convergence section for CRA control commands.

---

## `simulation`

Global runtime settings.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `log_level` | string | "INFO" | Logging verbosity |
| `max_runtime` | float | 0.0 | Seconds before auto-stop; `0` = no app-level runtime stop |
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
- Reduce `neural.training.memory_size` to 10000–50000 (default 50000; legacy configs may have 1,000,000,000 which is unbounded — fix that first)
- Set `neural.checkpointing.include_experience_buffer` to `false` (saves both checkpoint disk and the memory spike during checkpoint serialization)
- Set `neural.checkpointing.compression` to `true` (gzip the .pt files)
- Lower `neural.checkpointing.max_checkpoints` to 3–5 (default 5; was 10)
- Lower `network.max_organisms` (300)
- Enable `ray.memory_management.cleanup_on_organism_death`

**Symptom:** generation counter climbs to 100–130 then resets to 50–90 every 30–60 minutes, RAM at 86–95%. **Root cause:** unbounded replay buffer + `include_experience_buffer: true` in checkpoints. **Fix:** cap `memory_size` at 50000, set `include_experience_buffer: false`.

### Performance Issues
- Set `rendering.render_quality` to "low"
- Reduce `rendering.frame_rate` (10)
- Disable `neural.optimization.use_compile`
- Increase `ray.parallelization_threshold` (200)

---

## Hardware Profile & Autodetection

Butterfly System automatically detects hardware capabilities and optimizes configuration at runtime. The `hardware_profile` key can be set to `beast`, `workstation`, `standard`, `laptop`, `potato`, or `cpu_only` to override autodetection, but leaving it `null` or unset enables full dynamic optimization.

- **Autodetects:** GPU (model, VRAM, CUDA), CPU (cores, model), RAM, disk, network
- **Dynamic scaling:** Population size, batch size, memory, and device settings are clamped to hardware limits
- **Envelope:** HardwareGovernor applies safe limits and stores metadata in config for CRA awareness
- **Manual override:** Set `hardware_profile` in config to force a profile tier
- **Best practice:** Let autodetect handle scaling for cloud/local/multi-machine setups

See `reality_simulator/hardware_governor.py` for implementation details.

---

## Checkpointing & Persistence (Planned)

**CURRENT STATUS**: Partially implemented. Neural training state is NOT automatically persisted.

### What IS Currently Persisted
| Data | Location | Status |
|------|----------|--------|
| Highlander Champions | `highlander_capsules/` | ✅ Working |
| Config Rollback | In-memory (10 snapshots) | ✅ Working (lost on restart) |
| Event Logs | `data/logs/*.log` | ✅ Working |
| Frame State | `data/shared_state.json` | ✅ Working |
| Concept System | Via `trainer.save_concept_system()` | ✅ Manual |

### What is NOT Persisted (Training Lost on Restart)
| Data | Impact | Priority |
|------|--------|----------|
| Neural Brains | Organisms restart with random/inherited weights | 🔴 Critical |
| Experience Buffer | Must recollect all training experiences | 🔴 Critical |
| Optimizer States | Adam momentum/velocity reset | 🟡 High |
| VP History | Stabilization history lost | 🟡 Medium |
| Training Metrics | Loss/epsilon history lost | 🟢 Low |

### Planned Configuration

```json
{
  "checkpointing": {
    "enabled": true,
    "auto_save_interval_generations": 100,
    "auto_save_interval_minutes": 30,
    "max_checkpoints": 5,
    "checkpoint_dir": "data/neural_checkpoints",
    "include_experience_buffer": false,
    "include_optimizer_states": true,
    "compression": true,
    "auto_resume": true
  }
}
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Master toggle for auto-checkpointing |
| `auto_save_interval_generations` | int | 100 | Save checkpoint every N generations |
| `auto_save_interval_minutes` | int | 30 | Save checkpoint every N minutes |
| `max_checkpoints` | int | 5 | Maximum checkpoints to retain (older deleted). Was 10 — lowered to 5 because each checkpoint is heavy. |
| `checkpoint_dir` | string | "data/neural_checkpoints" | Directory for checkpoint storage |
| `include_experience_buffer` | bool | false | **Default flipped to `false`** — saving the experience replay buffer with each checkpoint was the second-largest contributor to memory pressure (the first being the unbounded `memory_size`). Disable unless you have a specific reason to persist replay state. |
| `include_optimizer_states` | bool | true | Save optimizer momentum/velocity |
| `compression` | bool | true | Compress .pt files to save space |
| `auto_resume` | bool | true | Load latest checkpoint on startup |

### Checkpoint Directory Structure

```
data/neural_checkpoints/
├── checkpoint_20251206_143022/
│   ├── neural_brains.pt         # All organism neural weights
│   ├── experience_buffer.pt     # Experience replay buffer
│   ├── optimizer_states.pt      # Optimizer states
│   ├── concept_system.pt        # Concept tracker state
│   └── metadata.json            # Generation, timestamp, metrics
└── latest -> checkpoint_20251206_143022/
```

### Best Practices
1. **Enable checkpointing before long training runs** - Hours of training can be lost
2. **Set reasonable intervals** - 50-100 generations or 15-30 minutes
3. **Monitor disk space** - Each checkpoint can be 10-100MB
4. **Test recovery** - Verify checkpoints actually load correctly
5. **Archive before experiments** - Manually checkpoint before config changes

### Related Systems
- `OrganismCapsuleManager` - Saves individual champion organisms (Highlander mode)
- `ConfigManager` - 10-snapshot rollback for config (in-memory, lost on restart)
- `NeuralTrainer.save_concept_system()` - Manual concept system persistence

---

## Quick Reference: Genesis Protocol (Boom/Bust)

### Starting from 5 Progenitors

```json
{
  "highlander": {
    "population_size": 5,
    "min_population": 3,
    "max_population": 800,
    "survival_threshold": 0.25,
    "competition_intensity": 0.15,
    "germination_rate": 0.8,
    "chaos_factor": 0.10
  },
  "evolution": {
    "population_size": 5,
    "mutation_rate": { "initial": 0.08 },
    "diversity_guard": {
      "hash_similarity_threshold": 0.75,
      "penalty": 0.12
    }
  },
  "neural.training": {
    "batch_size": 32,
    "memory_size": 50000,
    "epsilon_decay": 0.992
  },
  "network": {
    "resource_pool": 1500
  }
}
```

### Phase Controls

| Phase | Key Parameters |
|-------|----------------|
| **BOOM** | ↑ `germination_rate`, ↓ `survival_threshold`, ↓ `competition_intensity` |
| **BUST** | ↑ `competition_intensity`, ↑ `survival_threshold`, `predation_enabled: true` |
| **RECOVERY** | `min_population` floor triggers emergency germination |

### Extinction Prevention

| Risk | Mitigation |
|------|------------|
| Mass culling | Keep `survival_threshold` ≤ 0.3 for small pops |
| Battle extinction | Keep `competition_intensity` ≤ 0.2 |
| Genetic monoculture | Enforce `diversity_guard` with low threshold |
| Training starvation | Use `batch_size` ≤ population × 2 |
| Resource collapse | Set `resource_pool` ≥ 50 × population |

### Runaway Growth Prevention

| Risk | Mitigation |
|------|------------|
| Population explosion | Enforce `max_population` ceiling |
| Immortal dynasties | Enable `betrayal_chance` > 0.02 |
| Alliance domination | Limit `max_alliance_size` |

---

## System Interaction Map

```
┌─────────────────────────────────────────────────────────────────┐
│                     UNIFIED_ENTRY.PY                            │
│                    (Main orchestrator)                          │
└─────────────────────────────┬───────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   HIGHLANDER    │  │  GERMINATION    │  │    ALLIANCE     │
│   PROTOCOL      │◄─┤     POOL        │◄─┤    WARFARE      │
│                 │  │                 │  │                 │
│ • run_round()   │  │ • collect_essence│ │ • propose_war() │
│ • _run_culling()│  │ • prepare_germ..│  │ • vote_proposal()│
│ • _run_battle() │  │ • _apply_chimera│  │ • resolve_war() │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    NEURAL_ORGANISM                              │
│                                                                 │
│  • brain (OrganismBrain)      • experience_buffer               │
│  • atomic_language            • magnetism states                │
│  • alliance_id                • illumination_level              │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  BATTLE_ARENA   │  │ NEURAL_TRAINER  │  │ HEALTH_MONITOR  │
│                 │  │                 │  │                 │
│ • resolve_battle│  │ • train_step()  │  │ • compute_health│
│ • combat_stats  │  │ • batch_sample()│  │ • emit_alerts() │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### Germination Strategies

| Strategy | Weight | Description |
|----------|--------|-------------|
| `TWO_PARENT_BLEND` | 25% | Two-parent trait combination |
| `CHIMERA_MAGNETISM` | 40% | Multi-parent weighted blending with magnetism inheritance |
| `NOVA` | 18% | Completely random new organism |
| `ADAPTIVE_CHALLENGER` | 17% | Population-fitness-calibrated challengers |

### Inheritance Chain

When a new organism is born:
1. **Neural template**: Brain weights inherited/blended from parents
2. **Concept seed**: Vocabulary and concepts passed down
3. **Magnetism template**: Attractor landscape states (healed/trapped phenotype)
4. **Association template**: Knowledge web relationships
5. **Trait template**: Behavioral tendencies

---

