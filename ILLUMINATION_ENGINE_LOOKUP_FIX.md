# Illumination Engine Lookup Fix

## Problem
The Illumination Engine API endpoints (`/api/events/<event_id>/root-causes`, `/api/events/<event_id>/impact`, `/api/events/<event_id>/explain`) were not properly handling event lookup failures. The endpoints would check if events exist, log warnings, but then still call the methods anyway, which would return error responses that weren't properly formatted.

Additionally, there was a critical indentation bug in the `analyze_impact` method that caused the function to fail when events were found.

## Root Causes

### 1. API Endpoints Not Returning Errors
**File:** `causation_web_ui.py:6073-6168`

The endpoints were checking if events exist but not returning early with proper error responses. They would:
1. Check if event exists
2. Log warning if not found
3. **Still call the method anyway** (which would fail)
4. Return whatever the method returned (often an error dict, but not as HTTP 404)

### 2. Indentation Bug in `analyze_impact`
**File:** `causation_explorer.py:1509-1638`

The `analyze_impact` method had critical indentation issues:
- Line 1536: `event_id = normalized_id` was incorrectly indented inside the `if normalized_id not in self.events:` block, so it would never execute
- Line 1539: `impacts = []` was inside the `if event_id not in self.events:` block, so it would only initialize if the event was NOT found
- Line 1543: `leaf_effects = {}` was outside the `with self.graph_lock:` block, causing thread-safety issues
- Line 1631: The return statement was incorrectly indented inside the `for` loop instead of at function level

## Fixes Applied

### 1. Fixed API Endpoints (`causation_web_ui.py`)

**Root Causes Endpoint:**
- Now returns HTTP 404 with proper error JSON when event not found
- Includes debugging information (recent event IDs, similar event IDs)

**Impact Endpoint:**
- Now returns HTTP 404 with proper error JSON when event not found
- Includes debugging information

**Explain Endpoint:**
- Now returns HTTP 404 with proper error JSON when event not found
- Includes debugging information

### 2. Fixed `analyze_impact` Method (`causation_explorer.py`)

**Changes:**
- Added `with self.graph_lock:` block for thread safety
- Fixed indentation of `event_id = normalized_id` (now correctly executes after normalization)
- Fixed indentation of `impacts = []` (now always initializes)
- Fixed indentation of `leaf_effects = {}` (now inside lock)
- Fixed indentation of entire function body (now all inside lock)
- Fixed indentation of return statement (now at function level, not inside loop)

## How It Works Now

### When Event Exists:
1. Event ID is normalized (if needed)
2. Event is verified in explorer
3. Method is called with proper thread locking
4. Results are returned as JSON

### When Event Not Found:
1. Event ID is normalized (if needed)
2. Event is verified in explorer
3. **HTTP 404 is returned immediately** with error JSON containing:
   - Error message
   - Normalized ID attempted
   - Total available events count
   - Recent event IDs (for debugging)
   - Similar event IDs (for debugging)
4. Method is NOT called

## Testing

To verify the fix:

1. **Test with valid event ID:**
   - Click a causation button in Butterfly Chat
   - Should see results in Illumination Engine panel

2. **Test with invalid event ID:**
   - Manually enter a non-existent event ID in Illumination Engine
   - Click Root Causes/Impact/Explain
   - Should see error message with debugging info

3. **Check browser console:**
   - Should see `[Butterfly Chat] Illumination button clicked` logs
   - Should see event ID being set
   - Should see API calls being made
   - Should see proper error responses if event not found

4. **Check server logs:**
   - Should see `[ROOT_CAUSES]`, `[IMPACT]`, or `[EXPLAIN]` warnings if event not found
   - Should see event lookup normalization logs
   - Should see thread-safe access logs

## Status: ✅ FIXED

The Illumination Engine lookup system now:
- ✅ Properly handles missing events with HTTP 404
- ✅ Returns detailed error information for debugging
- ✅ Uses thread-safe locking in `analyze_impact`
- ✅ Correctly normalizes event IDs
- ✅ Provides helpful debugging information (recent IDs, similar IDs)

