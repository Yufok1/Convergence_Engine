# 🎓 Mastery Level System

**Vocabulary Progression Through Earned Growth**

---

## Overview

The Mastery Level System gates vocabulary expansion based on demonstrated competence. Organisms must master their current vocabulary before gaining access to more words.

**Philosophy**: Words are not given freely. They must be earned through usage (breadth) and understanding (depth - forming associations).

---

## Mastery Levels

| Level | Name | Max Words | Icon | Color |
|-------|------|-----------|------|-------|
| 0 | Novice | 6 | 🌱 | Gray |
| 1 | Adept | 26 | 🌿 | Green |
| 2 | Scholar | 76 | 🌳 | Dark Green |
| 3 | Master | 276 | 🎓 | Purple |
| 4 | Grandmaster | ∞ | 👑 | Gold |

---

## Advancement Criteria

To advance from level N to N+1, an organism must demonstrate:

### Breadth (50% threshold)
At least 50% of words must be used 3+ times.

```python
breadth_ratio = words_used_3plus / total_words
requirement: breadth_ratio >= 0.50
```

### Depth (30% threshold)
At least 30% of words must have 2+ associations formed.

```python
depth_ratio = words_with_2plus_associations / total_words
requirement: depth_ratio >= 0.30
```

### Experience Progress (Level-specific)
Minimum experience thresholds per level:
- Level 0→1: 25 experiences
- Level 1→2: 100 experiences
- Level 2→3: 300 experiences
- Level 3→4: 600 experiences

---

## Behavior-Driven Vocabulary Specialization

When organisms advance, they receive words biased by their dominant behavior:

### Behavioral Categories

**🗡️ Warriors** (high compete ratio)
```
aggression, attack, battle, combat, conflict, conquer, crush,
defeat, destroy, dominate, fight, force, hostile, overwhelm,
power, strike, struggle, vanquish, victory, war
```

**🤝 Diplomats** (high cooperate ratio)
```
alliance, bond, collaborate, community, consensus, cooperate,
friend, harmony, help, join, mutual, negotiate, partner,
peace, share, support, together, treaty, trust, unite
```

**🧭 Explorers** (high move ratio)
```
adventure, beyond, curiosity, discover, explore, far, horizon,
journey, map, navigate, new, path, pioneer, quest, roam,
search, travel, unknown, venture, wander
```

**🏔️ Hermits** (high isolate ratio)
```
alone, apart, detach, distant, independent, inner, isolate,
lonely, meditate, private, quiet, recluse, retreat, seclude,
separate, silence, solitary, solitude, withdraw, within
```

**🌱 Nurturers** (high reproduce ratio)
```
birth, bloom, care, child, create, cultivate, develop, family,
fertile, flourish, generate, grow, life, multiply, nurture,
offspring, parent, produce, seed, spawn
```

**🛡️ Conservers** (high rest ratio)
```
balance, calm, conserve, constant, endure, maintain, patience,
permanent, persist, preserve, protect, recover, reliable, reserve,
restore, safe, stable, steady, store, sustain
```

### Selection Algorithm

```python
def get_behavior_biased_words(fingerprint, available_words):
    # Find dominant behavior
    behaviors = ['explore', 'diplomacy', 'warrior', 'conserver', 'nurturer', 'hermit']
    dominant_idx = fingerprint.index(max(fingerprint))
    dominant = behaviors[dominant_idx]
    
    # Get behavior-specific words
    behavior_words = BEHAVIOR_VOCABULARY[dominant]
    
    # 60% from dominant behavior, 40% random
    biased = random.sample(behavior_words, int(count * 0.6))
    random_words = random.sample(available_words - biased, int(count * 0.4))
    
    return biased + random_words
```

---

## Integration Points

### AtomicLanguage

```python
class AtomicLanguage:
    def check_mastery_advancement(self) -> bool:
        """Check and potentially advance mastery level."""
        if self._mastery_level >= 4:
            return False  # Already max
        
        breadth, depth, exp_progress = self._calculate_mastery_progress()
        
        if breadth >= 0.50 and depth >= 0.30 and exp_progress >= 1.0:
            self._advance_mastery_level()
            return True
        return False
```

### Live Report

`data/live_report.json` includes mastery distribution:

```json
{
  "language": {
    "mastery_level_0": 12,
    "mastery_level_1": 45,
    "mastery_level_2": 8,
    "mastery_level_3": 2,
    "mastery_level_4": 0,
    "highest_mastery_achieved": 3,
    "avg_mastery_level": 1.2,
    "dominant_behaviors": {
      "diplomats": 23,
      "warriors": 18,
      "explorers": 15,
      "conservers": 8,
      "nurturers": 3,
      "hermits": 0
    }
  }
}
```

### UI Dossier

The organism dossier displays:
- Current mastery level with icon (🌱→👑)
- Progress bar toward next level
- Words learned / max words
- Words needed to advance

---

## Tournament Integration

### Mastery-Based Matchmaking

Organisms only battle others at the same mastery level:

```python
def get_mastery_level_peers(organism, all_organisms):
    my_level = organism.atomic_language._mastery_level
    return [o for o in all_organisms 
            if o.atomic_language._mastery_level == my_level]
```

### Highlander Rewards

Tournament winners can steal words from losers, but only words they don't already have. This accelerates vocabulary acquisition for victorious organisms.

---

## Configuration

No configuration needed - mastery thresholds are hardcoded as they represent fundamental progression milestones.

```python
MASTERY_VOCAB_SIZES = [6, 26, 76, 276, float('inf')]
BREADTH_THRESHOLD = 0.50
DEPTH_THRESHOLD = 0.30
EXPERIENCE_THRESHOLDS = [25, 100, 300, 600]
```

---

## Monitoring

Check mastery distribution in logs:
```
[LANGUAGE] Organism abc123 advanced to Level 2 (Scholar) with 26 words
[LANGUAGE] Mastery check: breadth=0.62, depth=0.38, exp=1.0 - PASSED
```

Or via API:
```bash
curl http://localhost:5000/api/organisms | jq '.[].mastery_level'
```

---

## Related Documentation

- [ATOMIC_LANGUAGE_CHAT.md](../ATOMIC_LANGUAGE_CHAT.md) - Language system overview
- [CHANGELOG.md](../CHANGELOG.md) - Implementation history
- [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) - System architecture
