# Configuration Reference – Butterfly System

This document mirrors `config.json` so you can keep the file itself machine-valid (no inline comments) while still knowing what each knob does. Open `config.json` side-by-side with this reference and use your editor's split view + search (e.g. `Ctrl/Cmd+P → >View: Toggle Split Editor`) to jump between a key and its description.

> **Editing tip:** Because the config is pure JSON, keep comments out of the file. Instead, jot notes in this guide or create git commit messages that highlight why a tweak was made.

---

## Top-Level Sections

### `agency`
- `confidence_threshold` – Minimum statistical confidence before the agent acts autonomously.
- `decision_precision` – Decimal precision for decision comparisons (smaller = more sensitive).
- `initial_mode` – Startup autonomy mode (`manual_only`, `assisted`, etc.).
- `learning_rate_resolution` – Step size when tuning adaptive learning rates.
- `performance_tracking_precision` – Decimal precision for KPI logging.

### `causation_detection`
Controls the real-time causation explorer.
- `correlation_threshold` – Minimum Pearson/Spearman correlation before an edge is drawn.
- `direct_causation_time_window` / `phase_transition_time_window` – How far back (in minutes) the system looks for direct or phase-transition events.
- `enable_*` toggles – Turn on/off specific causal domains (language, ML, neural, phase, etc.).
- `recent_events_window` – Number of recent events kept in memory.
- `thresholds.*` – Collapse/alert thresholds per metric (clustering, modularity, organism count, VP bands, etc.).

### `evolution`
- `adaptation_sensitivity` – Responsiveness of adaptation heuristics to environment changes.
- `diversity_guard.*` – Anti-clone guardrails (frequency hashing, penalties, enable flag).
- `fitness_precision` – Decimal precision for fitness comparisons.
- `genotype_length` – Length of the binary genome per organism.
- `max_generations` – Hard stop for evolution runs.
- `mutation_rate.*` – Initial mutation rate and tuning precision.
- `population_size` – Base population per generation.

### `feedback`
Closed-loop controllers for mutation/new-edge tuning.
- `interval_frames` – How frequently (in frames) feedback checks run.
- `knobs.*` – Each knob has `initial`, `min`, `max`, `step` for the adaptive sliders.
- `hysteresis_checks` – Number of confirmations before a change is accepted.
- `rate_limit_frames` – Cool-down between adjustments.

### `health_monitor`
- `enabled` / thresholds – Automatic health classification boundaries (`critical`, `warning`, `healthy`).
- `history_size` – Samples retained for moving averages.
- `weight_*` – Contribution of adaptability, coherence, diversity, lawfulness, sustainability to health.

### `highlander`
Tournament settings.
- `enabled` – Enables Highlander Protocol.
- `competition_intensity` / `chaos_factor` – Difficulty parameters.
- `population_size`, `max_population`, `min_population` – Arena sizing.
- `extreme_mode.*` – Overrides when EXTREME difficulty is selected.
- `germination_rate` – Probability that stored capsules respawn.
- `max_capsules`, `max_genetic_samples` – Vault capacities.
- `predation_enabled`, `rounds_per_cycle`, `survival_threshold` – Combat flow.

### `lattice`
Micro lattice simulation constants.
- `entropy_sensitivity` – Noise level that triggers entropy adjustments.
- `interaction_precision` – Decimal precision for lattice interactions.
- `particles` – Number of lattice particles tracked.
- `prune_threshold` – Minimum weight before particle links are removed.
- `stability_tolerance` – Acceptable deviation before rebalancing.

### `logging`
- `shared_state_dump_interval` – Seconds between shared-state snapshots.

### `meta_cognitive`
Self-tuning brain.
- `self_tuning.enabled/mode` – Whether autonomous tuning runs and at what authority (`autonomous`, `assist`).
- `min_confidence_threshold` – Confidence needed before a tuner update.
- `performance_targets` – Goals the tuner tries to hit (max anomaly ratio, min cluster diversity, etc.).
- `safe_parameters` – Whitelist of config paths the tuner is allowed to modify.
- `tuning_interval_frames` – How often (in frames) tuning cycles fire.

### `network`
Graph limits for the organism interaction network.
- `connection_strength_resolution`, `resource_flow_precision`, `stability_precision` – Decimal precision knobs.
- `max_connections`, `max_organisms` – Hard caps.
- `resource_pool` – Total shared resources available.

### `neural`
Brain + language system configuration.
- `device` – `cuda`, `cpu`, etc.
- `brain.*` – Core DQN architecture (dims, dropout, activation, vocab size for language head).
- `concept_system.*` – Concept lattice training hyperparameters.
- `inheritance.*` – Crossover/mutation settings when brains reproduce.
- `initialization.*` – Determinism/seed controls.
- `language_model.*` – Attention size, curriculum gating, knowledge-web, relationship learning, sequence window, teacher model, training weights, vocab.
- `optimization.*` – PyTorch compile/script flags.
- `rewards.*` – Reward shaping values.
- `training.*` – Batch size, epsilon schedule, gamma, learning rate, replay memory size, update cadence.
- `vp_aware_planning.*` – Adds VP-driven boosts to planning heuristics.

### `quantum`
Quantum subsystem heuristics.
- `entanglement_sensitivity`, `probability_precision`, `superposition_tolerance` – Numerical tolerances.
- `fitness_weights` – Contribution of entanglement/entropy/measurements/superposition to quantum fitness.
- `initial_states` – Count of quantum seeds.
- `performance_thresholds.*` – Boundaries that determine when to prune or keep a quantum state.
- `prune_check_interval` – Frames between quantum pruning sweeps.

### `ray`
Distributed execution options (if Ray is enabled).
- `enabled` – Toggle the Ray backend.
- `actor_pool_size`, `batch_inference_size`, `training_threshold` – Controls how many actors are spun up and when.
- `num_cpus`, `num_gpus`, `object_store_memory` – Resource reservations.
- `memory_management.*` – Automatic cleanup policies.
- `state_synchronization.*` – Consistency model and snapshot cadence between Ray workers and the core sim.
- `parallelization_threshold` – Minimum organism count before Ray is used.
- `logging_level`, `fallback_on_error` – Diagnostics and safety behavior.

### `rendering`
- `enable_visualizations`, `text_interface` – Toggle UI layers.
- `mode` – Camera mode (`god`, `organism`, etc.).
- `resolution`, `frame_rate`, `render_quality` – Output settings.
- `performance_monitoring` – Show FPS and perf overlays.
- `visualization_update_precision` – Decimal precision for metric overlays.

### `scikit`
Classical ML analytics.
- `enabled` – Master switch for the scikit toolset.
- `anomaly_detection.*` – Isolation Forest / contamination levels.
- `clustering.*` – HDBSCAN parameters.
- `concept_tracking.*` – Lifespan thresholds for discovered concepts.
- `dimensionality_reduction.*` – PCA/t-SNE style reductions (currently PCA).

### `simulation`
Global runtime settings.
- `log_level` – Logging verbosity for core loops.
- `max_runtime` – Seconds before the sim auto-stops.
- `measurement_precision` – Decimal precision for diagnostic prints.
- `performance_sampling_rate` – How often perf samples are recorded.
- `save_interval` – Seconds between state saves.
- `target_fps` – Desired simulation frames per second.
- `time_resolution_ms` – Base time slice for the scheduler.

### `vp_monitoring`
Vitality/Pleasure dashboards.
- `adaptive_response.*` – Threshold and streak length for elevated VP states.
- `component_weights` – Contribution of each VP component to the composite.
- `adaptive_thresholds_enabled`, `component_decomposition_enabled`, `diagnostics_enabled` – Feature toggles.
- `stabilization.*` – Moving-average smoothing of VP metrics.

---

## Working With the Reference
1. Split your editor: `config.json` on the left, this file on the right.
2. Use find (`Ctrl/Cmd+F`) to jump to the section name.
3. Adjust values in `config.json` and keep notes here if necessary (e.g., "2025‑12‑02: lowered `mutation_rate.initial` to 0.03 during GPU tests").
4. Commit both changes together so others have the rationale alongside the config tweak.

If you need deeper internals (e.g., what `meta_cognitive.self_tuning.safe_parameters` actually touch), cross-reference the specialized docs in `docs/` like `NEURAL_SYSTEM_README.md`, `SELF_TUNING_GUIDE.md`, or `CRA_SELF_TUNING_GUIDE.md`.
