# Alliance-Driven Causation Illumination - Implementation Checklist

**Target Completion:** Iterative  
**Estimated Effort:** 4-6 hours development + 2 hours testing  
**Owner:** User (with optional consultation)

---

## Phase 1: AllianceWarfareSystem Enhancement (1.5 hours)

### Task 1.1: Add sync_alliance_state() Method
- [ ] Location: `alliance_warfare.py`, in `AllianceWarfareSystem` class
- [ ] **Acceptance Criteria:**
  - Method accepts alliance_id and alliance_data dict
  - Creates/updates internal alliance record with member list
  - Tracks stability_rounds history
  - **No errors** when called with incomplete data
  - **Non-blocking** - returns immediately
- [ ] **Testing locally:**
  ```python
  aw = AllianceWarfareSystem()
  aw.sync_alliance_state("alliance_test", {
      'members': ['org_1', 'org_2'],
      'formation_round': 0,
      'stability_rounds': 1
  })
  assert 'alliance_test' in aw.alliances
  print("✅ Sync works")
  ```

### Task 1.2: Add check_and_grant_illumination() Method
- [ ] Location: `alliance_warfare.py`, in `AllianceWarfareSystem` class
- [ ] **Acceptance Criteria:**
  - Returns `True` if illumination was granted, `False` otherwise
  - Guards against re-granting (checks current status)
  - **Stability check:** member_count >= 3 AND stability_rounds >= threshold
  - **Threshold configurable:** reads from config, default = 5
  - **Returns False for already-illuminated alliances**
- [ ] **Testing locally:**
  ```python
  aw = AllianceWarfareSystem(config={'illumination_stability_threshold': 2})
  aw.sync_alliance_state("test", {
      'members': ['a', 'b', 'c'],
      'formation_round': 0,
      'stability_rounds': 2
  })
  result = aw.check_and_grant_illumination("test")
  assert result == True
  # Call again - should be False
  result2 = aw.check_and_grant_illumination("test")
  assert result2 == False
  print("✅ Illumination gating works")
  ```

### Task 1.3: Add unlock_causation_for_alliance() Method
- [ ] Location: `alliance_warfare.py`, in `AllianceWarfareSystem` class
- [ ] **Acceptance Criteria:**
  - Sets `_illumination_level` on each organism to the illumination_tier
  - **Only upgrades** - doesn't downgrade if organism has higher level
  - **Logs with emoji:** `logger.info(f"🔮 [{alliance_id}] UNLOCKED: {tier}")`
  - Emits event via `self.event_emitter` if available
  - **Silent success** if no organisms found (no exceptions)
- [ ] **Testing locally:**
  ```python
  events = []
  aw = AllianceWarfareSystem(event_emitter=lambda e: events.append(e))
  aw.unlock_causation_for_alliance("test", "basic")
  assert len(events) == 1
  assert events[0]['event_type'] == 'illumination_unlocked'
  print("✅ Unlock and event emission works")
  ```

### Task 1.4: Add _get_organism() Helper
- [ ] Location: `alliance_warfare.py`, in `AllianceWarfareSystem` class
- [ ] **Acceptance Criteria:**
  - Looks up organism from `self.highlander_protocol.get_organism(organism_id)`
  - Returns `None` if not found (doesn't throw)
  - Caches result to avoid repeated lookups (optional optimization)

### Task 1.5: Update config.json
- [ ] Location: `config.json` at root
- [ ] **Acceptance Criteria:**
  - Add section: `"alliance_warfare": { "illumination_stability_threshold": 5 }`
  - Check file is valid JSON after edit
  ```bash
  python -m json.tool config.json > /dev/null && echo "✅ Valid JSON"
  ```

---

## Phase 2: HighlanderProtocol Integration (1.5 hours)

### Task 2.1: Add set_alliance_warfare_system() Method
- [ ] Location: `highlander_protocol.py`, in `HighlanderProtocol` class
- [ ] **Acceptance Criteria:**
  - Stores reference: `self.alliance_warfare = alliance_warfare_system`
  - Logs: `logger.info("[HighlanderProtocol] AllianceWarfareSystem wired")`
  - Handles `None` gracefully (doesn't crash if called with None)

### Task 2.2: Add get_organism() Method
- [ ] Location: `highlander_protocol.py`, in `HighlanderProtocol` class
- [ ] **Acceptance Criteria:**
  - Returns organism by ID from network
  - Searches both dict and list formats (defensive)
  - Returns `None` if not found (doesn't throw)
  - **Fast:** O(1) for dict, O(n) for list (acceptable)

### Task 2.3: Hook _run_cooperation() for sync
- [ ] Location: `highlander_protocol.py`, find `_run_cooperation` method
- [ ] **Acceptance Criteria:**
  - After alliances are formed, iterate and call `sync_alliance_state()`
  - Calculate `stability_rounds = self.generation - formation_round`
  - **Only if** `alliance_warfare` is not None
  - Uses try/except to prevent Highlander from breaking if sync fails
- [ ] **Testing locally:**
  - Run a few rounds, check for log messages
  - Look for "AllianceWarfareSystem wired" in startup
  - Look for sync calls in cooperation logs

### Task 2.4: Hook _absorb_loser() for sync on death
- [ ] Location: `highlander_protocol.py`, find `_absorb_loser` method
- [ ] **Acceptance Criteria:**
  - After organism is removed, notify alliance_warfare
  - Call: `alliance_warfare.sync_alliance_state_on_member_removal(organism_id)`
  - **Only if** `alliance_warfare` is not None
  - Non-blocking

---

## Phase 3: NeuralOrganism Enhancement (1 hour)

### Task 3.1: Add set_system_references() Method
- [ ] Location: `neural_organism.py`, in `NeuralOrganism` class
- [ ] **Acceptance Criteria:**
  - Accepts `alliance_warfare` and `causation_explorer` parameters
  - Stores as `self.alliance_warfare` and `self.causation_explorer`
  - Initializes `_illumination_level = 'none'` if not exists
  - Idempotent (safe to call multiple times)

### Task 3.2: Add get_illumination_level() Method
- [ ] Location: `neural_organism.py`, in `NeuralOrganism` class
- [ ] **Acceptance Criteria:**
  - Returns `_illumination_level` attribute
  - Defaults to `'none'` if not set
  - Returns string: `'none' | 'basic' | 'alliance' | 'advanced'`

### Task 3.3: Add can_access_causation_features() Method
- [ ] Location: `neural_organism.py`, in `NeuralOrganism` class
- [ ] **Acceptance Criteria:**
  - Returns `True` if `_illumination_level != 'none'`
  - Returns `False` otherwise
  - Used for permission gating in decision logic

### Task 3.4: Add get_wisdom_from_causation() Method
- [ ] Location: `neural_organism.py`, in `NeuralOrganism` class
- [ ] **Acceptance Criteria:**
  - Returns empty string if `illumination == 'none'`
  - Queries `causation_explorer.get_events_for_organism()` if illuminated
  - Returns string like: `"🔮 Wisdom: Previous victory vs...; Alliance stability..."`
  - **Non-crashing:** wraps in try/except, returns "" on error
  - **Used in decision-making:** neural logic can call this to get insight

### Task 3.5: Update get_state_features() (Verification)
- [ ] Location: `neural_organism.py`, find `get_state_features` method
- [ ] **Acceptance Criteria:**
  - If `include_illumination=True`, adds `features['illumination_level']`
  - Defensive: checks `hasattr(self, '_illumination_level')` before using
  - Doesn't crash on old organisms without illumination

---

## Phase 4: unified_entry.py Integration (1 hour)

### Task 4.1: Wire AllianceWarfareSystem
- [ ] Location: `unified_entry.py`, in `UnifiedSystem.__init__()`
- [ ] **Acceptance Criteria:**
  - Creates `AllianceWarfareSystem` instance after `highlander_protocol` exists
  - Calls `highlander_protocol.set_alliance_warfare_system(alliance_warfare)`
  - Sets `alliance_warfare.event_emitter = neural_event_emitter`
  - Handles import failure with try/except
  - **Logs success:** `"[UNIFIED] [INTEGRATION] ✅ Alliance Warfare ↔ Causation Illumination"`

### Task 4.2: Wire Organism References
- [ ] Location: `unified_entry.py`, in `UnifiedSystem.__init__()` after 4.1
- [ ] **Acceptance Criteria:**
  - Iterates over `network.organisms` dict/list
  - Calls `organism.set_system_references(alliance_warfare, causation_explorer)`
  - **Only if** methods exist (defensive)
  - Logs: `"[UNIFIED] [ILLUMINATION] ✅ Organisms wired to causation system"`
  - **Non-breaking:** if organisms don't have method, skips silently

### Task 4.3: Wire Event Handlers (Optional)
- [ ] Location: `unified_entry.py`, in event handler setup section
- [ ] **Acceptance Criteria:**
  - Subscribe to `'illumination_unlocked'` event type
  - Handler logs the event with emoji
  - Optionally updates UI/visualization with illumination status

---

## Phase 5: Testing & Validation (2 hours)

### Task 5.1: Unit Tests
- [ ] Create `test_illumination_unlock.py` with tests from doc
- [ ] **Acceptance Criteria:**
  - `test_alliance_stability_threshold()` passes
  - `test_illumination_granted_to_members()` passes
  - `test_causation_explorer_event_emission()` passes
  - Run: `pytest test_illumination_unlock.py -v`

### Task 5.2: Integration Test - 50-Round Simulation
- [ ] Run: `python unified_entry.py --headless` for 50 rounds
- [ ] **Acceptance Criteria:**
  - No crashes
  - Alliances form naturally
  - Check logs for patterns:
    ```
    [HighlanderProtocol] AllianceWarfareSystem wired ✓
    sync_alliance_state called ✓
    check_and_grant_illumination called ✓
    ```

### Task 5.3: Manual Verification - Check Each Success Criterion
Run simulation, pause at round 10+ with alliance, verify:

**Criterion 1: Logs show 🔮 symbol for unlocked alliance**
```bash
grep "🔮" data/logs/system.log
# Expected output:
# 🔮 [alliance_xyz] UNLOCKED: BASIC Causation
```

**Criterion 2: Organism illumination level updated**
```python
# Add to neural decision logging:
logger.debug(f"Organism {org.id} illumination: {org.get_illumination_level()}")
# Check logs for "illumination: basic" entries
```

**Criterion 3: Causation events emitted**
```bash
grep "illumination_unlocked" data/logs/explorer.log
# Expected: ILLUMINATION_UNLOCKED events present
```

**Criterion 4: Decision logs use 🔮 Wisdom**
```bash
grep "Wisdom:" data/logs/*.log
# Expected: "🔮 Wisdom: Previous alliance victory..."
```

### Task 5.4: Performance Check
- [ ] Run simulation for 100+ rounds, monitor:
  - Memory usage (should not grow unbounded)
  - CPU usage during sync (should be <5% of round time)
  - No deadlocks or hangs
- [ ] Check: `Alliance sync time < 1ms per call`

---

## Phase 6: Documentation & Cleanup (30 min)

### Task 6.1: Update Docstrings
- [ ] Verify all new methods have docstrings
- [ ] Include examples in docstrings where helpful
- [ ] Document breaking change in README if exists

### Task 6.2: Code Review Checklist
- [ ] All variables named clearly (not `x`, `y`, `tmp`)
- [ ] No debug print() statements left (use logger instead)
- [ ] All error handling: try/except or validation
- [ ] No circular imports introduced
- [ ] Type hints present on method signatures

### Task 6.3: Final Log Analysis
- [ ] Search for any ERROR or CRITICAL in logs
- [ ] Verify ILLUMINATION_UNLOCKED events map to alliance formation
- [ ] Check that organisms stop using illumination if alliance dissolves

---

## Debugging Tips

### If sync_alliance_state() not called:
1. Check: Is `alliance_warfare` not None?
   ```python
   # Add to _run_cooperation():
   if not self.alliance_warfare:
       logger.warning("alliance_warfare is None - sync skipped")
   ```
2. Check: Is `_run_cooperation()` being called?
   ```python
   # Add at start of _run_cooperation():
   logger.debug("_run_cooperation called")
   ```

### If illumination not granted:
1. Check: Stability threshold met?
   ```python
   # In check_and_grant_illumination():
   logger.debug(f"Alliance {id}: members={member_count}, rounds={stability_rounds}, threshold={threshold}")
   ```
2. Check: Already illuminated?
   ```python
   # Already-illuminated alliances skip
   ```

### If organisms don't have illumination_level:
1. Check: set_system_references() called?
   ```bash
   grep "set_system_references" data/logs/*.log
   ```
2. Check: Organisms are NeuralOrganism type?
   ```python
   # Type verification in set_system_references()
   ```

### If events not emitted to CausationExplorer:
1. Check: event_emitter is not None?
   ```python
   # In unlock_causation_for_alliance():
   if self.event_emitter:
       logger.debug("Emitting event")
   ```
2. Check: CausationExplorer.subscribe() called?
   ```bash
   grep "subscribe" data/logs/*.log
   ```

---

## Success Metrics

After completion, you should be able to:

✅ **Run simulation for 50+ rounds without crashes**

✅ **See "🔮 [AllianceName] UNLOCKED" messages in logs**

✅ **Query organism.get_illumination_level() and get 'basic' or higher**

✅ **See "🔮 Wisdom:" in organism decision reasoning logs**

✅ **CausationExplorer events include 'illumination_unlocked' type**

✅ **Alliance stability tracking shows member count and rounds survived**

✅ **Config accepts illumination_stability_threshold setting**

---

## Questions to Ask Before Starting

1. **Where should logging go?** Recommend `reality_simulator` or `alliance_warfare` logger
2. **Event data structure correct?** Review Task 1.3 event_data dict
3. **Config path correct?** Should config.json be at root or in a config/ folder?
4. **Organism lookup pattern?** Is network.organisms a dict or list in current codebase?
5. **Cascade illumination on death?** Should alliance lose illumination if too many members die?

---

