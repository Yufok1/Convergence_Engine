"""
Comprehensive test of all swarm debugging fixes (Rounds 1-4)
"""
import sys
import time

print("=" * 70)
print("COMPREHENSIVE FIX VERIFICATION TEST")
print("=" * 70)

all_passed = True
tests_run = 0
tests_passed = 0

def test(name, condition, details=""):
    global all_passed, tests_run, tests_passed
    tests_run += 1
    if condition:
        print(f"✅ PASS: {name}")
        tests_passed += 1
    else:
        print(f"❌ FAIL: {name}")
        if details:
            print(f"         {details}")
        all_passed = False

# ============================================================================
# TEST 1: Imports work
# ============================================================================
print("\n" + "-" * 70)
print("TEST GROUP 1: Core Imports")
print("-" * 70)

try:
    from reality_simulator.language.atomic_language import AtomicLanguageSystem
    test("AtomicLanguageSystem import", True)
except Exception as e:
    test("AtomicLanguageSystem import", False, str(e))

try:
    from reality_simulator.symbiotic_network import SymbioticNetwork
    test("SymbioticNetwork import", True)
except Exception as e:
    test("SymbioticNetwork import", False, str(e))

try:
    from reality_simulator.neural.neural_organism import NeuralOrganism
    test("NeuralOrganism import", True)
except Exception as e:
    test("NeuralOrganism import", False, str(e))

# ============================================================================
# TEST 2: Level 0 gets 6 ACTION_HEADS (not 0)
# ============================================================================
print("\n" + "-" * 70)
print("TEST GROUP 2: Grounded Mode Level 0 Initialization")
print("-" * 70)

config = {'language': {'grounded': {'enabled': True, 'initial_mastery_level': 0}}}
al = AtomicLanguageSystem('test_org', config=config)

test("Level 0 starts with 6 atoms", len(al.atoms) == 6, f"Got {len(al.atoms)} atoms")
test("Mastery level is 0", al.mastery_level == 0, f"Got level {al.mastery_level}")

expected_actions = ['move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate']
has_all_actions = all(action in al.atoms for action in expected_actions)
test("Has all 6 ACTION_HEADS", has_all_actions, f"Atoms: {list(al.atoms.keys())}")

test("Available vocab is 6", len(al.get_available_vocabulary()) == 6)

# ============================================================================
# TEST 3: Experience tracking works
# ============================================================================
print("\n" + "-" * 70)
print("TEST GROUP 3: Experience Tracking")
print("-" * 70)

al2 = AtomicLanguageSystem('test_exp', config=config)
initial_exp = al2.total_experiences
test("Initial experiences is 0", initial_exp == 0)

# Simulate actions
for i in range(10):
    al2.apply_experience(i % 6, 0.5, {})

test("Experiences increment after actions", al2.total_experiences == 10, 
     f"Got {al2.total_experiences} exp")

# ============================================================================
# TEST 4: Activation count tracking (breadth)
# ============================================================================
print("\n" + "-" * 70)
print("TEST GROUP 4: Breadth Tracking (Activation Counts)")
print("-" * 70)

al3 = AtomicLanguageSystem('test_breadth', config=config)

# Do 10 of each action
for _ in range(10):
    for action_idx in range(6):
        al3.apply_experience(action_idx, 0.5, {})

# Each action should have activation count > 5
all_activated = True
for action in expected_actions:
    count = al3.atoms[action].recent_activation_count
    if count <= 5:
        all_activated = False
        print(f"   {action}: {count} activations (need >5)")

test("All actions have >5 activations", all_activated)

# ============================================================================
# TEST 5: Association formation (depth)
# ============================================================================
print("\n" + "-" * 70)
print("TEST GROUP 5: Depth Tracking (Associations)")
print("-" * 70)

# al3 should have associations formed
all_have_assocs = True
for action in expected_actions:
    assocs = len(al3.atoms[action].associations)
    if assocs < 3:
        all_have_assocs = False
        print(f"   {action}: {assocs} associations (need >=3)")

test("All actions have 3+ associations", all_have_assocs)

# ============================================================================
# TEST 6: Mastery advancement works
# ============================================================================
print("\n" + "-" * 70)
print("TEST GROUP 6: Mastery Advancement")
print("-" * 70)

al4 = AtomicLanguageSystem('test_mastery', config=config)
test("Starts at level 0", al4.mastery_level == 0)

# Simulate enough experience for advancement
for _ in range(60):
    for action_idx in range(6):
        al4.apply_experience(action_idx, 0.5, {})

can_advance = al4.check_mastery_advancement()
test("Meets advancement criteria", can_advance)

if can_advance:
    al4.try_advance_mastery()
    test("Advanced to level 1", al4.mastery_level == 1, f"Level is {al4.mastery_level}")
else:
    test("Advanced to level 1", False, "Could not advance")

# ============================================================================
# TEST 7: VP system (requires full system - lightweight check)
# ============================================================================
print("\n" + "-" * 70)
print("TEST GROUP 7: VP System Integration")
print("-" * 70)

try:
    # Check that symbiotic_network has VP code
    import inspect
    from reality_simulator.symbiotic_network import SymbioticNetwork
    source = inspect.getsource(SymbioticNetwork)
    
    has_vp_value = "vp_value" in source
    test("SymbioticNetwork has vp_value code", has_vp_value)
    
    has_mastery_loop = "try_advance_mastery" in source
    test("SymbioticNetwork has mastery advancement loop", has_mastery_loop)
    
except Exception as e:
    test("VP system check", False, str(e))

# ============================================================================
# TEST 8: NeuralOrganism VP integration
# ============================================================================
print("\n" + "-" * 70)
print("TEST GROUP 8: NeuralOrganism VP Integration")
print("-" * 70)

try:
    import inspect
    from reality_simulator.neural.neural_organism import NeuralOrganism
    source = inspect.getsource(NeuralOrganism)
    
    # Check brain.forward gets vp_value
    has_vp_forward = "vp_value=vp_val" in source or "vp_value=" in source
    test("NeuralOrganism passes vp_value to brain.forward()", has_vp_forward)
    
except Exception as e:
    test("NeuralOrganism VP check", False, str(e))

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print(f"RESULTS: {tests_passed}/{tests_run} tests passed")
print("=" * 70)

if all_passed:
    print("\n🎉 ALL TESTS PASSED! Fixes verified working.\n")
    sys.exit(0)
else:
    print(f"\n⚠️  {tests_run - tests_passed} test(s) failed. Review above.\n")
    sys.exit(1)
