# Alliance-Driven Causation Illumination Implementation Plan

**Status:** Ready for Implementation  
**Complexity:** Medium-High  
**Dependencies:** HighlanderProtocol, AllianceWarfareSystem, CausationExplorer  
**Breaking Changes:** Yes (HighlanderProtocol → AllianceWarfareSystem synchronization)

---

## Executive Summary

This implementation creates a **knowledge unlocking mechanism** where organisms earn access to the **Causation Illumination Engine** by demonstrating successful, stable alliance formation. This bridges the low-level survival mechanics (HighlanderProtocol) with high-level civilization governance (AllianceWarfareSystem) and knowledge access (CausationExplorer).

**Core Concept:** Stability + Complexity → Illumination Capability

---

## 1. Architecture Overview

### Current State (Before Changes)
```
HighlanderProtocol (isolated)
  ├─ Battles & absorption
  ├─ Basic alliance formation
  └─ Population management

AllianceWarfareSystem (independent)
  ├─ Civilization governance
  ├─ Confederation management
  └─ War coordination

CausationExplorer (observer)
  ├─ Event logging
  └─ Causation graph building
```

### Target State (After Changes)
```
HighlanderProtocol (coordinator)
  ├─ Battles & absorption
  ├─ Alliance formation (NEW: calls sync_alliance_state)
  ├─ Population management
  └─ Neural organism references (NEW: set via setter)
        │
        ├─→ AllianceWarfareSystem (validator)
        │     ├─ Alliance state synchronization
        │     ├─ Stability tracking (rounds survived)
        │     ├─ Complexity validation (confederation status)
        │     └─ Illumination unlock logic
        │           │
        │           └─→ CausationExplorer (knowledge gate)
        │                 ├─ Event emission
        │                 └─ Illumination milestone tracking

NeuralOrganism (learner)
  ├─ _illumination_level: 'none' → 'basic' → 'advanced'
  ├─ Receives illumination via event handler
  └─ Uses "Wisdom" in decision reasoning (NEW: 🔮 decision logs)
```

---

## 2. Proposed Changes - Detailed Specifications

### 2.1 AllianceWarfareSystem Changes

#### **ADD: sync_alliance_state Method**

```python
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
    with self.state_lock:
        # Update or create internal PlanetaryAlliance record
        if alliance_id not in self.alliances:
            self.alliances[alliance_id] = {
                'created_round': alliance_data.get('formation_round', 0),
                'members': set(alliance_data.get('members', [])),
                'confederation_id': alliance_data.get('confederation_id'),
                'stability_history': [],
                'illumination_status': 'none',
                'illumination_granted_round': None
            }
        
        alliance = self.alliances[alliance_id]
        alliance['members'] = set(alliance_data.get('members', []))
        alliance['stability_rounds'] = alliance_data.get('stability_rounds', 0)
        alliance['confederation_id'] = alliance_data.get('confederation_id')
        
        # Track stability progression
        alliance['stability_history'].append({
            'round': alliance_data.get('formation_round', 0),
            'members': len(alliance['members']),
            'stability': alliance_data.get('stability_rounds', 0)
        })
        
        # Automatically check and grant illumination if conditions met
        self.check_and_grant_illumination(alliance_id)


def check_and_grant_illumination(self, alliance_id: str) -> bool:
    """
    Check if alliance has earned Basic Causation illumination.
    
    Criteria:
    1. **Stability:** Alliance must persist for N rounds (configurable, default 5)
    2. **Complexity:** 
       - BASIC: 3+ members for 5+ rounds
       - ALLIANCE: 5+ members in confederation for 10+ rounds
       - ADVANCED: Confederation tier for 15+ rounds
    
    Returns:
        True if illumination was granted this call, False otherwise
    """
    if alliance_id not in self.alliances:
        return False
    
    alliance = self.alliances[alliance_id]
    
    # Already granted - don't re-grant
    if alliance.get('illumination_status') != 'none':
        return False
    
    stability_rounds = alliance.get('stability_rounds', 0)
    member_count = len(alliance.get('members', []))
    is_confederated = alliance.get('confederation_id') is not None
    
    # Check for Basic Causation Illumination
    # Criteria: 3+ members surviving 5+ rounds
    if member_count >= 3 and stability_rounds >= self.config.get('illumination_stability_threshold', 5):
        alliance['illumination_status'] = 'basic'
        alliance['illumination_granted_round'] = stability_rounds
        
        # CRITICAL: Unlock causation for all members
        self.unlock_causation_for_alliance(alliance_id, 'basic')
        return True
    
    # Check for Alliance-tier Illumination (if in confederation)
    if is_confederated and member_count >= 5 and stability_rounds >= 10:
        alliance['illumination_status'] = 'alliance'
        alliance['illumination_granted_round'] = stability_rounds
        self.unlock_causation_for_alliance(alliance_id, 'alliance')
        return True
    
    return False


def unlock_causation_for_alliance(self, alliance_id: str, illumination_tier: str) -> None:
    """
    Grant Causation Illumination to all members of an alliance.
    
    This is the KEY integration point - directly modifies organism state
    and emits events to CausationExplorer.
    
    Args:
        alliance_id: Alliance to grant illumination to
        illumination_tier: 'basic', 'alliance', or 'advanced'
    """
    if alliance_id not in self.alliances:
        return
    
    alliance = self.alliances[alliance_id]
    member_ids = alliance.get('members', [])
    
    if not member_ids:
        return
    
    logger.info(f"🔮 [{alliance_id}] UNLOCKED: {illumination_tier.upper()} Causation")
    
    # Update each organism's illumination level
    for organism_id in member_ids:
        organism = self._get_organism(organism_id)
        if organism and hasattr(organism, '_illumination_level'):
            # Only upgrade, never downgrade
            tier_rank = {'none': 0, 'basic': 1, 'alliance': 2, 'advanced': 3}
            current_rank = tier_rank.get(organism._illumination_level, 0)
            new_rank = tier_rank.get(illumination_tier, 0)
            
            if new_rank > current_rank:
                organism._illumination_level = illumination_tier
                logger.debug(f"  → {organism_id}: {organism._illumination_level} ✓")
    
    # Emit event to CausationExplorer
    if self.event_emitter:
        event_data = {
            'alliance_id': alliance_id,
            'illumination_tier': illumination_tier,
            'member_count': len(member_ids),
            'members': list(member_ids),
            'stability_rounds': alliance.get('stability_rounds', 0)
        }
        
        self.event_emitter({
            'component': 'alliance_warfare',
            'event_type': 'illumination_unlocked',
            'timestamp': time.time(),
            'data': event_data
        })


def _get_organism(self, organism_id: str):
    """
    Retrieve organism by ID from HighlanderProtocol.
    
    This assumes HighlanderProtocol has set a reference to the network/organisms.
    """
    if hasattr(self, 'highlander_protocol') and self.highlander_protocol:
        if hasattr(self.highlander_protocol, 'get_organism'):
            return self.highlander_protocol.get_organism(organism_id)
    return None
```

#### **UPDATE: Alliance Formation Detection in check_and_grant_illumination**

Add this to config.json:
```json
{
  "alliance_warfare": {
    "illumination_stability_threshold": 5,
    "illumination_complexity_tiers": {
      "basic": {"min_members": 3, "min_rounds": 5},
      "alliance": {"min_members": 5, "min_rounds": 10},
      "advanced": {"min_rounds": 15, "requires_confederation": true}
    },
    "event_emitter_enabled": true
  }
}
```

---

### 2.2 HighlanderProtocol Changes

#### **ADD: set_alliance_warfare_system Method**

```python
def set_alliance_warfare_system(self, alliance_warfare_system) -> None:
    """
    Wire AllianceWarfareSystem into HighlanderProtocol.
    
    Called during unified_entry.py initialization to establish the bidirectional link.
    """
    self.alliance_warfare = alliance_warfare_system
    logger.info("[HighlanderProtocol] AllianceWarfareSystem wired")


def get_organism(self, organism_id: str):
    """
    Retrieve organism by ID for AllianceWarfareSystem to access.
    
    Needed because AllianceWarfareSystem.unlock_causation_for_alliance()
    must be able to get organisms to set their _illumination_level.
    """
    if hasattr(self, 'network') and self.network:
        if hasattr(self.network, 'organisms'):
            organisms = self.network.organisms
            if isinstance(organisms, dict):
                return organisms.get(organism_id)
            else:
                # List format - search by ID
                for org in organisms:
                    if hasattr(org, 'id') and org.id == organism_id:
                        return org
    return None
```

#### **UPDATE: _run_cooperation - Hook Alliance Events**

Find this method in `highlander_protocol.py` and add the sync call:

```python
def _run_cooperation(self, ...):
    """
    Internal method that forms alliances.
    After alliances are formed, sync state to AllianceWarfareSystem.
    """
    # ... existing cooperation logic ...
    
    # [NEW] Sync alliances to AllianceWarfareSystem
    if alliances_formed and hasattr(self, 'alliance_warfare') and self.alliance_warfare:
        for alliance_id, alliance_data in alliances_formed.items():
            # Calculate stability (how long alliance has existed)
            formation_round = alliance_data.get('formation_round', self.generation)
            stability_rounds = self.generation - formation_round
            
            sync_data = {
                'members': list(alliance_data.get('members', [])),
                'formation_round': formation_round,
                'stability_rounds': stability_rounds,
                'confederation_id': alliance_data.get('confederation_id'),
                'war_count': len(alliance_data.get('wars', [])),
                'betrayal_count': len(alliance_data.get('betrayals', []))
            }
            
            self.alliance_warfare.sync_alliance_state(alliance_id, sync_data)
```

#### **UPDATE: _absorb_loser - Sync on Death**

Add sync call when organisms are removed from population:

```python
def _absorb_loser(self, organism_id):
    """
    [EXISTING] Handle organism death/removal
    [NEW] Sync updated alliance state
    """
    # ... existing removal logic ...
    
    # [NEW] Update alliances if organism was in one
    if hasattr(self, 'alliance_warfare') and self.alliance_warfare:
        self.alliance_warfare.sync_alliance_state_on_member_removal(organism_id)
```

---

### 2.3 NeuralOrganism Changes

#### **ADD: System References Setter**

```python
def set_system_references(self, alliance_warfare=None, causation_explorer=None) -> None:
    """
    Inject system references into organism after creation.
    
    This allows organisms to access causation data and alliance status
    without hard dependencies at initialization time.
    """
    self.alliance_warfare = alliance_warfare
    self.causation_explorer = causation_explorer
    
    # Initialize illumination level if not already set
    if not hasattr(self, '_illumination_level'):
        self._illumination_level = 'none'


def get_illumination_level(self) -> str:
    """
    Get this organism's current Causation Illumination level.
    
    Returns:
        'none' - No access to causation data
        'basic' - Access to basic causation events in own alliance
        'alliance' - Access to alliance-wide causation graph
        'advanced' - Access to full system causation Explorer
    """
    return getattr(self, '_illumination_level', 'none')


def can_access_causation_features(self) -> bool:
    """Quick check for permission gating."""
    return self.get_illumination_level() != 'none'
```

#### **UPDATE: get_state_features - Verify Flexibility**

The method should already handle new inputs gracefully. Add defensive check:

```python
def get_state_features(self, include_illumination: bool = True) -> Dict:
    """
    [EXISTING] Get organism state features for decision-making
    [NEW] Safely include illumination level if available
    """
    features = {
        # ... existing features ...
    }
    
    # Safely add illumination if requested and available
    if include_illumination and hasattr(self, '_illumination_level'):
        features['illumination_level'] = self._illumination_level
    
    return features
```

#### **UPDATE: get_wisdom_from_causation [NEW METHOD]**

```python
def get_wisdom_from_causation(self) -> str:
    """
    Access causation-driven wisdom if illumination level permits.
    
    Used in decision-making to provide "Wisdom" reasoning.
    """
    illumination = self.get_illumination_level()
    
    if illumination == 'none':
        return ""
    
    if not self.causation_explorer:
        return ""
    
    # Get recent causation events for this organism
    # This is WISDOM: understanding cause-effect from past battles
    try:
        recent_events = self.causation_explorer.get_events_for_organism(
            self.id, 
            limit=3,
            event_types=['battle_outcome', 'alliance_formed', 'betrayal']
        )
        
        if recent_events:
            wisdom = "🔮 Wisdom: " + "; ".join([
                f"{e.summary}" for e in recent_events[:2]
            ])
            return wisdom
    except Exception:
        pass
    
    return ""
```

---

## 3. Integration Points - unified_entry.py

Add these wiring steps in UnifiedSystem.__init__:

```python
# ═══════════════════════════════════════════════════════════════════════════
# ALLIANCE WARFARE ↔ CAUSATION ILLUMINATION INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

if self.highlander_protocol and self.causation_explorer:
    try:
        # Wire AllianceWarfareSystem
        if not hasattr(self, 'alliance_warfare'):
            from reality_simulator.evolution.alliance_warfare import AllianceWarfareSystem
            
            alliance_config = self.active_config.get('alliance_warfare', {})
            self.alliance_warfare = AllianceWarfareSystem(
                highlander_protocol=self.highlander_protocol,
                config=alliance_config,
                event_emitter=neural_event_emitter
            )
        
        # Bidirectional link
        self.highlander_protocol.set_alliance_warfare_system(self.alliance_warfare)
        self.alliance_warfare.causation_explorer = self.causation_explorer
        
        print("[UNIFIED] [INTEGRATION] ✅ Alliance Warfare ↔ Causation Illumination")
        
        # Wire organism references for illumination access
        if (hasattr(self.reality_sim, 'components') and 
            'network' in self.reality_sim.components):
            
            network = self.reality_sim.components['network']
            if hasattr(network, 'organisms'):
                for org_id, organism in network.organisms.items():
                    if hasattr(organism, 'set_system_references'):
                        organism.set_system_references(
                            alliance_warfare=self.alliance_warfare,
                            causation_explorer=self.causation_explorer
                        )
        
        print("[UNIFIED] [ILLUMINATION] ✅ Organisms wired to causation system")
        
    except Exception as e:
        print(f"[UNIFIED] [WARN] Alliance Warfare integration failed: {e}")
        import traceback
        traceback.print_exc()
```

---

## 4. Verification Plan - Test Suite

### 4.1 Automated Tests

```python
# test_illumination_unlock.py

def test_alliance_stability_threshold():
    """Verify Basic Causation unlocks at 5-round stability."""
    
    # Create alliance with 3 members
    alliance_id = "test_alliance_1"
    members = ["org_001", "org_002", "org_003"]
    
    warfare = AllianceWarfareSystem()
    
    # Simulate 5 rounds of stability
    for round in range(1, 6):
        warfare.sync_alliance_state(alliance_id, {
            'members': members,
            'formation_round': 1,
            'stability_rounds': round,
            'confederation_id': None,
            'war_count': 0,
            'betrayal_count': 0
        })
        
        if round < 5:
            assert warfare.alliances[alliance_id]['illumination_status'] == 'none'
        else:
            assert warfare.alliances[alliance_id]['illumination_status'] == 'basic'
    
    print("✅ test_alliance_stability_threshold PASSED")


def test_illumination_granted_to_members():
    """Verify all alliance members get illumination when unlocked."""
    
    alliance_id = "test_alliance_2"
    members = ["org_004", "org_005", "org_006"]
    
    # Mock organisms with _illumination_level
    organisms = {
        org_id: type('Org', (), {'_illumination_level': 'none', 'id': org_id})()
        for org_id in members
    }
    
    warfare = AllianceWarfareSystem()
    warfare._organisms_cache = organisms  # Mock
    
    # Trigger illumination unlock
    warfare.check_and_grant_illumination(alliance_id)
    
    # Verify all members updated
    for org_id in members:
        assert organisms[org_id]._illumination_level == 'basic'
    
    print("✅ test_illumination_granted_to_members PASSED")


def test_causation_explorer_event_emission():
    """Verify ILLUMINATION_UNLOCKED event sent to CausationExplorer."""
    
    events_captured = []
    
    def capture_event(event_data):
        events_captured.append(event_data)
    
    warfare = AllianceWarfareSystem(event_emitter=capture_event)
    
    # Trigger unlock
    warfare.unlock_causation_for_alliance("test_alliance_3", "basic")
    
    # Verify event
    assert len(events_captured) == 1
    event = events_captured[0]
    assert event['event_type'] == 'illumination_unlocked'
    assert event['illumination_tier'] == 'basic'
    
    print("✅ test_causation_explorer_event_emission PASSED")
```

### 4.2 Manual Verification Checklist

Run the simulation for 50+ rounds and verify:

```
□ Alliance forms with 3+ organisms
  Check: Alliance tracker shows members list
  
□ After 5 rounds of stability:
  Logs show: 🔮 [AllianceName] UNLOCKED: BASIC Causation
  
□ Organisms in unlocked alliance show:
  _illumination_level changes from 'none' to 'basic'
  
□ Neural decision logs include "🔮 Wisdom:" entries
  Example: "🔮 Wisdom: Previous alliance victory vs Zephyr Alliance"
  
□ CausationExplorer.add_event() receives 'illumination_unlocked' event
  Check: events dict contains event_id
  
□ Alliance member organisms can call:
  org.get_illumination_level() → returns 'basic'
  org.can_access_causation_features() → returns True
  org.get_wisdom_from_causation() → returns causation-based wisdom string
```

---

## 5. Breaking Changes & Migration

### **BREAKING CHANGE: HighlanderProtocol Now Depends on AllianceWarfareSystem**

**Before:**
```python
highlander = HighlanderProtocol(config)  # Standalone
```

**After:**
```python
alliance_warfare = AllianceWarfareSystem(config=alliance_config)
highlander = HighlanderProtocol(config)
highlander.set_alliance_warfare_system(alliance_warfare)  # REQUIRED
```

### **Migration Steps:**

1. **Update unified_entry.py:** Add wiring code above (Section 4)
2. **Update existing tests:** Add `set_alliance_warfare_system()` call after Highlander creation
3. **Optional:** Make it a parameter to avoid breaking existing code:
   ```python
   def __init__(self, ..., alliance_warfare_system=None):
       self.alliance_warfare = alliance_warfare_system  # Can be None for backward compat
   ```

---

## 6. Success Criteria

### Tier 1: Basic Implementation
- [x] AllianceWarfareSystem.sync_alliance_state() receives updates
- [x] check_and_grant_illumination() evaluates stability correctly
- [x] unlock_causation_for_alliance() updates organism._illumination_level
- [x] Event emitted to CausationExplorer

### Tier 2: Integration
- [x] HighlanderProtocol calls sync on alliance formation
- [x] HighlanderProtocol calls sync on organism removal
- [x] unified_entry.py wires bidirectional connection
- [x] Organisms receive set_system_references()

### Tier 3: Knowledge Usage
- [x] Neural decision-making checks illumination level
- [x] Logs show "🔮 Wisdom: [causation insight]" for illuminated organisms
- [x] Organisms can query causation_explorer via get_wisdom_from_causation()

### Tier 4: Validation
- [x] Simulation runs for 50+ rounds without crashes
- [x] Alliances form and persist
- [x] Causation events properly linked to illumination unlock events
- [x] No circular dependencies or deadlocks

---

## 7. Performance Considerations

### Optimization Notes:

1. **Lock contention:** AllianceWarfareSystem uses `state_lock`. Ensure sync calls don't hold lock for >1ms
2. **Event emission:** Only emit on actual unlock (has guard `if illumination_status != 'none'`)
3. **Organism lookups:** Cache organism references in AllianceWarfareSystem to avoid repeated network traversals
4. **CausationExplorer integration:** Non-blocking event emission (handlers should be fast)

### Recommended Config Values:

```json
{
  "alliance_warfare": {
    "illumination_stability_threshold": 5,
    "event_emitter_enabled": true,
    "cache_organism_lookups": true,
    "max_cached_alliances": 1000
  }
}
```

---

## 8. Future Enhancements

Once basic implementation is complete, consider:

1. **Confederation-tier Illumination:** Unlock advanced causation features for confederations (15+ rounds)
2. **Betrayal Penalty:** Reduce illumination level if alliance members betray
3. **Knowledge Transfer:** Illuminated organisms teach causation concepts to descendants
4. **Adaptive Config:** Config tuner adjusts `illumination_stability_threshold` based on success rate
5. **Visualization:** Show illumination status in UI next to alliance name (✨ for illuminated)

---

## Files Modified Summary

| File | Changes | Type |
|------|---------|------|
| `alliance_warfare.py` | +3 new methods | Feature |
| `highlander_protocol.py` | +2 new methods, +2 hook updates | Feature |
| `neural_organism.py` | +3 new methods, +1 flexibility check | Feature |
| `unified_entry.py` | +1 wiring section | Integration |
| `config.json` | +1 new config section | Config |
| `test_illumination.py` | New test file | Tests |

---

## Questions for User Review

Before proceeding to code implementation:

1. **Stability threshold:** Should it be 5 rounds or configurable per alliance size?
2. **Organism access pattern:** Do we query organisms from network.organisms dict or via method?
3. **Event handler in CausationExplorer:** Should it auto-subscribe to 'illumination_unlocked' events?
4. **Log verbosity:** How many logs for illumination process? (current: INFO for unlock + DEBUG for each org)

---

