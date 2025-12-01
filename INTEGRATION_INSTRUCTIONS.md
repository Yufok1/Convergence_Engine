# 📋 CURSOR INSTRUCTIONS: Integrate Linguistic Knowledge Base

## Overview
This guide will integrate the comprehensive linguistic knowledge base (326 concepts, 1395 relations, 106 n-gram patterns) into the Butterfly System's language learning system.

---

## STEP 1: Copy Files from Integration to Data Folder

**In Cursor Terminal, run these PowerShell commands:**

```powershell
# Navigate to project root
cd d:\ZZZZZ

# Copy JSON files to data folder
Copy-Item "integration\linguistic_concepts.json" -Destination "data\" -Force
Copy-Item "integration\semantic_relations.json" -Destination "data\" -Force
Copy-Item "integration\ngram_patterns.json" -Destination "data\" -Force

# Copy import script to language folder
Copy-Item "integration\import_knowledge_base.py" -Destination "reality_simulator\language\" -Force
```

**Expected Result:** Files copied successfully (no errors)

---

## STEP 2: Verify Files Exist

**In Cursor Terminal, verify files are in place:**

```powershell
# Check files exist
Test-Path "data\linguistic_concepts.json"
Test-Path "data\semantic_relations.json"
Test-Path "data\ngram_patterns.json"
Test-Path "reality_simulator\language\import_knowledge_base.py"
```

**Expected Result:** All commands return `True`

---

## STEP 3: Test the Import Script (Optional - Verify It Works)

**In Cursor Terminal, test the import script:**

```powershell
cd d:\ZZZZZ
python -m reality_simulator.language.import_knowledge_base
```

**Expected Output:**
```
============================================================
IMPORTING LINGUISTIC KNOWLEDGE BASE
============================================================
INFO - Loaded 326 concepts from data\linguistic_concepts.json
INFO - Loaded 1395 relations from data\semantic_relations.json
INFO - Loaded 106 n-gram patterns from data\ngram_patterns.json
============================================================
IMPORT COMPLETE
  Concepts: 326
  Relations: 1395
  Patterns: 106
  Total in web: 376 concepts, 1595 relations
============================================================

Test situational awareness: ['thrive', 'flourish', 'social', 'cooperate', ...]
```

**Note:** This test creates a temporary knowledge web. The real integration happens in Step 4.

---

## STEP 4: Update Language Teacher to Load Knowledge Base on Startup

**In Cursor, open the file:**
`reality_simulator\language\language_teacher.py`

**Find the `__init__` method of the `LanguageTeacher` class (around line 228-275)**

**Look for this section (around line 269-274):**
```python
self.use_knowledge_web = teacher_config.get('use_knowledge_web', True)
if self.use_knowledge_web:
    self.knowledge_web = LinguisticKnowledgeWeb(config)
    logger.info(f"[LANGUAGE_TEACHER] Linguistic Knowledge Web enabled ({len(self.knowledge_web.concepts)} concepts)")
else:
    self.knowledge_web = None
    logger.warning("[LANGUAGE_TEACHER] Knowledge web disabled in config")
```

**Replace that entire section with this (adds import after creation):**
```python
self.use_knowledge_web = teacher_config.get('use_knowledge_web', True)
if self.use_knowledge_web:
    self.knowledge_web = LinguisticKnowledgeWeb(config)
    
    # Load comprehensive knowledge base from JSON files
    try:
        from .import_knowledge_base import KnowledgeBaseImporter
        from pathlib import Path
        
        data_dir = Path(__file__).parent.parent.parent / "data"
        if data_dir.exists():
            importer = KnowledgeBaseImporter(data_dir=str(data_dir))
            import_results = importer.import_all(self.knowledge_web, grammar_learner=None)
            logger.info(f"[LANGUAGE_TEACHER] Knowledge base loaded: {import_results['concepts']} concepts, "
                       f"{import_results['relations']} relations, {import_results['patterns']} patterns")
            logger.info(f"[LANGUAGE_TEACHER] Total in web: {import_results['total_concepts']} concepts, "
                       f"{import_results['total_relations']} relations")
        else:
            logger.warning(f"[LANGUAGE_TEACHER] Data directory not found: {data_dir}. Skipping knowledge base import.")
    except ImportError as e:
        logger.warning(f"[LANGUAGE_TEACHER] Could not import knowledge base: {e}. Using base knowledge only.")
    except Exception as e:
        logger.warning(f"[LANGUAGE_TEACHER] Error loading knowledge base: {e}. Using base knowledge only.")
    
    logger.info(f"[LANGUAGE_TEACHER] Linguistic Knowledge Web enabled ({len(self.knowledge_web.concepts)} concepts)")
else:
    self.knowledge_web = None
    logger.warning("[LANGUAGE_TEACHER] Knowledge web disabled in config")
```

**Save the file** (Ctrl+S)

---

## STEP 5: Verify Integration

**In Cursor Terminal, run the unified system:**

```powershell
cd d:\ZZZZZ
python unified_entry.py --no-viz
```

**Look for these log messages in the output:**
```
[LANGUAGE_TEACHER] Knowledge base loaded: 326 concepts, 1395 relations, 106 patterns
[LANGUAGE_TEACHER] Total in web: 376 concepts, 1595 relations
[LANGUAGE_TEACHER] Linguistic Knowledge Web enabled (376 concepts)
```

**Expected Result:** You should see the knowledge base loaded successfully.

**Press Ctrl+C to stop the simulation** after verifying the logs.

---

## STEP 6: Test Butterfly Chat

**In Cursor Terminal, start the full system:**

```powershell
cd d:\ZZZZZ
python unified_entry.py
```

**Wait for the system to start, then:**

1. **Open your browser** to `http://localhost:5000`
2. **Navigate to the CRA Panel** (if not already visible)
3. **Click the "🦋 Butterfly Chat" tab**
4. **Try these test messages:**

   - `"hello"`
   - `"can you help me?"`
   - `"I am strong"`
   - `"we thrive together"`

**Expected Results:**

**Before Integration:**
- User: `"hello"`
- Organism: `"thrive stable grow"` ← Word salad

**After Integration:**
- User: `"hello"`  
- Organism: `"I thrive with others"` ← Actual sentence with pronouns and prepositions!

---

## STEP 7: Verify Vocabulary Expansion

**Check the logs for these indicators:**

✅ **Knowledge base loaded:** Look for log messages showing concept/relation counts  
✅ **More varied responses:** Organisms should generate more grammatically structured responses  
✅ **Function words appearing:** Look for pronouns ("I", "we", "you"), prepositions ("with", "and", "but"), articles ("the", "a")  
✅ **Better sentence structure:** Responses should have subject-verb-object patterns

**In the web UI, check the Debug Panel:**
- Open Butterfly Chat
- Send a message
- Check the Debug Panel (right side of chat)
- Look for more detailed word associations and situational awareness

---

## TROUBLESHOOTING

### Issue: Import Script Not Found

**Error:** `ModuleNotFoundError: No module named 'reality_simulator.language.import_knowledge_base'`

**Solution:**
```powershell
# Verify file exists
Test-Path "reality_simulator\language\import_knowledge_base.py"

# If missing, copy it again
Copy-Item "integration\import_knowledge_base.py" -Destination "reality_simulator\language\" -Force
```

### Issue: JSON Files Not Found

**Error:** `Concepts file not found: data\linguistic_concepts.json`

**Solution:**
```powershell
# Verify files exist
Test-Path "data\linguistic_concepts.json"
Test-Path "data\semantic_relations.json"
Test-Path "data\ngram_patterns.json"

# If missing, copy them again
Copy-Item "integration\linguistic_concepts.json" -Destination "data\" -Force
Copy-Item "integration\semantic_relations.json" -Destination "data\" -Force
Copy-Item "integration\ngram_patterns.json" -Destination "data\" -Force
```

### Issue: JSON Validation Errors

**Error:** `JSONDecodeError` or similar

**Solution:**
```powershell
# Validate JSON files
python -c "import json; json.load(open('data/linguistic_concepts.json')); print('Concepts JSON: OK')"
python -c "import json; json.load(open('data/semantic_relations.json')); print('Relations JSON: OK')"
python -c "import json; json.load(open('data/ngram_patterns.json')); print('Patterns JSON: OK')"
```

### Issue: Import Works But No Improvement in Responses

**Possible Causes:**
1. **Knowledge web disabled in config:** Check `config.json`:
   ```json
   {
     "neural": {
       "language_model": {
         "teacher": {
           "use_knowledge_web": true
         },
         "knowledge_web": {
           "enabled": true
         }
       }
     }
   }
   ```

2. **Language model not enabled:** Check `config.json`:
   ```json
   {
     "neural": {
       "language_model": {
         "enabled": true
       }
     }
   }
   ```

3. **Neural system not enabled:** Check `config.json`:
   ```json
   {
     "neural": {
       "enabled": true
     }
   }
   ```

### Issue: Module Import Error in Language Teacher

**Error:** `ImportError: cannot import name 'KnowledgeBaseImporter'`

**Solution:**
- Make sure `import_knowledge_base.py` is in `reality_simulator\language\` folder
- Check that the import statement uses relative import: `from .import_knowledge_base import KnowledgeBaseImporter`
- Verify the file has no syntax errors:
  ```powershell
  python -m py_compile reality_simulator\language\import_knowledge_base.py
  ```

---

## VERIFICATION CHECKLIST

After completing all steps, verify:

- [ ] Files copied to `data\` folder (3 JSON files)
- [ ] Import script copied to `reality_simulator\language\`
- [ ] Language teacher code updated with import logic
- [ ] System starts without errors
- [ ] Logs show "Knowledge base loaded" message
- [ ] Logs show total concept/relation counts (376+ concepts, 1595+ relations)
- [ ] Butterfly Chat accessible in web UI
- [ ] Organisms generate more varied responses
- [ ] Function words appear in responses
- [ ] Sentence structure improved

---

## EXPECTED RESULTS SUMMARY

**Before Integration:**
- ~50-100 base concepts in knowledge web
- Simple word associations
- Word salad responses: `"thrive stable grow"`

**After Integration:**
- **376+ concepts** in knowledge web
- **1595+ semantic relations**
- **106 n-gram patterns** for grammar
- Structured responses: `"I thrive with others"`
- Function words: pronouns, prepositions, articles
- Better situational awareness

---

## NEXT STEPS (Optional)

After successful integration:

1. **Monitor Performance:** Check if knowledge base loading impacts startup time
2. **Tune Configuration:** Adjust `max_concepts` in config if needed
3. **Expand Vocabulary:** Add more domain-specific words if needed
4. **Test Grammar:** Verify n-gram patterns improve sentence structure

---

**That's it! Just follow these steps in order in Cursor's terminal and editor.** 🚀

