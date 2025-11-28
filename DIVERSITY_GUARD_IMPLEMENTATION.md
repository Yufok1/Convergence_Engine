# 🧬 Diversity Guard Implementation Spec

**Prevent premature fitness saturation through genotype diversity enforcement**

---

## Problem Statement

**Current Issue:**
- Fitness reaches 1.0 by generation 9 (premature convergence)
- Population may collapse to single dominant genotype
- Low genetic diversity reduces exploration and network connectivity

**Root Cause:**
- Fitness function may be too permissive
- Mutation rate insufficient to maintain diversity
- No penalty for genotype clustering

---

## Solution: Diversity Guard System

### Core Concept

Track genotype frequencies and apply fitness penalties to over-represented genotypes, encouraging exploration of genetic space.

---

## Implementation

### 1. Genotype Hash Tracking

**Location:** `reality_simulator/evolution_engine.py`

```python
from collections import Counter
from typing import Dict

class DiversityGuard:
    """Prevents premature convergence through diversity enforcement"""
    
    def __init__(self, 
                 hash_similarity_threshold: float = 0.92,
                 penalty: float = 0.05,
                 enabled: bool = True):
        self.hash_similarity_threshold = hash_similarity_threshold
        self.penalty = penalty
        self.enabled = enabled
        
        # Track genotype frequencies per generation
        self.genotype_counts: Dict[str, int] = Counter()
        self.generation_history: List[Dict[str, int]] = []
        
    def calculate_genotype_similarity(self, hash1: str, hash2: str) -> float:
        """Calculate similarity between two genotype hashes (0.0-1.0)"""
        # Simple Hamming distance on hash strings
        if len(hash1) != len(hash2):
            return 0.0
        
        matches = sum(c1 == c2 for c1, c2 in zip(hash1, hash2))
        return matches / len(hash1)
    
    def find_similar_genotypes(self, target_hash: str, population_hashes: List[str]) -> List[str]:
        """Find genotypes similar to target (above threshold)"""
        similar = []
        for hash_val in population_hashes:
            similarity = self.calculate_genotype_similarity(target_hash, hash_val)
            if similarity >= self.hash_similarity_threshold:
                similar.append(hash_val)
        return similar
    
    def apply_diversity_penalty(self, organism: Organism, population: List[Organism]) -> float:
        """Apply fitness penalty based on genotype frequency"""
        if not self.enabled:
            return 0.0
        
        # Get organism's genotype hash
        genotype_hash = organism.genotype.get_hash()
        
        # Count similar genotypes in population
        population_hashes = [org.genotype.get_hash() for org in population]
        similar_count = len(self.find_similar_genotypes(genotype_hash, population_hashes))
        
        # Calculate frequency
        total_population = len(population)
        frequency = similar_count / total_population if total_population > 0 else 0.0
        
        # Apply penalty if frequency exceeds threshold
        if frequency > 0.1:  # More than 10% of population is similar
            # Penalty increases with frequency
            penalty_multiplier = min(frequency / 0.5, 1.0)  # Max penalty at 50% frequency
            return self.penalty * penalty_multiplier
        
        return 0.0
    
    def update_generation(self, population: List[Organism]):
        """Track genotype frequencies for this generation"""
        self.genotype_counts.clear()
        for org in population:
            hash_val = org.genotype.get_hash()
            self.genotype_counts[hash_val] += 1
        
        # Store generation snapshot
        self.generation_history.append(dict(self.genotype_counts))
        
        # Keep only last 10 generations
        if len(self.generation_history) > 10:
            self.generation_history.pop(0)
    
    def get_diversity_metrics(self) -> Dict[str, float]:
        """Get current diversity metrics"""
        if not self.genotype_counts:
            return {
                'unique_genotypes': 0,
                'max_frequency': 0.0,
                'diversity_index': 0.0
            }
        
        total = sum(self.genotype_counts.values())
        unique = len(self.genotype_counts)
        max_freq = max(self.genotype_counts.values()) / total if total > 0 else 0.0
        
        # Shannon diversity index
        diversity_index = 0.0
        for count in self.genotype_counts.values():
            if count > 0:
                p = count / total
                diversity_index -= p * np.log2(p)
        
        return {
            'unique_genotypes': unique,
            'max_frequency': max_freq,
            'diversity_index': diversity_index,
            'unique_genotypes_ratio': unique / total if total > 0 else 0.0
        }
```

### 2. Integration with Evolution Engine

**Location:** `reality_simulator/evolution_engine.py` (EvolutionEngine class)

```python
class EvolutionEngine:
    def __init__(self, ..., diversity_guard_config: Optional[Dict] = None):
        # ... existing init ...
        
        # Initialize diversity guard
        if diversity_guard_config:
            self.diversity_guard = DiversityGuard(
                hash_similarity_threshold=diversity_guard_config.get('hash_similarity_threshold', 0.92),
                penalty=diversity_guard_config.get('penalty', 0.05),
                enabled=diversity_guard_config.get('enabled', True)
            )
        else:
            self.diversity_guard = DiversityGuard(enabled=False)
    
    def evaluate_fitness(self, organism: Organism, population: List[Organism]) -> float:
        """Evaluate fitness with diversity penalty"""
        # Calculate base fitness (existing logic)
        base_fitness = self._calculate_base_fitness(organism)
        
        # Apply diversity penalty
        penalty = self.diversity_guard.apply_diversity_penalty(organism, population)
        adjusted_fitness = base_fitness - penalty
        
        # Clamp to valid range
        return max(0.0, min(1.0, adjusted_fitness))
    
    def evolve_generation(self, population: List[Organism]) -> List[Organism]:
        """Evolve with diversity tracking"""
        # ... existing evolution logic ...
        
        # Update diversity guard
        self.diversity_guard.update_generation(new_population)
        
        # Log diversity metrics
        metrics = self.diversity_guard.get_diversity_metrics()
        if metrics['max_frequency'] > 0.2:  # Warning threshold
            logger.warning(f"[Diversity] High genotype frequency: {metrics['max_frequency']:.2%}, "
                          f"unique genotypes: {metrics['unique_genotypes']}/{len(new_population)}")
        
        return new_population
```

### 3. Configuration Integration

**Location:** `config.json`

```json
{
  "evolution": {
    "population_size": 2000,
    "genotype_length": 48,
    "mutation_rate": {
      "initial": 0.055
    },
    "diversity_guard": {
      "enabled": true,
      "hash_similarity_threshold": 0.92,
      "penalty": 0.05,
      "frequency_threshold": 0.1
    }
  }
}
```

### 4. Metrics Logging

**Location:** `reality_simulator/main.py` (add to state logging)

```python
# In RealitySimulator.update_network()
if hasattr(self.evolution_engine, 'diversity_guard'):
    diversity_metrics = self.evolution_engine.diversity_guard.get_diversity_metrics()
    self.logger.log_state('evolution', {
        'generation': self.evolution_engine.current_generation,
        'unique_genotypes': diversity_metrics['unique_genotypes'],
        'max_genotype_frequency': diversity_metrics['max_frequency'],
        'diversity_index': diversity_metrics['diversity_index'],
        'unique_genotypes_ratio': diversity_metrics['unique_genotypes_ratio']
    })
```

---

## Metrics to Track

### Rolling Metrics

1. **Connections per Organism Average**
   ```python
   connections_per_org_avg = connection_count / organism_count
   ```

2. **Unique Genotypes Ratio**
   ```python
   unique_genotypes_ratio = unique_genotypes / population_size
   ```

3. **Max Genotype Frequency**
   ```python
   max_genotype_frequency = max(genotype_counts.values()) / population_size
   ```

4. **Diversity Index (Shannon)**
   ```python
   diversity_index = -sum(p * log2(p) for p in frequencies)
   ```

---

## Testing Strategy

### Unit Tests

1. **Diversity Guard Tests** (`tests/test_diversity_guard.py`)
   - Test similarity calculation
   - Test penalty application
   - Test frequency tracking
   - Test metrics calculation

2. **Integration Tests**
   - Test with EvolutionEngine
   - Verify fitness adjustment
   - Check diversity maintenance

### Behavioral Tests

1. **Premature Convergence Prevention**
   - Run evolution with diversity guard enabled
   - Verify unique genotypes remain >50% of population
   - Verify fitness doesn't saturate prematurely

2. **Penalty Effectiveness**
   - Create population with 80% identical genotypes
   - Verify penalty reduces their fitness
   - Verify next generation has more diversity

---

## Monitoring & Tuning

### Warning Thresholds

- **Max Frequency > 20%**: Warning logged
- **Max Frequency > 50%**: Critical warning
- **Unique Genotypes Ratio < 0.3**: Low diversity alert

### Tuning Parameters

- **hash_similarity_threshold** (0.92): How similar genotypes must be to count as "same"
  - Lower = stricter (more penalties)
  - Higher = lenient (fewer penalties)

- **penalty** (0.05): Fitness reduction per violation
  - Increase if convergence still too fast
  - Decrease if too disruptive

- **frequency_threshold** (0.1): Frequency above which penalty applies
  - Lower = more aggressive diversity enforcement
  - Higher = only penalize extreme clustering

---

## Expected Outcomes

### Before Diversity Guard
- Fitness: 1.0 by generation 9
- Unique genotypes: <30% of population
- Network connectivity: Low (sparse)

### After Diversity Guard
- Fitness: Gradual increase, plateaus around 0.85-0.95
- Unique genotypes: >50% of population
- Network connectivity: Improved (more diverse organisms = more connection opportunities)

---

## Implementation Checklist

- [ ] Create `DiversityGuard` class in `evolution_engine.py`
- [ ] Integrate with `EvolutionEngine.evaluate_fitness()`
- [ ] Add config section for diversity guard
- [ ] Add metrics logging to state logger
- [ ] Create unit tests
- [ ] Create integration tests
- [ ] Test with premature convergence scenario
- [ ] Monitor and tune parameters

---

## Risk Mitigation

1. **Start Conservative**: Begin with `penalty=0.02` and `frequency_threshold=0.15`
2. **Monitor Closely**: Watch for over-penalization (fitness stuck too low)
3. **Gradual Tuning**: Adjust parameters incrementally based on metrics
4. **Fallback**: Can disable via `enabled: false` if issues arise

---

**Status:** Ready for implementation in Phase 1 (Enhanced Cognitive Foundation)

