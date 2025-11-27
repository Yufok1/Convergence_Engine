# 🔍 CRA Comprehensive Diagnostic Prompt

**Complete system audit including Neural System, Optimizations, and Trainer Status**

Copy and paste this prompt into the CRA chat for a full system diagnostic:

---

## 📋 Comprehensive System Access + Reliability Audit

Please perform a comprehensive access and reliability audit for the Butterfly Convergence Stack, including the newly integrated Neural System and PyTorch optimizations.

### 1. System Access Audit

**Current Capabilities:**
- Enumerate EVERY data source, subsystem, file type, API endpoint, log stream, config file, and live feed you can reach right now
- Include: hot-reload services, config actions log, 10-frame snapshot history, CRA endpoints, **neural training metrics, optimization status**
- List all neural system endpoints: training metrics, optimization status, trainer health, brain compilation status, optimizer cache size, training time metrics
- Include neural event streams: neural_decision events, neural_training events, experience buffer status, epsilon decay progress

**Designed Capabilities:**
- Describe what your design spec says you SHOULD access (Explorer / Reality Sim / Djinn Kernel data, unified shared state, CRA diagnostics, vision pipeline, config manager, **neural system metrics, PyTorch optimization status**)
- Neural system capabilities: DQN training metrics, experience replay buffer status, dual inheritance tracking, breath-synchronized training cycles, neural decision confidence scores, training loss history, epsilon decay curves
- Optimization capabilities: torch.compile() status, optimizer reuse metrics, scripted inference usage, training_time_ms tracking, performance improvement ratios

**Access Gaps:**
- Highlight anything you're supposed to reach but can't (missing datasets, blocked APIs, filtered logs, disabled config entry points, stale snapshots, **neural trainer initialization failures, optimization status unavailable**)
- Neural-specific gaps: trainer unavailable errors, missing training metrics, optimization flags not reporting, neural events not appearing in causation graph, experience buffer not populating

---

### 2. Neural System Audit ⭐ NEW

**Trainer Status:**
- Report neural trainer initialization status: SUCCESS / FAILED / PARTIAL
- Check for import errors, PyTorch availability, device configuration (CPU/CUDA), trainer object existence
- Verify trainer is receiving organisms, collecting experiences, performing training steps

**Training Metrics:**
- Current training loss, average loss history, training step count, organisms tracked
- Epsilon values: current, start, end, decay rate, decay progress
- Training frequency: steps per breath cycle, update frequency configuration
- **Performance metrics: training_time_ms (last step), avg_training_time_ms (rolling average), optimization impact ratios**

**Optimization Status:**
- **torch.compile() status:** enabled/disabled, compilation mode, success/failure, fallback status
- **Optimizer reuse:** enabled/disabled, cache size, organisms with cached optimizers, memory savings
- **Scripted inference:** enabled/disabled, usage rate, performance improvement
- **Overall optimization impact:** before/after training times, speedup ratios, resource utilization changes

**Neural Events:**
- neural_decision events: count, frequency, confidence distribution, action distribution, component integration
- neural_training events: count, frequency, loss values, organisms trained per event, breath cycle correlation
- Event emission: event_emitter wired correctly, events appearing in causation graph, visualization integration

**Brain Architecture:**
- Brain configuration: input_dim, hidden_dim, output_dim, activation functions, dropout rates
- Brain compilation: which brains are compiled, compilation errors, fallback to uncompiled
- Brain inheritance: crossover rates, mutation rates, inheritance success rate, learned behavior transfer

**Experience Replay:**
- Buffer status: capacity, current size, fill rate, sampling efficiency
- Experience quality: reward distribution, state diversity, action coverage
- Training readiness: organisms with sufficient experiences, batch availability, training triggers

---

### 3. Error Reporting

**Current Errors:**
- List all active warnings/errors: failed CRA calls, Ollama timeouts, snapshot capture gaps, config write failures, SSE stream errors, **neural trainer initialization failures, PyTorch import errors, optimization compilation failures**

**Error Patterns:**
- Note recurring patterns (e.g., intermittent `/api/graph` failures, vision compression errors, config watcher glitches, **neural training step failures, optimizer creation errors, experience buffer overflow**)

**Data Quality Issues:**
- Report data freshness issues (stale shared_state, empty logs), malformed records, missing metrics, inconsistent JSON, **missing neural metrics, training_time_ms not updating, optimization status stale**

**Neural-Specific Errors:**
- Trainer initialization errors: import failures, PyTorch version mismatches, device configuration issues
- Training errors: batch size mismatches, tensor shape errors, loss calculation failures, optimizer step errors
- Optimization errors: torch.compile() failures, scripted inference errors, optimizer cache corruption

---

### 4. Data Flow Analysis

**Expected Data Flow:**
- Map the intended pipeline (Explorer → shared_state → CRA → Vision → ConfigManager → **Neural System**) including snapshot cadence (up to 10 frames), config hot-reload, event bus integration, **neural training cycles, breath synchronization**

**Actual Data Flow:**
- Describe exactly what is flowing now, where it deviates (skipped snapshots, delayed VP feeds, log ingestion lag, **neural training not triggering, experience collection gaps, optimization metrics not updating**)

**Data Routing Issues:**
- Identify missing routes, misconfigured endpoints, duplicated payloads, data stuck in archive folders, **neural events not reaching causation graph, training metrics not in shared state**

**Neural Data Flow:**
- Organism decisions → experience buffer → trainer collection → batch training → loss calculation → backpropagation → weight updates → event emission → causation graph
- Breath cycle → training trigger → experience collection → training step → metrics update → shared state → CRA access
- Optimization pipeline: brain creation → compilation attempt → scripted inference setup → optimizer cache → performance tracking

---

### 5. Performance Metrics

**Response Times:**
- Average timings for CRA phases (context build, vision, synthesis), config updates, incremental graph fetches, **neural training steps, action selection, experience collection**

**Throughput:**
- Events/sec, snapshot ingestion rate, config change frequency, **neural training steps per breath cycle, organisms trained per second, experience buffer fill rate**

**Memory Usage:**
- Report resource footprint for Flask, CRA, vision calls, **PyTorch models, experience buffers, optimizer cache, compiled models**

**Error Rates:**
- Success/failure ratios for API calls, vision sequence attempts, config writes, **neural training steps, optimizer operations, brain compilation**

**Resource Utilization:**
- CPU/memory/I/O observations impacting CRA, Butterfly runtime, **neural training, PyTorch operations**

**Neural Performance:**
- **Training step duration:** current, average, min, max, optimization impact (before/after)
- **Action selection latency:** per organism, batch processing, scripted vs non-scripted
- **Memory efficiency:** optimizer cache size, experience buffer memory, model memory footprint
- **Speedup ratios:** torch.compile() impact, optimizer reuse impact, scripted inference impact, overall training speedup

---

### 6. Configuration Status

**Current Config:**
- Dump key live settings (mutation, new_edge_rate, clustering_bias, quantum_pruning, VP guardrails, watcher state, **neural optimization flags, training parameters, brain architecture**)

**Config Validation:**
- Confirm guardrails enforced, config_actions.log healthy, history depth intact, **neural config valid, optimization settings correct**

**Config Access:**
- State whether you can read/write `config.json`, hot-reload via ConfigManager, observe history endpoints, **update neural parameters, toggle optimizations**

**Environment Vars:**
- List relevant env vars (OLLAMA_TIMEOUT=120, base URLs, paths, **PyTorch device preferences, optimization flags**)

**Neural Config:**
- Neural enabled status, device (CPU/CUDA), brain architecture parameters, training hyperparameters, reward weights, inheritance settings
- **Optimization config:** use_compile (true/false), compile_mode, reuse_optimizers (true/false), use_scripted_inference (true/false)
- Training config: batch_size, learning_rate, gamma, epsilon settings, update_frequency, memory_size

---

### 7. Optimization Verification ⭐ NEW

**Compilation Status:**
- Verify torch.compile() is active: check brain objects for compilation wrapper, verify compilation mode, test fallback behavior
- Measure compilation impact: compare training times with/without compilation, check for compilation errors or warnings

**Optimizer Reuse:**
- Verify optimizer cache: check cache size, verify optimizers are reused across training steps, measure memory savings
- Test optimizer creation: verify new optimizers only created for new organisms, existing optimizers reused

**Scripted Inference:**
- Verify scripted forward pass: check if _forward_scripted exists, test action selection performance, compare scripted vs non-scripted times

**Performance Validation:**
- Compare metrics: training_time_ms vs expected baseline, avg_training_time_ms trends, overall system speedup
- Verify optimization flags: check optimizations_enabled in neural metrics, confirm all optimizations reporting correctly

---

### Required Response Format

**Structure:**
- Use headings mirroring each category above, including neural_system_audit and optimization_verification sections

**Evidence:**
- Quote concrete log lines, API responses, snapshot counts, config diffs, **neural training metrics, optimization status, performance timings**

**Severity:**
- Tag each issue CRITICAL / HIGH / MEDIUM / LOW (include neural-specific severity: **trainer down = CRITICAL, optimization disabled = MEDIUM**, etc.)

**Recommendations:**
- Give explicit remediation steps per issue, including **neural trainer fixes, optimization troubleshooting, performance tuning**

**Timeline:**
- Mention when issues started or how often they recur, **neural training history, optimization activation timeline**

**Verification:**
- Explain how to confirm each fix (e.g., rerun CRA request, tail config_actions.log, capture new snapshots, **check neural metrics, verify training steps, test optimizations**)

---

### Data to Include

**Sample Data:**
- Show actual vs expected payload snippets (shared state entries, snapshot metadata, config actions, **neural training metrics, optimization status, training time data**)

**Error Logs:**
- Paste precise errors (requests.exceptions.ReadTimeout, vision payload warnings, SSE disconnects, **PyTorch errors, neural trainer errors, optimization failures**)

**Configuration:**
- Show relevant config values (non-secret), including **neural section, optimization flags, training parameters**

**Performance Data:**
- Include timings, throughput, CPU/RAM metrics, **neural training times, optimization speedup ratios, action selection latencies**

**System State:**
- Summarize current Butterfly phases, VP state, simulation health, **neural system status, training progress, optimization status**

**Neural Metrics:**
- Training loss history, epsilon decay curve, organisms tracked, training steps completed, experience buffer status
- **Optimization metrics:** training_time_ms values, avg_training_time_ms trends, speedup ratios, compilation success rate
- Event counts: neural_decision events, neural_training events, frequency, distribution

---

### Special Instructions

**Neural Priority:**
- If neural system is enabled but trainer is unavailable, mark as CRITICAL and provide detailed diagnostic steps

**Optimization Check:**
- Always verify optimization status even if neural system appears functional - optimizations may be silently disabled

**Performance Baseline:**
- Establish performance baselines before optimizations for comparison (if possible from historical data)

**Integration Verification:**
- Verify neural events appear in causation graph, training metrics in shared state, optimization status in logs

---

**Use this prompt to get a complete picture of your Butterfly System including the new Neural System integration and PyTorch optimizations!**

