# 🔧 Troubleshooting Guide

**Common issues and solutions for The Butterfly System**

---

## 🚨 Critical Issues

### Pre-Flight Checks Fail

**Problem:** System won't start due to pre-flight check failures

**Solutions:**
```bash
# Missing dependencies
pip install numpy networkx matplotlib

# Missing optional (Windows)
pip install pywin32

# Check Python version
python --version  # Should be 3.8+
```

### Explorer Won't Initialize

**Problem:** `ModuleNotFoundError: No module named 'win32job'`

**Solution:**
```bash
pip install pywin32
```

**Note:** This is Windows-only. On Linux/Mac, Explorer will run without it (some features disabled).

### Reality Simulator Won't Initialize

**Problem:** `Reality Simulator failed to initialize`

**Solutions:**
1. Check `config.json` exists in root directory
2. Verify `config.json` is valid JSON:
   ```bash
   python -c "import json; json.load(open('config.json'))"
   ```
3. Check that required directories exist:
   - `reality_simulator/`
   - `data/`

### Djinn Kernel Won't Initialize

**Problem:** `Djinn Kernel not available` or import errors

**Solutions:**
1. Check `kernel/` directory exists
2. Verify kernel modules are present:
   ```bash
   ls kernel/*.py
   ```
3. Check for import path issues (kernel should be importable)

### Butterfly Chat Issues

**Problem:** Empty responses, errors, or no learning

**Solutions:**
- See [Butterfly Chat Troubleshooting](#-butterfly-chat-issues) section below
- Check debug panel for detailed error information
- Verify vocabulary is growing (check for "Learned new word" in logs)

---

## ⚠️ Warnings

### Low System Memory

**Problem:** Pre-flight check warns about low memory

**Solutions:**
- Close other applications
- Run without visualization: `python unified_entry.py --no-viz`
- Reduce simulation parameters in `config.json`:
  - Lower `network.max_organisms`
  - Lower `lattice.particles`
  - Lower `evolution.population_size`

### Optional Dependencies Missing

**Problem:** Warnings about optional dependencies

**Solutions:**
- These are warnings, not errors
- System will run with reduced functionality
- Install if you need full features:
  ```bash
  pip install pywin32  # Windows process isolation
  pip install psutil   # System monitoring
  ```

---

## 🎨 Visualization Issues

### Visualization Won't Open

**Problem:** `Visualization error: tkinter not available`

**Solutions:**
- **Windows:** Usually comes with Python
- **Linux:** `sudo apt-get install python3-tk`
- **Mac:** Usually comes with Python
- **Workaround:** Run with `--no-viz` flag

### Visualization Freezes

**Problem:** GUI becomes unresponsive

**Solutions:**
1. Close and restart visualization
2. Run without visualization: `--no-viz`
3. Reduce update frequency in code (if modifying)

### Visualization Shows No Data

**Problem:** Panels are empty or show zeros

**Solutions:**
1. Check that systems are actually running:
   ```bash
   python unified_entry.py --check-only
   ```
2. Verify Reality Simulator initialized:
   - Look for `[Explorer] ✅ Reality Simulator initialized`
3. Check log files in `data/logs/` for errors

---

## 📊 Logging Issues

### Log Files Not Created

**Problem:** No log files in `data/logs/`

**Solutions:**
1. Check directory exists:
   ```bash
   mkdir -p data/logs
   ```
2. Check write permissions
3. Verify `StateLogger` initialized (check console output)

### Log Files Too Large

**Problem:** Log files growing very large

**Solutions:**
- Logs are automatically trimmed (last 10,000 entries)
- Manually clean old logs:
  ```bash
  rm data/logs/*.log
  ```
- Add to `.gitignore` (already done)

---

## 🔌 Integration Issues

### Systems Not Connected

**Problem:** Reality Simulator or Djinn Kernel not responding

**Solutions:**
1. Check initialization messages:
   - `[Explorer] ✅ Reality Simulator initialized`
   - `[Explorer] ✅ Djinn Kernel initialized`
2. Verify imports work:
   ```bash
   python -c "from reality_simulator.main import RealitySimulator; print('OK')"
   python -c "from kernel.utm_kernel_design import UTMKernel; print('OK')"
   ```
3. Check path setup in `explorer/main.py`

### Breath Not Driving Systems

**Problem:** Systems run independently, not driven by breath

**Solutions:**
1. Verify breath-driven code in `explorer/main.py` lines 289, 312
2. Check that `run_genesis_phase()` is being called
3. Verify systems are initialized in `BiphasicController.__init__()`

---

## 🐛 Runtime Errors

### Import Errors

**Problem:** `ModuleNotFoundError` or `ImportError`

**Solutions:**
1. Check Python path:
   ```bash
   python -c "import sys; print(sys.path)"
   ```
2. Verify you're running from project root:
   ```bash
   pwd  # Should be Reality_Sim-main/
   ```
3. Check relative imports in code

### Configuration Errors

**Problem:** `KeyError` or `TypeError` in config

**Solutions:**
1. Validate `config.json`:
   ```bash
   python -c "import json; json.load(open('config.json'))"
   ```
2. Check required keys exist
3. Verify value types match expected types

### Memory Errors

**Problem:** `MemoryError` or system runs out of memory

**Solutions:**
1. Reduce simulation size in `config.json`
2. Run without visualization: `--no-viz`
3. Close other applications
4. Check system memory: `python unified_entry.py --check-only`

---

## 🦋 Butterfly Chat Issues

### Empty Responses from Organisms

**Symptoms:**
- Chat shows "[Confidence: X%, Organisms: Y, Strategy: Z]" but no actual response text
- Debug logs show `word_count: 0` for most organisms

**Causes:**
- Vocabulary is too small (only special tokens)
- Generated token IDs don't map to vocabulary words
- Organisms haven't learned words yet

**Solutions:**
1. **Wait for Vocabulary Growth**: Organisms learn words from interactions
   - Send a few messages to help vocabulary grow
   - Check "Logs" tab for "Learned new word" entries
2. **Check Debug Panel**: 
   - Open "Causation Trail" tab to see token generation
   - Check "Errors" tab for generation issues
3. **Verify Vocabulary**: 
   - Check that vocabulary has words beyond special tokens
   - Look for vocabulary_growth events in causation graph

### "integer modulo by zero" Error

**Symptoms:**
- Error in debug logs: `ZeroDivisionError: integer modulo by zero`
- All organisms fail to generate responses

**Cause:**
- Vocabulary only has special tokens (vocab_size = 5)
- Token mapping tries to divide by zero

**Solution:**
- ✅ **FIXED**: System now handles empty vocabularies safely
- Restart the system - fix is already applied
- Vocabulary will grow as organisms learn

### Event ID Collision

**Symptoms:**
- All events in debug logs have the same event ID
- Illumination Engine can't distinguish between events

**Cause:**
- Events created at same timestamp get identical IDs

**Solution:**
- ✅ **FIXED**: Event IDs now include counter for uniqueness
- Format: `evt_{timestamp}_{counter}`
- Restart system to apply fix

### No Learning from Interactions

**Symptoms:**
- Organisms don't improve over time
- No experience storage in debug logs

**Causes:**
- Organisms don't have experience buffers
- Neural system not enabled
- Experience storage failing silently

**Solutions:**
1. **Check Neural System**: Ensure `config.json` has `"neural": {"enabled": true}`
2. **Check Debug Logs**: Look for "Stored chat experience" entries
3. **Verify Experience Buffers**: Organisms need `experience_buffer` attribute
4. **Check Errors Tab**: Look for "EXPERIENCE_STORAGE_ERROR" entries

### Vocabulary Not Growing

**Symptoms:**
- Vocabulary size stays at 5 (only special tokens)
- No new words added from interactions

**Causes:**
- Vocabulary learning not triggered
- Words already in vocabulary
- Learning mechanism not active

**Solutions:**
1. **Check Debug Logs**: Look for "Learned new word" entries
2. **Send Diverse Messages**: Use different words to trigger learning
3. **Check Vocabulary**: Verify words are being added via `vocabulary.add_word()`
4. **Monitor Events**: Check for `vocabulary_growth` events in causation graph

### Illumination Buttons Not Working

**Symptoms:**
- Clicking Root Causes/Impact/Explain does nothing
- No results appear in debug panel

**Causes:**
- Event ID not captured
- Illumination Engine not initialized
- API endpoint errors

**Solutions:**
1. **Check Event IDs**: Verify causation trail steps have `event_id` field
2. **Check Console**: Look for JavaScript errors in browser console
3. **Verify API**: Check that `/api/events/<event_id>/root-causes` works
4. **Check Network State**: Ensure event emitter is available

---

## 🔍 Debugging

### Enable Verbose Logging

**Problem:** Need more detailed error information

**Solutions:**
1. Check log files in `data/logs/`
2. Run with Python debugger:
   ```bash
   python -m pdb unified_entry.py
   ```
3. Add print statements in code (temporary)

### Check System State

**Problem:** Need to verify system is working

**Solutions:**
1. Run pre-flight checks:
   ```bash
   python unified_entry.py --check-only
   ```
2. Check log files:
   ```bash
   tail -f data/logs/system.log
   ```
3. Verify systems initialized (check console output)

### Test Individual Systems

**Problem:** Need to test systems separately

**Solutions:**
```bash
# Test Explorer
cd explorer && python main.py

# Test Reality Simulator
python reality_simulator/main.py --mode observer

# Test integration
cd explorer && python test_integration.py
```

---

## 📞 Getting Help

### Check Documentation

1. **[DOCUMENTATION_HUB.md](./DOCUMENTATION_HUB.md)** - All documentation
2. **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - Quick commands
3. **[UNIFIED_SYSTEM_GUIDE.md](./UNIFIED_SYSTEM_GUIDE.md)** - Complete guide

### Common Solutions Summary

| Problem | Solution |
|---------|----------|
| Import errors | `pip install numpy networkx matplotlib` |
| win32job missing | `pip install pywin32` (Windows) |
| Config errors | Validate `config.json` |
| Memory issues | Run with `--no-viz` |
| Visualization issues | Install tkinter or use `--no-viz` |
| Systems not connecting | Check initialization messages |

---

## 🎯 Still Having Issues?

1. **Check logs:** `data/logs/system.log`
2. **Run checks:** `python unified_entry.py --check-only`
3. **Verify setup:** All dependencies installed
4. **Check paths:** Running from project root
5. **Review docs:** [DOCUMENTATION_HUB.md](./DOCUMENTATION_HUB.md)

**The butterfly will fly once all systems are properly initialized.** 🦋

