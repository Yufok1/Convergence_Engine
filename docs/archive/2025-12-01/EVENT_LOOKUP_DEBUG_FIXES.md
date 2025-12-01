# Event Lookup Debug Fixes

## Problem
Causation buttons in the UI were showing "Event not found" errors even though events were being emitted with unique IDs and stored in `CausationExplorer.events`.

## Root Causes Identified
1. **No logging in `get_event_summary()`** - Silent failures when events weren't found
2. **Inconsistent event ID normalization** - Some methods normalized IDs, others didn't
3. **No verification after storage** - Events could be stored but immediately lost
4. **Limited debug information** - Hard to trace which events were available vs requested

## Fixes Applied

### 1. Enhanced Event Lookup Methods (`causation_explorer.py`)

#### `get_event_summary(event_id)`
- Added event ID normalization (handles `evt_xxx` vs `evt-xxx` variations)
- Added comprehensive logging when events are not found
- Returns detailed error information including:
  - Normalized ID attempted
  - Total available events count
  - Sample event IDs (first 20) for comparison
- Logs successful lookups for debugging

#### `analyze_impact(event_id)`
- Added same event ID normalization
- Enhanced error messages with available event information
- Added debug logging for successful lookups

#### `explain_event(event_id)`
- Added same event ID normalization
- Enhanced error messages with available event information
- Added debug logging for successful lookups

### 2. Event Storage Verification (`causation_explorer.py`)

#### Immediate Verification
- Added immediate verification after storing critical events (butterfly_chat_message, butterfly_chat_response, word_assignment)
- Logs error if event is missing immediately after storage
- Logs confirmation when event is successfully stored

#### Enhanced Debug Logging
- Language events now log with `[EVENT_STORAGE]` prefix for easy filtering
- Logs include event ID, type, component, and total event count
- Verification step confirms event presence in dictionary

### 3. Enhanced Debug Endpoint (`causation_web_ui.py`)

#### `/api/debug/events` Improvements
- Now uses shared explorer instance if available (from `unified_entry.py`)
- Returns comprehensive event information:
  - `total_events`: Total count
  - `event_ids`: First 100 event IDs for inspection
  - `events_by_type`: Count breakdown by event type
  - `events_by_component`: Count breakdown by component
  - `recent_events`: Last 20 events with full details
  - `language_events`: All language-related events (first 50)
  - `word_assignment_events`: All word assignment events (first 20)
  - `explorer_source`: Whether using shared or local explorer instance

## Debugging Workflow

### 1. Check Event Storage
```bash
curl http://localhost:5000/api/debug/events
```
This will show:
- Total events stored
- All event IDs (first 100)
- Language events with full details
- Word assignment events

### 2. Check Logs for Event Lookups
Look for log entries with:
- `[EVENT_LOOKUP]` - Event lookup attempts
- `[EVENT_STORAGE]` - Event storage confirmations
- `Event not found` - Missing events with available IDs

### 3. Verify Event IDs Match
Compare:
- Event IDs in `/api/debug/events` response
- Event IDs in causation trail from Butterfly Chat
- Event IDs in UI button clicks

### 4. Check Explorer Instance
The debug endpoint now reports `explorer_source`:
- `shared` - Using shared instance from `unified_entry.py` (correct for live events)
- `local` - Using local instance (may not have latest events)

## Expected Behavior

### Successful Event Lookup
```
[EVENT_LOOKUP] Found event: evt_1764512285827837_6963 (type=butterfly_chat_response, component=butterfly_chat)
```

### Failed Event Lookup
```
[EVENT_LOOKUP] Event not found in get_event_summary: evt_1764512285827837_6963 (normalized: evt_1764512285827837_6963). Available events: 150 total. Sample IDs: ['evt_1764512285827837_6962', 'evt_1764512285827837_6961', ...]
```

### Event Storage Verification
```
[EVENT_STORAGE] Stored language event: evt_1764512285827837_6963 (type=butterfly_chat_response, component=butterfly_chat) in events dict (total: 151)
[EVENT_STORAGE] Verified: Event evt_1764512285827837_6963 is present in self.events
```

## Next Steps for Further Debugging

If events are still not found:

1. **Check Thread Safety**: Ensure `graph_lock` is properly protecting event storage
2. **Check State Reloads**: Verify that shared state reloads aren't overwriting events
3. **Check Event ID Format**: Ensure UI and backend use same ID format
4. **Check Session Alignment**: Verify UI and backend are in same session/namespace
5. **Add Event Persistence**: Consider writing events to persistent store if they're only in-memory

## Testing

After these fixes:
1. Send a message via Butterfly Chat
2. Check `/api/debug/events` for the new event IDs
3. Click causation buttons in the UI
4. Check logs for `[EVENT_LOOKUP]` entries
5. Verify events are found and buttons work

