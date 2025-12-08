#!/usr/bin/env python3
"""
🦋 SWARM EVALUATION TOOL

Evaluates exported cocoon ensembles for architecture alignment and quality.
"""

import json
import os
import sys
from pathlib import Path

def evaluate_swarm(export_dir: str):
    """Evaluate an exported swarm for quality and alignment."""
    export_path = Path(export_dir)
    
    if not export_path.exists():
        print(f"❌ Export directory not found: {export_dir}")
        return
    
    print("=" * 70)
    print("  🦋 COCOON ENSEMBLE EVALUATION")
    print("=" * 70)
    
    # ═══════════════════════════════════════════════════════════════════
    # 1. METADATA ANALYSIS
    # ═══════════════════════════════════════════════════════════════════
    
    metadata_file = export_path / 'metadata.json'
    if not metadata_file.exists():
        print("❌ No metadata.json found")
        return
    
    with open(metadata_file, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    print(f"\n📋 EXPORT METADATA")
    print(f"  Mode: {meta.get('mode', 'N/A')}")
    print(f"  Organisms: {meta.get('num_organisms', 'N/A')}")
    print(f"  Max Input Dim: {meta.get('max_input_dim', 'N/A')}")
    
    # ═══════════════════════════════════════════════════════════════════
    # 2. ORGANISM PROFILES
    # ═══════════════════════════════════════════════════════════════════
    
    print(f"\n🧬 ORGANISM PROFILES")
    print("-" * 70)
    print(f"{'ID':<18} {'Fitness':>8} {'Personality':<12} {'Dominant Action':<15} {'Lang':^5}")
    print("-" * 70)
    
    profiles = meta.get('member_profiles', [])
    total_fitness = 0
    personalities = {}
    
    for p in profiles:
        org_id = p['organism_id'][:16] + '..'
        fitness = p.get('fitness', 0)
        total_fitness += fitness
        
        bf = p.get('behavioral_fingerprint', {})
        personality = bf.get('personality_label', 'unknown')
        dominant = bf.get('dominant_action', 'N/A')
        dominant_pct = bf.get('dominant_action_percentage', 0)
        has_lang = '✅' if p.get('use_language_head', False) else '❌'
        
        personalities[personality] = personalities.get(personality, 0) + 1
        
        print(f"{org_id:<18} {fitness:>8.4f} {personality:<12} {dominant:<10} ({dominant_pct:>3.0f}%) {has_lang:^5}")
    
    avg_fitness = total_fitness / len(profiles) if profiles else 0
    print("-" * 70)
    print(f"{'AVERAGE':<18} {avg_fitness:>8.4f}")
    
    # ═══════════════════════════════════════════════════════════════════
    # 3. PERSONALITY DIVERSITY
    # ═══════════════════════════════════════════════════════════════════
    
    print(f"\n🎭 PERSONALITY DIVERSITY")
    for personality, count in sorted(personalities.items(), key=lambda x: -x[1]):
        bar = '█' * count
        print(f"  {personality:<12} {bar} ({count})")
    
    diversity_score = len(personalities) / max(len(profiles), 1)
    print(f"\n  Diversity Score: {diversity_score:.1%} ({len(personalities)} unique personalities)")
    
    # ═══════════════════════════════════════════════════════════════════
    # 4. VOCABULARY ANALYSIS
    # ═══════════════════════════════════════════════════════════════════
    
    vocab_file = export_path / 'vocabulary.json'
    if vocab_file.exists():
        with open(vocab_file, 'r', encoding='utf-8') as f:
            vocab = json.load(f)
        
        vocab_size = vocab.get('vocab_size', len(vocab.get('word_to_id', {})))
        source = vocab.get('source', 'unknown')
        
        print(f"\n📚 VOCABULARY")
        print(f"  Size: {vocab_size:,} words")
        print(f"  Source: {source}")
        
        # Check for full vocabulary export
        if vocab_size >= 70000:
            print(f"  ✅ FULL vocabulary exported (base pool included)")
        elif vocab_size >= 1000:
            print(f"  ⚠️ Partial vocabulary ({vocab_size:,} words)")
        else:
            print(f"  ❌ Minimal vocabulary (only {vocab_size} words)")
    
    # ═══════════════════════════════════════════════════════════════════
    # 5. KNOWLEDGE WEB ANALYSIS
    # ═══════════════════════════════════════════════════════════════════
    
    kw_file = export_path / 'knowledge_web.json'
    if kw_file.exists():
        with open(kw_file, 'r', encoding='utf-8') as f:
            kw = json.load(f)
        
        concept_count = kw.get('concept_count', len(kw.get('concepts', {})))
        relation_count = kw.get('relation_count', len(kw.get('relations', {})))
        
        print(f"\n🕸️ KNOWLEDGE WEB")
        print(f"  Concepts: {concept_count:,}")
        print(f"  Relations: {relation_count:,}")
        
        if concept_count >= 70000:
            print(f"  ✅ FULL knowledge web exported")
        elif concept_count >= 1000:
            print(f"  ⚠️ Partial knowledge web")
        else:
            print(f"  ❌ Minimal knowledge web")
    
    # ═══════════════════════════════════════════════════════════════════
    # 6. CONTEXT MEMORY ANALYSIS
    # ═══════════════════════════════════════════════════════════════════
    
    cm_file = export_path / 'context_memory.json'
    if cm_file.exists():
        with open(cm_file, 'r', encoding='utf-8') as f:
            cm = json.load(f)
        
        word_freq = len(cm.get('word_frequencies', {}))
        anchors = len(cm.get('language_anchors', {}))
        
        print(f"\n🧠 CONTEXT MEMORY")
        print(f"  Word Frequencies: {word_freq:,}")
        print(f"  Language Anchors: {anchors:,}")
    
    # ═══════════════════════════════════════════════════════════════════
    # 7. NEURAL MODELS
    # ═══════════════════════════════════════════════════════════════════
    
    print(f"\n🧠 NEURAL MODELS")
    
    pt_file = export_path / 'brain_ensemble.pt'
    onnx_file = export_path / 'brain_ensemble.onnx'
    
    if pt_file.exists():
        size_kb = os.path.getsize(pt_file) / 1024
        print(f"  TorchScript: {size_kb:.1f} KB ✅")
    else:
        print(f"  TorchScript: ❌ Not found")
    
    if onnx_file.exists():
        size_kb = os.path.getsize(onnx_file) / 1024
        print(f"  ONNX: {size_kb:.1f} KB ✅")
    else:
        print(f"  ONNX: ❌ Not found")
    
    # ═══════════════════════════════════════════════════════════════════
    # 8. CAUSATION SYSTEM
    # ═══════════════════════════════════════════════════════════════════
    
    cs_file = export_path / 'causation_system.json'
    if cs_file.exists():
        with open(cs_file, 'r', encoding='utf-8') as f:
            cs = json.load(f)
        
        events = cs.get('total_events', len(cs.get('events', [])))
        print(f"\n🔬 CAUSATION SYSTEM")
        print(f"  Events Recorded: {events:,}")
    
    # ═══════════════════════════════════════════════════════════════════
    # 9. FILES CHECKLIST
    # ═══════════════════════════════════════════════════════════════════
    
    print(f"\n📦 FILES CHECKLIST")
    
    expected_files = [
        ('metadata.json', 'Core metadata'),
        ('vocabulary.json', 'Vocabulary mappings'),
        ('knowledge_web.json', 'Semantic knowledge'),
        ('context_memory.json', 'Context/anchors'),
        ('brain_ensemble.pt', 'TorchScript model'),
        ('brain_ensemble.onnx', 'ONNX model'),
        ('causation_system.json', 'Event history'),
        ('semantic_convergence.json', 'Embeddings'),
        ('cocoon.py', 'Standalone chat'),
        ('bridge.py', 'Integration bridge'),
        ('README.md', 'Documentation'),
        ('requirements.txt', 'Dependencies'),
        ('start.bat', 'Windows launcher'),
        ('start.sh', 'Unix launcher'),
    ]
    
    found = 0
    for filename, description in expected_files:
        exists = (export_path / filename).exists()
        status = '✅' if exists else '❌'
        if exists:
            found += 1
        print(f"  {status} {filename:<25} {description}")
    
    # ═══════════════════════════════════════════════════════════════════
    # 10. FINAL SCORE
    # ═══════════════════════════════════════════════════════════════════
    
    print("\n" + "=" * 70)
    print("  📊 EVALUATION SUMMARY")
    print("=" * 70)
    
    # Scoring criteria
    scores = {
        'files': found / len(expected_files),
        'fitness': min(avg_fitness / 1.0, 1.0),  # Normalize to max 1.0
        'diversity': diversity_score,
        'vocab': 1.0 if vocab_size >= 70000 else (vocab_size / 70000),
    }
    
    total_score = sum(scores.values()) / len(scores)
    
    print(f"\n  Files Complete:     {scores['files']:>6.1%}")
    print(f"  Avg Fitness:        {scores['fitness']:>6.1%}")
    print(f"  Personality Div:    {scores['diversity']:>6.1%}")
    print(f"  Vocabulary Size:    {scores['vocab']:>6.1%}")
    print(f"\n  {'─' * 30}")
    print(f"  OVERALL SCORE:      {total_score:>6.1%}")
    
    if total_score >= 0.9:
        print("\n  ✅ EXCELLENT - Production ready!")
    elif total_score >= 0.7:
        print("\n  ⚠️ GOOD - Minor issues to address")
    elif total_score >= 0.5:
        print("\n  🟡 FAIR - Significant gaps exist")
    else:
        print("\n  🔴 POOR - Major issues need fixing")
    
    print()
    return total_score


if __name__ == "__main__":
    if len(sys.argv) > 1:
        export_dir = sys.argv[1]
    else:
        # Default to the latest export
        export_dir = "agent_downloads/cocoon_ensemble_20251208164133"
    
    evaluate_swarm(export_dir)
