# 🤖 CRA Full System Test Prompt

**Copy and paste this prompt into the CRA chat to test all capabilities:**

---

## 📋 Full System Capability Test Request

Please perform a comprehensive test of all your capabilities and provide a detailed report. I want to verify that all systems are working correctly after the PyTorch integration.

### Test Requirements:

1. **Visualization Settings Test** - Test ALL 40+ visualization settings:
   - Adjust link appearance (base width, max width, opacity ranges, multipliers)
   - Adjust node appearance (sizes, opacity, depth effects, stroke)
   - Adjust depth effects (strength, opacity range, size range, parallax)
   - Toggle visual effects (shadows, glow, with intensity adjustments)
   - Adjust color settings (brightness, saturation)
   - Change ALL component colors (reality_sim, explorer, djinn_kernel, breath, neural, system)
   - Change ALL link colors (threshold, correlation, direct, temporal, unknown)
   - Adjust performance settings (viewport culling, max visible links/nodes, render quality)
   - Adjust animation settings (transitions, duration, speed)

2. **Graph Filter Test** - Test all filter capabilities:
   - Toggle component visibility (all 5 components)
   - Toggle causation type filters (all 4 types)
   - Toggle display options (labels, links, temporal paths)

3. **Configuration Update Test** - Test config hot-reload:
   - Update neural system parameters (learning rate, batch size, epsilon decay)
   - Update feedback controller knobs (mutation rate, new edge rate, clustering bias, quantum pruning)
   - Update network settings (max connections, max organisms)
   - Enable VP diagnostics
   - Test rollback functionality

4. **Diagnostic Endpoints Test** - Query all diagnostic endpoints:
   - VP history
   - Network trends
   - Memory breakdown
   - Event throughput
   - Breath cycles
   - VP diagnostics breakdown
   - VP component decomposition
   - VP stabilization history
   - VP adaptive thresholds

5. **System State Analysis** - Analyze current system state:
   - Check all three systems (Reality Simulator, Explorer, Djinn Kernel)
   - Analyze neural system status
   - Check phase synchronization
   - Identify any anomalies or issues

6. **Snapshot System Test** - Test snapshot capabilities:
   - Configure snapshot capture settings
   - Verify snapshot gallery functionality
   - Test vision analysis integration

### Report Format:

Please provide a comprehensive report with:

1. **Test Execution Summary**
   - List all tests performed
   - Success/failure status for each
   - Any errors encountered

2. **Capability Verification**
   - Which capabilities worked correctly
   - Which capabilities had issues
   - Specific error messages if any

3. **System Health Assessment**
   - Current state of all three systems
   - Neural system integration status
   - Any critical issues identified

4. **Configuration Changes Made**
   - List all config updates attempted
   - Which succeeded and which failed
   - Current configuration state

5. **Visualization Changes Made**
   - List all visualization settings adjusted
   - Before/after values where applicable
   - Visual impact assessment

6. **Diagnostic Data Summary**
   - Key metrics from all diagnostic endpoints
   - Trends and patterns identified
   - Anomalies detected

7. **Recommendations**
   - Immediate actions needed
   - Configuration optimizations
   - System improvements

### Test Execution Instructions:

- Perform tests systematically, one category at a time
- Use the appropriate command formats ([[VIZ_SETTINGS_UPDATE]], [[CONFIG_UPDATE]], [[GRAPH_FILTER_UPDATE]], etc.)
- Document each test with before/after states
- If a test fails, note the error and continue with other tests
- Group related changes together (e.g., all color changes in one batch)
- Use correlation_ids for config updates to track them in the config actions log

### Expected Output:

A detailed, structured report showing:
- ✅ What works
- ⚠️ What has issues
- 🔧 What needs fixing
- 📊 Current system metrics
- 💡 Recommendations for optimization

Please execute all tests and provide the comprehensive report.

---

**Alternative Shorter Version:**

"Please perform a full system capability test. Test all visualization settings (40+), graph filters, config updates, diagnostic endpoints, and system state analysis. Provide a detailed report showing what works, what doesn't, current metrics, and recommendations. Use appropriate command formats and document all changes."

