# Highlander Mode Configuration

## Overview
Highlander mode enables a survival-of-the-fittest tournament system where organisms compete for dominance. Only the strongest survive, with the ultimate champion becoming the template for immortality.

## Configuration

### Config File (config.json)
The system is now configured in `config.json` under the `highlander` section:

```json
{
  "highlander": {
    "description": "Highlander Protocol - Survival of the fittest tournament system",
    "enabled": true,
    "predation_enabled": true,
    "survival_threshold": 0.5,
    "competition_intensity": 0.8,
    "population_size": 10,
    "max_battle_rounds": 10,
    "chaos_factor": 0.15,
    "max_capsules": 5,
    "max_genetic_samples": 100,
    "min_population": 5,
    "max_population": 50,
    "germination_rate": 0.1,
    "mutation_rate": 0.05,
    "rounds_per_cycle": 1
  }
}
```

### Key Settings
- **predation_enabled**: Enables predator/prey mechanics
- **survival_threshold**: Fitness threshold for survival (0.5 = 50% fitness required)
- **competition_intensity**: How many organisms battle per round (0.8 = 80% of population)
- **population_size**: Target population size for tournaments
- **germination_rate**: Rate at which new organisms spawn from fallen genetic material

## Running Highlander Mode

### Method 1: Direct Command
```bash
python unified_entry.py --highlander --predation --survival-threshold 0.5 --competition-intensity 0.8
```

### Method 2: Batch File (Windows)
```cmd
run_highlander.bat
```

### Method 3: PowerShell Script
```powershell
.\run_highlander.ps1
```

## What Happens in Highlander Mode

1. **Tournament System**: Organisms compete in survival battles
2. **Battle Arena**: Resolution of combat between organisms
3. **Capsule Manager**: Checkpoints champion organisms for backup
4. **Germination Pool**: Spawns new warriors from fallen genetic material
5. **Champion Emergence**: "There can be only one" - ultimate survivor becomes immortal template

## Monitoring
The system will display Highlander status updates during operation:
- Battle results and eliminations
- Alliance formations and betrayals
- Champion emergence notifications
- Population statistics
- Genetic pool status

## Command Line Overrides
Command line arguments override config.json settings:
- `--survival-threshold`: Override fitness threshold
- `--competition-intensity`: Override battle frequency
- `--predation`: Enable/disable predation mechanics