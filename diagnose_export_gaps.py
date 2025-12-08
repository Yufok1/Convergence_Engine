#!/usr/bin/env python3
"""
🔬 EXPORT ARCHITECTURE GAP DIAGNOSTIC

Compares the LIVE butterfly system vs EXPORTED standalone system
to identify all "projected vs actual" gaps.

This is a checklist validator - run it to see what's missing.
"""

import sys
import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Files to compare
LIVE_SYSTEM = Path("reality_simulator/language/butterfly_chat.py")
STANDALONE = Path("standalone_butterfly_chat.py")
AGENT_COMPILER = Path("reality_simulator/agent_compiler.py")

def extract_methods(filepath: Path) -> Set[str]:
    """Extract all method names from a Python file."""
    methods = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                methods.add(node.name)
    except Exception as e:
        print(f"  [!] Could not parse {filepath}: {e}")
    return methods

def search_patterns(filepath: Path, patterns: Dict[str, str]) -> Dict[str, bool]:
    """Search for regex patterns in file content."""
    results = {}
    try:
        content = filepath.read_text(encoding='utf-8')
        for name, pattern in patterns.items():
            results[name] = bool(re.search(pattern, content, re.IGNORECASE))
    except Exception as e:
        print(f"  [!] Could not read {filepath}: {e}")
        for name in patterns:
            results[name] = False
    return results

def main():
    print("=" * 70)
    print("  🔬 EXPORT ARCHITECTURE GAP DIAGNOSTIC")
    print("=" * 70)
    print()
    
    # ═══════════════════════════════════════════════════════════════════
    # FEATURE CHECKLIST - What the live system has
    # ═══════════════════════════════════════════════════════════════════
    
    features = {
        # Core Chat Features
        "routing_strategies": r"(all|random|fittest|connected|by_word)",
        "fitness_weighted_aggregation": r"fitness.*confidence|weight.*fitness",
        "neural_token_generation": r"generate_tokens|_generate_tokens",
        
        # Learning Features
        "vocabulary_learning": r"learn.*word|add_word|_learn_words",
        "experience_storage": r"store.*experience|_store_chat_experience|experience_buffer",
        "neural_training": r"trainer\.|train_on_chat|chat.*train",
        "adaptive_response_length": r"adaptive_max_length|experience_count.*<",
        
        # Semantic Features
        "knowledge_web_integration": r"knowledge_web|semantic_related|_get_semantic",
        "context_memory": r"context_memory|language_anchors",
        "semantic_reward": r"semantic_reward|reward.*calc|calculate.*reward",
        
        # Quality Features
        "confidence_calculation": r"_calculate_confidence|confidence.*score",
        "repetition_penalty": r"repetition_penalty|recent_tokens",
        "top_k_sampling": r"top_k|top-k",
        
        # Tracking Features
        "debug_logging": r"debug_logs|_log_debug",
        "causation_events": r"event_emitter|causation|emit.*event",
        "conversation_history": r"conversation_history",
        
        # Export-specific
        "full_vocabulary_export": r"base_pool|74.*557|full.*vocab",
        "knowledge_web_export": r"knowledge_web.*json|serialize.*knowledge",
        "organism_state_export": r"atomic_language|organism.*state",
    }
    
    print("📋 FEATURE COMPARISON: Live System vs Standalone Export")
    print("-" * 70)
    print(f"{'Feature':<35} {'Live':^10} {'Export':^10} {'Status':^12}")
    print("-" * 70)
    
    live_features = search_patterns(LIVE_SYSTEM, features)
    standalone_features = search_patterns(STANDALONE, features)
    
    gaps = []
    aligned = []
    extra = []
    
    for feature, live_has in live_features.items():
        export_has = standalone_features.get(feature, False)
        
        live_mark = "✅" if live_has else "❌"
        export_mark = "✅" if export_has else "❌"
        
        if live_has and not export_has:
            status = "⚠️ GAP"
            gaps.append(feature)
        elif live_has and export_has:
            status = "✅ ALIGNED"
            aligned.append(feature)
        elif not live_has and export_has:
            status = "➕ EXTRA"
            extra.append(feature)
        else:
            status = "➖ NEITHER"
        
        feature_display = feature.replace("_", " ").title()
        print(f"{feature_display:<35} {live_mark:^10} {export_mark:^10} {status:^12}")
    
    print("-" * 70)
    
    # ═══════════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════════
    
    print()
    print("=" * 70)
    print("  📊 GAP ANALYSIS SUMMARY")
    print("=" * 70)
    
    print(f"\n  ✅ ALIGNED: {len(aligned)} features")
    for f in aligned:
        print(f"      • {f.replace('_', ' ')}")
    
    print(f"\n  ⚠️  GAPS (Live has, Export missing): {len(gaps)} features")
    for f in gaps:
        print(f"      • {f.replace('_', ' ')}")
    
    if extra:
        print(f"\n  ➕ EXTRA (Export has, Live missing): {len(extra)} features")
        for f in extra:
            print(f"      • {f.replace('_', ' ')}")
    
    # ═══════════════════════════════════════════════════════════════════
    # CRITICAL GAPS DETAIL
    # ═══════════════════════════════════════════════════════════════════
    
    print()
    print("=" * 70)
    print("  🔴 CRITICAL GAPS - Must Fix for Parity")
    print("=" * 70)
    
    critical_gaps = {
        "vocabulary_learning": {
            "description": "Organisms learn new words from chat",
            "live_method": "_learn_words_from_chat()",
            "impact": "Export vocabulary stays static, never grows",
            "fix": "Add vocabulary.add_word() and persistence to standalone"
        },
        "experience_storage": {
            "description": "Store chat interactions as learning experiences",
            "live_method": "_store_chat_experience()",
            "impact": "Export can't improve from conversations",
            "fix": "Add experience buffer and store_experience() to standalone"
        },
        "neural_training": {
            "description": "Train neural networks on chat data",
            "live_method": "trainer.train_on_batch()",
            "impact": "Export neural weights frozen forever",
            "fix": "Add optional trainer integration (requires PyTorch)"
        },
        "adaptive_response_length": {
            "description": "Response length grows with experience",
            "live_method": "adaptive_max_length based on experience_count",
            "impact": "Export uses fixed length, no growth",
            "fix": "Track experience_count and scale max_length"
        },
        "semantic_reward": {
            "description": "Calculate semantic quality rewards",
            "live_method": "_calculate_semantic_reward()",
            "impact": "Export can't evaluate response quality",
            "fix": "Port reward calculation from butterfly_chat.py"
        },
        "causation_events": {
            "description": "Emit events for debugging/analysis",
            "live_method": "event_emitter()",
            "impact": "Export has no causation trail",
            "fix": "Add optional event emission to standalone"
        }
    }
    
    for gap_name in gaps:
        if gap_name in critical_gaps:
            info = critical_gaps[gap_name]
            print(f"\n  🔴 {gap_name.replace('_', ' ').upper()}")
            print(f"     Description: {info['description']}")
            print(f"     Live Method: {info['live_method']}")
            print(f"     Impact:      {info['impact']}")
            print(f"     Fix:         {info['fix']}")
    
    # ═══════════════════════════════════════════════════════════════════
    # EXPORT DATA COMPLETENESS CHECK
    # ═══════════════════════════════════════════════════════════════════
    
    print()
    print("=" * 70)
    print("  📦 EXPORT DATA COMPLETENESS CHECK")
    print("=" * 70)
    
    export_data_checks = {
        "vocabulary.json": {
            "expected": "74,557+ words (full base pool)",
            "pattern": r"vocab.*size.*74|74.*557|base_pool",
            "file": AGENT_COMPILER
        },
        "knowledge_web.json": {
            "expected": "74,557+ concepts with relations",
            "pattern": r"concept_count.*74|74.*557.*concept|full.*knowledge",
            "file": AGENT_COMPILER
        },
        "context_memory.json": {
            "expected": "Language anchors, word frequencies",
            "pattern": r"context_memory.*json|language_anchors|word_frequencies",
            "file": AGENT_COMPILER
        },
        "atomic_language.json": {
            "expected": "Per-organism linguistic atoms",
            "pattern": r"atomic.*lang|atoms.*json|atomic_language_state",
            "file": AGENT_COMPILER
        },
        "experience_buffer": {
            "expected": "Stored learning experiences",
            "pattern": r"experience.*buffer|experience.*json",
            "file": AGENT_COMPILER
        },
        "semantic_convergence.json": {
            "expected": "Word embeddings, semantic anchors",
            "pattern": r"semantic_convergence|word_embeddings",
            "file": AGENT_COMPILER
        }
    }
    
    print(f"\n{'Export File':<25} {'Expected Content':<40} {'Exported?':^10}")
    print("-" * 75)
    
    for export_file, info in export_data_checks.items():
        content = info["file"].read_text(encoding='utf-8') if info["file"].exists() else ""
        has_export = bool(re.search(info["pattern"], content, re.IGNORECASE))
        status = "✅" if has_export else "❌"
        print(f"{export_file:<25} {info['expected']:<40} {status:^10}")
    
    # ═══════════════════════════════════════════════════════════════════
    # STANDALONE LOADER CHECKS
    # ═══════════════════════════════════════════════════════════════════
    
    print()
    print("=" * 70)
    print("  🔧 STANDALONE LOADER CAPABILITIES")
    print("=" * 70)
    
    loader_checks = {
        "Loads vocabulary.json": r"vocabulary.*json|chat_vocabulary",
        "Loads knowledge_web.json": r"knowledge_web.*json|knowledge_web\.get",
        "Loads context_memory.json": r"context_memory.*json|context_memory\.get",
        "Loads metadata.json": r"metadata.*json|metadata\.get",
        "Loads brain (TorchScript)": r"brain.*torchscript|jit\.load",
        "Loads brain (ONNX)": r"brain.*onnx|InferenceSession",
        "Uses semantic boosting": r"semantic.*boost|_get_semantic_related",
        "Uses organism preferences": r"preferred_words|_get_organism_preferred",
        "Applies TF-IDF boosting": r"tfidf|_get_tfidf_important",
    }
    
    print(f"\n{'Capability':<35} {'Implemented?':^15}")
    print("-" * 50)
    
    standalone_content = STANDALONE.read_text(encoding='utf-8') if STANDALONE.exists() else ""
    
    for capability, pattern in loader_checks.items():
        has_cap = bool(re.search(pattern, standalone_content, re.IGNORECASE))
        status = "✅" if has_cap else "❌"
        print(f"{capability:<35} {status:^15}")
    
    # ═══════════════════════════════════════════════════════════════════
    # PRIORITY ACTION ITEMS
    # ═══════════════════════════════════════════════════════════════════
    
    print()
    print("=" * 70)
    print("  🎯 PRIORITY ACTION ITEMS")
    print("=" * 70)
    
    actions = [
        ("HIGH", "Add vocabulary learning to standalone", "vocabulary_learning" in gaps),
        ("HIGH", "Add experience storage to standalone", "experience_storage" in gaps),
        ("HIGH", "Add semantic reward calculation", "semantic_reward" in gaps),
        ("MED", "Add adaptive response length", "adaptive_response_length" in gaps),
        ("MED", "Add causation event emission", "causation_events" in gaps),
        ("LOW", "Add optional neural training", "neural_training" in gaps),
    ]
    
    print()
    for priority, action, is_gap in actions:
        if is_gap:
            icon = "🔴" if priority == "HIGH" else "🟡" if priority == "MED" else "🟢"
            print(f"  {icon} [{priority}] {action}")
    
    # ═══════════════════════════════════════════════════════════════════
    # FINAL SCORE
    # ═══════════════════════════════════════════════════════════════════
    
    total_features = len(features)
    alignment_score = len(aligned) / total_features * 100 if total_features > 0 else 0
    
    print()
    print("=" * 70)
    print(f"  📊 ALIGNMENT SCORE: {alignment_score:.1f}% ({len(aligned)}/{total_features} features)")
    print("=" * 70)
    
    if alignment_score >= 90:
        print("  ✅ Excellent! Export closely matches live system.")
    elif alignment_score >= 70:
        print("  ⚠️ Good, but some gaps need attention.")
    elif alignment_score >= 50:
        print("  🟡 Moderate - significant gaps exist.")
    else:
        print("  🔴 Poor - major architectural gaps need fixing.")
    
    print()
    return len(gaps)

if __name__ == "__main__":
    sys.exit(main())
