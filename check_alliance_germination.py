"""Check if alliance info is being captured in germination"""
import json
import os

# Check context_memory for alliance data
print("=== CONTEXT MEMORY ALLIANCE DATA ===")
try:
    with open('data/context_memory.json', 'r') as f:
        data = json.load(f)
    
    # Look for alliance-related keys
    for key in data.keys():
        if 'alliance' in key.lower():
            val = data[key]
            if isinstance(val, dict):
                print(f"{key}: {len(val)} entries")
            elif isinstance(val, list):
                print(f"{key}: {len(val)} items")
            else:
                print(f"{key}: {val}")
    
    # Check node_word_associations for Generation patterns
    node_words = data.get('node_word_associations', {})
    gen_pattern_orgs = [org for org in node_words.keys() if 'gen' in org.lower() or 'wave' in org.lower()]
    print(f"\nOrganisms with 'gen' or 'wave' in ID: {len(gen_pattern_orgs)}")
    if gen_pattern_orgs:
        print(f"  Sample: {gen_pattern_orgs[:5]}")
        
except Exception as e:
    print(f"Error: {e}")

# Check shared state for alliance info
print()
print("=== SHARED STATE ===")
try:
    with open('data/.shared_simulation_state.json', 'r') as f:
        state = json.load(f)
    
    # Look for alliance data
    alliance_keys = [k for k in state.keys() if 'alliance' in k.lower()]
    print(f"Alliance-related keys: {alliance_keys}")
    
    for key in alliance_keys:
        val = state[key]
        if isinstance(val, dict):
            print(f"  {key}: {len(val)} entries")
            if val:
                sample = list(val.items())[:3]
                for k, v in sample:
                    if isinstance(v, dict):
                        print(f"    {k[:20]}: {list(v.keys())[:5]}")
                    else:
                        print(f"    {k[:20]}: {v}")
        elif isinstance(val, list):
            print(f"  {key}: {len(val)} items")
        else:
            print(f"  {key}: {val}")
            
except Exception as e:
    print(f"Error: {e}")

# Check phase transition checkpoints for alliance data
print()
print("=== RECENT CHECKPOINT DATA ===")
try:
    checkpoint_dir = 'data/checkpoints'
    checkpoints = sorted([f for f in os.listdir(checkpoint_dir) if f.startswith('phase_transition')])
    if checkpoints:
        latest = checkpoints[-1]
        with open(os.path.join(checkpoint_dir, latest), 'r') as f:
            cp = json.load(f)
        
        print(f"Latest checkpoint: {latest}")
        
        # Look for alliance data
        for key in cp.keys():
            if 'alliance' in key.lower():
                print(f"  {key}: {cp[key]}")
        
        # Check organisms for alliance_id
        organisms = cp.get('organisms', cp.get('state', {}).get('organisms', []))
        if organisms:
            if isinstance(organisms, list):
                with_alliance = [o for o in organisms if isinstance(o, dict) and o.get('alliance_id')]
                print(f"  Organisms with alliance_id: {len(with_alliance)}/{len(organisms)}")
            elif isinstance(organisms, dict):
                with_alliance = [o for o in organisms.values() if isinstance(o, dict) and o.get('alliance_id')]
                print(f"  Organisms with alliance_id: {len(with_alliance)}/{len(organisms)}")
                
except Exception as e:
    print(f"Error: {e}")

# Check for generation wave alliances
print()
print("=== LOOKING FOR WAVE ALLIANCES ===")
try:
    with open('data/.shared_simulation_state.json', 'r') as f:
        state = json.load(f)
    
    alliances = state.get('alliances', {})
    wave_alliances = {k: v for k, v in alliances.items() if 'wave' in k.lower() or 'gen' in k.lower()}
    print(f"Wave/Gen alliances: {len(wave_alliances)}")
    
    if wave_alliances:
        for aid, adata in list(wave_alliances.items())[:5]:
            name = adata.get('name', 'Unknown')
            members = adata.get('members', [])
            print(f"  {name}: {len(members)} members")
    else:
        # Show regular alliances
        print(f"Total alliances: {len(alliances)}")
        for aid, adata in list(alliances.items())[:5]:
            if isinstance(adata, dict):
                name = adata.get('name', aid[:20])
                members = adata.get('members', [])
                print(f"  {name}: {len(members) if isinstance(members, list) else members} members")
            
except Exception as e:
    print(f"Error: {e}")
