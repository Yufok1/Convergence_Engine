# 🤖 CURSOR IMPLEMENTATION GUIDE - CRA Robust Solution

**For:** Cursor AI Assistant
**Task:** Implement CRA settings robustness improvements
**Source:** CRA_ROBUST_SOLUTION_PLAN.md (full technical specs)
**File:** templates/causation_explorer.html (10,887 lines)

---

## 📋 IMPLEMENTATION CHECKLIST

### Phase 1: Add Settings Validation (Lines 3331-3400)

**Location:** After `vizSettings` definition (around line 3331)

**Add these exact blocks:**

```javascript
// BATCH UPDATE MODE: Prevents multiple re-renders during bulk CRA updates
let batchUpdateMode = false;
let batchUpdateTimeout = null;
let pendingBatchUpdates = [];

// Settings validation ranges
const settingsValidation = {
    linkBaseWidth: { min: 1, max: 5, type: 'number' },
    linkMaxWidth: { min: 8, max: 30, type: 'number' },
    linkMinOpacity: { min: 0.1, max: 0.8, type: 'number' },
    linkMaxOpacity: { min: 0.5, max: 1.0, type: 'number' },
    linkDensityMultiplier: { min: 0, max: 10, type: 'number' },
    linkDepthMultiplier: { min: 0, max: 5, type: 'number' },
    linkNodeConnMultiplier: { min: 0, max: 3, type: 'number' },
    nodeBaseSize: { min: 5, max: 15, type: 'number' },
    nodeMaxSize: { min: 10, max: 20, type: 'number' },
    nodeMinOpacity: { min: 0.3, max: 0.9, type: 'number' },
    nodeMaxOpacity: { min: 0.7, max: 1.0, type: 'number' },
    nodeDepthSizeMultiplier: { min: 0, max: 6, type: 'number' },
    nodeStrokeWidth: { min: 1, max: 6, type: 'number' },
    nodeStrokeOpacity: { min: 0, max: 1.0, type: 'number' },
    depthStrength: { min: 0, max: 2, type: 'number' },
    depthOpacityRange: { min: 0, max: 1, type: 'number' },
    depthSizeRange: { min: 0, max: 1, type: 'number' },
    depthParallaxAmount: { min: 0, max: 2, type: 'number' },
    shadowOffset: { min: 0, max: 5, type: 'number' },
    shadowBlur: { min: 0, max: 10, type: 'number' },
    glowIntensity: { min: 0, max: 5, type: 'number' },
    frontColorBrightness: { min: 0.5, max: 1.5, type: 'number' },
    backColorBrightness: { min: 0.3, max: 1.0, type: 'number' },
    colorSaturation: { min: 0, max: 2, type: 'number' },
    maxVisibleLinks: { min: 1000, max: 50000, type: 'number' },
    maxVisibleNodes: { min: 500, max: 20000, type: 'number' },
    transitionDuration: { min: 100, max: 1000, type: 'number' },
    animationSpeed: { min: 0.1, max: 3.0, type: 'number' },
    enableShadows: { type: 'boolean' },
    enableGlow: { type: 'boolean' },
    enableTransitions: { type: 'boolean' },
    renderQuality: { enum: ['low', 'medium', 'high'] }
};

// Validate a single setting value
function validateSettingValue(key, value) {
    const validation = settingsValidation[key];
    if (!validation) {
        // No validation rule - allow any value (for colors, etc.)
        return { valid: true, value: value };
    }

    // Type validation
    if (validation.type === 'number' && typeof value !== 'number') {
        console.warn(`[VizSettings] ${key} must be a number, got ${typeof value}. Using default.`);
        return { valid: false, value: vizSettings[key], reason: 'Type mismatch' };
    }

    if (validation.type === 'boolean' && typeof value !== 'boolean') {
        console.warn(`[VizSettings] ${key} must be boolean, got ${typeof value}. Using default.`);
        return { valid: false, value: vizSettings[key], reason: 'Type mismatch' };
    }

    // Range validation
    if (validation.min !== undefined && value < validation.min) {
        console.warn(`[VizSettings] ${key} value ${value} below minimum ${validation.min}. Clamping.`);
        return { valid: true, value: validation.min, clamped: true };
    }

    if (validation.max !== undefined && value > validation.max) {
        console.warn(`[VizSettings] ${key} value ${value} above maximum ${validation.max}. Clamping.`);
        return { valid: true, value: validation.max, clamped: true };
    }

    // Enum validation
    if (validation.enum && !validation.enum.includes(value)) {
        console.warn(`[VizSettings] ${key} value ${value} not in allowed values [${validation.enum.join(', ')}]. Using default.`);
        return { valid: false, value: vizSettings[key], reason: 'Invalid enum value' };
    }

    // Hex color validation (for color keys)
    if (key.startsWith('componentColor_') || key.startsWith('linkColor_')) {
        const hexPattern = /^#[0-9A-Fa-f]{6}$/;
        if (!hexPattern.test(value)) {
            console.warn(`[VizSettings] ${key} invalid hex color ${value}. Using default.`);
            return { valid: false, value: null, reason: 'Invalid hex color format' };
        }
    }

    return { valid: true, value: value };
}
```

**Checkpoint:** Verify code compiles without errors

---

### Phase 2: Add Batch Update Functions (After validation code)

```javascript
// Batch update mode functions
function enableBatchUpdateMode() {
    batchUpdateMode = true;
    pendingBatchUpdates = [];
    console.log('[VizSettings] Batch update mode ENABLED');

    // Auto-disable after 500ms if not explicitly committed
    if (batchUpdateTimeout) clearTimeout(batchUpdateTimeout);
    batchUpdateTimeout = setTimeout(() => {
        if (batchUpdateMode) {
            console.warn('[VizSettings] Batch mode timeout - committing automatically');
            commitBatchUpdates();
        }
    }, 500);
}

function addToBatch(key, value) {
    if (!batchUpdateMode) {
        console.warn('[VizSettings] Not in batch mode, applying immediately');
        updateVizSetting(key, value);
        return;
    }

    // Validate before adding to batch
    const validated = validateSettingValue(key, value);
    if (validated.valid) {
        pendingBatchUpdates.push({ key, value: validated.value });
        console.log(`[VizSettings] Added to batch: ${key} = ${validated.value}${validated.clamped ? ' (clamped)' : ''}`);
    } else {
        console.warn(`[VizSettings] Skipped invalid setting: ${key} = ${value} (${validated.reason})`);
    }
}

function commitBatchUpdates() {
    if (!batchUpdateMode) {
        console.warn('[VizSettings] Not in batch mode');
        return;
    }

    console.log(`[VizSettings] Committing ${pendingBatchUpdates.length} batched updates`);
    batchUpdateMode = false;
    if (batchUpdateTimeout) {
        clearTimeout(batchUpdateTimeout);
        batchUpdateTimeout = null;
    }

    if (pendingBatchUpdates.length === 0) {
        console.log('[VizSettings] No updates to commit');
        return;
    }

    // Apply all settings to vizSettings object first
    pendingBatchUpdates.forEach(({ key, value }) => {
        vizSettings[key] = value;
    });

    // Update UI elements
    pendingBatchUpdates.forEach(({ key, value }) => {
        const element = document.getElementById(key);
        if (element) {
            if (element.type === 'checkbox') {
                element.checked = value;
            } else if (element.type === 'range' || element.type === 'number') {
                element.value = value;
            } else if (element.type === 'color') {
                element.value = value;
            } else if (element.tagName === 'SELECT') {
                element.value = value;
            }

            // Visual feedback
            element.style.backgroundColor = 'rgba(0, 255, 255, 0.3)';
            setTimeout(() => {
                element.style.backgroundColor = '';
            }, 300);

            // Update display value
            const displayElement = document.getElementById(key + 'Value');
            if (displayElement) {
                displayElement.textContent = typeof value === 'boolean' ? (value ? 'On' : 'Off') : value;
            }
        }
    });

    // THEN trigger ONE visualization update with ALL changes
    if (svg && allNodes.length > 0 && simulation) {
        // Real-time update for all settings at once
        console.log('[VizSettings] Applying all updates in real-time');
        pendingBatchUpdates.forEach(({ key, value }) => {
            updateVisualizationInRealTime(key, value);
        });
        console.log('[VizSettings] All updates applied in real-time (simulation preserved)');
    } else if (svg && allNodes.length > 0) {
        // Full re-render (but only once for all changes)
        console.log('[VizSettings] Full re-render with all updates');
        renderGraph();
    } else {
        console.log('[VizSettings] Settings saved for next render');
    }

    pendingBatchUpdates = [];
    console.log('[VizSettings] Batch commit complete');
}
```

**Checkpoint:** Test batch mode with console: `enableBatchUpdateMode(); addToBatch('nodeBaseSize', 10); commitBatchUpdates();`

---

### Phase 3: Fix Performance Settings Race Condition (Line ~3778)

**Find this code:**
```javascript
// Update performance settings (may require re-render, but try to avoid it)
if (key === 'maxVisibleLinks' || key === 'maxVisibleNodes' || key === 'renderQuality') {
    // These require filtering, so we need to re-apply filters
    // But we can do it gently without full re-render
    applyFilters(); // This will gently restart simulation with alpha(0.05)
}
```

**Replace with:**
```javascript
// Update performance settings (may require re-render, but try to avoid it)
if (key === 'maxVisibleLinks' || key === 'maxVisibleNodes' || key === 'renderQuality') {
    // CRITICAL FIX: Only call applyFilters if simulation is active
    // This prevents race condition where applyFilters() → renderGraph() when simulation is null
    if (simulation && svg) {
        // Safe: simulation exists, can call applyFilters
        console.log('[VizSettings] Applying performance setting with gentle filter update');
        applyFilters();
    } else {
        // Defer to next renderGraph() call
        console.log('[VizSettings] Performance setting deferred - will apply on next render');
        // Setting already saved to vizSettings, will be used by renderGraph()
    }
}
```

**Checkpoint:** Search for "applyFilters()" to verify only one location calls it from updateVisualizationInRealTime

---

### Phase 4: Modify applyVizSettingsFromCRA() (Line ~3835)

**Find the function:** `function applyVizSettingsFromCRA(settings)`

**Replace the entire function with:**
```javascript
function applyVizSettingsFromCRA(settings) {
    // Apply ALL settings received from CRA using BATCH MODE
    console.log('[CRA] Applying visualization settings (BATCH MODE):', settings);
    console.log('[CRA] Current state:', {
        hasSvg: !!svg,
        hasSimulation: !!simulation,
        nodeCount: allNodes.length,
        linkCount: allLinks.length
    });

    try {
        // ENABLE BATCH MODE for bulk CRA updates
        enableBatchUpdateMode();

        Object.keys(settings).forEach(key => {
            // Handle component colors
            if (key.startsWith('componentColor_')) {
                const component = key.replace('componentColor_', '')
                    .replace('realitysim', 'reality_sim')
                    .replace('reality_simulator', 'reality_sim')
                    .replace('djinnkernel', 'djinn_kernel')
                    .replace('utm_kernel', 'djinn_kernel');

                const validated = validateSettingValue(key, settings[key]);
                if (validated.valid && validated.value) {
                    componentColors[component] = validated.value;
                    addToBatch(key, validated.value);

                    // Update color picker if it exists
                    const colorPicker = document.getElementById('componentColor_' + component);
                    if (colorPicker) {
                        colorPicker.value = validated.value;
                    }

                    // Update legend color immediately
                    if (svg) {
                        svg.select(`circle[data-component="${component}"]`)
                            .attr('fill', validated.value);
                    }

                    // Update node colors if graph exists
                    if (svg && simulation) {
                        svg.selectAll('.node-circle').each(function(d) {
                            if (d.component === component || d.component === component.replace('_', '')) {
                                d3.select(this).attr('fill', validated.value);
                            }
                        });
                    }
                }
            }
            // Handle link colors
            else if (key.startsWith('linkColor_')) {
                const linkType = key.replace('linkColor_', '').toLowerCase();
                const validated = validateSettingValue(key, settings[key]);
                if (validated.valid && validated.value) {
                    linkColors[linkType] = validated.value;
                    addToBatch(key, validated.value);

                    // Update color picker if it exists
                    const colorPicker = document.getElementById('linkColor_' + linkType);
                    if (colorPicker) {
                        colorPicker.value = validated.value;
                    }

                    // Update legend color immediately
                    if (svg) {
                        svg.select(`line[data-link-type="${linkType}"]`)
                            .attr('stroke', validated.value);
                    }

                    // Update link colors if graph exists
                    if (svg && simulation) {
                        svg.selectAll('.link').each(function(d) {
                            const type = (d.type || 'unknown').toLowerCase();
                            if (type === linkType) {
                                d3.select(this).attr('stroke', validated.value);
                            }
                        });
                    }
                }
            }
            // Handle general settings
            else {
                addToBatch(key, settings[key]);
            }
        });

        // COMMIT all updates at once
        commitBatchUpdates();

        console.log('[CRA] All settings applied successfully');
    } catch (e) {
        console.error('[CRA] Error applying settings:', e);
        console.error('[CRA] Stack trace:', e.stack);
        addChatMessage('system', `⚠️ Error applying settings: ${e.message}`, true);

        // Disable batch mode on error
        batchUpdateMode = false;
        pendingBatchUpdates = [];
        if (batchUpdateTimeout) {
            clearTimeout(batchUpdateTimeout);
            batchUpdateTimeout = null;
        }
    }
}
```

**Checkpoint:** Find "applyVizSettingsFromCRA" to verify only one definition exists

---

### Phase 5: Fix Color Update Functions (Lines ~5720, ~5758)

**Find in updateComponentColor():**
```javascript
} else if (svg && allNodes.length > 0) {
    // Fallback: full re-render if simulation doesn't exist yet
    // This will recreate the legend with new colors
    renderGraph();
}
```

**Replace with:**
```javascript
} else if (svg && allNodes.length > 0 && !simulation) {
    // Only re-render if simulation truly doesn't exist (not just temporarily null)
    console.log('[Color] Full re-render needed for component color update');
    renderGraph();
} else if (!svg || allNodes.length === 0) {
    console.log('[Color] Component color saved for next render');
}
// If simulation exists, real-time update already happened above
```

**Find in updateLinkColor():**
```javascript
} else if (svg && allNodes.length > 0) {
    // Fallback: full re-render if simulation doesn't exist yet
    // This will recreate the legend with new colors
    renderGraph();
}
```

**Replace with:**
```javascript
} else if (svg && allNodes.length > 0 && !simulation) {
    // Only re-render if simulation truly doesn't exist (not just temporarily null)
    console.log('[Color] Full re-render needed for link color update');
    renderGraph();
} else if (!svg || allNodes.length === 0) {
    console.log('[Color] Link color saved for next render');
}
// If simulation exists, real-time update already happened above
```

**Checkpoint:** Search for "renderGraph()" in both functions to verify changes

---

### Phase 6: Add Error Recovery to renderGraph() (Line ~4418)

**Find:** `function renderGraph() {`

**Add at the very beginning of the function (right after the opening `{`):**
```javascript
function renderGraph() {
    console.log('[RenderGraph] Starting graph render');
    console.log('[RenderGraph] State:', {
        nodeCount: allNodes.length,
        linkCount: allLinks.length,
        hasOldSimulation: !!simulation,
        vizSettingsCount: Object.keys(vizSettings).length
    });

    try {
        // Save current transform state for restoration
        let savedTransform = null;
        if (svg && graphGroup) {
            const currentTransform = d3.select('.graph-group').attr('transform');
            if (currentTransform) {
                savedTransform = currentTransform;
                console.log('[RenderGraph] Saved transform state');
            }
        }
```

**Find the end of renderGraph() function (last `}` before next function):**

**Add before the closing `}`:**
```javascript
        // Restore transform if it was saved
        if (savedTransform && graphGroup) {
            graphGroup.attr('transform', savedTransform);
            console.log('[RenderGraph] Restored transform state');
        }

        console.log('[RenderGraph] Render complete successfully');
    } catch (e) {
        console.error('[RenderGraph] CRITICAL ERROR during render:', e);
        console.error('[RenderGraph] Error details:', {
            message: e.message,
            stack: e.stack,
            nodeCount: allNodes.length,
            linkCount: allLinks.length
        });

        // User notification
        addChatMessage('system', `🔴 Graph rendering failed: ${e.message}. Attempting recovery...`, true);

        // Attempt recovery
        console.warn('[RenderGraph] Attempting recovery with default settings...');
        try {
            // Reset to safe defaults
            resetVizSettings();
            // Try again with defaults after short delay
            setTimeout(() => {
                console.log('[RenderGraph] Retry render with default settings');
                renderGraph();
            }, 1000);
        } catch (recoveryError) {
            console.error('[RenderGraph] Recovery attempt failed:', recoveryError);
            addChatMessage('system', `🔴 Recovery failed. Please refresh the page.`, true);
        }
    }
}
```

**Checkpoint:** Verify renderGraph() is wrapped in try-catch with proper braces

---

### Phase 7: Add Diagnostic Function (End of script, ~line 10800)

**Add at the very end of the script (before closing `</script>` tag):**
```javascript
// Diagnostic function for debugging visualization state
window.vizDebug = function() {
    const state = {
        hasSvg: !!svg,
        hasSimulation: !!simulation,
        simulationRunning: simulation ? !simulation.stopped : false,
        simulationAlpha: simulation ? simulation.alpha().toFixed(4) : null,
        nodeCount: allNodes.length,
        linkCount: allLinks.length,
        visibleNodeCount: svg ? d3.selectAll('.node-circle').size() : 0,
        visibleLinkCount: svg ? d3.selectAll('.link').size() : 0,
        currentSettings: Object.keys(vizSettings).length,
        batchMode: batchUpdateMode,
        pendingBatchUpdates: pendingBatchUpdates.length,
        componentColorsCount: Object.keys(componentColors).length,
        linkColorsCount: Object.keys(linkColors).length
    };

    console.log('=== VISUALIZATION DEBUG STATE ===');
    console.table(state);
    console.log('vizSettings:', vizSettings);
    console.log('componentColors:', componentColors);
    console.log('linkColors:', linkColors);
    console.log('filters:', filters);
    console.log('================================');
    return state;
};

console.log('[VizDebug] Diagnostic function loaded. Type vizDebug() in console to view state.');
```

**Checkpoint:** Reload page, type `vizDebug()` in console, verify it runs

---

## ✅ VALIDATION CHECKLIST

After all phases complete, verify:

- [ ] Page loads without console errors
- [ ] `vizDebug()` command works in console
- [ ] Pre-start: Set settings via CRA, then start simulation → graph renders correctly
- [ ] Live: Start simulation, then change settings via CRA → updates in real-time
- [ ] Invalid values: Try `addToBatch('nodeBaseSize', 10000)` → value clamped to 15
- [ ] Batch mode: `enableBatchUpdateMode(); addToBatch('nodeBaseSize', 10); commitBatchUpdates();` → works
- [ ] Search for "CRITICAL FIX" comment to verify performance fix is in place
- [ ] Search for "try {" in renderGraph to verify error handling

---

## 🚨 COMMON ISSUES

**Issue:** "validateSettingValue is not defined"
**Fix:** Make sure validation function is added BEFORE it's used

**Issue:** "Unclosed brace" errors
**Fix:** Count all `{` and `}` carefully, ensure they match

**Issue:** "applyVizSettingsFromCRA already defined"
**Fix:** Replace entire function, don't add duplicate

**Issue:** Console errors about "Cannot read property 'value'"
**Fix:** Check UI element IDs match setting keys exactly

---

## 📊 PROGRESS REPORTING

After each phase, report back to user:
```
✅ Phase X complete: [What was added]
- Lines modified: XXX-XXX
- Functions added: [list]
- Tests passed: [list]
⚠️ Issues encountered: [if any]
```

---

## 🎯 SUCCESS CRITERIA

Implementation is successful when:
1. No console errors on page load
2. vizDebug() returns complete state
3. Pre-start configuration works (set settings → start sim → renders)
4. Live drastic updates work (running sim → change settings → updates real-time)
5. Invalid values are clamped (console warnings but no crashes)
6. Batch mode prevents cascading re-renders

---

**Good luck, Cursor! Report back after each phase for review.** 🤖
