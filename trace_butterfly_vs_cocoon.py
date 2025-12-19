#!/usr/bin/env python3
"""
🦋 BUTTERFLY vs COCOON - FULL CAPABILITY TRACE
Identifies all divergences between the full system and the cocoon export.
"""
import inspect
import sys

print("=" * 80)
print("🦋 BUTTERFLY SYSTEM - FULL CAPABILITY TRACE")
print("=" * 80)

butterfly_caps = {}
cocoon_caps = {}

# =============================================================================
# TRACE BUTTERFLY CAPABILITIES
# =============================================================================

# 1. Neural Brain
print("\n[1] NEURAL BRAIN (OrganismBrain)")
try:
    from reality_simulator.neural.brain import OrganismBrain
    brain = OrganismBrain(input_dim=28, hidden_dim=64, output_dim=6)
    butterfly_caps['brain'] = {
        'class': 'OrganismBrain',
        'attributes': [a for a in dir(brain) if not a.startswith('_')],
        'init_params': list(inspect.signature(OrganismBrain.__init__).parameters.keys()),
        'forward_params': list(inspect.signature(OrganismBrain.forward).parameters.keys()),
        'has_attention': hasattr(brain, 'attention'),
        'has_language_head': hasattr(brain, 'fc_language'),
        'has_concept_head': hasattr(brain, 'concept_head'),
    }
    print(f"    ✅ OrganismBrain loaded")
    print(f"    init params: {butterfly_caps['brain']['init_params']}")
    print(f"    forward params: {butterfly_caps['brain']['forward_params']}")
except Exception as e:
    print(f"    ❌ ERROR: {e}")
    butterfly_caps['brain'] = None

# 2. Language System
print("\n[2] LANGUAGE SYSTEM")
try:
    from reality_simulator.neural.language import LanguageSystem, Vocabulary
    butterfly_caps['language'] = {
        'vocabulary_methods': [m for m in dir(Vocabulary) if not m.startswith('_')],
        'language_system_methods': [m for m in dir(LanguageSystem) if not m.startswith('_')],
    }
    print(f"    ✅ Vocabulary methods: {butterfly_caps['language']['vocabulary_methods']}")
    print(f"    ✅ LanguageSystem methods: {len(butterfly_caps['language']['language_system_methods'])}")
except Exception as e:
    print(f"    ❌ ERROR: {e}")
    butterfly_caps['language'] = None

# 3. Knowledge Web
print("\n[3] KNOWLEDGE WEB")
try:
    from reality_simulator.neural.knowledge_web import KnowledgeWeb, Concept, ConceptRelation
    kw = KnowledgeWeb()
    butterfly_caps['knowledge_web'] = {
        'methods': [m for m in dir(kw) if not m.startswith('_') and callable(getattr(kw, m))],
        'concept_attrs': [a for a in dir(Concept) if not a.startswith('_')],
        'has_relations': hasattr(kw, 'relations'),
        'has_concepts': hasattr(kw, 'concepts'),
    }
    print(f"    ✅ KnowledgeWeb methods: {butterfly_caps['knowledge_web']['methods']}")
except Exception as e:
    print(f"    ❌ ERROR: {e}")
    butterfly_caps['knowledge_web'] = None

# 4. Concept System (RCUS)
print("\n[4] CONCEPT SYSTEM (RCUS)")
try:
    from reality_simulator.neural.concept_system import ConceptHead, KEY_COMPOSITIONS, ConceptComposer
    butterfly_caps['concept_system'] = {
        'concept_head': True,
        'key_compositions': len(KEY_COMPOSITIONS),
        'compositions_list': KEY_COMPOSITIONS[:5],
        'composer_methods': [m for m in dir(ConceptComposer) if not m.startswith('_')],
    }
    print(f"    ✅ ConceptHead: YES")
    print(f"    ✅ KEY_COMPOSITIONS: {len(KEY_COMPOSITIONS)}")
    print(f"    ✅ Sample: {KEY_COMPOSITIONS[:3]}")
except Exception as e:
    print(f"    ❌ ERROR: {e}")
    butterfly_caps['concept_system'] = None

# 5. Causation Explorer
print("\n[5] CAUSATION EXPLORER")
try:
    from causation_explorer import CausationExplorer
    butterfly_caps['causation'] = {
        'methods': [m for m in dir(CausationExplorer) if not m.startswith('_') and callable(getattr(CausationExplorer, m, None))],
    }
    print(f"    ✅ CausationExplorer methods: {len(butterfly_caps['causation']['methods'])}")
except Exception as e:
    print(f"    ❌ ERROR: {e}")
    butterfly_caps['causation'] = None

# 6. Alliance Warfare
print("\n[6] ALLIANCE WARFARE")
try:
    from reality_simulator.symbiotic_network import AllianceWarfare
    butterfly_caps['alliances'] = {
        'methods': [m for m in dir(AllianceWarfare) if not m.startswith('_')],
    }
    print(f"    ✅ AllianceWarfare methods: {len(butterfly_caps['alliances']['methods'])}")
    print(f"    Key: {[m for m in butterfly_caps['alliances']['methods'] if 'battle' in m.lower() or 'alliance' in m.lower()]}")
except Exception as e:
    print(f"    ❌ ERROR: {e}")
    butterfly_caps['alliances'] = None

# 7. Neural Trainer (correlation tracking)
print("\n[7] NEURAL TRAINER & CORRELATION")
try:
    from reality_simulator.neural.trainer import NeuralTrainer
    butterfly_caps['trainer'] = {
        'methods': [m for m in dir(NeuralTrainer) if not m.startswith('_')],
        'correlation_methods': [m for m in dir(NeuralTrainer) if 'correl' in m.lower()],
        'tracking_methods': [m for m in dir(NeuralTrainer) if 'track' in m.lower()],
    }
    print(f"    ✅ NeuralTrainer methods: {len(butterfly_caps['trainer']['methods'])}")
    print(f"    Correlation: {butterfly_caps['trainer']['correlation_methods']}")
    print(f"    Tracking: {butterfly_caps['trainer']['tracking_methods']}")
except Exception as e:
    print(f"    ❌ ERROR: {e}")
    butterfly_caps['trainer'] = None

# 8. Experience Buffer
print("\n[8] EXPERIENCE BUFFER")
try:
    from reality_simulator.neural.trainer import ExperienceBuffer as ButterflyEB
    butterfly_caps['experience_buffer'] = {
        'methods': [m for m in dir(ButterflyEB) if not m.startswith('_')],
    }
    print(f"    ✅ ExperienceBuffer methods: {butterfly_caps['experience_buffer']['methods']}")
except Exception as e:
    print(f"    ❌ ERROR: {e}")
    butterfly_caps['experience_buffer'] = None

# 9. Curriculum System
print("\n[9] CURRICULUM / TEACHERS")
try:
    from reality_simulator.neural.trainer import LanguageTeacher
    butterfly_caps['curriculum'] = {
        'has_language_teacher': True,
        'teacher_methods': [m for m in dir(LanguageTeacher) if not m.startswith('_')],
    }
    print(f"    ✅ LanguageTeacher methods: {butterfly_caps['curriculum']['teacher_methods']}")
except Exception as e:
    print(f"    ⚠️ LanguageTeacher: {e}")
    butterfly_caps['curriculum'] = None

# =============================================================================
# NOW TRACE COCOON CAPABILITIES
# =============================================================================
print("\n" + "=" * 80)
print("🥚 COCOON - CAPABILITY TRACE")
print("=" * 80)

# Read cocoon template from agent_compiler
try:
    with open('reality_simulator/agent_compiler.py', 'r', encoding='utf-8') as f:
        compiler_source = f.read()
    
    # Find the template string
    import re
    template_match = re.search(r"template = Template\(r'''(.*?)'''\)", compiler_source, re.DOTALL)
    if template_match:
        cocoon_template = template_match.group(1)
        
        # Check what's in the cocoon template
        print("\n[COCOON TEMPLATE ANALYSIS]")
        
        checks = [
            ('OrganismBrain class', 'class OrganismBrain'),
            ('MultiHeadAttention', 'class MultiHeadAttention'),
            ('ConceptHead', 'class ConceptHead'),
            ('ExperienceBuffer', 'class ExperienceBuffer'),
            ('VP-aware attention', 'vp_value'),
            ('Language head', 'fc_language'),
            ('Triple loss', 'rl_loss.*lang_loss.*concept_loss'),
            ('Vocabulary expansion', 'add_word'),
            ('Knowledge web', 'knowledge_web'),
            ('Causation tracking', 'causation'),
            ('Alliance system', 'alliance'),
            ('Correlation tracking', 'correlation'),
            ('Language teacher', 'teacher'),
            ('Curriculum', 'curriculum'),
            ('Tokenize', 'def tokenize'),
            ('Detokenize', 'def detokenize'),
            ('Generate response', 'def generate_response'),
            ('Train step', 'def train_step'),
            ('Ensemble voting', 'EnsembleVoting'),
            ('Gym adapter', 'GymRunner'),
            ('HTTP server', 'run_http_server'),
            ('Self export', 'def export_cocoon'),
        ]
        
        cocoon_caps['features'] = {}
        for name, pattern in checks:
            found = bool(re.search(pattern, cocoon_template, re.IGNORECASE))
            cocoon_caps['features'][name] = found
            status = "✅" if found else "❌"
            print(f"    {status} {name}")
        
except Exception as e:
    print(f"    ❌ ERROR reading cocoon template: {e}")

# =============================================================================
# DIVERGENCE ANALYSIS
# =============================================================================
print("\n" + "=" * 80)
print("⚡ DIVERGENCE ANALYSIS - BUTTERFLY vs COCOON")
print("=" * 80)

missing = []
if 'features' in cocoon_caps:
    for name, has in cocoon_caps['features'].items():
        if not has:
            missing.append(name)

print("\n❌ MISSING IN COCOON:")
for m in missing:
    print(f"    - {m}")

print("\n" + "=" * 80)
print("🎯 RECOMMENDED ADDITIONS TO COCOON:")
print("=" * 80)
recommendations = [
    ("Causation tracking", "Track cause-effect relationships for decisions"),
    ("Correlation tracking", "Track statistical correlations between states/actions"),
    ("Alliance system", "Multi-agent cooperation and competition"),
    ("Language teacher", "Guided vocabulary and grammar learning"),
    ("Curriculum system", "Progressive learning difficulty"),
]
for name, desc in recommendations:
    if name.lower().replace(' ', '') in [m.lower().replace(' ', '') for m in missing]:
        print(f"    🔧 {name}: {desc}")
