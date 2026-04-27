"""Full Vocabulary Pipeline - Build Curated 250K Dataset from WordNet

Pipeline:
1. Extract ~141k words from Princeton WordNet lexical database (100% proper English, ZERO names)
2. Filter obvious jargon/technical terms
3. Score by domain relevance (organism behavior/communication/comprehension)
4. Extract top 250k most relevant words (or all available)
5. Seed knowledge web with semantic associations

Source: Princeton WordNet via NLTK (141k+ curated English words)
Result: Clean vocabulary with ZERO proper nouns, brand names, or personal names
"""

import sys
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def run_step(script_path: str) -> int:
    """Run each pipeline step with the current interpreter."""
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / script_path)],
        check=False,
        cwd=PROJECT_ROOT,
    )
    return result.returncode


def run_pipeline():
    print("="*70)
    print("🦋 BUTTERFLY VOCABULARY PIPELINE")
    print("="*70)
    
    # Step 1: Build raw vocabulary from WordNet
    print("\n[1/3] Building raw vocabulary from WordNet...")
    print("-"*70)
    ret = run_step("reality_simulator/build_vocabulary.py")
    if ret != 0:
        print("❌ Failed to build raw vocabulary")
        return 1
    
    # Step 2: Refine to 250k curated vocabulary
    print("\n[2/3] Refining to 250k curated vocabulary...")
    print("-"*70)
    ret = run_step("reality_simulator/refine_vocabulary.py")
    if ret != 0:
        print("❌ Failed to refine vocabulary")
        return 1
    
    # Step 3: Seed knowledge web
    print("\n[3/3] Seeding knowledge web with 250k words...")
    print("-"*70)
    ret = run_step("reality_simulator/seed_knowledge_web_from_vocab.py")
    if ret != 0:
        print("❌ Failed to seed knowledge web")
        return 1
    
    print("\n" + "="*70)
    print("✅ PIPELINE COMPLETE")
    print("="*70)
    print("\nGenerated files:")
    print("  📄 data/butterfly_vocabulary_200k_raw.json (WordNet ~141k)")
    print("  📄 data/butterfly_vocabulary_250k_curated.json (filtered vocabulary)")
    print("  📄 data/seeded_knowledge_web_250k.json (knowledge web)")
    print("\nYour organisms now have:")
    print("  ✓ Up to 250,000 domain-aligned words from WordNet")
    print("  ✓ Semantic associations for infinite variety")
    print("  ✓ 100% proper English vocabulary")
    print("  ✓ ZERO proper nouns, brand names, or personal names")
    print("\nRun: python unified_entry.py")
    return 0

if __name__ == '__main__':
    sys.exit(run_pipeline())
