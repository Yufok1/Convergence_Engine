# Illumination Engine Language Component Fix

## Problem
The Illumination Engine dropdown was missing `language` and `butterfly_chat` components, preventing users from filtering language events and causing causation links on Butterfly Chat to not work properly.

## Solution
Added the missing language components to the Illumination Engine dropdown and updated related mappings.

## Changes Made

### 1. Added Language Components to Illumination Engine Dropdown
**File:** `templates/causation_explorer.html:2379-2387`

**Before:**
```html
<select id="illuminationComponent">
    <option value="">All Components</option>
    <option value="realitysim">realitysim</option>
    <option value="explorer">explorer</option>
    <option value="djinnkernel">djinnkernel</option>
    <option value="quantum">quantum</option>
    <option value="neural">neural</option>
    <option value="ml_analysis">ml_analysis</option>
</select>
```

**After:**
```html
<select id="illuminationComponent">
    <option value="">All Components</option>
    <option value="realitysim">realitysim</option>
    <option value="explorer">explorer</option>
    <option value="djinnkernel">djinnkernel</option>
    <option value="quantum">quantum</option>
    <option value="neural">neural</option>
    <option value="ml_analysis">ml_analysis</option>
    <option value="language">language</option>
    <option value="butterfly_chat">butterfly_chat</option>
</select>
```

### 2. Updated Event Type Placeholder
**File:** `templates/causation_explorer.html:2393`

**Before:**
```html
<input type="text" id="illuminationEventType" placeholder="e.g., config_update">
```

**After:**
```html
<input type="text" id="illuminationEventType" placeholder="e.g., config_update, vocabulary_growth, organism_communication, butterfly_chat_message">
```

### 3. Updated Component Map for CRA Filter Control
**File:** `templates/causation_explorer.html:5342-5352`

**Before:**
```javascript
const componentMap = {
    'reality_sim': 'filter-reality_sim',
    'reality_simulator': 'filter-reality_sim',
    'explorer': 'filter-explorer',
    'djinn_kernel': 'filter-djinn_kernel',
    'utm_kernel': 'filter-djinn_kernel',
    'breath': 'filter-breath',
    'neural': 'filter-neural',
    'ml_analysis': 'filter-ml_analysis',
    'system': 'filter-system'
};
```

**After:**
```javascript
const componentMap = {
    'reality_sim': 'filter-reality_sim',
    'reality_simulator': 'filter-reality_sim',
    'explorer': 'filter-explorer',
    'djinn_kernel': 'filter-djinn_kernel',
    'utm_kernel': 'filter-djinn_kernel',
    'breath': 'filter-breath',
    'neural': 'filter-neural',
    'ml_analysis': 'filter-ml_analysis',
    'language': 'filter-language',
    'butterfly_chat': 'filter-butterfly_chat',
    'system': 'filter-system'
};
```

## Language Event Types Supported

The Illumination Engine now supports filtering by these language event types:

1. **`vocabulary_growth`** - Component: `language`
   - Emitted when new words are added to vocabulary
   - Shows: `vocab_size`, `word`, `word_id`

2. **`organism_communication`** - Component: `language`
   - Emitted when organisms exchange tokens
   - Shows: `tokens_exchanged`, `num_organisms`, `organism_a_id`, `organism_b_id`

3. **`butterfly_chat_message`** - Component: `butterfly_chat`
   - Emitted when user sends message
   - Shows: `message`, `tokens`, `num_organisms_queried`

4. **`butterfly_chat_response`** - Component: `butterfly_chat`
   - Emitted when organism responds
   - Shows: `response`, `tokens`, `confidence`, `fitness`

5. **`word_assignment`** - Component: `language`
   - Emitted when words are assigned to organisms
   - Shows: `word`, `organism_id`, `context`

## Usage Examples

### Filter by Language Component
1. Open Illumination Engine
2. Select "language" from Component dropdown
3. Click "Search" to see all language events

### Filter by Butterfly Chat Component
1. Open Illumination Engine
2. Select "butterfly_chat" from Component dropdown
3. Click "Search" to see all chat events

### Filter by Event Type
1. Open Illumination Engine
2. Type `vocabulary_growth` in Event Type field
3. Click "Search" to see vocabulary growth events

### Combined Filter
1. Open Illumination Engine
2. Select "language" from Component dropdown
3. Type `organism_communication` in Event Type field
4. Click "Search" to see organism communication events

## Impact

✅ **Causation links on Butterfly Chat now work** - Users can filter by language/butterfly_chat components
✅ **Language events are discoverable** - Can search for vocabulary_growth, organism_communication, etc.
✅ **CRA can control language filters** - Component map updated for CRA filter control
✅ **Better UX** - Placeholder text shows language event types as examples

## Verification

After this fix:
- ✅ Illumination Engine dropdown includes "language" and "butterfly_chat"
- ✅ Event type placeholder includes language event examples
- ✅ Component map includes language components for CRA control
- ✅ Causation links on Butterfly Chat should now be visible when filtering by language/butterfly_chat

