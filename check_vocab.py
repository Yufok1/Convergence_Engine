"""Quick check of organism vocab counts in running system."""
import urllib.request
import json

try:
    r = urllib.request.urlopen('http://localhost:5000/api/organisms')
    raw = r.read().decode('utf-8')
    data = json.loads(raw)
    
    # Handle different response formats
    if isinstance(data, list):
        orgs = data
    elif isinstance(data, dict):
        orgs = data.get('organisms', data.get('data', []))
        if not orgs and 'organisms' not in data:
            # Maybe the dict itself contains organism data
            orgs = [data] if 'id' in data else []
    else:
        orgs = []
    
    print(f"Organisms: {len(orgs)}")
    
    if orgs:
        print(f"Sample organism keys: {list(orgs[0].keys())[:15]}")
        
        # Try different key names for vocab
        vocabs = []
        for o in orgs:
            v = o.get('words_learned') or o.get('vocab') or o.get('vocabulary_size') or o.get('vocab_size', 0)
            vocabs.append(v)
        
        unique_vocabs = sorted(set(vocabs))
        
        print(f"\nVocab counts seen: {unique_vocabs}")
        print(f"\nDistribution:")
        for v in unique_vocabs:
            count = vocabs.count(v)
            print(f"  {v} words: {count} organisms")
        
        # Check if any are at exactly 6 (level 0)
        at_six = vocabs.count(6)
        above_six = sum(1 for v in vocabs if v > 6)
        
        print(f"\n--- MASTERY CHECK ---")
        print(f"At level 0 (6 words): {at_six}")
        print(f"Above 6 words: {above_six}")
        
        if above_six > 0 and at_six == 0:
            print("⚠️  WARNING: No organisms at level 0, all have extra words!")
        elif at_six > 0 and above_six == 0:
            print("✅ All organisms at level 0 (6 words) - mastery gating working!")
        elif vocabs.count(0) == len(vocabs):
            print("⚠️  All vocab counts are 0 - check API field name")
        else:
            print(f"Mixed: {at_six} at level 0, {above_six} advanced")
    else:
        print("No organisms found in response")
        print(f"Raw response (first 500 chars): {raw[:500]}")

except Exception as e:
    import traceback
    traceback.print_exc()
