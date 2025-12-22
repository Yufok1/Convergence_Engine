import json

# Load the fresh live report
with open('live_report_fresh.json', 'r') as f:
    data = json.load(f)

events = data.get('events', {})

print('=== LIVE EVENT ANALYSIS ===')
print(f'Total events tracked: {events.get("total_events")}')
print(f'Events in last hour: {events.get("events_last_hour")}')
print(f'Events in last minute: {events.get("events_last_minute")}')

print('\n=== EVENT TYPE BREAKDOWN (Top 15) ===')
event_types = events.get('events_by_type', {})
sorted_events = sorted(event_types.items(), key=lambda x: x[1], reverse=True)[:15]
for event_type, count in sorted_events:
    print(f'{event_type}: {count}')

print('\n=== RECENT EVENTS (Last 10) ===')
recent = data.get('recent_events', [])[:10]
for i, event in enumerate(recent, 1):
    print(f'{i}. {event.get("type")} - {event.get("component")} ({event.get("age_seconds"):.1f}s ago)')

print('\n=== HIGHLANDER EVENT BREAKDOWN ===')
hl_events = {k: v for k, v in event_types.items() if 'highlander' in k.lower()}
if hl_events:
    for event_type, count in sorted(hl_events.items(), key=lambda x: x[1], reverse=True):
        print(f'{event_type}: {count}')
else:
    print('No highlander events found')

print('\n=== NEURAL EVENT BREAKDOWN ===')
neural_events = {k: v for k, v in event_types.items() if 'neural' in k.lower()}
if neural_events:
    for event_type, count in sorted(neural_events.items(), key=lambda x: x[1], reverse=True):
        print(f'{event_type}: {count}')
else:
    print('No neural events found')

print('\n=== LANGUAGE EVENT BREAKDOWN ===')
lang_events = {k: v for k, v in event_types.items() if any(word in k.lower() for word in ['language', 'vocab', 'conversation'])}
if lang_events:
    for event_type, count in sorted(lang_events.items(), key=lambda x: x[1], reverse=True):
        print(f'{event_type}: {count}')
else:
    print('No language events found')
