# 🦋 Language System Visualization Strategy

**Problem:** How to visualize language associations in the causation graph without cluttering it, since organisms already exist as nodes and words are associations, not separate entities.

**Solution:** **Hybrid Multi-Layer Approach**

---

## 🎯 Core Principle

**"Language is a property of relationships, not a separate entity"**

- Organisms are nodes (already exist)
- Words are associations between organisms and concepts
- Language connections are semantic/causal relationships
- Language events are temporal snapshots of vocabulary growth

---

## 📊 Visualization Layers

### Layer 1: Language Events as Nodes (Primary)

**Show language events as regular causation graph nodes:**

- `vocabulary_growth` → Node with component="language"
- `organism_communication` → Node with component="language"  
- `neural_language_training` → Node with component="neural" (already exists)
- `butterfly_chat_message` → Node with component="butterfly_chat"
- `butterfly_chat_response` → Node with component="butterfly_chat"

**Styling:**
- Component color: `#9B59B6` (purple) for language events
- Component color: `#E91E63` (pink) for butterfly_chat events
- Node shape: Diamond for language events (distinct from circles)
- Tooltip shows: word count, vocabulary size, communication details

**Causation Links:**
- `vocabulary_growth` → `organism_communication` (words enable communication)
- `organism_communication` → `neural_language_training` (communication trains language)
- `butterfly_chat_message` → `butterfly_chat_response` (user message causes response)

---

### Layer 2: Linguistic Edge Highlighting (Secondary)

**Highlight edges between organisms that have linguistic connections:**

**Detection:**
- Check if organisms share words in `language_anchors`
- Check if organisms have `LinguisticSubgraph` edges
- Check if organisms participated in `organism_communication` events

**Styling:**
- Edge color: `#9B59B6` (purple) for linguistic connections
- Edge style: Dashed line (distinct from solid causation links)
- Edge width: Thicker for stronger linguistic associations
- Edge opacity: Based on word overlap strength

**Implementation:**
```javascript
function isLinguisticEdge(link, allNodes, languageAnchors) {
    const sourceId = link.source.id || link.source;
    const targetId = link.target.id || link.target;
    
    // Check if organisms share words
    const sourceWords = getOrganismWords(sourceId, languageAnchors);
    const targetWords = getOrganismWords(targetId, languageAnchors);
    const sharedWords = intersection(sourceWords, targetWords);
    
    return sharedWords.length > 0;
}
```

---

### Layer 3: Node Attributes (Metadata)

**Show words as metadata on organism nodes:**

**Tooltip/Hover:**
- When hovering organism node, show:
  - Associated words (from `node_word_associations`)
  - Word count
  - Most frequent words
  - Communication activity

**Node Badge:**
- Small badge on organism nodes showing word count
- Color intensity based on vocabulary size
- Optional: Show top 3 words as text labels

**Implementation:**
```javascript
function getOrganismLanguageInfo(nodeId, contextMemory) {
    const words = contextMemory.node_word_associations[nodeId] || [];
    const wordCount = words.length;
    const topWords = words.slice(0, 3).join(', ');
    return {
        wordCount,
        topWords,
        allWords: words
    };
}
```

---

### Layer 4: Illumination System (Deep Analysis)

**Language-specific illumination queries:**

1. **`illumination_search` with language filters:**
   - `component:language` - Find all language events
   - `word:explore` - Find organisms/events involving word "explore"
   - `vocabulary_size:>50` - Find events with vocabulary > 50 words

2. **`illumination_explain` for language events:**
   - Explain why vocabulary grew
   - Explain why organisms communicated
   - Explain language causation patterns

3. **`illumination_root_causes` for language:**
   - Trace back: What caused organism to learn word X?
   - Trace back: What behaviors led to vocabulary growth?

4. **`illumination_impact` for language:**
   - Forward trace: How did vocabulary growth affect communication?
   - Forward trace: How did communication affect organism fitness?

5. **New Query: `illumination_language_network`:**
   - Show semantic network of words
   - Show organism-word associations
   - Show word-word co-occurrence patterns

---

### Layer 5: Language Layer Toggle (Optional Overlay)

**Separate overlay for detailed language visualization:**

**Toggle Button:** "Show Language Network"

**When Enabled:**
- Show word nodes (smaller, different shape)
- Show organism-word edges (which words organisms know)
- Show word-word edges (semantic relationships, co-occurrence)
- Show linguistic subgraph edges (protected connections)

**Styling:**
- Word nodes: Small squares, color by frequency
- Organism-word edges: Thin, light purple
- Word-word edges: Medium, darker purple
- Linguistic edges: Thick, bright purple

**Filtering:**
- Show only top N words (by frequency)
- Show only words with >X associations
- Show only active words (used recently)

---

## 🔧 Implementation Plan

### Phase 1: Event Nodes (Immediate)

1. **Add language event detection in causation explorer**
   - Detect `vocabulary_growth`, `organism_communication` events
   - Mark with `component: "language"` or `component: "butterfly_chat"`
   - Style with purple/pink colors

2. **Add language causation links**
   - Link vocabulary growth → communication events
   - Link communication → training events
   - Link chat message → chat response

3. **Add component filter for "language"**
   - Filter toggle in UI
   - Show/hide language events

### Phase 2: Edge Highlighting (Next)

1. **Detect linguistic connections**
   - Check `language_anchors` for shared words
   - Check `LinguisticSubgraph` for protected edges
   - Mark edges as linguistic

2. **Style linguistic edges**
   - Purple color, dashed line
   - Thicker width for stronger associations
   - Tooltip shows shared words

3. **Add edge type filter**
   - Toggle for "linguistic edges"
   - Show/hide linguistic connections

### Phase 3: Node Attributes (Then)

1. **Add language metadata to organism nodes**
   - Store word associations in node data
   - Show in tooltip on hover
   - Optional badge showing word count

2. **Add word frequency visualization**
   - Color intensity based on vocabulary size
   - Size based on communication activity

### Phase 4: Illumination Integration (Finally)

1. **Add language queries to illumination system**
   - `search` with language filters
   - `explain` for language events
   - `root_causes` for language patterns
   - `impact` for language effects

2. **Add `illumination_language_network` query**
   - Semantic network visualization
   - Word-organism associations
   - Word-word relationships

### Phase 5: Language Layer Toggle (Optional)

1. **Add overlay toggle**
   - "Show Language Network" button
   - Separate visualization layer

2. **Implement word nodes**
   - Create word nodes from vocabulary
   - Connect to organisms
   - Show semantic relationships

---

## 🎨 Visual Design

### Colors

- **Language Events:** `#9B59B6` (purple)
- **Butterfly Chat:** `#E91E63` (pink)
- **Linguistic Edges:** `#9B59B6` (purple, dashed)
- **Word Nodes:** `#8E44AD` (darker purple)

### Shapes

- **Language Events:** Diamond (◇)
- **Organisms:** Circle (○)
- **Word Nodes:** Square (□)
- **Regular Events:** Circle (○)

### Edge Styles

- **Causation Links:** Solid line
- **Linguistic Edges:** Dashed line
- **Word-Organism Edges:** Dotted line (in overlay)

---

## 📋 Configuration

### New Config Options

```json
{
  "causation": {
    "enable_language_causations": true,  // Already exists
    "language_visualization": {
      "show_language_events": true,
      "highlight_linguistic_edges": true,
      "show_word_metadata": true,
      "language_layer_enabled": false  // Overlay toggle
    }
  }
}
```

### CRA Controls

- `causation.language_visualization.show_language_events`
- `causation.language_visualization.highlight_linguistic_edges`
- `causation.language_visualization.show_word_metadata`
- `causation.language_visualization.language_layer_enabled`

---

## 🎯 Recommended Approach

**Start with Phase 1 + Phase 2:**

1. **Show language events as nodes** (clear, simple)
2. **Highlight linguistic edges** (shows relationships without clutter)
3. **Add node metadata** (tooltip shows words on hover)

**Skip Phase 5 (overlay) initially** - too complex, can add later if needed.

**Use Illumination System** for deep analysis - keeps main graph clean.

---

## ✅ Benefits

1. **Non-intrusive:** Language doesn't clutter main graph
2. **Informative:** Shows language relationships clearly
3. **Flexible:** Can toggle layers on/off
4. **Scalable:** Works with any vocabulary size
5. **Integrated:** Language events appear in causation chain

---

**Status:** Ready for implementation! 🦋✨

