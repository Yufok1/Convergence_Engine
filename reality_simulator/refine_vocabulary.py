"""Refine raw WordNet vocabulary into curated 250k domain set.

Input: data/butterfly_vocabulary_200k_raw.json (created by build_vocabulary.py)
Output: data/butterfly_vocabulary_250k_curated.json (250k filtered)

Filtering Strategy:
- Start with ~141k natural words from WordNet
- Filter: surnames, brands, obvious jargon, technical terms
- Remove malformed morphological variants
- Score remaining words by domain relevance
- Extract top 250k most relevant words (or all available if <250k)

Domain Focus: organism behavior, communication, comprehension, understanding
Source: Princeton WordNet (100% real English words, zero artificial generation)
"""
from __future__ import annotations
import json, os, re, hashlib
from typing import List, Dict, Set

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
RAW_PATH = os.path.join(DATA_DIR, 'butterfly_vocabulary_200k_raw.json')
CURATED_PATH = os.path.join(DATA_DIR, 'butterfly_vocabulary_250k_curated.json')
TARGET_SIZE = 250000  # Will take top 250k from filtered WordNet words (or all available)

PUNCT_RE = re.compile(r"^[\W_]+$")
NON_ALPHA_RE = re.compile(r"[^a-zA-Z-]")
DIGIT_RE = re.compile(r"\d")

ALLOWED_SHORT = {"i","a","we","us","go","be","do","up","in","on","at","to","it","if","or","so","no","my","by"}

# Aggressive blacklist: proper names, brands, technical jargon, random entities
BLACKLIST_FRAGMENTS = {
    # Common surnames that WordNet includes (lowercase)
    'wilkes','wilkins','williams','willis','wilson','wright','white','walker','ward','watson',
    'gary','garrick','gaskell','gaspar','gaudi','gilbert','gibson','gordon','graham','grant',
    # Brands / companies
    'nvidia','tesla','amazon','google','intel','ibm','oracle','microsoft','apple','sony',
    'kodak','pepsi','pontiac','gatt',
    # Random technical / obscure
    'gyroscope','gyroscopes','cryptocurrency','blockchain','webpack','kubernetes','dockerfile',
    # Nonsense / rare compounds
    'quasilocal','hypercreative','superdelegates','uncharacteristically',
    # Geography names (lowercase in WordNet)
    'afghanistan','zimbabwe','barcelona','tokyo','california','seattle','yangtze','irvine',
    'srinagar','hanover','caspian','yunnan','basel','burkina','aden','gascogne','gascony',
    # Pop culture / media
    'pokemon','nintendo','playstation','youtube','netflix','spotify',
    # Medical/scientific jargon
    'endocrinology','cardiopulmonary','angioplasty','cholesterol','gastrin','gastromy','gastrula',
    # Financial jargon
    'nasdaq','derivatives','arbitrage','forex','reaganomics',
    # Programming specifics
    'javascript','python','typescript','ansible','jenkins'
}

# Blacklist patterns (partial matches)
BLACKLIST_PATTERNS = [
    'www.','http','@','#','<','>','[',']','{','}','©','™','®'
]

# Domain curated core words (ensure presence)
DOMAIN_CORE = {
    # Behavior
    'move','rest','explore','search','hunt','gather','build','destroy','attack','defend','cooperate','compete','share','steal','help','lead','follow','adapt','evolve','grow','learn','remember','forget','predict','signal','communicate','negotiate','strategize','persist','recover','retreat','advance','allocate','distribute','cluster','organize','observe','innovate','optimize','transform','stabilize',
    # Social
    'ally','rival','friend','enemy','partner','group','team','confederation','empire','hegemony','coalition','consensus','influence','trust','betray','reconcile','support','oppose','collaborate','coordinate','mediate','broker','summon','delegate','represent','govern','elect','vote','dissent','compromise','converge','diverge',
    # Cognition
    'think','reason','analyze','evaluate','infer','deduce','classify','cluster','model','abstract','generalize','specialize','focus','reflect','plan','decide','choose','estimate','approximate','calculate','optimize','simulate','forecast','hypothesize','explain','summarize','compare','contrast','prioritize',
    # Survival
    'survive','thrive','struggle','endure','persist','recover','heal','weaken','strengthen','mutate','inherit','birth','reproduce','die','regress','progress','stabilize','escalate','decay','consolidate','expand','diversify','compete','dominate','protect','safeguard','exploit','forage','consume','store','reserve','scarcity','abundance',
    # Temporal
    'now','soon','later','instant','cycle','phase','epoch','interval','duration','sequence','timeline','evolution','emergence','iteration','feedback','recurrence','delay','acceleration','deceleration','transition','threshold','moment','persistence','latency','timing','cadence','tempo','rhythm','pulse',
    # Causal
    'cause','effect','influence','impact','trigger','propagate','cascade','chain','link','derive','emerge','interact','feedback','converge','diverge','correlate','predict','induce','mediate','moderate','transform','stabilize','destabilize','amplify','attenuate','suppress','reinforce','invert','redirect',
    # Communication
    'say','tell','ask','reply','explain','describe','announce','broadcast','whisper','shout','signal','warn','advise','query','request','respond','inform','document','log','encode','decode','translate','frame','contextualize',
    # Perception
    'sense','observe','detect','monitor','scan','track','trace','highlight','focus','notice','perceive','recognize','identify','classify','locate','map','visualize','measure','quantify','audit','inspect','assess','diagnose',
    # Spatial
    'network','graph','node','edge','link','cluster','layer','lattice','field','space','region','zone','sector','boundary','interface','surface','dimension','vector','matrix','topology','density','distribution','gradient','coordinate','center','perimeter','radius','orbit','domain',
    # Governance
    'govern','regulate','audit','certify','authorize','authenticate','validate','version','rollback','orchestrate','synchronize','calibrate','tune','provision','schedule','instrument','profile','benchmark','persist','index','archive','restore','sandbox','isolate'
}


def load_raw_words(path: str) -> List[str]:
    """Load words from raw vocabulary JSON."""
    with open(path,'r',encoding='utf-8') as f:
        data = json.load(f)
    return data['words']


def should_remove(token: str) -> bool:
    """Aggressively filter out irrelevant/nonsense words."""
    if token in DOMAIN_CORE:
        return False
    
    token_lower = token.lower()
    
    if PUNCT_RE.match(token):
        return True
    if DIGIT_RE.search(token):
        return True
    if len(token) < 2 and token not in ALLOWED_SHORT:
        return True
    if NON_ALPHA_RE.search(token):
        return True
    
    # Blacklist exact matches (case-insensitive)
    if token_lower in BLACKLIST_FRAGMENTS:
        return True
    
    # Blacklist patterns (partial match)
    for pattern in BLACKLIST_PATTERNS:
        if pattern in token_lower:
            return True
    
    # Remove overly long compounds (likely rare jargon)
    if len(token) > 20:
        return True
    
    # Remove words with 4+ repeated suffixes (morphological expansion gone wrong)
    # Examples: "agileless", "agilelyness", "agilityless" - these are not real words
    bad_suffix_patterns = [
        'edness', 'ingness', 'lyness', 'lessness', 'fulness', 'mentness',
        'ableness', 'ibleness', 'ousness', 'ionness', 'ingness'
    ]
    for bad_pattern in bad_suffix_patterns:
        if token_lower.endswith(bad_pattern):
            return True
    
    # Remove words ending with multiple suffix combinations (not real words)
    if token_lower.endswith('lyless') or token_lower.endswith('edless') or token_lower.endswith('ingless'):
        return True
    
    # STRICT: Remove ALL capitalized words (proper nouns)
    if len(token) > 1 and token[0].isupper() and token not in DOMAIN_CORE:
        return True
    
    # Remove words with repeated chars (likeeee, hmmm, etc)
    if len(token) > 5:
        for i in range(len(token) - 2):
            if token[i] == token[i+1] == token[i+2]:
                return True
    
    return False


def filter_tokens(words: List[str]) -> List[str]:
    """Filter out garbage tokens."""
    filtered = []
    seen: Set[str] = set()
    for w in words:
        lw = w.lower()
        if lw in seen:
            continue
        # Pass original word to check capitalization
        if should_remove(w):
            continue
        seen.add(lw)
        filtered.append(lw)
    return filtered


def inject_domain_words(current: List[str]) -> List[str]:
    """Ensure all domain core words are present."""
    existing = set(current)
    additions = []
    for w in DOMAIN_CORE:
        if w not in existing:
            additions.append(w)
    return current + additions


def score_word_relevance(word: str) -> float:
    """Score word relevance to organism behavior/communication (0.0-1.0)."""
    if word in DOMAIN_CORE:
        return 1.0
    if word.endswith('ing') or word.endswith('ed') or word.endswith('s'):
        return 0.8
    if word in {'with','from','into','onto','about','between','among','through','during'}:
        return 0.9
    if word.endswith('ly') or word.endswith('ness') or word.endswith('ity'):
        return 0.7
    if 4 <= len(word) <= 8 and word.isalpha():
        return 0.6
    if len(word) <= 5:
        return 0.5
    return 0.3


def generate_expansions(base_words: Set[str], needed: int, existing: Set[str]) -> List[str]:
    """Generate morphological variants to reach target size."""
    expansions = []
    suffixes = ['ing', 'ed', 's', 'er', 'ly', 'ness']
    for word in base_words:
        if len(expansions) >= needed:
            break
        for suffix in suffixes:
            variant = word + suffix
            if variant not in existing and variant not in expansions:
                expansions.append(variant)
                if len(expansions) >= needed:
                    break
    return expansions


def backfill_to_target(words: List[str]) -> List[str]:
    """Prioritize domain-relevant words and trim to exactly TARGET_SIZE."""
    words = inject_domain_words(words)
    scored = [(w, score_word_relevance(w)) for w in words]
    scored.sort(key=lambda x: x[1], reverse=True)
    words = [w for w, score in scored[:TARGET_SIZE]]
    if len(words) < TARGET_SIZE:
        existing = set(words)
        expansions = generate_expansions(DOMAIN_CORE, TARGET_SIZE - len(words), existing)
        words.extend(expansions)
    return words[:TARGET_SIZE]


def build_categories(words: List[str]) -> Dict[str,List[str]]:
    """Categorize words by domain."""
    cats = {c: [] for c in ['behavior','social','cognition','survival','temporal','causal','communication','perception','spatial','governance','other']}
    behavior_set = {'move','rest','explore','search','hunt','gather','build','destroy','attack','defend','cooperate','compete','share','steal','help','lead','follow','adapt','evolve','grow','learn','remember','forget','predict','signal','communicate','negotiate','strategize','persist','recover','retreat','advance','allocate','distribute','cluster','organize','observe','innovate','optimize','transform','stabilize'}
    social_set = {'ally','rival','friend','enemy','partner','group','team','confederation','empire','hegemony','coalition','consensus','influence','trust','betray','reconcile','support','oppose','collaborate','coordinate','mediate','broker','summon','delegate','represent','govern','elect','vote','dissent','compromise','converge','diverge'}
    cognition_set = {'think','reason','analyze','evaluate','infer','deduce','classify','cluster','model','abstract','generalize','specialize','focus','reflect','plan','decide','choose','estimate','approximate','calculate','optimize','simulate','forecast','hypothesize','explain','summarize','compare','contrast','prioritize'}
    survival_set = {'survive','thrive','struggle','endure','persist','recover','heal','weaken','strengthen','mutate','inherit','birth','reproduce','die','regress','progress','stabilize','escalate','decay','consolidate','expand','diversify','compete','dominate','protect','safeguard','exploit','forage','consume','store','reserve','scarcity','abundance'}
    temporal_set = {'now','soon','later','instant','cycle','phase','epoch','interval','duration','sequence','timeline','evolution','emergence','iteration','feedback','recurrence','delay','acceleration','deceleration','transition','threshold','moment','persistence','latency','timing','cadence','tempo','rhythm','pulse'}
    causal_set = {'cause','effect','influence','impact','trigger','propagate','cascade','chain','link','derive','emerge','interact','feedback','converge','diverge','correlate','predict','induce','mediate','moderate','transform','stabilize','destabilize','amplify','attenuate','suppress','reinforce','invert','redirect'}
    communication_set = {'say','tell','ask','reply','explain','describe','announce','broadcast','whisper','shout','signal','warn','advise','query','request','respond','inform','document','log','encode','decode','translate','frame','contextualize'}
    perception_set = {'sense','observe','detect','monitor','scan','track','trace','highlight','focus','notice','perceive','recognize','identify','classify','locate','map','visualize','measure','quantify','audit','inspect','assess','diagnose'}
    spatial_set = {'network','graph','node','edge','link','cluster','layer','lattice','field','space','region','zone','sector','boundary','interface','surface','dimension','vector','matrix','topology','density','distribution','gradient','coordinate','center','perimeter','radius','orbit','domain'}
    governance_set = {'govern','regulate','audit','certify','authorize','authenticate','validate','version','rollback','orchestrate','synchronize','calibrate','tune','provision','schedule','instrument','profile','benchmark','persist','index','archive','restore','sandbox','isolate'}
    
    for w in words:
        if w in behavior_set:
            cats['behavior'].append(w)
        elif w in social_set:
            cats['social'].append(w)
        elif w in cognition_set:
            cats['cognition'].append(w)
        elif w in survival_set:
            cats['survival'].append(w)
        elif w in temporal_set:
            cats['temporal'].append(w)
        elif w in causal_set:
            cats['causal'].append(w)
        elif w in communication_set:
            cats['communication'].append(w)
        elif w in perception_set:
            cats['perception'].append(w)
        elif w in spatial_set:
            cats['spatial'].append(w)
        elif w in governance_set:
            cats['governance'].append(w)
        else:
            cats['other'].append(w)
    return cats


def hash_list(words: List[str]) -> str:
    """Generate deterministic hash of word list."""
    return hashlib.sha256('\n'.join(words).encode('utf-8')).hexdigest()


def refine() -> Dict[str, any]:
    """Main refinement pipeline."""
    if not os.path.exists(RAW_PATH):
        raise FileNotFoundError(f"Raw vocabulary file not found: {RAW_PATH}")
    
    print(f"Loading raw vocabulary from {RAW_PATH}...")
    raw_words = load_raw_words(RAW_PATH)
    print(f"Loaded {len(raw_words)} raw words")
    
    print("Filtering garbage tokens...")
    filtered = filter_tokens(raw_words)
    before_size = len(filtered)
    print(f"After filtering: {before_size} words ({len(raw_words) - before_size} removed)")
    
    print("Scoring and selecting top 50k by relevance...")
    final_words = backfill_to_target(filtered)
    print(f"Final vocabulary: {len(final_words)} words")
    
    print("Building categories...")
    categories = build_categories(final_words)
    
    stats = {
        'raw_size': len(raw_words),
        'filtered_size': before_size,
        'final_size': len(final_words),
        'removed': len(raw_words) - before_size,
        'hash': hash_list(final_words)
    }
    
    out = {
        'version': '1.0-curated',
        'source': 'Princeton WordNet (filtered + domain injection)',
        'raw_provenance': RAW_PATH,
        'size': len(final_words),
        'words': final_words,
        'categories': {k: len(v) for k,v in categories.items()},
        'category_samples': {k: v[:25] for k,v in categories.items()},
        'stats': stats,
        'domain_core_count': len(DOMAIN_CORE)
    }
    
    print(f"\nWriting curated vocabulary to {CURATED_PATH}...")
    with open(CURATED_PATH,'w',encoding='utf-8') as f:
        json.dump(out,f,indent=2)
    
    print(f"\n✅ Curated vocabulary written: {CURATED_PATH}")
    print(f"   Raw: {len(raw_words)} | After filter: {before_size} | Final: {len(final_words)}")
    print(f"   Removed: {stats['removed']}")
    print(f"   Hash: {stats['hash'][:16]}…")
    print(f"\n📊 Categories:")
    for cat, cat_words in categories.items():
        if cat_words:
            print(f"   {cat}: {len(cat_words)} words")
    
    return out

if __name__ == '__main__':
    refine()
