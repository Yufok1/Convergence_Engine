import torch
import json
import zipfile
import zlib
from io import BytesIO
import numpy as np
import datetime
import os
import sys
from typing import Dict, Any, List, Optional, Tuple
import base64
from string import Template
import uuid
import pickle
from pathlib import Path

# Optional ONNX runtime - graceful degradation if not installed
try:
    import onnxruntime
    ONNX_AVAILABLE = True
except ImportError:
    onnxruntime = None
    ONNX_AVAILABLE = False

# Assuming Organism and OrganismBrain are importable from their respective paths
# Using relative imports suitable for agent_compiler.py in reality_simulator/
try:
    from .evolution_engine import Organism, Genotype, Phenotype
    from .neural.brain import OrganismBrain
    from .checkpointing.organism_capsule import OrganismCapsule
    from .portable_agent.agent_runtime import AgentState
except ImportError:
    # Fallback for direct execution or different import contexts
    import sys
    
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir)) # Add reality_simulator to path
    
    from evolution_engine import Organism, Genotype, Phenotype
    from neural.brain import OrganismBrain
    from checkpointing.organism_capsule import OrganismCapsule
    from portable_agent.agent_runtime import AgentState

import logging
logger = logging.getLogger(__name__)

# Constants for action mapping
ACTION_MAP = {
    0: 'move',
    1: 'cooperate',
    2: 'compete',
    3: 'rest',
    4: 'reproduce',
    5: 'isolate'
}

PORTABLE_AGENT_DIR = Path(__file__).parent / 'portable_agent'


def _safe_brain_to_cpu(brain):
    """Safely move brain to CPU, handling torch.compile() CUDA graph issues.
    
    torch.compile() with CUDA graphs caches tensor locations, making direct
    .cpu() calls fail. This helper handles both compiled and non-compiled models.
    """
    # Handle torch.compile() models - get underlying model if compiled
    if hasattr(brain, '_orig_mod'):
        brain = brain._orig_mod
    # Clone to avoid CUDA graph issues
    try:
        import copy
        brain_copy = copy.deepcopy(brain)
        brain_copy.eval()
        return brain_copy.cpu()
    except Exception:
        # Fallback
        brain.eval()
        return brain.cpu()


def _json_default(obj):
    """
    Custom JSON serializer for objects not natively serializable.
    
    Handles:
    - numpy integers/floats/bools -> Python native types
    - numpy arrays -> lists
    - Any other non-serializable -> str representation
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return str(obj)


class AgentCompiler:
    """
    Compiles a NeuralOrganism's state, particularly its neural network brain,
    into a portable, deployable agent archive.
    """

    def __init__(self):
        self.supported_formats = ['onnx', 'torchscript', 'statedict']
        self._base_vocabulary_cache = None  # Cache for base vocabulary pool
        self._base_knowledge_web_cache = None  # Cache for base knowledge web

    def _load_base_vocabulary_pool(self) -> Dict[str, Any]:
        """
        🌐 Load the base vocabulary pool from the distilled knowledge web.
        
        This provides the FULL vocabulary (74,557+ concepts) that should be
        exported with every package, not just the learned/discovered words.
        
        Returns:
            Dict containing full vocabulary pool with concepts and relations
        """
        if self._base_vocabulary_cache is not None:
            return self._base_vocabulary_cache
        
        # Search paths for the base vocabulary
        search_paths = [
            Path(__file__).parent.parent / 'data' / 'knowledge_web_distilled.json',
            Path(__file__).parent.parent / 'data' / 'seeded_knowledge_web_250k.json',
            Path(__file__).parent.parent / 'data' / 'seeded_knowledge_web_expanded.json',
            Path(__file__).parent.parent / 'data' / 'seeded_knowledge_web_50k.json',
        ]
        
        for vocab_path in search_paths:
            if vocab_path.exists():
                try:
                    with open(vocab_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    concept_count = len(data.get('concepts', {}))
                    logger.info(f"[COMPILER] Loaded base vocabulary pool: {concept_count:,} concepts from {vocab_path.name}")
                    
                    self._base_vocabulary_cache = data
                    return data
                except Exception as e:
                    logger.warning(f"[COMPILER] Failed to load {vocab_path}: {e}")
                    continue
        
        logger.warning("[COMPILER] No base vocabulary pool found - exports will only contain learned words")
        self._base_vocabulary_cache = {'concepts': {}, 'relations': []}
        return self._base_vocabulary_cache
    
    def _build_full_vocabulary_export(self, runtime_vocabulary: Any = None) -> Dict[str, Any]:
        """
        🔧 Build a complete vocabulary export combining base pool + runtime learned words.
        
        Args:
            runtime_vocabulary: The runtime vocabulary object (may have learned words)
            
        Returns:
            Dict with full vocabulary data for export
        """
        base_pool = self._load_base_vocabulary_pool()
        
        # Start with base vocabulary mappings
        full_vocab = {
            'word_to_id': {},
            'id_to_word': {},
            'vocab_size': 0,
            'base_pool_size': len(base_pool.get('concepts', {})),
            'source': 'base_pool + runtime',
        }
        
        # Build word_to_id from base concepts
        word_id = 0
        for word in base_pool.get('concepts', {}):
            if word not in full_vocab['word_to_id']:
                full_vocab['word_to_id'][word] = word_id
                full_vocab['id_to_word'][str(word_id)] = word
                word_id += 1
        
        # Merge runtime vocabulary if provided
        if runtime_vocabulary is not None:
            runtime_w2i = getattr(runtime_vocabulary, 'word_to_id', {})
            for word in runtime_w2i:
                if word not in full_vocab['word_to_id']:
                    full_vocab['word_to_id'][word] = word_id
                    full_vocab['id_to_word'][str(word_id)] = word
                    word_id += 1
        
        full_vocab['vocab_size'] = word_id
        return full_vocab
    
    def _build_full_knowledge_web_export(self, runtime_knowledge_web: Any = None) -> Dict[str, Any]:
        """
        🌐 Build knowledge web export with ONLY learned concepts (not base pool dump).
        
        FIXED: Organisms should LEARN concepts, not have 62k+ WordNet concepts dumped on them.
        We only export concepts that were actually discovered/learned at runtime.
        
        Args:
            runtime_knowledge_web: The runtime knowledge web object (contains learned concepts)
            
        Returns:
            Dict with ONLY learned/discovered concepts for export
        """
        # FIXED: Don't dump the entire base_pool into exports!
        # Organisms should learn concepts, not have them pre-loaded
        
        # Start with empty knowledge web - organisms earn their knowledge
        full_kw = {
            'version': '2.0',
            'source': 'runtime_learned',
            'concepts': {},
            'relations': [],
            'concept_count': 0,
            'relation_count': 0,
        }
        
        # REMOVED: The old code dumped 62k+ base_pool concepts here
        # for word, concept_data in base_pool.get('concepts', {}).items():
        #     full_kw['concepts'][word] = concept_data
        
        # ONLY export runtime discoveries - what the organism actually learned
        if runtime_knowledge_web is not None:
            try:
                # Handle dict-style knowledge web (from CocoonAgent)
                if isinstance(runtime_knowledge_web, dict):
                    runtime_concepts = runtime_knowledge_web.get('concepts', {})
                    runtime_relations = runtime_knowledge_web.get('relations', [])
                    
                    for word, concept_data in runtime_concepts.items():
                        if isinstance(concept_data, dict):
                            full_kw['concepts'][word] = {
                                'word': word,
                                **concept_data,
                                'learned': True,
                            }
                        else:
                            full_kw['concepts'][word] = {
                                'word': word,
                                'category': 'learned',
                                'confidence': 0.5,
                                'learned': True,
                            }
                    
                    full_kw['relations'] = runtime_relations if isinstance(runtime_relations, list) else []
                else:
                    # Handle object-style knowledge web
                    runtime_concepts = getattr(runtime_knowledge_web, 'concepts', {})
                    runtime_relations = getattr(runtime_knowledge_web, 'relations', [])
                    
                    for concept in runtime_concepts.values():
                        word = getattr(concept, 'word', str(concept))
                        full_kw['concepts'][word] = {
                            'word': word,
                            'category': getattr(concept, 'category', 'learned'),
                            'confidence': getattr(concept, 'confidence', 0.5),
                            'discovery_count': getattr(concept, 'discovery_count', 0),
                            'learned': True,
                        }
                    
                    # Add runtime relations
                    for rel in runtime_relations:
                        if hasattr(rel, 'to_dict'):
                            full_kw['relations'].append(rel.to_dict())
                        elif isinstance(rel, dict):
                            full_kw['relations'].append(rel)
            except Exception as e:
                logger.warning(f"[COMPILER] Error merging runtime knowledge: {e}")
        
        full_kw['concept_count'] = len(full_kw['concepts'])
        full_kw['relation_count'] = len(full_kw['relations'])
        
        return full_kw

    def _extract_alliance_data_for_cocoon(self, capsules: List['OrganismCapsule'], 
                                           alliance_system: Any,
                                           organism_names: List[str]) -> Dict[str, Any]:
        """
        🤝 Extract FULL alliance social structure for cocoon export.
        
        "Connections formed are causeways for rationality" - the alliance graph
        represents the emergent social brain. Without it, cocoons lose the
        cooperative intelligence that organisms developed together.
        
        This exports:
        - Alliance memberships (who is allied with whom)
        - Trust scores (earned through cooperation/defection history)
        - Reputation data (how organisms are perceived)
        - Competition stats (wins/losses that establish credibility)
        - Social graph (connections between organisms)
        
        Args:
            capsules: List of organism capsules being exported
            alliance_system: AllianceWarfareSystem or LiveAllianceSystem (or None)
            organism_names: List of organism IDs
            
        Returns:
            Alliance data structure for cocoon embedding
        """
        alliance_data = {
            'version': '1.0',
            'source': 'emergent_social_structure',
            'alliances': {},              # alliance_id -> {members, trust, wars_won, ...}
            'organism_to_alliance': {},   # organism_id -> alliance_id
            'organism_trust': {},         # organism_id -> trust_score (0.0-1.0)
            'organism_reputation': {},    # organism_id -> OrganismReputation data
            'organism_stats': {},         # organism_id -> competition stats
            'social_graph': {},           # organism_id -> [connected_organism_ids]
        }
        
        org_ids_set = set(organism_names)
        
        # 1) Extract competition stats from capsules (these are EARNED achievements)
        for capsule in capsules:
            org_id = self._get_organism_id(capsule)
            
            # Get competition stats from organism
            stats = {}
            
            # Tournament stats
            tournament_wins = getattr(capsule, 'tournament_wins', None) or getattr(capsule, 'battles_won', 0)
            tournament_losses = getattr(capsule, 'tournament_losses', None) or getattr(capsule, 'battles_lost', 0)
            
            if tournament_wins is not None:
                stats['tournament_wins'] = int(tournament_wins)
            if tournament_losses is not None:
                stats['tournament_losses'] = int(tournament_losses)
                
            # Proton game stats
            proton_wins = getattr(capsule, 'proton_wins', 0)
            proton_losses = getattr(capsule, 'proton_losses', 0)
            if proton_wins or proton_losses:
                stats['proton_wins'] = int(proton_wins)
                stats['proton_losses'] = int(proton_losses)
            
            # Skills unlocked (proof of capability)
            skills = getattr(capsule, 'skills_mastered', None) or getattr(capsule, 'skills_unlocked', [])
            if skills:
                stats['skills_mastered'] = list(skills) if hasattr(skills, '__iter__') else []
            
            # Win streak (momentum)
            win_streak = getattr(capsule, 'win_streak', 0)
            if win_streak:
                stats['win_streak'] = int(win_streak)
            
            # Illumination level (enlightenment)
            illumination = getattr(capsule, 'illumination_level', None)
            if illumination is not None:
                stats['illumination_level'] = float(illumination)
            
            # Alliance reputation
            alliance_rep = getattr(capsule, 'alliance_reputation', 0.5)
            stats['alliance_reputation'] = float(alliance_rep)
            
            # Alliance ID from organism
            alliance_id = getattr(capsule, 'alliance_id', None)
            if alliance_id:
                alliance_data['organism_to_alliance'][org_id] = str(alliance_id)
            
            if stats:
                alliance_data['organism_stats'][org_id] = stats
        
        # 2) Extract alliance structure from alliance_system
        if alliance_system is not None:
            try:
                # Handle AllianceWarfareSystem (has PlanetaryAlliance objects)
                if hasattr(alliance_system, 'alliances'):
                    alliances_dict = alliance_system.alliances
                    for alliance_id, alliance in alliances_dict.items():
                        # Only include alliances that contain our organisms
                        members = []
                        if hasattr(alliance, 'members'):
                            if isinstance(alliance.members, dict):
                                members = list(alliance.members.keys())
                            else:
                                members = list(alliance.members)
                        
                        # Filter to only organisms in this cocoon
                        relevant_members = [m for m in members if str(m) in org_ids_set]
                        if not relevant_members:
                            continue
                        
                        # Extract alliance data
                        alliance_export = {
                            'alliance_id': str(alliance_id),
                            'name': getattr(alliance, 'name', f'Alliance_{alliance_id}'),
                            'members': relevant_members,
                            'founder_id': getattr(alliance, 'founder_id', None),
                            'warchief_id': getattr(alliance, 'warchief_id', None),
                            'wars_won': getattr(alliance, 'wars_won', 0),
                            'wars_lost': getattr(alliance, 'wars_lost', 0),
                            'formation_time': getattr(alliance, 'formation_time', 0),
                        }
                        
                        # Controlled territories (proof of power)
                        territories = getattr(alliance, 'controlled_territories', [])
                        if territories:
                            alliance_export['territories'] = [str(t.value) if hasattr(t, 'value') else str(t) for t in territories]
                        
                        # Betrayers (trust violations)
                        betrayers = getattr(alliance, 'betrayers', set())
                        if betrayers:
                            alliance_export['betrayers'] = list(betrayers)
                        
                        alliance_data['alliances'][str(alliance_id)] = alliance_export
                        
                        # Update organism_to_alliance mapping
                        for member_id in relevant_members:
                            alliance_data['organism_to_alliance'][str(member_id)] = str(alliance_id)
                
                # 3) Extract reputation data
                if hasattr(alliance_system, 'reputations'):
                    for org_id, rep in alliance_system.reputations.items():
                        if str(org_id) in org_ids_set:
                            if hasattr(rep, 'get_trust_score'):
                                # OrganismReputation object
                                alliance_data['organism_trust'][str(org_id)] = rep.get_trust_score()
                                alliance_data['organism_reputation'][str(org_id)] = {
                                    'alliances_honored': getattr(rep, 'alliances_honored', 0),
                                    'alliances_betrayed': getattr(rep, 'alliances_betrayed', 0),
                                    'wars_fought': getattr(rep, 'wars_fought', 0),
                                    'wars_won': getattr(rep, 'wars_won', 0),
                                    'trust_score': rep.get_trust_score(),
                                    'threat_level': rep.get_threat_level() if hasattr(rep, 'get_threat_level') else 0.3,
                                }
                            elif isinstance(rep, (int, float)):
                                # Simple reputation score
                                alliance_data['organism_trust'][str(org_id)] = float(rep)
                
                # 4) Build social graph (who trusts whom)
                if hasattr(alliance_system, 'organism_to_alliance'):
                    # Same-alliance members are connected
                    for org_id, ally_id in alliance_system.organism_to_alliance.items():
                        if str(org_id) not in org_ids_set:
                            continue
                        
                        alliance = alliance_system.alliances.get(ally_id)
                        if alliance:
                            members = []
                            if hasattr(alliance, 'members'):
                                if isinstance(alliance.members, dict):
                                    members = list(alliance.members.keys())
                                else:
                                    members = list(alliance.members)
                            
                            # Connect to other members in same alliance
                            connected = [str(m) for m in members if str(m) != str(org_id) and str(m) in org_ids_set]
                            if connected:
                                alliance_data['social_graph'][str(org_id)] = connected
                                
            except Exception as e:
                logger.warning(f"[COMPILER] Error extracting alliance data: {e}")
        
        # 5) Handle LiveAllianceSystem format (from portable_agent/bridge.py)
        if alliance_system is not None and not alliance_data['alliances']:
            try:
                # LiveAllianceSystem uses different attribute names
                if hasattr(alliance_system, 'organism_to_alliance') and hasattr(alliance_system, 'reputations'):
                    # Extract mappings
                    for org_id, ally_id in getattr(alliance_system, 'organism_to_alliance', {}).items():
                        if str(org_id) in org_ids_set:
                            alliance_data['organism_to_alliance'][str(org_id)] = str(ally_id)
                    
                    # Extract reputations
                    for org_id, rep in getattr(alliance_system, 'reputations', {}).items():
                        if str(org_id) in org_ids_set:
                            alliance_data['organism_trust'][str(org_id)] = float(rep)
                    
                    # Extract alliances
                    for ally_id, ally_data in getattr(alliance_system, 'alliances', {}).items():
                        members = ally_data.get('members', set())
                        if isinstance(members, set):
                            members = list(members)
                        relevant = [m for m in members if str(m) in org_ids_set]
                        if relevant:
                            alliance_data['alliances'][str(ally_id)] = {
                                'alliance_id': str(ally_id),
                                'members': relevant,
                                'tier': ally_data.get('tier', 1),
                                'reputation': ally_data.get('reputation', 0.5),
                            }
            except Exception as e:
                logger.warning(f"[COMPILER] Error extracting LiveAllianceSystem data: {e}")
        
        return alliance_data

    class LanguageHeadWrapper(torch.nn.Module):
        """Wrapper that exports both action and language heads together."""
        
        def __init__(self, brain: 'OrganismBrain'):
            super().__init__()
            self.brain = brain
            self.has_language_head = brain.use_language_head
            self.input_dim = brain.input_dim
            self.output_dim = brain.output_dim
            self.vocab_size = brain.vocab_size if hasattr(brain, 'vocab_size') else 10000
            
        def forward(self, x: torch.Tensor):
            """Forward pass returning (action_probs, language_logits) if language head exists."""
            if self.has_language_head:
                # Call forward with return_language_logits=True
                action_probs, language_logits = self.brain(x, return_language_logits=True)
                return action_probs, language_logits
            else:
                # Just return action probs
                action_probs = self.brain(x)
                return action_probs

    class MultiOrganismWrapper(torch.nn.Module):
        def __init__(self, brains: List['OrganismBrain'], names: List[str]):
            super().__init__()
            self.brains = torch.nn.ModuleList(brains)
            self.names = names
            self.input_dims = [b.input_dim for b in brains]
            self.output_dims = [b.output_dim for b in brains]
            self.max_input_dim = max(self.input_dims) if self.input_dims else 0
            # Check if any brain has language head
            self.has_language_heads = [getattr(b, 'use_language_head', False) for b in brains]
            self.any_language_head = any(self.has_language_heads)

        def forward(self, x: torch.Tensor):
            # x shape: [B, max_input_dim] (we will slice/pad per brain)
            # Returns FLAT tuple: (action1, action2, ..., lang1, lang2, ...) for ONNX compatibility
            action_outputs = []
            language_outputs = []
            
            for brain, in_dim, has_lang in zip(self.brains, self.input_dims, self.has_language_heads):
                if x.shape[1] < in_dim:
                    pad = torch.zeros(x.shape[0], in_dim - x.shape[1], dtype=x.dtype, device=x.device)
                    x_i = torch.cat([x, pad], dim=1)
                else:
                    x_i = x[:, :in_dim]
                
                if has_lang:
                    action_probs, lang_logits = brain(x_i, return_language_logits=True)
                    action_outputs.append(action_probs)
                    language_outputs.append(lang_logits)
                else:
                    action_probs = brain(x_i)
                    action_outputs.append(action_probs)
            
            # Return flat tuple: all actions first, then all language outputs
            # This is compatible with ONNX which expects flat output tuple
            if language_outputs:
                return tuple(action_outputs + language_outputs)
            return tuple(action_outputs)
    
    def _get_brain_from_entity(self, entity) -> OrganismBrain:
        """
        Extract or reconstruct brain from either a live NeuralOrganism or an OrganismCapsule.
        
        Args:
            entity: Either a NeuralOrganism (live) or OrganismCapsule (saved)
            
        Returns:
            OrganismBrain instance
        """
        # Check if it's a live organism with a brain attribute
        if hasattr(entity, 'brain') and entity.brain is not None:
            return entity.brain
        
        # Otherwise, treat as capsule and reconstruct from neural snapshot
        return self._reconstruct_brain_from_capsule(entity)
    
    def _get_organism_id(self, entity) -> str:
        """Get organism ID from either a live organism or capsule."""
        if hasattr(entity, 'organism_id'):
            return str(entity.organism_id)
        if hasattr(entity, 'id'):
            return str(entity.id)
        if hasattr(entity, 'species_id'):
            return str(entity.species_id)
        return "unknown"
    
    def _get_capsule_from_entity(self, entity) -> Optional[OrganismCapsule]:
        """
        Get capsule from an entity, handling both live organisms and capsules.
        
        Args:
            entity: Either a NeuralOrganism (live) or OrganismCapsule (saved)
            
        Returns:
            OrganismCapsule if the entity is a capsule, or None if it's a live organism
            (since live organisms don't have capsule-specific data like atomic_language_state)
        """
        # If it's already a capsule (has capsule-specific attributes), return it
        if isinstance(entity, OrganismCapsule):
            return entity
        
        # Check for capsule-like attributes (atomic_language_state is capsule-specific)
        if hasattr(entity, 'atomic_language_state') or hasattr(entity, 'neural'):
            return entity
        
        # It's a live organism without capsule data
        return None
        
    def _reconstruct_brain_from_capsule(self, capsule: OrganismCapsule) -> OrganismBrain:
        """
        Reconstructs the OrganismBrain model from the capsule data OR
        extracts the brain directly from a live NeuralOrganism.
        
        Handles both:
        - Live NeuralOrganism objects (have .brain attribute)
        - OrganismCapsule objects (have .neural attribute)
        """
        # Check if this is a live organism with a brain attached
        if hasattr(capsule, 'brain') and capsule.brain is not None:
            return capsule.brain
        
        # Otherwise, it should be a capsule with neural snapshot
        if not hasattr(capsule, 'neural') or not capsule.neural:
            raise ValueError("Capsule does not contain neural network state.")
        
        # Extract from NeuralSnapshot
        neural_snap = capsule.neural
        brain_state_dict_b64 = neural_snap.to_dict().get('state_dict_b64')
        
        if not brain_state_dict_b64:
            raise ValueError("Neural network state in capsule is incomplete.")
            
        # Extract parameters from NeuralSnapshot
        input_dim = neural_snap.input_size
        hidden_dim = neural_snap.hidden_size
        output_dim = neural_snap.output_size

        # Load the state_dict FIRST to detect architecture
        state_dict_bytes = base64.b64decode(brain_state_dict_b64)
        # Some snapshots may be gzip compressed before base64 encoding
        # Note: PyTorch's native ZIP format (PK header with archive/ prefix) should NOT be extracted
        try:
            if len(state_dict_bytes) >= 2 and state_dict_bytes[:2] == b"\x1f\x8b":
                import gzip
                state_dict_bytes = gzip.decompress(state_dict_bytes)
            elif len(state_dict_bytes) >= 2 and state_dict_bytes[:2] == b"PK":
                # Check if this is PyTorch's native ZIP format (has archive/ prefix)
                # If so, leave it alone - torch.load handles it directly
                with zipfile.ZipFile(BytesIO(state_dict_bytes)) as zf:
                    names = zf.namelist()
                    is_pytorch_native = any(n.startswith('archive/') for n in names)
                    
                    if not is_pytorch_native:
                        # Legacy: manually zipped checkpoint file - extract it
                        candidate = None
                        for ext in ('.pt', '.pth', '.pkl', '.bin', '.tensors'):
                            for n in names:
                                if n.lower().endswith(ext):
                                    candidate = n
                                    break
                            if candidate:
                                break
                        if candidate:
                            state_dict_bytes = zf.read(candidate)
                    # else: PyTorch native format, pass through to torch.load unchanged
        except Exception:
            # If decompression fails, fall back to raw bytes
            pass

        # PyTorch 2.6 defaults weights_only=True; allow full, trusted load
        state_dict = torch.load(BytesIO(state_dict_bytes), map_location='cpu', weights_only=False)

        # Infer architecture from state_dict to avoid shape/key mismatches
        sd_keys = set(state_dict.keys())
        def _shape(name, dim):
            return state_dict[name].shape[dim] if name in state_dict else None

        inferred_input = _shape('fc1.weight', 1) or getattr(capsule.neural, 'input_size', None) or 18
        inferred_hidden = _shape('fc1.weight', 0) or getattr(capsule.neural, 'hidden_size', None) or 64
        inferred_output = _shape('fc3.weight', 0) or getattr(capsule.neural, 'output_size', None) or 6

        use_attention = any(k.startswith('attention.') for k in sd_keys) or 'attention_norm.weight' in sd_keys
        use_language_head = 'fc_language.weight' in sd_keys
        use_concept_head = any(k.startswith('concept_head.') for k in sd_keys)

        # Use .size() instead of .shape[] for robustness
        vocab_size = state_dict['fc_language.weight'].size(0) if use_language_head else 10000

        # Infer num_attention_heads if attention is used
        if use_attention:
            # Infer from hidden_dim and common head counts
            # attention uses hidden_dim as embed_dim, which must be divisible by num_heads
            # Try to match common patterns: 8, 16, 4, 2
            for candidate_heads in [8, 16, 4, 2, 1]:
                if inferred_hidden % candidate_heads == 0:
                    num_attention_heads = candidate_heads
                    break
            else:
                num_attention_heads = 4  # Fallback
        else:
            num_attention_heads = 4

        # Use reasonable dropout matching current config (can't infer from state_dict)
        dropout = 0.15

        # Infer num_key_compositions from concept_head if present
        num_key_compositions = 30  # Default (matches config.json)
        if use_concept_head and 'concept_head.composition_value.weight' in state_dict:
            # composition_value.weight shape is (num_key_compositions, hidden_dim)
            num_key_compositions = state_dict['concept_head.composition_value.weight'].size(0)
            logger.debug(f"Inferred num_key_compositions={num_key_compositions} from state_dict")

        # Create a new instance of OrganismBrain matching the checkpoint
        reconstructed_brain = OrganismBrain(
            input_dim=int(inferred_input),
            hidden_dim=int(inferred_hidden),
            output_dim=int(inferred_output),
            activation='relu',
            dropout=dropout,
            use_attention=bool(use_attention),
            num_attention_heads=int(num_attention_heads),
            attention_dim=int(inferred_hidden),
            vocab_size=int(vocab_size),
            use_language_head=bool(use_language_head),
            use_concept_head=bool(use_concept_head),
            num_key_compositions=int(num_key_compositions)
        )

        # Load state dict allowing extra/missing keys (robust to optional heads)
        missing, unexpected = reconstructed_brain.load_state_dict(state_dict, strict=False)
        if unexpected:
            logger.debug(f"AgentCompiler: Ignored unexpected keys during load: {sorted(list(unexpected))[:5]}...")
        reconstructed_brain.eval() # Set to evaluation mode
        
        return reconstructed_brain

    def _export_onnx(self, brain: OrganismBrain, dummy_input: torch.Tensor, model_path: str) -> None: 
        """Exports the PyTorch brain to ONNX format, including language head if present."""
        try:
            # Wrap brain to export both action and language heads
            wrapper = self.LanguageHeadWrapper(brain)
            wrapper.eval()
            
            # Log brain architecture for debugging
            logger.debug(f"ONNX export: input_dim={brain.input_dim}, hidden_dim={brain.hidden_dim}, "
                        f"output_dim={brain.output_dim}, use_attention={brain.use_attention}, "
                        f"use_language_head={brain.use_language_head}, use_concept_head={brain.use_concept_head}, "
                        f"num_key_compositions={getattr(brain, 'num_key_compositions', 'N/A')}")
            
            # Test forward pass before export to catch errors early
            logger.debug("Testing forward pass before ONNX export...")
            with torch.no_grad():
                test_output = wrapper(dummy_input)
                if isinstance(test_output, tuple):
                    logger.debug(f"Forward pass OK: {len(test_output)} outputs")
                else:
                    logger.debug(f"Forward pass OK: single output shape {test_output.shape}")
            
            # Configure output names based on whether language head exists
            if wrapper.has_language_head:
                output_names = ['action_probs', 'language_logits']
                dynamic_axes = {
                    'input': {0: 'batch_size'},
                    'action_probs': {0: 'batch_size'},
                    'language_logits': {0: 'batch_size'}
                }
            else:
                output_names = ['action_probs']
                dynamic_axes = {
                    'input': {0: 'batch_size'},
                    'action_probs': {0: 'batch_size'}
                }
            
            logger.debug("Starting torch.onnx.export...")
            torch.onnx.export(
                wrapper,
                dummy_input,
                model_path,
                input_names=['input'],
                output_names=output_names,
                dynamic_axes=dynamic_axes,
                opset_version=11 # A commonly supported opset version
            )
            head_info = " (with language head)" if wrapper.has_language_head else ""
            logger.info(f"Successfully exported brain to ONNX{head_info}: {model_path}")
        except Exception as e:
            # Provide clearer guidance when onnx/onnxscript is missing (PyTorch 2.6+)
            import traceback
            msg = str(e)
            hint = ""
            if 'onnxscript' in msg.lower():
                hint = " (install with: pip install onnx onnxscript)"
            logger.error(f"Failed to export brain to ONNX at {model_path}: {e}{hint}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            raise

    def _export_torchscript(self, brain: OrganismBrain, model_path) -> None: 
        """Exports the PyTorch brain to TorchScript format, including language head if present.
        
        Args:
            brain: The OrganismBrain to export
            model_path: Either a file path string or a BytesIO buffer
        """
        try:
            # Wrap brain to export both action and language heads
            wrapper = self.LanguageHeadWrapper(brain)
            wrapper.eval()
            
            # Log brain architecture for debugging
            logger.debug(f"TorchScript export: input_dim={brain.input_dim}, hidden_dim={brain.hidden_dim}, "
                        f"output_dim={brain.output_dim}, use_attention={brain.use_attention}, "
                        f"use_language_head={brain.use_language_head}, use_concept_head={brain.use_concept_head}, "
                        f"num_key_compositions={getattr(brain, 'num_key_compositions', 'N/A')}")
            
            # Use torch.jit.trace instead of torch.jit.script
            # trace captures the execution path dynamically, which works with
            # OrganismBrain's complex control flow (conditional attention, etc.)
            # script analyzes code statically and fails on Python 3.12 + PyTorch 2.5
            dummy_input = torch.randn(1, brain.input_dim, dtype=torch.float32)
            
            # Test forward pass before tracing to catch errors early
            logger.debug("Testing forward pass before trace...")
            with torch.no_grad():
                test_output = wrapper(dummy_input)
                if isinstance(test_output, tuple):
                    logger.debug(f"Forward pass OK: {len(test_output)} outputs")
                else:
                    logger.debug(f"Forward pass OK: single output shape {test_output.shape}")
            
            logger.debug("Starting torch.jit.trace...")
            traced_brain = torch.jit.trace(wrapper, (dummy_input,))
            
            head_info = " (with language head)" if wrapper.has_language_head else ""
            
            # Handle both file path (str) and BytesIO buffer
            if isinstance(model_path, BytesIO):
                torch.jit.save(traced_brain, model_path)
                model_path.seek(0)  # Reset buffer position for reading
                logger.info(f"Successfully exported brain to TorchScript (traced){head_info} in memory buffer")
            else:
                traced_brain.save(model_path)
                logger.info(f"Successfully exported brain to TorchScript (traced){head_info}: {model_path}")
        except Exception as e:
            import traceback
            logger.error(f"Failed to export brain to TorchScript: {e}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            raise

    def _export_statedict(self, brain: OrganismBrain, model_path: str) -> None: 
        """Exports the PyTorch brain's state_dict."""
        try:
            torch.save(brain.state_dict(), model_path)
            logger.info(f"Successfully exported brain state_dict: {model_path}")
        except Exception as e:
            logger.error(f"Failed to export brain state_dict at {model_path}: {e}")
            raise

    def _extract_fitness_value(self, entity) -> Optional[float]:
        """Safely extract fitness value from capsule or organism, handling various data formats."""
        # Handle direct numeric fitness (live organisms)
        if hasattr(entity, 'fitness'):
            fitness_attr = entity.fitness
            # If it's already a number, return it directly
            if isinstance(fitness_attr, (int, float)):
                return float(fitness_attr)
            # numpy scalar
            if hasattr(fitness_attr, 'item'):
                return float(fitness_attr.item())
            # If it's a fitness object with history
            if hasattr(fitness_attr, 'fitness_history') and fitness_attr.fitness_history:
                history = fitness_attr.fitness_history
                try:
                    # Handle list of tuples: [(time, fitness), ...]
                    if isinstance(history, list) and len(history) > 0:
                        last_entry = history[-1]
                        if isinstance(last_entry, (list, tuple)) and len(last_entry) >= 2:
                            return float(last_entry[1])
                        else:
                            return float(last_entry)
                    # Handle numpy array
                    elif hasattr(history, 'shape'):
                        if len(history.shape) == 2:
                            return float(history[-1, 1])
                        elif len(history.shape) == 1:
                            return float(history[-1])
                except (IndexError, TypeError, ValueError) as e:
                    logger.warning(f"Could not extract fitness from history: {e}")
        
        # Try get_fitness() method
        if hasattr(entity, 'get_fitness'):
            try:
                return float(entity.get_fitness())
            except Exception:
                pass
        
        return None

    def _create_rich_metadata(self, capsule: OrganismCapsule, brain: Optional[OrganismBrain] = None) -> Dict[str, Any]:
        """
        Creates comprehensive metadata for the compiled agent, leveraging the rich capsule data.
        
        Args:
            capsule: The OrganismCapsule containing agent state
            brain: Optional reconstructed brain for extracting additional architecture info
        """
        metadata = {
            'agent_id': capsule.organism_id,
            'capsule_id': capsule.capsule_id,
            'export_timestamp': datetime.datetime.now().isoformat(),
            'capsule_version': capsule.version,
            'capture_reason': capsule.capture_reason,

            # Organism Core Data
            'organism_core': {
                'species_id': capsule.organism_id,
                'capsule_id': capsule.capsule_id,
                'fitness': self._extract_fitness_value(capsule),
                'organism_age': capsule.organism_age,
                'birth_time': capsule.organism_birth_time,
            },
            
            # Neural Network Details
            'neural_network': {
                'architecture': {
                    'input_size': capsule.neural.input_size,
                    'hidden_size': capsule.neural.hidden_size,
                    'output_size': capsule.neural.output_size,
                    'num_layers': capsule.neural.num_layers,
                    'total_parameters': capsule.neural.total_parameters,
                    'has_language_head': hasattr(brain, 'use_language_head') and brain.use_language_head if brain else False,
                    'has_attention': hasattr(brain, 'use_attention') and brain.use_attention if brain else False,
                    'has_concept_head': hasattr(brain, 'use_concept_head') and brain.use_concept_head if brain else False,
                    'vocab_size': brain.vocab_size if brain and hasattr(brain, 'vocab_size') and hasattr(brain, 'use_language_head') and brain.use_language_head else None
                } if capsule.neural else {},
                'training_steps': capsule.neural.training_steps if capsule.neural else 0,
                'avg_loss': None,
                'device_trained_on': 'cpu',
            },
            
            # Language System Details
            'atomic_language': {
                'enabled': bool(capsule.language),
                'concept_count': capsule.language.total_concepts if capsule.language else 0,
                'dialect_signature': str(capsule.language.dialect_signature) if capsule.language else 'N/A',
            },

            # Configuration & Environment
            'atomic_config': {
                'enabled': bool(capsule.config),
                'atom_count': len(capsule.config.atoms) if capsule.config else 0,
            },
            'environment_context': capsule.environment.to_dict() if capsule.environment else {},
            
            # Highlander & Social Data
            'highlander_data': capsule.highlander.to_dict() if capsule.highlander else {},
            'social_connections': {},  # Not stored in capsule directly
            
            # VP (Vitality-Pleasure) State - CRITICAL for runtime behavior
            'vp_state': {
                'enabled': bool(capsule.vp),
                'vitality': capsule.vp.vitality if capsule.vp else None,
                'pleasure': capsule.vp.pleasure if capsule.vp else None,
                'violation_pressure': capsule.vp.violation_pressure if capsule.vp else None,
                'trajectory_length': len(capsule.vp.vp_trajectory) if capsule.vp else 0,
                'critical_events_count': len(capsule.vp.critical_events) if capsule.vp else 0,
            },
            
            # Causation Trace
            'causation_trace': {
                'enabled': bool(capsule.causation),
                'key_event_count': len(capsule.causation.key_events) if capsule.causation else 0,
                'turning_point_count': len(capsule.causation.turning_points) if capsule.causation else 0,
                'causal_chain_count': len(capsule.causation.causal_chains) if capsule.causation else 0,
            },
            
            # Export Options (to be added by the compiler)
            'export_format': None, 
            'runtime_dependencies': {
                'onnxruntime': onnxruntime.__version__ if ONNX_AVAILABLE else 'not installed',
                'numpy': np.__version__,
                'python': sys.version.split(' ')[0]
            },
            'compatibility': {
                'python_versions': ['3.8+', '3.9+', '3.10+', '3.11+', '3.12+'],
                'platforms': ['windows', 'linux', 'macos'],
                'architectures': ['x64', 'arm64']
            }
        }
        return metadata

    def _generate_formation_fingerprint(self, 
                                         capsules: List['OrganismCapsule'],
                                         causation_explorer: Any = None,
                                         alliance_system: Any = None,
                                         attractor_landscape: Any = None,
                                         shared_state: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        🧬 Generate a "Formation Fingerprint" - a condensed history of the cocoon's formation.
        
        This captures the emergent story of how these organisms came to be:
        - Key events from causation system
        - Alliance structure at export time
        - Attractor landscape state (fixed points, bifurcations)
        - Population dynamics summary
        - Behavioral emergence milestones
        
        This fingerprint is embedded in the README and metadata for provenance.
        """
        fingerprint = {
            'version': '1.0',
            'organisms_count': len(capsules),
            'organism_ids': [getattr(c, 'organism_id', None) or getattr(c, 'species_id', 'unknown') for c in capsules],
            'export_timestamp': datetime.datetime.now().isoformat(),
        }
        
        # Organism stats
        fitnesses = []
        ages = []
        for cap in capsules:
            fitness = self._extract_fitness_value(cap)
            if fitness is not None:
                fitnesses.append(fitness)
            age = getattr(cap, 'organism_age', None)
            if age is not None:
                ages.append(age)
        
        if fitnesses:
            fingerprint['fitness_stats'] = {
                'min': round(min(fitnesses), 4),
                'max': round(max(fitnesses), 4),
                'mean': round(sum(fitnesses) / len(fitnesses), 4),
            }
        if ages:
            fingerprint['age_stats'] = {
                'min': min(ages),
                'max': max(ages),
                'mean': round(sum(ages) / len(ages), 1),
            }
        
        # Causation system summary
        if causation_explorer is not None:
            try:
                events = getattr(causation_explorer, 'events', {})
                event_types = {}
                for event in events.values():
                    et = getattr(event, 'event_type', 'unknown')
                    event_types[et] = event_types.get(et, 0) + 1
                
                fingerprint['causation_summary'] = {
                    'total_events': len(events),
                    'event_types': dict(sorted(event_types.items(), key=lambda x: -x[1])[:10]),
                }
            except Exception:
                pass
        
        # Alliance structure
        if alliance_system is not None:
            try:
                org_ids = set(fingerprint['organism_ids'])
                alliance_memberships = []
                for alliance_id, alliance in getattr(alliance_system, 'alliances', {}).items():
                    members = list(getattr(alliance, 'members', []))
                    for m in members:
                        if str(m) in org_ids or m in org_ids:
                            alliance_memberships.append({
                                'alliance_id': str(alliance_id),
                                'tier': getattr(alliance, 'tier', 1),
                                'size': len(members),
                            })
                            break
                fingerprint['alliance_structure'] = {
                    'memberships': alliance_memberships,
                    'total_alliances': len(getattr(alliance_system, 'alliances', {})),
                }
            except Exception:
                pass
        
        # Attractor landscape state
        if attractor_landscape is not None:
            try:
                landscape_state = attractor_landscape.get_landscape_state() if hasattr(attractor_landscape, 'get_landscape_state') else {}
                fingerprint['attractor_landscape'] = {
                    'field_coherence': round(landscape_state.get('field_coherence', 0), 4),
                    'field_entropy': round(landscape_state.get('field_entropy', 0), 4),
                    'field_stability': round(landscape_state.get('field_stability', 0), 4),
                    'at_fixed_point': landscape_state.get('at_fixed_point', False),
                    'fixed_point_type': landscape_state.get('fixed_point_type'),
                    'total_fixed_points': landscape_state.get('total_fixed_points', 0),
                    'total_bifurcations': landscape_state.get('total_bifurcations', 0),
                }
            except Exception:
                pass
        
        # Shared state snapshot
        if shared_state is not None:
            try:
                fingerprint['simulation_snapshot'] = {
                    'population_count': shared_state.get('population_count', 0),
                    'cycle_count': shared_state.get('cycle_count', 0),
                    'generation': shared_state.get('generation', 0),
                    'vp_current': round(shared_state.get('vp_current', 0), 4) if shared_state.get('vp_current') else None,
                    'health_score': round(shared_state.get('health_score', 0), 4) if shared_state.get('health_score') else None,
                }
            except Exception:
                pass
        
        return fingerprint

    def _generate_ensemble_topology_html(self, capsules: List['OrganismCapsule'], 
                                          brain_configs: List[Dict]) -> str:
        """
        🔬 Neural Lab - Interactive Ensemble Topology Explorer.
        
        A comprehensive science lab for exploring neural architectures:
        
        VIEW MODES:
        ├── Overlay: All organisms superimposed with adjustable opacity
        ├── Radial: Circular arrangement showing ensemble unity  
        ├── Stacked: Horizontal strips for direct visual comparison
        ├── Grid: Side-by-side matrix for detailed analysis
        └── Weights: Heatmap visualization of weight matrices
        
        INTERACTIVE FEATURES:
        ├── Per-organism toggle filters with shift-click isolation
        ├── Opacity slider for overlay blending
        ├── Animation speed control
        ├── Hover tooltips with neuron/organism details
        └── Screenshot export to PNG
        
        KEYBOARD SHORTCUTS:
        ├── 1-9: Toggle organism visibility
        ├── Space: Toggle animation
        ├── A: Select all organisms
        ├── C: Clear selection
        └── R: Switch to radial view
        
        ANALYSIS PANELS:
        ├── Architecture comparison charts
        ├── Fitness distribution visualization
        └── Real-time ensemble metrics
        
        Returns:
            Complete standalone HTML string for the Neural Lab
        """
        import json
        
        # Collect comprehensive organism data
        organisms_data = []
        colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7', 
                  '#dfe6e9', '#fd79a8', '#a29bfe', '#00b894', '#e17055',
                  '#74b9ff', '#ff7675', '#55efc4', '#fdcb6e', '#81ecec']
        
        total_params = 0
        total_neurons = 0
        
        for i, (capsule, config) in enumerate(zip(capsules, brain_configs)):
            brain = self._get_brain_from_entity(capsule)
            org_id = self._get_organism_id(capsule)
            
            # Get architecture details
            input_dim = getattr(brain, 'input_dim', config.get('input_dim', 25))
            hidden_dim = getattr(brain, 'hidden_dim', config.get('hidden_dim', 64))
            output_dim = getattr(brain, 'output_dim', config.get('output_dim', 6))
            use_language = getattr(brain, 'use_language_head', False)
            vocab_size = getattr(brain, 'vocab_size', 0) if use_language else 0
            fitness = config.get('fitness', 0.5)
            
            # Calculate parameter count estimate
            params = (input_dim * hidden_dim) + (hidden_dim * output_dim) + hidden_dim + output_dim
            if use_language:
                params += hidden_dim * vocab_size
            
            neurons = input_dim + hidden_dim + output_dim + (vocab_size if use_language else 0)
            total_params += params
            total_neurons += neurons
            
            # 🔬 EXTRACT ACTUAL WEIGHT DATA for visualization
            weight_data = {'ih': [], 'ho': [], 'stats': {}}
            try:
                import torch
                ih_weights = None
                ho_weights = None
                
                for name, param in brain.named_parameters():
                    if param.dim() >= 2:
                        if ih_weights is None and param.shape[0] >= hidden_dim * 0.5:
                            ih_weights = param.detach().cpu()
                        elif ih_weights is not None and ho_weights is None:
                            ho_weights = param.detach().cpu()
                
                if ih_weights is not None:
                    ih_sample = ih_weights[:min(20, ih_weights.shape[0]), :min(20, ih_weights.shape[1] if ih_weights.dim() > 1 else 1)]
                    ih_abs = torch.abs(ih_sample).tolist()
                    weight_data['ih'] = [[round(w, 4) for w in row] if isinstance(row, list) else [round(row, 4)] for row in ih_abs]
                    weight_data['stats']['ih_mean'] = round(float(torch.abs(ih_weights).mean()), 4)
                    weight_data['stats']['ih_max'] = round(float(torch.abs(ih_weights).max()), 4)
                    weight_data['stats']['ih_std'] = round(float(ih_weights.std()), 4)
                
                if ho_weights is not None:
                    ho_sample = ho_weights[:min(20, ho_weights.shape[0]), :min(20, ho_weights.shape[1] if ho_weights.dim() > 1 else 1)]
                    ho_abs = torch.abs(ho_sample).tolist()
                    weight_data['ho'] = [[round(w, 4) for w in row] if isinstance(row, list) else [round(row, 4)] for row in ho_abs]
                    weight_data['stats']['ho_mean'] = round(float(torch.abs(ho_weights).mean()), 4)
                    weight_data['stats']['ho_max'] = round(float(torch.abs(ho_weights).max()), 4)
                    weight_data['stats']['ho_std'] = round(float(ho_weights.std()), 4)
            except Exception as e:
                weight_data['error'] = str(e)[:50]
            
            organisms_data.append({
                'id': org_id[:20] if len(org_id) > 20 else org_id,
                'index': i,
                'color': colors[i % len(colors)],
                'input_dim': input_dim,
                'hidden_dim': hidden_dim,
                'output_dim': output_dim,
                'use_language': use_language,
                'vocab_size': vocab_size,
                'fitness': round(fitness, 4),
                'params': params,
                'neurons': neurons,
                'weights': weight_data,
            })
        
        num_organisms = len(organisms_data)
        avg_fitness = sum(o['fitness'] for o in organisms_data) / max(num_organisms, 1)
        max_hidden = max(o['hidden_dim'] for o in organisms_data) if organisms_data else 0
        min_hidden = min(o['hidden_dim'] for o in organisms_data) if organisms_data else 0
        
        # Generate the Neural Lab HTML
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔬 Neural Lab - Ensemble Topology Explorer</title>
    <style>
        :root {{
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-tertiary: #1a1a25;
            --accent-cyan: #00ffff;
            --accent-magenta: #ff00ff;
            --accent-yellow: #ffff00;
            --accent-green: #00ff88;
            --text-primary: #e0e0e0;
            --text-secondary: #888;
            --border-color: rgba(255,255,255,0.1);
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            background: var(--bg-primary);
            color: var(--text-primary);
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            min-height: 100vh;
            overflow-x: hidden;
        }}
        
        /* === HEADER === */
        .header {{
            background: linear-gradient(180deg, var(--bg-secondary) 0%, transparent 100%);
            padding: 20px 30px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }}
        
        .header h1 {{
            font-size: 1.8em;
            background: linear-gradient(90deg, var(--accent-cyan), var(--accent-magenta));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .header .subtitle {{ color: var(--text-secondary); font-size: 0.9em; margin-top: 5px; }}
        
        .header-stats {{ display: flex; gap: 25px; }}
        .header-stat {{ text-align: center; }}
        .header-stat .value {{ font-size: 1.5em; font-weight: bold; color: var(--accent-cyan); }}
        .header-stat .label {{ font-size: 0.75em; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 1px; }}
        
        /* === MAIN LAYOUT === */
        .main-container {{ display: grid; grid-template-columns: 280px 1fr 280px; min-height: calc(100vh - 100px); }}
        
        /* === PANELS === */
        .control-panel, .analysis-panel {{
            background: var(--bg-secondary);
            padding: 20px;
            overflow-y: auto;
        }}
        .control-panel {{ border-right: 1px solid var(--border-color); }}
        .analysis-panel {{ border-left: 1px solid var(--border-color); }}
        
        .panel-section {{ margin-bottom: 25px; }}
        .panel-section h3 {{
            font-size: 0.8em;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-secondary);
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border-color);
        }}
        
        /* === ORGANISM LIST === */
        .organism-list {{ display: flex; flex-direction: column; gap: 8px; }}
        
        .organism-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 12px;
            background: var(--bg-tertiary);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            border: 1px solid transparent;
        }}
        .organism-item:hover {{ background: rgba(255,255,255,0.05); }}
        .organism-item.active {{ border-color: var(--org-color); box-shadow: 0 0 15px color-mix(in srgb, var(--org-color) 30%, transparent); }}
        
        .organism-item .color-indicator {{ width: 14px; height: 14px; border-radius: 50%; background: var(--org-color); flex-shrink: 0; }}
        .organism-item .org-info {{ flex: 1; min-width: 0; }}
        .organism-item .org-name {{ font-size: 0.85em; font-family: 'Consolas', monospace; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .organism-item .org-meta {{ font-size: 0.7em; color: var(--text-secondary); }}
        .organism-item .fitness-bar {{ width: 40px; height: 4px; background: var(--bg-primary); border-radius: 2px; overflow: hidden; }}
        .organism-item .fitness-fill {{ height: 100%; background: var(--org-color); transition: width 0.3s; }}
        
        /* === VIEW MODES === */
        .view-modes {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
        
        .view-btn {{
            padding: 12px 8px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-primary);
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.8em;
            text-align: center;
        }}
        .view-btn:hover {{ background: rgba(255,255,255,0.05); }}
        .view-btn.active {{ background: linear-gradient(135deg, rgba(0,255,255,0.15), rgba(255,0,255,0.15)); border-color: var(--accent-cyan); }}
        .view-btn .icon {{ font-size: 1.2em; display: block; margin-bottom: 4px; }}
        
        /* === SLIDERS === */
        .slider-control {{ margin: 12px 0; }}
        .slider-control label {{ display: flex; justify-content: space-between; font-size: 0.8em; color: var(--text-secondary); margin-bottom: 6px; }}
        .slider-control input[type="range"] {{ width: 100%; height: 4px; -webkit-appearance: none; background: var(--bg-tertiary); border-radius: 2px; outline: none; }}
        .slider-control input[type="range"]::-webkit-slider-thumb {{ -webkit-appearance: none; width: 14px; height: 14px; background: var(--accent-cyan); border-radius: 50%; cursor: pointer; }}
        
        /* === ACTION BUTTONS === */
        .action-buttons {{ display: flex; flex-direction: column; gap: 8px; }}
        .action-btn {{
            padding: 10px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-primary);
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.85em;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .action-btn:hover {{ background: rgba(255,255,255,0.05); border-color: var(--accent-cyan); }}
        .action-btn.animate-active {{ background: rgba(0,255,255,0.1); border-color: var(--accent-cyan); }}
        
        /* === VISUALIZATION === */
        .visualization-area {{
            position: relative;
            background: radial-gradient(ellipse at center, var(--bg-tertiary) 0%, var(--bg-primary) 70%);
            overflow: hidden;
        }}
        #topology-svg {{ width: 100%; height: 100%; min-height: 600px; }}
        
        /* === TOOLTIP === */
        .tooltip {{
            position: absolute;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px 15px;
            font-size: 0.85em;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            z-index: 1000;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }}
        .tooltip.visible {{ opacity: 1; }}
        .tooltip h4 {{ color: var(--accent-cyan); margin-bottom: 8px; font-size: 1em; }}
        .tooltip .tip-row {{ display: flex; justify-content: space-between; gap: 15px; margin: 4px 0; }}
        .tooltip .tip-label {{ color: var(--text-secondary); }}
        .tooltip .tip-value {{ color: var(--text-primary); font-family: monospace; }}
        
        /* === CHARTS === */
        .chart-container {{ background: var(--bg-tertiary); border-radius: 12px; padding: 15px; margin-bottom: 20px; }}
        .chart-container h4 {{ font-size: 0.85em; color: var(--text-secondary); margin-bottom: 15px; }}
        .bar-chart {{ display: flex; flex-direction: column; gap: 8px; }}
        .bar-row {{ display: flex; align-items: center; gap: 10px; }}
        .bar-label {{ width: 60px; font-size: 0.7em; color: var(--text-secondary); text-align: right; overflow: hidden; text-overflow: ellipsis; }}
        .bar-track {{ flex: 1; height: 18px; background: var(--bg-primary); border-radius: 4px; overflow: hidden; }}
        .bar-fill {{ height: 100%; border-radius: 4px; transition: width 0.5s ease-out; display: flex; align-items: center; justify-content: flex-end; padding-right: 6px; }}
        .bar-value {{ font-size: 0.7em; color: rgba(0,0,0,0.7); font-weight: bold; }}
        
        /* === METRICS === */
        .metrics-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
        .metric-card {{ background: var(--bg-tertiary); border-radius: 10px; padding: 15px; text-align: center; }}
        .metric-card .metric-value {{ font-size: 1.4em; font-weight: bold; background: linear-gradient(135deg, var(--accent-cyan), var(--accent-magenta)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
        .metric-card .metric-label {{ font-size: 0.7em; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 5px; }}
        
        /* === KEYBOARD HINTS === */
        .keyboard-hints {{ background: var(--bg-tertiary); border-radius: 8px; padding: 12px; font-size: 0.75em; }}
        .keyboard-hints h4 {{ color: var(--text-secondary); margin-bottom: 8px; font-size: 1em; }}
        .key-hint {{ display: flex; gap: 8px; margin: 4px 0; color: var(--text-secondary); }}
        .key {{ background: var(--bg-primary); padding: 2px 6px; border-radius: 4px; font-family: monospace; color: var(--accent-cyan); }}
        
        /* === ANIMATIONS === */
        @keyframes pulse {{ 0%, 100% {{ opacity: 0.6; }} 50% {{ opacity: 1; }} }}

        .node-pulse {{ animation: pulse 1.5s ease-in-out infinite; }}
        
        /* === FOOTER === */
        .footer {{ text-align: center; padding: 15px; color: var(--text-secondary); font-size: 0.8em; border-top: 1px solid var(--border-color); }}
        .footer a {{ color: var(--accent-cyan); text-decoration: none; }}
        
        /* === RESPONSIVE === */
        @media (max-width: 1200px) {{ .main-container {{ grid-template-columns: 250px 1fr; }} .analysis-panel {{ display: none; }} }}
        @media (max-width: 800px) {{ .main-container {{ grid-template-columns: 1fr; }} .control-panel {{ display: none; }} }}
    </style>
</head>
<body>
    <header class="header">
        <div>
            <h1>🔬 Neural Lab</h1>
            <p class="subtitle">Ensemble Topology Explorer • {num_organisms} organisms</p>
        </div>
        <div class="header-stats">
            <div class="header-stat"><div class="value">{num_organisms}</div><div class="label">Organisms</div></div>
            <div class="header-stat"><div class="value">{total_neurons:,}</div><div class="label">Neurons</div></div>
            <div class="header-stat"><div class="value">{total_params:,}</div><div class="label">Parameters</div></div>
            <div class="header-stat"><div class="value">{avg_fitness:.3f}</div><div class="label">Avg Fitness</div></div>
        </div>
    </header>
    
    <div class="main-container">
        <!-- Left Panel - Controls -->
        <aside class="control-panel">
            <div class="panel-section">
                <h3>🧬 Organisms</h3>
                <div class="organism-list" id="organism-list"></div>
            </div>
            
            <div class="panel-section">
                <h3>👁️ View Mode</h3>
                <div class="view-modes">
                    <button class="view-btn active" data-view="overlay"><span class="icon">◉</span>Overlay</button>
                    <button class="view-btn" data-view="radial"><span class="icon">◎</span>Radial</button>
                    <button class="view-btn" data-view="stack"><span class="icon">≡</span>Stacked</button>
                    <button class="view-btn" data-view="grid"><span class="icon">▦</span>Grid</button>
                    <button class="view-btn" data-view="weights"><span class="icon">🔥</span>Weights</button>
                </div>
            </div>
            
            <div class="panel-section">
                <h3>⚙️ Settings</h3>
                <div class="slider-control">
                    <label><span>Opacity</span><span id="opacity-value">70%</span></label>
                    <input type="range" id="opacity-slider" min="20" max="100" value="70">
                </div>
                <div class="slider-control">
                    <label><span>Animation Speed</span><span id="speed-value">1x</span></label>
                    <input type="range" id="speed-slider" min="1" max="10" value="5">
                </div>
            </div>
            
            <div class="panel-section">
                <h3>🎬 Actions</h3>
                <div class="action-buttons">
                    <button class="action-btn" id="toggle-animate"><span>▶️</span> Toggle Animation</button>
                    <button class="action-btn" id="select-all"><span>✓</span> Select All</button>
                    <button class="action-btn" id="select-none"><span>✗</span> Clear Selection</button>
                    <button class="action-btn" id="screenshot"><span>📷</span> Screenshot</button>
                </div>
            </div>
            
            <div class="panel-section">
                <div class="keyboard-hints">
                    <h4>⌨️ Shortcuts</h4>
                    <div class="key-hint"><span class="key">1-9</span> Toggle organism</div>
                    <div class="key-hint"><span class="key">Space</span> Animate</div>
                    <div class="key-hint"><span class="key">A</span> Select all</div>
                    <div class="key-hint"><span class="key">C</span> Clear</div>
                    <div class="key-hint"><span class="key">R</span> Radial view</div>
                </div>
            </div>
        </aside>
        
        <!-- Main Visualization -->
        <main class="visualization-area">
            <svg id="topology-svg"></svg>
            <div class="tooltip" id="tooltip"></div>
        </main>
        
        <!-- Right Panel - Analysis -->
        <aside class="analysis-panel">
            <div class="panel-section">
                <h3>📊 Architecture</h3>
                <div class="chart-container">
                    <h4>Hidden Layer Size</h4>
                    <div class="bar-chart" id="hidden-chart"></div>
                </div>
                <div class="chart-container">
                    <h4>Fitness Distribution</h4>
                    <div class="bar-chart" id="fitness-chart"></div>
                </div>
            </div>
            
            <div class="panel-section">
                <h3>🔢 Metrics</h3>
                <div class="metrics-grid">
                    <div class="metric-card"><div class="metric-value">{max_hidden}</div><div class="metric-label">Max Hidden</div></div>
                    <div class="metric-card"><div class="metric-value">{min_hidden}</div><div class="metric-label">Min Hidden</div></div>
                    <div class="metric-card"><div class="metric-value">{round(total_params/1000, 1)}K</div><div class="metric-label">Tot Params</div></div>
                    <div class="metric-card"><div class="metric-value" id="active-count">{num_organisms}</div><div class="metric-label">Active</div></div>
                </div>
            </div>
            
            <div class="panel-section">
                <h3>📋 Legend</h3>
                <div style="font-size: 0.85em;">
                    <div style="display: flex; align-items: center; gap: 8px; margin: 8px 0;"><svg width="16" height="16"><circle cx="8" cy="8" r="6" fill="#00ffff"/></svg><span>Input</span></div>
                    <div style="display: flex; align-items: center; gap: 8px; margin: 8px 0;"><svg width="16" height="16"><circle cx="8" cy="8" r="6" fill="#ff00ff"/></svg><span>Hidden</span></div>
                    <div style="display: flex; align-items: center; gap: 8px; margin: 8px 0;"><svg width="16" height="16"><circle cx="8" cy="8" r="6" fill="#ffff00"/></svg><span>Output</span></div>
                    <div style="display: flex; align-items: center; gap: 8px; margin: 8px 0;"><svg width="16" height="16"><circle cx="8" cy="8" r="6" fill="#00ff88"/></svg><span>Language</span></div>
                </div>
            </div>
        </aside>
    </div>
    
    <footer class="footer">
        Generated by 🦋 <a href="https://github.com/Yufok1/Convergence_Engine">Butterfly Convergence Engine</a> • Neural Lab v1.0
    </footer>
    
    <script>
        // ═══════════════════════════════════════════════════════════════
        // 🔬 NEURAL LAB - Interactive Ensemble Topology Explorer
        // ═══════════════════════════════════════════════════════════════
        
        const organisms = {json.dumps(organisms_data)};
        
        // State
        let activeOrganisms = new Set(organisms.map(o => o.index));
        let viewMode = 'overlay';
        let isAnimating = false;
        let animationFrame = null;
        let opacity = 0.7;
        let animationSpeed = 1;
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {{
            createOrganismList();
            createCharts();
            setupEventListeners();
            render();
        }});
        
        // ─────────────────────────────────────────────────────────────
        // UI SETUP
        // ─────────────────────────────────────────────────────────────
        
        function createOrganismList() {{
            const container = document.getElementById('organism-list');
            organisms.forEach(org => {{
                const item = document.createElement('div');
                item.className = 'organism-item active';
                item.style.setProperty('--org-color', org.color);
                item.dataset.index = org.index;
                item.innerHTML = `
                    <div class="color-indicator"></div>
                    <div class="org-info">
                        <div class="org-name">${{org.id}}</div>
                        <div class="org-meta">${{org.hidden_dim}}h • ${{org.params.toLocaleString()}} params</div>
                    </div>
                    <div class="fitness-bar"><div class="fitness-fill" style="width: ${{org.fitness * 100}}%"></div></div>
                `;
                item.addEventListener('click', (e) => {{
                    if (e.shiftKey) {{ activeOrganisms.clear(); activeOrganisms.add(org.index); updateOrganismUI(); }}
                    else {{ toggleOrganism(org.index); }}
                }});
                container.appendChild(item);
            }});
        }}
        
        function createCharts() {{
            const maxHidden = Math.max(...organisms.map(o => o.hidden_dim));
            const hiddenChart = document.getElementById('hidden-chart');
            const fitnessChart = document.getElementById('fitness-chart');
            
            organisms.forEach(org => {{
                hiddenChart.innerHTML += `<div class="bar-row"><div class="bar-label">${{org.id.slice(0,8)}}</div><div class="bar-track"><div class="bar-fill" style="width: ${{(org.hidden_dim/maxHidden)*100}}%; background: ${{org.color}}"><span class="bar-value">${{org.hidden_dim}}</span></div></div></div>`;
                fitnessChart.innerHTML += `<div class="bar-row"><div class="bar-label">${{org.id.slice(0,8)}}</div><div class="bar-track"><div class="bar-fill" style="width: ${{org.fitness*100}}%; background: ${{org.color}}"><span class="bar-value">${{org.fitness.toFixed(3)}}</span></div></div></div>`;
            }});
        }}
        
        function setupEventListeners() {{
            // View mode buttons
            document.querySelectorAll('.view-btn').forEach(btn => {{
                btn.addEventListener('click', () => {{
                    document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    viewMode = btn.dataset.view;
                    render();
                }});
            }});
            
            // Sliders
            document.getElementById('opacity-slider').addEventListener('input', (e) => {{
                opacity = e.target.value / 100;
                document.getElementById('opacity-value').textContent = e.target.value + '%';
                render();
            }});
            document.getElementById('speed-slider').addEventListener('input', (e) => {{
                animationSpeed = e.target.value / 5;
                document.getElementById('speed-value').textContent = animationSpeed.toFixed(1) + 'x';
            }});
            
            // Action buttons
            document.getElementById('toggle-animate').addEventListener('click', toggleAnimation);
            document.getElementById('select-all').addEventListener('click', selectAll);
            document.getElementById('select-none').addEventListener('click', selectNone);
            document.getElementById('screenshot').addEventListener('click', takeScreenshot);
            
            // Keyboard shortcuts
            document.addEventListener('keydown', (e) => {{
                if (e.key >= '1' && e.key <= '9') {{ const idx = parseInt(e.key) - 1; if (idx < organisms.length) toggleOrganism(idx); }}
                else if (e.key === ' ') {{ e.preventDefault(); toggleAnimation(); }}
                else if (e.key.toLowerCase() === 'a') {{ selectAll(); }}
                else if (e.key.toLowerCase() === 'c') {{ selectNone(); }}
                else if (e.key.toLowerCase() === 'r') {{ document.querySelector('[data-view="radial"]').click(); }}
            }});
            
            window.addEventListener('resize', render);
        }}
        
        // ─────────────────────────────────────────────────────────────
        // ORGANISM CONTROLS
        // ─────────────────────────────────────────────────────────────
        
        function toggleOrganism(index) {{
            if (activeOrganisms.has(index)) activeOrganisms.delete(index);
            else activeOrganisms.add(index);
            updateOrganismUI();
            render();
        }}
        
        function updateOrganismUI() {{
            document.querySelectorAll('.organism-item').forEach(item => {{
                item.classList.toggle('active', activeOrganisms.has(parseInt(item.dataset.index)));
            }});
            document.getElementById('active-count').textContent = activeOrganisms.size;
        }}
        
        function selectAll() {{ organisms.forEach(o => activeOrganisms.add(o.index)); updateOrganismUI(); render(); }}
        function selectNone() {{ activeOrganisms.clear(); updateOrganismUI(); render(); }}
        
        function toggleAnimation() {{
            isAnimating = !isAnimating;
            document.getElementById('toggle-animate').classList.toggle('animate-active', isAnimating);
            if (isAnimating) animate();
            else if (animationFrame) cancelAnimationFrame(animationFrame);
        }}
        
        function animate() {{
            if (!isAnimating) return;
            render(true);
            animationFrame = requestAnimationFrame(animate);
        }}
        
        function takeScreenshot() {{
            const svg = document.getElementById('topology-svg');
            const svgData = new XMLSerializer().serializeToString(svg);
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const img = new Image();
            canvas.width = svg.clientWidth * 2;
            canvas.height = svg.clientHeight * 2;
            ctx.scale(2, 2);
            ctx.fillStyle = '#0a0a0f';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            img.onload = () => {{
                ctx.drawImage(img, 0, 0);
                const link = document.createElement('a');
                link.download = 'neural_topology.png';
                link.href = canvas.toDataURL('image/png');
                link.click();
            }};
            img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
        }}
        
        // ─────────────────────────────────────────────────────────────
        // RENDERING ENGINE
        // ─────────────────────────────────────────────────────────────
        
        function render(animating = false) {{
            const svg = document.getElementById('topology-svg');
            const rect = svg.getBoundingClientRect();
            const width = rect.width || 800;
            const height = rect.height || 600;
            
            svg.innerHTML = '';
            svg.setAttribute('viewBox', `0 0 ${{width}} ${{height}}`);
            
            const active = organisms.filter(o => activeOrganisms.has(o.index));
            if (active.length === 0) return;
            
            switch(viewMode) {{
                case 'overlay': renderOverlay(svg, width, height, active, animating); break;
                case 'radial': renderRadial(svg, width, height, active, animating); break;
                case 'stack': renderStacked(svg, width, height, active); break;
                case 'grid': renderGrid(svg, width, height, active); break;
                case 'weights': renderWeights(svg, width, height, active); break;
            }}
        }}
        
        function renderOverlay(svg, width, height, active, animating) {{
            const padding = 80;
            const layerX = [padding, width * 0.35, width * 0.65, width - padding];
            
            ['INPUT', 'HIDDEN', 'OUTPUT', 'LANGUAGE'].forEach((label, i) => addText(svg, layerX[i], 30, label, '#444', 11));
            
            active.forEach((org, idx) => {{
                const g = createGroup(svg, opacity - (idx * 0.03));
                const nodes = {{
                    input: createLayerNodes(org.input_dim, layerX[0], height, padding),
                    hidden: createLayerNodes(org.hidden_dim, layerX[1], height, padding),
                    output: createLayerNodes(org.output_dim, layerX[2], height, padding),
                    language: org.use_language ? createLayerNodes(Math.min(org.vocab_size, 15), layerX[3], height, padding) : []
                }};
                
                drawConnections(g, nodes.input, nodes.hidden, org.color, 0.15, animating);
                drawConnections(g, nodes.hidden, nodes.output, org.color, 0.2, animating);
                if (nodes.language.length) drawConnections(g, nodes.hidden, nodes.language, org.color, 0.1, animating);
                
                nodes.input.forEach(n => drawNode(g, n.x, n.y, 5, '#00ffff', org.color, org, 'input', animating));
                nodes.hidden.forEach(n => drawNode(g, n.x, n.y, 6, '#ff00ff', org.color, org, 'hidden', animating));
                nodes.output.forEach(n => drawNode(g, n.x, n.y, 7, '#ffff00', org.color, org, 'output', animating));
                nodes.language.forEach(n => drawNode(g, n.x, n.y, 4, '#00ff88', org.color, org, 'language', animating));
            }});
        }}
        
        function renderRadial(svg, width, height, active, animating) {{
            const cx = width / 2, cy = height / 2;
            const maxRadius = Math.min(width, height) * 0.4;
            
            [0.25, 0.5, 0.75, 1].forEach(r => {{
                const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                circle.setAttribute('cx', cx); circle.setAttribute('cy', cy);
                circle.setAttribute('r', maxRadius * r);
                circle.setAttribute('fill', 'none'); circle.setAttribute('stroke', '#222'); circle.setAttribute('stroke-dasharray', '5,5');
                svg.appendChild(circle);
            }});
            
            active.forEach((org, idx) => {{
                const g = createGroup(svg, opacity);
                const angleOffset = (idx / active.length) * Math.PI * 2;
                const inputNodes = createRadialNodes(org.input_dim, cx, cy, maxRadius * 0.25, angleOffset);
                const hiddenNodes = createRadialNodes(org.hidden_dim, cx, cy, maxRadius * 0.55, angleOffset);
                const outputNodes = createRadialNodes(org.output_dim, cx, cy, maxRadius * 0.85, angleOffset);
                
                drawConnections(g, inputNodes, hiddenNodes, org.color, 0.1, animating);
                drawConnections(g, hiddenNodes, outputNodes, org.color, 0.15, animating);
                
                inputNodes.forEach(n => drawNode(g, n.x, n.y, 4, '#00ffff', org.color, org, 'input', animating));
                hiddenNodes.forEach(n => drawNode(g, n.x, n.y, 5, '#ff00ff', org.color, org, 'hidden', animating));
                outputNodes.forEach(n => drawNode(g, n.x, n.y, 6, '#ffff00', org.color, org, 'output', animating));
            }});
            
            addText(svg, cx, cy, '🧠', '#fff', 24);
        }}
        
        function renderStacked(svg, width, height, active) {{
            const rowHeight = height / active.length;
            active.forEach((org, idx) => renderOrganism(svg, org, 0, idx * rowHeight, width, rowHeight * 0.9));
        }}
        
        function renderGrid(svg, width, height, active) {{
            const cols = Math.ceil(Math.sqrt(active.length));
            const rows = Math.ceil(active.length / cols);
            const cellW = width / cols, cellH = height / rows;
            active.forEach((org, idx) => {{
                const col = idx % cols, row = Math.floor(idx / cols);
                renderOrganism(svg, org, col * cellW, row * cellH, cellW * 0.95, cellH * 0.95);
            }});
        }}
        
        // ─────────────────────────────────────────────────────────────
        // WEIGHT HEATMAP VIEW - The Soul of the Network
        // ─────────────────────────────────────────────────────────────
        function renderWeights(svg, width, height, active) {{
            if (active.length === 0) return;
            
            const org = active[0];
            const weights = org.weights;
            
            if (!weights || (!weights.ih.length && !weights.ho.length)) {{
                addText(svg, width/2, height/2, 'No weight data available', '#666', 16);
                addText(svg, width/2, height/2 + 25, '(Weights extracted during cocoon compilation)', '#555', 12);
                return;
            }}
            
            addText(svg, width/2, 35, `🧠 ${{org.id}} - Weight Heatmap`, org.color, 16);
            
            const matrixGap = 60;
            const ihWidth = Math.min(weights.ih[0]?.length || 0, 20);
            const ihHeight = weights.ih.length;
            const hoWidth = Math.min(weights.ho[0]?.length || 0, 20);
            const hoHeight = weights.ho.length;
            
            const cellSize = Math.min(20, (width - 200) / Math.max(ihWidth + hoWidth + 4, 10), (height - 200) / Math.max(ihHeight, hoHeight, 8));
            
            if (weights.ih.length > 0) {{
                const ihStartX = 80;
                const ihStartY = 80;
                addText(svg, ihStartX + ihWidth * cellSize / 2, ihStartY - 15, 'Input → Hidden', '#00ffff', 12);
                
                weights.ih.forEach((row, i) => {{
                    row.forEach((val, j) => {{
                        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                        rect.setAttribute('x', ihStartX + j * cellSize);
                        rect.setAttribute('y', ihStartY + i * cellSize);
                        rect.setAttribute('width', cellSize - 1);
                        rect.setAttribute('height', cellSize - 1);
                        rect.setAttribute('fill', weightToColor(val, weights.stats.ih_max));
                        rect.setAttribute('rx', 2);
                        const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
                        title.textContent = `[${{i}},${{j}}] = ${{val.toFixed(4)}}`;
                        rect.appendChild(title);
                        svg.appendChild(rect);
                    }});
                }});
                
                const ihStatsY = ihStartY + ihHeight * cellSize + 20;
                addText(svg, ihStartX, ihStatsY, `μ=${{weights.stats.ih_mean?.toFixed(3) || '?'}}  max=${{weights.stats.ih_max?.toFixed(3) || '?'}}  σ=${{weights.stats.ih_std?.toFixed(3) || '?'}}`, '#888', 10, 'start');
            }}
            
            if (weights.ho.length > 0) {{
                const hoStartX = 80 + (ihWidth + 4) * cellSize + matrixGap;
                const hoStartY = 80;
                addText(svg, hoStartX + hoWidth * cellSize / 2, hoStartY - 15, 'Hidden → Output', '#ff00ff', 12);
                
                weights.ho.forEach((row, i) => {{
                    row.forEach((val, j) => {{
                        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                        rect.setAttribute('x', hoStartX + j * cellSize);
                        rect.setAttribute('y', hoStartY + i * cellSize);
                        rect.setAttribute('width', cellSize - 1);
                        rect.setAttribute('height', cellSize - 1);
                        rect.setAttribute('fill', weightToColor(val, weights.stats.ho_max));
                        rect.setAttribute('rx', 2);
                        const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
                        title.textContent = `[${{i}},${{j}}] = ${{val.toFixed(4)}}`;
                        rect.appendChild(title);
                        svg.appendChild(rect);
                    }});
                }});
                
                const hoStatsY = hoStartY + hoHeight * cellSize + 20;
                addText(svg, hoStartX, hoStatsY, `μ=${{weights.stats.ho_mean?.toFixed(3) || '?'}}  max=${{weights.stats.ho_max?.toFixed(3) || '?'}}  σ=${{weights.stats.ho_std?.toFixed(3) || '?'}}`, '#888', 10, 'start');
            }}
            
            const legendX = width - 100;
            const legendY = 80;
            addText(svg, legendX + 30, legendY - 10, 'Magnitude', '#666', 10);
            
            for (let i = 0; i < 10; i++) {{
                const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                rect.setAttribute('x', legendX);
                rect.setAttribute('y', legendY + i * 15);
                rect.setAttribute('width', 20);
                rect.setAttribute('height', 14);
                rect.setAttribute('fill', weightToColor((10 - i) / 10, 1));
                rect.setAttribute('rx', 2);
                svg.appendChild(rect);
                addText(svg, legendX + 35, legendY + i * 15 + 10, ((10 - i) / 10).toFixed(1), '#555', 9, 'start');
            }}
            
            addText(svg, width/2, height - 30, `Network: ${{org.input_dim}}→${{org.hidden_dim}}→${{org.output_dim}} | Fitness: ${{org.fitness.toFixed(4)}}`, '#555', 11);
        }}
        
        function weightToColor(value, maxVal) {{
            const normalized = Math.min(Math.abs(value) / Math.max(maxVal, 0.001), 1);
            if (normalized < 0.25) {{
                const t = normalized / 0.25;
                return `rgb(${{Math.round(t * 150)}}, 0, ${{Math.round(t * 50)}})`;
            }} else if (normalized < 0.5) {{
                const t = (normalized - 0.25) / 0.25;
                return `rgb(${{Math.round(150 + t * 105)}}, ${{Math.round(t * 80)}}, ${{Math.round(50 - t * 50)}})`;
            }} else if (normalized < 0.75) {{
                const t = (normalized - 0.5) / 0.25;
                return `rgb(255, ${{Math.round(80 + t * 120)}}, 0)`;
            }} else {{
                const t = (normalized - 0.75) / 0.25;
                return `rgb(255, ${{Math.round(200 + t * 55)}}, ${{Math.round(t * 100)}})`;
            }}
        }}
        
        function renderOrganism(svg, org, x, y, w, h) {{
            const g = createGroup(svg, 1);
            g.setAttribute('transform', `translate(${{x}}, ${{y}})`);
            
            const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            bg.setAttribute('x', 5); bg.setAttribute('y', 5);
            bg.setAttribute('width', w - 10); bg.setAttribute('height', h - 10);
            bg.setAttribute('rx', 10); bg.setAttribute('fill', 'rgba(255,255,255,0.02)');
            bg.setAttribute('stroke', org.color); bg.setAttribute('stroke-opacity', 0.3);
            g.appendChild(bg);
            
            addText(g, 15, 25, `${{org.id}} (f=${{org.fitness.toFixed(3)}})`, org.color, 11, 'start');
            
            const padding = 40;
            const layers = org.use_language ? 4 : 3;
            const layerW = (w - padding * 2) / layers;
            
            const nodes = {{
                input: createLayerNodes(Math.min(org.input_dim, 12), padding, h - 40, padding),
                hidden: createLayerNodes(Math.min(org.hidden_dim, 12), padding + layerW, h - 40, padding),
                output: createLayerNodes(Math.min(org.output_dim, 8), padding + layerW * 2, h - 40, padding)
            }};
            
            drawConnections(g, nodes.input, nodes.hidden, org.color, 0.2, false);
            drawConnections(g, nodes.hidden, nodes.output, org.color, 0.25, false);
            
            nodes.input.forEach(n => drawNode(g, n.x, n.y, 4, '#00ffff', org.color, org, 'input', false));
            nodes.hidden.forEach(n => drawNode(g, n.x, n.y, 5, '#ff00ff', org.color, org, 'hidden', false));
            nodes.output.forEach(n => drawNode(g, n.x, n.y, 6, '#ffff00', org.color, org, 'output', false));
        }}
        
        // ─────────────────────────────────────────────────────────────
        // DRAWING HELPERS
        // ─────────────────────────────────────────────────────────────
        
        function createGroup(parent, opacity) {{
            const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            g.setAttribute('opacity', opacity);
            parent.appendChild(g);
            return g;
        }}
        
        function createLayerNodes(count, x, totalHeight, padding) {{
            const nodes = [];
            const displayCount = Math.min(count, 25);
            const spacing = (totalHeight - padding * 2) / Math.max(displayCount - 1, 1);
            for (let i = 0; i < displayCount; i++) {{
                nodes.push({{ x: x + (Math.random() - 0.5) * 10, y: padding + i * spacing }});
            }}
            return nodes;
        }}
        
        function createRadialNodes(count, cx, cy, radius, angleOffset) {{
            const nodes = [];
            const displayCount = Math.min(count, 20);
            const angleStep = (Math.PI * 0.8) / Math.max(displayCount - 1, 1);
            for (let i = 0; i < displayCount; i++) {{
                const angle = angleOffset + i * angleStep - Math.PI * 0.4;
                nodes.push({{ x: cx + Math.cos(angle) * radius, y: cy + Math.sin(angle) * radius }});
            }}
            return nodes;
        }}
        
        function drawConnections(parent, from, to, color, baseOpacity, animating) {{
            const step = Math.max(1, Math.floor(from.length / 8), Math.floor(to.length / 8));
            for (let i = 0; i < from.length; i += step) {{
                for (let j = 0; j < to.length; j += step) {{
                    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                    line.setAttribute('x1', from[i].x); line.setAttribute('y1', from[i].y);
                    line.setAttribute('x2', to[j].x); line.setAttribute('y2', to[j].y);
                    line.setAttribute('stroke', color); line.setAttribute('stroke-width', 0.8);
                    line.setAttribute('stroke-opacity', baseOpacity);
                    if (animating) line.classList.add('signal-path');
                    parent.appendChild(line);
                }}
            }}
        }}
        
        function drawNode(parent, x, y, r, fill, stroke, org, layerType, animating) {{
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', x); circle.setAttribute('cy', y); circle.setAttribute('r', r);
            circle.setAttribute('fill', fill); circle.setAttribute('stroke', stroke); circle.setAttribute('stroke-width', 1.5);
            if (animating) circle.classList.add('node-pulse');
            circle.addEventListener('mouseenter', (e) => showTooltip(e, org, layerType));
            circle.addEventListener('mouseleave', hideTooltip);
            parent.appendChild(circle);
        }}
        
        function addText(parent, x, y, text, fill, size, anchor = 'middle') {{
            const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            t.setAttribute('x', x); t.setAttribute('y', y);
            t.setAttribute('fill', fill); t.setAttribute('font-size', size);
            t.setAttribute('font-family', 'system-ui, sans-serif'); t.setAttribute('text-anchor', anchor);
            t.textContent = text;
            parent.appendChild(t);
        }}
        
        function addLine(parent, x1, y1, x2, y2, stroke) {{
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', x1); line.setAttribute('y1', y1);
            line.setAttribute('x2', x2); line.setAttribute('y2', y2);
            line.setAttribute('stroke', stroke); line.setAttribute('stroke-width', 1);
            parent.appendChild(line);
        }}
        
        // ─────────────────────────────────────────────────────────────
        // TOOLTIP
        // ─────────────────────────────────────────────────────────────
        
        function showTooltip(e, org, layerType) {{
            const tooltip = document.getElementById('tooltip');
            const layerDim = {{'input': org.input_dim, 'hidden': org.hidden_dim, 'output': org.output_dim, 'language': org.vocab_size}}[layerType];
            tooltip.innerHTML = `
                <h4 style="color: ${{org.color}}">${{org.id}}</h4>
                <div class="tip-row"><span class="tip-label">Layer:</span><span class="tip-value">${{layerType.toUpperCase()}}</span></div>
                <div class="tip-row"><span class="tip-label">Neurons:</span><span class="tip-value">${{layerDim}}</span></div>
                <div class="tip-row"><span class="tip-label">Fitness:</span><span class="tip-value">${{org.fitness.toFixed(4)}}</span></div>
                <div class="tip-row"><span class="tip-label">Params:</span><span class="tip-value">${{org.params.toLocaleString()}}</span></div>
            `;
            tooltip.style.left = (e.clientX + 15) + 'px';
            tooltip.style.top = (e.clientY - 10) + 'px';
            tooltip.classList.add('visible');
        }}
        
        function hideTooltip() {{ document.getElementById('tooltip').classList.remove('visible'); }}
    </script>
</body>
</html>'''
        
        return html

    def _compute_behavioral_fingerprint(self, brain: OrganismBrain, num_samples: int = 100) -> Dict[str, Any]:
        """
        Compute a behavioral fingerprint by sampling the brain's decision tendencies.
        
        This runs multiple random states through the network and analyzes:
        - Action distribution (which actions does it prefer?)
        - Decision confidence (how certain is it?)
        - Response patterns (how does it react to different input ranges?)
        
        Returns a dictionary with behavioral metrics that can be used for:
        - Clustering organisms by behavior
        - Filtering populations for specific traits
        - Visualizing behavioral space
        """
        brain.eval()
        
        action_counts = {i: 0 for i in range(brain.output_dim)}
        q_value_sums = {i: 0.0 for i in range(brain.output_dim)}
        confidence_scores = []
        
        # Response patterns for different input scenarios
        low_energy_actions = []    # When energy-related inputs are low
        high_threat_actions = []   # When threat signals are high
        social_actions = []        # When social signals are present
        
        with torch.no_grad():
            for i in range(num_samples):
                # Generate random state vector
                state = torch.rand(1, brain.input_dim)
                
                # Get Q-values
                q_values = brain(state)
                if isinstance(q_values, tuple):
                    q_values = q_values[0]  # Handle multi-head output
                
                q_np = q_values.squeeze().numpy()
                
                # Track action selection
                action = int(np.argmax(q_np))
                action_counts[action] += 1
                
                # Track Q-value magnitudes per action
                for j, qv in enumerate(q_np):
                    q_value_sums[j] += float(qv)
                
                # Track confidence (max Q minus mean Q)
                confidence = float(np.max(q_np) - np.mean(q_np))
                confidence_scores.append(confidence)
                
                # Scenario-specific responses
                # Low energy scenario (dims 6-8 low)
                low_energy_state = state.clone()
                low_energy_state[0, 6:9] = 0.1
                le_q = brain(low_energy_state)
                if isinstance(le_q, tuple):
                    le_q = le_q[0]
                low_energy_actions.append(int(torch.argmax(le_q).item()))
                
                # High threat scenario (dims 9-11 high)
                high_threat_state = state.clone()
                high_threat_state[0, 9:12] = 0.9
                ht_q = brain(high_threat_state)
                if isinstance(ht_q, tuple):
                    ht_q = ht_q[0]
                high_threat_actions.append(int(torch.argmax(ht_q).item()))
                
                # Social scenario (cooperative signals)
                social_state = state.clone()
                social_state[0, 15:18] = 0.8
                soc_q = brain(social_state)
                if isinstance(soc_q, tuple):
                    soc_q = soc_q[0]
                social_actions.append(int(torch.argmax(soc_q).item()))
        
        # Compute action distribution (normalized)
        total_actions = sum(action_counts.values())
        action_distribution = {
            ACTION_MAP.get(k, f'action_{k}'): round(v / total_actions, 4)
            for k, v in action_counts.items()
        }
        
        # Compute average Q-values per action
        avg_q_values = {
            ACTION_MAP.get(k, f'action_{k}'): round(v / num_samples, 4)
            for k, v in q_value_sums.items()
        }
        
        # Dominant action (most frequently chosen)
        dominant_action_idx = max(action_counts, key=action_counts.get)
        dominant_action = ACTION_MAP.get(dominant_action_idx, f'action_{dominant_action_idx}')
        
        # Behavioral tendencies (simplified categories)
        cooperative_score = action_distribution.get('cooperate', 0) + action_distribution.get('reproduce', 0) * 0.5
        competitive_score = action_distribution.get('compete', 0) + action_distribution.get('move', 0) * 0.3
        passive_score = action_distribution.get('rest', 0) + action_distribution.get('isolate', 0)
        
        # Scenario response analysis
        def mode_action(actions):
            if not actions:
                return 'unknown'
            counts = {}
            for a in actions:
                counts[a] = counts.get(a, 0) + 1
            mode_idx = max(counts, key=counts.get)
            return ACTION_MAP.get(mode_idx, f'action_{mode_idx}')
        
        return {
            'action_distribution': action_distribution,
            'avg_q_values': avg_q_values,
            'dominant_action': dominant_action,
            'dominant_action_percentage': round(action_counts[dominant_action_idx] / total_actions * 100, 1),
            'decision_confidence': {
                'mean': round(float(np.mean(confidence_scores)), 4),
                'std': round(float(np.std(confidence_scores)), 4),
                'min': round(float(np.min(confidence_scores)), 4),
                'max': round(float(np.max(confidence_scores)), 4)
            },
            'behavioral_tendencies': {
                'cooperative': round(cooperative_score, 4),
                'competitive': round(competitive_score, 4),
                'passive': round(passive_score, 4)
            },
            'scenario_responses': {
                'low_energy': mode_action(low_energy_actions),
                'high_threat': mode_action(high_threat_actions),
                'social_opportunity': mode_action(social_actions)
            },
            'behavioral_vector': [
                round(cooperative_score, 4),
                round(competitive_score, 4),
                round(passive_score, 4),
                round(float(np.mean(confidence_scores)), 4)
            ],
            'personality_label': self._classify_personality(cooperative_score, competitive_score, passive_score)
        }
    
    def _classify_personality(self, coop: float, comp: float, passive: float) -> str:
        """Classify organism into a personality archetype based on behavioral tendencies."""
        max_trait = max(coop, comp, passive)
        
        if max_trait < 0.2:
            return "balanced"
        elif coop == max_trait:
            if comp > 0.2:
                return "diplomatic"  # Cooperative but will compete if needed
            else:
                return "altruist"    # Strongly cooperative
        elif comp == max_trait:
            if coop > 0.2:
                return "opportunist" # Competitive but can cooperate
            else:
                return "aggressor"   # Strongly competitive
        elif passive == max_trait:
            if coop > comp:
                return "pacifist"    # Passive and cooperative
            else:
                return "hermit"      # Passive and isolated
        return "complex"

    def _merge_capsule_language_data(self, capsules: List['OrganismCapsule']) -> Optional[Dict[str, Any]]:
        """
        Merge language data from multiple capsules into a unified vocabulary.
        
        This creates a combined vocabulary that includes:
        - All unique concepts from all capsules
        - Merged word frequencies (summed)
        - Aggregated dialect signatures (averaged)
        - Union of all semantic associations
        
        Args:
            capsules: List of OrganismCapsule objects
            
        Returns:
            Merged language dictionary, or None if no capsules have language data
        """
        merged = {
            'vocabulary': [],
            'word_frequencies': {},
            'concepts': {},
            'semantic_associations': {},
            'dialect_signatures': [],
            'total_concepts': 0,
            'source_organisms': [],
            'ensemble_merged': True
        }
        
        has_language = False
        
        for cap in capsules:
            # Handle both capsules (.language) and live organisms (.atomic_language)
            lang_obj = None
            if hasattr(cap, 'language') and cap.language:
                lang_obj = cap.language
            elif hasattr(cap, 'atomic_language') and cap.atomic_language:
                lang_obj = cap.atomic_language
            
            if not lang_obj:
                continue
                
            has_language = True
            lang_data = lang_obj.to_dict() if hasattr(lang_obj, 'to_dict') else lang_obj
            
            # Track source organism - handle both capsule.organism_id and organism.species_id
            org_id = getattr(cap, 'organism_id', None) or getattr(cap, 'species_id', 'unknown')
            merged['source_organisms'].append(str(org_id))
            
            # Handle LanguageSnapshot format (atoms, concept_order, etc.)
            # OR legacy format (vocabulary, word_frequencies, etc.)
            
            # Extract vocabulary from atoms or concept_order
            if 'atoms' in lang_data:
                # LanguageSnapshot format - extract concept names as vocabulary
                for concept_id in lang_data['atoms'].keys():
                    if concept_id not in merged['vocabulary']:
                        merged['vocabulary'].append(concept_id)
                # Also merge atom data as concepts
                for concept_id, atom_data in lang_data['atoms'].items():
                    if concept_id not in merged['concepts']:
                        merged['concepts'][concept_id] = atom_data
                    else:
                        # Merge strengths by taking max
                        existing = merged['concepts'][concept_id]
                        if isinstance(atom_data, dict) and isinstance(existing, dict):
                            if atom_data.get('strength', 0) > existing.get('strength', 0):
                                merged['concepts'][concept_id] = atom_data
            
            # Also check concept_order for vocabulary
            if 'concept_order' in lang_data:
                for concept in lang_data['concept_order']:
                    if concept not in merged['vocabulary']:
                        merged['vocabulary'].append(concept)
            
            # Legacy format support
            if 'vocabulary' in lang_data:
                for word in lang_data['vocabulary']:
                    if word not in merged['vocabulary']:
                        merged['vocabulary'].append(word)
            
            # Merge word frequencies (sum them)
            if 'word_frequencies' in lang_data:
                for word, freq in lang_data['word_frequencies'].items():
                    merged['word_frequencies'][word] = merged['word_frequencies'].get(word, 0) + freq
            
            # Legacy concepts format
            if 'concepts' in lang_data:
                for concept_id, concept_data in lang_data['concepts'].items():
                    if concept_id not in merged['concepts']:
                        merged['concepts'][concept_id] = concept_data
            
            # Merge semantic associations
            if 'semantic_associations' in lang_data:
                for word, associations in lang_data['semantic_associations'].items():
                    if word not in merged['semantic_associations']:
                        merged['semantic_associations'][word] = associations
                    else:
                        # Merge association lists
                        existing = set(merged['semantic_associations'][word])
                        existing.update(associations)
                        merged['semantic_associations'][word] = list(existing)
            
            # Collect dialect signatures for averaging
            if 'dialect_signature' in lang_data:
                merged['dialect_signatures'].append(lang_data['dialect_signature'])
        
        if not has_language:
            return None
        
        # Finalize merged data
        merged['total_concepts'] = len(merged['concepts']) + len(merged['vocabulary'])
        
        # Average dialect signatures if we have multiple
        if merged['dialect_signatures']:
            import numpy as np
            try:
                avg_dialect = np.mean(merged['dialect_signatures'], axis=0).tolist()
                merged['dialect_signature'] = avg_dialect
            except Exception:
                merged['dialect_signature'] = merged['dialect_signatures'][0] if merged['dialect_signatures'] else []
        
        # Remove the list now that we've computed average
        del merged['dialect_signatures']
        
        logger.info(f"Merged language data from {len(merged['source_organisms'])} organisms: "
                   f"{merged['total_concepts']} concepts, {len(merged['vocabulary'])} words")
        
        return merged

    def _serialize_semantic_convergence(self, context_memory: Any, 
                                        capsules: Optional[List['OrganismCapsule']] = None) -> Optional[Dict[str, Any]]:
        """
        🔗 Serialize semantic convergence data from ContextMemory.
        
        This captures:
        - Word embeddings (nn.Embedding 1000×64)
        - Language anchors (word → organism mappings)
        - Node word associations (organism → words)
        - Semantic config
        
        Args:
            context_memory: ContextMemory instance
            capsules: Optional capsules for filtering to relevant organisms
            
        Returns:
            Serialized semantic convergence data
        """
        if context_memory is None:
            return None
        
        try:
            semantic_data = {
                'version': '1.0',
                'source_note': 'Semantic Convergence - unified word embeddings from organism neural networks',
                'total_words': 0,
                'total_anchors': 0,
                'embedding_dim': getattr(context_memory, 'embedding_dim', 64),
                'max_vocab_size': getattr(context_memory, 'max_vocab_size', 1000),
                'organism_embedding_alpha': getattr(context_memory, 'organism_embedding_alpha', 0.1),
                'use_learned_embeddings': getattr(context_memory, 'use_learned_embeddings', True),
            }
            
            # Get capsule organism IDs for filtering
            capsule_org_ids = set()
            if capsules:
                for cap in capsules:
                    org_id = getattr(cap, 'organism_id', None) or getattr(cap, 'species_id', None)
                    if org_id:
                        capsule_org_ids.add(str(org_id))
                        capsule_org_ids.add(hash(str(org_id)))  # Also add hash version
            
            # Serialize language anchors (word → organisms)
            language_anchors = {}
            if hasattr(context_memory, 'language_anchors'):
                for word, org_ids in context_memory.language_anchors.items():
                    # Filter to capsule organisms if specified
                    if capsule_org_ids:
                        filtered_ids = [str(oid) for oid in org_ids if oid in capsule_org_ids or str(oid) in capsule_org_ids]
                        if filtered_ids:
                            language_anchors[word] = filtered_ids
                    else:
                        language_anchors[word] = [str(oid) for oid in org_ids]
            semantic_data['language_anchors'] = language_anchors
            semantic_data['total_anchors'] = sum(len(v) for v in language_anchors.values())
            
            # Serialize node word associations (organism → words)
            node_word_associations = {}
            if hasattr(context_memory, 'node_word_associations'):
                for org_id, words in context_memory.node_word_associations.items():
                    # Filter to capsule organisms if specified
                    if capsule_org_ids and org_id not in capsule_org_ids and str(org_id) not in capsule_org_ids:
                        continue
                    node_word_associations[str(org_id)] = list(words)
            semantic_data['node_word_associations'] = node_word_associations
            
            # Serialize word frequencies
            word_frequencies = {}
            if hasattr(context_memory, 'word_frequencies'):
                word_frequencies = dict(context_memory.word_frequencies)
            semantic_data['word_frequencies'] = word_frequencies
            semantic_data['total_words'] = len(word_frequencies)
            
            # Serialize word embeddings (compressed)
            word_embeddings_b64 = None
            if (hasattr(context_memory, 'word_embedding') and 
                context_memory.word_embedding is not None and
                hasattr(context_memory, 'vocabulary') and 
                context_memory.vocabulary is not None):
                try:
                    # Get all words in language anchors
                    words_to_export = set(language_anchors.keys())
                    # Also add top words by frequency
                    if word_frequencies:
                        sorted_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)
                        for word, _ in sorted_words[:500]:  # Top 500
                            words_to_export.add(word)
                    
                    embeddings_dict = {}
                    for word in words_to_export:
                        token_id = context_memory.vocabulary.get_id(word)
                        if token_id is not None and token_id < context_memory.word_embedding.weight.shape[0]:
                            embed = context_memory.word_embedding.weight[token_id].detach().cpu().numpy().tolist()
                            embeddings_dict[word] = embed
                    
                    if embeddings_dict:
                        embed_json = json.dumps(embeddings_dict)
                        embed_bytes = zlib.compress(embed_json.encode('utf-8'), level=9)
                        word_embeddings_b64 = base64.b64encode(embed_bytes).decode('ascii')
                        semantic_data['word_embeddings_compressed'] = word_embeddings_b64
                        semantic_data['word_embeddings_count'] = len(embeddings_dict)
                except Exception as e:
                    logger.warning(f"Could not serialize word embeddings: {e}")
            
            return semantic_data
            
        except Exception as e:
            logger.warning(f"Could not serialize semantic convergence: {e}")
            return None
    
    def _serialize_knowledge_web_full(self, knowledge_web: Any) -> Optional[Dict[str, Any]]:
        """
        🌐 Serialize full LinguisticKnowledgeWeb data INCLUDING BASE VOCABULARY POOL.
        
        This captures:
        - FULL base vocabulary pool (74,557+ concepts)
        - Runtime learned concepts (merged with higher priority)
        - All relations
        - Semantic frames
        - Discovery history
        
        Args:
            knowledge_web: LinguisticKnowledgeWeb instance (runtime)
            
        Returns:
            Serialized knowledge web data with full vocabulary
        """
        # Use the new method that includes base pool
        return self._build_full_knowledge_web_export(knowledge_web)
    
    def _serialize_causation_system(self, causation_explorer: Any,
                                    capsules: Optional[List['OrganismCapsule']] = None) -> Optional[Dict[str, Any]]:
        """
        🔬 Serialize causation system events.
        
        This captures:
        - Events for exported organisms
        - Event statistics
        - Causal chains
        
        Args:
            causation_explorer: CausationExplorer instance
            capsules: Optional capsules for filtering
            
        Returns:
            Serialized causation data
        """
        if causation_explorer is None:
            return None
        
        try:
            causation_data = {
                'version': '1.0',
                'source_note': 'Causation Explorer - event history and causal chains',
                'total_events': 0,
                'events_by_component': {},
                'events_by_type': {},
            }
            
            # Get capsule organism IDs
            capsule_org_ids = set()
            if capsules:
                for cap in capsules:
                    org_id = getattr(cap, 'organism_id', None) or getattr(cap, 'species_id', None)
                    if org_id:
                        capsule_org_ids.add(str(org_id))
            
            # Collect events
            events = []
            if hasattr(causation_explorer, 'events'):
                for event_id, event in list(causation_explorer.events.items())[:2000]:  # Max 2k events
                    event_org_id = event.data.get('organism_id')
                    
                    # Filter by organism if capsules specified
                    if capsule_org_ids and event_org_id and str(event_org_id) not in capsule_org_ids:
                        continue
                    
                    events.append({
                        'id': event_id,
                        'timestamp': event.timestamp,
                        'component': event.component,
                        'event_type': event.event_type,
                        'data': event.data,
                    })
                    
                    # Count by component and type
                    causation_data['events_by_component'][event.component] = \
                        causation_data['events_by_component'].get(event.component, 0) + 1
                    causation_data['events_by_type'][event.event_type] = \
                        causation_data['events_by_type'].get(event.event_type, 0) + 1
            
            causation_data['events'] = events
            causation_data['total_events'] = len(events)
            
            return causation_data
            
        except Exception as e:
            logger.warning(f"Could not serialize causation system: {e}")
            return None
    
    def _serialize_alliance_system(self, alliance_system: Any,
                                   capsules: Optional[List['OrganismCapsule']] = None) -> Optional[Dict[str, Any]]:
        """
        🏛️ Serialize alliance system state.
        
        This captures:
        - Alliance memberships
        - Reputation scores
        - Battle history
        
        Args:
            alliance_system: AllianceWarfare instance
            capsules: Optional capsules for filtering
            
        Returns:
            Serialized alliance data
        """
        if alliance_system is None:
            return None
        
        try:
            alliance_data = {
                'version': '1.0',
                'source_note': 'Alliance Warfare - social structures and reputation',
                'alliance_count': 0,
            }
            
            # Get capsule organism IDs
            capsule_org_ids = set()
            if capsules:
                for cap in capsules:
                    org_id = getattr(cap, 'organism_id', None) or getattr(cap, 'species_id', None)
                    if org_id:
                        capsule_org_ids.add(str(org_id))
            
            # Serialize alliances
            alliances = {}
            if hasattr(alliance_system, 'alliances'):
                for alliance_id, alliance in alliance_system.alliances.items():
                    members = list(getattr(alliance, 'members', []))
                    
                    # Filter by capsule organisms if specified
                    if capsule_org_ids:
                        members = [m for m in members if str(m) in capsule_org_ids]
                        if not members:
                            continue
                    
                    alliances[str(alliance_id)] = {
                        'members': [str(m) for m in members],
                        'tier': getattr(alliance, 'tier', 1),
                        'reputation': getattr(alliance, 'reputation', 0.5),
                        'founding_generation': getattr(alliance, 'founding_generation', 0),
                    }
            
            alliance_data['alliances'] = alliances
            alliance_data['alliance_count'] = len(alliances)
            
            # Serialize organism reputations
            reputations = {}
            if hasattr(alliance_system, 'reputation_scores'):
                for org_id, score in alliance_system.reputation_scores.items():
                    if capsule_org_ids and str(org_id) not in capsule_org_ids:
                        continue
                    reputations[str(org_id)] = float(score)
            alliance_data['reputations'] = reputations
            
            return alliance_data
            
        except Exception as e:
            logger.warning(f"Could not serialize alliance system: {e}")
            return None

    def _serialize_context_memory_full(self, context_memory: Any,
                                       capsules: Optional[List['OrganismCapsule']] = None) -> Optional[Dict[str, Any]]:
        """
        🧠 Serialize full context memory data for standalone_butterfly_chat.py compatibility.
        
        This exports data in the format expected by standalone_butterfly_chat.py:
        - language_anchors: word → organism IDs
        - node_word_associations: organism → words
        - word_frequencies: word usage counts
        - ml_analysis: TF-IDF scores and semantic analysis
        - organism_sequences: recent token sequences per organism
        
        Args:
            context_memory: ContextMemory instance
            capsules: Optional capsules for filtering
            
        Returns:
            Serialized context memory data in standalone chat format
        """
        if context_memory is None:
            return None
        
        try:
            # Get capsule organism IDs for filtering
            capsule_org_ids = set()
            if capsules:
                for cap in capsules:
                    org_id = getattr(cap, 'organism_id', None) or getattr(cap, 'species_id', None)
                    if org_id:
                        capsule_org_ids.add(str(org_id))
                        capsule_org_ids.add(hash(str(org_id)))
            
            contex