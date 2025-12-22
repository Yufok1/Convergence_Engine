import json

# Load the fresh live report
with open('live_report_fresh.json', 'r') as f:
    data = json.load(f)

print('LIVE CONVERGENCE ENGINE STATUS')
print('='*60)
print(f'Timestamp: {data.get("timestamp")}')
print(f'Population: {data.get("population", {}).get("total_organisms")} organisms ({data.get("population", {}).get("active_organisms")} active)')
print(f'Active Alliances: {data.get("alliances", {}).get("active_alliances")}')
print(f'Warchiefs: {data.get("alliances", {}).get("warchief_count")}')
print(f'Wars in Progress: {data.get("alliances", {}).get("wars_in_progress")}')
print(f'Neural Training Steps: {data.get("neural", {}).get("total_training_steps")}')
print(f'Vocabulary Words: {data.get("language", {}).get("total_vocabulary_words")}')
print(f'Breath Cycle: {data.get("resources", {}).get("breath_cycle")}')
print(f'Events in Last Minute: {data.get("events", {}).get("events_last_minute")}')
print('='*60)

print('\nHIGHLANDER STATUS')
print('-'*30)
hl = data.get('highlander', {})
print(f'Phase: {hl.get("phase")}')
print(f'Round: {hl.get("round_number")}')
print(f'Eliminations: {hl.get("eliminations_total")}')
print(f'Survival Threshold: {hl.get("survival_threshold")}')

print('\nNEURAL STATUS')
print('-'*30)
nn = data.get('neural', {})
print(f'Brains: {nn.get("organisms_with_brains")}')
print('.4f')
print('.4f')
print(f'Experience Buffer: {nn.get("experience_buffer_total")}')

print('\nLANGUAGE STATUS')
print('-'*30)
lang = data.get('language', {})
print(f'Vocab Size: {lang.get("total_vocabulary_words")}')
print('.1f')
print(f'Highest Mastery: Level {lang.get("highest_mastery_achieved")}')

print('\nNETWORK STATUS')
print('-'*30)
net = data.get('network', {})
print(f'Connections: {net.get("connections")}')
print('.4f')
print(f'Communities: {net.get("communities")}')
print('.4f')

print('\nBEHAVIORAL BREAKDOWN')
print('-'*30)
behaviors = data.get('language', {}).get('dominant_behaviors', {})
for behavior, count in behaviors.items():
    print(f'{behavior}: {count}')

print('\nTOP ORGANISMS')
print('-'*30)
top_orgs = data.get('top_organisms', [])[:5]
for i, org in enumerate(top_orgs, 1):
    print(f'{i}. {org["id"][:8]} - Fitness: {org["fitness"]:.4f}, Age: {org["age"]}, Exp: {org["experience_count"]}')

print('\nWARNINGS')
print('-'*30)
warnings = data.get('warnings', [])
if warnings:
    for warning in warnings:
        print(f'WARNING: {warning}')
else:
    print('No warnings - system running smoothly!')