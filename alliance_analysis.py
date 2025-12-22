import json
import sys

# Load the shared state
try:
    with open('shared_state.json', 'r') as f:
        data = json.load(f)

    # Extract highlander alliances
    highlander = data.get('data', {}).get('highlander', {})
    alliances = highlander.get('alliances', {})

    print('=== HIGHLANDER ALLIANCE ANALYSIS ===')
    print(f'Total alliances: {len(alliances)}')

    # Count warchiefs (alliances with 3+ members)
    warchiefs = []
    alliance_sizes = []

    for aid, alliance in alliances.items():
        members = alliance.get('members', [])
        size = len(members)
        alliance_sizes.append(size)

        if size >= 3:
            warchiefs.append({
                'id': aid,
                'size': size,
                'power': alliance.get('power', 0),
                'leader': alliance.get('leader', 'unknown')
            })

    print(f'Warchiefs (>=3 members): {len(warchiefs)}')
    print(f'Average alliance size: {sum(alliance_sizes)/len(alliance_sizes):.1f}' if alliance_sizes else 'N/A')

    # Sort warchiefs by size
    warchiefs_sorted = sorted(warchiefs, key=lambda x: x['size'], reverse=True)

    print('\n=== TOP WARCHIEFS ===')
    for i, w in enumerate(warchiefs_sorted[:10]):
        print(f'{i+1}. Alliance {w["id"][:8]} - {w["size"]} members, power: {w["power"]:.2f}')

    # Check for territories
    territories = highlander.get('territories', {})
    claimed = [t for t in territories.values() if t.get('claimed_by')]
    print(f'\nTerritories claimed: {len(claimed)}/{len(territories)}')

    # Check for recent events
    events = highlander.get('recent_events', [])
    recent_events = events[-10:] if events else []

    print('\n=== RECENT HIGHLANDER EVENTS ===')
    for event in recent_events:
        print(f'{event.get("type", "unknown")}: {event.get("description", "")}')

except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
