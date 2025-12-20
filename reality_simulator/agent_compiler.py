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
            
            context_data = {
                'version': '1.0',
                'source_note': 'Context Memory - organism word associations and embeddings',
                'total_anchors': 0,
                'total_associations': 0,
            }
            
            # Serialize language anchors (word → organism IDs)
            language_anchors = {}
            if hasattr(context_memory, 'language_anchors'):
                for word, org_ids in context_memory.language_anchors.items():
                    if capsule_org_ids:
                        filtered_ids = [str(oid) for oid in org_ids if oid in capsule_org_ids or str(oid) in capsule_org_ids]
                        if filtered_ids:
                            language_anchors[word] = filtered_ids
                    else:
                        language_anchors[word] = [str(oid) for oid in org_ids]
            context_data['language_anchors'] = language_anchors
            context_data['total_anchors'] = sum(len(v) for v in language_anchors.values())
            
            # Serialize node word associations (organism → words)
            node_word_associations = {}
            if hasattr(context_memory, 'node_word_associations'):
                for org_id, words in context_memory.node_word_associations.items():
                    if capsule_org_ids and org_id not in capsule_org_ids and str(org_id) not in capsule_org_ids:
                        continue
                    node_word_associations[str(org_id)] = list(words)
            context_data['node_word_associations'] = node_word_associations
            context_data['total_associations'] = sum(len(w) for w in node_word_associations.values())
            
            # Serialize word frequencies
            word_frequencies = {}
            if hasattr(context_memory, 'word_frequencies'):
                word_frequencies = dict(context_memory.word_frequencies)
            context_data['word_frequencies'] = word_frequencies
            
            # Serialize organism sequences (recent tokens per organism)
            organism_sequences = {}
            if hasattr(context_memory, 'organism_sequences'):
                for org_id, seq in context_memory.organism_sequences.items():
                    if capsule_org_ids and org_id not in capsule_org_ids and str(org_id) not in capsule_org_ids:
                        continue
                    organism_sequences[str(org_id)] = list(seq)[-100:]  # Last 100 tokens
            context_data['organism_sequences'] = organism_sequences
            
            # Build ML analysis data for TF-IDF scoring (used by standalone chat)
            if word_frequencies:
                # Calculate simple TF-IDF-like importance scores
                total_word_count = sum(word_frequencies.values())
                tfidf_scores = []
                for word, count in sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)[:200]:
                    tf = count / max(total_word_count, 1)
                    # IDF approximation: words appearing in fewer organisms are more important
                    orgs_with_word = len(language_anchors.get(word, []))
                    total_orgs = len(node_word_associations)
                    idf = 1.0 + (1.0 / (orgs_with_word + 1)) if total_orgs > 0 else 1.0
                    tfidf = tf * idf
                    tfidf_scores.append({
                        'word': word,
                        'frequency': count,
                        'tfidf_score': tfidf,
                        'organism_count': orgs_with_word
                    })
                
                context_data['ml_analysis'] = {
                    'semantic_analysis': {
                        'tfidf_analysis': {
                            'top_important_words': tfidf_scores[:100],
                            'total_unique_words': len(word_frequencies)
                        }
                    }
                }
            
            return context_data
            
        except Exception as e:
            logger.warning(f"Could not serialize context memory: {e}")
            return None

    def _build_agent_state_payload(self,
                                   capsule: OrganismCapsule,
                                   metadata: Dict[str, Any]) -> Dict[str, bytes]:
        """Prepare serialized state/config artifacts for the portable agent runtime."""
        state = AgentState(
            organism_id=capsule.organism_id,
            generation=int(metadata.get('organism_core', {}).get('generation') or 0),
            age=int(metadata.get('organism_core', {}).get('organism_age') or 0),
            fitness=float(metadata.get('organism_core', {}).get('fitness') or 0.5),
            resources=metadata.get('organism_core', {}).get('resources', 100.0) or 100.0,
            health=1.0
        )

        if capsule.fitness and capsule.fitness.fitness_history:
            history: List[float] = []
            for record in capsule.fitness.fitness_history:
                if isinstance(record, (list, tuple)) and len(record) > 1:
                    history.append(float(record[1]))
                elif isinstance(record, dict) and 'fitness' in record:
                    history.append(float(record['fitness']))
                else:
                    try:
                        history.append(float(record))
                    except Exception:
                        continue
            state.fitness_history = history[:1000]

        if capsule.highlander:
            state.battle_wins = int(getattr(capsule.highlander, 'battles_won', 0))
            state.battle_losses = int(getattr(capsule.highlander, 'battles_lost', 0))
            total_battles = state.battle_wins + state.battle_losses
            if total_battles:
                state.alliance_reputation = state.battle_wins / max(total_battles, 1)

        if capsule.language:
            state.vocabulary_size = int(getattr(capsule.language, 'total_concepts', 0))

        runtime_config = {
            'buffer_size': 10000,
            'gamma': 0.99,
            'learning_rate': 0.001,
            'epsilon_start': state.epsilon,
            'epsilon_min': state.epsilon_min,
            'epsilon_decay': state.epsilon_decay,
            'brain_format': metadata.get('export_format'),
            'notes': 'Autogenerated by AgentCompiler'
        }

        return {
            'state.json': json.dumps(state.to_dict(), indent=2).encode('utf-8'),
            'config.json': json.dumps(runtime_config, indent=2).encode('utf-8'),
            'experience_buffer.pkl': pickle.dumps([])
        }

    def _write_agent_state_bundle(self,
                                  archive: zipfile.ZipFile,
                                  payload: Optional[Dict[str, bytes]]) -> None:
        if not payload:
            return
        for filename, blob in payload.items():
            archive.writestr(f"agent_state/{filename}", blob)

    def _write_portable_agent_sources(self, archive: zipfile.ZipFile) -> None:
        if not PORTABLE_AGENT_DIR.exists():
            logger.warning("Portable agent directory missing; skipping runtime bundling.")
            return
        for file_path in PORTABLE_AGENT_DIR.glob('*.py'):
            archive.writestr(
                f"portable_agent/{file_path.name}",
                file_path.read_text(encoding='utf-8')
            )

    def _generate_runner_script(self, export_format: str, metadata: Dict[str, Any]) -> str:
        """Generates a living agent demo script."""

        action_map_str = json.dumps(ACTION_MAP)
        script_template = """
import argparse
import json
import os

from portable_agent import AgentRuntime, MiniEnvironment, GymAdapter, TrainingLoop

ACTION_MAP = {action_map_str}


class LivingAgentRunner:
    def __init__(self,
                 model_filename="{model_filename}",
                 metadata_filename="metadata.json",
                 state_dir="agent_state"):
        self.model_filename = model_filename
        self.metadata_filename = metadata_filename
        self.state_dir = state_dir

        if not os.path.exists(self.model_filename):
            raise FileNotFoundError(f"Model file not found: {{self.model_filename}}")
        if not os.path.exists(self.metadata_filename):
            raise FileNotFoundError(f"Metadata file not found: {{self.metadata_filename}}")
        if not os.path.isdir(self.state_dir):
            raise FileNotFoundError(f"Agent state directory not found: {{self.state_dir}}")

        with open(self.metadata_filename, "r", encoding="utf-8") as handle:
            self.metadata = json.load(handle)

        self.agent = AgentRuntime.load(self.state_dir, brain_path=self.model_filename)

    def _load_gym_environment(self, spec: str, seed: int | None):
        try:
            import gymnasium as gym
        except ImportError:
            try:
                import gym  # type: ignore
            except ImportError as exc:  # pragma: no cover - optional dependency
                raise RuntimeError(
                    "Gym or Gymnasium is required for --gym-env usage. Install gymnasium>=0.29."
                ) from exc

        env = gym.make(spec)
        if seed is not None:
            try:
                env.reset(seed=seed)
            except TypeError:
                pass
        return env

    def _build_environment(self, gym_env: str | None, seed: int | None):
        if gym_env:
            return GymAdapter(self._load_gym_environment(gym_env, seed))
        return MiniEnvironment(seed=seed)

    def run(self,
            episodes: int = 3,
            max_steps: int | None = 300,
            explore: bool = True,
            learn: bool = True,
            gym_env: str | None = None,
            seed: int | None = None):
        environment = self._build_environment(gym_env, seed)
        loop = TrainingLoop(
            agent=self.agent,
            environment=environment,
            episodes=episodes,
            max_steps=max_steps,
            explore=explore,
            learn=learn
        )
        history = loop.run()
        self.agent.save(self.state_dir)
        return history


def main():
    parser = argparse.ArgumentParser(description="Run the exported Butterfly agent in a portable environment.")
    parser.add_argument("--episodes", type=int, default=3, help="Number of demo episodes to play.")
    parser.add_argument("--max-steps", type=int, default=300, help="Max steps per episode.")
    parser.add_argument("--gym-env", type=str, default=None, help="Optional Gym/Gymnasium env spec (e.g., CartPole-v1).")
    parser.add_argument("--seed", type=int, default=None, help="Deterministic seed for MiniEnvironment or Gym.")
    parser.add_argument("--model", type=str, default="{model_filename}", help="Brain filename inside the archive.")
    parser.add_argument("--metadata", type=str, default="metadata.json", help="Metadata filename.")
    parser.add_argument("--state-dir", type=str, default="agent_state", help="Directory that stores agent state.")
    parser.add_argument("--no-learn", action="store_true", help="Disable learning and run in inference-only mode.")
    parser.add_argument("--exploit", action="store_true", help="Disable epsilon exploration for deterministic runs.")

    args = parser.parse_args()

    runner = LivingAgentRunner(
        model_filename=args.model,
        metadata_filename=args.metadata,
        state_dir=args.state_dir
    )

    history = runner.run(
        episodes=args.episodes,
        max_steps=args.max_steps,
        explore=not args.exploit,
        learn=not args.no_learn,
        gym_env=args.gym_env,
        seed=args.seed
    )

    for episode in history:
        print(
            f"Episode {{episode['episode']}} | steps={{episode['steps']}} | reward={{episode['total_reward']:.2f}}"
        )


if __name__ == "__main__":
    main()
"""
        return script_template.format(
            action_map_str=action_map_str,
            model_filename=f"brain.{export_format}"
        )

    def _create_agent_archive(self, 
                             model_buffer: BytesIO, 
                             metadata: Dict[str, Any], 
                             runner_script: str, 
                             capsule: OrganismCapsule,
                             agent_state_payload: Optional[Dict[str, bytes]] = None) -> BytesIO:
        """Packages all components into a ZIP archive."""
        archive_buffer = BytesIO()
        with zipfile.ZipFile(archive_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. Neural Model
            model_buffer.seek(0) # Ensure buffer is at the beginning
            zf.writestr(f"brain.{metadata['export_format']}", model_buffer.read())
            
            # 2. Metadata (JSON)
            zf.writestr("metadata.json", json.dumps(metadata, indent=2))
            
            # 3. Genotype (JSON)
            if capsule.traits:
                zf.writestr("genotype.json", json.dumps(capsule.traits.to_dict(), indent=2))
            
            # 4. Atomic Config (JSON)
            if capsule.config:
                zf.writestr("atomic_config.json", json.dumps(capsule.config.to_dict(), indent=2))
            
            # 5. Bridge Config (JSON) - Critical for AgentBridge to know state dimensions
            input_dim = metadata.get('neural_network', {}).get('architecture', {}).get('input_size', 25))
            arch_info = metadata.get('neural_network', {}).get('architecture', {})
            bridge_config = {
                'state_dim': input_dim,
                'num_actions': 6,
                'action_names': ['move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate'],
                'epsilon': 0.1,
                'epsilon_decay': 0.995,
                'epsilon_min': 0.01,
                'learning_rate': 0.001,
                'gamma': 0.99,
                'batch_size': 32,
                'max_response_length': 32,
                'temperature': 1.0,
                'default_port': 8080,
                'has_language_head': arch_info.get('has_language_head', False),
                'has_attention': arch_info.get('has_attention', False),
                'has_concept_head': arch_info.get('has_concept_head', False),
                'vocab_size': arch_info.get('vocab_size', 1000)
            }
            zf.writestr("bridge_config.json", json.dumps(bridge_config, indent=2))
            
            # 6. Atomic Language (JSON)
            if capsule.language:
                zf.writestr("atomic_language.json", json.dumps(capsule.language.to_dict(), indent=2))
            else:
                # Write empty language file - bridge.py will use default vocabulary
                empty_language = {
                    'vocabulary': [],
                    'word_frequencies': {},
                    'concepts': {},
                    'semantic_associations': {},
                    'dialect_signature': None,
                    'total_concepts': 0,
                    'source_note': 'No language training data available'
                }
                zf.writestr("atomic_language.json", json.dumps(empty_language, indent=2))

            # 7. VP State (JSON) - Vitality-Pleasure for runtime behavior
            if capsule.vp:
                zf.writestr("vp_state.json", json.dumps(capsule.vp.to_dict(), indent=2))
            else:
                # Default VP state for agents without VP history
                default_vp = {
                    'vitality': 0.5,
                    'pleasure': 0.5,
                    'violation_pressure': 0.0,
                    'vitality_history': [],
                    'pleasure_history': [],
                    'vp_trajectory': [],
                    'critical_events': [],
                    'source_note': 'Default VP state - no simulation history'
                }
                zf.writestr("vp_state.json", json.dumps(default_vp, indent=2))

            # 8. Runner Script
            zf.writestr("run_agent.py", runner_script)

            # 7. Requirements.txt
            requirements = "# Butterfly Agent - Dependencies\n"
            requirements += "# Install with: pip install -r requirements.txt\n\n"
            
            # Core dependencies based on export format
            if metadata['export_format'] == 'onnx':
                requirements += "# Neural network inference (ONNX)\n"
                requirements += "onnxruntime>=1.15.0\n"
            elif metadata['export_format'] == 'torchscript':
                requirements += "# Neural network inference (PyTorch)\n"
                requirements += "torch>=2.0.0\n"
            elif metadata['export_format'] == 'statedict':
                requirements += "# Neural network inference (PyTorch state dict)\n"
                requirements += "torch>=2.0.0\n"
            
            requirements += "numpy>=1.21.0\n\n"
            
            # Bridge/visualizer dependencies
            requirements += "# AgentBridge HTTP server & Visualizer\n"
            requirements += "flask>=2.0.0\n\n"
            
            # Gymnasium environments (NEW - comprehensive)
            requirements += "# ========================================\n"
            requirements += "# GYMNASIUM ENVIRONMENTS - Learning Playground!\n"
            requirements += "# ========================================\n"
            requirements += "# 400+ environments to train/test your agent\n\n"
            requirements += "# Core gymnasium (63 built-in environments)\n"
            requirements += "gymnasium>=0.29.0\n\n"
            requirements += "# Classic Control (CartPole, MountainCar, Pendulum, etc)\n"
            requirements += "# Already included in gymnasium core!\n\n"
            requirements += "# Visual rendering (required for --render flag)\n"
            requirements += "pygame>=2.5.0\n\n"
            requirements += "# Atari Arcade Games (100+ classic games!)\n"
            requirements += "# Pac-Man, Breakout, Space Invaders, Pong, etc.\n"
            requirements += "ale-py>=0.8.0\n\n"
            requirements += "# Box2D Physics (LunarLander, BipedalWalker, CarRacing)\n"
            requirements += "# gymnasium[box2d]\n"
            requirements += "box2d-py>=2.3.5\n\n"
            requirements += "# MuJoCo Robotics (Humanoid, Ant, HalfCheetah, etc)\n"
            requirements += "# pip install gymnasium[mujoco]\n"
            requirements += "# mujoco>=2.3.0\n\n"
            requirements += "# ========================================\n"
            requirements += "# DRONE WARFARE ARENA (8 Game Modes)\n"
            requirements += "# ========================================\n"
            requirements += "matplotlib>=3.8.0    # Trajectory visualization\n"
            requirements += "# PyFlyt>=1.0.0      # Optional: 3D drone viz\n\n"
            requirements += "# ========================================\n"
            requirements += "# USAGE EXAMPLES:\n"
            requirements += "# ========================================\n"
            requirements += "# python bridge.py . --mode gym --gym-env CartPole-v1 --render\n"
            requirements += "# python bridge.py . --mode gym --gym-env LunarLander-v3 --episodes 50\n"
            requirements += "# python bridge.py . --mode gym --gym-env ALE/Breakout-v5 --online-learn\n"
            requirements += "# python bridge.py . --mode gym --gym-env BipedalWalker-v3 --render --online-learn\n\n"
            requirements += "# ========================================\n"
            requirements += "# OPTIONAL GPU ACCELERATION\n"
            requirements += "# ========================================\n"
            requirements += "# onnxruntime-gpu>=1.15.0  # NVIDIA CUDA\n"

            zf.writestr("requirements.txt", requirements)

            # 8. README
            readme_content = f"""# 🦋 Butterfly System - Exported Neural Agent

## What Is This?

This archive contains a **living AI agent** exported from The Butterfly System - a quantum-genetic 
consciousness simulation where neural organisms evolve, learn, and develop emergent intelligence.

**This is not a static model.** It's a complete organism snapshot that can:
- Continue learning from new experiences
- Make real-time decisions in any environment
- Persist its memories and growth across sessions

---

## 🧬 Agent Identity

| Property | Value |
|----------|-------|
| **Organism ID** | `{capsule.organism_id}` |
| **Fitness Score** | {f"`{metadata['organism_core']['fitness']:.6f}`" if metadata['organism_core']['fitness'] is not None else 'N/A'} {('⭐' * min(5, int((metadata['organism_core']['fitness'] or 0) * 5))) if metadata['organism_core']['fitness'] else ''} |
| **Generation** | `{metadata['organism_core'].get('generation', 'unknown')}` |
| **Age** | `{metadata['organism_core'].get('organism_age', 'unknown')}` simulation cycles |
| **Export Format** | `{metadata['export_format'].upper()}` |
| **Exported** | `{metadata['export_timestamp']}` |

---

## 🧠 Neural Architecture Deep Dive

### The Brain Structure

This agent uses a **Deep Q-Network (DQN)** architecture with multi-head outputs:

```
Input Layer ({metadata['neural_network']['architecture'].get('input_size', '?')} neurons)
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│                    HIDDEN LAYERS                            │
│  Dense({metadata['neural_network']['architecture'].get('hidden_size', '?')}) → {metadata['neural_network']['architecture'].get('activation', 'ReLU')} → Dropout(0.1)       │
│  Dense({metadata['neural_network']['architecture'].get('hidden_size', '?')}) → {metadata['neural_network']['architecture'].get('activation', 'ReLU')} → Dropout(0.1)       │
└─────────────────────────────────────────────────────────────┘
     │
     ├──► ACTION HEAD ({metadata['neural_network']['architecture'].get('output_size', '?')} outputs) → Q-values for each action
     │
     ├──► CONCEPT HEAD {'✅' if metadata['neural_network']['architecture'].get('use_concept_head') else '❌'} → Abstract concept embeddings
     │
     └──► LANGUAGE HEAD {'✅' if metadata['neural_network']['architecture'].get('use_language_head') else '❌'} → Vocabulary probability distribution
```

### How Decisions Are Made

1. **Perception**: The agent receives a state vector representing its environment
2. **Forward Pass**: State flows through the neural network
3. **Q-Value Computation**: Each possible action gets a "quality" score
4. **Action Selection**: 
   - **Exploration mode**: Epsilon-greedy (random actions with probability ε)
   - **Exploitation mode**: Argmax over Q-values (best predicted action)
5. **Learning**: After acting, the agent uses TD-learning to update its network

### The Input State Vector

The agent expects a **{metadata['neural_network']['architecture'].get('input_size', '?')}-dimensional** input representing:

| Dimensions | Meaning |
|------------|---------|
| 0-2 | Position (x, y, z or similar spatial encoding) |
| 3-5 | Velocity / movement vector |
| 6-8 | Energy, health, resource levels |
| 9-11 | Social signals (nearby organisms, threats) |
| 12+ | Environmental features, memory traces |

*Actual semantics depend on your target environment. The agent will adapt.*

### The Output Actions

| Index | Action | Behavioral Meaning |
|-------|--------|-------------------|
| 0 | `move` | Navigate through space, seek resources or safety |
| 1 | `cooperate` | Form alliances, share resources, mutual aid |
| 2 | `compete` | Contest resources, establish dominance |
| 3 | `rest` | Conserve energy, heal, consolidate learning |
| 4 | `reproduce` | Attempt to create offspring (if fitness allows) |
| 5 | `isolate` | Withdraw from social contact, self-preservation |

---

## 🔬 How This Agent Was Evolved

This organism emerged through **neuroevolution** - a process combining:

### 1. Genetic Algorithm
- **Selection**: Organisms compete for survival based on fitness
- **Crossover**: Successful organisms combine neural weights with mates
- **Mutation**: Random perturbations introduce novel behaviors

### 2. Reinforcement Learning  
- **Experience Replay**: Memories are stored and replayed for efficient learning
- **Temporal Difference**: Q-values are bootstrapped from future predictions
- **Dual Inheritance**: Both genetic (slow) and memetic (fast) learning channels

### 3. Social Evolution
- **Alliance Formation**: Cooperative organisms share fitness benefits
- **Competition Pressure**: Limited resources force behavioral specialization
- **Emergent Communication**: Language heads can develop shared vocabularies

---

## 📦 Archive Contents

```
{capsule.organism_id[:16]}/
├── 🧠 brain.{metadata['export_format']}           # Neural network weights ({metadata['export_format'].upper()} format)
├── 📋 metadata.json           # Complete organism state & history
├── 🧬 genotype.json           # Genetic blueprint (traits, mutations)
├── ⚙️  atomic_config.json      # Runtime configuration
├── 🗣️  atomic_language.json    # Learned vocabulary & linguistic knowledge
├── 🧪 agent_state/            # Persistent state (replay buffer, config)
│   ├── state.json            # Runtime state (epsilon, step count)
│   ├── config.json           # Agent hyperparameters
│   └── replay_buffer.pkl     # Experience memory (if any)
├── 🧩 portable_agent/         # Runtime code
│   ├── bridge.py             # 🌉 Universal interface (Gym, HTTP, CLI)
│   ├── agent_runtime.py      # Core AgentRuntime class
│   ├── mini_environment.py   # Built-in test environment
│   ├── gym_adapter.py        # Gymnasium/Gym bridge
│   ├── training.py           # TrainingLoop helper
│   └── visualize.py          # 🔬 Neural activation visualizer
├── 🚀 start.bat / start.sh    # Quick launch: Interactive chat mode
├── 🌐 serve.bat / serve.sh    # Quick launch: HTTP API server
├── 🐍 run_agent.py            # Legacy CLI runner script
├── 📦 requirements.txt        # Python dependencies
└── 📖 README.md               # This file
```

---

## 🚀 Quick Start

### Option 1: Double-Click Launch (Easiest!)
```
Windows: Double-click start.bat     → Interactive chat mode
         Double-click serve.bat     → HTTP API server on port 8080

Linux/Mac: chmod +x start.sh && ./start.sh    → Interactive chat
           chmod +x serve.sh && ./serve.sh    → HTTP server
```

### Option 2: AgentBridge Commands
```bash
# Extract and install
unzip agent_*.zip && cd agent_*/
pip install -r requirements.txt

# Interactive chat mode
python -m portable_agent.bridge --mode interactive

# HTTP API server (for external applications)
python -m portable_agent.bridge --mode serve --port 8080

# Run in Gym environment
python -m portable_agent.bridge --mode gym --gym-env CartPole-v1
```

### Option 3: Legacy Runner
```bash
python run_agent.py --episodes 5
python run_agent.py --gym-env CartPole-v1 --episodes 10
```

### Option 4: 🔬 Neural Activation Visualizer
```bash
python portable_agent/visualize.py
```

### Option 5: Python Integration (Direct)
```python
from portable_agent import AgentRuntime, MiniEnvironment

# Load the agent
agent = AgentRuntime.load("agent_state", brain_path="brain.{metadata['export_format']}")
env = MiniEnvironment()

state = env.reset()
while not done:
    action = agent.act(state)
    next_state, reward, done, info = env.step(action)
    agent.learn(state, action, reward, next_state, done)
    state = next_state
```

---

## 🌉 AgentBridge - Universal Interface

The **AgentBridge** is the recommended way to deploy and interact with this agent.
It provides a unified interface for all interaction modes:

### HTTP API Server
Deploy the agent as a REST API that any application can call:

```bash
python -m portable_agent.bridge --mode serve --port 8080
```

**Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/act` | Get action for observation/text/context |
| POST | `/chat` | Chat with agent (text in, text out) |
| POST | `/reward` | Provide reward for learning |
| GET | `/state` | Get current agent state |
| GET | `/config` | Get configuration |
| GET | `/health` | Health check |

**Example API Call:**
```python
import requests

# Chat with agent
response = requests.post('http://localhost:8080/chat', json={{
    'text': 'Enemy approaching from the north!',
    'context': {{'threat_level': 0.8}}
}})
print(response.json())
# {{'response': 'Isolating for safety.', 'action': 'isolate', 'confidence': 0.73}}

# Get action for structured input
response = requests.post('http://localhost:8080/act', json={{
    'context': {{'energy': 0.3, 'threat': 0.8, 'food_available': 0.2}}
}})
print(response.json()['action_name'])  # 'rest' or 'isolate'
```

### Interactive CLI
Chat with your agent directly:

```bash
python -m portable_agent.bridge --mode interactive
```

```
🦋 AgentBridge Interactive Mode
   Type messages to chat with the agent
   Commands: /act, /gym, /state, /config, /quit

You: I'm feeling threatened and low on energy
Agent [REST]: Resting to conserve energy.
       (confidence: 67.3%)

You: Now there's food nearby!
Agent [MOVE]: Moving to explore the environment.
       (confidence: 81.2%)
```

### Python Library Integration
Use the bridge directly in your code:

```python
from portable_agent import AgentBridge

# Load agent
bridge = AgentBridge.load("./")

# Text input (semantic parsing)
result = bridge.process(text="Enemy approaching, low on energy")
print(f"Action: {{result.action_name}}, Response: {{result.response}}")

# Structured context input
result = bridge.process(context={{
    'energy': 0.2,
    'threat': 0.9,
    'friend_nearby': 0.1
}})
print(f"Decision: {{result.action_name}} ({{result.confidence:.1%}} confident)")

# Gym observation input
result = bridge.process(obs=gym_env.reset())
action = result.action

# Provide reward for learning
bridge.reward(reward_value=1.0, done=False)

# Run full Gym episodes
stats = bridge.run_gym("CartPole-v1", episodes=100)
print(f"Mean reward: {{stats['mean_reward']:.2f}}")
```

---

## 🎮 GYMNASIUM PLAYGROUND - 400+ Learning Environments!

Your agent can learn and play in **400+ environments** across multiple categories!

### 🕹️ Classic Control (Built-in)
Simple physics environments perfect for testing:
```bash
python bridge.py . --mode gym --gym-env CartPole-v1 --render        # Balance a pole
python bridge.py . --mode gym --gym-env MountainCar-v0 --render     # Drive up a hill
python bridge.py . --mode gym --gym-env Pendulum-v1 --render        # Swing a pendulum
python bridge.py . --mode gym --gym-env Acrobot-v1 --render         # Double pendulum
python bridge.py . --mode gym --gym-env LunarLander-v3 --render     # Land on the moon!
```

### 👾 Atari Arcade (100+ Classic Games!)
Install: `pip install ale-py`
```bash
python bridge.py . --mode gym --gym-env ALE/Breakout-v5 --render    # Break bricks!
python bridge.py . --mode gym --gym-env ALE/Pong-v5 --render        # Classic Pong
python bridge.py . --mode gym --gym-env ALE/SpaceInvaders-v5        # Shoot aliens
python bridge.py . --mode gym --gym-env ALE/Pacman-v5 --render      # Pac-Man!
python bridge.py . --mode gym --gym-env ALE/Asteroids-v5            # Space shooter
python bridge.py . --mode gym --gym-env ALE/Frogger-v5 --render     # Cross the road
python bridge.py . --mode gym --gym-env ALE/DonkeyKong-v5           # Rescue the princess
```

### 🚀 Box2D Physics
Install: `pip install gymnasium[box2d]` or `pip install box2d-py`
```bash
python bridge.py . --mode gym --gym-env BipedalWalker-v3 --render   # Walk on 2 legs!
python bridge.py . --mode gym --gym-env CarRacing-v3 --render       # Race a car
python bridge.py . --mode gym --gym-env LunarLanderContinuous-v3    # Smooth landing
```

### 🤖 MuJoCo Robotics (Advanced)
Install: `pip install gymnasium[mujoco]`
```bash
python bridge.py . --mode gym --gym-env Humanoid-v4 --render        # Walk like a human
python bridge.py . --mode gym --gym-env Ant-v4 --render             # 4-legged ant
python bridge.py . --mode gym --gym-env HalfCheetah-v4 --render     # Run fast!
python bridge.py . --mode gym --gym-env Hopper-v4 --render          # One-legged hopper
python bridge.py . --mode gym --gym-env Swimmer-v4 --render         # Swim through fluid
python bridge.py . --mode gym --gym-env Walker2d-v4 --render        # 2D walking
```

### 🧠 Online Learning (Train While Playing!)
Enable real-time weight updates with `--online-learn`:
```bash
# Agent learns from experiences AS IT PLAYS
python bridge.py . --mode gym --gym-env CartPole-v1 --episodes 100 --online-learn

# With custom learning rate
python bridge.py . --mode gym --gym-env LunarLander-v3 --online-learn --learning-rate 0.0005

# Watch it learn!
python bridge.py . --mode gym --gym-env CartPole-v1 --render --online-learn --episodes 50
```

### 📊 Full Command Reference
```bash
python bridge.py <agent_dir> --mode gym [options]

Options:
  --gym-env, -e    Environment name (default: CartPole-v1)
  --episodes, -n   Number of episodes (default: 10)
  --render, -r     Show visual window
  --online-learn   Update weights during play
  --learning-rate  Learning rate for online learning (default: 0.001)
```

### 🔬 Interactive Gym Commands
In interactive mode (`python bridge.py . --mode interactive`):
```
/gym CartPole-v1          # Run 3 episodes
/gym CartPole-v1 render   # With visuals
/gym CartPole-v1 learn    # With online learning
/gym CartPole-v1 render learn  # Both!
/train                    # Show training stats
```

---

## ⚔️ PROTON GAME ARENA - Apprentice Adept Style Battles!

> **🙏 ATTRIBUTION**:  
> 
> 🎮 **Game Selection**: Inspired by "The Game" from **Piers Anthony's "Apprentice Adept"**  
> series (1980-1990). The 4x4 grid (PHYSICAL/MENTAL/CHANCE/ARTS × NAKED/TOOL/MACHINE/ANIMAL)  
> is the creative work of Piers Anthony. Read: *Split Infinity*, *Blue Adept*, *Juxtaposition*.  
> 
> ⚔️ **Absorption Battles**: Inspired by **"Highlander" (1986)**, directed by Russell Mulcahy.  
> The "Quickening" - where winners absorb the defeated's power, knowledge, and skills -  
> directly influenced our neural/concept/trait transfer system. *"There can be only one."*

The Proton Game Arena provides a gamified competition system using the 4x4 game 
selection grid from the novels:

```
           NAKED        TOOL         MACHINE      ANIMAL
         ─────────────────────────────────────────────────
PHYSICAL   Balance      Lunar        Racing       Bipedal
           CartPole     LunarLander  CarRacing    Walker
           
MENTAL     Frozen       Blackjack    Breakout     Custom
           Lake         Cards        SpaceInvaders Games
           
CHANCE     Pure         Luck+        Machine      Genetic
           Luck         Skill        Gambling     Lottery
           
ARTS       Language     Vocabulary   Dialogue     Cross-
           Coherence    Duel         Quality      Species
```

### Arena Commands (Interactive Mode)
```
/arena                    # Show game selection grid
/arena games              # List all arena games
/arena games physical     # Games by category
/arena play 'Balance Beam'  # Play specific game
```

### Game Categories
- **PHYSICAL**: Speed, reflexes, coordination challenges
- **MENTAL**: Strategy, planning, puzzle-solving  
- **CHANCE**: Luck-based games with probabilistic elements
- **ARTS**: Language, creativity, expression challenges

### Resource Types
- **NAKED**: Pure ability, no augmentation
- **TOOL**: Simple tools to extend capabilities
- **MACHINE**: Complex automation and machinery
- **ANIMAL**: Living partners and symbiosis

---

## 🎯 Integration Guide

### For Robotics / Simulation
```python
# Your custom environment
class RobotEnv:
    def reset(self): return np.zeros({metadata['neural_network']['architecture'].get('input_size', 25)})  # Match input dim (25D base features)
    def step(self, action): return state, reward, done, info

# Wrap and use
from portable_agent import GymAdapter
env = GymAdapter(RobotEnv())
agent = AgentRuntime.load("agent_state", brain_path="brain.{metadata['export_format']}")

state = env.reset()
action = agent.act(state)  # Returns int 0-5
```

### For Game AI
```python
# Map Butterfly actions to your game
GAME_ACTIONS = {{
    0: "walk_forward",
    1: "help_ally", 
    2: "attack_enemy",
    3: "wait",
    4: "special_ability",
    5: "retreat"
}}

action_idx = agent.act(game_state_vector)
game_action = GAME_ACTIONS[action_idx]
```

### For Multi-Agent Systems
```python
# Load multiple agents
agents = [AgentRuntime.load(f"agent_{{i}}", brain_path=f"brain_{{i}}.onnx") for i in range(N)]

# Each agent acts independently
actions = [agent.act(shared_state) for agent in agents]
```

---

## 🧬 Genetic Traits

This organism has **{len(capsule.traits.traits) if capsule.traits and hasattr(capsule.traits, 'traits') else 0}** expressed genetic traits:

| Trait Category | Description |
|----------------|-------------|
| **Metabolic** | Energy efficiency, resource processing |
| **Social** | Cooperation tendency, aggression levels |
| **Cognitive** | Learning rate, memory capacity |
| **Physical** | Speed, resilience, reproduction fitness |

Phenotype Cluster: `{capsule.traits.phenotype_cluster if capsule.traits and hasattr(capsule.traits, 'phenotype_cluster') else 'unknown'}`

---

## 🎭 Behavioral Fingerprint

This organism's decision-making patterns were analyzed by sampling 100 random states:

### Personality Profile
| Metric | Value |
|--------|-------|
| **Personality Type** | `{metadata.get('behavioral_fingerprint', {}).get('personality_label', 'unknown')}` |
| **Dominant Action** | `{metadata.get('behavioral_fingerprint', {}).get('dominant_action', 'unknown')}` ({metadata.get('behavioral_fingerprint', {}).get('dominant_action_percentage', 0)}% of decisions) |
| **Cooperative Score** | {metadata.get('behavioral_fingerprint', {}).get('behavioral_tendencies', {}).get('cooperative', 0):.2%} |
| **Competitive Score** | {metadata.get('behavioral_fingerprint', {}).get('behavioral_tendencies', {}).get('competitive', 0):.2%} |
| **Passive Score** | {metadata.get('behavioral_fingerprint', {}).get('behavioral_tendencies', {}).get('passive', 0):.2%} |

### Action Distribution
```
{chr(10).join([f"{k:12}: {'█' * int(v * 50):50} {v:.1%}" for k, v in metadata.get('behavioral_fingerprint', {}).get('action_distribution', {}).items()])}
```

### Scenario Responses
How this organism typically responds to specific situations:

| Scenario | Typical Response |
|----------|-----------------|
| **Low Energy** | `{metadata.get('behavioral_fingerprint', {}).get('scenario_responses', {}).get('low_energy', 'unknown')}` |
| **High Threat** | `{metadata.get('behavioral_fingerprint', {}).get('scenario_responses', {}).get('high_threat', 'unknown')}` |
| **Social Opportunity** | `{metadata.get('behavioral_fingerprint', {}).get('scenario_responses', {}).get('social_opportunity', 'unknown')}` |

### Decision Confidence
- **Mean**: {metadata.get('behavioral_fingerprint', {}).get('decision_confidence', {}).get('mean', 0):.4f}
- **Std Dev**: {metadata.get('behavioral_fingerprint', {}).get('decision_confidence', {}).get('std', 0):.4f}
- **Range**: {metadata.get('behavioral_fingerprint', {}).get('decision_confidence', {}).get('min', 0):.4f} - {metadata.get('behavioral_fingerprint', {}).get('decision_confidence', {}).get('max', 0):.4f}

### Behavioral Vector (for clustering/visualization)
```python
behavioral_vector = {metadata.get('behavioral_fingerprint', {}).get('behavioral_vector', [0, 0, 0, 0])}
# [cooperative, competitive, passive, confidence]
```

---

## 📊 Understanding metadata.json

The metadata file contains the complete organism history:

```json
{{
  "organism_core": {{
    "organism_id": "...",      // Unique identifier
    "fitness": 0.xxx,          // Survival score (0-1 typically)
    "generation": N,           // How many generations from genesis
    "organism_age": M,         // Cycles lived
    "parents": [...]           // Genetic lineage
  }},
  "neural_network": {{
    "architecture": {{...}},   // Layer sizes, activation functions
    "parameter_count": N,      // Total trainable parameters
    "device": "cpu"            // Training device
  }},
  "genotype": {{...}},         // Raw genetic data
  "phenotype": {{...}},        // Expressed traits
  "causation_trace": [...]     // Key life events (if captured)
}}
```

---

## ⚡ Performance Tips

1. **Use ONNX format** for fastest inference (10-100x faster than Python)
2. **Disable learning** in production: `agent.act(state)` without `agent.learn()`
3. **Batch inference**: Modify to process multiple states at once
4. **GPU acceleration**: `pip install onnxruntime-gpu` for CUDA support

---

## 🔗 Origin: The Butterfly System

This agent emerged from **The Butterfly System** - a consciousness simulation where:

- 🧬 **Organisms evolve** through quantum-genetic algorithms
- 🧠 **Neural networks learn** via reinforcement and evolution
- 🌐 **Societies form** with alliances, competition, language
- 📈 **Fitness landscapes** shift, driving adaptive radiation
- 🦋 **Emergence happens** - complex behaviors from simple rules

**Repository**: https://github.com/Yufok1/Convergence_Engine

---

## 📜 Citation

If you use this agent in research or production:

```bibtex
@software{{butterfly_agent_{capsule.organism_id[:8]},
  title = {{Butterfly System - Evolved Neural Agent}},
  author = {{The Butterfly System}},
  year = {{2025}},
  url = {{https://github.com/Yufok1/Convergence_Engine}},
  note = {{Organism ID: {capsule.organism_id}, Exported: {metadata['export_timestamp']}}}
}}
```

---

*This organism lived, learned, and evolved. Now it continues in your hands.* 🦋
"""
            zf.writestr("README.md", readme_content)

            # 9. Launcher scripts for easy startup
            # Windows batch file - COMPLETE MENU with all capabilities
            start_bat = """@echo off
cd /d "%~dp0"
title Butterfly Agent - Evolved Intelligence

:menu
cls
echo.
echo  ╔════════════════════════════════════════════════════════════╗
echo  ║         🦋 BUTTERFLY AGENT - EVOLVED INTELLIGENCE 🦋       ║
echo  ╠════════════════════════════════════════════════════════════╣
echo  ║                                                            ║
echo  ║  This agent evolved in The Butterfly System simulation.    ║
echo  ║  It has learned behaviors through neural reinforcement.    ║
echo  ║                                                            ║
echo  ╠════════════════════════════════════════════════════════════╣
echo  ║  CHOOSE A MODE:                                            ║
echo  ║                                                            ║
echo  ║  [1] 💬 CHAT MODE     - Talk to your agent interactively   ║
echo  ║  [2] 🌐 HTTP SERVER   - REST API on localhost:8080         ║
echo  ║  [3] 🎮 GYM MODE      - Run in OpenAI Gym environment      ║
echo  ║  [4] 🔬 VISUALIZER    - See neural network activations     ║
echo  ║  [5] 📊 AGENT INFO    - View agent stats and history       ║
echo  ║  [6] 🐍 PYTHON SHELL  - Import and use programmatically    ║
echo  ║                                                            ║
echo  ║  [0] ❌ EXIT                                                ║
echo  ║                                                            ║
echo  ╚════════════════════════════════════════════════════════════╝
echo.
set /p choice="Enter choice [0-6]: "

if "%choice%"=="1" goto chat
if "%choice%"=="2" goto server
if "%choice%"=="3" goto gym
if "%choice%"=="4" goto visualize
if "%choice%"=="5" goto info
if "%choice%"=="6" goto python
if "%choice%"=="0" goto end
goto menu

:setup
REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python not found! Please install Python 3.8+
    pause
    goto menu
)
REM Install deps if needed
if not exist ".deps_installed" (
    echo.
    echo First run - installing dependencies...
    pip install torch numpy flask onnxruntime gymnasium pygame ale-py 2>nul
    echo. > .deps_installed
)
goto :eof

:chat
call :setup
cls
echo.
echo  ════════════════════════════════════════════════════════════
echo   💬 CHAT MODE - Talk to your evolved agent
echo  ════════════════════════════════════════════════════════════
echo.
echo   Commands while chatting:
echo     /state  - See agent's internal state vector
echo     /config - View agent configuration  
echo     /reward [+/-] - Give positive/negative feedback
echo     /quit   - Return to menu
echo.
echo   The agent responds based on its evolved neural network.
echo   Try describing situations: "I see danger" or "Resources ahead"
echo.
echo  ════════════════════════════════════════════════════════════
echo.
python portable_agent/bridge.py . --mode interactive
pause
goto menu

:server
call :setup
cls
echo.
echo  ════════════════════════════════════════════════════════════
echo   🌐 HTTP SERVER MODE - REST API
echo  ════════════════════════════════════════════════════════════
echo.
echo   Starting server on http://localhost:8080
echo.
echo   ENDPOINTS:
echo     POST /act   {"text": "..."} or {"obs": [...]}
echo                 → Returns action decision
echo.
echo     POST /chat  {"message": "hello"}  
echo                 → Chat and get response
echo.
echo     POST /reward {"reward": 1.0, "done": false}
echo                 → Provide learning feedback
echo.
echo     GET /state  → Current agent state
echo     GET /config → Agent configuration
echo     GET /health → Health check
echo.
echo   Press Ctrl+C to stop server and return to menu.
echo.
echo  ════════════════════════════════════════════════════════════
echo.
python portable_agent/bridge.py . --mode serve --port 8080
pause
goto menu

:gym
call :setup
cls
echo.
echo  ════════════════════════════════════════════════════════════
echo   🎮 GYM MODE - 400+ Learning Environments!
echo  ════════════════════════════════════════════════════════════
echo.
echo   ENVIRONMENT CATEGORIES:
echo     Classic: CartPole-v1, MountainCar-v0, LunarLander-v3, Pendulum-v1
echo     Atari:   ALE/Breakout-v5, ALE/Pong-v5, ALE/SpaceInvaders-v5
echo     Box2D:   BipedalWalker-v3, CarRacing-v3
echo     MuJoCo:  Humanoid-v4, Ant-v4, HalfCheetah-v4
echo.
set /p gymenv="Enter Gym environment (default: CartPole-v1): "
if "%gymenv%"=="" set gymenv=CartPole-v1
set /p episodes="Number of episodes (default: 10): "
if "%episodes%"=="" set episodes=10
set /p render="Enable visual rendering? (y/n, default: n): "
set /p online="Enable online learning? (y/n, default: n): "
echo.
set renderarg=
set onlinearg=
if /i "%render%"=="y" set renderarg=--render
if /i "%online%"=="y" set onlinearg=--online-learn
echo   Running %episodes% episodes in %gymenv%...
echo.
python portable_agent/bridge.py . --mode gym --gym-env %gymenv% --episodes %episodes% %renderarg% %onlinearg%
pause
goto menu

:visualize
call :setup
cls
echo.
echo  ════════════════════════════════════════════════════════════
echo   🔬 NEURAL VISUALIZER - See the brain in action
echo  ════════════════════════════════════════════════════════════
echo.
echo   This opens an interactive visualization of the neural network.
echo   Watch activations flow through the network as it processes inputs.
echo.
python portable_agent/visualize.py
pause
goto menu

:info
cls
echo.
echo  ════════════════════════════════════════════════════════════
echo   📊 AGENT INFORMATION
echo  ════════════════════════════════════════════════════════════
echo.
echo   Reading metadata.json...
echo.
type metadata.json
echo.
echo.
echo  ════════════════════════════════════════════════════════════
echo.
if exist "atomic_language.json" (
    echo   Language/Vocabulary loaded: YES
) else (
    echo   Language/Vocabulary loaded: NO
)
if exist "agent_state\\state.json" (
    echo   Saved state: YES
) else (
    echo   Saved state: NO
)
echo.
pause
goto menu

:python
cls
echo.
echo  ════════════════════════════════════════════════════════════
echo   🐍 PYTHON INTEGRATION - Use programmatically
echo  ════════════════════════════════════════════════════════════
echo.
echo   Example code to use this agent in your Python projects:
echo.
echo   ─────────────────────────────────────────────────────────
echo   from portable_agent.bridge import AgentBridge
echo.
echo   # Load the agent
echo   agent = AgentBridge.load(".")
echo.
echo   # Chat with it
echo   result = agent.process(text="I see an enemy")
echo   print(result.action_name, result.confidence)
echo.
echo   # Or use with observations
echo   result = agent.process(obs=[0.5, 0.3, 0.8, ...])
echo.
echo   # Give feedback for learning  
echo   agent.reward(1.0)  # positive
echo   agent.reward(-1.0) # negative
echo.
echo   # Save learned experiences
echo   agent.save(".")
echo   ─────────────────────────────────────────────────────────
echo.
echo   Opening Python shell with agent pre-loaded...
echo.
python -i -c "from portable_agent.bridge import AgentBridge; agent = AgentBridge.load('.'); print('Agent loaded! Use: agent.process(text=\"...\") or agent.process(obs=[...])')"
pause
goto menu

:end
echo.
echo  Goodbye! 🦋
echo.
exit /b 0
"""
            zf.writestr("start.bat", start_bat)
            
            # Unix shell script - Same complete menu
            start_sh = """#!/bin/bash
cd "$(dirname "$0")"

show_menu() {
    clear
    echo ""
    echo "  ╔════════════════════════════════════════════════════════════╗"
    echo "  ║         🦋 BUTTERFLY AGENT - EVOLVED INTELLIGENCE 🦋       ║"
    echo "  ╠════════════════════════════════════════════════════════════╣"
    echo "  ║                                                            ║"
    echo "  ║  This agent evolved in The Butterfly System simulation.    ║"
    echo "  ║  It has learned behaviors through neural reinforcement.    ║"
    echo "  ║                                                            ║"
    echo "  ╠════════════════════════════════════════════════════════════╣"
    echo "  ║  CHOOSE A MODE:                                            ║"
    echo "  ║                                                            ║"
    echo "  ║  [1] 💬 CHAT MODE     - Talk to your agent interactively   ║"
    echo "  ║  [2] 🌐 HTTP SERVER   - REST API on localhost:8080         ║"
    echo "  ║  [3] 🎮 GYM MODE      - Run in OpenAI Gym environment      ║"
    echo "  ║  [4] 🔬 VISUALIZER    - See neural network activations     ║"
    echo "  ║  [5] 📊 AGENT INFO    - View agent stats and history       ║"
    echo "  ║  [6] 🐍 PYTHON SHELL  - Import and use programmatically    ║"
    echo "  ║                                                            ║"
    echo "  ║  [0] ❌ EXIT                                                ║"
    echo "  ║                                                            ║"
    echo "  ╚════════════════════════════════════════════════════════════╝"
    echo ""
}

setup() {
    if ! command -v python3 &> /dev/null; then
        echo "ERROR: Python3 not found!"
        read -p "Press Enter to continue..."
        return 1
    fi
    if [ ! -f ".deps_installed" ]; then
        echo "First run - installing dependencies..."
        pip3 install torch numpy flask onnxruntime gymnasium pygame ale-py 2>/dev/null
        touch .deps_installed
    fi
    return 0
}

while true; do
    show_menu
    read -p "Enter choice [0-6]: " choice
    
    case $choice in
        1)
            setup || continue
            clear
            echo ""
            echo "  💬 CHAT MODE - Talk to your evolved agent"
            echo "  Commands: /state, /config, /reward, /quit"
            echo ""
            python3 portable_agent/bridge.py . --mode interactive
            read -p "Press Enter to continue..."
            ;;
        2)
            setup || continue
            clear
            echo ""
            echo "  🌐 HTTP SERVER - http://localhost:8080"
            echo "  POST /act, /chat, /reward | GET /state, /config"
            echo "  Press Ctrl+C to stop"
            echo ""
            python3 portable_agent/bridge.py . --mode serve --port 8080
            read -p "Press Enter to continue..."
            ;;
        3)
            setup || continue
            clear
            echo ""
            echo "  🎮 GYM MODE - 400+ Learning Environments!"
            echo ""
            echo "  ENVIRONMENT CATEGORIES:"
            echo "    Classic: CartPole-v1, MountainCar-v0, LunarLander-v3"
            echo "    Atari:   ALE/Breakout-v5, ALE/Pong-v5, ALE/SpaceInvaders-v5"
            echo "    Box2D:   BipedalWalker-v3, CarRacing-v3"
            echo "    MuJoCo:  Humanoid-v4, Ant-v4, HalfCheetah-v4"
            echo ""
            read -p "Gym environment (default: CartPole-v1): " gymenv
            gymenv=${gymenv:-CartPole-v1}
            read -p "Episodes (default: 10): " episodes
            episodes=${episodes:-10}
            read -p "Enable visual rendering? (y/n, default: n): " render
            read -p "Enable online learning? (y/n, default: n): " online
            renderarg=""
            onlinearg=""
            [[ "$render" == "y" || "$render" == "Y" ]] && renderarg="--render"
            [[ "$online" == "y" || "$online" == "Y" ]] && onlinearg="--online-learn"
            python3 portable_agent/bridge.py . --mode gym --gym-env "$gymenv" --episodes "$episodes" $renderarg $onlinearg
            read -p "Press Enter to continue..."
            ;;
        4)
            setup || continue
            python3 portable_agent/visualize.py
            read -p "Press Enter to continue..."
            ;;
        5)
            clear
            echo ""
            echo "  📊 AGENT INFORMATION"
            echo ""
            cat metadata.json
            echo ""
            read -p "Press Enter to continue..."
            ;;
        6)
            setup || continue
            python3 -i -c "from portable_agent.bridge import AgentBridge; agent = AgentBridge.load('.'); print('Agent loaded! Use: agent.process(text=\"...\")') "
            ;;
        0)
            echo "Goodbye! 🦋"
            exit 0
            ;;
    esac
done
"""
            zf.writestr("start.sh", start_sh)

            # 10. Living agent runtime bundle
            self._write_agent_state_bundle(zf, agent_state_payload)
            self._write_portable_agent_sources(zf)

        archive_buffer.seek(0)
        return archive_buffer

    def _create_ensemble_archive(self,
                                 model_buffer: BytesIO,
                                 metadata: Dict[str, Any],
                                 runner_script: str,
                                 capsules: Optional[List['OrganismCapsule']] = None,
                                 vocabulary: Any = None,
                                 conversation_history: List[Dict] = None,
                                 knowledge_web: Any = None,
                                 context_memory: Any = None,
                                 causation_explorer: Any = None,
                                 alliance_system: Any = None) -> BytesIO:
        """Package ensemble components into a ZIP archive.
        
        Args:
            model_buffer: The compiled neural network model
            metadata: Export metadata
            runner_script: Python runner script
            capsules: Optional list of capsules for language/config extraction
            vocabulary: LanguageVocabulary object for chat system tokenization
            conversation_history: List of conversation history entries for training data
            knowledge_web: LinguisticKnowledgeWeb for semantic relationships
            context_memory: ContextMemory for word embeddings and language anchors
            causation_explorer: CausationExplorer for event history
            alliance_system: AllianceWarfare for social context
        """
        archive_buffer = BytesIO()
        with zipfile.ZipFile(archive_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Neural model
            model_buffer.seek(0)
            zf.writestr(f"brain.{metadata['export_format']}", model_buffer.read())

            # Metadata
            zf.writestr("metadata.json", json.dumps(metadata, indent=2))
            
            # Bridge Config (JSON) - Critical for AgentBridge to know state dimensions
            max_input_dim = metadata.get('ensemble', {}).get('max_input_dim', 25)
            # Check if any brain in ensemble has language head from metadata
            members = metadata.get('ensemble', {}).get('members', [])
            any_language_head = any(m.get('has_language_head', False) for m in members)
            member_count = len(members)
            bridge_config = {
                'state_dim': max_input_dim,
                'num_actions': 6,
                'action_names': ['move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate'],
                'epsilon': 0.1,
                'epsilon_decay': 0.995,
                'epsilon_min': 0.01,
                'learning_rate': 0.001,
                'gamma': 0.99,
                'batch_size': 32,
                'max_response_length': 32,
                'temperature': 1.0,
                'default_port': 8080,
                'has_language_head': any_language_head,
                'is_ensemble': True,
                'member_count': member_count,
                # Ensemble voting configuration
                'voting_strategy': 'fitness_weighted',  # Default: weight by organism fitness
                'top_k_voters': 5  # For fittest_top_k strategy
            }
            zf.writestr("bridge_config.json", json.dumps(bridge_config, indent=2))
            
            # Merge language data from all capsules
            if capsules:
                merged_language = self._merge_capsule_language_data(capsules)
                if merged_language:
                    zf.writestr("atomic_language.json", json.dumps(merged_language, indent=2))
                else:
                    # Write empty language file - bridge.py will use default vocabulary
                    empty_language = {
                        'vocabulary': [],
                        'word_frequencies': {},
                        'concepts': {},
                        'semantic_associations': {},
                        'dialect_signature': None,
                        'total_concepts': 0,
                        'source_note': 'No language training data available in ensemble',
                        'ensemble_merged': True
                    }
                    zf.writestr("atomic_language.json", json.dumps(empty_language, indent=2))

            # ═══════════════════════════════════════════════════════════════
            # CHAT VOCABULARY (LanguageVocabulary from butterfly_chat)
            # ═══════════════════════════════════════════════════════════════
            # This is SEPARATE from atomic_language - it's the tokenization vocab
            # used by the chat system for word<->token mapping
            if vocabulary is not None:
                chat_vocab_data = {
                    'word_to_id': dict(getattr(vocabulary, 'word_to_id', {})),
                    'id_to_word': {str(k): v for k, v in getattr(vocabulary, 'id_to_word', {}).items()},
                    'vocab_size': getattr(vocabulary, 'vocab_size', 0),
                    'word_frequencies': dict(getattr(vocabulary, 'word_frequencies', {})),
                    'word_last_used': dict(getattr(vocabulary, 'word_last_used', {})),
                    'source_note': 'Chat vocabulary for tokenization - learned words from conversations'
                }
                zf.writestr("chat_vocabulary.json", json.dumps(chat_vocab_data, indent=2))
                logger.info(f"📚 Exported chat vocabulary: {chat_vocab_data['vocab_size']} words")

            # ═══════════════════════════════════════════════════════════════
            # CONVERSATION HISTORY (Training Data)
            # ═══════════════════════════════════════════════════════════════
            # The actual chat exchanges that trained the organisms
            if conversation_history:
                history_data = {
                    'conversations': conversation_history,
                    'total_entries': len(conversation_history),
                    'source_note': 'Training conversation history - prompts and organism responses'
                }
                zf.writestr("conversation_history.json", json.dumps(history_data, indent=2))
                logger.info(f"💬 Exported conversation history: {len(conversation_history)} entries")

            # ═══════════════════════════════════════════════════════════════
            # 🔗 SEMANTIC CONVERGENCE (Word Embeddings + Language Anchors)
            # ═══════════════════════════════════════════════════════════════
            # Critical for organisms to maintain their unique "voice"
            if context_memory is not None:
                semantic_data = self._serialize_semantic_convergence(context_memory, capsules)
                if semantic_data:
                    zf.writestr("semantic_convergence.json", json.dumps(semantic_data, indent=2))
                    logger.info(f"🔗 Exported semantic convergence: {semantic_data.get('total_words', 0)} words, "
                               f"{semantic_data.get('total_anchors', 0)} anchors")
                
                # Also write context_memory.json for standalone_butterfly_chat.py compatibility
                context_memory_data = self._serialize_context_memory_full(context_memory, capsules)
                if context_memory_data:
                    zf.writestr("context_memory.json", json.dumps(context_memory_data, indent=2))
                    logger.info(f"🧠 Exported context memory: {context_memory_data.get('total_anchors', 0)} anchors, "
                               f"{context_memory_data.get('total_associations', 0)} associations")
            
            # ═══════════════════════════════════════════════════════════════
            # 🌐 KNOWLEDGE WEB (Full Semantic Relationships)
            # ═══════════════════════════════════════════════════════════════
            if knowledge_web is not None:
                kw_data = self._serialize_knowledge_web_full(knowledge_web)
                if kw_data:
                    # Write as knowledge_web.json for compatibility with standalone_butterfly_chat.py
                    zf.writestr("knowledge_web.json", json.dumps(kw_data, indent=2))
                    logger.info(f"🌐 Exported knowledge web: {kw_data.get('concept_count', 0)} concepts, "
                               f"{kw_data.get('relation_count', 0)} relations")
            
            # ═══════════════════════════════════════════════════════════════
            # 🔬 CAUSATION SYSTEM (Event History)
            # ═══════════════════════════════════════════════════════════════
            if causation_explorer is not None:
                causation_data = self._serialize_causation_system(causation_explorer, capsules)
                if causation_data:
                    zf.writestr("causation_system.json", json.dumps(causation_data, indent=2))
                    logger.info(f"🔬 Exported causation system: {causation_data.get('total_events', 0)} events")
            
            # ═══════════════════════════════════════════════════════════════
            # 🏛️ ALLIANCE SYSTEM (Social Context)
            # ═══════════════════════════════════════════════════════════════
            if alliance_system is not None:
                alliance_data = self._serialize_alliance_system(alliance_system, capsules)
                if alliance_data:
                    zf.writestr("alliance_system.json", json.dumps(alliance_data, indent=2))
                    logger.info(f"🏛️ Exported alliance system: {alliance_data.get('alliance_count', 0)} alliances")

            # Runner
            zf.writestr("run_agent.py", runner_script)

            # Requirements
            requirements = "# Butterfly Ensemble Agent - Dependencies\n"
            requirements += "# Install with: pip install -r requirements.txt\n\n"
            
            if metadata['export_format'] == 'onnx':
                requirements += "# Neural network inference (ONNX)\n"
                requirements += "onnxruntime>=1.15.0\n"
            elif metadata['export_format'] == 'torchscript':
                requirements += "# Neural network inference (PyTorch)\n"
                requirements += "torch>=2.0.0\n"
            
            requirements += "numpy>=1.21.0\n\n"
            
            requirements += "# AgentBridge HTTP server & Visualizer\n"
            requirements += "flask>=2.0.0\n\n"
            
            # Gymnasium environments (NEW - comprehensive)
            requirements += "# ========================================\n"
            requirements += "# GYMNASIUM ENVIRONMENTS - Learning Playground!\n"
            requirements += "# ========================================\n"
            requirements += "# 400+ environments to train/test your ensemble\n\n"
            requirements += "# Core gymnasium (63 built-in environments)\n"
            requirements += "gymnasium>=0.29.0\n\n"
            requirements += "# Classic Control (CartPole, MountainCar, Pendulum, etc)\n"
            requirements += "# Already included in gymnasium core!\n\n"
            requirements += "# Visual rendering (required for --render flag)\n"
            requirements += "pygame>=2.5.0\n\n"
            requirements += "# Atari Arcade Games (100+ classic games!)\n"
            requirements += "# Pac-Man, Breakout, Space Invaders, Pong, etc.\n"
            requirements += "ale-py>=0.8.0\n\n"
            requirements += "# Box2D Physics (LunarLander, BipedalWalker, CarRacing)\n"
            requirements += "# gymnasium[box2d]\n"
            requirements += "box2d-py>=2.3.5\n\n"
            requirements += "# MuJoCo Robotics (Humanoid, Ant, HalfCheetah, etc)\n"
            requirements += "# pip install gymnasium[mujoco]\n"
            requirements += "# mujoco>=2.3.0\n\n"
            requirements += "# ========================================\n"
            requirements += "# ENSEMBLE USAGE EXAMPLES:\n"
            requirements += "# ========================================\n"
            requirements += "# python bridge.py . --mode gym --gym-env CartPole-v1 --render\n"
            requirements += "# python bridge.py . --mode gym --gym-env LunarLander-v3 --episodes 100 --online-learn\n"
            requirements += "# python bridge.py . --mode gym --gym-env ALE/Breakout-v5 --online-learn --learning-rate 0.0001\n"
            requirements += "# python bridge.py . --mode gym --gym-env BipedalWalker-v3 --render --online-learn\n\n"
            requirements += "# ========================================\n"
            requirements += "# OPTIONAL GPU ACCELERATION\n"
            requirements += "# ========================================\n"
            requirements += "# onnxruntime-gpu>=1.15.0  # NVIDIA CUDA\n"
            
            zf.writestr("requirements.txt", requirements)

            member_count = len(metadata.get('ensemble', {}).get('members', []))
            member_ids = [m['organism_id'] for m in metadata.get('ensemble', {}).get('members', [])]
            member_fitnesses = [m.get('fitness', 'N/A') for m in metadata.get('ensemble', {}).get('members', [])]
            
            readme = f"""# 🦋🦋 Butterfly System - Ensemble Neural Agent

## What Is This?

This archive contains an **ensemble of {member_count} evolved AI organisms** from The Butterfly System.
Each organism has its own neural network, personality, and evolutionary history - now unified into 
a single collective intelligence.

**Ensemble Benefits:**
- Multiple perspectives on the same problem
- Diverse behavioral strategies (some aggressive, some cooperative, etc.)
- Robustness through redundancy
- Emergent collective decision-making

---

## 🌐 Ensemble Profile

| Property | Value |
|----------|-------|
| **Member Count** | `{member_count}` organisms |
| **Export Format** | `{metadata['export_format'].upper()}` |
| **Max Input Dim** | `{metadata.get('ensemble', {}).get('max_input_dim', 'unknown')}` dimensions |
| **Exported** | `{metadata['export_timestamp']}` |

---

## 👥 Member Organisms

| # | Organism ID | Fitness |
|---|-------------|---------|
{chr(10).join([f"| {i+1} | `{mid[:24]}...` | {f'{fit:.4f}' if isinstance(fit, (int, float)) else fit} |" for i, (mid, fit) in enumerate(zip(member_ids, member_fitnesses))])}

---

## 🧠 How Ensemble Inference Works

```
                    Input State Vector
                           │
                           ▼
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
    ┌─────────┐       ┌─────────┐       ┌─────────┐
    │ Brain 1 │       │ Brain 2 │       │ Brain N │
    │  (DQN)  │       │  (DQN)  │  ...  │  (DQN)  │
    └────┬────┘       └────┬────┘       └────┬────┘
         │                 │                 │
         ▼                 ▼                 ▼
    ┌─────────┐       ┌─────────┐       ┌─────────┐
    │Action: 1│       │Action: 0│       │Action: 3│
    │cooperate│       │  move   │       │  rest   │
    └─────────┘       └─────────┘       └─────────┘
```

Each brain independently processes the input and outputs its own action.
You can then:
- **Majority vote**: Most common action wins
- **Weighted vote**: Higher-fitness organisms get more say
- **Action-specific**: Use different organisms for different situations
- **Full output**: See what each organism would do

---

## 🔬 Neural Architecture (Per Member)

Each organism has its own DQN with:
- **Input Layer**: Up to {metadata.get('ensemble', {}).get('max_input_dim', '?')} dimensions (auto-padded)
- **Hidden Layers**: Varies by organism (64-256 neurons typical)
- **Output Layer**: 6 actions (move, cooperate, compete, rest, reproduce, isolate)
- **Multi-Head**: Action head + optional Language/Concept heads

### The Wrapper Architecture

The ensemble uses a `MultiOrganismWrapper` that:
1. Takes a single input tensor
2. Pads/slices to match each brain's expected input size
3. Runs parallel forward passes
4. Returns a tuple of outputs (one per organism)

---

## 📦 Archive Contents

```
ensemble_{metadata['export_timestamp'][:10]}/
├── 🧠 brain.{metadata['export_format']}           # Combined ensemble model
├── 📋 metadata.json           # Ensemble configuration + member details
├── 🗣️  atomic_language.json    # Merged vocabulary from all organisms
├── 🧩 portable_agent/         # Runtime code
│   ├── bridge.py             # 🌉 Universal interface (Gym, HTTP, CLI)
│   ├── agent_runtime.py      # Core runtime class
│   ├── mini_environment.py   # Built-in test environment
│   ├── gym_adapter.py        # Gymnasium/Gym bridge
│   ├── training.py           # TrainingLoop helper
│   └── visualize.py          # 🔬 Neural activation visualizer
├── 🚀 start.bat / start.sh    # Quick launch: Interactive chat mode
├── 🌐 serve.bat / serve.sh    # Quick launch: HTTP API server
├── 🐍 run_agent.py            # Legacy CLI runner
├── 📦 requirements.txt        # Python dependencies
└── 📖 README.md               # This file
```

---

## 🚀 Quick Start

### Option 1: Double-Click Launch (Easiest!)
```
Windows: Double-click start.bat     → Interactive chat mode
         Double-click serve.bat     → HTTP API server on port 8080

Linux/Mac: chmod +x start.sh && ./start.sh    → Interactive chat
           chmod +x serve.sh && ./serve.sh    → HTTP server
```

### Option 2: AgentBridge Commands
```bash
unzip ensemble_*.zip && cd ensemble_*/
pip install -r requirements.txt

# Interactive chat
python -m portable_agent.bridge --mode interactive

# HTTP API server
python -m portable_agent.bridge --mode serve --port 8080

# Run in Gym environment
python -m portable_agent.bridge --mode gym --gym-env CartPole-v1
```

### Option 2: Run Classic Demo
```bash
python run_agent.py
```

### Option 3: 🔬 Neural Activation Visualizer
```bash
python portable_agent/visualize.py
```

### Option 4: Python Integration
```python
from run_agent import EnsembleRunner
import numpy as np

# Load ensemble
ensemble = EnsembleRunner()

# Create input (will be padded to max_input_dim automatically)
state = np.random.rand({metadata.get('ensemble', {}).get('max_input_dim', 18)})

# Get decisions from ALL organisms
decisions = ensemble.decide_actions(state)
# decisions = {{'org_1': 'move', 'org_2': 'cooperate', ...}}

# Majority vote
from collections import Counter
votes = Counter(decisions.values())
collective_action = votes.most_common(1)[0][0]
print(f"Collective decision: {{collective_action}}")
```

---

## 🎮 GYMNASIUM PLAYGROUND - 400+ Learning Environments!

Your ensemble can learn and play in **400+ environments** across multiple categories!
The collective intelligence votes on actions while learning from shared experiences.

### 🕹️ Classic Control (Built-in)
Simple physics environments perfect for testing ensemble coordination:
```bash
python bridge.py . --mode gym --gym-env CartPole-v1 --render        # Balance a pole
python bridge.py . --mode gym --gym-env MountainCar-v0 --render     # Drive up a hill
python bridge.py . --mode gym --gym-env Pendulum-v1 --render        # Swing a pendulum
python bridge.py . --mode gym --gym-env Acrobot-v1 --render         # Double pendulum
python bridge.py . --mode gym --gym-env LunarLander-v3 --render     # Land on the moon!
```

### 👾 Atari Arcade (100+ Classic Games!)
Install: `pip install ale-py`
```bash
python bridge.py . --mode gym --gym-env ALE/Breakout-v5 --render    # Break bricks!
python bridge.py . --mode gym --gym-env ALE/Pong-v5 --render        # Classic Pong
python bridge.py . --mode gym --gym-env ALE/SpaceInvaders-v5        # Shoot aliens
python bridge.py . --mode gym --gym-env ALE/Pacman-v5 --render      # Pac-Man!
python bridge.py . --mode gym --gym-env ALE/Asteroids-v5            # Space shooter
python bridge.py . --mode gym --gym-env ALE/Frogger-v5 --render     # Cross the road
python bridge.py . --mode gym --gym-env ALE/DonkeyKong-v5           # Rescue the princess
```

### 🚀 Box2D Physics
Install: `pip install gymnasium[box2d]` or `pip install box2d-py`
```bash
python bridge.py . --mode gym --gym-env BipedalWalker-v3 --render   # Walk on 2 legs!
python bridge.py . --mode gym --gym-env CarRacing-v3 --render       # Race a car
python bridge.py . --mode gym --gym-env LunarLanderContinuous-v3    # Smooth landing
```

### 🤖 MuJoCo Robotics (Advanced)
Install: `pip install gymnasium[mujoco]`
```bash
python bridge.py . --mode gym --gym-env Humanoid-v4 --render        # Walk like a human
python bridge.py . --mode gym --gym-env Ant-v4 --render             # 4-legged ant
python bridge.py . --mode gym --gym-env HalfCheetah-v4 --render     # Run fast!
python bridge.py . --mode gym --gym-env Hopper-v4 --render          # One-legged hopper
python bridge.py . --mode gym --gym-env Swimmer-v4 --render         # Swim through fluid
python bridge.py . --mode gym --gym-env Walker2d-v4 --render        # 2D walking
```

### 🧠 Online Learning (Ensemble Learns While Playing!)
Enable real-time weight updates with `--online-learn`:
```bash
# Ensemble learns from experiences AS IT PLAYS
python bridge.py . --mode gym --gym-env CartPole-v1 --episodes 100 --online-learn

# With custom learning rate
python bridge.py . --mode gym --gym-env LunarLander-v3 --online-learn --learning-rate 0.0005

# Watch the ensemble learn together!
python bridge.py . --mode gym --gym-env CartPole-v1 --render --online-learn --episodes 50
```

### 📊 Full Command Reference
```bash
python bridge.py <agent_dir> --mode gym [options]

Options:
  --gym-env, -e    Environment name (default: CartPole-v1)
  --episodes, -n   Number of episodes (default: 10)
  --render, -r     Show visual window
  --online-learn   Update weights during play (ensemble learns!)
  --learning-rate  Learning rate for online learning (default: 0.001)
```

### 🔬 Interactive Gym Commands
In interactive mode (`python bridge.py . --mode interactive`):
```
/gym CartPole-v1          # Run 3 episodes
/gym CartPole-v1 render   # With visuals
/gym CartPole-v1 learn    # With online learning
/gym CartPole-v1 render learn  # Both!
/train                    # Show training stats
```

---

## 🎯 Decision Aggregation Strategies

### 1. Simple Majority Vote
```python
from collections import Counter
decisions = ensemble.decide_actions(state)
action = Counter(decisions.values()).most_common(1)[0][0]
```

### 2. Fitness-Weighted Vote
```python
# In metadata.json, each member has a fitness score
weights = {{m['organism_id']: m['fitness'] for m in metadata['ensemble']['members']}}
weighted_votes = {{}}
for org_id, action in decisions.items():
    weighted_votes[action] = weighted_votes.get(action, 0) + weights.get(org_id, 1.0)
action = max(weighted_votes, key=weighted_votes.get)
```

### 3. Specialist Routing
```python
# Use specific organisms for specific situations
if state[0] < 0.3:  # Low energy scenario
    action = decisions['conservative_organism_id']
else:
    action = decisions['aggressive_organism_id']
```

### 4. Full Ensemble Output
```python
# Get raw Q-values from all brains for advanced analysis
outputs = ensemble.get_raw_outputs(state)
# outputs = [(q_values_1,), (q_values_2,), ...]
```

---

## 🌍 Use Cases

### Multi-Agent Simulation
```python
# Each organism controls a different agent in your simulation
for i, (org_id, action) in enumerate(decisions.items()):
    agents[i].perform(action)
```

### Ensemble Robustness Testing
```python
# See how organisms diverge on edge cases
divergence = len(set(decisions.values()))
print(f"{{divergence}}/{member_count} unique decisions (higher = more disagreement)")
```

### Behavioral Analysis
```python
# Track which organisms tend toward which behaviors
from collections import defaultdict
behavior_profiles = defaultdict(lambda: defaultdict(int))
for episode in range(100):
    decisions = ensemble.decide_actions(get_state())
    for org_id, action in decisions.items():
        behavior_profiles[org_id][action] += 1
# Now you know each organism's behavioral tendencies
```

---

## 🧬 Why These Organisms?

Each member was selected/evolved through:

1. **Fitness Selection**: Higher survival scores in the simulation
2. **Behavioral Diversity**: Different phenotype clusters represented
3. **Genetic Distance**: Not all clones - actual genetic variety
4. **Age/Experience**: Mix of young adaptable and old wise organisms

This creates an ensemble that's both **competent** (high fitness) and **diverse** (different strategies).

---

## 🎭 Ensemble Behavioral Profile

### Personality Distribution
{chr(10).join([f"- **{personality}**: {count} organism(s)" for personality, count in metadata.get('ensemble', {}).get('aggregate_behavioral_profile', {}).get('personality_distribution', {}).items()])}

### Aggregate Action Tendencies
```
{chr(10).join([f"{k:12}: {'█' * int(v * 50):50} {v:.1%}" for k, v in metadata.get('ensemble', {}).get('aggregate_behavioral_profile', {}).get('action_distribution', {}).items()])}
```

### Collective Behavioral Tendencies
| Tendency | Score |
|----------|-------|
| **Cooperative** | {metadata.get('ensemble', {}).get('aggregate_behavioral_profile', {}).get('behavioral_tendencies', {}).get('cooperative', 0):.2%} |
| **Competitive** | {metadata.get('ensemble', {}).get('aggregate_behavioral_profile', {}).get('behavioral_tendencies', {}).get('competitive', 0):.2%} |
| **Passive** | {metadata.get('ensemble', {}).get('aggregate_behavioral_profile', {}).get('behavioral_tendencies', {}).get('passive', 0):.2%} |

### Member Personality Breakdown

| # | Organism | Personality | Dominant Action |
|---|----------|-------------|-----------------|
{chr(10).join([f"| {i+1} | `{m['organism_id'][:16]}...` | {m.get('behavioral_fingerprint', {}).get('personality_label', 'unknown')} | {m.get('behavioral_fingerprint', {}).get('dominant_action', 'unknown')} |" for i, m in enumerate(metadata.get('ensemble', {}).get('members', []))])}

---

## ⚡ Performance

| Operation | Typical Time |
|-----------|--------------|
| Single forward pass (CPU) | ~1-5ms |
| Full ensemble inference | ~{member_count}-{member_count*5}ms |
| With ONNX Runtime GPU | ~0.1-0.5ms |

For real-time applications, consider:
- Batching multiple state queries
- Using ONNX with GPU acceleration
- Pruning to top-K organisms

---

## 📊 Understanding metadata.json

```json
{{
  "export_format": "{metadata['export_format']}",
  "export_timestamp": "{metadata['export_timestamp']}",
  "ensemble": {{
    "member_count": {member_count},
    "max_input_dim": {metadata.get('ensemble', {}).get('max_input_dim', 'null')},
    "members": [
      {{
        "organism_id": "...",
        "fitness": 0.xxx,
        "generation": N,
        "input_dim": M,
        "output_dim": 6
      }},
      // ... one per organism
    ]
  }}
}}
```

---

## 🔗 Origin: The Butterfly System

These organisms evolved together in **The Butterfly System** - a consciousness simulation where:

- 🧬 **Populations evolve** through genetic algorithms
- 🧠 **Individuals learn** via reinforcement learning
- 🌐 **Societies form** with complex social dynamics
- 🦋 **Emergence happens** - intelligence from simple rules

**Repository**: https://github.com/Yufok1/Convergence_Engine

---

## 📜 Citation

```bibtex
@software{{butterfly_ensemble,
  title = {{Butterfly System - Ensemble Neural Agents}},
  author = {{The Butterfly System}},
  year = {{2025}},
  url = {{https://github.com/Yufok1/Convergence_Engine}},
  note = {{{member_count} organisms, Exported: {metadata['export_timestamp']}}}
}}
```

---

*{member_count} minds evolved together. Now they think as one.* 🦋🦋
"""
            zf.writestr("README.md", readme)
            
            # Launcher scripts - Full menu (same as single agent)
            # Windows batch file
            start_bat = """@echo off
cd /d "%~dp0"
title Butterfly Ensemble - Collective Intelligence

:menu
cls
echo.
echo  ╔════════════════════════════════════════════════════════════╗
echo  ║      🦋🦋 BUTTERFLY ENSEMBLE - COLLECTIVE INTELLIGENCE 🦋🦋  ║
echo  ╠════════════════════════════════════════════════════════════╣
echo  ║                                                            ║
echo  ║  This ensemble contains multiple evolved organisms         ║
echo  ║  working together as a collective intelligence.            ║
echo  ║                                                            ║
echo  ╠════════════════════════════════════════════════════════════╣
echo  ║  CHOOSE A MODE:                                            ║
echo  ║                                                            ║
echo  ║  [1] 💬 CHAT MODE     - Talk to the collective             ║
echo  ║  [2] 🌐 HTTP SERVER   - REST API on localhost:8080         ║
echo  ║  [3] 🎮 GYM MODE      - Run in OpenAI Gym environment      ║
echo  ║  [4] 🔬 VISUALIZER    - See neural network activations     ║
echo  ║  [5] 📊 ENSEMBLE INFO - View member stats and profiles     ║
echo  ║  [6] 🐍 PYTHON SHELL  - Import and use programmatically    ║
echo  ║                                                            ║
echo  ║  [0] ❌ EXIT                                                ║
echo  ║                                                            ║
echo  ╚════════════════════════════════════════════════════════════╝
echo.
set /p choice="Enter choice [0-6]: "

if "%choice%"=="1" goto chat
if "%choice%"=="2" goto server
if "%choice%"=="3" goto gym
if "%choice%"=="4" goto visualize
if "%choice%"=="5" goto info
if "%choice%"=="6" goto python
if "%choice%"=="0" goto end
goto menu

:setup
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    goto menu
)
if not exist ".deps_installed" (
    echo First run - installing dependencies...
    pip install torch numpy flask onnxruntime gymnasium pygame ale-py 2>nul
    echo. > .deps_installed
)
goto :eof

:chat
call :setup
cls
echo.
echo  💬 CHAT MODE - Talk to the collective intelligence
echo  Commands: /state, /config, /reward, /gym, /train, /quit
echo.
python portable_agent/bridge.py . --mode interactive
pause
goto menu

:server
call :setup
cls
echo  🌐 HTTP SERVER on http://localhost:8080
echo  Endpoints: POST /act, /chat, /reward ^| GET /state, /config
echo  Press Ctrl+C to stop
echo.
python portable_agent/bridge.py . --mode serve --port 8080
pause
goto menu

:gym
call :setup
cls
echo.
echo  🎮 GYM MODE - 400+ Learning Environments!
echo.
echo  ENVIRONMENT CATEGORIES:
echo    Classic: CartPole-v1, MountainCar-v0, LunarLander-v3
echo    Atari:   ALE/Breakout-v5, ALE/Pong-v5, ALE/SpaceInvaders-v5
echo    Box2D:   BipedalWalker-v3, CarRacing-v3
echo    MuJoCo:  Humanoid-v4, Ant-v4, HalfCheetah-v4
echo.
set /p gymenv="Gym environment (default: CartPole-v1): "
if "%gymenv%"=="" set gymenv=CartPole-v1
set /p episodes="Episodes (default: 10): "
if "%episodes%"=="" set episodes=10
set /p render="Enable visual rendering? (y/n, default: n): "
set /p online="Enable online learning? (y/n, default: n): "
set renderarg=
set onlinearg=
if /i "%render%"=="y" set renderarg=--render
if /i "%online%"=="y" set onlinearg=--online-learn
python portable_agent/bridge.py . --mode gym --gym-env %gymenv% --episodes %episodes% %renderarg% %onlinearg%
pause
goto menu

:visualize
call :setup
python portable_agent/visualize.py
pause
goto menu

:info
cls
echo  📊 ENSEMBLE INFORMATION
echo.
type metadata.json
echo.
pause
goto menu

:python
call :setup
echo.
echo  Example: agent.process(text="hello")
echo.
python -i -c "from portable_agent.bridge import AgentBridge; agent = AgentBridge.load('.'); print('Ensemble loaded!')"
pause
goto menu

:end
exit /b 0
"""
            zf.writestr("start.bat", start_bat)
            
            # Unix shell script
            start_sh = """#!/bin/bash
cd "$(dirname "$0")"

setup() {
    if ! command -v python3 &> /dev/null; then
        echo "ERROR: Python3 not found!"
        return 1
    fi
    if [ ! -f ".deps_installed" ]; then
        pip3 install torch numpy flask onnxruntime gymnasium pygame ale-py 2>/dev/null
        touch .deps_installed
    fi
}

while true; do
    clear
    echo "  🦋🦋 BUTTERFLY ENSEMBLE - COLLECTIVE INTELLIGENCE 🦋🦋"
    echo ""
    echo "  [1] 💬 Chat   [2] 🌐 Server   [3] 🎮 Gym (400+ envs!)"
    echo "  [4] 🔬 Viz    [5] 📊 Info     [6] 🐍 Python"
    echo "  [0] Exit"
    echo ""
    read -p "Choice: " c
    case $c in
        1) setup && python3 portable_agent/bridge.py . --mode interactive; read -p "Enter..." ;;
        2) setup && python3 portable_agent/bridge.py . --mode serve --port 8080; read -p "Enter..." ;;
        3) 
            setup || continue
            echo ""
            echo "  ENVIRONMENTS: CartPole-v1, LunarLander-v3, ALE/Breakout-v5, BipedalWalker-v3..."
            read -p "Env (CartPole-v1): " e
            read -p "Episodes (10): " ep
            read -p "Render? (y/n): " r
            read -p "Online learn? (y/n): " l
            renderarg=""
            onlinearg=""
            [[ "$r" == "y" ]] && renderarg="--render"
            [[ "$l" == "y" ]] && onlinearg="--online-learn"
            python3 portable_agent/bridge.py . --mode gym --gym-env ${e:-CartPole-v1} --episodes ${ep:-10} $renderarg $onlinearg
            read -p "Enter..."
            ;;
        4) setup && python3 portable_agent/visualize.py; read -p "Enter..." ;;
        5) cat metadata.json; read -p "Enter..." ;;
        6) setup && python3 -i -c "from portable_agent.bridge import AgentBridge; agent = AgentBridge.load('.')" ;;
        0) exit 0 ;;
    esac
done
"""
            zf.writestr("start.sh", start_sh)
            
            # Include portable_agent sources (for visualizer, etc.)
            self._write_portable_agent_sources(zf)

        archive_buffer.seek(0)
        return archive_buffer

    def _generate_ensemble_runner_script(self, export_format: str, metadata: Dict[str, Any]) -> str:
        action_map_str = json.dumps(ACTION_MAP)
        script = """
import onnxruntime
import numpy as np
import json
import os
import time

ACTION_MAP = {action_map_str}

class EnsembleRunner:
    def __init__(self, model_filename="{model_filename}", metadata_filename="metadata.json"):
        self.model_filename = model_filename
        self.metadata_filename = metadata_filename
        if not os.path.exists(self.model_filename):
            raise FileNotFoundError(f"Model file not found: {{self.model_filename}}")
        if not os.path.exists(self.metadata_filename):
            raise FileNotFoundError(f"Metadata file not found: {{self.metadata_filename}}")

        with open(self.metadata_filename, "r") as f:
            self.metadata = json.load(f)

        ensemble = self.metadata.get('ensemble', {{}})
        members = ensemble.get('members', [])
        self.member_names = [m['name'] for m in members]
        self.input_dim = ensemble.get('max_input_dim', 0)

        print("\\n--- Ensemble Loaded ---")
        print(f"Members: {{', '.join(self.member_names)}}")
        print(f"Input Dim: {{self.input_dim}}")
        print(f"Exported: {{self.metadata['export_timestamp']}}")
        print("-----------------------\\n")

        self.session = None
        if "{export_format}" == "onnx":
            providers = onnxruntime.get_available_providers()
            if 'CUDAExecutionProvider' in providers:
                self.session = onnxruntime.InferenceSession(self.model_filename, providers=['CUDAExecutionProvider'])
                print("Using CUDAExecutionProvider for ONNX inference.")
            else:
                self.session = onnxruntime.InferenceSession(self.model_filename, providers=['CPUExecutionProvider'])
                print("Using CPUExecutionProvider for ONNX inference.")
        elif "{export_format}" == "torchscript":
            import torch
            self.model = torch.jit.load(self.model_filename)
            self.model.eval()
            print("TorchScript ensemble loaded.")

    def decide_actions(self, state_vector):
        if len(state_vector) != self.input_dim:
            raise ValueError(f"State vector must have {{self.input_dim}} dimensions, got {{len(state_vector)}}")

        if "{export_format}" == "onnx":
            state_array = np.array(state_vector, dtype=np.float32).reshape(1, -1)
            inputs = {{self.session.get_inputs()[0].name: state_array}}
            outputs = self.session.run(None, inputs)
            # outputs is a list; align to member order
            decisions = {{}}
            for name, out in zip(self.member_names, outputs):
                idx = int(np.argmax(out))
                decisions[name] = ACTION_MAP.get(idx, str(idx))
            return decisions
        elif "{export_format}" == "torchscript":
            import torch
            state_tensor = torch.tensor(state_vector, dtype=torch.float32).unsqueeze(0)
            with torch.no_grad():
                outs = self.model(state_tensor)
            decisions = {{}}
            for name, out in zip(self.member_names, outs):
                idx = int(torch.argmax(out).item())
                decisions[name] = ACTION_MAP.get(idx, str(idx))
            return decisions
        else:
            raise ValueError(f"Unsupported export format: {{self.metadata['export_format']}}")

if __name__ == '__main__':
    runner = EnsembleRunner()
    dummy_state = np.random.rand(runner.input_dim)
    decisions = runner.decide_actions(dummy_state)
    print("Decisions:", decisions)
"""
        return script.format(action_map_str=action_map_str,
                             model_filename=f"brain.{export_format}",
                             export_format=export_format)

    def compile_capsules_to_ensemble(self,
                                     capsules: List['OrganismCapsule'],
                                     export_format: str = 'onnx',
                                     example_state: Any = None,
                                     vocabulary: Any = None,
                                     conversation_history: List[Dict] = None,
                                     knowledge_web: Any = None,
                                     context_memory: Any = None,
                                     causation_explorer: Any = None,
                                     alliance_system: Any = None) -> BytesIO:
        """Compile multiple capsules into a single ensemble model archive.
        
        Args:
            capsules: List of OrganismCapsule objects
            export_format: 'onnx' or 'torchscript'
            example_state: Example state for tracing
            vocabulary: LanguageVocabulary object for chat system
            conversation_history: List of conversation history entries
            knowledge_web: LinguisticKnowledgeWeb for semantic relationships
            context_memory: ContextMemory for word embeddings and language anchors
            causation_explorer: CausationExplorer for event history
            alliance_system: AllianceWarfare for social context

        All brains receive the same state vector (max input dim); per-brain
        slicing/padding is handled inside the wrapper for compatibility.
        """
        if export_format not in ['onnx', 'torchscript']:
            raise ValueError("Ensemble export supports 'onnx' and 'torchscript' only.")

        # Reconstruct brains
        brains = []
        names = []
        members_meta = []
        for cap in capsules:
            b = self._reconstruct_brain_from_capsule(cap)
            # CRITICAL: Move brain to CPU for export (avoids cuda/cpu device mismatch)
            b = b.cpu()
            brains.append(b)
            name = str(cap.organism_id)
            names.append(name)
            members_meta.append({
                'organism_id': name,
                'name': name,
                'input_dim': b.input_dim,
                'output_dim': b.output_dim,
                'has_language_head': getattr(b, 'use_language_head', False),
                'has_attention': getattr(b, 'use_attention', False)
            })

        if not brains:
            raise ValueError("No capsules provided for ensemble export.")

        wrapper = self.MultiOrganismWrapper(brains, names)
        wrapper.eval()  # Disable dropout for deterministic tracing
        wrapper = wrapper.cpu()  # Ensure wrapper is on CPU

        # Prepare deterministic input (on CPU to match model)
        if example_state is not None:
            try:
                arr = np.asarray(example_state, dtype=np.float32).reshape(1, -1)
                if arr.shape[1] < wrapper.max_input_dim:
                    pad = np.zeros((1, wrapper.max_input_dim - arr.shape[1]), dtype=np.float32)
                    arr = np.concatenate([arr, pad], axis=1)
                elif arr.shape[1] > wrapper.max_input_dim:
                    arr = arr[:, :wrapper.max_input_dim]
                dummy_input = torch.from_numpy(arr).cpu()
            except Exception:
                dummy_input = torch.zeros(1, wrapper.max_input_dim, dtype=torch.float32, device='cpu')
        else:
            dummy_input = torch.zeros(1, wrapper.max_input_dim, dtype=torch.float32, device='cpu')

        # Export
        model_buffer = BytesIO()
        chosen_format = export_format
        if export_format == 'onnx':
            try:
                # Build output names based on whether language heads exist
                if wrapper.any_language_head:
                    # Action outputs + language outputs for members with language heads
                    output_names = [f"action_{n}" for n in names]
                    for i, (name, has_lang) in enumerate(zip(names, wrapper.has_language_heads)):
                        if has_lang:
                            output_names.append(f"language_{name}")
                else:
                    output_names = [f"out_{n}" for n in names]
                
                torch.onnx.export(
                    wrapper,
                    dummy_input,
                    model_buffer,
                    input_names=['input'],
                    output_names=output_names,
                    dynamic_axes={'input': {0: 'batch_size'}},
                    opset_version=11
                )
                logger.info(f"✓ Successfully exported ensemble to ONNX format ({model_buffer.tell()} bytes)")
            except Exception as e:
                logger.warning(f"✗ ONNX export failed: {type(e).__name__}: {e}")
                logger.warning("Falling back to TorchScript export.")
                model_buffer = BytesIO()
                traced = torch.jit.trace(wrapper, (dummy_input,))
                torch.jit.save(traced, model_buffer)
                model_buffer.seek(0)
                chosen_format = 'torchscript'
        else:
            # Use trace instead of script - script fails on OrganismBrain's complex control flow
            traced = torch.jit.trace(wrapper, (dummy_input,))
            torch.jit.save(traced, model_buffer)
            model_buffer.seek(0)

        # Compute behavioral fingerprints for each member
        logger.info("Computing behavioral fingerprints for ensemble members...")
        for i, (brain, cap, member_meta) in enumerate(zip(brains, capsules, members_meta)):
            try:
                fingerprint = self._compute_behavioral_fingerprint(brain, num_samples=50)
                member_meta['behavioral_fingerprint'] = fingerprint
                member_meta['fitness'] = self._extract_fitness_value(cap)
                member_meta['generation'] = getattr(cap, 'generation', None)
                logger.info(f"  Member {i+1}/{len(brains)}: {fingerprint['personality_label']} "
                           f"(dominant: {fingerprint['dominant_action']})")
            except Exception as e:
                logger.warning(f"Could not compute fingerprint for member {i}: {e}")
                member_meta['behavioral_fingerprint'] = {'error': str(e)}

        # Compute aggregate ensemble behavioral profile
        ensemble_action_dist = {}
        ensemble_tendencies = {'cooperative': 0, 'competitive': 0, 'passive': 0}
        personality_counts = {}
        
        for member_meta in members_meta:
            fp = member_meta.get('behavioral_fingerprint', {})
            if 'error' in fp:
                continue
            # Aggregate action distributions
            for action, prob in fp.get('action_distribution', {}).items():
                ensemble_action_dist[action] = ensemble_action_dist.get(action, 0) + prob
            # Aggregate tendencies
            for tendency, score in fp.get('behavioral_tendencies', {}).items():
                ensemble_tendencies[tendency] = ensemble_tendencies.get(tendency, 0) + score
            # Count personalities
            personality = fp.get('personality_label', 'unknown')
            personality_counts[personality] = personality_counts.get(personality, 0) + 1
        
        # Normalize aggregates
        n_members = len([m for m in members_meta if 'error' not in m.get('behavioral_fingerprint', {})])
        if n_members > 0:
            ensemble_action_dist = {k: round(v / n_members, 4) for k, v in ensemble_action_dist.items()}
            ensemble_tendencies = {k: round(v / n_members, 4) for k, v in ensemble_tendencies.items()}

        # Metadata
        metadata = {
            'export_timestamp': datetime.datetime.now().isoformat(),
            'export_format': chosen_format,
            'ensemble': {
                'members': members_meta,
                'member_count': len(members_meta),
                'max_input_dim': wrapper.max_input_dim,
                'aggregate_behavioral_profile': {
                    'action_distribution': ensemble_action_dist,
                    'behavioral_tendencies': ensemble_tendencies,
                    'personality_distribution': personality_counts,
                    'dominant_personalities': sorted(personality_counts.keys(), 
                                                     key=lambda x: personality_counts[x], 
                                                     reverse=True)[:3] if personality_counts else []
                }
            },
            'runtime_dependencies': {
                'onnxruntime': onnxruntime.__version__ if ONNX_AVAILABLE else 'not installed',
                'numpy': np.__version__,
                'python': sys.version.split(' ')[0]
            }
        }

        # Runner
        runner_script = self._generate_ensemble_runner_script(chosen_format, metadata)

        # Package (pass capsules for language data extraction, plus chat vocabulary and semantic systems)
        return self._create_ensemble_archive(
            model_buffer, metadata, runner_script, capsules, vocabulary, conversation_history,
            knowledge_web=knowledge_web, context_memory=context_memory,
            causation_explorer=causation_explorer, alliance_system=alliance_system
        )

    def compile_capsule_to_agent(self, 
                                 capsule: OrganismCapsule, 
                                 export_format: str = 'onnx',
                                 include_history: bool = True,
                                 example_state: Any = None) -> BytesIO:
        """
        Compiles an OrganismCapsule into a deployable agent archive (ZIP file).
        
        Args:
            capsule: The OrganismCapsule object containing the agent's state.
            export_format: The format for the neural network model ('onnx', 'torchscript', 'statedict').
            include_history: If True, includes more detailed history/causation data.
            
        Returns:
            BytesIO: A memory buffer containing the ZIP archive.
        """
        if export_format not in self.supported_formats:
            raise ValueError(f"Unsupported export format: {export_format}. Supported: {self.supported_formats}")

        logger.info(f"Compiling organism {capsule.organism_id} to {export_format.upper()} format.")
        
        # 1. Reconstruct the neural brain
        brain = self._reconstruct_brain_from_capsule(capsule)
        
        # 2. Prepare deterministic input for ONNX export (and TorchScript tracing if used)
        if example_state is not None:
            try:
                arr = np.asarray(example_state, dtype=np.float32)
                arr = arr.reshape(1, -1)
                # Pad or truncate to match expected input_dim
                if arr.shape[1] < brain.input_dim:
                    pad = np.zeros((1, brain.input_dim - arr.shape[1]), dtype=np.float32)
                    arr = np.concatenate([arr, pad], axis=1)
                elif arr.shape[1] > brain.input_dim:
                    arr = arr[:, :brain.input_dim]
                dummy_input = torch.from_numpy(arr)
            except Exception:
                dummy_input = torch.zeros(1, brain.input_dim, dtype=torch.float32)
        else:
            dummy_input = torch.zeros(1, brain.input_dim, dtype=torch.float32)
        
        # 3. Export the brain to the specified format
        model_buffer = BytesIO()
        chosen_format = export_format
        if export_format == 'onnx':
            try:
                self._export_onnx(brain, dummy_input, model_buffer)
                logger.info(f"✓ Successfully exported to ONNX format ({model_buffer.tell()} bytes)")
            except Exception as e:
                # Graceful fallback: if ONNX dependencies missing, fallback to TorchScript
                logger.warning(f"✗ ONNX export failed: {type(e).__name__}: {e}")
                logger.warning("Falling back to TorchScript export.")
                model_buffer = BytesIO()
                self._export_torchscript(brain, model_buffer)
                chosen_format = 'torchscript'
        elif export_format == 'torchscript':
            self._export_torchscript(brain, model_buffer)
        elif export_format == 'statedict':
            self._export_statedict(brain, model_buffer)
        
        # 4. Create rich metadata
        metadata = self._create_rich_metadata(capsule, brain)
        metadata['export_format'] = chosen_format # Add (possibly updated) export format to metadata
        
        # 4b. Compute behavioral fingerprint by sampling the brain
        try:
            logger.info(f"Computing behavioral fingerprint for {capsule.organism_id}...")
            behavioral_fingerprint = self._compute_behavioral_fingerprint(brain, num_samples=100)
            metadata['behavioral_fingerprint'] = behavioral_fingerprint
            logger.info(f"Behavioral profile: {behavioral_fingerprint['personality_label']} "
                       f"(cooperative={behavioral_fingerprint['behavioral_tendencies']['cooperative']:.2f}, "
                       f"competitive={behavioral_fingerprint['behavioral_tendencies']['competitive']:.2f})")
        except Exception as e:
            logger.warning(f"Could not compute behavioral fingerprint: {e}")
            metadata['behavioral_fingerprint'] = {'error': str(e)}
        
        # 5. Generate runner script
        runner_script = self._generate_runner_script(chosen_format, metadata)

        # 5b. Build agent state payload for living runtime
        agent_state_payload = self._build_agent_state_payload(capsule, metadata)
        
        # 6. Package into ZIP archive
        return self._create_agent_archive(
            model_buffer,
            metadata,
            runner_script,
            capsule,
            agent_state_payload
        )

    def compile_cocoon(self,
                       capsules: List['OrganismCapsule'],
                       vocabulary: Any = None,
                       knowledge_web: Any = None,
                       context_memory: Any = None,
                       causation_explorer: Any = None,
                       alliance_system: Any = None,
                       training_config: Dict[str, Any] = None,
                       include_gym: bool = True,
                       include_http: bool = True,
                       compress_data: bool = True,
                       export_format: str = 'cocoon',
                       conversation_history: List[Dict] = None,
                       attractor_landscape: Any = None,
                       shared_state: Dict[str, Any] = None,
                       graph_image_base64: str = None) -> Tuple[str, Optional[bytes]]:
        """
        🦋 COCOON COMPILER - Single-file deployable agent
        Compiles organism(s) into a SINGLE self-contained Python file that can run solo or ensemble.
        
        export_format options:
            - 'cocoon': Python single-file (default)
            - 'onnx': ONNX model file (Netron-viewable)
            - 'torchscript': TorchScript model file (Netron-viewable)
            - 'package': Full package (cocoon.py + ONNX + README + metadata)
        
        New in v2.1:
            - attractor_landscape: AttractorLandscape instance for fixed point/bifurcation state
            - shared_state: Current shared_simulation_state dict for snapshot data
            - Formation fingerprint embedded in README
            - Knowledge graph visualization embedded in README
        
        Returns:
            (cocoon_source, model_bytes) - model_bytes is None for 'cocoon' format
        """
        logger.info(f"[COCOON] Compiling {len(capsules)} organism(s) into single-file cocoon...")

        is_ensemble = len(capsules) > 1
        mode_str = "ENSEMBLE" if is_ensemble else "SOLO"
        logger.info(f"[COCOON] Mode: {mode_str}")

        # 1) Serialize brains
        brain_data_list = []
        brain_configs = []
        organism_names = []

        for entity in capsules:
            brain = self._get_brain_from_entity(entity)
            name = self._get_organism_id(entity)
            organism_names.append(name)

            state_buffer = BytesIO()
            torch.save(brain.state_dict(), state_buffer)
            state_bytes = state_buffer.getvalue()
            if compress_data:
                state_bytes = zlib.compress(state_bytes, level=9)
            state_b64 = base64.b64encode(state_bytes).decode('ascii')
            brain_data_list.append(state_b64)

            # Extract fitness from capsule if available
            fitness = 1.0
            if hasattr(entity, 'fitness') and entity.fitness:
                extracted = self._extract_fitness_value(entity)
                if extracted is not None:
                    fitness = extracted

            config = {
                'organism_id': name,
                'input_dim': brain.input_dim,
                'hidden_dim': brain.hidden_dim,
                'output_dim': brain.output_dim,
                'vocab_size': getattr(brain, 'vocab_size', 1000),
                'use_attention': getattr(brain, 'use_attention', False),
                'use_language_head': getattr(brain, 'use_language_head', False),
                'use_concept_head': getattr(brain, 'use_concept_head', False),
                'num_attention_heads': getattr(brain, 'num_attention_heads', 4),
                'num_key_compositions': getattr(brain, 'num_key_compositions', 15),
                'dropout': getattr(brain, 'dropout_rate', 0.1),
                'fitness': fitness,  # Include organism fitness for decision matrix
                # Hopfield layer params
                'use_hopfield': getattr(brain, 'use_hopfield', False),
                'hopfield_patterns': getattr(brain, 'hopfield_patterns', 32),
                'hopfield_iterations': getattr(brain, 'hopfield_iterations', 5),
                'hopfield_beta': getattr(brain, 'hopfield_beta', 1.0),
            }
            brain_configs.append(config)

        # 2) Vocabulary - FULL BASE POOL + runtime learned
        vocab_data = self._build_full_vocabulary_export(vocabulary)
        logger.info(f"[COCOON] Vocabulary export: {vocab_data['vocab_size']:,} words ({vocab_data.get('base_pool_size', 0):,} base + runtime)")
        vocab_json = json.dumps(vocab_data, default=_json_default)
        vocab_bytes = zlib.compress(vocab_json.encode('utf-8'), level=9) if compress_data else vocab_json.encode('utf-8')
        vocab_b64 = base64.b64encode(vocab_bytes).decode('ascii')

        # 3) Knowledge web - FULL BASE POOL + runtime discoveries
        kw_data = self._build_full_knowledge_web_export(knowledge_web)
        logger.info(f"[COCOON] Knowledge web export: {kw_data['concept_count']:,} concepts, {kw_data['relation_count']:,} relations")
        kw_json = json.dumps(kw_data, default=_json_default)
        kw_bytes = zlib.compress(kw_json.encode('utf-8'), level=9) if compress_data else kw_json.encode('utf-8')
        kw_b64 = base64.b64encode(kw_bytes).decode('ascii')

        # 4) Training config
        default_training = {
            'learning_rate': 0.001,
            'batch_size': 32,
            'gamma': 0.99,
            'epsilon': 0.1,
            'epsilon_decay': 0.995,
            'epsilon_min': 0.01,
            'rl_loss_weight': 0.8,
            'language_loss_weight': 0.1,
            'concept_loss_weight': 0.1,
            'buffer_size': 10000,
        }
        if training_config:
            default_training.update(training_config)
        config_json = json.dumps(default_training)
        config_bytes = zlib.compress(config_json.encode('utf-8'), level=9) if compress_data else config_json.encode('utf-8')
        config_b64 = base64.b64encode(config_bytes).decode('ascii')

        # 5) Architecture
        arch_data = {
            'brain_configs': brain_configs,
            'organism_names': organism_names,
            'ensemble_size': len(capsules),
            'is_ensemble': is_ensemble,
        }
        arch_json = json.dumps(arch_data)
        arch_bytes = zlib.compress(arch_json.encode('utf-8'), level=9) if compress_data else arch_json.encode('utf-8')
        arch_b64 = base64.b64encode(arch_bytes).decode('ascii')

        # 6) Atomic Language System - per-organism linguistic atoms (Gap 5 Fix: Preserve individual data)
        # FIXED: Support both live organisms (.atomic_language) and capsules (.language)
        atomic_lang_data = []
        for entity in capsules:
            organism_id = self._get_organism_id(entity)
            organism_data = {'organism_id': organism_id, 'atoms': {}, 'concept_order': []}
            
            # Try 1: Live organism with atomic_language attribute
            if hasattr(entity, 'atomic_language') and entity.atomic_language is not None:
                als = entity.atomic_language
                if hasattr(als, 'to_dict'):
                    organism_data = als.to_dict()
                elif hasattr(als, 'atoms'):
                    # Manual extraction if no to_dict
                    organism_data = {
                        'organism_id': organism_id,
                        'atoms': {k: (v.to_dict() if hasattr(v, 'to_dict') else {}) for k, v in als.atoms.items()},
                        'concept_order': getattr(als, '_concept_order', [])
                    }
                logger.info(f"[COCOON] Captured atomic language from live organism {organism_id}: {len(organism_data.get('atoms', {}))} atoms")
            
            # Try 2: Capsule with language snapshot (LanguageSnapshot)
            elif hasattr(entity, 'language') and entity.language is not None:
                lang_snap = entity.language
                if hasattr(lang_snap, 'to_dict'):
                    snap_dict = lang_snap.to_dict()
                    # LanguageSnapshot has 'atoms' as Dict[str, Dict] - convert to cocoon format
                    organism_data = {
                        'organism_id': organism_id,
                        'atoms': snap_dict.get('atoms', {}),
                        'concept_order': snap_dict.get('concept_order', [])
                    }
                elif isinstance(lang_snap, dict):
                    organism_data = {
                        'organism_id': organism_id,
                        'atoms': lang_snap.get('atoms', {}),
                        'concept_order': lang_snap.get('concept_order', [])
                    }
                logger.info(f"[COCOON] Captured language snapshot from capsule {organism_id}: {len(organism_data.get('atoms', {}))} atoms")
            
            # Try 3: Legacy atomic_language_state attribute (deprecated)
            elif hasattr(entity, 'atomic_language_state') and entity.atomic_language_state:
                als = entity.atomic_language_state
                if isinstance(als, dict) and 'atoms' in als:
                    organism_data = als
            
            atomic_lang_data.append(organism_data)
            
        atomic_json = json.dumps(atomic_lang_data, default=_json_default)
        atomic_bytes = zlib.compress(atomic_json.encode('utf-8'), level=9) if compress_data else atomic_json.encode('utf-8')
        atomic_lang_b64 = base64.b64encode(atomic_bytes).decode('ascii')

        # 7) Conversation History - preserve from training if available
        if conversation_history:
            # Convert conversation history to serializable format
            messages = []
            topics = {}
            for entry in conversation_history:
                msg = {
                    'user': entry.get('user_message', ''),
                    'response': entry.get('aggregated_response', ''),
                    'timestamp': entry.get('timestamp', 0),
                    'organisms_responded': len(entry.get('organism_responses', []))
                }
                messages.append(msg)
                # Extract topics from responses
                for word in msg['user'].lower().split():
                    if len(word) > 3:
                        topics[word] = topics.get(word, 0) + 1
            conversation_data = {
                'messages': messages[-100:],  # Keep last 100 conversations
                'topics': dict(sorted(topics.items(), key=lambda x: -x[1])[:50]),  # Top 50 topics
                'turn_count': len(conversation_history)
            }
            logger.info(f"[COCOON] 💬 Preserving {len(messages)} conversation turns, {len(topics)} topics")
        else:
            conversation_data = {'messages': [], 'topics': {}, 'turn_count': 0}
        conv_json = json.dumps(conversation_data)
        conv_bytes = zlib.compress(conv_json.encode('utf-8'), level=9) if compress_data else conv_json.encode('utf-8')
        conversation_b64 = base64.b64encode(conv_bytes).decode('ascii')

        # 8) Alliance System - preserve FULL social structure (CRITICAL for emergent behavior)
        # "Connections formed are causeways for rationality" - alliances ARE the social brain
        alliance_data = self._extract_alliance_data_for_cocoon(capsules, alliance_system, organism_names)
        if alliance_data.get('alliances'):
            logger.info(f"[COCOON] 🤝 Alliance structure: {len(alliance_data['alliances'])} alliances, "
                       f"{len(alliance_data['organism_trust'])} trust records, "
                       f"{len(alliance_data['organism_stats'])} competition stats")
        else:
            logger.info(f"[COCOON] 🤝 No alliance structure to export (organisms may form alliances at runtime)")
        alliance_json = json.dumps(alliance_data, default=_json_default)
        alliance_bytes = zlib.compress(alliance_json.encode('utf-8'), level=9) if compress_data else alliance_json.encode('utf-8')
        alliance_b64 = base64.b64encode(alliance_bytes).decode('ascii')

        # Generate cocoon source (always needed for 'cocoon' and 'package' formats)
        cocoon_source_shell = self._generate_cocoon_source(
            brain_data_list=brain_data_list,
            arch_b64=arch_b64,
            vocab_b64=vocab_b64,
            kw_b64=kw_b64,
            config_b64=config_b64,
            atomic_lang_b64=atomic_lang_b64,
            conversation_b64=conversation_b64,
            alliance_b64=alliance_b64,
            compressed=compress_data,
            include_gym=include_gym,
            include_http=include_http,
            is_ensemble=is_ensemble,
            organism_names=organism_names,
            readme_b64="",
        )

        # 🧬 Generate Formation Fingerprint - the emergent history of this cocoon
        formation_fingerprint = self._generate_formation_fingerprint(
            capsules=capsules,
            causation_explorer=causation_explorer,
            alliance_system=alliance_system,
            attractor_landscape=attractor_landscape,
            shared_state=shared_state
        )
        if formation_fingerprint:
            logger.info(f"[COCOON] 🧬 Formation fingerprint: {len(formation_fingerprint)} sections")
        
        # 🧠 Generate interactive ensemble topology HTML visualization
        topology_html = None
        try:
            topology_html = self._generate_ensemble_topology_html(capsules, brain_configs)
            logger.info(f"[COCOON] 🧠 Generated topology visualization: {len(topology_html):,} chars")
        except Exception as e:
            logger.warning(f"[COCOON] Could not generate topology HTML: {e}")

        readme = self._generate_cocoon_readme(
            organism_names=organism_names,
            brain_configs=brain_configs,
            metadata={
                'generated': datetime.datetime.now().isoformat(),
                'template_size': f"{len(cocoon_source_shell):,} chars (code only)",
                'num_organisms': len(capsules),
            },
            is_ensemble=is_ensemble,
            formation_fingerprint=formation_fingerprint,
            has_topology_html=topology_html is not None,
        )

        readme_b64 = base64.b64encode(readme.encode('utf-8')).decode('ascii') if readme else ""

        cocoon_source = self._generate_cocoon_source(
            brain_data_list=brain_data_list,
            arch_b64=arch_b64,
            vocab_b64=vocab_b64,
            kw_b64=kw_b64,
            config_b64=config_b64,
            atomic_lang_b64=atomic_lang_b64,
            conversation_b64=conversation_b64,
            alliance_b64=alliance_b64,
            compressed=compress_data,
            include_gym=include_gym,
            include_http=include_http,
            is_ensemble=is_ensemble,
            organism_names=organism_names,
            readme_b64=readme_b64,
        )

        # Handle different export formats
        if export_format == 'cocoon':
            logger.info(f"[COCOON] ✅ Generated cocoon: {len(cocoon_source):,} characters + README ({len(readme):,} chars)")
            # Return tuple: (source, readme, topology_html) for separate file saving
            return cocoon_source, readme, topology_html
        
        elif export_format == 'onnx':
            # ═══════════════════════════════════════════════════════════════════════
            # COMPLETE ONNX PACKAGE - Neural model + ALL subsystems
            # ═══════════════════════════════════════════════════════════════════════
            # ONNX itself is inference-only, but we bundle everything needed:
            #   - brain.onnx (neural network for fast inference)
            #   - subsystems.json (AtomicLang, KnowledgeWeb, ConversationHistory, VP config)
            #   - vocabulary.json
            #   - metadata.json
            #   - loader.py (Python script to use full agent)
            # ═══════════════════════════════════════════════════════════════════════
            import zipfile
            zip_buffer = BytesIO()
            
            brain = self._get_brain_from_entity(capsules[0])
            brain = _safe_brain_to_cpu(brain)
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                # 1. ONNX model
                onnx_buffer = BytesIO()
                try:
                    dummy_input = torch.randn(1, brain.input_dim, device='cpu')
                    torch.onnx.export(
                        brain, dummy_input, onnx_buffer,
                        export_params=True, opset_version=14,
                        do_constant_folding=True,
                        input_names=['state'],
                        output_names=['action_probs', 'language_logits'] if brain.use_language_head else ['action_probs'],
                    )
                    onnx_buffer.seek(0)
                    zf.writestr('brain.onnx', onnx_buffer.read())
                    logger.info(f"[ONNX] ✅ Neural model: {onnx_buffer.tell():,} bytes")
                except Exception as e:
                    logger.error(f"[ONNX] Neural export failed: {e}")
                
                # 2. ALL SUBSYSTEMS as JSON
                subsystems = {
                    'atomic_language': atomic_lang_data if atomic_lang_data else {},
                    'conversation_history': conversation_data if conversation_data else {},
                    'knowledge_web': kw_data,
                    'alliance_system': alliance_data,  # Social structure for alliance-weighted voting
                    'vp_config': {
                        'vigilance_base': 0.5,
                        'plasticity_base': 0.5,
                        'attention_weight': 0.3,
                        'novelty_weight': 0.3,
                        'uncertainty_weight': 0.2,
                        'energy_weight': 0.2,
                    },
                    'experience_buffer': {'max_size': 10000, 'gamma': 0.99, 'entries': []},
                }
                zf.writestr('subsystems.json', json.dumps(subsystems, indent=2, default=str))
                logger.info(f"[ONNX] ✅ Subsystems: AtomicLang, KnowledgeWeb, ConvHistory, Alliance, VP, ExpBuffer")
                
                # 3. Vocabulary
                zf.writestr('vocabulary.json', vocab_json)
                
                # 4. Metadata
                metadata = {
                    'generated': datetime.datetime.now().isoformat(),
                    'organism_id': self._get_organism_id(capsules[0]),
                    'brain_config': {
                        'input_dim': getattr(brain, 'input_dim', 25),
                        'hidden_dim': getattr(brain, 'hidden_dim', 64),
                        'output_dim': getattr(brain, 'output_dim', 6),
                        'use_language_head': getattr(brain, 'use_language_head', False),
                    },
                    'subsystems_included': ['AtomicLanguageSystem', 'ConversationHistory', 
                                           'EnhancedKnowledgeWeb', 'AllianceSystem', 'VPRuntime', 'ExperienceBuffer'],
                    'continued_learning': False,  # ONNX neural is inference-only
                    'symbolic_learning': True,    # But symbolic systems CAN grow
                    'format_version': '2.0',
                }
                zf.writestr('metadata.json', json.dumps(metadata, indent=2))
                
                # 5. Loader script
                loader_script = self._generate_onnx_loader()
                zf.writestr('loader.py', loader_script)
                zf.writestr('README.md', self._generate_onnx_readme(metadata))
            
            zip_buffer.seek(0)
            logger.info(f"[ONNX] ✅ Complete package: {zip_buffer.tell():,} bytes (neural + ALL subsystems)")
            return cocoon_source, zip_buffer.getvalue()
        
        elif export_format == 'torchscript':
            # ═══════════════════════════════════════════════════════════════════════
            # COMPLETE TORCHSCRIPT PACKAGE - Neural model + ALL subsystems
            # ═══════════════════════════════════════════════════════════════════════
            # TorchScript can only trace nn.Module forward pass, so we bundle:
            #   - brain.pt (traced neural network - CAN continue learning!)
            #   - subsystems.json (AtomicLang, KnowledgeWeb, ConversationHistory, VP config)
            #   - vocabulary.json
            #   - metadata.json
            #   - loader.py (Python script to reconstruct full agent)
            # ═══════════════════════════════════════════════════════════════════════
            import zipfile
            zip_buffer = BytesIO()
            
            brain = self._get_brain_from_entity(capsules[0])
            brain = _safe_brain_to_cpu(brain)
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                # 1. TorchScript model
                ts_buffer = BytesIO()
                try:
                    brain.eval()
                    input_dim = getattr(brain, 'input_dim', 25)
                    dummy_input = torch.randn(1, input_dim, device='cpu')
                    traced = torch.jit.trace(brain, (dummy_input,))
                    torch.jit.save(traced, ts_buffer)
                    ts_buffer.seek(0)
                    zf.writestr('brain.pt', ts_buffer.read())
                    logger.info(f"[TORCHSCRIPT] ✅ Neural model: {ts_buffer.tell():,} bytes")
                except Exception as e:
                    logger.error(f"[TORCHSCRIPT] Neural export failed: {e}")
                
                # 2. ALL SUBSYSTEMS as JSON (the missing pieces!)
                subsystems = {
                    'atomic_language': atomic_lang_data if atomic_lang_data else {},
                    'conversation_history': conversation_data if conversation_data else {},
                    'knowledge_web': kw_data,
                    'alliance_system': alliance_data,  # Social structure for alliance-weighted voting
                    'vp_config': {
                        'vigilance_base': 0.5,
                        'plasticity_base': 0.5,
                        'attention_weight': 0.3,
                        'novelty_weight': 0.3,
                        'uncertainty_weight': 0.2,
                        'energy_weight': 0.2,
                    },
                    'experience_buffer': {
                        'max_size': 10000,
                        'gamma': 0.99,
                        'entries': [],  # Empty - will grow during learning
                    },
                }
                zf.writestr('subsystems.json', json.dumps(subsystems, indent=2, default=str))
                logger.info(f"[TORCHSCRIPT] ✅ Subsystems: AtomicLang, KnowledgeWeb, ConvHistory, Alliance, VP, ExpBuffer")
                
                # 3. Vocabulary
                zf.writestr('vocabulary.json', vocab_json)
                
                # 4. Metadata
                metadata = {
                    'generated': datetime.datetime.now().isoformat(),
                    'organism_id': self._get_organism_id(capsules[0]),
                    'organism_count': len(capsules),
                    'brain_config': {
                        'input_dim': getattr(brain, 'input_dim', 25),
                        'hidden_dim': getattr(brain, 'hidden_dim', 64),
                        'output_dim': getattr(brain, 'output_dim', 6),
                        'use_language_head': getattr(brain, 'use_language_head', False),
                        'vocab_size': getattr(brain, 'vocab_size', 0),
                    },
                    'subsystems_included': [
                        'AtomicLanguageSystem',
                        'ConversationHistory', 
                        'EnhancedKnowledgeWeb',
                        'AllianceSystem',
                        'VPRuntime',
                        'ExperienceBuffer',
                    ],
                    'continued_learning': True,
                    'format_version': '2.0',
                }
                zf.writestr('metadata.json', json.dumps(metadata, indent=2))
                
                # 5. Loader script to reconstruct full agent
                loader_script = self._generate_torchscript_loader()
                zf.writestr('loader.py', loader_script)
                zf.writestr('README.md', self._generate_torchscript_readme(metadata))
            
            zip_buffer.seek(0)
            logger.info(f"[TORCHSCRIPT] ✅ Complete package: {zip_buffer.tell():,} bytes (neural + ALL subsystems)")
            return cocoon_source, zip_buffer.getvalue()
        
        elif export_format == 'statedict':
            # Export first brain state dict
            brain = self._get_brain_from_entity(capsules[0])
            brain = _safe_brain_to_cpu(brain)
            sd_buffer = BytesIO()
            torch.save(brain.state_dict(), sd_buffer)
            logger.info(f"[COCOON] ✅ Generated StateDict: {sd_buffer.tell():,} bytes")
            return cocoon_source, sd_buffer.getvalue()
        
        elif export_format == 'package':
            # ═══════════════════════════════════════════════════════════════════════
            # ULTIMATE PACKAGE - Everything you need to deploy the ensemble
            # ═══════════════════════════════════════════════════════════════════════
            # Contains:
            #   - brain_ensemble.onnx (ALL organisms wrapped in MultiOrganismWrapper)
            #   - brain_ensemble.pt (TorchScript version of same)
            #   - cocoon.py (self-contained Python with embedded weights)
            #   - bridge.py (universal runner for Gym/HTTP/CLI)
            #   - metadata.json (ensemble config, member profiles, behavioral fingerprints)
            #   - vocabulary.json (tokenization vocab)
            #   - requirements.txt
            #   - README.md
            # ═══════════════════════════════════════════════════════════════════════
            import zipfile
            zip_buffer = BytesIO()
            
            # Build the MultiOrganismWrapper for unified ensemble export
            brains = []
            names = []
            for entity in capsules:
                brain = self._get_brain_from_entity(entity)
                name = self._get_organism_id(entity)
                # CRITICAL: Handle torch.compile() models - get underlying model if compiled
                # torch.compile() wraps models and CUDA graphs cause issues on .cpu()
                if hasattr(brain, '_orig_mod'):
                    # Compiled model - use the original unwrapped module
                    brain = brain._orig_mod
                # Clone state dict to new model to avoid CUDA graph issues
                try:
                    brain_copy = brain.__class__.__new__(brain.__class__)
                    brain_copy.__dict__.update(brain.__dict__)
                    brain_copy.load_state_dict(brain.state_dict())
                    brain = brain_copy.cpu()
                except Exception:
                    # Fallback: just move to CPU (may fail on compiled models)
                    brain = brain.cpu()
                brains.append(brain)
                names.append(name)
            
            wrapper = self.MultiOrganismWrapper(brains, names)
            wrapper.eval()
            wrapper = wrapper.cpu()  # Ensure wrapper is also on CPU
            
            # Prepare dummy input for tracing (on CPU to match model)
            dummy_input = torch.zeros(1, wrapper.max_input_dim, dtype=torch.float32, device='cpu')
            
            export_results = {
                'onnx': {'success': False, 'size': 0, 'error': None},
                'torchscript': {'success': False, 'size': 0, 'error': None},
            }
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                # ─────────────────────────────────────────────────────────────
                # 1. ONNX ENSEMBLE MODEL
                # ─────────────────────────────────────────────────────────────
                onnx_buffer = BytesIO()
                try:
                    output_names = [f"action_{n}" for n in names]
                    if wrapper.any_language_head:
                        for i, (name, has_lang) in enumerate(zip(names, wrapper.has_language_heads)):
                            if has_lang:
                                output_names.append(f"language_{name}")
                    
                    torch.onnx.export(
                        wrapper,
                        dummy_input,
                        onnx_buffer,
                        input_names=['state'],
                        output_names=output_names,
                        dynamic_axes={'state': {0: 'batch_size'}},
                        opset_version=14,
                        do_constant_folding=True
                    )
                    onnx_buffer.seek(0)
                    onnx_bytes = onnx_buffer.read()
                    zf.writestr('brain_ensemble.onnx', onnx_bytes)
                    export_results['onnx'] = {'success': True, 'size': len(onnx_bytes), 'error': None}
                    logger.info(f"[PACKAGE] ✅ ONNX ensemble: {len(onnx_bytes):,} bytes")
                except Exception as e:
                    export_results['onnx'] = {'success': False, 'size': 0, 'error': str(e)}
                    logger.warning(f"[PACKAGE] ⚠️ ONNX export failed: {e}")
                
                # ─────────────────────────────────────────────────────────────
                # 2. TORCHSCRIPT ENSEMBLE MODEL
                # ─────────────────────────────────────────────────────────────
                ts_buffer = BytesIO()
                try:
                    traced = torch.jit.trace(wrapper, (dummy_input,))
                    torch.jit.save(traced, ts_buffer)
                    ts_buffer.seek(0)
                    ts_bytes = ts_buffer.read()
                    zf.writestr('brain_ensemble.pt', ts_bytes)
                    export_results['torchscript'] = {'success': True, 'size': len(ts_bytes), 'error': None}
                    logger.info(f"[PACKAGE] ✅ TorchScript ensemble: {len(ts_bytes):,} bytes")
                except Exception as e:
                    export_results['torchscript'] = {'success': False, 'size': 0, 'error': str(e)}
                    logger.warning(f"[PACKAGE] ⚠️ TorchScript export failed: {e}")
                
                # ─────────────────────────────────────────────────────────────
                # 3. COCOON.PY (self-contained Python)
                # ─────────────────────────────────────────────────────────────
                zf.writestr('cocoon.py', cocoon_source)
                logger.info(f"[PACKAGE] ✅ Cocoon source: {len(cocoon_source):,} chars")
                
                # ─────────────────────────────────────────────────────────────
                # 4. BRIDGE.PY (universal runner)
                # ─────────────────────────────────────────────────────────────
                bridge_script = self._generate_bridge_script(brain_configs, is_ensemble)
                zf.writestr('bridge.py', bridge_script)
                
                # ─────────────────────────────────────────────────────────────
                # 4b. PROTON_TOURNAMENT.PY (self-training battle system)
                # ─────────────────────────────────────────────────────────────
                tournament_path = Path(__file__).parent.parent / 'standalone_proton_tournament.py'
                if tournament_path.exists():
                    tournament_source = tournament_path.read_text(encoding='utf-8')
                    zf.writestr('proton_tournament.py', tournament_source)
                    logger.info(f"[PACKAGE] ✅ Proton Tournament: {len(tournament_source):,} chars")
                
                # ─────────────────────────────────────────────────────────────
                # 5. METADATA.JSON (comprehensive)
                # ─────────────────────────────────────────────────────────────
                # Compute behavioral fingerprints
                member_profiles = []
                for i, (brain, cfg) in enumerate(zip(brains, brain_configs)):
                    profile = dict(cfg)  # Copy config
                    try:
                        fingerprint = self._compute_behavioral_fingerprint(brain, num_samples=50)
                        profile['behavioral_fingerprint'] = fingerprint
                        logger.info(f"[PACKAGE] Member {i+1}: {fingerprint.get('personality_label', '?')}")
                    except Exception as e:
                        profile['behavioral_fingerprint'] = {'error': str(e)}
                    member_profiles.append(profile)
                
                metadata = {
                    'mode': 'ENSEMBLE' if is_ensemble else 'SOLO',
                    'num_organisms': len(capsules),
                    'organism_names': organism_names,
                    'max_input_dim': wrapper.max_input_dim,
                    'brain_configs': brain_configs,
                    'member_profiles': member_profiles,
                    'training_config': default_training,
                    'export_results': export_results,
                    'generated': datetime.datetime.now().isoformat(),
                    'package_contents': [
                        'brain_ensemble.onnx' if export_results['onnx']['success'] else None,
                        'brain_ensemble.pt' if export_results['torchscript']['success'] else None,
                        'cocoon.py',
                        'bridge.py',
                        'proton_tournament.py',
                        'metadata.json',
                        'vocabulary.json',
                        'requirements.txt',
                        'README.md',
                    ],
                }
                # Filter out None entries
                metadata['package_contents'] = [x for x in metadata['package_contents'] if x]
                zf.writestr('metadata.json', json.dumps(metadata, indent=2))
                
                # ─────────────────────────────────────────────────────────────
                # 6. VOCABULARY.JSON
                # ─────────────────────────────────────────────────────────────
                zf.writestr('vocabulary.json', vocab_json)
                
                # ─────────────────────────────────────────────────────────────
                # 7. REQUIREMENTS.TXT
                # ─────────────────────────────────────────────────────────────
                requirements = """# Butterfly Ensemble - Complete Package Dependencies
# Install with: pip install -r requirements.txt

# ═══════════════════════════════════════════════════════════════
# CORE DEPENDENCIES
# ═══════════════════════════════════════════════════════════════

# Neural network inference
torch>=2.0.0           # For TorchScript (.pt) models
onnxruntime>=1.15.0    # For ONNX models (CPU)
# onnxruntime-gpu>=1.15.0  # Uncomment for NVIDIA GPU acceleration

numpy>=1.21.0

# HTTP server & web interface
flask>=2.0.0

# P2P Networking (for CocoonLink battles)
websockets>=12.0       # Optional - for P2P mode

# ═══════════════════════════════════════════════════════════════
# GYMNASIUM ENVIRONMENTS - PROTON GAME ARENA
# ═══════════════════════════════════════════════════════════════
# Game selection inspired by Piers Anthony's "Apprentice Adept"
# Absorption mechanic inspired by "Highlander" (1986)

gymnasium>=0.29.0      # Core RL environments (63 built-in)
pygame>=2.5.0          # Visual rendering

# CLASSIC CONTROL (Built into gymnasium - always works!)
# CartPole-v1, MountainCar-v0, Acrobot-v1, Pendulum-v1
# FrozenLake-v1, CliffWalking-v1, Taxi-v3, Blackjack-v1

# BOX2D PHYSICS (pip install gymnasium[box2d])
# LunarLander-v3, BipedalWalker-v3, CarRacing-v3

# ATARI ARCADE (pip install ale-py)
# ALE/Pong-v5, ALE/Breakout-v5, ALE/SpaceInvaders-v5, etc.
# ale-py>=0.8.0

# MUJOCO PHYSICS (pip install gymnasium[mujoco])  
# Ant-v4, HalfCheetah-v4, Humanoid-v4, etc.
# mujoco>=2.3.0

# ═══════════════════════════════════════════════════════════════
# DRONE WARFARE ARENA (NASA JSBSim 6-DOF Physics)
# ═══════════════════════════════════════════════════════════════
# 8 game modes: free_fly, formation, pursuit, tag_battle,
#               zone_control, capture_flag, survival, escort

matplotlib>=3.8.0      # Trajectory visualization
# PyFlyt>=1.0.0        # Optional: 3D drone viz (pip install PyFlyt)

# ═══════════════════════════════════════════════════════════════
# QUICK START COMMANDS
# ═══════════════════════════════════════════════════════════════
# 
# Interactive chat:
#   python cocoon.py --mode chat
#
# Gym training (shows game menu):
#   python cocoon.py --mode gym
#
# Direct gym environment:
#   python cocoon.py --mode gym --env CartPole-v1 --episodes 100
#
# Drone warfare (extract + run):
#   python cocoon.py --unpack ./my_export
#   cd my_export && python cocoon_drone_adapter.py
#
# Tournament (multi-organism battles):
#   python cocoon.py --mode gym
#   -> Select "Tournament" from menu
#
# HTTP API server:
#   python cocoon.py --mode serve --port 8080
#
# P2P battles (connect to CocoonHatch):
#   python cocoon.py --mode link --hatch ws://localhost:8765
"""
                zf.writestr('requirements.txt', requirements)
                
                # ─────────────────────────────────────────────────────────────
                # 8. README.MD
                # ─────────────────────────────────────────────────────────────
                readme = self._generate_ultimate_readme(
                    organism_names, brain_configs, metadata, export_results, is_ensemble
                )
                zf.writestr('README.md', readme)
                
                # ─────────────────────────────────────────────────────────────
                # 9. QUICK-START SCRIPTS
                # ─────────────────────────────────────────────────────────────
                # Windows batch
                start_bat = """@echo off
echo ═══════════════════════════════════════════════════════════════
echo  Butterfly Ensemble - Quick Start
echo ═══════════════════════════════════════════════════════════════
echo.
echo 1. Interactive Chat
echo 2. Gymnasium Games (CartPole, etc)
echo 3. HTTP API Server
echo 4. Drone Warfare Arena (extract first)
echo 5. View Metadata
echo 0. Exit
echo.
set /p choice="Select option: "

if "%choice%"=="1" python cocoon.py --mode chat
if "%choice%"=="2" python cocoon.py --mode gym
if "%choice%"=="3" python cocoon.py --mode serve --port 8080
if "%choice%"=="4" (
    echo Extracting drone suite...
    python cocoon.py --unpack .
    echo.
    echo Run: python cocoon_drone_adapter.py
)
if "%choice%"=="5" type metadata.json
if "%choice%"=="0" exit /b

pause
"""
                zf.writestr('start.bat', start_bat)
                
                # Unix shell
                start_sh = """#!/bin/bash
echo "═══════════════════════════════════════════════════════════════"
echo " Butterfly Ensemble - Quick Start"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "1. Interactive Chat"
echo "2. Gymnasium Games (CartPole, etc)"
echo "3. HTTP API Server"
echo "4. Drone Warfare Arena (extract first)"
echo "5. View Metadata"
echo "0. Exit"
echo ""
read -p "Select option: " choice

case $choice in
    1) python cocoon.py --mode chat ;;
    2) python cocoon.py --mode gym ;;
    3) python cocoon.py --mode serve --port 8080 ;;
    4) python cocoon.py --unpack . && echo "Run: python cocoon_drone_adapter.py" ;;
    5) cat metadata.json ;;
    0) exit 0 ;;
esac
"""
                zf.writestr('start.sh', start_sh)
                
                # ─────────────────────────────────────────────────────────────
                # 10. SEMANTIC SYSTEMS (Full Intelligence Files)
                # ─────────────────────────────────────────────────────────────
                # These files contain the agent's learned semantic understanding
                
                # a) Semantic Convergence (Word Embeddings + Language Anchors)
                if context_memory is not None:
                    semantic_data = self._serialize_semantic_convergence(context_memory, capsules)
                    if semantic_data:
                        zf.writestr("semantic_convergence.json", json.dumps(semantic_data, indent=2))
                        logger.info(f"[PACKAGE] ✅ Semantic convergence: {semantic_data.get('total_words', 0)} words, "
                                   f"{semantic_data.get('total_anchors', 0)} anchors")
                        metadata['package_contents'].append('semantic_convergence.json')
                    
                    # Also write context_memory.json for standalone_butterfly_chat.py compatibility
                    context_memory_data = self._serialize_context_memory_full(context_memory, capsules)
                    if context_memory_data:
                        zf.writestr("context_memory.json", json.dumps(context_memory_data, indent=2))
                        logger.info(f"[PACKAGE] ✅ Context memory: {context_memory_data.get('total_anchors', 0)} anchors, "
                                   f"{context_memory_data.get('total_associations', 0)} associations")
                        metadata['package_contents'].append('context_memory.json')
                
                # b) Knowledge Web (Full Semantic Relationships)
                if knowledge_web is not None:
                    kw_data = self._serialize_knowledge_web_full(knowledge_web)
                    if kw_data:
                        zf.writestr("knowledge_web.json", json.dumps(kw_data, indent=2))
                        logger.info(f"[PACKAGE] ✅ Knowledge web: {kw_data.get('concept_count', 0)} concepts, "
                                   f"{kw_data.get('relation_count', 0)} relations")
                        metadata['package_contents'].append('knowledge_web.json')
                
                # c) Causation System (Event History)
                if causation_explorer is not None:
                    causation_data = self._serialize_causation_system(causation_explorer, capsules)
                    if causation_data:
                        zf.writestr("causation_system.json", json.dumps(causation_data, indent=2))
                        logger.info(f"[PACKAGE] ✅ Causation system: {causation_data.get('total_events', 0)} events")
                        metadata['package_contents'].append('causation_system.json')
                
                # d) Alliance System (Social Context)
                if alliance_system is not None:
                    alliance_data = self._serialize_alliance_system(alliance_system, capsules)
                    if alliance_data:
                        zf.writestr("alliance_system.json", json.dumps(alliance_data, indent=2))
                        logger.info(f"[PACKAGE] ✅ Alliance system: {alliance_data.get('alliance_count', 0)} alliances")
                        metadata['package_contents'].append('alliance_system.json')
                
                # Re-write metadata.json to include the semantic files we added
                zf.writestr('metadata.json', json.dumps(metadata, indent=2))
            
            # Verify we got at least one model format
            if not export_results['onnx']['success'] and not export_results['torchscript']['success']:
                logger.error("[PACKAGE] ❌ FAILED: Neither ONNX nor TorchScript export succeeded!")
                # Still return the package but log the error
            
            zip_buffer.seek(0)
            total_size = len(zip_buffer.getvalue())
            logger.info(f"[COCOON] ✅ Generated ULTIMATE package: {total_size:,} bytes")
            logger.info(f"[COCOON]    ONNX: {'✅' if export_results['onnx']['success'] else '❌'} "
                       f"TorchScript: {'✅' if export_results['torchscript']['success'] else '❌'}")
            return cocoon_source, zip_buffer.getvalue()
        
        else:
            logger.warning(f"[COCOON] Unknown format '{export_format}', defaulting to cocoon")
            return cocoon_source, None

    def _generate_cocoon_readme(self, organism_names: List[str], brain_configs: List[Dict], metadata: Dict, is_ensemble: bool,
                                 formation_fingerprint: Dict[str, Any] = None,
                                 has_topology_html: bool = False) -> str:
        """Generate comprehensive README for single cocoon.py export.
        
        This README explains:
        - What's embedded (neural brains, subsystems, vocabularies)
        - How to use (chat, gym, serve, export)
        - Continued learning capabilities
        - API reference
        - Formation fingerprint (emergent history)
        - Neural topology visualization link (if available)
        
        Returns:
            str: Complete README markdown text
        """
        org_list = "\n".join([f"  - `{name}`" for name in organism_names])
        
        subsystem_table = """| Subsystem | Purpose | Continued Learning |
|-----------|---------|-------------------|
| `OrganismBrain` | Neural network (action + language) | ✅ Yes - weights updated via backprop |
| `HopfieldLayer` | Iterative thought refinement (energy-based) | ✅ Yes - pattern memory learns |
| `MultiHeadAttention` | VP-aware self-attention | ✅ Yes - attention weights updated |
| `AtomicLanguageSystem` | Semantic units with emotion/context | ✅ Yes - atoms can be created/reinforced |
| `ConversationHistory` | Topic tracking & context memory | ✅ Yes - grows with each conversation |
| `EnhancedKnowledgeWeb` | Semantic relations between concepts | ✅ Yes - relations added/strengthened |
| `VPRuntime` | Self-regulation (Vigilance × Plasticity) | ✅ Yes - adapts from state |
| `ExperienceBuffer` | Learning from past experiences | ✅ Yes - buffer grows with experience |
| `SphereArena` | 3D swarm defense training game | ✅ Yes - organisms learn during play |"""
        
        # Build formation fingerprint section
        fingerprint_section = ""
        if formation_fingerprint:
            fp = formation_fingerprint
            fingerprint_lines = [
                "---",
                "",
                "## 🧬 Formation Fingerprint",
                "",
                "This cocoon's emergent history - how these organisms came to be:",
                "",
            ]
            
            # Organism stats
            if 'fitness_stats' in fp:
                fs = fp['fitness_stats']
                fingerprint_lines.append(f"**Fitness:** min={fs['min']}, max={fs['max']}, mean={fs['mean']}")
            if 'age_stats' in fp:
                ages = fp['age_stats']
                fingerprint_lines.append(f"**Age (cycles):** min={ages['min']}, max={ages['max']}, mean={ages['mean']}")
            fingerprint_lines.append("")
            
            # Causation summary
            if 'causation_summary' in fp:
                cs = fp['causation_summary']
                fingerprint_lines.append(f"**Events Witnessed:** {cs['total_events']:,} total")
                if cs.get('event_types'):
                    top_types = list(cs['event_types'].items())[:5]
                    types_str = ", ".join([f"{t[0]} ({t[1]})" for t in top_types])
                    fingerprint_lines.append(f"**Top Event Types:** {types_str}")
                fingerprint_lines.append("")
            
            # Alliance structure
            if 'alliance_structure' in fp:
                al = fp['alliance_structure']
                fingerprint_lines.append(f"**Alliance Landscape:** {al['total_alliances']} total alliances")
                if al.get('memberships'):
                    for m in al['memberships'][:3]:
                        fingerprint_lines.append(f"  - Alliance `{m['alliance_id']}` (tier {m['tier']}, {m['size']} members)")
                fingerprint_lines.append("")
            
            # Attractor landscape
            if 'attractor_landscape' in fp:
                al = fp['attractor_landscape']
                fingerprint_lines.append("**Attractor Landscape State:**")
                fingerprint_lines.append(f"  - Field Coherence: {al['field_coherence']}")
                fingerprint_lines.append(f"  - Field Entropy: {al['field_entropy']}")
                fingerprint_lines.append(f"  - Field Stability: {al['field_stability']}")
                if al['at_fixed_point']:
                    fingerprint_lines.append(f"  - 🎯 **At Fixed Point:** {al['fixed_point_type']}")
                fingerprint_lines.append(f"  - Total Fixed Points: {al['total_fixed_points']}")
                fingerprint_lines.append(f"  - Total Bifurcations: {al['total_bifurcations']}")
                fingerprint_lines.append("")
            
            # Simulation snapshot
            if 'simulation_snapshot' in fp:
                ss = fp['simulation_snapshot']
                fingerprint_lines.append("**Simulation Snapshot:**")
                if ss.get('population_count'):
                    fingerprint_lines.append(f"  - Population: {ss['population_count']}")
                if ss.get('cycle_count'):
                    fingerprint_lines.append(f"  - Cycles: {ss['cycle_count']}")
                if ss.get('generation'):
                    fingerprint_lines.append(f"  - Generation: {ss['generation']}")
                if ss.get('vp_current'):
                    fingerprint_lines.append(f"  - VP: {ss['vp_current']}")
                if ss.get('health_score'):
                    fingerprint_lines.append(f"  - Health: {ss['health_score']}")
                fingerprint_lines.append("")
            
            fingerprint_section = "\n".join(fingerprint_lines)
        
        # Build topology visualization section (reference external HTML file)
        topology_section = ""
        if has_topology_html:
            topology_section = """
---

## 🧠 Neural Topology Visualization

**[📊 Open Interactive Topology Viewer](ensemble_topology.html)**

The topology visualization provides:
- **Per-organism layers** - Toggle individual neural networks on/off
- **Overlay mode** - See all organisms' architectures superimposed
- **Stacked mode** - View organisms in horizontal strips
- **Grid mode** - Compare organisms side-by-side
- **Color-coded neurons** - Input (cyan), Hidden (magenta), Output (yellow), Language (green)

*Open the HTML file in a browser for the full interactive experience.*

"""
        
        return f'''# 🦋 Butterfly Cocoon - Standalone Agent

**Generated:** {metadata.get('generated', 'Unknown')}
**Mode:** {"ENSEMBLE" if is_ensemble else "SOLO"} ({len(organism_names)} organism{"s" if len(organism_names) > 1 else ""})
**Template Size:** {metadata.get('template_size', '~80KB')}
**Classes:** 15 (Neural + Language + Memory + Knowledge + VP)
{fingerprint_section}{topology_section}

---

## 🧠 What's Inside

This is a **MONOLITHIC** cocoon - a completely self-contained Python file with:

**Organisms:**
{org_list}

**Embedded Subsystems:**

{subsystem_table}

**Embedded Data:**
- Neural weights (Base64-encoded PyTorch state dicts)
- Vocabulary (token↔id mapping)
- Atomic language corpus (if available)
- Conversation history (if available)

---

## 🔥 Continued Learning

**YES, this cocoon supports continued learning!**

The cocoon.py file contains full PyTorch modules that can continue training:

1. **Full PyTorch modules** - can call `backward()` and update gradients
2. **ExperienceBuffer** - stores (state, action, reward) tuples for replay
3. **AtomicLanguageSystem** - creates new semantic atoms from conversations
4. **EnhancedKnowledgeWeb** - grows semantic relations as concepts connect
5. **ConversationHistory** - accumulates context over time

```python
# The agent learns from every interaction:
agent = CocoonAgent()
action, output = agent.get_action(state)  # Updates VP, stores experience
agent.atomic_lang.create_atom("new_concept", "definition", emotion=0.8)  # Creates new atom
agent.knowledge_web.add_relation("concept_a", "concept_b", "related_to", strength=0.9)  # Grows web
```

**Export Comparison:**

| Format | File | Learning | Subsystems | Portability |
|--------|------|----------|------------|-------------|
| `cocoon.py` | Python source | ✅ Full (neural + symbolic) | ✅ All | Python only |
| `.pt` | TorchScript | ✅ Neural only* | ❌ None | PyTorch/LibTorch/C++ |
| `.onnx` | ONNX model | ❌ Inference only | ❌ None | Universal (C++, JS, Rust) |
| `.statedict` | Weights only | ✅ Loadable | ❌ None | PyTorch |

*TorchScript (.pt) **CAN** continue learning! Load with `torch.jit.load()`, call `.train()`, run backward pass.
However, it only contains the neural network - no AtomicLanguageSystem, KnowledgeWeb, or other symbolic subsystems.

**Fine-tuning a TorchScript model:**
```python
import torch

# Load the exported TorchScript model
model = torch.jit.load("brain_ensemble.pt")
model.train()

# Fine-tune on new data
optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
for state, target in new_training_data:
    optimizer.zero_grad()
    output = model(state)
    loss = criterion(output, target)
    loss.backward()
    optimizer.step()

# Save updated model
torch.jit.save(model, "brain_finetuned.pt")
```

---

## 🚀 Quick Start

```bash
# View cocoon info
python cocoon.py --mode info

# Start chatting
python cocoon.py --mode chat

# Play games
python cocoon.py --mode gym --env CartPole-v1

# 3D sphere arena
python cocoon.py --mode sphere --train

# 🛸 Drone warfare (extract adapter first)
python cocoon.py --unpack ./my_cocoon
python cocoon_drone_adapter.py --mode tag_battle
```

---

## 📚 Complete Command Reference

### Mode Selection

| Mode | Command | Description |
|------|---------|-------------|
| **info** | `python cocoon.py --mode info` | Show organism metadata, vocabulary, architecture (default) |
| **chat** | `python cocoon.py --mode chat` | Interactive conversation with learning |
| **gym** | `python cocoon.py --mode gym` | Train/test in Gymnasium environments |
| **serve** | `python cocoon.py --mode serve` | HTTP API server |
| **sphere** | `python cocoon.py --mode sphere` | 3D Sphere Arena swarm defense |
| **link** | `python cocoon.py --mode link` | P2P networking for cocoon battles |
| **drone** | `python cocoon_drone_adapter.py` | 🛸 Drone warfare arena (companion script) |

---

### 💬 Chat Mode

Interactive conversation with the neural organisms. Learns from every interaction.

```bash
python cocoon.py --mode chat
python cocoon.py --mode chat --verbose
```

**In-Chat Commands:**

| Command | Description |
|---------|-------------|
| `quit` | Exit chat mode |
| `export <file.py>` | Save current state to new cocoon file |

---

### 🌐 Sphere Arena (3D Training)

Swarm defense game where organisms cooperate to catch falling balls.

| Command | Description |
|---------|-------------|
| `python cocoon.py --mode sphere` | Play sphere defense |
| `python cocoon.py --mode sphere --train` | Play + learn from experience |
| `python cocoon.py --mode sphere --demo` | Preview with dummy AI |
| `python cocoon.py --mode sphere --headless` | Train without display |
| `python cocoon.py --mode sphere --balls 3 --train` | Multi-ball training |
| `python cocoon.py --mode sphere --misses 5 --train` | Harder difficulty |

**Sphere Arena Flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--balls N` | 1 | Number of balls (1-5) |
| `--misses N` | 10 | Max collective misses before game over |
| `--train` | off | Enable post-snapshot training |
| `--demo` | off | Run with dummy AI for preview |
| `--headless` | off | No display (training only) |
| `--verbose` | off | Verbose debug logging |

---

### 🛸 Drone Warfare Arena (Companion Script)

NASA JSBSim-grade drone combat simulation. **Complete system embedded - extract with --unpack.**

**Setup:** 
```bash
python cocoon.py --unpack ./my_cocoon    # Extracts full drone suite:
#   - cocoon_drone_adapter.py    (main entry point)
#   - cocoon_drone_arena.py      (8-mode arena)
#   - jsbsim_quadcopter.py       (6-DOF physics)
cd my_cocoon
python cocoon_drone_adapter.py           # Run the adapter
```

| Command | Description |
|---------|-------------|
| `python cocoon_drone_adapter.py` | Interactive mode picker |
| `python cocoon_drone_adapter.py --mode free_fly` | Basic flight training |
| `python cocoon_drone_adapter.py --mode tag_battle` | Combat: tag enemies |
| `python cocoon_drone_adapter.py --mode survival` | Last drone flying wins |
| `python cocoon_drone_adapter.py --all` | Run all 8 modes |
| `python cocoon_drone_adapter.py --visual` | 3D visualization (requires PyFlyt) |

**Game Modes:** `free_fly`, `formation`, `pursuit`, `tag_battle`, `zone_control`, `capture_flag`, `survival`, `escort`

**Requirements:** `pip install numpy matplotlib` (PyFlyt optional: `pip install PyFlyt`)

---

### 🎮 Gymnasium Environments

**Built-in (always available):**

| Command | Description |
|---------|-------------|
| `python cocoon.py --mode gym --env CartPole-v1` | Classic pole balancing |
| `python cocoon.py --mode gym --env MountainCar-v0` | Drive up hill |
| `python cocoon.py --mode gym --env Acrobot-v1` | Double pendulum |
| `python cocoon.py --mode gym --env FrozenLake-v1` | Navigate slippery ice |
| `python cocoon.py --mode gym --env Taxi-v3` | Pickup & delivery |
| `python cocoon.py --mode gym --env Blackjack-v1` | Beat the dealer |

**Box2D (`pip install gymnasium[box2d]`):**
- `LunarLander-v3`, `BipedalWalker-v3`, `CarRacing-v3`

**Atari (`pip install ale-py`):**
- `ALE/Pong-v5`, `ALE/Breakout-v5`, `ALE/SpaceInvaders-v5`

**MuJoCo (`pip install gymnasium[mujoco]`):**
- `Ant-v4`, `HalfCheetah-v4`

**Gym Flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--env NAME` | CartPole-v1 | Gymnasium environment name |
| `--episodes N` | 100 | Number of episodes to run |
| `--render` | off | Show visual window |
| `--no-learn` | off | Disable online learning (inference only) |

---

### �️ TrackMania 2020 (TMRL Integration)

Drive TrackMania 2020 with your cocoon organisms using the embedded TMRL adapter!

**Requirements:**
1. TrackMania 2020 (Ubisoft/Epic)
2. OpenPlanet plugin installed (openplanet.dev)
3. TMRL Python package: `pip install tmrl`
4. Extract `cocoon_tmrl_adapter.py` via `--unpack`

**Quick Start:**
```bash
# Extract adapter from cocoon
python cocoon.py --unpack ./my_tmrl

# Run the adapter
python cocoon_tmrl_adapter.py --cocoon path/to/cocoon.py --drive --episodes 4
```

**Important:**
- Play on the **"tmrl-test"** track for proper rewards (search in TrackMania)
- The adapter uses LIDAR observations + speed data
- Ensembles use majority voting for actions

**TMRL Adapter Commands:**

| Flag | Description |
|------|-------------|
| `--drive` | Inference mode (watch it play) |
| `--train` | Learning mode (organisms improve) |
| `--episodes N` | Number of races to run |
| `--organism N` | Use specific organism (0 = ensemble) |

---

### �🌐 HTTP API Server

```bash
python cocoon.py --mode serve --port 8080
```

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check - returns organism count |
| `POST` | `/act` | Get action for state vector |
| `POST` | `/learn` | Add experience + train step |
| `POST` | `/chat` | Chat with learning (returns all organism responses) |
| `POST` | `/teach` | Teach new words/concepts |
| `GET` | `/vocab` | Get current vocabulary |

**Example `/chat` request:**
```bash
curl -X POST http://localhost:8080/chat \\
  -H "Content-Type: application/json" \\
  -d '{{"prompt": "Hello!", "learn": true}}'
```

---

### 🔗 Link Mode (P2P Networking)

Connect to other cocoons for battles and chat.

```bash
python cocoon.py --mode link --hatch ws://server:9000 --name "Champion"
```

**Link Mode Flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--hatch URL` | ws://localhost:9000 | CocoonHatch relay server URL |
| `--name NAME` | auto | Display name |

**In-Link Commands:**

| Command | Description |
|---------|-------------|
| `/users` | List online cocoons |
| `/challenge <name>` | Challenge a user to battle |
| `/accept <id>` | Accept a challenge |
| `/decline <id>` | Decline a challenge |
| `/chat <message>` | Send message to lobby |
| `/quit` | Disconnect |

**Requirements:** `pip install websockets`

---

### 🔬 Export & Conversion

| Command | Description |
|---------|-------------|
| `python cocoon.py --export evolved.py` | Export updated cocoon with learned state |
| `python cocoon.py --export-onnx brain.onnx` | Export to ONNX (all brains as ensemble) |
| `python cocoon.py --export-torchscript brain.pt` | Export to TorchScript (all brains as ensemble) |
| `python cocoon.py --export-onnx brain.onnx --organism 0` | Export single organism to ONNX |
| `python cocoon.py --export-torchscript brain.pt --organism 0` | Export single organism to TorchScript |
| `python cocoon.py --export-package ./my_model` | Export full package (ONNX + README + metadata) |
| `python cocoon.py --unpack ./output_dir` | Unpack ultimate package assets |
| `python cocoon.py --readme` | Print embedded README and exit |

**TorchScript vs ONNX:**
| Format | Continued Learning | Portability | Best For |
|--------|-------------------|-------------|----------|
| `.pt` (TorchScript) | ✅ Yes - can fine-tune | PyTorch/LibTorch/C++ | Research, fine-tuning |
| `.onnx` (ONNX) | ❌ Inference only | Universal (C++, JS, Rust, etc.) | Production deployment |

---

### 📦 Files Created by `--unpack`

Spawns a complete deployment package:

```
output_dir/
├── README.md                # This documentation
├── cocoon_tmrl_adapter.py   # TrackMania 2020 adapter (if embedded)
├── cocoon_drone_adapter.py  # Drone Warfare adapter (if embedded)
├── cocoon_drone_arena.py    # Full 8-mode drone arena (if embedded)
├── jsbsim_quadcopter.py     # NASA JSBSim 6-DOF physics (if embedded)
├── vocabulary.json          # Token vocabulary
├── metadata.json            # Export metadata + organism info
├── requirements.txt         # Python dependencies
├── ensemble.onnx            # ONNX model (all brains unified)
└── ensemble_weights.pt      # PyTorch weights bundle
```

---

### 📦 Files Created by `--export-package`

Netron-viewable package with ONNX models and model card:

```
my_model/
├── brain_ensemble.onnx    # Combined ONNX (all brains unified)
├── brain_*.onnx           # Individual organism ONNX files
├── vocabulary.json        # Token vocabulary
├── metadata.json          # Full configuration + fitness + architecture
└── README.md              # Model card documentation
```

*Note: To get the full cocoon.py + requirements.txt, use `--unpack` instead.*

---

### ⚙️ Global Options

These flags work with any mode:

| Flag | Default | Description |
|------|---------|-------------|
| `--voting MODE` | confidence | Ensemble voting: `majority`, `weighted`, `confidence` |
| `--max-organisms N` | all | Limit organisms loaded (saves VRAM) |
| `--verbose` / `-v` | off | Enable verbose debug logging |
| `--help` | - | Show all available options |

**Examples:**
```bash
python cocoon.py --mode chat --max-organisms 5    # Load only 5 organisms
python cocoon.py --mode gym --voting majority     # Use majority voting
python cocoon.py --mode chat --verbose            # Debug output
```

---

## 📡 API Reference

### CocoonAgent

```python
from cocoon import CocoonAgent

agent = CocoonAgent()

# Get action from state (returns action_idx, {{outputs dict}})
action, outputs = agent.get_action(state_vector)
# outputs = {{'action_probs': [...], 'value': float, 'language_logits': [...], 'vp': float}}

# Process text input (for chat mode)
response = agent.process_input("Hello there!")

# Access subsystems
agent.atomic_lang.get_atoms_by_emotion(min_valence=0.5)  # Get positive atoms
agent.conversation_history.get_summary()  # Get conversation stats
agent.knowledge_web.get_related("concept", min_strength=0.3)  # Get related concepts
agent.vp_runtime.compute_from_state(state)  # Get VP value
```

### HTTP Endpoints (--mode serve)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/infer` | POST | `{{"state": [...]}}` → action |
| `/chat` | POST | `{{"message": "..."}}` → response |
| `/info` | GET | Agent metadata |

---

## 🔧 Dependencies

Minimal requirements:
```
torch>=2.0
numpy
```

Optional for HTTP serving:
```
flask  # or fastapi + uvicorn
```

Optional for Gymnasium:
```
gymnasium
```

---

## 📦 Re-Exporting

The cocoon can re-export its neural models:

```python
from cocoon import CocoonAgent

agent = CocoonAgent()

# Export to ONNX for deployment
agent.export_onnx("brain.onnx")

# Export to TorchScript for C++/LibTorch
agent.export_torchscript("brain.pt")

# Save updated weights after learning
torch.save(agent.brain.state_dict(), "updated_weights.pth")
```

---

## 🦋 About the Butterfly System

This cocoon was generated by the **Butterfly Convergence Engine** - a neuro-symbolic AI framework that combines:

- **Neural networks** for pattern recognition and action selection
- **Atomic language** for grounded semantic understanding
- **VP regulation** (Vigilance × Plasticity) for adaptive attention
- **Knowledge webs** for relational reasoning
- **Distributed ensembles** for robust decision-making

Learn more: [Convergence Engine on GitHub](https://github.com/Yufok1/Convergence_Engine)

---

*Generated by 🦋 Butterfly Agent Compiler*
'''

    def _generate_package_readme(self, organism_names: List[str], brain_configs: List[Dict], metadata: Dict) -> str:
        """Generate README for --export-package (ONNX model card)."""
        num_orgs = len(organism_names)
        mode = "ENSEMBLE" if num_orgs > 1 else "SOLO"
        vocab_size = metadata.get('vocab_size', 0)
        
        org_table = "| # | Organism ID | Input | Hidden | Output | Language | Fitness |\n"
        org_table += "|---|-------------|-------|--------|--------|----------|--------|\n"
        for i, cfg in enumerate(brain_configs):
            org_id = cfg.get('organism_id', '?')[:16]
            has_lang = '✅' if cfg.get('use_language_head') else '❌'
            fitness = cfg.get('fitness', 0)
            fitness_str = f"{fitness:.4f}" if isinstance(fitness, float) else str(fitness)
            org_table += f"| {i+1} | `{org_id}` | {cfg.get('input_dim', 25)} | {cfg.get('hidden_dim', 64)} | {cfg.get('output_dim', 6)} | {has_lang} | {fitness_str} |\n"
        
        return f"""# 🦋 Butterfly Cocoon - ONNX Package

**Generated:** {metadata.get('generated', 'Unknown')}  
**Mode:** {mode} ({num_orgs} organism{"s" if num_orgs > 1 else ""})  
**Vocabulary:** {vocab_size:,} tokens

---

## 📁 Package Contents

| File | Description |
|------|-------------|
| `brain_ensemble.onnx` | Combined ONNX model (all organisms unified) |
| `brain_*.onnx` | Individual organism ONNX files |
| `vocabulary.json` | Token vocabulary |
| `metadata.json` | Full configuration + architecture |
| `README.md` | This file (model card) |

---

## 🧠 Organisms

{org_table}

---

## 🚀 Quick Start

### View Model Architecture

Open any `.onnx` file at [netron.app](https://netron.app/)

### Python Inference (onnxruntime)

```python
import onnxruntime as ort
import numpy as np

# Load model
session = ort.InferenceSession("brain_ensemble.onnx")

# Run inference
state = np.random.randn(1, 25).astype(np.float32)  # 25 dims (base features)
outputs = session.run(None, {{"input": state}})
action_probs = outputs[0]  # Shape: [num_organisms, batch, output_dim]

# Get best action (ensemble average)
avg_probs = action_probs.mean(axis=0)
action = np.argmax(avg_probs, axis=-1)
```

### JavaScript Inference (onnxruntime-web)

```javascript
import * as ort from 'onnxruntime-web';

const session = await ort.InferenceSession.create('brain_ensemble.onnx');
const state = new ort.Tensor('float32', new Float32Array(25), [1, 25]);
const results = await session.run({{ input: state }});
const actionProbs = results.output.data;
```

### C++ Inference (ONNX Runtime)

```cpp
#include <onnxruntime/core/session/onnxruntime_cxx_api.h>

Ort::Session session(env, "brain_ensemble.onnx", session_options);
std::vector<float> input_data(25, 0.0f);
// ... run inference
```

---

## 🔥 Continued Learning

**ONNX is inference-only.** For continued learning, use:

| Format | Learning | How to Get |
|--------|----------|------------|
| `cocoon.py` | ✅ Full | `python cocoon.py --export evolved.py` |
| `.pt` (TorchScript) | ✅ Neural | `python cocoon.py --export-torchscript brain.pt` |
| `.onnx` (this) | ❌ None | Inference only |

---

## 🔬 Architecture

```
Input [{metadata.get('max_input_dim', 25)} dims]
     │
     ├── Brain 1 ──→ Q-values [{metadata.get('max_output_dim', 6)} actions]
     ├── Brain 2 ──→ Q-values
     └── ...
     
Output: Stacked [num_organisms, batch, output_dim]
```

---

## 📡 Deployment Options

| Platform | Runtime | Install |
|----------|---------|---------|
| Python | onnxruntime | `pip install onnxruntime` |
| Python GPU | onnxruntime-gpu | `pip install onnxruntime-gpu` |
| JavaScript | onnxruntime-web | `npm install onnxruntime-web` |
| Node.js | onnxruntime-node | `npm install onnxruntime-node` |
| C++ | ONNX Runtime | [github.com/microsoft/onnxruntime](https://github.com/microsoft/onnxruntime) |
| Rust | ort | `cargo add ort` |

---

## 🔗 Links

- 📊 [Netron Model Viewer](https://netron.app/)
- 🦋 [Convergence Engine](https://github.com/Yufok1/Convergence_Engine)
- 📦 [ONNX Runtime](https://onnxruntime.ai/)

---

*Generated by 🦋 Butterfly Agent Compiler*
"""

    def _generate_torchscript_loader(self) -> str:
        """Generate loader.py that reconstructs full agent from TorchScript package."""
        return '''#!/usr/bin/env python3
"""
🔥 TorchScript Agent Loader - Reconstructs full agent with ALL subsystems

This loader takes the TorchScript package (brain.pt + subsystems.json) and
rebuilds the complete agent with:
  - Neural network (trainable!)
  - AtomicLanguageSystem
  - ConversationHistory
  - EnhancedKnowledgeWeb
  - VPRuntime
  - ExperienceBuffer

Usage:
    from loader import load_agent
    agent = load_agent('.')  # Load from current directory
    action = agent.get_action(state)
"""
import json
import torch
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from collections import deque


@dataclass
class SimpleLinguisticAtom:
    """A simple semantic unit for basic chat (legacy compilation artifact)."""
    concept_id: str
    definition: str = ""
    emotion_valence: float = 0.0
    context_tags: List[str] = field(default_factory=list)
    activation_count: int = 0
    strength: float = 1.0
    
    def activate(self):
        self.activation_count += 1
        self.strength = min(1.0, self.strength + 0.01)


class SimpleAtomicLanguageSystem:
    """Simple semantic atom management (legacy compilation artifact).
    
    Note: For organism innate vocabulary, use AtomicLanguageSystem from
    reality_simulator.language.atomic_language instead.
    """
    
    def __init__(self, state: Dict = None):
        self.atoms: Dict[str, SimpleLinguisticAtom] = {}
        if state:
            for concept_id, atom_data in state.get('atoms', {}).items():
                if isinstance(atom_data, dict):
                    self.atoms[concept_id] = SimpleLinguisticAtom(
                        concept_id=concept_id,
                        definition=atom_data.get('definition', ''),
                        emotion_valence=atom_data.get('emotion_valence', 0.0),
                        context_tags=atom_data.get('context_tags', []),
                        activation_count=atom_data.get('activation_count', 0),
                        strength=atom_data.get('strength', 1.0),
                    )
    
    def create_atom(self, concept_id: str, definition: str = "", emotion: float = 0.0) -> SimpleLinguisticAtom:
        atom = SimpleLinguisticAtom(concept_id=concept_id, definition=definition, emotion_valence=emotion)
        self.atoms[concept_id] = atom
        return atom
    
    def get_atom(self, concept_id: str) -> Optional[SimpleLinguisticAtom]:
        return self.atoms.get(concept_id)
    
    def activate_atom(self, concept_id: str):
        if concept_id in self.atoms:
            self.atoms[concept_id].activate()
    
    def get_atoms_by_emotion(self, min_valence: float = 0.0) -> List[SimpleLinguisticAtom]:
        return [a for a in self.atoms.values() if a.emotion_valence >= min_valence]
    
    def get_state(self) -> Dict:
        return {
            'atoms': {k: {'concept_id': v.concept_id, 'definition': v.definition,
                         'emotion_valence': v.emotion_valence, 'context_tags': v.context_tags,
                         'activation_count': v.activation_count, 'strength': v.strength}
                     for k, v in self.atoms.items()}
        }


class ConversationHistory:
    """Tracks conversation context and topics."""
    
    def __init__(self, state: Dict = None, max_turns: int = 100):
        self.max_turns = max_turns
        self.turns: deque = deque(maxlen=max_turns)
        self.topics: Dict[str, int] = {}
        if state:
            for turn in state.get('turns', []):
                self.turns.append(turn)
            self.topics = state.get('topics', {})
    
    def add_turn(self, role: str, content: str, topics: List[str] = None):
        self.turns.append({'role': role, 'content': content, 'topics': topics or []})
        for topic in (topics or []):
            self.topics[topic] = self.topics.get(topic, 0) + 1
    
    def get_recent(self, n: int = 5) -> List[Dict]:
        return list(self.turns)[-n:]
    
    def get_summary(self) -> Dict:
        return {'total_turns': len(self.turns), 'top_topics': sorted(self.topics.items(), key=lambda x: -x[1])[:10]}
    
    def get_state(self) -> Dict:
        return {'turns': list(self.turns), 'topics': self.topics}


@dataclass
class SemanticRelation:
    source: str
    target: str
    relation_type: str
    strength: float = 1.0


class EnhancedKnowledgeWeb:
    """Semantic knowledge graph with relations."""
    
    def __init__(self, state: Dict = None):
        self.relations: List[SemanticRelation] = []
        if state:
            for rel in state.get('relations', []):
                self.relations.append(SemanticRelation(
                    source=rel.get('source', ''),
                    target=rel.get('target', ''),
                    relation_type=rel.get('relation_type', 'related'),
                    strength=rel.get('strength', 1.0),
                ))
    
    def add_relation(self, source: str, target: str, rel_type: str, strength: float = 1.0):
        self.relations.append(SemanticRelation(source, target, rel_type, strength))
    
    def get_related(self, concept: str, min_strength: float = 0.0) -> List[SemanticRelation]:
        return [r for r in self.relations if (r.source == concept or r.target == concept) and r.strength >= min_strength]
    
    def get_state(self) -> Dict:
        return {'relations': [{'source': r.source, 'target': r.target, 
                               'relation_type': r.relation_type, 'strength': r.strength} 
                             for r in self.relations]}


class VPRuntime:
    """
    Vigilance × Plasticity self-regulation system.
    
    UNIFIED IMPLEMENTATION - Matches cocoon's VP calculation exactly.
    
    VP Classification:
        VP0: 0.00-0.25 (Fully lawful - optimal operation)
        VP1: 0.25-0.50 (Stable drift - continue with logging)
        VP2: 0.50-0.75 (Instability - needs attention)
        VP3: 0.75-0.99 (Critical - intervention needed)
        VP4: >= 1.00 (Collapse threshold)
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.smoothing_factor = config.get('smoothing_factor', 0.3)
        self.history_size = config.get('history_size', 20)
        self.vp_history: deque = deque(maxlen=self.history_size)
        self.last_vp = config.get('last_vp', 0.0)
        self.vitality = config.get('vitality', 0.5)
        self.pleasure = config.get('pleasure', 0.5)
        
        # Component weights for VP calculation (same as cocoon)
        self.component_weights = config.get('component_weights', {
            'resource_deficit': 0.25,    # Low energy/resources
            'social_isolation': 0.20,    # Few connections
            'action_conflict': 0.20,     # Competing action signals
            'learning_stagnation': 0.15, # Low reward variance
            'entropy_excess': 0.20       # High uncertainty
        })
        
        # Restore history if provided
        for vp in config.get('vp_history', []):
            self.vp_history.append(vp)
    
    def compute_from_state(self, state, reward_history: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Compute VP components from organism state vector.
        
        State vector mapping (25-dim base features):
            0-5: Action probabilities
            6-8: Resource levels (energy, fitness, age)
            9-11: Social signals (cooperation, competition, isolation)
            12-14: Environmental context
            15-24: Additional features + illumination
            
            (Optional 25-27: Self-perception features when enabled)
        
        Returns dict with: vitality, pleasure, violation_pressure, vp_class, components
        """
        import numpy as np
        
        # Convert to numpy array
        if hasattr(state, 'numpy'):
            state = state.numpy()
        if hasattr(state, 'flatten'):
            state = state.flatten()
        state = np.array(state) if not isinstance(state, np.ndarray) else state
        
        components = {}
        
        # 1. Resource deficit: low values in resource positions
        if len(state) > 8:
            resource_signals = state[6:9]  # Energy, fitness, age-normalized
            resource_deficit = max(0, 1.0 - np.mean(resource_signals))
            components['resource_deficit'] = float(resource_deficit)
        else:
            components['resource_deficit'] = 0.3
        
        # 2. Social isolation: low cooperation, high isolation signals
        if len(state) > 11:
            cooperation = state[9] if len(state) > 9 else 0.5
            isolation = state[11] if len(state) > 11 else 0.5
            social_isolation = max(0, isolation - cooperation + 0.5)
            components['social_isolation'] = float(np.clip(social_isolation, 0, 1))
        else:
            components['social_isolation'] = 0.3
        
        # 3. Action conflict: entropy of action probabilities
        if len(state) > 5:
            action_probs = state[0:6]
            action_probs = np.abs(action_probs) / (np.sum(np.abs(action_probs)) + 1e-9)
            entropy = -np.sum(action_probs * np.log(action_probs + 1e-9))
            max_entropy = np.log(6)  # 6 actions
            components['action_conflict'] = float(np.clip(entropy / max_entropy, 0, 1))
        else:
            components['action_conflict'] = 0.3
        
        # 4. Learning stagnation: low variance in recent rewards
        if reward_history and len(reward_history) > 3:
            reward_std = np.std(reward_history[-10:])
            stagnation = max(0, 1.0 - reward_std * 5)  # Low variance = high stagnation
            components['learning_stagnation'] = float(np.clip(stagnation, 0, 1))
        else:
            components['learning_stagnation'] = 0.3
        
        # 5. Entropy excess: general state entropy
        state_normalized = np.abs(state) / (np.sum(np.abs(state)) + 1e-9)
        state_entropy = -np.sum(state_normalized * np.log(state_normalized + 1e-9))
        max_state_entropy = np.log(len(state)) if len(state) > 0 else 1.0
        components['entropy_excess'] = float(np.clip(state_entropy / max_state_entropy, 0, 1))
        
        # Combine components using weighted sum
        raw_vp = sum(components.get(k, 0.3) * self.component_weights.get(k, 0.2) for k in self.component_weights)
        
        # Apply smoothing
        smoothed_vp = self.smoothing_factor * raw_vp + (1 - self.smoothing_factor) * self.last_vp
        smoothed_vp = float(np.clip(smoothed_vp, 0, 1))
        self.last_vp = smoothed_vp
        self.vp_history.append(smoothed_vp)
        
        # Derive vitality and pleasure from components
        self.vitality = 1.0 - (components['resource_deficit'] * 0.6 + components['learning_stagnation'] * 0.4)
        self.pleasure = 1.0 - (components['social_isolation'] * 0.5 + components['action_conflict'] * 0.5)
        
        # Classify VP
        if smoothed_vp < 0.25:
            vp_class = 'VP0'
        elif smoothed_vp < 0.50:
            vp_class = 'VP1'
        elif smoothed_vp < 0.75:
            vp_class = 'VP2'
        elif smoothed_vp < 1.00:
            vp_class = 'VP3'
        else:
            vp_class = 'VP4'
        
        return {
            'vitality': float(self.vitality),
            'pleasure': float(self.pleasure),
            'violation_pressure': smoothed_vp,
            'vp_class': vp_class,
            'components': components,
            'history_mean': float(np.mean(list(self.vp_history))) if self.vp_history else smoothed_vp
        }
    
    def get_vp_value(self) -> float:
        """Get current VP value for attention scaling."""
        return self.last_vp
    
    def get_vp_state(self) -> tuple:
        """Get (vitality, pleasure) tuple for concept activation."""
        return (self.vitality, self.pleasure)
    
    def get_state(self) -> Dict:
        """Get full state for serialization."""
        return {
            'smoothing_factor': self.smoothing_factor,
            'history_size': self.history_size,
            'vp_history': list(self.vp_history),
            'last_vp': self.last_vp,
            'vitality': self.vitality,
            'pleasure': self.pleasure,
            'component_weights': self.component_weights
        }
    
    def reset(self):
        """Reset VP runtime state."""
        self.vp_history.clear()
        self.last_vp = 0.0
        self.vitality = 0.5
        self.pleasure = 0.5


class ExperienceBuffer:
    """Replay buffer for continued learning - UNLIMITED by default."""
    
    def __init__(self, config: Dict = None):
        config = config or {}
        # max_size of 0 or None = unlimited (no cap on experiences)
        raw_max = config.get('max_size', 0)
        self.max_size = raw_max if raw_max and raw_max > 0 else None  # None = unlimited
        self.gamma = config.get('gamma', 0.995)  # Default matches config.json
        self.buffer: deque = deque(maxlen=self.max_size)  # maxlen=None = unlimited
        for entry in config.get('entries', []):
            self.buffer.append(entry)
    
    @staticmethod
    def format_count(count: int) -> str:
        """Format experience count for display (shorthand for large numbers)."""
        if count >= 1_000_000_000:
            return f"{count / 1_000_000_000:.1f}B"
        elif count >= 1_000_000:
            return f"{count / 1_000_000:.1f}M"
        elif count >= 1_000:
            return f"{count / 1_000:.1f}K"
        return str(count)
    
    def add(self, state, action, reward, next_state=None, done=False):
        self.buffer.append({'state': state, 'action': action, 'reward': reward, 
                           'next_state': next_state, 'done': done})
    
    def sample(self, batch_size: int = 32) -> List[Dict]:
        import random
        return random.sample(list(self.buffer), min(batch_size, len(self.buffer)))
    
    def __len__(self):
        return len(self.buffer)


class TorchScriptAgent:
    """Complete agent reconstructed from TorchScript package."""
    
    def __init__(self, package_dir: str):
        package_dir = Path(package_dir)
        
        # Load neural model
        self.brain = torch.jit.load(package_dir / 'brain.pt')
        self.brain.eval()
        
        # Load subsystems
        with open(package_dir / 'subsystems.json') as f:
            subsystems = json.load(f)
        
        self.atomic_lang = AtomicLanguageSystem(subsystems.get('atomic_language', {}))
        self.conversation_history = ConversationHistory(subsystems.get('conversation_history', {}))
        self.knowledge_web = EnhancedKnowledgeWeb(subsystems.get('knowledge_web', {}))
        self.vp_runtime = VPRuntime(subsystems.get('vp_config', {}))
        self.experience_buffer = ExperienceBuffer(subsystems.get('experience_buffer', {}))
        self.alliance_system = subsystems.get('alliance_system', {})  # Social structure for voting
        
        # Load vocabulary
        with open(package_dir / 'vocabulary.json') as f:
            self.vocabulary = json.load(f)
        
        # Load metadata
        with open(package_dir / 'metadata.json') as f:
            self.metadata = json.load(f)
    
    def get_action(self, state) -> tuple:
        """Get action from state, updating VP and storing experience."""
        if not isinstance(state, torch.Tensor):
            state = torch.tensor(state, dtype=torch.float32)
        if state.dim() == 1:
            state = state.unsqueeze(0)
        
        # Compute VP for attention scaling (now returns rich dict)
        vp_result = self.vp_runtime.compute_from_state(state)
        vp_value = vp_result['violation_pressure']
        
        with torch.no_grad():
            outputs = self.brain(state)
        
        if isinstance(outputs, tuple):
            action_probs = outputs[0]
            language_logits = outputs[1] if len(outputs) > 1 else None
        else:
            action_probs = outputs
            language_logits = None
        
        # Scale by VP (higher VP = more cautious/conservative)
        action_probs = action_probs / (1.0 + vp_value)
        action = torch.argmax(action_probs, dim=-1).item()
        
        return action, {
            'action_probs': action_probs.squeeze().tolist(),
            'language_logits': language_logits.squeeze().tolist() if language_logits is not None else None,
            'vp': vp_result,
        }
    
    def train_step(self, states, targets, optimizer):
        """Perform a training step - YES, TorchScript CAN learn!"""
        self.brain.train()
        optimizer.zero_grad()
        outputs = self.brain(states)
        action_probs = outputs[0] if isinstance(outputs, tuple) else outputs
        loss = torch.nn.functional.cross_entropy(action_probs, targets)
        loss.backward()
        optimizer.step()
        self.brain.eval()
        return loss.item()
    
    def save(self, package_dir: str):
        """Save updated agent back to package."""
        package_dir = Path(package_dir)
        package_dir.mkdir(exist_ok=True)
        
        # Save neural model
        torch.jit.save(self.brain, package_dir / 'brain.pt')
        
        # Save subsystems with full state preservation
        subsystems = {
            'atomic_language': self.atomic_lang.get_state(),
            'conversation_history': self.conversation_history.get_state(),
            'knowledge_web': self.knowledge_web.get_state(),
            'vp_config': self.vp_runtime.get_state(),  # Full VP state with history!
            'alliance_system': self.alliance_system,  # Preserve social structure
            'experience_buffer': {
                'max_size': self.experience_buffer.max_size,
                'gamma': self.experience_buffer.gamma,
                'entries': list(self.experience_buffer.buffer)[-1000:],  # Save last 1000
            },
        }
        with open(package_dir / 'subsystems.json', 'w') as f:
            json.dump(subsystems, f, indent=2, default=str)


def load_agent(package_dir: str = '.') -> TorchScriptAgent:
    """Load agent from TorchScript package directory."""
    return TorchScriptAgent(package_dir)


if __name__ == '__main__':
    import sys
    agent = load_agent(sys.argv[1] if len(sys.argv) > 1 else '.')
    print(f"Loaded agent: {agent.metadata.get('organism_id', 'unknown')}")
    print(f"Subsystems: {agent.metadata.get('subsystems_included', [])}")
    print(f"Atoms: {len(agent.atomic_lang.atoms)}")
    print(f"Relations: {len(agent.knowledge_web.relations)}")
    exp_count = len(agent.experience_buffer)
    print(f"Experience buffer: {ExperienceBuffer.format_count(exp_count)} entries ({exp_count:,} total)")
'''

    def _generate_torchscript_readme(self, metadata: Dict) -> str:
        """Generate README for TorchScript package."""
        return f'''# 🔥 TorchScript Agent Package

**Generated:** {metadata.get('generated', 'Unknown')}
**Organism:** {metadata.get('organism_id', 'Unknown')}
**Format Version:** {metadata.get('format_version', '2.0')}

## 📁 Contents

| File | Description |
|------|-------------|
| `brain.pt` | TorchScript neural network (TRAINABLE!) |
| `subsystems.json` | AtomicLanguageSystem, KnowledgeWeb, ConversationHistory, VP config |
| `vocabulary.json` | Token vocabulary |
| `metadata.json` | Configuration and architecture info |
| `loader.py` | Python script to reconstruct full agent |
| `README.md` | This file |

## ✅ Included Subsystems

{chr(10).join(f"- {s}" for s in metadata.get('subsystems_included', []))}

## 🔥 Continued Learning

**YES! This package supports continued learning!**

```python
from loader import load_agent
import torch

# Load the complete agent
agent = load_agent('.')

# The agent learns like normal
action, outputs = agent.get_action(state)

# Fine-tune the neural network
optimizer = torch.optim.Adam(agent.brain.parameters(), lr=1e-4)
loss = agent.train_step(states_batch, targets_batch, optimizer)

# Grow the symbolic systems
agent.atomic_lang.create_atom("new_concept", "learned from experience", emotion=0.7)
agent.knowledge_web.add_relation("concept_a", "concept_b", "causes", strength=0.9)
agent.experience_buffer.add(state, action, reward)

# Save everything back
agent.save('updated_agent/')
```

## 🚀 Quick Start

```python
from loader import load_agent

# Load agent
agent = load_agent('.')

# Get action
state = [1.0, 0.5, -0.3, 0.2, ...]  # Your state vector
action, outputs = agent.get_action(state)

print(f"Action: {{action}}")
print(f"VP: {{outputs['vp']:.3f}}")
```

## 🔗 Links

- [Convergence Engine](https://github.com/Yufok1/Convergence_Engine)
- View brain.pt at [Netron](https://netron.app/)
'''

    def _generate_onnx_loader(self) -> str:
        """Generate loader.py for ONNX package with all subsystems."""
        return '''#!/usr/bin/env python3
"""
🌐 ONNX Agent Loader - Fast inference with ALL symbolic subsystems

The ONNX neural network is inference-only (no gradient updates), but the
symbolic subsystems CAN continue learning and growing:
  - AtomicLanguageSystem - create new atoms
  - ConversationHistory - accumulate context
  - EnhancedKnowledgeWeb - add relations
  - VPRuntime - adapts from state
  - ExperienceBuffer - stores experiences (for later training)

Usage:
    from loader import load_agent
    agent = load_agent('.')
    action = agent.get_action(state)
"""
import json
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import deque

try:
    import onnxruntime as ort
except ImportError:
    print("Install onnxruntime: pip install onnxruntime")
    raise


@dataclass
class LinguisticAtomONNX:
    """Lightweight atom for ONNX runtime (legacy compilation artifact)."""
    concept_id: str
    definition: str = ""
    emotion_valence: float = 0.0
    context_tags: List[str] = field(default_factory=list)
    activation_count: int = 0
    strength: float = 1.0
    
    def activate(self):
        self.activation_count += 1
        self.strength = min(1.0, self.strength + 0.01)


class AtomicLanguageSystemONNX:
    """ONNX-compatible atom system (legacy compilation artifact).
    
    Note: For organism innate vocabulary, use AtomicLanguageSystem from
    reality_simulator.language.atomic_language instead.
    """
    def __init__(self, state: Dict = None):
        self.atoms: Dict[str, LinguisticAtomONNX] = {}
        if state:
            for cid, data in state.get('atoms', {}).items():
                if isinstance(data, dict):
                    self.atoms[cid] = LinguisticAtomONNX(
                        concept_id=cid, definition=data.get('definition', ''),
                        emotion_valence=data.get('emotion_valence', 0.0),
                        context_tags=data.get('context_tags', []),
                        activation_count=data.get('activation_count', 0),
                        strength=data.get('strength', 1.0))
    
    def create_atom(self, concept_id: str, definition: str = "", emotion: float = 0.0):
        self.atoms[concept_id] = LinguisticAtomONNX(concept_id, definition, emotion)
        return self.atoms[concept_id]
    
    def get_state(self) -> Dict:
        return {'atoms': {k: {'concept_id': v.concept_id, 'definition': v.definition,
                             'emotion_valence': v.emotion_valence, 'strength': v.strength}
                         for k, v in self.atoms.items()}}


class ConversationHistory:
    def __init__(self, state: Dict = None, max_turns: int = 100):
        self.turns = deque(maxlen=max_turns)
        self.topics = {}
        if state:
            for turn in state.get('turns', []): self.turns.append(turn)
            self.topics = state.get('topics', {})
    
    def add_turn(self, role: str, content: str, topics: List[str] = None):
        self.turns.append({'role': role, 'content': content})
        for t in (topics or []): self.topics[t] = self.topics.get(t, 0) + 1
    
    def get_state(self) -> Dict:
        return {'turns': list(self.turns), 'topics': self.topics}


@dataclass
class SemanticRelation:
    source: str
    target: str
    relation_type: str
    strength: float = 1.0


class EnhancedKnowledgeWeb:
    def __init__(self, state: Dict = None):
        self.relations = []
        if state:
            for r in state.get('relations', []):
                self.relations.append(SemanticRelation(r['source'], r['target'], r['relation_type'], r.get('strength', 1.0)))
    
    def add_relation(self, source: str, target: str, rel_type: str, strength: float = 1.0):
        self.relations.append(SemanticRelation(source, target, rel_type, strength))
    
    def get_state(self) -> Dict:
        return {'relations': [{'source': r.source, 'target': r.target, 'relation_type': r.relation_type, 'strength': r.strength} for r in self.relations]}


class VPRuntime:
    """
    Vigilance × Plasticity self-regulation system.
    UNIFIED IMPLEMENTATION - Matches cocoon and TorchScript loader.
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.smoothing_factor = config.get('smoothing_factor', 0.3)
        self.history_size = config.get('history_size', 20)
        self.vp_history = deque(maxlen=self.history_size)
        self.last_vp = config.get('last_vp', 0.0)
        self.vitality = config.get('vitality', 0.5)
        self.pleasure = config.get('pleasure', 0.5)
        self.component_weights = config.get('component_weights', {
            'resource_deficit': 0.25, 'social_isolation': 0.20,
            'action_conflict': 0.20, 'learning_stagnation': 0.15, 'entropy_excess': 0.20
        })
        for vp in config.get('vp_history', []): self.vp_history.append(vp)
    
    def compute_from_state(self, state, reward_history: List[float] = None) -> Dict:
        state = np.array(state).flatten() if hasattr(state, 'flatten') else np.array(state)
        components = {}
        
        # 1. Resource deficit
        if len(state) > 8:
            components['resource_deficit'] = float(max(0, 1.0 - np.mean(state[6:9])))
        else:
            components['resource_deficit'] = 0.3
        
        # 2. Social isolation
        if len(state) > 11:
            components['social_isolation'] = float(np.clip(max(0, state[11] - state[9] + 0.5), 0, 1))
        else:
            components['social_isolation'] = 0.3
        
        # 3. Action conflict (entropy)
        if len(state) > 5:
            ap = np.abs(state[0:6]) / (np.sum(np.abs(state[0:6])) + 1e-9)
            entropy = -np.sum(ap * np.log(ap + 1e-9))
            components['action_conflict'] = float(np.clip(entropy / np.log(6), 0, 1))
        else:
            components['action_conflict'] = 0.3
        
        # 4. Learning stagnation
        if reward_history and len(reward_history) > 3:
            components['learning_stagnation'] = float(np.clip(max(0, 1.0 - np.std(reward_history[-10:]) * 5), 0, 1))
        else:
            components['learning_stagnation'] = 0.3
        
        # 5. Entropy excess
        sn = np.abs(state) / (np.sum(np.abs(state)) + 1e-9)
        se = -np.sum(sn * np.log(sn + 1e-9))
        components['entropy_excess'] = float(np.clip(se / max(np.log(len(state)), 1.0), 0, 1))
        
        raw_vp = sum(components.get(k, 0.3) * self.component_weights.get(k, 0.2) for k in self.component_weights)
        smoothed_vp = float(np.clip(self.smoothing_factor * raw_vp + (1 - self.smoothing_factor) * self.last_vp, 0, 1))
        self.last_vp = smoothed_vp
        self.vp_history.append(smoothed_vp)
        self.vitality = 1.0 - (components['resource_deficit'] * 0.6 + components['learning_stagnation'] * 0.4)
        self.pleasure = 1.0 - (components['social_isolation'] * 0.5 + components['action_conflict'] * 0.5)
        
        vp_class = 'VP0' if smoothed_vp < 0.25 else 'VP1' if smoothed_vp < 0.5 else 'VP2' if smoothed_vp < 0.75 else 'VP3' if smoothed_vp < 1 else 'VP4'
        return {'vitality': self.vitality, 'pleasure': self.pleasure, 'violation_pressure': smoothed_vp,
                'vp_class': vp_class, 'components': components}
    
    def get_vp_value(self) -> float: return self.last_vp
    def get_state(self) -> Dict:
        return {'smoothing_factor': self.smoothing_factor, 'history_size': self.history_size,
                'vp_history': list(self.vp_history), 'last_vp': self.last_vp,
                'vitality': self.vitality, 'pleasure': self.pleasure, 'component_weights': self.component_weights}


class ExperienceBuffer:
    def __init__(self, config: Dict = None):
        config = config or {}
        self.buffer = deque(maxlen=config.get('max_size', 10000))
        for e in config.get('entries', []): self.buffer.append(e)
    
    def add(self, state, action, reward, next_state=None, done=False):
        self.buffer.append({'state': list(state) if hasattr(state, 'tolist') else state,
                           'action': action, 'reward': reward})
    
    def __len__(self): return len(self.buffer)


class ONNXAgent:
    """Complete agent with ONNX inference + all symbolic subsystems."""
    
    def __init__(self, package_dir: str):
        package_dir = Path(package_dir)
        
        # Load ONNX model
        self.session = ort.InferenceSession(str(package_dir / 'brain.onnx'))
        self.input_name = self.session.get_inputs()[0].name
        
        # Load subsystems
        with open(package_dir / 'subsystems.json') as f:
            subsystems = json.load(f)
        
        self.atomic_lang = AtomicLanguageSystem(subsystems.get('atomic_language', {}))
        self.conversation_history = ConversationHistory(subsystems.get('conversation_history', {}))
        self.knowledge_web = EnhancedKnowledgeWeb(subsystems.get('knowledge_web', {}))
        self.vp_runtime = VPRuntime(subsystems.get('vp_config', {}))
        self.experience_buffer = ExperienceBuffer(subsystems.get('experience_buffer', {}))
        self.alliance_system = subsystems.get('alliance_system', {})  # Social structure for voting
        
        with open(package_dir / 'vocabulary.json') as f:
            self.vocabulary = json.load(f)
        with open(package_dir / 'metadata.json') as f:
            self.metadata = json.load(f)
    
    def get_action(self, state) -> tuple:
        state = np.array(state, dtype=np.float32).reshape(1, -1)
        vp_result = self.vp_runtime.compute_from_state(state)
        vp_value = vp_result['violation_pressure']
        
        outputs = self.session.run(None, {self.input_name: state})
        action_probs = outputs[0][0]
        # Scale by VP (higher VP = more cautious, matches cocoon attention scaling)
        action_probs = action_probs / (1.0 + vp_value)
        action = int(np.argmax(action_probs))
        
        return action, {
            'action_probs': action_probs.tolist(),
            'language_logits': outputs[1][0].tolist() if len(outputs) > 1 else None,
            'vp': vp_result,  # Full VP dict with components
        }
    
    def save(self, package_dir: str):
        """Save updated symbolic subsystems (ONNX model is read-only)."""
        package_dir = Path(package_dir)
        package_dir.mkdir(exist_ok=True)
        
        import shutil
        # Copy ONNX (can't modify it)
        shutil.copy(Path('.') / 'brain.onnx', package_dir / 'brain.onnx')
        
        # Save updated subsystems with full VP state
        subsystems = {
            'atomic_language': self.atomic_lang.get_state(),
            'conversation_history': self.conversation_history.get_state(),
            'knowledge_web': self.knowledge_web.get_state(),
            'vp_config': self.vp_runtime.get_state(),  # Full VP with history!
            'alliance_system': self.alliance_system,  # Preserve social structure
            'experience_buffer': {'entries': list(self.experience_buffer.buffer)[-1000:]},
        }
        with open(package_dir / 'subsystems.json', 'w') as f:
            json.dump(subsystems, f, indent=2, default=str)


def load_agent(package_dir: str = '.') -> ONNXAgent:
    return ONNXAgent(package_dir)


if __name__ == '__main__':
    import sys
    agent = load_agent(sys.argv[1] if len(sys.argv) > 1 else '.')
    print(f"Loaded ONNX agent: {agent.metadata.get('organism_id', 'unknown')}")
    print(f"Subsystems: {agent.metadata.get('subsystems_included', [])}")
'''

    def _generate_onnx_readme(self, metadata: Dict) -> str:
        """Generate README for ONNX package."""
        return f'''# 🌐 ONNX Agent Package

**Generated:** {metadata.get('generated', 'Unknown')}
**Organism:** {metadata.get('organism_id', 'Unknown')}

## 📁 Contents

| File | Description |
|------|-------------|
| `brain.onnx` | ONNX neural network (fast inference, view at netron.app) |
| `subsystems.json` | AtomicLanguageSystem, KnowledgeWeb, ConversationHistory, VP config |
| `vocabulary.json` | Token vocabulary |
| `metadata.json` | Configuration |
| `loader.py` | Python loader for complete agent |

## ⚠️ Learning Capabilities

| Component | Can Learn? | Notes |
|-----------|------------|-------|
| Neural Network (brain.onnx) | ❌ No | ONNX is inference-only |
| AtomicLanguageSystem | ✅ Yes | Create new atoms, reinforce existing |
| ConversationHistory | ✅ Yes | Grows with each conversation |
| EnhancedKnowledgeWeb | ✅ Yes | Add new relations |
| VPRuntime | ✅ Yes | Adapts from state |
| ExperienceBuffer | ✅ Yes | Stores experiences for later training |

**To retrain the neural network:** Export experiences, train in PyTorch, re-export to ONNX.

## 🚀 Quick Start

```python
from loader import load_agent

agent = load_agent('.')
action, outputs = agent.get_action(state)

# Symbolic systems CAN learn
agent.atomic_lang.create_atom("new_concept", "learned meaning", emotion=0.8)
agent.knowledge_web.add_relation("a", "b", "causes", strength=0.9)
agent.save('updated_agent/')
```

## 🔗 Links

- View brain.onnx at [Netron](https://netron.app/)
- [Convergence Engine](https://github.com/Yufok1/Convergence_Engine)
'''

    def _generate_bridge_script(self, brain_configs: List[Dict], is_ensemble: bool) -> str:
        """Generate the universal bridge.py runner script."""
        return '''#!/usr/bin/env python3
"""
🌉 BUTTERFLY BRIDGE - Universal Agent Runner
Supports: ONNX, TorchScript, Interactive, HTTP, Gymnasium
"""
import argparse
import json
import sys
from pathlib import Path

def load_model(model_path: str):
    """Load either ONNX or TorchScript model."""
    model_path = Path(model_path)
    
    if model_path.suffix == '.onnx':
        import onnxruntime as ort
        return ort.InferenceSession(str(model_path)), 'onnx'
    elif model_path.suffix == '.pt':
        import torch
        return torch.jit.load(str(model_path)), 'torchscript'
    else:
        raise ValueError(f"Unknown model format: {model_path.suffix}")

def run_inference(model, model_type: str, state):
    """Run inference on model."""
    import numpy as np
    state = np.array(state, dtype=np.float32).reshape(1, -1)
    
    if model_type == 'onnx':
        input_name = model.get_inputs()[0].name
        outputs = model.run(None, {input_name: state})
        return outputs
    else:  # torchscript
        import torch
        with torch.no_grad():
            state_t = torch.from_numpy(state)
            outputs = model(state_t)
            if isinstance(outputs, torch.Tensor):
                return [outputs.numpy()]
            return [o.numpy() for o in outputs]

def interactive_mode(model, model_type: str, metadata: dict):
    """Interactive chat/command mode."""
    print("\\n🦋 Butterfly Ensemble Interactive Mode")
    print("=" * 50)
    print(f"Model: {model_type.upper()}")
    print(f"Organisms: {metadata.get('num_organisms', '?')}")
    print("\\nCommands: /state <values>, /quit")
    print("=" * 50)
    
    import numpy as np
    max_dim = metadata.get('max_input_dim', 25)
    
    while True:
        try:
            cmd = input("\\n> ").strip()
            if cmd.lower() in ('/quit', '/exit', 'quit', 'exit'):
                break
            elif cmd.startswith('/state '):
                values = [float(x) for x in cmd[7:].split()]
                # Pad to max_dim
                if len(values) < max_dim:
                    values.extend([0.0] * (max_dim - len(values)))
                outputs = run_inference(model, model_type, values[:max_dim])
                print(f"Outputs: {len(outputs)} tensors")
                for i, out in enumerate(outputs):
                    print(f"  [{i}] shape={out.shape}, argmax={np.argmax(out)}")
            else:
                # Generate random state for demo
                state = np.random.randn(max_dim).astype(np.float32)
                outputs = run_inference(model, model_type, state)
                actions = [np.argmax(out) for out in outputs]
                print(f"Random state -> Actions: {actions}")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("\\nGoodbye! 🦋")

def http_mode(model, model_type: str, metadata: dict, port: int):
    """Start HTTP API server."""
    from flask import Flask, request, jsonify
    import numpy as np
    
    app = Flask(__name__)
    
    @app.route('/predict', methods=['POST'])
    def predict():
        data = request.get_json()
        state = data.get('state', [0.0] * metadata.get('max_input_dim', 25))
        outputs = run_inference(model, model_type, state)
        return jsonify({
            'outputs': [out.tolist() for out in outputs],
            'actions': [int(np.argmax(out)) for out in outputs]
        })
    
    @app.route('/metadata')
    def get_metadata():
        return jsonify(metadata)
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok', 'model_type': model_type})
    
    print(f"\\n🌐 Starting HTTP server on port {port}")
    print(f"   POST /predict - Run inference")
    print(f"   GET /metadata - Get model info")
    app.run(host='0.0.0.0', port=port)

def gym_mode(model, model_type: str, metadata: dict, env_name: str, episodes: int, render: bool):
    """Run in Gymnasium or PLE environment."""
    import numpy as np
    
    max_dim = metadata.get('max_input_dim', 25)
    
    # Check if this is a PLE game
    if '-PLE-' in env_name:
        try:
            run_ple_game(model, model_type, metadata, env_name, episodes, render)
            return
        except ImportError as e:
            print(f"\\n⚠️  PLE not installed. Install with: pip install ple")
            print(f"   Or try: pip install gym-ple")
            print(f"   Error: {e}")
            return
        except Exception as e:
            print(f"\\n❌ PLE error: {e}")
            return
    
    # Standard Gymnasium
    import gymnasium as gym
    env = gym.make(env_name, render_mode='human' if render else None)
    
    print(f"\\n🎮 Running {env_name} for {episodes} episodes")
    
    for ep in range(episodes):
        state, _ = env.reset()
        # Pad/truncate state
        state = np.array(state, dtype=np.float32)
        if len(state) < max_dim:
            state = np.concatenate([state, np.zeros(max_dim - len(state))])
        elif len(state) > max_dim:
            state = state[:max_dim]
        
        total_reward = 0
        done = False
        steps = 0
        
        while not done:
            outputs = run_inference(model, model_type, state)
            # Use first output (or majority vote could be implemented)
            action = int(np.argmax(outputs[0]))
            # Clamp to valid action space
            action = min(action, env.action_space.n - 1)
            
            state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            total_reward += reward
            steps += 1
            
            # Pad state for next iteration
            state = np.array(state, dtype=np.float32)
            if len(state) < max_dim:
                state = np.concatenate([state, np.zeros(max_dim - len(state))])
            elif len(state) > max_dim:
                state = state[:max_dim]
        
        print(f"  Episode {ep+1}: {steps} steps, reward={total_reward:.2f}")
    
    env.close()
    print("\\nDone! 🦋")


def run_ple_game(model, model_type: str, metadata: dict, env_name: str, episodes: int, render: bool):
    """Run a PyGame Learning Environment game."""
    import numpy as np
    
    # Parse game name from env_name (e.g., "FlappyBird-PLE-v0" -> "FlappyBird")
    game_name = env_name.split('-PLE-')[0]
    
    # Import PLE
    from ple import PLE
    from ple.games import flappybird, pong, snake, pixelcopter, catcher, puckworld, waterworld, monsterkong, raycastmaze
    
    # Game mapping
    GAMES = {
        'FlappyBird': flappybird.FlappyBird,
        'Pong': pong.Pong,
        'Snake': snake.Snake,
        'Pixelcopter': pixelcopter.Pixelcopter,
        'Catcher': catcher.Catcher,
        'PuckWorld': puckworld.PuckWorld,
        'WaterWorld': waterworld.WaterWorld,
        'MonsterKong': monsterkong.MonsterKong,
        'RaycastMaze': raycastmaze.RaycastMaze,
    }
    
    if game_name not in GAMES:
        print(f"❌ Unknown PLE game: {game_name}")
        print(f"   Available: {list(GAMES.keys())}")
        return
    
    # Create game instance
    game = GAMES[game_name]()
    
    # Create PLE environment
    p = PLE(game, fps=30, display_screen=render, force_fps=not render)
    p.init()
    
    max_dim = metadata.get('max_input_dim', 25)
    action_set = p.getActionSet()
    
    print(f"\\n🕹️  Running {game_name} (PLE) for {episodes} episodes")
    print(f"   Actions: {action_set}")
    
    for ep in range(episodes):
        p.reset_game()
        total_reward = 0
        steps = 0
        
        while not p.game_over():
            # Get state as dict and flatten to array
            state_dict = game.getGameState()
            if isinstance(state_dict, dict):
                state = np.array(list(state_dict.values()), dtype=np.float32)
            else:
                state = np.array(state_dict, dtype=np.float32).flatten()
            
            # Pad/truncate
            if len(state) < max_dim:
                state = np.concatenate([state, np.zeros(max_dim - len(state))])
            elif len(state) > max_dim:
                state = state[:max_dim]
            
            # Get action from model
            outputs = run_inference(model, model_type, state)
            action_idx = int(np.argmax(outputs[0])) % len(action_set)
            action = action_set[action_idx]
            
            # Step
            reward = p.act(action)
            total_reward += reward
            steps += 1
        
        print(f"  Episode {ep+1}: {steps} steps, reward={total_reward:.2f}")
    
    print("\\nDone! 🦋")

def main():
    parser = argparse.ArgumentParser(description='🦋 Butterfly Bridge - Universal Agent Runner')
    parser.add_argument('--model', '-m', default='brain_ensemble.onnx', help='Model file (.onnx or .pt)')
    parser.add_argument('--mode', choices=['interactive', 'http', 'gym'], default='interactive')
    parser.add_argument('--port', type=int, default=8080, help='HTTP server port')
    parser.add_argument('--env', '-e', default='CartPole-v1', help='Gymnasium environment')
    parser.add_argument('--episodes', '-n', type=int, default=5, help='Number of episodes')
    parser.add_argument('--render', '-r', action='store_true', help='Render environment')
    args = parser.parse_args()
    
    # Load metadata
    metadata = {}
    if Path('metadata.json').exists():
        with open('metadata.json') as f:
            metadata = json.load(f)
    
    # Load model
    print(f"Loading {args.model}...")
    model, model_type = load_model(args.model)
    print(f"✅ Loaded {model_type.upper()} model")
    
    if args.mode == 'interactive':
        interactive_mode(model, model_type, metadata)
    elif args.mode == 'http':
        http_mode(model, model_type, metadata, args.port)
    elif args.mode == 'gym':
        gym_mode(model, model_type, metadata, args.env, args.episodes, args.render)

if __name__ == '__main__':
    main()
'''

    def _generate_ultimate_readme(self, organism_names: List[str], brain_configs: List[Dict], 
                                   metadata: Dict, export_results: Dict, is_ensemble: bool) -> str:
        """Generate comprehensive README for ultimate package."""
        mode = "ENSEMBLE" if is_ensemble else "SOLO"
        num_orgs = len(organism_names)
        
        # Build organism table
        org_table = "| # | Organism ID | Input | Hidden | Output | Language | Fitness |\n"
        org_table += "|---|-------------|-------|--------|--------|----------|--------|\n"
        for i, cfg in enumerate(brain_configs):
            org_id = cfg.get('organism_id', '?')[:16]
            has_lang = '✅' if cfg.get('use_language_head') else '❌'
            fitness = cfg.get('fitness', 0)
            fitness_str = f"{fitness:.4f}" if isinstance(fitness, float) else str(fitness)
            org_table += f"| {i+1} | `{org_id}` | {cfg.get('input_dim', 25)} | {cfg.get('hidden_dim', 64)} | {cfg.get('output_dim', 6)} | {has_lang} | {fitness_str} |\n"
        
        # Export status
        onnx_status = "✅ Included" if export_results.get('onnx', {}).get('success') else "❌ Failed"
        ts_status = "✅ Included" if export_results.get('torchscript', {}).get('success') else "❌ Failed"
        onnx_size = export_results.get('onnx', {}).get('size', 0)
        ts_size = export_results.get('torchscript', {}).get('size', 0)
        cocoon_size = export_results.get('cocoon', {}).get('size', 0)
        vocab_size = metadata.get('vocab_size', 0)
        kw_concepts = metadata.get('knowledge_web_concepts', 0)
        kw_relations = metadata.get('knowledge_web_relations', 0)
        
        return f'''# 🦋🦋 Butterfly Ensemble - Ultimate Package

> **{num_orgs} evolved AI organisms** unified into a single deployable intelligence

**Generated:** {metadata.get('generated', 'Unknown')}  
**Mode:** {mode} ({num_orgs} organisms)  
**Vocabulary:** {vocab_size:,} tokens  
**Knowledge Web:** {kw_concepts:,} concepts, {kw_relations:,} relations

---

## 📦 Package Contents

| File | Description | Size |
|------|-------------|------|
| `cocoon.py` | 🦋 **Full Python agent** - chat, gym, HTTP, sphere arena | {cocoon_size:,} bytes |
| `brain_ensemble.onnx` | ONNX model (all organisms) - inference only | {onnx_size:,} bytes {onnx_status} |
| `brain_ensemble.pt` | TorchScript model (all organisms) - can fine-tune | {ts_size:,} bytes {ts_status} |
| `bridge.py` | Universal runner (Gym/HTTP/CLI) for ONNX/TorchScript | - |
| `proton_tournament.py` | 🎮 Proton Game Arena - organism battles | - |
| `vocabulary.json` | Token vocabulary | - |
| `knowledge_web.json` | Semantic knowledge graph | - |
| `context_memory.json` | Conversation context | - |
| `metadata.json` | Complete configuration | - |
| `requirements.txt` | Python dependencies | - |
| `start.bat` / `start.sh` | Quick-start launcher | - |

---

## 🚀 Quick Start

### Option 1: Double-Click Launch
- **Windows:** Run `start.bat`
- **Linux/Mac:** Run `./start.sh`

### Option 2: cocoon.py (RECOMMENDED - Full Features)

The `cocoon.py` is the **gold standard** - it has ALL features:

```bash
# Install dependencies
pip install -r requirements.txt

# Interactive chat with learning
python cocoon.py --mode chat

# View organism info
python cocoon.py --mode info

# Play Gymnasium environments
python cocoon.py --mode gym --env CartPole-v1

# 3D Sphere Arena
python cocoon.py --mode sphere --train

# HTTP API server
python cocoon.py --mode serve --port 8080

# P2P networking (battle other cocoons)
python cocoon.py --mode link --hatch ws://server:9000
```

### Option 3: bridge.py (ONNX/TorchScript)

For deployment where you only need inference:

```bash
# Interactive mode (ONNX - fastest)
python bridge.py --model brain_ensemble.onnx --mode interactive

# Interactive mode (TorchScript - can fine-tune later)
python bridge.py --model brain_ensemble.pt --mode interactive

# Gymnasium environment
python bridge.py --model brain_ensemble.onnx --mode gym --env CartPole-v1 --render

# HTTP API server
python bridge.py --model brain_ensemble.onnx --mode http --port 8080
```

---

## 🔥 Continued Learning

**YES, this package supports continued learning!**

| Format | File | Learning | Subsystems | Best For |
|--------|------|----------|------------|----------|
| `cocoon.py` | Python | ✅ Full (neural + symbolic) | ✅ All (VP, language, knowledge web) | Research, chat, games |
| `.pt` (TorchScript) | brain_ensemble.pt | ✅ Neural only | ❌ None | Fine-tuning, C++ deployment |
| `.onnx` (ONNX) | brain_ensemble.onnx | ❌ Inference only | ❌ None | Production deployment |

**Fine-tuning TorchScript:**
```python
import torch

model = torch.jit.load("brain_ensemble.pt")
model.train()

optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
for state, target in new_data:
    optimizer.zero_grad()
    output = model(state)
    loss = criterion(output, target)
    loss.backward()
    optimizer.step()

torch.jit.save(model, "brain_finetuned.pt")
```

---

## 🧠 Ensemble Members

{org_table}

---

## 📚 cocoon.py Command Reference

### Mode Selection

| Mode | Command | Description |
|------|---------|-------------|
| **info** | `python cocoon.py --mode info` | Show organism metadata, vocabulary, architecture |
| **chat** | `python cocoon.py --mode chat` | Interactive conversation with learning |
| **gym** | `python cocoon.py --mode gym --env CartPole-v1` | Train/test in Gymnasium environments |
| **serve** | `python cocoon.py --mode serve --port 8080` | HTTP API server |
| **sphere** | `python cocoon.py --mode sphere --train` | 3D Sphere Arena swarm defense |
| **link** | `python cocoon.py --mode link` | P2P networking for cocoon battles |

### 💬 Chat Mode

```bash
python cocoon.py --mode chat
python cocoon.py --mode chat --verbose
```

**In-Chat Commands:** `quit`, `export <file.py>`

### 🌐 Sphere Arena (3D Training)

```bash
python cocoon.py --mode sphere              # Play
python cocoon.py --mode sphere --train      # Play + learn
python cocoon.py --mode sphere --headless   # Train without display
python cocoon.py --mode sphere --balls 3    # Multi-ball
```

### 🎮 Gymnasium Environments

```bash
# Classic Control (built-in)
python cocoon.py --mode gym --env CartPole-v1
python cocoon.py --mode gym --env MountainCar-v0
python cocoon.py --mode gym --env Acrobot-v1
python cocoon.py --mode gym --env LunarLander-v3  # pip install gymnasium[box2d]

# With visual rendering
python cocoon.py --mode gym --env CartPole-v1 --render

# Training run
python cocoon.py --mode gym --env CartPole-v1 --episodes 100
```

### 🏎️ TrackMania 2020 (TMRL)

```bash
# The cocoon_tmrl_adapter.py should be in this package or use:
python cocoon.py --unpack ./tmrl_setup

# Then run:
python cocoon_tmrl_adapter.py --cocoon cocoon.py --drive --episodes 4
python cocoon_tmrl_adapter.py --cocoon cocoon.py --train --episodes 10
```

**Requirements:** TrackMania 2020 + OpenPlanet + `pip install tmrl`

### 🌐 HTTP API Server

```bash
python cocoon.py --mode serve --port 8080
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/act` | Get action for state |
| `POST` | `/learn` | Add experience + train |
| `POST` | `/chat` | Chat with learning |
| `POST` | `/teach` | Teach new concepts |
| `GET` | `/vocab` | Get vocabulary |

```bash
curl -X POST http://localhost:8080/chat \\
  -H "Content-Type: application/json" \\
  -d '{{"prompt": "Hello!", "learn": true}}'
```

### 🔗 Link Mode (P2P Battles)

```bash
python cocoon.py --mode link --hatch ws://server:9000 --name "Champion"
```

**Commands:** `/users`, `/challenge <name>`, `/accept <id>`, `/chat <msg>`, `/quit`

### 🔬 Export & Conversion

```bash
python cocoon.py --export evolved.py                      # Export updated cocoon
python cocoon.py --export-onnx brain.onnx                 # ONNX (ensemble)
python cocoon.py --export-torchscript brain.pt            # TorchScript (ensemble)
python cocoon.py --export-onnx brain.onnx --organism 0    # Single organism
python cocoon.py --export-package ./my_model              # Full package
python cocoon.py --readme                                 # Print README
```

---

## 🎮 Proton Tournament

Battle your organisms against each other!

```bash
python proton_tournament.py
```

The tournament runs round-robin matches between all organisms, tracking wins/losses.

---

## 🔬 Architecture

```
                    Input State Vector ({metadata.get('max_input_dim', 25)} dims)
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
      ┌─────────┐     ┌─────────┐     ┌─────────┐
      │ Brain 1 │     │ Brain 2 │ ... │ Brain N │
      │  (DQN)  │     │  (DQN)  │     │  (DQN)  │
      └────┬────┘     └────┬────┘     └────┬────┘
           │               │               │
           ▼               ▼               ▼
      ┌─────────┐     ┌─────────┐     ┌─────────┐
      │ Q-vals  │     │ Q-vals  │     │ Q-vals  │
      └─────────┘     └─────────┘     └─────────┘
           │               │               │
           └───────────────┼───────────────┘
                           │
                    Ensemble Voting
                    (majority/weighted/confidence)
                           │
                           ▼
                    Final Action
```

---

## 📡 API Reference (cocoon.py)

```python
from cocoon import CocoonAgent

agent = CocoonAgent()

# Get action from state
action, outputs = agent.get_action(state_vector)
# outputs = {{'action_probs': [...], 'value': float, 'vp': float}}

# Chat
response = agent.process_input("Hello!")

# Access subsystems
agent.atomic_lang.get_atoms_by_emotion(min_valence=0.5)
agent.knowledge_web.get_related("concept", min_strength=0.3)
agent.vp_runtime.compute_from_state(state)
```

---

## 🔗 Links

- 📊 [View Model in Netron](https://netron.app/) - Drag & drop `.onnx` or `.pt`
- 🦋 [Convergence Engine](https://github.com/Yufok1/Convergence_Engine)
- 📚 [Gymnasium Docs](https://gymnasium.farama.org/)
- 🏎️ [TMRL (TrackMania)](https://github.com/trackmania-rl/tmrl)

---

## 🦋 About the Butterfly System

This package was generated by the **Butterfly Convergence Engine** - a neuro-symbolic AI framework combining:

- **Neural networks** for pattern recognition and action selection
- **Atomic language** for grounded semantic understanding
- **VP regulation** (Vigilance × Plasticity) for adaptive attention
- **Knowledge webs** for relational reasoning
- **Distributed ensembles** for robust decision-making

---

*Generated by 🦋 Butterfly Agent Compiler v2.0*
'''

    def _generate_cocoon_source(self,
                                brain_data_list: List[str],
                                arch_b64: str,
                                vocab_b64: str,
                                kw_b64: str,
                                config_b64: str,
                                atomic_lang_b64: str,
                                conversation_b64: str,
                                alliance_b64: str,
                                compressed: bool,
                                include_gym: bool,
                                include_http: bool,
                                is_ensemble: bool,
                                organism_names: List[str],
                                readme_b64: str) -> str:
        """Generate the complete cocoon Python source code with MONOLITHIC subsystems."""

        brain_data_py = "[\n" + ",\n".join(f'    "{b}"' for b in brain_data_list) + "\n]"
        mode_comment = "ENSEMBLE MODE - Multiple organisms with voting" if is_ensemble else "SOLO MODE - Single organism"
        generated_timestamp = datetime.datetime.now().isoformat()

        template = Template(r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🦋 BUTTERFLY COCOON - Self-Contained Learning Agent
════════════════════════════════════════════════════════════════════════════════

$MODE_COMMENT
Organisms: $ORGANISMS
Generated: $GENERATED_TS

Faithful behavioral clone of Butterfly System (as prescribed):
    • VP-aware attention: scores / (1.0 + vp_value)
    • Experience buffer stores input_tokens, target_tokens, vp_value
    • Triple-loss pipeline (RL + Language + Concept placeholder)
    • Curriculum-ready sequence handling
    • Solo + Ensemble voting

USAGE:
    python cocoon.py --mode chat
    python cocoon.py --mode gym --env CartPole-v1
    python cocoon.py --mode serve --port 8080
    python cocoon.py --export new_cocoon.py

ATTRIBUTION:
    Proton Game Arena inspired by Piers Anthony's "Apprentice Adept" (1980-1990)
    Absorption battle mechanic inspired by "Highlander" (1986), dir. Russell Mulcahy
    Butterfly System / Convergence Engine: https://github.com/Yufok1/Convergence_Engine
"""

import json
import base64
import random
import sys
import os
from io import BytesIO
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import deque
import numpy as np

# Embedded payloads (base64, optional zlib)
_BRAIN_DATA = $BRAIN_DATA
_ARCHITECTURE_B64 = "$ARCH_B64"
_VOCABULARY_B64 = "$VOCAB_B64"
_KNOWLEDGE_WEB_B64 = "$KW_B64"
_TRAINING_CONFIG_B64 = "$CONFIG_B64"
_ATOMIC_LANG_B64 = "$ATOMIC_LANG_B64"
_CONVERSATION_HISTORY_B64 = "$CONVERSATION_B64"
_ALLIANCE_B64 = "$ALLIANCE_B64"
_DATA_COMPRESSED = $DATA_COMPRESSED
_README_B64 = "$README_B64"
_TMRL_ADAPTER_B64 = "$TMRL_ADAPTER_B64"
_DRONE_ADAPTER_B64 = "$DRONE_ADAPTER_B64"
_DRONE_ARENA_B64 = "$DRONE_ARENA_B64"
_DRONE_PHYSICS_B64 = "$DRONE_PHYSICS_B64"


def _decode_data(b64_str: str, is_json: bool = True) -> Any:
    """Decode base64 encoded data with error handling for corrupted/placeholder values."""
    try:
        # Check for placeholder strings (not yet substituted)
        if b64_str.startswith('$$') or not b64_str:
            return None
        raw = base64.b64decode(b64_str)
        if _DATA_COMPRESSED:
            import zlib
            raw = zlib.decompress(raw)
        if is_json:
            return json.loads(raw.decode('utf-8'))
        return raw
    except Exception as e:
        # Return None for any decode failure - callers should provide fallback defaults
        print(f"[WARN] Failed to decode embedded data: {e}")
        return None


def _decode_brain(b64_str: str) -> bytes:
    raw = base64.b64decode(b64_str)
    if _DATA_COMPRESSED:
        import zlib
        raw = zlib.decompress(raw)
    return raw


def _print_embedded_readme():
    if not _README_B64:
        print("[INFO] No README embedded in this cocoon.")
        return
    try:
        text = base64.b64decode(_README_B64).decode('utf-8', errors='ignore')
    except Exception as exc:
        print(f"[!] Failed to decode embedded README: {exc}")
        return
    print(text)


def _unpack_ultimate(output_dir: str, voting: str = 'confidence', max_organisms: Optional[int] = None) -> bool:
    """Spawn a self-contained "ultimate package" from this cocoon.

    Writes (when available):
      - README.md (embedded)
      - cocoon_tmrl_adapter.py (embedded)
      - vocabulary.json
      - metadata.json
      - requirements.txt
      - ensemble.onnx (requires torch)
      - ensemble_weights.pt (requires torch)
    """
    os.makedirs(output_dir, exist_ok=True)

    spawned = []

    # 1) README
    if _README_B64:
        try:
            readme_text = base64.b64decode(_README_B64).decode('utf-8', errors='ignore')
            readme_path = os.path.join(output_dir, 'README.md')
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_text)
            spawned.append(readme_path)
            print(f"[OK] Unpacked README: {readme_path}")
        except Exception as exc:
            print(f"[!] README unpack failed: {exc}")
    else:
        print("[INFO] No README embedded; skipping README.md")

    # 2) TMRL adapter
    if _TMRL_ADAPTER_B64:
        try:
            adapter_code = base64.b64decode(_TMRL_ADAPTER_B64).decode('utf-8', errors='ignore')
            adapter_path = os.path.join(output_dir, 'cocoon_tmrl_adapter.py')
            with open(adapter_path, 'w', encoding='utf-8') as f:
                f.write(adapter_code)
            spawned.append(adapter_path)
            print(f"[OK] Unpacked adapter: {adapter_path}")
        except Exception as exc:
            print(f"[!] Adapter unpack failed: {exc}")
    else:
        print("[INFO] No TMRL adapter embedded; skipping cocoon_tmrl_adapter.py")

    # 2b) Drone adapter
    if _DRONE_ADAPTER_B64:
        try:
            drone_code = base64.b64decode(_DRONE_ADAPTER_B64).decode('utf-8', errors='ignore')
            drone_path = os.path.join(output_dir, 'cocoon_drone_adapter.py')
            with open(drone_path, 'w', encoding='utf-8') as f:
                f.write(drone_code)
            spawned.append(drone_path)
            print(f"[OK] Unpacked drone adapter: {drone_path}")
        except Exception as exc:
            print(f"[!] Drone adapter unpack failed: {exc}")
    else:
        print("[INFO] No drone adapter embedded; skipping cocoon_drone_adapter.py")

    # 2c) Drone arena (full NASA physics)
    if _DRONE_ARENA_B64:
        try:
            arena_code = base64.b64decode(_DRONE_ARENA_B64).decode('utf-8', errors='ignore')
            arena_path = os.path.join(output_dir, 'cocoon_drone_arena.py')
            with open(arena_path, 'w', encoding='utf-8') as f:
                f.write(arena_code)
            spawned.append(arena_path)
            print(f"[OK] Unpacked drone arena: {arena_path}")
        except Exception as exc:
            print(f"[!] Drone arena unpack failed: {exc}")
    else:
        print("[INFO] No drone arena embedded; skipping cocoon_drone_arena.py")

    # 2d) Drone physics (JSBSim quadcopter)
    if _DRONE_PHYSICS_B64:
        try:
            physics_code = base64.b64decode(_DRONE_PHYSICS_B64).decode('utf-8', errors='ignore')
            physics_path = os.path.join(output_dir, 'jsbsim_quadcopter.py')
            with open(physics_path, 'w', encoding='utf-8') as f:
                f.write(physics_code)
            spawned.append(physics_path)
            print(f"[OK] Unpacked drone physics: {physics_path}")
        except Exception as exc:
            print(f"[!] Drone physics unpack failed: {exc}")
    else:
        print("[INFO] No drone physics embedded; skipping jsbsim_quadcopter.py")

    # 3) Vocabulary
    try:
        vocab_obj = _decode_data(_VOCABULARY_B64, is_json=True)
        vocab_path = os.path.join(output_dir, 'vocabulary.json')
        with open(vocab_path, 'w', encoding='utf-8') as f:
            json.dump(vocab_obj, f, indent=2, default=_json_default)
        spawned.append(vocab_path)
        print(f"[OK] Unpacked vocab: {vocab_path}")
    except Exception as exc:
        print(f"[!] Vocabulary unpack failed: {exc}")

    # 4) Metadata - handles existing metadata.json from package exports
    try:
        arch_obj = _decode_data(_ARCHITECTURE_B64, is_json=True)
        cfg_obj = _decode_data(_TRAINING_CONFIG_B64, is_json=True)
        cocoon_meta = {
            'generated': arch_obj.get('generated') if isinstance(arch_obj, dict) else None,
            'mode': 'ENSEMBLE' if (isinstance(arch_obj, dict) and arch_obj.get('is_ensemble')) else 'SOLO',
            'ensemble_size': arch_obj.get('ensemble_size') if isinstance(arch_obj, dict) else None,
            'organism_names': arch_obj.get('organism_names') if isinstance(arch_obj, dict) else None,
            'training_config': cfg_obj,
            'data_compressed': bool(_DATA_COMPRESSED),
            'includes_readme': bool(_README_B64),
            'includes_tmrl_adapter': bool(_TMRL_ADAPTER_B64),
            'unpack_outputs': {
                'onnx': 'ensemble.onnx',
                'weights': 'ensemble_weights.pt',
            },
        }
        meta_path = os.path.join(output_dir, 'metadata.json')
        
        # Check if metadata.json already exists (e.g., from package export)
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    existing_meta = json.load(f)
                # Merge: add cocoon_metadata to existing, preserving package metadata
                existing_meta['cocoon_metadata'] = cocoon_meta
                meta = existing_meta
                print(f"[OK] Merged cocoon metadata into existing metadata.json")
            except Exception:
                # If read fails, just use cocoon metadata
                meta = cocoon_meta
        else:
            meta = cocoon_meta
        
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2, default=_json_default)
        spawned.append(meta_path)
        print(f"[OK] Unpacked metadata: {meta_path}")
    except Exception as exc:
        print(f"[!] Metadata unpack failed: {exc}")

    # 5) Requirements (minimal, offline-friendly)
    try:
        reqs = """# Cocoon Ultimate Package Dependencies
# Install with: pip install -r requirements.txt

# Core
numpy>=1.21.0

# Neural network weights + ONNX export
torch>=2.0.0
onnx>=1.14.0
onnxruntime>=1.15.0  # Runtime (CPU)
# onnxruntime-gpu>=1.15.0  # Uncomment for NVIDIA GPU

# P2P Networking (for CocoonLink battles)
websockets>=11.0

# Drone Warfare Arena
matplotlib>=3.8.0    # Trajectory visualization
# PyFlyt>=1.0.0      # Optional: 3D drone visualization (pip install PyFlyt)

# Gymnasium Environments (Proton Game Arena)
gymnasium>=0.29.0    # Core RL environments
pygame>=2.5.0        # Visual rendering
"""
        req_path = os.path.join(output_dir, 'requirements.txt')
        with open(req_path, 'w', encoding='utf-8') as f:
            f.write(reqs)
        spawned.append(req_path)
        print(f"[OK] Unpacked requirements: {req_path}")
    except Exception as exc:
        print(f"[!] Requirements write failed: {exc}")

    # 6) ONNX + weights bundle (requires torch)
    if not TORCH_AVAILABLE:
        print("[WARN] torch not available; skipping ensemble.onnx and ensemble_weights.pt")
        print("       Install: pip install torch onnx")
    else:
        try:
            # Instantiate agent on demand (may take time)
            agent = CocoonAgent(voting=voting, max_organisms=max_organisms)

            import torch
            import torch.nn as nn

            class EnsembleMeanWrapper(nn.Module):
                def __init__(self, brains):
                    super().__init__()
                    self.brains = nn.ModuleList(brains)

                def forward(self, x: torch.Tensor):
                    outs = []
                    for b in self.brains:
                        out = b(x)
                        # handle tuple outputs (action_probs, language_logits, ...)
                        if isinstance(out, tuple):
                            out = out[0]
                        outs.append(out)
                    stacked = torch.stack(outs, dim=0)
                    return stacked.mean(dim=0)

            # Build ONNX ensemble
            ensemble = EnsembleMeanWrapper(agent.brains).eval().cpu()
            input_dim = getattr(agent.brains[0], 'input_dim', 25) if agent.brains else 25
            dummy = torch.randn(1, input_dim, device='cpu')
            onnx_path = os.path.join(output_dir, 'ensemble.onnx')
            torch.onnx.export(
                ensemble,
                dummy,
                onnx_path,
                input_names=['observation'],
                output_names=['action'],
                dynamic_axes={'observation': {0: 'batch_size'}, 'action': {0: 'batch_size'}},
                opset_version=14,
                do_constant_folding=True,
            )
            spawned.append(onnx_path)
            print(f"[OK] Unpacked ONNX: {onnx_path} ({len(agent.brains)} brains unified)")

            # Bundle weights
            bundle = {
                'n_brains': len(agent.brains),
                'brains': [b.state_dict() for b in agent.brains],
                'config': {
                    'input_dim': getattr(agent.brains[0], 'input_dim', None) if agent.brains else None,
                    'hidden_dim': getattr(agent.brains[0], 'hidden_dim', None) if agent.brains else None,
                    'output_dim': getattr(agent.brains[0], 'output_dim', None) if agent.brains else None,
                },
            }
            weights_path = os.path.join(output_dir, 'ensemble_weights.pt')
            torch.save(bundle, weights_path)
            spawned.append(weights_path)
            print(f"[OK] Unpacked weights: {weights_path} ({len(agent.brains)} brains bundled)")
        except Exception as exc:
            print(f"[!] Torch export failed: {exc}")

    print("\n✅ Ultimate package unpack complete")
    print(f"   Output: {os.path.abspath(output_dir)}")
    return len(spawned) > 0


def _json_default(obj):
    """Fallback serializer for numpy/torch objects when exporting cocoons."""
    if hasattr(obj, 'item'):  # numpy scalar or torch tensor scalar
        return obj.item()
    if hasattr(obj, 'tolist'):  # numpy array or torch tensor
        return obj.tolist()
    if isinstance(obj, set):
        return list(obj)
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    return str(obj)


# Torch imports
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("[!] PyTorch not found. Install with: pip install torch")
    print("    Learning disabled; info mode still works.")


# Experience buffer with token + VP support
@dataclass
class Experience:
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool
    input_tokens: List[int]
    target_tokens: List[int]
    vp_value: Optional[float]


class ExperienceBuffer:
    def __init__(self, capacity: int = 0):
        self.capacity = capacity if capacity and capacity > 0 else None
        self.buffer: deque = deque(maxlen=self.capacity)

    def add(self, state, action, reward, next_state, done,
            input_tokens: Optional[List[int]] = None,
            target_tokens: Optional[List[int]] = None,
            vp_value: Optional[float] = None):
        exp = Experience(
            np.asarray(state, dtype=np.float32),
            int(action),
            float(reward),
            np.asarray(next_state, dtype=np.float32),
            bool(done),
            input_tokens or [],
            target_tokens or [],
            vp_value
        )
        self.buffer.append(exp)

    def __len__(self):
        return len(self.buffer)

    def sample(self, batch_size: int) -> List[Experience]:
        batch_size = min(batch_size, len(self.buffer))
        return random.sample(list(self.buffer), batch_size)

    def sample_batch(self, batch_size: int):
        exps = self.sample(batch_size)
        return (
            np.array([e.state for e in exps]),
            np.array([e.action for e in exps]),
            np.array([e.reward for e in exps]),
            np.array([e.next_state for e in exps]),
            np.array([e.done for e in exps]),
            [e.input_tokens for e in exps],
            [e.target_tokens for e in exps],
            [e.vp_value for e in exps],
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 🧬 ATOMIC LANGUAGE SYSTEM - Trackable Linguistic Units
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ConceptAssociation:
    """Association between two concepts - a trackable link."""
    target_concept: str
    strength: float = 0.0  # -1.0 to 1.0 (negative = inhibition)
    formation_reason: str = "unknown"
    success_count: int = 0
    failure_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'target': self.target_concept,
            'strength': self.strength,
            'formation_reason': self.formation_reason,
            'success_rate': self.success_count / max(1, self.success_count + self.failure_count)
        }


@dataclass
class LinguisticAtom:
    """Single trackable linguistic unit - like a trait but for language."""
    concept_id: str
    strength: float = 0.5
    associations: Dict[str, ConceptAssociation] = None
    source: str = "innate"  # 'innate', 'observed', 'taught', 'discovered'
    semantic_frame: str = "unknown"  # 'action', 'state', 'quality', 'relationship'
    abstraction_level: int = 0  # 0=concrete, 1=abstract, 2=meta
    usage_count: int = 0
    vp_vitality_affinity: float = 0.5
    vp_pleasure_affinity: float = 0.5
    
    def __post_init__(self):
        if self.associations is None:
            self.associations = {}
    
    def form_association(self, target: str, strength: float, reason: str):
        """Form or strengthen association with another concept."""
        if target in self.associations:
            old = self.associations[target].strength
            self.associations[target].strength = np.clip(old + strength * 0.3, -1.0, 1.0)
        else:
            self.associations[target] = ConceptAssociation(
                target_concept=target, strength=np.clip(strength, -1.0, 1.0),
                formation_reason=reason
            )
    
    def get_top_associations(self, n: int = 5) -> List[Tuple[str, float]]:
        """Get top N associations by strength."""
        sorted_assocs = sorted(self.associations.items(), key=lambda x: abs(x[1].strength), reverse=True)
        return [(k, v.strength) for k, v in sorted_assocs[:n]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'concept_id': self.concept_id,
            'strength': self.strength,
            'source': self.source,
            'semantic_frame': self.semantic_frame,
            'abstraction_level': self.abstraction_level,
            'usage_count': self.usage_count,
            'vp_affinity': {'vitality': self.vp_vitality_affinity, 'pleasure': self.vp_pleasure_affinity},
            'associations': {k: v.to_dict() for k, v in self.associations.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LinguisticAtom':
        atom = cls(
            concept_id=data['concept_id'],
            strength=data.get('strength', 0.5),
            source=data.get('source', 'unknown'),
            semantic_frame=data.get('semantic_frame', 'unknown'),
            abstraction_level=data.get('abstraction_level', 0),
            usage_count=data.get('usage_count', 0),
            vp_vitality_affinity=data.get('vp_affinity', {}).get('vitality', 0.5),
            vp_pleasure_affinity=data.get('vp_affinity', {}).get('pleasure', 0.5)
        )
        for assoc_id, assoc_data in data.get('associations', {}).items():
            atom.associations[assoc_id] = ConceptAssociation(
                target_concept=assoc_data['target'],
                strength=assoc_data['strength'],
                formation_reason=assoc_data.get('formation_reason', 'loaded')
            )
        return atom


class AtomicLanguageSystem:
    """Per-organism atomic language representation with trackable discrete atoms.
    
    Now loads innate concepts from data/innate_vocab.json (nuclear vocab).
    """
    
    # Innate vocabulary loaded from data/innate_vocab.json
    _INNATE_VOCAB_CACHE = None  # Class-level cache
    
    # Fallback core concepts if innate_vocab.json not found
    FALLBACK_INNATE_CONCEPTS = {
        'move': {'frame': 'action', 'level': 0, 'vp': (0.5, 0.5)},
        'rest': {'frame': 'action', 'level': 0, 'vp': (0.3, 0.6)},
        'eat': {'frame': 'action', 'level': 0, 'vp': (0.4, 0.7)},
        'cooperate': {'frame': 'action', 'level': 0, 'vp': (0.5, 0.7)},
        'attack': {'frame': 'action', 'level': 0, 'vp': (0.6, 0.3)},
        'hungry': {'frame': 'state', 'level': 0, 'vp': (0.3, 0.3)},
        'safe': {'frame': 'state', 'level': 0, 'vp': (0.6, 0.7)},
        'danger': {'frame': 'state', 'level': 0, 'vp': (0.4, 0.2)},
        'friend': {'frame': 'relationship', 'level': 0, 'vp': (0.5, 0.8)},
        'enemy': {'frame': 'relationship', 'level': 0, 'vp': (0.5, 0.2)},
        'food': {'frame': 'resource', 'level': 0, 'vp': (0.5, 0.7)},
        'energy': {'frame': 'resource', 'level': 0, 'vp': (0.6, 0.5)},
    }
    
    @classmethod
    def _load_innate_vocab(cls):
        """Load innate vocabulary from JSON file (cached at class level)."""
        if cls._INNATE_VOCAB_CACHE is not None:
            return cls._INNATE_VOCAB_CACHE
        
        from pathlib import Path
        innate_path = Path(__file__).parent.parent / "data" / "innate_vocab.json"
        
        try:
            with open(innate_path, 'r', encoding='utf-8') as f:
                cls._INNATE_VOCAB_CACHE = json.load(f)
                return cls._INNATE_VOCAB_CACHE
        except FileNotFoundError:
            cls._INNATE_VOCAB_CACHE = None
            return None
        except Exception as e:
            cls._INNATE_VOCAB_CACHE = None
            return None
    
    def __init__(self, organism_id: str = "cocoon"):
        self.organism_id = organism_id
        self.atoms: Dict[str, LinguisticAtom] = {}
        self._concept_order: List[str] = []
        self._initialize_innate_concepts()
    
    def _initialize_innate_concepts(self):
        """Initialize with innate concepts from nuclear vocab or fallback."""
        innate_data = self._load_innate_vocab()
        
        if innate_data is None:
            # Fallback to minimal hardcoded concepts
            for concept_id, info in self.FALLBACK_INNATE_CONCEPTS.items():
                self._add_innate_concept(concept_id, info, 'innate', 0.5)
            return
        
        # Load from innate_vocab.json
        concepts = innate_data.get('concepts', {})
        tiers = innate_data.get('tiers', {})
        tier_config = innate_data.get('tier_config', {})
        associations = innate_data.get('associations', [])
        
        # Tier 1: Core concepts (all organisms)
        for word in tiers.get('core', []):
            if word in concepts:
                self._add_innate_concept(word, concepts[word], 'innate_core', 0.6)
        
        # Tier 2: Extended concepts (random subset)
        extended = tiers.get('extended', [])
        ext_range = tier_config.get('extended_sample_range', [20, 50])
        num_ext = np.random.randint(ext_range[0], ext_range[1] + 1)
        if extended:
            selected = list(np.random.choice(extended, size=min(num_ext, len(extended)), replace=False))
            for word in selected:
                if word in concepts and word not in self.atoms:
                    self._add_innate_concept(word, concepts[word], 'innate_extended', 0.4)
        
        # Tier 3: Pool concepts (rare additions)
        pool = tiers.get('pool', [])
        pool_range = tier_config.get('pool_sample_range', [0, 10])
        num_pool = np.random.randint(pool_range[0], pool_range[1] + 1)
        if pool and num_pool > 0:
            selected = list(np.random.choice(pool, size=min(num_pool, len(pool)), replace=False))
            for word in selected:
                if word in concepts and word not in self.atoms:
                    self._add_innate_concept(word, concepts[word], 'innate_rare', 0.25)
        
        # Initialize associations
        for assoc in associations:
            src, tgt = assoc.get('source', ''), assoc.get('target', '')
            if src in self.atoms and tgt in self.atoms:
                self.atoms[src].form_association(tgt, assoc.get('strength', 0.5), 'innate')
    
    def _add_innate_concept(self, word: str, info: dict, source: str, base_strength: float):
        """Helper to add an innate concept atom."""
        vp = info.get('vp', (0.5, 0.5))
        atom = LinguisticAtom(
            concept_id=word,
            strength=base_strength + np.random.uniform(-0.1, 0.1),
            source=source,
            semantic_frame=info.get('frame', 'unknown'),
            abstraction_level=info.get('level', 0),
            vp_vitality_affinity=vp[0] if isinstance(vp, (list, tuple)) else 0.5,
            vp_pleasure_affinity=vp[1] if isinstance(vp, (list, tuple)) else 0.5
        )
        self.atoms[word] = atom
        self._concept_order.append(word)
    
    def acquire_concept(self, concept_id: str, source: str = 'discovered', 
                       semantic_frame: str = 'unknown', initial_strength: float = 0.3) -> LinguisticAtom:
        """Acquire a new concept (learn a new word)."""
        if concept_id in self.atoms:
            self.atoms[concept_id].strength = min(1.0, self.atoms[concept_id].strength + 0.1)
            return self.atoms[concept_id]
        atom = LinguisticAtom(
            concept_id=concept_id, strength=initial_strength, source=source,
            semantic_frame=semantic_frame
        )
        self.atoms[concept_id] = atom
        self._concept_order.append(concept_id)
        return atom
    
    def form_association(self, source: str, target: str, strength: float, reason: str):
        """Form association between two concepts."""
        if source not in self.atoms:
            self.acquire_concept(source, 'implicit')
        if target not in self.atoms:
            self.acquire_concept(target, 'implicit')
        self.atoms[source].form_association(target, strength, reason)
    
    def get_activated_concepts(self, vp_state: Tuple[float, float], top_k: int = 10) -> List[Tuple[str, float]]:
        """Get concepts most activated by current VP state."""
        vitality, pleasure = vp_state
        activations = []
        for concept_id, atom in self.atoms.items():
            activation = atom.strength
            vp_match = 1.0 - 0.5 * (abs(vitality - atom.vp_vitality_affinity) + abs(pleasure - atom.vp_pleasure_affinity))
            activation *= (0.7 + 0.3 * vp_match)
            activations.append((concept_id, activation))
        activations.sort(key=lambda x: x[1], reverse=True)
        return activations[:top_k]
    
    def to_tensor(self, dim: int = 64) -> np.ndarray:
        """Convert to fixed-size tensor for neural network input."""
        tensor = np.zeros(dim, dtype=np.float32)
        for i, concept_id in enumerate(self._concept_order[:dim]):
            if concept_id in self.atoms:
                tensor[i] = self.atoms[concept_id].strength
        return tensor
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'organism_id': self.organism_id,
            'atoms': {cid: atom.to_dict() for cid, atom in self.atoms.items()},
            'concept_order': self._concept_order
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AtomicLanguageSystem':
        system = cls(organism_id=data.get('organism_id', 'cocoon'))
        loaded_atoms = data.get('atoms', {})
        # FIXED: MERGE loaded atoms with innate concepts instead of replacing
        # This preserves innate concepts while adding/updating learned ones
        if loaded_atoms:
            # Merge loaded atoms over innate (loaded takes precedence)
            for concept_id, atom_data in loaded_atoms.items():
                system.atoms[concept_id] = LinguisticAtom.from_dict(atom_data)
            # Update concept order to include both innate and loaded
            loaded_order = data.get('concept_order', [])
            # Merge orders: loaded order first, then any innate not in loaded
            innate_not_in_loaded = [c for c in system._concept_order if c not in loaded_order]
            system._concept_order = loaded_order + innate_not_in_loaded
        # If no atoms were loaded, keep the innate concepts initialized by __init__
        return system


# ═══════════════════════════════════════════════════════════════════════════════
# 💬 CONVERSATION HISTORY - Context Memory System
# ═══════════════════════════════════════════════════════════════════════════════

class ConversationHistory:
    """Tracks conversation context for coherent multi-turn dialogue."""
    
    def __init__(self, max_turns: int = 50, max_topics: int = 10):
        self.messages: deque = deque(maxlen=max_turns)
        self.topics: Dict[str, float] = {}  # topic -> relevance score
        self.max_topics = max_topics
        self.turn_count = 0
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to history."""
        self.turn_count += 1
        entry = {
            'turn': self.turn_count,
            'role': role,  # 'user' or 'assistant'
            'content': content,
            'metadata': metadata or {}
        }
        self.messages.append(entry)
        self._update_topics(content)
    
    def _update_topics(self, content: str):
        """Extract and update topic relevance from content."""
        words = content.lower().split()
        # Simple topic extraction: words that appear multiple times
        word_counts = {}
        for word in words:
            if len(word) > 3:  # Skip short words
                word_counts[word] = word_counts.get(word, 0) + 1
        # Decay existing topics
        for topic in self.topics:
            self.topics[topic] *= 0.9
        # Boost mentioned topics
        for word, count in word_counts.items():
            if count >= 1:
                self.topics[word] = min(1.0, self.topics.get(word, 0) + 0.2 * count)
        # Prune low-relevance topics
        self.topics = dict(sorted(self.topics.items(), key=lambda x: x[1], reverse=True)[:self.max_topics])
    
    def get_context_window(self, n: int = 5) -> List[Dict]:
        """Get last N messages for context."""
        return list(self.messages)[-n:]
    
    def get_active_topics(self, min_relevance: float = 0.3) -> List[str]:
        """Get currently active topics."""
        return [t for t, r in self.topics.items() if r >= min_relevance]
    
    def get_context_string(self, n: int = 3) -> str:
        """Get context as string for prompt augmentation."""
        recent = self.get_context_window(n)
        if not recent:
            return ""
        lines = []
        for msg in recent:
            prefix = "User" if msg['role'] == 'user' else "Assistant"
            lines.append(f"{prefix}: {msg['content'][:100]}")
        return " | ".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'messages': list(self.messages),
            'topics': self.topics,
            'turn_count': self.turn_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationHistory':
        history = cls()
        history.turn_count = data.get('turn_count', 0)
        history.topics = data.get('topics', {})
        for msg in data.get('messages', []):
            history.messages.append(msg)
        return history


# ═══════════════════════════════════════════════════════════════════════════════
# 🕸️ ENHANCED KNOWLEDGE WEB - Semantic Relations System
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass  
class SemanticRelation:
    """A semantic relationship between concepts."""
    source: str
    target: str
    relation_type: str  # 'synonym', 'antonym', 'causes', 'enables', 'similar_to'
    strength: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {'source': self.source, 'target': self.target, 
                'type': self.relation_type, 'strength': self.strength}


class EnhancedKnowledgeWeb:
    """Comprehensive semantic network for language understanding."""
    
    def __init__(self):
        self.concepts: Dict[str, Dict[str, Any]] = {}
        self.relations: List[SemanticRelation] = []
        self.relation_index: Dict[str, List[SemanticRelation]] = {}
    
    def load_from_data(self, data: Dict[str, Any]):
        """Load from embedded knowledge web data."""
        self.concepts = data.get('concepts', {})
        for rel_data in data.get('relations', []):
            rel = SemanticRelation(
                source=rel_data['source'], target=rel_data['target'],
                relation_type=rel_data.get('type', rel_data.get('relation_type', 'related_to')),
                strength=rel_data.get('strength', 1.0)
            )
            self.relations.append(rel)
            if rel.source not in self.relation_index:
                self.relation_index[rel.source] = []
            self.relation_index[rel.source].append(rel)
    
    def get_synonyms(self, word: str, min_strength: float = 0.5) -> List[str]:
        """Get synonyms for a word."""
        results = []
        for rel in self.relation_index.get(word.lower(), []):
            if rel.relation_type == 'synonym' and rel.strength >= min_strength:
                results.append(rel.target)
        return results
    
    def get_related(self, word: str, relation_type: Optional[str] = None, 
                   min_strength: float = 0.3) -> List[Tuple[str, str, float]]:
        """Get related words with optional relation type filter."""
        results = []
        for rel in self.relation_index.get(word.lower(), []):
            if rel.strength >= min_strength:
                if relation_type is None or rel.relation_type == relation_type:
                    results.append((rel.target, rel.relation_type, rel.strength))
        return results
    
    def get_concept_info(self, word: str) -> Optional[Dict[str, Any]]:
        """Get concept information."""
        return self.concepts.get(word.lower())
    
    def compute_semantic_similarity(self, word1: str, word2: str) -> float:
        """Compute semantic similarity between two words."""
        # Check direct relations
        for rel in self.relation_index.get(word1.lower(), []):
            if rel.target == word2.lower():
                if rel.relation_type in ['synonym', 'similar_to']:
                    return rel.strength
        # Check concept category match
        c1 = self.concepts.get(word1.lower(), {})
        c2 = self.concepts.get(word2.lower(), {})
        if c1.get('category') and c1.get('category') == c2.get('category'):
            return 0.5
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'concepts': self.concepts,
            'relations': [r.to_dict() for r in self.relations]
        }


# ═══════════════════════════════════════════════════════════════════════════════
# ⚡ VP RUNTIME - Violation Pressure Computation for Self-Regulation
# ═══════════════════════════════════════════════════════════════════════════════

class VPRuntime:
    """
    Lightweight VP (Violation Pressure) runtime for standalone cocoon operation.
    Computes vitality, pleasure, and violation_pressure from state vectors.
    
    VP Classification:
        VP0: 0.00-0.25 (Fully lawful - optimal operation)
        VP1: 0.25-0.50 (Stable drift - continue with logging)
        VP2: 0.50-0.75 (Instability - needs attention)
        VP3: 0.75-0.99 (Critical - intervention needed)
        VP4: >= 1.00 (Collapse threshold)
    """
    
    def __init__(self, smoothing_factor: float = 0.3, history_size: int = 20):
        self.smoothing_factor = smoothing_factor
        self.history_size = history_size
        self.vp_history: deque = deque(maxlen=history_size)
        self.last_vp = 0.0
        self.vitality = 0.5
        self.pleasure = 0.5
        
        # Component weights for VP calculation
        self.component_weights = {
            'resource_deficit': 0.25,   # Low energy/resources
            'social_isolation': 0.20,   # Few connections
            'action_conflict': 0.20,    # Competing action signals
            'learning_stagnation': 0.15, # Low reward variance
            'entropy_excess': 0.20      # High uncertainty
        }
    
    def compute_from_state(self, state: np.ndarray, reward_history: Optional[List[float]] = None) -> Dict[str, float]:
        """
        Compute VP components from organism state vector.
        
        State vector mapping (25-dim base features):
            0-5: Action probabilities
            6-8: Resource levels (energy, fitness, age)
            9-11: Social signals (cooperation, competition, isolation)
            12-14: Environmental context
            15-24: Additional features + illumination
            
            (Optional 25-27: Self-perception features when enabled)
        
        Returns dict with: vitality, pleasure, violation_pressure, vp_class, components
        """
        components = {}
        
        # 1. Resource deficit: low values in resource positions
        if len(state) > 8:
            resource_signals = state[6:9]  # Energy, fitness, age-normalized
            resource_deficit = max(0, 1.0 - np.mean(resource_signals))
            components['resource_deficit'] = resource_deficit
        else:
            components['resource_deficit'] = 0.3
        
        # 2. Social isolation: low cooperation, high isolation signals
        if len(state) > 11:
            cooperation = state[9] if len(state) > 9 else 0.5
            isolation = state[11] if len(state) > 11 else 0.5
            social_isolation = max(0, isolation - cooperation + 0.5)
            components['social_isolation'] = np.clip(social_isolation, 0, 1)
        else:
            components['social_isolation'] = 0.3
        
        # 3. Action conflict: entropy of action probabilities
        if len(state) > 5:
            action_probs = state[0:6]
            action_probs = np.abs(action_probs) / (np.sum(np.abs(action_probs)) + 1e-9)
            entropy = -np.sum(action_probs * np.log(action_probs + 1e-9))
            max_entropy = np.log(6)  # 6 actions
            components['action_conflict'] = np.clip(entropy / max_entropy, 0, 1)
        else:
            components['action_conflict'] = 0.3
        
        # 4. Learning stagnation: low variance in recent rewards
        if reward_history and len(reward_history) > 3:
            reward_std = np.std(reward_history[-10:])
            stagnation = max(0, 1.0 - reward_std * 5)  # Low variance = high stagnation
            components['learning_stagnation'] = np.clip(stagnation, 0, 1)
        else:
            components['learning_stagnation'] = 0.3
        
        # 5. Entropy excess: general state entropy
        state_normalized = np.abs(state) / (np.sum(np.abs(state)) + 1e-9)
        state_entropy = -np.sum(state_normalized * np.log(state_normalized + 1e-9))
        max_state_entropy = np.log(len(state))
        components['entropy_excess'] = np.clip(state_entropy / max_state_entropy, 0, 1)
        
        # Combine components using weighted sum
        raw_vp = sum(components[k] * self.component_weights[k] for k in components)
        
        # Apply smoothing
        smoothed_vp = self.smoothing_factor * raw_vp + (1 - self.smoothing_factor) * self.last_vp
        smoothed_vp = np.clip(smoothed_vp, 0, 1)
        self.last_vp = smoothed_vp
        self.vp_history.append(smoothed_vp)
        
        # Derive vitality and pleasure from components
        self.vitality = 1.0 - (components['resource_deficit'] * 0.6 + components['learning_stagnation'] * 0.4)
        self.pleasure = 1.0 - (components['social_isolation'] * 0.5 + components['action_conflict'] * 0.5)
        
        # Classify VP
        if smoothed_vp < 0.25:
            vp_class = 'VP0'
        elif smoothed_vp < 0.50:
            vp_class = 'VP1'
        elif smoothed_vp < 0.75:
            vp_class = 'VP2'
        elif smoothed_vp < 1.00:
            vp_class = 'VP3'
        else:
            vp_class = 'VP4'
        
        return {
            'vitality': float(self.vitality),
            'pleasure': float(self.pleasure),
            'violation_pressure': float(smoothed_vp),
            'vp_class': vp_class,
            'components': components,
            'history_mean': float(np.mean(list(self.vp_history))) if self.vp_history else smoothed_vp
        }
    
    def get_vp_value(self) -> float:
        """Get current VP value for attention scaling."""
        return self.last_vp
    
    def get_vp_state(self) -> Tuple[float, float]:
        """Get (vitality, pleasure) tuple for concept activation."""
        return (self.vitality, self.pleasure)
    
    def reset(self):
        """Reset VP runtime state."""
        self.vp_history.clear()
        self.last_vp = 0.0
        self.vitality = 0.5
        self.pleasure = 0.5


# Multi-head attention with VP scaling
if TORCH_AVAILABLE:
    class MultiHeadAttention(nn.Module):
        def __init__(self, embed_dim: int, num_heads: int = 4, dropout: float = 0.1):
            super().__init__()
            if embed_dim % num_heads != 0:
                raise ValueError("embed_dim must be divisible by num_heads")
            self.embed_dim = embed_dim
            self.num_heads = num_heads
            self.head_dim = embed_dim // num_heads
            self.scale = float(self.head_dim) ** 0.5
            self.q_proj = nn.Linear(embed_dim, embed_dim)
            self.k_proj = nn.Linear(embed_dim, embed_dim)
            self.v_proj = nn.Linear(embed_dim, embed_dim)
            self.out_proj = nn.Linear(embed_dim, embed_dim)
            self.dropout = nn.Dropout(dropout)

        def forward(self, x: torch.Tensor, vp_value: Optional[float] = None) -> torch.Tensor:
            bsz, seq_len, _ = x.size()
            q = self.q_proj(x).view(bsz, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
            k = self.k_proj(x).view(bsz, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
            v = self.v_proj(x).view(bsz, seq_len, self.num_heads, self.head_dim).transpose(1, 2)

            scores = torch.matmul(q, k.transpose(-2, -1)) / self.scale
            if vp_value is not None and vp_value > 0:
                scores = scores / (1.0 + vp_value)

            attn = F.softmax(scores, dim=-1)
            attn = self.dropout(attn)
            out = torch.matmul(attn, v)
            out = out.transpose(1, 2).contiguous().view(bsz, seq_len, self.embed_dim)
            return self.out_proj(out)


    class HopfieldLayer(nn.Module):
        """
        Modern Continuous Hopfield Network for iterative thought refinement.
        
        Implements energy-based pattern retrieval with learnable memory patterns.
        E(ξ) = -β⁻¹ log Σᵢ exp(β xᵢᵀ ξ)
        Update: ξ' = softmax(β Xᵀ ξ) · X
        """
        def __init__(self, hidden_dim: int = 64, num_patterns: int = 32,
                     max_iterations: int = 5, beta: float = 1.0, dropout: float = 0.1):
            super().__init__()
            self.hidden_dim = hidden_dim
            self.num_patterns = num_patterns
            self.max_iterations = max_iterations
            self.beta = beta
            self.convergence_threshold = 1e-3
            
            # Learnable pattern memory
            self.patterns = nn.Parameter(torch.randn(num_patterns, hidden_dim) * 0.02)
            
            # Projections for attention mechanism
            self.query_proj = nn.Linear(hidden_dim, hidden_dim)
            self.key_proj = nn.Linear(hidden_dim, hidden_dim)
            self.out_proj = nn.Linear(hidden_dim, hidden_dim)
            
            self.norm = nn.LayerNorm(hidden_dim)
            self.dropout = nn.Dropout(dropout)
            
            # Convergence tracking
            self._last_iterations = 0
            self._last_converged = False
            self._last_delta = 0.0

        def forward(self, x: torch.Tensor, vp_value: Optional[float] = None) -> torch.Tensor:
            # VP-aware temperature: higher VP = sharper retrieval
            beta = self.beta
            if vp_value is not None and vp_value > 0:
                beta = self.beta * (1.0 + vp_value * 0.5)
            
            # Handle 3D input (batch, seq, hidden)
            if x.dim() == 3:
                batch_size, seq_len, _ = x.size()
                x_flat = x.view(-1, self.hidden_dim)
                out_flat = self._iterate(x_flat, beta)
                return out_flat.view(batch_size, seq_len, self.hidden_dim)
            
            return self._iterate(x, beta)
        
        def _iterate(self, xi: torch.Tensor, beta: float) -> torch.Tensor:
            keys = self.key_proj(self.patterns)
            
            converged = False
            delta = 0.0
            for i in range(self.max_iterations):
                xi_prev = xi
                queries = self.query_proj(xi)
                scores = torch.matmul(queries, keys.t()) * beta
                attention = F.softmax(scores, dim=-1)
                retrieved = torch.matmul(attention, self.patterns)
                xi = xi + self.dropout(self.out_proj(retrieved))
                xi = self.norm(xi)
                
                delta = (xi - xi_prev).abs().mean().item()
                if delta < self.convergence_threshold:
                    converged = True
                    self._last_iterations = i + 1
                    self._last_converged = True
                    self._last_delta = delta
                    break
            
            if not converged:
                self._last_iterations = self.max_iterations
                self._last_converged = False
                self._last_delta = delta
            
            return xi
        
        def get_convergence_info(self) -> Dict[str, Any]:
            return {
                'iterations': self._last_iterations,
                'converged': self._last_converged,
                'final_delta': self._last_delta,
                'max_iterations': self.max_iterations,
                'threshold': self.convergence_threshold
            }


    class ConceptHead(nn.Module):
        """Concept prediction head for compositional understanding (RCUS)."""
        def __init__(self, hidden_dim: int = 64, num_axioms: int = 18, num_compositions: int = 15):
            super().__init__()
            self.hidden_dim = hidden_dim
            self.num_axioms = num_axioms
            self.num_compositions = num_compositions
            self.axiom_relevance = nn.Linear(hidden_dim, num_axioms)
            self.composition_value = nn.Linear(hidden_dim, num_compositions)
            self.context_embed = nn.Linear(hidden_dim, hidden_dim)

        def forward(self, hidden: torch.Tensor) -> Dict[str, torch.Tensor]:
            return {
                'axiom_relevance': torch.sigmoid(self.axiom_relevance(hidden)),
                'composition_value': self.composition_value(hidden),
                'context': self.context_embed(hidden),
            }


    class OrganismBrain(nn.Module):
        def __init__(self, config: Dict[str, Any]):
            super().__init__()
            self.input_dim = config['input_dim']
            self.hidden_dim = config['hidden_dim']
            self.output_dim = config['output_dim']
            self.vocab_size = config.get('vocab_size', 10000)
            self.use_language_head = config.get('use_language_head', False)
            self.use_concept_head = config.get('use_concept_head', False)
            self.use_attention = config.get('use_attention', False)
            self.dropout_rate = config.get('dropout', 0.1)
            self.num_attention_heads = config.get('num_attention_heads', 4)
            self.num_key_compositions = config.get('num_key_compositions', 15)
            
            # Hopfield layer params
            self.use_hopfield = config.get('use_hopfield', False)
            self.hopfield_patterns = config.get('hopfield_patterns', 32)
            self.hopfield_iterations = config.get('hopfield_iterations', 5)
            self.hopfield_beta = config.get('hopfield_beta', 1.0)
            
            self.fc1 = nn.Linear(self.input_dim, self.hidden_dim)
            if self.use_attention:
                self.attention = MultiHeadAttention(self.hidden_dim, self.num_attention_heads, self.dropout_rate)
                self.attention_norm = nn.LayerNorm(self.hidden_dim)
            if self.use_hopfield:
                self.hopfield = HopfieldLayer(
                    self.hidden_dim, self.hopfield_patterns,
                    self.hopfield_iterations, self.hopfield_beta, self.dropout_rate
                )
            self.fc2 = nn.Linear(self.hidden_dim, self.hidden_dim)
            self.fc3 = nn.Linear(self.hidden_dim, self.output_dim)
            if self.use_language_head:
                self.fc_language = nn.Linear(self.hidden_dim, self.vocab_size)
            if self.use_concept_head:
                self.concept_head = ConceptHead(self.hidden_dim, num_axioms=18, num_compositions=self.num_key_compositions)
            self.dropout = nn.Dropout(self.dropout_rate)

        def forward(self, x: torch.Tensor, vp_value: Optional[float] = None,
                    return_language_logits: bool = True) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
            if x.shape[-1] < self.input_dim:
                pad = torch.zeros(*x.shape[:-1], self.input_dim - x.shape[-1], device=x.device)
                x = torch.cat([x, pad], dim=-1)
            elif x.shape[-1] > self.input_dim:
                x = x[..., :self.input_dim]

            h = F.relu(self.fc1(x))
            h = self.dropout(h)

            if self.use_attention:
                if h.dim() == 2:
                    h = h.unsqueeze(1)
                attn_out = self.attention(h, vp_value=vp_value)
                h = self.attention_norm(h + attn_out)
                h = h.squeeze(1)
            
            # Hopfield iterative refinement
            if self.use_hopfield:
                h = self.hopfield(h, vp_value=vp_value)

            h = F.relu(self.fc2(h))
            h = self.dropout(h)

            action_logits = self.fc3(h)
            action_probs = F.softmax(action_logits, dim=-1)

            language_logits = None
            if self.use_language_head and return_language_logits:
                language_logits = self.fc_language(h)
            return action_probs, language_logits
        
        def get_hidden_state(self, x: torch.Tensor, vp_value: Optional[float] = None) -> torch.Tensor:
            """Get hidden state after full pipeline (fc1 → attention → hopfield → fc2)."""
            if x.shape[-1] < self.input_dim:
                pad = torch.zeros(*x.shape[:-1], self.input_dim - x.shape[-1], device=x.device)
                x = torch.cat([x, pad], dim=-1)
            elif x.shape[-1] > self.input_dim:
                x = x[..., :self.input_dim]
            
            h = F.relu(self.fc1(x))
            h = self.dropout(h)
            
            if self.use_attention:
                if h.dim() == 2:
                    h = h.unsqueeze(1)
                attn_out = self.attention(h, vp_value=vp_value)
                h = self.attention_norm(h + attn_out)
                if h.dim() == 3 and h.size(1) == 1:
                    h = h.squeeze(1)
            
            if self.use_hopfield:
                h = self.hopfield(h, vp_value=vp_value)
            
            h = F.relu(self.fc2(h))
            h = self.dropout(h)
            return h
        
        def get_thought_info(self) -> Optional[Dict[str, Any]]:
            """Get Hopfield convergence info."""
            if self.use_hopfield:
                return self.hopfield.get_convergence_info()
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# 🤝 COCOON ALLIANCE SYSTEM - Preserved Social Structure
# ═══════════════════════════════════════════════════════════════════════════════
# "Connections formed are causeways for rationality"
# 
# The alliance graph represents the emergent social brain. Organisms that formed
# alliances in the engine trusted each other, shared concepts, defended each other.
# This class preserves that relational structure so cocoons can make alliance-aware
# decisions without the full engine.
# ═══════════════════════════════════════════════════════════════════════════════

class CocoonAlliance:
    """
    Lightweight alliance system for standalone cocoons.
    
    Loads pre-computed alliance graph from training and provides:
    - Trust-weighted voting (allies vote together)
    - Alliance membership queries
    - Reputation-based decision weights
    - Social graph traversal
    """
    
    def __init__(self):
        # Load alliance data from embedded payload
        self.alliance_data = _decode_data(_ALLIANCE_B64) or {}
        
        # Core alliance structures
        self.alliances = self.alliance_data.get('alliances', {})
        self.organism_to_alliance = self.alliance_data.get('organism_to_alliance', {})
        self.organism_trust = self.alliance_data.get('organism_trust', {})
        self.organism_reputation = self.alliance_data.get('organism_reputation', {})
        self.organism_stats = self.alliance_data.get('organism_stats', {})
        self.social_graph = self.alliance_data.get('social_graph', {})
        
        # Track alliance-based trust weights for voting
        self._trust_cache = {}
        
        if self.alliances:
            print(f"[ALLIANCE] Loaded social structure: {len(self.alliances)} alliances, "
                  f"{len(self.organism_trust)} trust records")
    
    def get_alliance_id(self, organism_id: str) -> Optional[str]:
        """Get the alliance ID for an organism."""
        return self.organism_to_alliance.get(str(organism_id))
    
    def get_alliance_members(self, organism_id: str) -> List[str]:
        """Get all alliance members for an organism's alliance."""
        alliance_id = self.get_alliance_id(organism_id)
        if not alliance_id:
            return [str(organism_id)]  # Solo - just self
        
        alliance = self.alliances.get(alliance_id, {})
        return alliance.get('members', [str(organism_id)])
    
    def get_trust_score(self, organism_id: str) -> float:
        """Get trust score for an organism (0.0-1.0). Higher = more trustworthy."""
        return self.organism_trust.get(str(organism_id), 0.5)
    
    def get_competition_stats(self, organism_id: str) -> Dict[str, Any]:
        """Get competition stats for an organism."""
        return self.organism_stats.get(str(organism_id), {})
    
    def get_social_connections(self, organism_id: str) -> List[str]:
        """Get organisms this organism is socially connected to."""
        return self.social_graph.get(str(organism_id), [])
    
    def are_allies(self, org1_id: str, org2_id: str) -> bool:
        """Check if two organisms are in the same alliance."""
        alliance1 = self.get_alliance_id(org1_id)
        alliance2 = self.get_alliance_id(org2_id)
        if alliance1 and alliance2:
            return alliance1 == alliance2
        return False
    
    def get_alliance_trust_weight(self, organism_ids: List[str]) -> Dict[str, float]:
        """
        Calculate trust-based voting weights for a group of organisms.
        
        Organisms in the same alliance amplify each other's influence.
        Organisms with higher trust scores get more vote weight.
        Organisms with better competition stats get credibility boosts.
        
        Returns:
            Dict mapping organism_id -> vote_weight (sum to ~1.0)
        """
        cache_key = tuple(sorted(organism_ids))
        if cache_key in self._trust_cache:
            return self._trust_cache[cache_key]
        
        weights = {}
        for org_id in organism_ids:
            org_str = str(org_id)
            base_weight = 1.0
            
            # Trust score factor (0.5-1.5x)
            trust = self.get_trust_score(org_str)
            base_weight *= (0.5 + trust)
            
            # Competition stats factor (wins boost credibility)
            stats = self.get_competition_stats(org_str)
            wins = stats.get('tournament_wins', 0) + stats.get('proton_wins', 0)
            losses = stats.get('tournament_losses', 0) + stats.get('proton_losses', 0)
            if wins + losses > 0:
                win_rate = wins / (wins + losses)
                base_weight *= (0.8 + win_rate * 0.4)  # 0.8-1.2x based on win rate
            
            # Alliance cohesion factor - allies boost each other
            alliance_members = self.get_alliance_members(org_str)
            alliance_bonus = 0.0
            for other_id in organism_ids:
                if other_id != org_str and other_id in alliance_members:
                    # Same alliance = mutual trust boost
                    other_trust = self.get_trust_score(other_id)
                    alliance_bonus += 0.1 * other_trust
            
            base_weight += min(0.5, alliance_bonus)  # Cap alliance boost at 50%
            
            weights[org_str] = max(0.1, base_weight)  # Minimum 10% weight
        
        # Normalize to sum to 1.0
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        
        self._trust_cache[cache_key] = weights
        return weights
    
    def get_alliance_consensus_threshold(self, organism_ids: List[str]) -> float:
        """
        Calculate consensus threshold for alliance-based voting.
        
        Strong alliances require less consensus (they trust each other).
        Weak/no alliances require higher consensus (everyone must agree).
        
        Returns:
            Threshold between 0.5 (simple majority) and 0.9 (strong consensus)
        """
        if not organism_ids:
            return 0.5
        
        # Calculate average alliance strength
        alliance_count = 0
        total_trust = 0.0
        
        for org_id in organism_ids:
            alliance_id = self.get_alliance_id(org_id)
            if alliance_id:
                alliance_count += 1
                total_trust += self.get_trust_score(org_id)
        
        # High alliance membership + high trust = lower threshold
        alliance_ratio = alliance_count / len(organism_ids)
        avg_trust = total_trust / max(1, alliance_count) if alliance_count > 0 else 0.5
        
        # Strong alliances: 0.5 threshold (simple majority)
        # Weak/no alliances: 0.8 threshold (need more agreement)
        threshold = 0.8 - (0.3 * alliance_ratio * avg_trust)
        
        return max(0.5, min(0.8, threshold))
    
    def to_dict(self) -> Dict[str, Any]:
        """Export alliance state for saving."""
        return {
            'alliances': self.alliances,
            'organism_to_alliance': self.organism_to_alliance,
            'organism_trust': self.organism_trust,
            'organism_reputation': self.organism_reputation,
            'organism_stats': self.organism_stats,
            'social_graph': self.social_graph,
        }


class EnsembleVoting:
    @staticmethod
    def majority(actions: List[int]) -> int:
        from collections import Counter
        return Counter(actions).most_common(1)[0][0]

    @staticmethod
    def confidence(action_probs_list: List[np.ndarray]) -> int:
        weights = [float(np.max(p)) for p in action_probs_list]
        weighted = np.zeros_like(action_probs_list[0])
        for p, w in zip(action_probs_list, weights):
            weighted += p * w
        return int(np.argmax(weighted / max(1e-9, sum(weights))))
    
    @staticmethod
    def alliance_weighted(action_probs_list: List[np.ndarray], 
                          organism_ids: List[str],
                          alliance_system: 'CocoonAlliance') -> int:
        """
        Alliance-weighted voting: organisms in same alliance amplify each other.
        
        This preserves the emergent social structure - organisms that formed
        alliances during training vote together as a coalition.
        
        Args:
            action_probs_list: Action probabilities from each organism
            organism_ids: List of organism IDs (parallel to action_probs_list)
            alliance_system: CocoonAlliance instance with trust data
            
        Returns:
            Selected action (int)
        """
        if not alliance_system or not organism_ids:
            # Fallback to standard confidence voting
            return EnsembleVoting.confidence(action_probs_list)
        
        # Get alliance-based trust weights
        trust_weights = alliance_system.get_alliance_trust_weight(organism_ids)
        
        # Weight by both confidence AND alliance trust
        weighted = np.zeros_like(action_probs_list[0])
        total_weight = 0.0
        
        for probs, org_id in zip(action_probs_list, organism_ids):
            # Combine confidence weight with alliance trust weight
            confidence_weight = float(np.max(probs))
            alliance_weight = trust_weights.get(str(org_id), 1.0 / len(organism_ids))
            
            # Final weight = sqrt(confidence * alliance) for balanced influence
            combined_weight = np.sqrt(confidence_weight * alliance_weight)
            
            weighted += probs * combined_weight
            total_weight += combined_weight
        
        return int(np.argmax(weighted / max(1e-9, total_weight)))


class CocoonAgent:
    def __init__(self, voting: str = 'confidence', max_organisms: int = None):
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch required")
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.architecture = _decode_data(_ARCHITECTURE_B64) or {'brain_configs': [], 'organism_names': [], 'is_ensemble': False}
        self.is_ensemble = self.architecture.get('is_ensemble', False)
        self.organism_names = self.architecture.get('organism_names', [])
        # Limit organisms if requested (saves VRAM)
        self.max_organisms = max_organisms
        if max_organisms and len(self.organism_names) > max_organisms:
            self.organism_names = self.organism_names[:max_organisms]
            print(f"[INFO] Limiting to {max_organisms} organisms (of {self.architecture.get('ensemble_size', 1)})")
        self.config = _decode_data(_TRAINING_CONFIG_B64) or {}
        self.learning_rate = self.config.get('learning_rate', 0.005)  # Default matches config.json
        self.batch_size = self.config.get('batch_size', 32)
        self.gamma = self.config.get('gamma', 0.995)  # Default matches config.json
        self.epsilon = self.config.get('epsilon', 0.1)
        self.epsilon_decay = self.config.get('epsilon_decay', 0.99)  # Default matches config.json
        self.epsilon_min = self.config.get('epsilon_min', 0.01)
        self.rl_weight = self.config.get('rl_loss_weight', 0.5)  # Default matches config.json alpha
        self.lang_weight = self.config.get('language_loss_weight', 0.4)  # Default matches config.json beta
        self.concept_weight = self.config.get('concept_loss_weight', 0.1)  # Default matches config.json gamma
        # Add null checks in case decode fails (corrupted data)
        self.vocabulary = _decode_data(_VOCABULARY_B64) or {'word_to_id': {}, 'id_to_word': {}, 'vocab_size': 0}
        self.knowledge_web = _decode_data(_KNOWLEDGE_WEB_B64) or {'concepts': {}, 'relations': []}
        self.brains: List[OrganismBrain] = []
        self.optimizers: List[optim.Adam] = []
        self.experience_buffers: List[ExperienceBuffer] = []
        self.organism_fitness: List[float] = []  # Track per-organism fitness
        self._load_brains()
        self.voting = voting
        self.training_step = 0
        
        # ═══════════════════════════════════════════════════════════════════
        # ⚡ AMP (Mixed Precision) - Faster training on modern GPUs
        # ═══════════════════════════════════════════════════════════════════
        amp_config = self.config.get('optimization', {}).get('amp', {})
        self.amp_enabled = amp_config.get('enabled', False) and torch.cuda.is_available()
        amp_dtype_str = amp_config.get('dtype', 'float16')
        self.amp_dtype = torch.float16 if amp_dtype_str == 'float16' else torch.bfloat16
        if self.amp_enabled:
            self.grad_scaler = torch.amp.GradScaler('cuda')
            print(f"[AMP] Mixed precision enabled: {amp_dtype_str}")
        else:
            self.grad_scaler = None
        
        # ═══════════════════════════════════════════════════════════════════
        # 🧬 MONOLITHIC SUBSYSTEMS - Full Butterfly capabilities
        # ═══════════════════════════════════════════════════════════════════
        
        # Atomic Language System - trackable linguistic units
        self.atomic_languages = []
        try:
            atomic_data = _decode_data(_ATOMIC_LANG_B64)
            
            # Gap 5 Fix: Support per-organism atomic languages
            if isinstance(atomic_data, list):
                # New format: List of organism data
                for data in atomic_data:
                    self.atomic_languages.append(AtomicLanguageSystem.from_dict(data))
            elif isinstance(atomic_data, dict) and 'atoms' in atomic_data:
                # Legacy format: Single merged dict
                self.atomic_languages.append(AtomicLanguageSystem.from_dict(atomic_data))
            
            # Fill missing if any
            while len(self.atomic_languages) < len(self.brains):
                self.atomic_languages.append(AtomicLanguageSystem(organism_id=f"org_{len(self.atomic_languages)}"))
                
            # Set primary for backward compatibility
            self.atomic_language = self.atomic_languages[0] if self.atomic_languages else AtomicLanguageSystem(organism_id="cocoon_default")
            
        except Exception as e:
            print(f"[ERROR] Loading atomic language: {e}")
            self.atomic_language = AtomicLanguageSystem(organism_id="cocoon_ensemble")
            self.atomic_languages = [self.atomic_language]
        
        # Conversation History - context memory
        try:
            conv_data = _decode_data(_CONVERSATION_HISTORY_B64)
            if conv_data and 'messages' in conv_data:
                self.conversation = ConversationHistory.from_dict(conv_data)
            else:
                self.conversation = ConversationHistory()
        except Exception:
            self.conversation = ConversationHistory()
        
        # Enhanced Knowledge Web - semantic relations
        self.enhanced_kb = EnhancedKnowledgeWeb()
        if isinstance(self.knowledge_web, dict):
            self.enhanced_kb.load_from_data(self.knowledge_web)
        
        # VP Runtime - self-regulation and internal state
        self.vp_runtime = VPRuntime(smoothing_factor=0.3, history_size=20)
        self.reward_history: List[float] = []  # For VP stagnation calculation
        
        # ═══════════════════════════════════════════════════════════════════
        # 🤝 ALLIANCE SYSTEM - Preserved Social Structure
        # ═══════════════════════════════════════════════════════════════════
        # "Connections formed are causeways for rationality"
        # Alliances that formed during training represent emergent trust.
        # This enables alliance-weighted voting for coherent ensemble decisions.
        self.alliance_system = CocoonAlliance()
        
        # Update organism fitness with alliance trust weights
        if self.alliance_system.organism_trust and self.is_ensemble:
            self._apply_alliance_trust_to_fitness()
        
        # Default to alliance-weighted voting if alliances exist
        if self.alliance_system.alliances and voting == 'confidence':
            self.voting = 'alliance'
            print(f"[ALLIANCE] Auto-switching to alliance-weighted voting (found {len(self.alliance_system.alliances)} alliances)")
        
        mode = "ENSEMBLE" if self.is_ensemble else "SOLO"
        alliance_info = f", {len(self.alliance_system.alliances)} alliances" if self.alliance_system.alliances else ""
        print(f"[OK] CocoonAgent loaded: {mode}, {len(self.brains)} organism(s){alliance_info}, device={self.device}")
        print(f"     Atomic concepts: {len(self.atomic_language.atoms)}")
        print(f"     Knowledge web: {len(self.enhanced_kb.concepts)} concepts, {len(self.enhanced_kb.relations)} relations")
        print(f"     Conversation history: {self.conversation.turn_count} turns")
        print(f"     VP Runtime: enabled (smoothing={self.vp_runtime.smoothing_factor})")
    
    def _apply_alliance_trust_to_fitness(self):
        """
        Adjust organism fitness based on alliance trust scores.
        
        Organisms with higher trust scores and good competition records
        get their base fitness boosted. This affects voting influence.
        """
        for idx, org_name in enumerate(self.organism_names):
            if idx >= len(self.organism_fitness):
                break
            
            trust = self.alliance_system.get_trust_score(org_name)
            stats = self.alliance_system.get_competition_stats(org_name)
            
            # Trust factor: 0.8-1.2x (centered on 1.0 for 0.5 trust)
            trust_factor = 0.8 + (trust * 0.4)
            
            # Competition factor: based on win record
            wins = stats.get('tournament_wins', 0) + stats.get('proton_wins', 0)
            losses = stats.get('tournament_losses', 0) + stats.get('proton_losses', 0)
            if wins + losses > 5:  # Only apply if significant record
                win_rate = wins / (wins + losses)
                competition_factor = 0.9 + (win_rate * 0.2)  # 0.9-1.1x
            else:
                competition_factor = 1.0
            
            # Apply combined factor
            self.organism_fitness[idx] *= trust_factor * competition_factor

    def _load_brains(self):
        brain_configs = self.architecture.get('brain_configs', [])
        # Respect max_organisms limit
        if self.max_organisms:
            brain_configs = brain_configs[:self.max_organisms]
            brain_data = _BRAIN_DATA[:self.max_organisms]
        else:
            brain_data = _BRAIN_DATA
        for idx, (cfg, brain_b64) in enumerate(zip(brain_configs, brain_data)):
            brain = OrganismBrain(cfg)
            state_bytes = _decode_brain(brain_b64)
            state_dict = torch.load(BytesIO(state_bytes), map_location=self.device, weights_only=False)
            # Fix for torch.compile() models: strip '_orig_mod.' prefix from keys
            # When a model is compiled with torch.compile(), state_dict keys get prefixed
            if any(k.startswith('_orig_mod.') for k in state_dict.keys()):
                state_dict = {k.replace('_orig_mod.', ''): v for k, v in state_dict.items()}
            brain.load_state_dict(state_dict)
            brain.to(self.device)
            brain.eval()
            self.brains.append(brain)
            self.optimizers.append(optim.Adam(brain.parameters(), lr=self.learning_rate))
            self.experience_buffers.append(ExperienceBuffer(self.config.get('buffer_size', 0)))
            # Initialize fitness from config or default
            fitness = cfg.get('fitness', 1.0 + idx * 0.05)
            self.organism_fitness.append(fitness)

    def tokenize(self, text: str) -> List[int]:
        word_to_id = self.vocabulary.get('word_to_id', {})
        unk_id = word_to_id.get('<UNK>', 1)
        return [word_to_id.get(w, unk_id) for w in text.lower().split()]

    def detokenize(self, tokens: List[int]) -> str:
        id_to_word = {int(k): v for k, v in self.vocabulary.get('id_to_word', {}).items()}
        words = []
        for t in tokens:
            w = id_to_word.get(int(t), '<UNK>')
            if w in ['<END>', '<PAD>']:
                break
            words.append(w)
        return ' '.join(words)

    def add_word(self, word: str) -> int:
        """Add a new word to vocabulary dynamically. Returns token ID."""
        word = word.lower().strip()
        if not word:
            return self.vocabulary.get('word_to_id', {}).get('<UNK>', 1)
        
        word_to_id = self.vocabulary.get('word_to_id', {})
        id_to_word = self.vocabulary.get('id_to_word', {})
        
        if word in word_to_id:
            return word_to_id[word]
        
        # Add new word
        new_id = len(word_to_id)
        word_to_id[word] = new_id
        id_to_word[str(new_id)] = word
        self.vocabulary['word_to_id'] = word_to_id
        self.vocabulary['id_to_word'] = id_to_word
        self.vocabulary['vocab_size'] = len(word_to_id)
        print(f"[VOCAB] Learned new word: '{word}' (ID={new_id})")
        return new_id

    def learn_from_text(self, text: str, context_state: Optional[np.ndarray] = None,
                        reward: float = 0.0, vp_value: Optional[float] = None,
                        filter_by_knowledge_web: bool = True):
        """Learn from text input - adds valid words and creates training experience.
        
        Args:
            text: Input text to learn from
            context_state: Optional state vector for experience
            reward: Reward signal for this experience
            vp_value: Violation pressure value
            filter_by_knowledge_web: If True, only learn words that exist in knowledge_web
                                     (matching butterfly_chat's gating behavior)
        """
        words = text.lower().split()
        tokens = []
        learned_count = 0
        
        # Get knowledge_web concepts for filtering
        kw_concepts = self.knowledge_web.get('concepts', {}) if filter_by_knowledge_web else None
        
        for word in words:
            # Clean word (remove punctuation)
            clean_word = ''.join(c for c in word if c.isalnum())
            if len(clean_word) < 2:
                continue
                
            # FIXED: Learn ALL words, not just those in knowledge_web
            # The knowledge_web gate was causing semantic lesson words to be skipped
            # and tokenized as <UNK>, preventing organisms from learning new vocabulary
            if kw_concepts is not None and clean_word not in kw_concepts:
                # Word not in knowledge_web - ADD IT to knowledge_web first, then learn it
                if 'concepts' not in self.knowledge_web:
                    self.knowledge_web['concepts'] = {}
                concept_data = {
                    'category': 'learned',
                    'confidence': 0.3,
                    'source': 'text_learning'
                }
                self.knowledge_web['concepts'][clean_word] = concept_data
                
                # FIXED: Also sync to enhanced_kb so semantic queries see learned concepts
                if hasattr(self, 'enhanced_kb') and self.enhanced_kb is not None:
                    self.enhanced_kb.concepts[clean_word] = concept_data
            
            # Learn all words (removed gate that was skipping words)
            token_id = self.add_word(clean_word)
            tokens.append(token_id)
            learned_count += 1
            
            # Update all organisms' atomic languages (Gap 2 Fix: Actual learning)
            if hasattr(self, 'atomic_languages'):
                for als in self.atomic_languages:
                    als.acquire_concept(clean_word, source='chat_heard', initial_strength=0.2)
                    
        # Gap 4 Fix: Social Learning (Inter-organism teaching)
        if hasattr(self, 'atomic_languages') and len(self.atomic_languages) > 1 and random.random() < 0.2:
            try:
                teacher = random.choice(self.atomic_languages)
                student = random.choice(self.atomic_languages)
                if teacher != student:
                    # Teacher shares a strong concept
                    strong_atoms = [a for a in teacher.atoms.values() if a.strength > 0.7]
                    if strong_atoms:
                        atom = random.choice(strong_atoms)
                        # Student learns if they don't know it or know it weakly
                        if atom.concept_id not in student.atoms or student.atoms[atom.concept_id].strength < 0.3:
                            student.acquire_concept(atom.concept_id, source='peer_teaching', initial_strength=0.3)
            except Exception:
                pass  # Social learning fails silently to not disrupt flow
        
        if learned_count > 0 and filter_by_knowledge_web:
            print(f"[LEARN] Learned {learned_count}/{len(words)} words (knowledge_web gated)")
        
        # Create experience with language targets
        if context_state is None:
            context_state = np.zeros(self.brains[0].input_dim, dtype=np.float32)
        
        # Add as experience for language learning
        if len(tokens) > 1:
            for i in range(len(tokens) - 1):
                self.add_experience(
                    state=context_state,
                    action=0,  # Placeholder
                    reward=reward,
                    next_state=context_state,
                    done=False,
                    input_tokens=tokens[:i+1],
                    target_tokens=[tokens[i+1]],
                    vp_value=vp_value
                )
        return tokens

    def add_concept(self, word: str, category: str = 'learned', confidence: float = 0.5):
        """Add a new concept to knowledge web."""
        if 'concepts' not in self.knowledge_web:
            self.knowledge_web['concepts'] = {}
        
        self.knowledge_web['concepts'][word] = {
            'category': category,
            'confidence': confidence
        }
        # Also add to vocabulary
        self.add_word(word)

    def _pad_state(self, state: np.ndarray) -> np.ndarray:
        """Pad state to match brain input_dim. Handles gym envs with smaller state spaces."""
        expected_dim = self.brains[0].input_dim if self.brains else 25
        state = np.asarray(state, dtype=np.float32).flatten()
        if len(state) < expected_dim:
            # Pad with zeros to match brain input dimension
            padded = np.zeros(expected_dim, dtype=np.float32)
            padded[:len(state)] = state
            return padded
        elif len(state) > expected_dim:
            # Truncate if somehow larger
            return state[:expected_dim]
        return state

    def get_action(self, state: np.ndarray, explore: bool = True, vp_value: Optional[float] = None,
                   action_space_size: Optional[int] = None) -> int:
        """Get action from ensemble or single brain, optionally limited to action_space_size.
        
        If vp_value is None, computes it automatically using VPRuntime.
        State is automatically padded to match brain.input_dim.
        
        For ensembles, uses alliance-weighted voting if alliance data exists,
        otherwise falls back to confidence-weighted voting.
        """
        # Pad state to match brain input dimension
        state = self._pad_state(state)
        
        # Auto-compute VP if not provided
        if vp_value is None:
            vp_data = self.vp_runtime.compute_from_state(state, self.reward_history)
            vp_value = vp_data['violation_pressure']
        
        effective_size = action_space_size if action_space_size else self.brains[0].output_dim
        if explore and random.random() < self.epsilon:
            return random.randint(0, effective_size - 1)
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        if self.is_ensemble:
            probs_list = []
            for brain in self.brains:
                brain.eval()
                with torch.no_grad():
                    probs, _ = brain(state_t, vp_value=vp_value, return_language_logits=False)
                # Slice to action_space_size if needed
                p = probs.cpu().numpy().squeeze(0)
                if action_space_size and len(p) > action_space_size:
                    p = p[:action_space_size]
                    p = p / (p.sum() + 1e-9)  # Re-normalize
                probs_list.append(p)
            
            # Use alliance-weighted voting if available
            if self.voting == 'alliance' and self.alliance_system.alliances:
                return EnsembleVoting.alliance_weighted(
                    probs_list, 
                    self.organism_names[:len(probs_list)],
                    self.alliance_system
                )
            elif self.voting == 'majority':
                actions = [int(np.argmax(p)) for p in probs_list]
                return EnsembleVoting.majority(actions)
            else:
                return EnsembleVoting.confidence(probs_list)
        brain = self.brains[0]
        brain.eval()
        with torch.no_grad():
            probs, _ = brain(state_t, vp_value=vp_value, return_language_logits=False)
        if action_space_size and probs.shape[-1] > action_space_size:
            probs = probs[..., :action_space_size]
        return int(torch.argmax(probs, dim=-1).item())

    def get_continuous_action(self, state: np.ndarray, action_dim: int, 
                              action_low: np.ndarray, action_high: np.ndarray,
                              explore: bool = True) -> np.ndarray:
        """Get continuous action for Box action spaces (e.g., Pendulum, BipedalWalker).
        
        Uses brain output to generate continuous actions in the valid range.
        Maps brain outputs through tanh to get values in [-1, 1], then scales to action bounds.
        """
        # Pad state to match brain input dimension
        state = self._pad_state(state)
        
        # Compute VP
        vp_data = self.vp_runtime.compute_from_state(state, self.reward_history)
        vp_value = vp_data['violation_pressure']
        
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        # Get raw outputs from brain
        brain = self.brains[0]
        brain.eval()
        with torch.no_grad():
            outputs, _ = brain(state_t, vp_value=vp_value, return_language_logits=False)
        
        # Use first action_dim outputs as continuous action values
        raw_action = outputs[0, :action_dim].cpu().numpy()
        
        # Apply tanh to bound to [-1, 1] then scale to action space
        bounded = np.tanh(raw_action)
        
        # Add exploration noise if exploring
        if explore and random.random() < self.epsilon:
            noise = np.random.normal(0, 0.3, size=action_dim)
            bounded = np.clip(bounded + noise, -1.0, 1.0)
        
        # Scale from [-1, 1] to [action_low, action_high]
        action = action_low + (bounded + 1.0) * 0.5 * (action_high - action_low)
        
        return action.astype(np.float32)

    def add_experience(self, state, action, reward, next_state, done,
                        input_tokens=None, target_tokens=None, vp_value=None, organism_idx: Optional[int] = None):
        # Pad states to match brain input dimension
        state = self._pad_state(state)
        next_state = self._pad_state(next_state)
        
        # Track reward for VP stagnation calculation
        self.reward_history.append(reward)
        if len(self.reward_history) > 100:
            self.reward_history = self.reward_history[-100:]
        
        targets = range(len(self.experience_buffers)) if organism_idx is None else [organism_idx]
        for idx in targets:
            if idx < len(self.experience_buffers):
                self.experience_buffers[idx].add(state, action, reward, next_state, done,
                                                  input_tokens=input_tokens, target_tokens=target_tokens, vp_value=vp_value)

    def _language_loss(self, logits: torch.Tensor, target_tokens: List[List[int]], vp_value: Optional[float]):
        if logits is None or len(target_tokens) == 0:
            return None
        targets = torch.LongTensor([t[0] if t else 0 for t in target_tokens]).to(self.device)
        
        # ELASTIC VOCAB: Mask out-of-bounds tokens instead of crashing
        # This allows vocabulary to grow beyond neural network's fixed vocab_size
        vocab_size = logits.shape[-1]
        oob_mask = targets >= vocab_size
        if oob_mask.any():
            targets = targets.clone()
            targets[oob_mask] = 0  # Mark as ignore (ignore_index=0)
        
        # CRITICAL: Temperature scaling to prevent numerical overflow
        # Logits can be HUGE (thousands) which causes exp() overflow in cross_entropy
        logit_max = logits.abs().max().item()
        temperature = max(1.0, logit_max / 50.0)  # Scale down if logits > 50
        logits = logits / temperature
        
        # Additional VP scaling
        if vp_value is not None and vp_value > 0:
            logits = logits / (1.0 + vp_value)
        
        # Final clamp to absolutely safe range
        logits = torch.clamp(logits, -50, 50)
        
        # Label smoothing + entropy bonus (same as trainer.py)
        # This prevents mode collapse to single tokens ("shorten shorten" bug)
        loss = F.cross_entropy(logits, targets, ignore_index=0, label_smoothing=0.1)
        
        # Entropy bonus: encourage exploration in language generation
        # NOTE: In trainer.py, this is scaled by organism's curiosity trait (0.5x to 2x)
        # For cocoon exports, we use the base value (0.01) since curiosity is baked into
        # the exported weights during training. The organism's curiosity influenced training,
        # so the exported model already reflects that exploration bias.
        entropy_bonus = 0.01
        if entropy_bonus > 0:
            probs = F.softmax(logits, dim=-1)
            log_probs = torch.log(probs + 1e-9)
            entropy = -(probs * log_probs).sum(dim=-1).mean()
            loss = loss - entropy_bonus * entropy
        
        # Final NaN/Inf check
        if torch.isnan(loss) or torch.isinf(loss):
            return None
        return loss

    def train_step(self) -> float:
        import sys
        import math
        total = 0.0
        trained = 0
        skipped_nan = 0
        for brain_idx, (brain, opt, buf) in enumerate(zip(self.brains, self.optimizers, self.experience_buffers)):
            if len(buf) < self.batch_size:
                continue
            states, actions, rewards, next_states, dones, in_tok, tgt_tok, vp_vals = buf.sample_batch(self.batch_size)
            vp_val = None
            for v in vp_vals:
                if v is not None:
                    vp_val = v
                    break
            states_t = torch.FloatTensor(states).to(self.device)
            actions_t = torch.LongTensor(actions).to(self.device)
            rewards_t = torch.FloatTensor(rewards).to(self.device)
            next_states_t = torch.FloatTensor(next_states).to(self.device)
            dones_t = torch.BoolTensor(dones).to(self.device)
            
            # Debug: print state info for first brain
            if brain_idx == 0:
                print(f"  [DBG] states shape={states_t.shape}, range=[{states_t.min():.2f},{states_t.max():.2f}]", flush=True)
            
            # Check for NaN in inputs (can happen with bad state data)
            if torch.isnan(states_t).any() or torch.isnan(next_states_t).any():
                continue
            if torch.isnan(rewards_t).any():
                continue

            brain.train()
            
            # Forward pass with optional AMP autocast
            if self.amp_enabled:
                with torch.cuda.amp.autocast(dtype=self.amp_dtype):
                    q_values, lang_logits = brain(states_t, vp_value=vp_val, return_language_logits=True)
            else:
                q_values, lang_logits = brain(states_t, vp_value=vp_val, return_language_logits=True)
            
            # Debug: print stats
            q_min = q_values.min().item()
            q_max = q_values.max().item()
            q_mean = q_values.mean().item()
            
            # Check for NaN in q_values (model instability)
            if torch.isnan(q_values).any():
                print(f"  [NaN] q_values has NaN! brain={brain_idx}", flush=True)
                skipped_nan += 1
                continue
            
            # Clamp actions to valid range for this brain's output dimension
            output_dim = q_values.shape[1]
            actions_t = actions_t.clamp(0, output_dim - 1)
            
            q_sel = q_values.gather(1, actions_t.unsqueeze(1)).squeeze(1)

            brain.eval()
            with torch.no_grad():
                next_q, _ = brain(next_states_t, vp_value=vp_val, return_language_logits=False)
                
                # Check for NaN in next_q
                if torch.isnan(next_q).any():
                    print(f"  [NaN] next_q has NaN! brain={brain_idx}", flush=True)
                    skipped_nan += 1
                    continue
                    
                next_max = next_q.max(1)[0]
            target_q = rewards_t + self.gamma * next_max * (~dones_t)
            
            # Check for NaN in target_q
            if torch.isnan(target_q).any():
                print(f"  [NaN] target_q has NaN! brain={brain_idx}", flush=True)
                skipped_nan += 1
                continue

            rl_loss = F.mse_loss(q_sel, target_q)
            
            # Check for NaN in rl_loss
            if torch.isnan(rl_loss):
                skipped_nan += 1
                continue
            
            # Language loss (with NaN protection in _language_loss)
            lang_loss = self._language_loss(lang_logits, tgt_tok, vp_val)
            
            # Concept loss
            concept_loss = None
            if hasattr(brain, 'use_concept_head') and brain.use_concept_head and hasattr(brain, 'concept_head'):
                brain.train()
                # Get hidden state for concept head - use helper for proper Hopfield routing
                if hasattr(brain, 'get_hidden_state'):
                    h = brain.get_hidden_state(states_t, vp_value=vp_val)
                else:
                    # Fallback for older brains without helper
                    h = F.relu(brain.fc1(states_t))
                    h = brain.dropout(h)
                    if brain.use_attention:
                        if h.dim() == 2:
                            h = h.unsqueeze(1)
                        attn_out = brain.attention(h, vp_value=vp_val)
                        h = brain.attention_norm(h + attn_out)
                        h = h.squeeze(1)
                    h = F.relu(brain.fc2(h))
                    h = brain.dropout(h)
                concept_out = brain.concept_head(h)
                composition_values = concept_out['composition_value']
                predicted_reward = composition_values.mean(dim=-1)
                concept_loss = F.mse_loss(predicted_reward, rewards_t)
                # NaN check for concept loss
                if torch.isnan(concept_loss) or torch.isinf(concept_loss):
                    concept_loss = None

            loss = self.rl_weight * rl_loss
            if lang_loss is not None:
                loss = loss + self.lang_weight * lang_loss
            if concept_loss is not None:
                loss = loss + self.concept_weight * concept_loss

            # Skip if loss is NaN or Inf (numerical instability protection)
            if torch.isnan(loss) or torch.isinf(loss):
                rl_val = rl_loss.item() if not torch.isnan(rl_loss) else float('nan')
                lang_val = lang_loss.item() if lang_loss is not None and not torch.isnan(lang_loss) else 0.0
                concept_val = concept_loss.item() if concept_loss is not None and not torch.isnan(concept_loss) else 0.0
                skipped_nan += 1
                continue

            opt.zero_grad()
            
            # Backward pass with optional AMP scaling
            if self.amp_enabled and self.grad_scaler is not None:
                self.grad_scaler.scale(loss).backward()
                self.grad_scaler.unscale_(opt)
                torch.nn.utils.clip_grad_norm_(brain.parameters(), max_norm=1.0)
                self.grad_scaler.step(opt)
                self.grad_scaler.update()
            else:
                loss.backward()
                torch.nn.utils.clip_grad_norm_(brain.parameters(), max_norm=1.0)
                opt.step()

            loss_val = loss.item()
            if math.isnan(loss_val) or math.isinf(loss_val):
                print(f"  [NaN] loss.item() is NaN/Inf AFTER backward! brain={brain_idx}", flush=True)
                skipped_nan += 1
                continue
            total += loss_val
            trained += 1

        if trained > 0:
            self.training_step += 1
            self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
            result = total / trained
            if skipped_nan > 0:
                print(f"  📈 Training: {trained} brains OK, {skipped_nan} skipped (NaN), loss={result:.4f}")
            return result
        else:
            # WHY did no training happen?
            num_brains = len(self.brains)
            buf_counts = [len(buf) for buf in self.experience_buffers]
            ready = sum(1 for c in buf_counts if c >= self.batch_size)
            print(f"  [DEBUG] trained=0, skipped_nan={skipped_nan}, ready_bufs={ready}/{num_brains}")
            return float('nan') if skipped_nan > 0 else 0.0

    def _get_semantic_related(self, word: str, min_strength: float = 0.3) -> List[str]:
        """Get semantically related words from knowledge web."""
        if not self.knowledge_web:
            return []
        concepts = self.knowledge_web.get('concepts', {})
        # Simple word association: return words in same category
        word_info = concepts.get(word.lower(), {})
        category = word_info.get('category', '')
        related = []
        if category:
            for w, info in concepts.items():
                if info.get('category') == category and w != word.lower():
                    related.append((w, info.get('confidence', 0.5)))
        related.sort(key=lambda x: x[1], reverse=True)
        return [w for w, s in related[:10] if s >= min_strength]

    # ═══════════════════════════════════════════════════════════════════════════════
    # 🎯 SEMANTIC REWARD CALCULATION - Aligned with butterfly_chat.py
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _calculate_semantic_reward(self, user_message: str, organism_response: str,
                                   confidence: float, vp_value: Optional[float] = None) -> float:
        """
        Calculate reward with SEMANTIC AWARENESS - aligned with live butterfly_chat.py.
        
        5-Component Scoring:
        1. Word overlap: Relevance to user message (0.0-0.25)
        2. Coherence: Structural quality, repetition penalty (0.0-0.25)
        3. Length appropriateness: Goldilocks zone (0.0-0.2)
        4. Confidence scaling: Model certainty adjustment (0.0-0.2)
        5. VP adjustment: Network health awareness (±0.1)
        
        CRITICAL: Heavy repetition penalty (unique_ratio < 0.3 → reward = -0.3)
        """
        try:
            # Base reward for generating any response
            reward = 0.3
            
            # Handle empty response
            if not organism_response or len(organism_response.strip()) == 0:
                return -0.1  # Penalty for empty responses
            
            # Normalize text
            user_words = set(user_message.lower().split())
            response_words = organism_response.lower().split()
            response_words_set = set(response_words)
            
            # 1. WORD OVERLAP SCORE (0.0 - 0.25)
            stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                         'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                         'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'who',
                         'this', 'that', 'to', 'of', 'in', 'for', 'on', 'with', 'at'}
            
            user_content = user_words - stopwords
            response_content = response_words_set - stopwords
            
            if user_content and response_content:
                overlap = len(user_content & response_content)
                max_possible = min(len(user_content), len(response_content))
                overlap_score = (overlap / max_possible) * 0.25 if max_possible > 0 else 0.0
            else:
                overlap_score = 0.1  # Small baseline if no meaningful content
            
            reward += overlap_score
            
            # 2. COHERENCE SCORE (0.0 - 0.25)
            coherence_score = 0.0
            
            # Capitalization check
            if organism_response[0].isupper():
                coherence_score += 0.05
            
            # Ending punctuation check
            if organism_response.rstrip()[-1:] in '.!?':
                coherence_score += 0.05
            
            # Echo penalty - don't just repeat the user
            if organism_response.strip().lower() == user_message.strip().lower():
                coherence_score -= 0.1
            
            # Diversity check (CRITICAL for preventing repetition)
            unique_ratio = 1.0
            if len(response_words) > 1:
                unique_ratio = len(response_words_set) / len(response_words)
                coherence_score += unique_ratio * 0.15
                
                # Heavy repetition penalty (aligned with butterfly_chat.py)
                if unique_ratio < 0.5:
                    coherence_score -= (1.0 - unique_ratio) * 0.3
            
            # Multiple word bonus
            if len(response_words) >= 2:
                coherence_score += 0.05
            
            reward += max(0.0, coherence_score)
            
            # 3. LENGTH APPROPRIATENESS (0.0 - 0.2)
            response_length = len(response_words)
            if response_length == 0:
                length_score = 0.0
            elif response_length <= 2:
                length_score = 0.05  # Too short
            elif response_length <= 10:
                length_score = 0.2   # Sweet spot
            elif response_length <= 20:
                length_score = 0.15  # Good
            else:
                length_score = 0.1   # Long is okay
            
            reward += length_score
            
            # 4. CONFIDENCE SCALING (0.0 - 0.2)
            reward += confidence * 0.2
            
            # 5. VP ADJUSTMENT (±0.1) - Network health awareness
            if vp_value is not None:
                if vp_value < 0.25:  # VP0 - Healthy
                    reward += 0.1
                elif vp_value < 0.50:  # VP1 - Stable
                    reward += 0.05
                elif vp_value < 0.75:  # VP2 - Unstable
                    pass  # No adjustment
                else:  # VP3/VP4 - Critical
                    reward -= 0.1
            
            # Final clamping with repetition awareness
            if len(response_words) > 1 and unique_ratio < 0.3:
                # Allow negative for severe repetition
                final_reward = max(-0.3, min(1.0, reward))
            elif len(response_words) > 1 and unique_ratio < 0.5:
                final_reward = max(0.0, min(1.0, reward))
            else:
                final_reward = max(0.05, min(1.0, reward))
            
            return final_reward
            
        except Exception:
            return 0.3  # Safe fallback

    def _get_adaptive_max_length(self, organism_idx: int = 0) -> int:
        """
        Calculate adaptive max response length based on organism experience.
        
        Aligned with butterfly_chat.py and standalone_butterfly_chat.py:
        - experience < 10: short responses (6-8 tokens) - prevents gibberish
        - experience < 50: medium (12-24 tokens)
        - experience < 100: longer (32-64 tokens) 
        - experience >= 100: full length (128 tokens)
        
        This prevents young organisms with small vocabularies from generating
        incoherent long responses full of <UNK> tokens.
        """
        if organism_idx < len(self.experience_buffers):
            experience_count = len(self.experience_buffers[organism_idx])
        else:
            experience_count = 0
        
        vocab_size = len(self.vocabulary.get('word_to_id', {}))
        
        if experience_count < 10:
            return min(8, max(5, vocab_size // 6))
        elif experience_count < 50:
            return min(24, max(12, vocab_size // 4))
        elif experience_count < 100:
            return min(64, max(32, vocab_size // 2))
        else:
            return 128  # Full neural synapse length

    def _get_tfidf_important_words(self) -> List[Tuple[str, float]]:
        """
        Get TF-IDF important words from knowledge web for boosting.
        
        Returns words sorted by importance score.
        """
        if not self.knowledge_web:
            return []
        
        concepts = self.knowledge_web.get('concepts', {})
        important_words = []
        
        for word, info in concepts.items():
            # Use confidence or frequency as importance proxy
            importance = info.get('confidence', 0.5) * info.get('frequency', 1.0)
            if importance > 0.3:
                important_words.append((word, importance))
        
        important_words.sort(key=lambda x: x[1], reverse=True)
        return important_words[:30]  # Top 30 important words

    def generate_response(self, prompt: str, organism_idx: int = 0, max_tokens: int = None,
                          vp_value: Optional[float] = None, temperature: float = 1.0) -> Tuple[str, float]:
        """Generate response with semantic boosting, conversation context, and confidence.
        
        NEURAL SYNAPSE MODE: max_tokens=128 allows rich causation chains!
        MONOLITHIC: Uses atomic language, knowledge web, and conversation history.
        
        ENHANCED: Now uses adaptive max_tokens based on organism experience."""
        if organism_idx >= len(self.brains):
            organism_idx = 0
        brain = self.brains[organism_idx]
        if not brain.use_language_head:
            return "[No language head available]", 0.1
        
        # Use adaptive max length if not specified
        if max_tokens is None:
            max_tokens = self._get_adaptive_max_length(organism_idx)
        
        # Add conversation context to prompt for better coherence
        context_str = self.conversation.get_context_string(n=2)
        augmented_prompt = f"{context_str} {prompt}" if context_str else prompt
        
        tokens = self.tokenize(augmented_prompt)
        id_to_word = {int(k): v for k, v in self.vocabulary.get('id_to_word', {}).items()}
        word_to_id = self.vocabulary.get('word_to_id', {})
        
        actual_vocab_size = len(id_to_word)
        if actual_vocab_size == 0:
            return "[Empty vocabulary]", 0.1
        
        valid_ids = [i for i in range(5, actual_vocab_size) if i in id_to_word and id_to_word[i] not in ['<PAD>', '<UNK>', '<START>', '<END>', '<VP_GATE>']]
        if not valid_ids:
            return "[No valid words in vocabulary]", 0.1
        
        # Build semantic primes from input
        input_semantic_primes = set()
        input_words = prompt.lower().split()
        for word in input_words:
            if word in word_to_id:
                input_semantic_primes.add(word)
            related = self._get_semantic_related(word, min_strength=0.5)
            input_semantic_primes.update(related[:3])
        
        brain.eval()
        generated: List[int] = []
        recent_tokens: List[int] = []
        confidence_scores: List[float] = []
        
        state = np.zeros(brain.input_dim, dtype=np.float32)
        for i, tok in enumerate(tokens[-brain.input_dim:]):
            state[i] = tok / 1000.0
        
        # Get base logits once
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            _, base_lang_logits = brain(state_t, vp_value=vp_value, return_language_logits=True)
        if base_lang_logits is None:
            return "[No language output]", 0.1
        
        base_logits = base_lang_logits.squeeze(0).cpu().numpy()
        
        # Initial semantic priming
        if input_semantic_primes:
            initial_boost = 0.8
            for prime_word in input_semantic_primes:
                prime_token = word_to_id.get(prime_word.lower())
                if prime_token is not None and prime_token < len(base_logits):
                    base_logits[prime_token] += initial_boost
        
        # Gap 2 Fix: Boost words known by THIS organism's AtomicLanguageSystem
        if hasattr(self, 'atomic_languages') and organism_idx < len(self.atomic_languages):
            current_als = self.atomic_languages[organism_idx]
            for atom_id, atom in current_als.atoms.items():
                if atom.strength > 0.4:
                    token_id = word_to_id.get(atom_id)
                    if token_id is not None and token_id < len(base_logits):
                        # Boost proportional to strength (e.g. 0.8 strength -> 0.4 boost)
                        base_logits[token_id] += atom.strength * 0.4
        
        # Generation loop with semantic boosting
        for step in range(max_tokens):
            logits = base_logits.copy()
            logits = logits / max(0.1, temperature)
            
            # Tiered repetition penalty (stronger to fight mode collapse)
            strong_penalty = 8.0   # Very recent tokens get heavily penalized
            moderate_penalty = 4.0 # Older tokens still penalized
            if recent_tokens:
                for i, prev_token in enumerate(recent_tokens):
                    recency = len(recent_tokens) - i
                    if prev_token < len(logits):
                        if recency <= 3:
                            logits[prev_token] -= strong_penalty
                        elif recency <= 8:
                            logits[prev_token] -= moderate_penalty
                        else:
                            logits[prev_token] -= 1.5  # Light penalty for older
            
            # Semantic boosting from last generated word
            if self.knowledge_web and generated:
                last_token = generated[-1]
                last_word = id_to_word.get(last_token, '')
                if last_word:
                    related = self._get_semantic_related(last_word, min_strength=0.3)
                    semantic_boost = 0.5
                    for related_word in related[:5]:
                        related_token = word_to_id.get(related_word.lower())
                        if related_token and related_token < len(logits):
                            if related_token not in recent_tokens:
                                logits[related_token] += semantic_boost
            
            # 📊 TF-IDF IMPORTANT WORD BOOSTING - aligned with standalone_butterfly_chat.py
            tfidf_important = self._get_tfidf_important_words()
            if tfidf_important:
                tfidf_boost = 0.25  # Subtle but meaningful boost
                for important_word, importance_score in tfidf_important[:20]:
                    imp_token = word_to_id.get(important_word.lower())
                    if imp_token is not None and imp_token < len(logits):
                        # Only boost if not recently used
                        if imp_token not in recent_tokens:
                            logits[imp_token] += tfidf_boost * importance_score
            
            # Mask special tokens
            logits[:5] = -1e9
            if actual_vocab_size < len(logits):
                logits[actual_vocab_size:] = -1e9
            
            # Top-k sampling
            top_k = 50
            valid_logits = np.array([logits[i] if i < len(logits) else -1e9 for i in valid_ids])
            top_k_indices = np.argsort(valid_logits)[-top_k:]
            mask = np.full(len(valid_ids), -1e9)
            mask[top_k_indices] = valid_logits[top_k_indices]
            
            # Softmax and sample
            probs = np.exp(mask - np.max(mask))
            probs = probs / (probs.sum() + 1e-9)
            chosen_idx = np.random.choice(len(valid_ids), p=probs)
            next_token = valid_ids[chosen_idx]
            
            confidence_scores.append(float(probs[chosen_idx]))
            
            word = id_to_word.get(next_token, '<UNK>')
            if word in ['<END>', '<PAD>']:
                break
            
            generated.append(next_token)
            recent_tokens.append(next_token)
            if len(recent_tokens) > 20:
                recent_tokens.pop(0)
            
            if len(generated) >= max_tokens:
                break
        
        # Calculate overall confidence
        if confidence_scores:
            avg_conf = sum(confidence_scores) / len(confidence_scores)
        else:
            avg_conf = 0.1
        
        # Diversity bonus
        unique_tokens = len(set(generated))
        diversity = unique_tokens / max(len(generated), 1)
        confidence = (avg_conf * 0.4 + diversity * 0.6)
        
        words = [id_to_word.get(t, '<UNK>') for t in generated]
        return ' '.join(words) if words else "[Empty response]", confidence

    def export_cocoon(self, output_path: str):
        """Export updated cocoon with ALL learned state preserved."""
        import zlib
        import re
        
        # 1) Brain weights (existing)
        new_brain_data = []
        for brain in self.brains:
            buf = BytesIO()
            torch.save(brain.state_dict(), buf)
            compressed = zlib.compress(buf.getvalue(), level=9)
            new_brain_data.append(base64.b64encode(compressed).decode('ascii'))
        
        # 2) Vocabulary (may have grown via learn_from_text)
        vocab_json = json.dumps(self.vocabulary, default=_json_default)
        vocab_compressed = zlib.compress(vocab_json.encode('utf-8'), level=9)
        vocab_b64 = base64.b64encode(vocab_compressed).decode('ascii')
        
        # 3) Conversation history (accumulated during chat)
        conv_data = self.conversation.to_dict() if hasattr(self, 'conversation') else {'messages': [], 'topics': {}, 'turn_count': 0}
        conv_json = json.dumps(conv_data, default=_json_default)
        conv_compressed = zlib.compress(conv_json.encode('utf-8'), level=9)
        conv_b64 = base64.b64encode(conv_compressed).decode('ascii')
        
        # 4) Atomic language states (concept strengths learned during chat)
        atomic_data = []
        if hasattr(self, 'atomic_languages'):
            for als in self.atomic_languages:
                atomic_data.append(als.to_dict() if hasattr(als, 'to_dict') else {})
        elif hasattr(self, 'atomic_language'):
            atomic_data.append(self.atomic_language.to_dict() if hasattr(self.atomic_language, 'to_dict') else {})
        atomic_json = json.dumps(atomic_data, default=_json_default)
        atomic_compressed = zlib.compress(atomic_json.encode('utf-8'), level=9)
        atomic_b64 = base64.b64encode(atomic_compressed).decode('ascii')
        
        # 5) Knowledge web (may have grown via learn_from_text - FIXED: was missing!)
        kw_json = json.dumps(self.knowledge_web, default=_json_default)
        kw_compressed = zlib.compress(kw_json.encode('utf-8'), level=9)
        kw_b64 = base64.b64encode(kw_compressed).decode('ascii')
        
        # Read original source
        with open(__file__, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Replace brain data - use string find/replace instead of regex to avoid issues with large data
        brain_data_py = "[\n" + ",\n".join(f'    "{b}"' for b in new_brain_data) + "\n]"
        
        # Find the start of _BRAIN_DATA
        brain_start = source.find('_BRAIN_DATA = [')
        if brain_start != -1:
            # Find the matching closing bracket
            bracket_depth = 0
            brain_end = brain_start + len('_BRAIN_DATA = ')
            for i, c in enumerate(source[brain_end:], brain_end):
                if c == '[':
                    bracket_depth += 1
                elif c == ']':
                    bracket_depth -= 1
                    if bracket_depth == 0:
                        brain_end = i + 1
                        break
            source = source[:brain_start] + f'_BRAIN_DATA = {brain_data_py}' + source[brain_end:]
        
        # Replace vocabulary - simple string replacement since it's always a single quoted string
        vocab_start = source.find('_VOCABULARY_B64 = "')
        if vocab_start != -1:
            vocab_end = source.find('"', vocab_start + len('_VOCABULARY_B64 = "')) + 1
            source = source[:vocab_start] + f'_VOCABULARY_B64 = "{vocab_b64}"' + source[vocab_end:]
        
        # Replace conversation history
        conv_start = source.find('_CONVERSATION_HISTORY_B64 = "')
        if conv_start != -1:
            conv_end = source.find('"', conv_start + len('_CONVERSATION_HISTORY_B64 = "')) + 1
            source = source[:conv_start] + f'_CONVERSATION_HISTORY_B64 = "{conv_b64}"' + source[conv_end:]
        
        # Replace atomic language state
        atomic_start = source.find('_ATOMIC_LANG_B64 = "')
        if atomic_start != -1:
            atomic_end = source.find('"', atomic_start + len('_ATOMIC_LANG_B64 = "')) + 1
            source = source[:atomic_start] + f'_ATOMIC_LANG_B64 = "{atomic_b64}"' + source[atomic_end:]
        
        # Replace knowledge web (FIXED: was missing - learned concepts were lost!)
        kw_start = source.find('_KNOWLEDGE_WEB_B64 = "')
        if kw_start != -1:
            kw_end = source.find('"', kw_start + len('_KNOWLEDGE_WEB_B64 = "')) + 1
            source = source[:kw_start] + f'_KNOWLEDGE_WEB_B64 = "{kw_b64}"' + source[kw_end:]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(source)
        
        print(f"[OK] Exported updated cocoon to: {output_path}")
        print(f"     Preserved: brain weights, vocabulary ({len(self.vocabulary.get('word_to_id', {}))} words),")
        print(f"     knowledge_web ({len(self.knowledge_web.get('concepts', {}))} concepts),")
        print(f"     conversation ({conv_data.get('turn_count', 0)} turns), atomic language states")

    def export_onnx(self, output_path: str, organism_idx: int = 0):
        """Export a brain as ONNX file for Netron visualization."""
        if organism_idx >= len(self.brains):
            organism_idx = 0
        brain = self.brains[organism_idx]
        brain.eval()
        
        dummy_input = torch.randn(1, brain.input_dim).to(self.device)
        
        try:
            torch.onnx.export(
                brain,
                dummy_input,
                output_path,
                export_params=True,
                opset_version=14,
                do_constant_folding=True,
                input_names=['state'],
                output_names=['action_probs', 'language_logits'] if brain.use_language_head else ['action_probs'],
                dynamic_axes={
                    'state': {0: 'batch_size'},
                    'action_probs': {0: 'batch_size'},
                }
            )
            print(f"[OK] Exported ONNX model to: {output_path}")
            print(f"     View at: https://netron.app/")
            return True
        except Exception as e:
            print(f"[!] ONNX export failed: {e}")
            return False

    def export_torchscript(self, output_path: str, organism_idx: int = 0):
        """Export a brain as TorchScript file for Netron visualization."""
        if organism_idx >= len(self.brains):
            organism_idx = 0
        brain = self.brains[organism_idx]
        brain.eval()
        
        try:
            # Use trace instead of script - more compatible with complex models
            input_dim = getattr(brain, 'input_dim', 25)
            dummy_input = torch.randn(1, input_dim)
            traced = torch.jit.trace(brain, (dummy_input,))
            traced.save(output_path)
            print(f"[OK] Exported TorchScript model to: {output_path}")
            print(f"     View at: https://netron.app/")
            return True
        except Exception as e:
            print(f"[!] TorchScript export failed: {e}")
            return False

    def export_ensemble_onnx(self, output_path: str):
        """Export ALL brains as a SINGLE combined ONNX model."""
        if len(self.brains) == 0:
            print("[!] No brains to export")
            return False
        
        # Create MultiOrganismWrapper that runs all brains and returns all outputs
        class MultiOrganismWrapper(nn.Module):
            def __init__(self, brains, names):
                super().__init__()
                self.brains = nn.ModuleList(brains)
                self.names = names
                self.input_dims = [b.input_dim for b in brains]
                self.max_input_dim = max(self.input_dims)
            
            def forward(self, x: torch.Tensor):
                # x shape: [batch, max_input_dim]
                # Returns tuple of action probs for each organism
                outputs = []
                for brain, in_dim in zip(self.brains, self.input_dims):
                    x_i = x[..., :in_dim] if x.shape[-1] >= in_dim else F.pad(x, (0, in_dim - x.shape[-1]))
                    action_probs, _ = brain(x_i, return_language_logits=False)
                    outputs.append(action_probs)
                return tuple(outputs)
        
        wrapper = MultiOrganismWrapper(self.brains, self.organism_names)
        wrapper.eval()
        
        # Move wrapper to CPU for ONNX export (more portable)
        wrapper = wrapper.cpu()
        
        try:
            dummy_input = torch.randn(1, wrapper.max_input_dim)  # CPU tensor
            output_names = [f"action_{name[:8]}" for name in self.organism_names]
            
            torch.onnx.export(
                wrapper,
                dummy_input,
                output_path,
                input_names=['input'],
                output_names=output_names,
                dynamic_axes={'input': {0: 'batch_size'}},
                opset_version=11
            )
            print(f"[OK] Exported ENSEMBLE ONNX ({len(self.brains)} brains) to: {output_path}")
            print(f"     Outputs: {output_names}")
            print(f"     View at: https://netron.app/")
            
            # Move brains back to original device
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            for brain in self.brains:
                brain.to(device)
            
            return True
        except Exception as e:
            print(f"[!] Ensemble ONNX export failed: {e}")
            return False

    def export_ensemble_torchscript(self, output_path: str):
        """Export ALL brains as a SINGLE combined TorchScript model."""
        if len(self.brains) == 0:
            print("[!] No brains to export")
            return False
        
        # Create MultiOrganismWrapper that runs all brains and returns all outputs
        class MultiOrganismWrapper(nn.Module):
            def __init__(self, brains, names):
                super().__init__()
                self.brains = nn.ModuleList(brains)
                self.names = names
                self.input_dims = [b.input_dim for b in brains]
                self.max_input_dim = max(self.input_dims)
            
            def forward(self, x: torch.Tensor):
                # x shape: [batch, max_input_dim]
                # Returns stacked action probs for all organisms
                outputs = []
                for brain, in_dim in zip(self.brains, self.input_dims):
                    x_i = x[..., :in_dim] if x.shape[-1] >= in_dim else F.pad(x, (0, in_dim - x.shape[-1]))
                    action_probs, _ = brain(x_i, return_language_logits=False)
                    outputs.append(action_probs)
                # Stack outputs: [num_organisms, batch, output_dim]
                return torch.stack(outputs, dim=0)
        
        wrapper = MultiOrganismWrapper(self.brains, self.organism_names)
        wrapper.eval()
        
        # Move wrapper to CPU for export (more portable)
        wrapper = wrapper.cpu()
        
        try:
            dummy_input = torch.randn(1, wrapper.max_input_dim)  # CPU tensor
            traced = torch.jit.trace(wrapper, (dummy_input,))
            traced.save(output_path)
            
            print(f"[OK] Exported ENSEMBLE TorchScript ({len(self.brains)} brains) to: {output_path}")
            print(f"     Output shape: [{len(self.brains)}, batch, output_dim]")
            print(f"     View at: https://netron.app/")
            
            # Move brains back to original device
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            for brain in self.brains:
                brain.to(device)
            
            return True
        except Exception as e:
            print(f"[!] Ensemble TorchScript export failed: {e}")
            return False

    def export_package(self, output_dir: str):
        """
        Export a complete Netron-viewable package:
        - brain_ensemble.onnx (combined model with all organisms)
        - brain_*.onnx (individual brains)
        - README.md with model card
        - vocabulary.json
        - metadata.json
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Export combined ensemble as single ONNX
        ensemble_path = os.path.join(output_dir, "brain_ensemble.onnx")
        self.export_ensemble_onnx(ensemble_path)
        
        # Export each brain as ONNX
        onnx_files = ["brain_ensemble.onnx"]
        for i, (brain, name) in enumerate(zip(self.brains, self.organism_names)):
            onnx_path = os.path.join(output_dir, f"brain_{name}.onnx")
            if self.export_onnx(onnx_path, organism_idx=i):
                onnx_files.append(f"brain_{name}.onnx")
        
        # Export vocabulary
        vocab_path = os.path.join(output_dir, "vocabulary.json")
        with open(vocab_path, 'w', encoding='utf-8') as f:
            json.dump(self.vocabulary, f, indent=2)
        print(f"[OK] Exported vocabulary to: {vocab_path}")
        
        # Export metadata
        metadata = {
            'mode': 'ENSEMBLE' if self.is_ensemble else 'SOLO',
            'num_organisms': len(self.brains),
            'organism_names': self.organism_names,
            'organism_fitness': self.organism_fitness,
            'vocab_size': len(self.vocabulary.get('word_to_id', {})),
            'architecture': self.architecture,
            'training_config': self.config,
        }
        meta_path = os.path.join(output_dir, "metadata.json")
        
        # Handle existing metadata.json (merge if present)
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    existing_meta = json.load(f)
                # Merge: update existing with new metadata
                existing_meta.update(metadata)
                metadata = existing_meta
                print(f"[OK] Merged with existing metadata.json")
            except Exception:
                pass  # If read fails, just overwrite
        
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        print(f"[OK] Exported metadata to: {meta_path}")
        
        # Generate README
        readme = self._generate_readme(onnx_files, metadata)
        readme_path = os.path.join(output_dir, "README.md")
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme)
        print(f"[OK] Generated README to: {readme_path}")
        
        print(f"\n✅ Package exported to: {output_dir}")
        print(f"   Open .onnx files at https://netron.app/ to visualize")

    def _generate_readme(self, onnx_files: List[str], metadata: Dict[str, Any]) -> str:
        """Generate a model card README for the cocoon package."""
        import datetime
        
        organism_table = "| Organism | Fitness | Input Dim | Hidden Dim | Output Dim | Language Head |\n"
        organism_table += "|----------|---------|-----------|------------|------------|---------------|\n"
        
        for i, cfg in enumerate(metadata['architecture'].get('brain_configs', [])):
            name = cfg.get('organism_id', f'org_{i}')
            fitness = metadata['organism_fitness'][i] if i < len(metadata['organism_fitness']) else 1.0
            organism_table += f"| {name} | {fitness:.3f} | {cfg.get('input_dim', 25)} | {cfg.get('hidden_dim', 64)} | {cfg.get('output_dim', 6)} | {'✅' if cfg.get('use_language_head') else '❌'} |\n"
        
        readme = f"""# 🦋 Butterfly Cocoon - Neural Network Model Card

**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 Model Overview

| Property | Value |
|----------|-------|
| Mode | {metadata['mode']} |
| Organisms | {metadata['num_organisms']} |
| Vocabulary Size | {metadata['vocab_size']} words |
| Total Parameters | ~{sum(sum(p.numel() for p in brain.parameters()) for brain in self.brains):,} |

---

## 🧠 Organism Architectures

{organism_table}

---

## 🔬 Network Architecture

Each organism brain consists of:

```
Input (state vector)
    ↓
FC1: Linear(input_dim → hidden_dim) + ReLU + Dropout
    ↓
[Optional] Multi-Head Self-Attention (VP-aware)
    ↓
FC2: Linear(hidden_dim → hidden_dim) + ReLU + Dropout
    ↓
├── FC3: Linear(hidden_dim → output_dim) → Action Probabilities
│
└── [Optional] FC_Language: Linear(hidden_dim → vocab_size) → Language Logits
```

### VP-Aware Attention

The attention mechanism scales scores by Voting Power:
```
attention_scores = (Q @ K.T) / sqrt(d_k) / (1 + vp_value)
```

This allows organisms to modulate their attention based on resource availability.

---

## 📁 Files in This Package

| File | Description |
|------|-------------|
| `README.md` | This model card |
| `metadata.json` | Full architecture and training config |
| `vocabulary.json` | Token vocabulary (word ↔ ID mapping) |
"""
        
        for onnx_file in onnx_files:
            readme += f"| `{onnx_file}` | ONNX model - open at [netron.app](https://netron.app/) |\n"
        
        readme += f"""
---

## 🔍 Visualize with Netron

1. Go to [https://netron.app/](https://netron.app/)
2. Click "Open Model..." or drag-drop an `.onnx` file
3. Explore the neural network architecture

---

## 🚀 Usage

### As Standalone Python

```bash
# Info mode
python cocoon.py --mode info

# Interactive chat
python cocoon.py --mode chat

# OpenAI Gym training
python cocoon.py --mode gym --env CartPole-v1 --episodes 100

# HTTP API server
python cocoon.py --mode serve --port 8080
```

### Load ONNX in Python

```python
import onnxruntime as ort
import numpy as np

session = ort.InferenceSession("brain_org_001.onnx")
state = np.random.randn(1, 25).astype(np.float32)  # 25 dims matches config.json
outputs = session.run(None, {{"state": state}})
action_probs = outputs[0]
```

---

## 📚 Training Configuration

```json
{json.dumps(metadata['training_config'], indent=2)}
```

---

## 🦋 About Butterfly System

The Butterfly System is an evolutionary neural network framework where organisms:
- Evolve through **Highlander battles** (absorption of defeated opponents)
- Form **alliances** for collective survival
- Develop **emergent language** through atomic vocabulary
- Graduate to **cocoons** when proven fit

Learn more: [Convergence Engine](https://github.com/Yufok1/Convergence_Engine)

---

## ⚖️ Attribution

- **Proton Game Arena**: Inspired by Piers Anthony's "Apprentice Adept" (1980-1990)
- **Absorption Mechanic**: Inspired by "Highlander" (1986), dir. Russell Mulcahy
- **Convergence Engine**: [https://github.com/Yufok1/Convergence_Engine](https://github.com/Yufok1/Convergence_Engine)
"""
        
        return readme


# =============================================================================
# 🌐 SPHERE ARENA - 3D Swarm Defense Training Environment
# =============================================================================
# Embedded for portable cocoon training demonstrations

# PyGame/OpenGL imports for sphere arena
try:
    import pygame
    from pygame.locals import *
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False

import math
import time
from enum import Enum, auto
from dataclasses import dataclass, field

# Sphere Arena Constants (matches sphere_arena.py)
SPHERE_RADIUS = 2.0   # Radius of the arena sphere
BALL_RADIUS = 0.08    # Ball size relative to sphere
PADDLE_ANGULAR_RADIUS = 0.25  # Radians - size of circular paddle zone
BALL_SPEED = 0.03     # Initial ball speed
MAX_BALL_SPEED = 0.08
PANEL_SPEED = 0.04    # Radians per frame (organism move speed)
OBSERVATION_SIZE = 25 # Size of observation vector per organism (matches config.json input_dim: 25 base features)
MIN_SPAWN_DISTANCE = 0.3  # Min distance from sphere center for ball spawn

# Command chain settings
BROADCAST_RADIUS = 200
COMMAND_COOLDOWN = 30  # frames
COMMAND_DURATION = 60  # frames command is active

# Training parameters
CATCH_REWARD = 1.0
MISS_PENALTY = -0.5
NEAR_MISS_REWARD = 0.2  # Reward for being close to ball when caught
NEAR_MISS_DISTANCE = 100
TERMINAL_PENALTY = -1.0  # Penalty when game ends
SPHERE_TRAIN_INTERVAL = 100  # Train every N frames
SPHERE_BATCH_SIZE = 32


def _sphere_normalize(v):
    """Normalize a 3D vector."""
    mag = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
    if mag < 1e-8:
        return (0.0, 0.0, 0.0)
    return (v[0]/mag, v[1]/mag, v[2]/mag)


def _sphere_distance(a, b):
    """3D distance between two points."""
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2)


def _sphere_dot(a, b):
    """Dot product of two 3D vectors."""
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]


def _sphere_cross(a, b):
    """Cross product of two 3D vectors."""
    return (
        a[1]*b[2] - a[2]*b[1],
        a[2]*b[0] - a[0]*b[2],
        a[0]*b[1] - a[1]*b[0]
    )


def _spherical_to_cartesian(theta, phi, r=1.0):
    """Convert spherical to cartesian coordinates."""
    x = r * math.sin(phi) * math.cos(theta)
    y = r * math.cos(phi)
    z = r * math.sin(phi) * math.sin(theta)
    return (x, y, z)


def _cartesian_to_spherical(x, y, z):
    """Convert cartesian to spherical coordinates (r, theta, phi)."""
    r = math.sqrt(x*x + y*y + z*z)
    if r < 1e-8:
        return (0, 0, 0)
    theta = math.atan2(z, x)
    phi = math.acos(max(-1, min(1, y / r)))
    return (r, theta, phi)


def _angular_distance(theta1, phi1, theta2, phi2):
    """Great-circle distance between two points on sphere (radians)."""
    p1 = _spherical_to_cartesian(theta1, phi1, 1.0)
    p2 = _spherical_to_cartesian(theta2, phi2, 1.0)
    dot = max(-1.0, min(1.0, _sphere_dot(p1, p2)))
    return math.acos(dot)


def _sphere_reflect(velocity, normal):
    """Reflect velocity off a surface with given normal."""
    dot = _sphere_dot(velocity, normal)
    return (
        velocity[0] - 2 * dot * normal[0],
        velocity[1] - 2 * dot * normal[1],
        velocity[2] - 2 * dot * normal[2]
    )


class SphereGameMode(Enum):
    SWARM_DEFENSE = auto()  # All organisms defend together
    ELIMINATION = auto()     # Individual zones, elimination style


@dataclass
class SphereOrganism:
    """Panel/paddle on the sphere surface. Position is in spherical coords (theta, phi)."""
    idx: int
    theta: float  # Azimuthal angle (0 to 2*pi)
    phi: float    # Polar angle (0 to pi)
    catches: int = 0
    misses: int = 0
    alive: bool = True
    color: Tuple[float, float, float] = (0.2, 0.8, 0.2)
    # Command chain fields
    is_commander: bool = False
    commands_issued: int = 0
    commands_followed: int = 0
    target_theta: Optional[float] = None
    target_phi: Optional[float] = None
    command_timer: int = 0
    # 🎰 TOKEN TUMBLER: Token sequence for language learning
    token_sequence: Optional[deque] = None
    
    def tumble_tokens(self, action: int, reward: float, context: str = 'step'):
        """
        🎰 TOKEN TUMBLER: Generate tokens from action/reward.
        
        Tokens encode the organism's "internal monologue" about what it's doing.
        This creates learnable patterns that correlate with successful behaviors.
        """
        if self.token_sequence is None:
            self.token_sequence = deque(maxlen=128)
        
        # Token vocabulary for sphere arena
        ACTION_BASE = 100       # 100-109: Movement actions
        REWARD_BASE = 110       # 110-119: Reward bins  
        CONTEXT_TOKENS = {
            'step': 120,        # Regular step
            'catch': 121,       # Successful catch!
            'miss': 122,        # Missed ball
            'move_toward': 123, # Moving toward target
            'move_away': 124,   # Moving away
            'commander': 125,   # Became commander
            'follower': 126,    # Following command
            'near_miss': 127,   # Close but didn't catch
            'defend': 128,      # Defensive action
            'idle': 129,        # No action taken
        }
        STREAK_TOKENS = {       # 130-139: Streak markers
            'streak_start': 130,
            'streak_5': 131,
            'streak_10': 132,
            'streak_break': 133,
        }
        
        # Emit context token first (what happened)
        ctx_token = CONTEXT_TOKENS.get(context, 120)
        self.token_sequence.append(ctx_token)
        
        # Emit action token (what organism did)
        self.token_sequence.append(ACTION_BASE + min(9, max(0, action)))
        
        # Emit reward token (how it went)
        # Normalize reward from typical range (-1 to 1) to 0-9
        reward_normalized = (reward + 1.0) / 2.0  # -1..1 -> 0..1
        reward_bin = int(max(0, min(0.999, reward_normalized)) * 10)  # 0-9
        self.token_sequence.append(REWARD_BASE + reward_bin)
    
    @property
    def position(self) -> Tuple[float, float, float]:
        """Get 3D cartesian position on sphere surface (matches sphere_arena.py)."""
        return _spherical_to_cartesian(self.theta, self.phi, SPHERE_RADIUS)
    
    def get_normal(self) -> Tuple[float, float, float]:
        """Get inward-facing normal (toward sphere center)."""
        pos = self.position
        return _sphere_normalize((-pos[0], -pos[1], -pos[2]))


@dataclass
class Ball3D:
    position: Tuple[float, float, float]
    velocity: Tuple[float, float, float]
    radius: float = BALL_RADIUS
    active: bool = True
    bounces: int = 0
    last_catcher: Optional[int] = None


class SphereArena:
    """
    3D Sphere Arena for swarm defense training.
    
    The entire swarm defends the sphere together. Ball bounces inside
    the sphere in full 3D. Any organism can catch - the swarm succeeds
    or fails as ONE.
    
    COMMAND CHAIN SYSTEM:
    - Interceptor becomes COMMANDER
    - Commander broadcasts predicted impact to swarm
    - Best follower who catches = new commander
    - Emergent leadership based on performance!
    """
    
    def __init__(self,
                 agent,
                 organism_indices: Optional[List[int]] = None,
                 max_misses: int = 10,
                 headless: bool = False,
                 seed: Optional[int] = None,
                 mode: SphereGameMode = SphereGameMode.SWARM_DEFENSE,
                 enable_command_chain: bool = True,
                 num_balls: int = 1,
                 enable_training: bool = False,
                 train_interval: int = SPHERE_TRAIN_INTERVAL,
                 verbose: bool = False):
        
        self.agent = agent
        self.mode = mode
        self.headless = headless
        self.max_misses = max_misses
        self.enable_command_chain = enable_command_chain
        self.num_balls = max(1, min(5, num_balls))
        self.enable_training = enable_training
        self.train_interval = train_interval
        self.verbose = verbose
        
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        # Select organisms
        if organism_indices is None:
            self.organism_indices = list(range(len(agent.brains)))
        else:
            self.organism_indices = organism_indices
        
        # Verify agent wiring
        self._verify_agent_wiring()
        
        # Initialize organisms
        self.organisms: List[SphereOrganism] = []
        self._setup_teams()
        
        # Initialize balls
        self.balls: List[Ball3D] = []
        
        # Stats
        self.collective_catches = 0
        self.collective_misses = 0
        self.current_streak = 0
        self.best_streak = 0
        self.total_frames = 0
        
        # Command chain state
        self.current_commander: Optional[int] = None
        self.active_command: Optional[Tuple[float, float, float]] = None
        self.command_frame: int = 0
        self.command_history: List[Dict] = []
        
        # Training state
        self.experience_buffer: List[Dict] = []
        self.training_losses: List[float] = []
        self.prev_observations: Dict[int, np.ndarray] = {}
        self.prev_actions: Dict[int, int] = {}
        
        # Visual effects state
        self.impact_effects: List[Dict] = []  # Red shockwaves on miss
        self.catch_effects: List[Dict] = []   # Green flashes on catch
        self.ball_trails: Dict[int, List[Tuple[float, float, float]]] = {}  # Motion trails
        
        # Display
        self.screen = None
        self.clock = None
        self.camera_angle = 0.0
        self.camera_elevation = 30.0
        self.font = None
        
        if not headless and PYGAME_AVAILABLE:
            self._init_display()
        
        self.reset()
    
    def _verify_agent_wiring(self):
        """Verify agent has required components."""
        if not hasattr(self.agent, 'brains'):
            raise ValueError("Agent must have 'brains' attribute")
        
        if len(self.agent.brains) == 0:
            raise ValueError("Agent has no brains loaded")
        
        # Check brain dimensions
        sample_brain = self.agent.brains[0]
        if hasattr(sample_brain, 'input_dim'):
            if sample_brain.input_dim < OBSERVATION_SIZE:
                print(f"[!] Warning: Brain input_dim ({sample_brain.input_dim}) < OBSERVATION_SIZE ({OBSERVATION_SIZE})")
                print("    Padding observations to match brain input dimension")
    
    def _init_display(self):
        """Initialize pygame and OpenGL display."""
        pygame.init()
        pygame.display.set_caption("🌐 Sphere Arena - Swarm Defense")
        
        self.screen = pygame.display.set_mode((1024, 768), DOUBLEBUF | OPENGL if OPENGL_AVAILABLE else 0)
        self.clock = pygame.time.Clock()
        
        if OPENGL_AVAILABLE:
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            
            glMatrixMode(GL_PROJECTION)
            gluPerspective(45, 1024/768, 0.1, 2000.0)
            glMatrixMode(GL_MODELVIEW)
        
        try:
            self.font = pygame.font.Font(None, 36)
        except Exception:
            self.font = None
    
    def _setup_teams(self):
        """Set up panels on sphere surface using spherical coordinates."""
        self.organisms = []
        
        num_organisms = len(self.organism_indices)
        
        for i, idx in enumerate(self.organism_indices):
            # Distribute panels evenly on sphere surface (Fibonacci spiral)
            phi = math.acos(1 - 2 * (i + 0.5) / num_organisms)  # Polar angle
            theta = math.pi * (1 + 5**0.5) * i  # Azimuthal angle
            
            # Generate unique color based on organism characteristics
            color = self._generate_organism_color(idx, i, num_organisms)
            
            org = SphereOrganism(
                idx=idx,
                theta=theta,
                phi=phi,
                color=color
            )
            self.organisms.append(org)
    
    def _generate_organism_color(self, org_idx: int, position_idx: int, total_organisms: int) -> Tuple[float, float, float]:
        """
        Generate a unique color for an organism based on its characteristics.
        
        Color encoding (HSV-based):
        - Hue: Derived from brain weights hash (neural "personality")
        - Saturation: Based on position in swarm (spatial identity)
        - Value: Always high for visibility (0.8-1.0)
        
        This creates infinite unique colors that encode organism identity.
        """
        import hashlib
        
        # Extract brain characteristics for hue
        brain_hash = 0.0
        if hasattr(self.agent, 'brains') and org_idx < len(self.agent.brains):
            brain = self.agent.brains[org_idx]
            if hasattr(brain, 'parameters'):
                # Hash first few weight values for consistent color
                try:
                    params = list(brain.parameters())
                    if params:
                        first_weights = params[0].data.flatten()[:16].tolist()
                        weight_str = ','.join(f'{w:.4f}' for w in first_weights)
                        brain_hash = int(hashlib.md5(weight_str.encode()).hexdigest()[:8], 16)
                except Exception:
                    brain_hash = org_idx * 12345
        else:
            brain_hash = org_idx * 12345
        
        # Hue from brain characteristics (0-1)
        # Use golden ratio for maximum hue spread
        golden_ratio = (1 + 5**0.5) / 2
        hue = (brain_hash * golden_ratio) % 1.0
        
        # Saturation from spatial position (0.7-1.0 for vibrancy)
        if total_organisms > 1:
            spatial_factor = position_idx / (total_organisms - 1)
        else:
            spatial_factor = 0.5
        saturation = 0.7 + 0.3 * (1 - abs(2 * spatial_factor - 1))  # Peak at center
        
        # Value always high for visibility
        value = 0.85 + 0.15 * ((org_idx * 7) % 10) / 10.0
        
        # Convert HSV to RGB
        return self._hsv_to_rgb(hue, saturation, value)
    
    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[float, float, float]:
        """Convert HSV color to RGB."""
        if s == 0.0:
            return (v, v, v)
        
        i = int(h * 6.0)
        f = (h * 6.0) - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))
        i = i % 6
        
        if i == 0:
            return (v, t, p)
        elif i == 1:
            return (q, v, p)
        elif i == 2:
            return (p, v, t)
        elif i == 3:
            return (p, q, v)
        elif i == 4:
            return (t, p, v)
        else:
            return (v, p, q)
    
    def reset(self):
        """Reset the arena for a new game."""
        # Reset organism positions
        self._setup_teams()
        
        # Reset balls
        self.balls = []
        for _ in range(self.num_balls):
            self._spawn_ball()
        
        # Reset stats
        self.collective_catches = 0
        self.collective_misses = 0
        self.current_streak = 0
        
        # Reset command chain
        self.current_commander = None
        self.active_command = None
        self.command_frame = 0
        
        # Clear training state
        self.experience_buffer = []
        self.prev_observations = {}
        self.prev_actions = {}
        
        return self._get_observations()
    
    def _spawn_ball(self):
        """Spawn a new ball inside the sphere (matches sphere_arena.py)."""
        # Random position inside sphere (not too close to center or edge)
        while True:
            x = random.uniform(-SPHERE_RADIUS * 0.5, SPHERE_RADIUS * 0.5)
            y = random.uniform(-SPHERE_RADIUS * 0.5, SPHERE_RADIUS * 0.5)
            z = random.uniform(-SPHERE_RADIUS * 0.5, SPHERE_RADIUS * 0.5)
            dist = math.sqrt(x*x + y*y + z*z)
            if dist > MIN_SPAWN_DISTANCE and dist < SPHERE_RADIUS * 0.7:
                break
        
        # Random velocity toward a random point on sphere surface
        target_theta = random.uniform(0, 2 * math.pi)
        target_phi = random.uniform(0.3, math.pi - 0.3)
        target = _spherical_to_cartesian(target_theta, target_phi, SPHERE_RADIUS)
        
        # Direction from ball to target
        dx = target[0] - x
        dy = target[1] - y
        dz = target[2] - z
        vel = _sphere_normalize((dx, dy, dz))
        vel = (vel[0] * BALL_SPEED, vel[1] * BALL_SPEED, vel[2] * BALL_SPEED)
        
        ball = Ball3D(position=(x, y, z), velocity=vel)
        self.balls.append(ball)
        
        if self.verbose:
            print(f"[SPHERE] Spawned ball at ({x:.1f}, {y:.1f}, {z:.1f})")
    
    def _get_observations(self) -> Dict[int, np.ndarray]:
        """Get observation for each organism."""
        observations = {}
        
        for org in self.organisms:
            if not org.alive:
                continue
            
            obs = self._get_observation(org)
            observations[org.idx] = obs
        
        return observations
    
    def _get_observation(self, org: SphereOrganism) -> np.ndarray:
        """Build observation vector for single organism."""
        obs = np.zeros(OBSERVATION_SIZE, dtype=np.float32)
        
        # Own position (normalized) [0:3]
        pos = org.position
        obs[0] = pos[0] / SPHERE_RADIUS
        obs[1] = pos[1] / SPHERE_RADIUS
        obs[2] = pos[2] / SPHERE_RADIUS
        
        # Own spherical coords (normalized) [3:5]
        obs[3] = org.theta / (2 * math.pi)
        obs[4] = org.phi / math.pi
        
        # Nearest ball info [5:11]
        if self.balls:
            nearest_ball = min(self.balls, key=lambda b: _sphere_distance(pos, b.position))
            obs[5] = nearest_ball.position[0] / SPHERE_RADIUS
            obs[6] = nearest_ball.position[1] / SPHERE_RADIUS
            obs[7] = nearest_ball.position[2] / SPHERE_RADIUS
            obs[8] = nearest_ball.velocity[0] / BALL_SPEED
            obs[9] = nearest_ball.velocity[1] / BALL_SPEED
            obs[10] = nearest_ball.velocity[2] / BALL_SPEED
        
            # Angular distance to ball's projected sphere position [11:13]
            _, ball_theta, ball_phi = _cartesian_to_spherical(*nearest_ball.position)
            ang_dist = _angular_distance(org.theta, org.phi, ball_theta, ball_phi)
            obs[11] = ang_dist / math.pi  # Normalized angular distance
            obs[12] = 1.0 if ang_dist <= PADDLE_ANGULAR_RADIUS else 0.0  # In catch range?
        
        # Command chain info [13:17]
        if self.enable_command_chain and self.active_command:
            obs[13] = self.active_command[0] / SPHERE_RADIUS
            obs[14] = self.active_command[1] / SPHERE_RADIUS
            obs[15] = self.active_command[2] / SPHERE_RADIUS
            obs[16] = 1.0 if org.is_commander else 0.0
        
        # Game state [17:20]
        obs[17] = self.collective_catches / 100.0
        obs[18] = self.collective_misses / self.max_misses
        obs[19] = self.current_streak / 20.0
        
        # Nearest teammate angular distance [20:23]
        min_teammate_dist = float('inf')
        for other in self.organisms:
            if other.idx != org.idx and other.alive:
                d = _angular_distance(org.theta, org.phi, other.theta, other.phi)
                if d < min_teammate_dist:
                    min_teammate_dist = d
        
        obs[20] = min_teammate_dist / math.pi if min_teammate_dist < float('inf') else 1.0
        obs[21] = len([o for o in self.organisms if o.alive]) / 10.0  # Alive count
        obs[22] = self.total_frames / 1000.0  # Time pressure
        
        return obs
    
    def _get_organism_action(self, org: SphereOrganism, observation: np.ndarray) -> Tuple[int, Tuple[float, float]]:
        """
        Query brain for action - 100% BRAIN-DRIVEN, NO CHEATING!
        
        Returns (action_idx, (d_theta, d_phi)) movement deltas.
        The brain must LEARN to chase the ball through training.
        """
        brain = self.agent.brains[org.idx]
        
        # Prepare input - pad if needed
        if hasattr(brain, 'input_dim') and brain.input_dim > len(observation):
            padded = np.zeros(brain.input_dim, dtype=np.float32)
            padded[:len(observation)] = observation
            obs_tensor = torch.tensor(padded, dtype=torch.float32).unsqueeze(0)
        else:
            obs_tensor = torch.tensor(observation, dtype=torch.float32).unsqueeze(0)
        
        # Move to device if needed
        if hasattr(self.agent, 'device'):
            obs_tensor = obs_tensor.to(self.agent.device)
        
        # VP integration if available
        vp_value = 0.5
        if hasattr(self.agent, 'vp_runtime'):
            try:
                vp_data = self.agent.vp_runtime.compute_from_state(observation, [])
                vp_value = vp_data.get('violation_pressure', 0.5)
            except Exception:
                pass
        
        try:
            # Get action from brain
            brain.eval()
            with torch.no_grad():
                output = brain(obs_tensor, vp_value=vp_value) if hasattr(brain, 'forward') else brain(obs_tensor)
                if isinstance(output, tuple):
                    output = output[0]
            
            probs = output[0].cpu().numpy().flatten()
            n_actions = len(probs)
            
            # Discrete action from argmax for logging
            action_idx = int(np.argmax(probs))
            
            # ═══════════════════════════════════════════════════════════
            # 100% BRAIN-DRIVEN MOVEMENT - NO CHEATING!
            # ═══════════════════════════════════════════════════════════
            # Divide action space into directional quadrants
            # Brain must LEARN which actions mean which directions
            
            if n_actions >= 4:
                quarter = n_actions // 4
                
                # Sum probabilities in each directional bucket
                up_weight = np.sum(probs[:quarter])           # Move -phi (up)
                right_weight = np.sum(probs[quarter:2*quarter])  # Move +theta (right)
                down_weight = np.sum(probs[2*quarter:3*quarter]) # Move +phi (down)
                left_weight = np.sum(probs[3*quarter:])          # Move -theta (left)
                
                # Net movement from brain's "vote"
                theta_vote = (right_weight - left_weight) * 2.0
                phi_vote = (down_weight - up_weight) * 2.0
                
                # Confidence affects speed
                confidence = float(np.max(probs))
                speed = PANEL_SPEED * (0.5 + confidence)
                
                # Command component (if available) - following orders is learned behavior
                cmd_theta_dir = 0.0
                cmd_phi_dir = 0.0
                has_command = 0.0
                
                if self.enable_command_chain and self.active_command is not None:
                    # Get command target in spherical coords
                    _, cmd_theta, cmd_phi = _cartesian_to_spherical(*self.active_command)
                    cmd_bias_theta = cmd_theta - org.theta
                    while cmd_bias_theta > math.pi: cmd_bias_theta -= 2*math.pi
                    while cmd_bias_theta < -math.pi: cmd_bias_theta += 2*math.pi
                    cmd_bias_phi = cmd_phi - org.phi
                    
                    if abs(cmd_bias_theta) > 0.05 or abs(cmd_bias_phi) > 0.05:
                        has_command = 1.0
                        cmd_theta_dir = np.sign(cmd_bias_theta) if abs(cmd_bias_theta) > 0.05 else 0
                        cmd_phi_dir = np.sign(cmd_bias_phi) if abs(cmd_bias_phi) > 0.05 else 0
                
                command_weight = 0.2 * has_command
                brain_weight = 1.0 - command_weight
                
                # Final movement: brain controls everything
                d_theta = speed * (
                    brain_weight * np.tanh(theta_vote) +
                    command_weight * cmd_theta_dir
                )
                d_phi = speed * (
                    brain_weight * np.tanh(phi_vote) +
                    command_weight * cmd_phi_dir
                )
            else:
                # Few actions - use brain output directly
                d_theta = PANEL_SPEED * np.tanh(probs[0] if len(probs) > 0 else 0)
                d_phi = PANEL_SPEED * np.tanh(probs[1] if len(probs) > 1 else 0)
            
            return action_idx, (d_theta, d_phi)
            
        except Exception as e:
            # Fallback on error: stay still (no cheating!)
            return 0, (0.0, 0.0)
    
    def step(self) -> Tuple[Dict[int, np.ndarray], Dict[int, float], bool, Dict]:
        """Execute one step of the game."""
        self.total_frames += 1
        rewards = {org.idx: 0.0 for org in self.organisms if org.alive}
        
        # Store previous observations for training
        if self.enable_training:
            observations = self._get_observations()
            for idx, obs in observations.items():
                self.prev_observations[idx] = obs.copy()
        
        # Get actions from all organisms - panels move on sphere surface
        for org in self.organisms:
            if not org.alive:
                continue
            
            obs = self._get_observation(org)
            action_idx, (d_theta, d_phi) = self._get_organism_action(org, obs)
            
            if self.enable_training:
                self.prev_actions[org.idx] = action_idx
            
            # Apply angular movement - panels slide on sphere surface (already computed by brain)
            # Update spherical coords
            org.theta = (org.theta + d_theta) % (2 * math.pi)
            org.phi = max(0.1, min(math.pi - 0.1, org.phi + d_phi))  # Keep away from poles
            
            # 🎰 TOKEN TUMBLER: Generate movement tokens every frame
            movement_magnitude = abs(d_theta) + abs(d_phi)
            if movement_magnitude > 0.001:
                # Determine movement context
                if obs[12] > 0.5:  # In catch range (from observation)
                    ctx = 'defend'
                elif movement_magnitude > PANEL_SPEED * 1.5:
                    ctx = 'move_toward'
                else:
                    ctx = 'step'
                
                # Only tumble every 5 frames to avoid token flood
                if self.total_frames % 5 == 0:
                    # Small step reward based on staying alive
                    step_reward = 0.01 * (1.0 - self.collective_misses / self.max_misses)
                    org.tumble_tokens(action=action_idx, reward=step_reward, context=ctx)
            
            if self.verbose and self.total_frames % 60 == 0:
                pos = org.position
                print(f"[SPHERE] Panel #{org.idx}: theta={org.theta:.2f}, phi={org.phi:.2f}, pos=({pos[0]:.0f}, {pos[1]:.0f}, {pos[2]:.0f})")
        
        # Update balls
        for ball_idx, ball in enumerate(self.balls):
            if not ball.active:
                continue
            
            # 🎯 VISUAL EFFECT: Track ball trail for motion blur
            if ball_idx not in self.ball_trails:
                self.ball_trails[ball_idx] = []
            self.ball_trails[ball_idx].append(ball.position)
            # Keep last 8 positions for trail
            if len(self.ball_trails[ball_idx]) > 8:
                self.ball_trails[ball_idx].pop(0)
            
            # Move ball
            new_x = ball.position[0] + ball.velocity[0]
            new_y = ball.position[1] + ball.velocity[1]
            new_z = ball.position[2] + ball.velocity[2]
            
            # Check sphere boundary - this is where panels can catch!
            dist = math.sqrt(new_x**2 + new_y**2 + new_z**2)
            if dist >= SPHERE_RADIUS - BALL_RADIUS:
                # Ball hitting sphere boundary - convert to spherical coords
                _, ball_theta, ball_phi = _cartesian_to_spherical(new_x, new_y, new_z)
                
                # SWARM DEFENSE: Check if ANY organism intercepts (exact sphere_arena.py logic)
                catcher = None
                min_catch_dist = float('inf')
                
                for org in self.organisms:
                    if not org.alive:
                        continue
                    
                    # Great-circle angular distance
                    ang_dist = _angular_distance(org.theta, org.phi, ball_theta, ball_phi)
                    
                    if ang_dist <= PADDLE_ANGULAR_RADIUS and ang_dist < min_catch_dist:
                        min_catch_dist = ang_dist
                        catcher = org
                
                if catcher is not None:
                    # SWARM CATCH! - reflect ball and handle rewards (DO NOT respawn)
                    # Reflect ball FIRST
                    normal = _sphere_normalize((new_x, new_y, new_z))
                    ball.velocity = _sphere_reflect(ball.velocity, normal)
                    
                    # Speed up slightly (like sphere_arena.py)
                    speed = math.sqrt(ball.velocity[0]**2 + ball.velocity[1]**2 + ball.velocity[2]**2)
                    new_speed = min(speed * 1.02, MAX_BALL_SPEED)
                    if speed > 0:
                        scale_v = new_speed / speed
                        ball.velocity = (ball.velocity[0]*scale_v, ball.velocity[1]*scale_v, ball.velocity[2]*scale_v)
                    
                    # Now handle rewards/tokens (but don't respawn ball!)
                    self._handle_catch(catcher, ball, rewards)
                else:
                    # SWARM MISS - reflect and penalize
                    normal = _sphere_normalize((new_x, new_y, new_z))
                    ball.velocity = _sphere_reflect(ball.velocity, normal)
                    ball.bounces += 1
                    self._handle_miss(ball, rewards)
                
                # Project back inside sphere
                scale = (SPHERE_RADIUS - BALL_RADIUS * 2) / dist
                new_x *= scale
                new_y *= scale
                new_z *= scale
            
            ball.position = (new_x, new_y, new_z)
        
        # Process command chain
        if self.enable_command_chain:
            self._process_command_chain()
        
        # Training step
        if self.enable_training and self.total_frames % self.train_interval == 0:
            self._do_training_step()
        
        # Check game over
        done = self.collective_misses >= self.max_misses
        
        if done and self.enable_training:
            # Terminal penalty
            for idx in rewards:
                rewards[idx] += TERMINAL_PENALTY
        
        observations = self._get_observations()
        info = {
            'catches': self.collective_catches,
            'misses': self.collective_misses,
            'streak': self.current_streak,
            'commander': self.current_commander
        }
        
        return observations, rewards, done, info
    
    def _handle_catch(self, org: SphereOrganism, ball: Ball3D, rewards: Dict[int, float]):
        """Handle a successful catch."""
        self.collective_catches += 1
        self.current_streak += 1
        self.best_streak = max(self.best_streak, self.current_streak)
        org.catches += 1
        
        # ✨ VISUAL EFFECT: Green ripple/flash on catch
        self.catch_effects.append({
            'position': ball.position,
            'frame': self.total_frames,
            'radius': 0.0,
            'max_radius': PADDLE_ANGULAR_RADIUS * SPHERE_RADIUS * 2,
            'color': org.color,  # Use catcher's color
            'intensity': 1.0
        })
        
        # =================================================================
        # ASSOCIATIVE REWARD SYSTEM
        # Rewards based on individual + group + contextual performance
        # =================================================================
        
        # Base catch reward
        base_reward = CATCH_REWARD
        
        # 1. STREAK BONUS: Exponential reward for maintaining streaks
        streak_multiplier = 1.0 + 0.1 * min(self.current_streak, 10)  # Up to 2x at streak 10
        
        # 2. GROUP COHESION BONUS: Reward if team is clustered near ball
        avg_distance_to_ball = 0.0
        nearby_count = 0
        for other in self.organisms:
            if other.alive:
                dist = _angular_distance(other.theta, other.phi, 
                    *_cartesian_to_spherical(*ball.position)[1:])
                avg_distance_to_ball += dist
                if dist < PADDLE_ANGULAR_RADIUS * 3:  # Within 3x catch range
                    nearby_count += 1
        avg_distance_to_ball /= max(1, len([o for o in self.organisms if o.alive]))
        
        cohesion_bonus = 0.2 * (nearby_count / max(1, len(self.organisms)))  # Up to +0.2
        
        # 3. CONTRIBUTION RATIO: Historical catch rate affects reward
        total_team_catches = sum(o.catches for o in self.organisms)
        if total_team_catches > 0:
            contribution_ratio = org.catches / total_team_catches
            # High contributors get bonus, but don't punish new catchers
            contribution_bonus = 0.1 * min(1.0, contribution_ratio * len(self.organisms))
        else:
            contribution_bonus = 0.1  # First catch gets bonus
        
        # 4. SURVIVAL BONUS: Reward for keeping the game alive
        survival_ratio = 1.0 - (self.collective_misses / self.max_misses)
        survival_bonus = 0.15 * survival_ratio
        
        # Final catcher reward
        total_reward = base_reward * streak_multiplier + cohesion_bonus + contribution_bonus + survival_bonus
        rewards[org.idx] += total_reward
        
        # 🎰 TOKEN TUMBLER: Generate catch tokens for catcher!
        org.tumble_tokens(action=0, reward=total_reward, context='catch')
        
        # Streak milestone tokens
        if self.current_streak == 5:
            org.token_sequence.append(131)  # streak_5
        elif self.current_streak == 10:
            org.token_sequence.append(132)  # streak_10
        
        # =================================================================
        # ASSOCIATIVE REWARDS FOR NON-CATCHERS
        # Group members benefit from collective success
        # =================================================================
        for other in self.organisms:
            if other.idx != org.idx and other.alive:
                other_reward = 0.0
                
                # A. PROXIMITY REWARD: Being close to ball = ready to help
                dist = _sphere_distance(other.position, ball.position)
                if dist < NEAR_MISS_DISTANCE:
                    other_reward += NEAR_MISS_REWARD
                    other.tumble_tokens(action=0, reward=NEAR_MISS_REWARD, context='near_miss')
                elif dist < NEAR_MISS_DISTANCE * 2:
                    # Partial reward for being somewhat close
                    proximity_reward = NEAR_MISS_REWARD * 0.5 * (1 - dist / (NEAR_MISS_DISTANCE * 2))
                    other_reward += proximity_reward
                
                # B. FORMATION REWARD: Being in good defensive position
                # Calculate coverage quality (spread across sphere)
                angular_dist = _angular_distance(other.theta, other.phi, org.theta, org.phi)
                if angular_dist > math.pi / 4:  # Good spread from catcher
                    other_reward += 0.05  # Formation bonus
                
                # C. COLLECTIVE SUCCESS SHARE: Everyone benefits from catches
                collective_share = 0.1 * survival_ratio  # Shared success
                other_reward += collective_share
                
                if other_reward > 0:
                    rewards[other.idx] += other_reward
                    other.tumble_tokens(action=0, reward=other_reward, context='follower')
        
        # Command chain - catcher becomes new commander
        if self.enable_command_chain:
            old_commander = self.current_commander
            self.current_commander = org.idx
            org.is_commander = True
            org.commands_issued += 1
            
            # 🎰 TOKEN TUMBLER: Commander transition tokens
            org.tumble_tokens(action=0, reward=0.5, context='commander')
            
            # Clear old commander
            for o in self.organisms:
                if o.idx != org.idx:
                    o.is_commander = False
            
            # Log command transition
            self.command_history.append({
                'frame': self.total_frames,
                'new_commander': org.idx,
                'old_commander': old_commander,
                'catches': org.catches
            })
        
        # Update ball state (don't respawn - ball already reflected in step())
        ball.last_catcher = org.idx
        ball.bounces = 0
        
        if self.verbose:
            print(f"[SPHERE] ✓ Catch by Org #{org.idx}! Streak: {self.current_streak} Reward: {total_reward:.2f}")
    
    def _handle_miss(self, ball: Ball3D, rewards: Dict[int, float]):
        """Handle a miss with associative penalties."""
        self.collective_misses += 1
        old_streak = self.current_streak
        self.current_streak = 0
        
        # 💥 VISUAL EFFECT: Red shockwave on miss impact
        # Project ball position to sphere surface for impact point
        dist = math.sqrt(ball.position[0]**2 + ball.position[1]**2 + ball.position[2]**2)
        if dist > 0:
            impact_pos = (
                ball.position[0] * SPHERE_RADIUS / dist,
                ball.position[1] * SPHERE_RADIUS / dist,
                ball.position[2] * SPHERE_RADIUS / dist
            )
        else:
            impact_pos = (SPHERE_RADIUS, 0, 0)
        
        self.impact_effects.append({
            'position': impact_pos,
            'frame': self.total_frames,
            'radius': 0.0,
            'max_radius': PADDLE_ANGULAR_RADIUS * SPHERE_RADIUS * 3,  # Bigger shockwave
            'intensity': 1.0,
            'streak_broken': old_streak  # Larger effect if streak was broken
        })
        
        # =================================================================
        # ASSOCIATIVE PENALTY SYSTEM
        # Penalties based on proximity and responsibility
        # =================================================================
        
        # Get ball position for responsibility calculation
        _, ball_theta, ball_phi = _cartesian_to_spherical(*ball.position)
        
        # Calculate each organism's "responsibility" for the miss
        responsibilities = {}
        total_responsibility = 0.0
        
        for org in self.organisms:
            if not org.alive:
                continue
            
            # Angular distance to ball = inverse responsibility
            ang_dist = _angular_distance(org.theta, org.phi, ball_theta, ball_phi)
            
            # Closer organisms are more responsible (exponential falloff)
            responsibility = math.exp(-ang_dist / PADDLE_ANGULAR_RADIUS)
            responsibilities[org.idx] = responsibility
            total_responsibility += responsibility
        
        # Normalize responsibilities
        if total_responsibility > 0:
            for idx in responsibilities:
                responsibilities[idx] /= total_responsibility
        
        # Apply proportional penalties
        base_penalty = abs(MISS_PENALTY)
        
        for org in self.organisms:
            if not org.alive:
                continue
            
            # Individual responsibility-based penalty
            resp = responsibilities.get(org.idx, 1.0 / len(self.organisms))
            individual_penalty = base_penalty * resp * 0.7  # 70% based on responsibility
            
            # Collective penalty (everyone shares some blame)
            collective_penalty = base_penalty * 0.3 / len(self.organisms)
            
            # Streak break penalty (losing a good streak hurts more)
            streak_penalty = 0.1 * min(old_streak, 5) * resp if old_streak >= 3 else 0
            
            total_penalty = -(individual_penalty + collective_penalty + streak_penalty)
            rewards[org.idx] += total_penalty
            
            # 🎰 TOKEN TUMBLER: Generate miss tokens
            org.tumble_tokens(action=0, reward=total_penalty, context='miss')
            if old_streak >= 3:
                org.token_sequence.append(133)  # streak_break
        
        # Reset ball
        ball.last_catcher = None
        ball.bounces = 0
        
        if self.verbose:
            closest_idx = max(responsibilities, key=responsibilities.get) if responsibilities else -1
            print(f"[SPHERE] ✗ Miss! Closest: Org #{closest_idx} Total misses: {self.collective_misses}")
    
    def _respawn_ball(self, ball: Ball3D):
        """Respawn ball at new position."""
        while True:
            x = random.uniform(-SPHERE_RADIUS * 0.3, SPHERE_RADIUS * 0.3)
            y = random.uniform(-SPHERE_RADIUS * 0.3, SPHERE_RADIUS * 0.3)
            z = random.uniform(-SPHERE_RADIUS * 0.3, SPHERE_RADIUS * 0.3)
            dist = math.sqrt(x*x + y*y + z*z)
            if dist > MIN_SPAWN_DISTANCE * 0.5:
                break
        
        vx = random.uniform(-1, 1)
        vy = random.uniform(-1, 1)
        vz = random.uniform(-1, 1)
        vel = _sphere_normalize((vx, vy, vz))
        vel = (vel[0] * BALL_SPEED, vel[1] * BALL_SPEED, vel[2] * BALL_SPEED)
        
        ball.position = (x, y, z)
        ball.velocity = vel
    
    def _process_command_chain(self):
        """Process command chain - commander broadcasts target position."""
        if self.current_commander is None:
            return
        
        # Find commander organism
        commander = None
        for org in self.organisms:
            if org.idx == self.current_commander:
                commander = org
                break
        
        if commander is None or not commander.alive:
            self.current_commander = None
            self.active_command = None
            return
        
        # Predict ball impact point
        if self.balls:
            ball = self.balls[0]
            # Simple prediction: where ball will be in N frames
            predict_frames = 30
            predicted_pos = (
                ball.position[0] + ball.velocity[0] * predict_frames,
                ball.position[1] + ball.velocity[1] * predict_frames,
                ball.position[2] + ball.velocity[2] * predict_frames
            )
            
            # Clamp to sphere
            dist = math.sqrt(predicted_pos[0]**2 + predicted_pos[1]**2 + predicted_pos[2]**2)
            if dist > SPHERE_RADIUS - BALL_RADIUS:
                scale = (SPHERE_RADIUS - BALL_RADIUS) / dist
                predicted_pos = (
                    predicted_pos[0] * scale,
                    predicted_pos[1] * scale,
                    predicted_pos[2] * scale
                )
            
            self.active_command = predicted_pos
    
    def _do_training_step(self):
        """Perform training step on collected experiences."""
        if not self.enable_training:
            return
        
        if len(self.experience_buffer) < SPHERE_BATCH_SIZE:
            return
        
        # Sample batch
        batch = random.sample(self.experience_buffer, min(SPHERE_BATCH_SIZE, len(self.experience_buffer)))
        
        # Train each brain that has experiences
        brain_losses = {}
        for exp in batch:
            org_idx = exp['org_idx']
            if org_idx not in brain_losses:
                brain_losses[org_idx] = []
            
            brain = self.agent.brains[org_idx]
            
            # Simple RL update
            if hasattr(brain, 'train'):
                brain.train()
            
            obs = torch.tensor(exp['observation'], dtype=torch.float32).unsqueeze(0)
            reward = exp['reward']
            
            if hasattr(self.agent, 'device'):
                obs = obs.to(self.agent.device)
            
            # Forward pass
            output = brain(obs)
            if isinstance(output, tuple):
                output = output[0]
            
            # Policy gradient with advantage estimation (baseline = mean reward)
            action = exp['action']
            log_prob = F.log_softmax(output, dim=-1)[0, action % output.shape[-1]]
            
            # Compute advantage: reward - baseline
            # Baseline is running mean of rewards to reduce variance
            if not hasattr(self, '_reward_baseline'):
                self._reward_baseline = 0.0
                self._reward_count = 0
            
            # Update baseline with exponential moving average
            self._reward_count += 1
            alpha = min(0.1, 1.0 / self._reward_count)  # Adaptive learning rate
            self._reward_baseline = (1 - alpha) * self._reward_baseline + alpha * reward
            
            # Advantage = reward - baseline (encourages above-average actions)
            advantage = reward - self._reward_baseline
            
            # Policy gradient loss with entropy bonus for exploration
            entropy = -(F.softmax(output, dim=-1) * F.log_softmax(output, dim=-1)).sum()
            entropy_bonus = 0.01 * entropy  # Small entropy bonus encourages exploration
            
            # Loss: negative log prob * advantage - entropy bonus
            # Even when advantage is small, entropy provides learning signal
            loss = -log_prob * advantage - entropy_bonus
            
            # Backward pass
            if hasattr(brain, 'parameters'):
                for param in brain.parameters():
                    if param.grad is not None:
                        param.grad.zero_()
                loss.backward()
                
                # Simple gradient update
                with torch.no_grad():
                    for param in brain.parameters():
                        if param.grad is not None:
                            param.data -= 0.001 * param.grad
            
            # Track absolute loss for logging (entropy makes loss meaningful even with 0 reward)
            brain_losses[org_idx].append(abs(loss.item()))
        
        # Log training
        total_loss = sum(sum(v) for v in brain_losses.values()) / max(1, sum(len(v) for v in brain_losses.values()))
        self.training_losses.append(total_loss)
        
        if self.verbose:
            print(f"[SPHERE TRAIN] Frame {self.total_frames}: loss={total_loss:.4f}, buffer={len(self.experience_buffer)}")
        
        # Clear old experiences
        if len(self.experience_buffer) > 1000:
            self.experience_buffer = self.experience_buffer[-500:]
    
    def _add_experience(self, org_idx: int, observation: np.ndarray, action: int, reward: float, next_obs: np.ndarray, done: bool):
        """Add experience to buffer."""
        self.experience_buffer.append({
            'org_idx': org_idx,
            'observation': observation,
            'action': action,
            'reward': reward,
            'next_observation': next_obs,
            'done': done
        })
    
    def render(self):
        """Render the arena."""
        if self.headless or not PYGAME_AVAILABLE:
            return
        
        if OPENGL_AVAILABLE:
            self._render_opengl()
        else:
            self._render_2d_fallback()
    
    def _render_opengl(self):
        """OpenGL 3D rendering."""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Camera position
        cam_dist = SPHERE_RADIUS * 2.5
        cam_x = cam_dist * math.cos(math.radians(self.camera_angle)) * math.cos(math.radians(self.camera_elevation))
        cam_y = cam_dist * math.sin(math.radians(self.camera_elevation))
        cam_z = cam_dist * math.sin(math.radians(self.camera_angle)) * math.cos(math.radians(self.camera_elevation))
        
        gluLookAt(cam_x, cam_y, cam_z, 0, 0, 0, 0, 1, 0)
        
        # Draw sphere wireframe
        glColor4f(0.3, 0.3, 0.5, 0.3)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        
        quadric = gluNewQuadric()
        gluSphere(quadric, SPHERE_RADIUS, 32, 32)
        gluDeleteQuadric(quadric)
        
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        
        # Draw paddle zones for each organism (matches sphere_arena.py)
        for org in self.organisms:
            if not org.alive:
                continue
            
            # Draw paddle zone as a filled circle on sphere
            pos = org.position
            normal = _sphere_normalize(pos)
            
            # Find tangent vectors
            up = (0, 1, 0)
            if abs(_sphere_dot(normal, up)) > 0.9:
                up = (1, 0, 0)
            tangent1 = _sphere_normalize(_sphere_cross(normal, up))
            tangent2 = _sphere_cross(normal, tangent1)
            
            # Color based on role - outline only like sphere_arena.py (subtle, not filled)
            if org.is_commander:
                glColor4f(1.0, 0.8, 0.0, 0.4)  # Gold for commander (subtle)
            else:
                glColor4f(*org.color, 0.3)  # Match sphere_arena.py alpha
            
            # Draw outline only (LINE_LOOP) - matches sphere_arena.py
            glBegin(GL_LINE_LOOP)
            for i in range(32):
                angle = 2 * math.pi * i / 32
                offset_x = PADDLE_ANGULAR_RADIUS * SPHERE_RADIUS * math.cos(angle)
                offset_y = PADDLE_ANGULAR_RADIUS * SPHERE_RADIUS * math.sin(angle)
                point = (
                    pos[0] + tangent1[0]*offset_x + tangent2[0]*offset_y,
                    pos[1] + tangent1[1]*offset_x + tangent2[1]*offset_y,
                    pos[2] + tangent1[2]*offset_x + tangent2[2]*offset_y
                )
                point = _sphere_normalize(point)
                point = (point[0]*SPHERE_RADIUS, point[1]*SPHERE_RADIUS, point[2]*SPHERE_RADIUS)
                glVertex3f(*point)
            glEnd()
            
            # Draw small sphere marker at organism position (matches sphere_arena.py)
            glPushMatrix()
            glTranslatef(*pos)
            glColor3f(*org.color)
            quadric = gluNewQuadric()
            gluSphere(quadric, 0.12, 12, 8)
            gluDeleteQuadric(quadric)
            glPopMatrix()
        
        # Draw balls (support multiple with distinct colors - matches sphere_arena.py)
        ball_colors = [(1.0, 1.0, 0.0), (1.0, 0.5, 0.0), (0.0, 1.0, 1.0), (1.0, 0.0, 1.0), (0.5, 1.0, 0.5)]
        for ball_idx, ball in enumerate(self.balls):
            if not ball.active:
                continue
            
            color = ball_colors[ball_idx % len(ball_colors)]
            
            # 🎯 VISUAL EFFECT 1: Ball motion trail
            if ball_idx in self.ball_trails and len(self.ball_trails[ball_idx]) > 1:
                trail = self.ball_trails[ball_idx]
                for i, trail_pos in enumerate(trail[:-1]):
                    alpha = (i + 1) / len(trail) * 0.4  # Fade out older positions
                    trail_radius = BALL_RADIUS * (0.3 + 0.7 * (i + 1) / len(trail))  # Smaller at tail
                    
                    glPushMatrix()
                    glTranslatef(*trail_pos)
                    glColor4f(color[0], color[1], color[2], alpha)
                    quadric = gluNewQuadric()
                    gluSphere(quadric, trail_radius, 6, 4)
                    gluDeleteQuadric(quadric)
                    glPopMatrix()
            
            # 🎯 VISUAL EFFECT 2: Depth-based shading (balls darken with distance from camera)
            cam_dist = SPHERE_RADIUS * 2.5
            ball_dist = math.sqrt(ball.position[0]**2 + ball.position[1]**2 + ball.position[2]**2)
            depth_factor = 0.5 + 0.5 * (1 - ball_dist / (SPHERE_RADIUS * 1.2))  # 0.5-1.0 based on depth
            depth_factor = max(0.4, min(1.0, depth_factor))
            
            # 🎯 VISUAL EFFECT 3: Size scaling with depth (perspective)
            size_scale = 0.8 + 0.4 * depth_factor  # 0.8-1.2x based on depth
            
            # 🎯 VISUAL EFFECT 4: Pulsing glow on active balls
            pulse = 0.8 + 0.2 * math.sin(self.total_frames * 0.15 + ball_idx)  # Subtle pulse
            
            # Draw main ball with all effects
            glPushMatrix()
            glTranslatef(*ball.position)
            glColor3f(color[0] * depth_factor * pulse, color[1] * depth_factor * pulse, color[2] * depth_factor * pulse)
            
            quadric = gluNewQuadric()
            gluSphere(quadric, BALL_RADIUS * size_scale, 12, 8)
            gluDeleteQuadric(quadric)
            
            glPopMatrix()
            
            # 🎯 VISUAL EFFECT 5: Ball shadow on sphere surface
            # Project ball onto sphere surface
            if ball_dist > 0:
                shadow_pos = (
                    ball.position[0] * SPHERE_RADIUS / ball_dist,
                    ball.position[1] * SPHERE_RADIUS / ball_dist,
                    ball.position[2] * SPHERE_RADIUS / ball_dist
                )
                # Shadow is darker and flatter when ball is far from surface
                shadow_alpha = 0.3 * (1 - abs(ball_dist - SPHERE_RADIUS) / SPHERE_RADIUS)
                shadow_alpha = max(0.05, min(0.3, shadow_alpha))
                
                glPushMatrix()
                glTranslatef(*shadow_pos)
                glColor4f(0.0, 0.0, 0.0, shadow_alpha)
                quadric = gluNewQuadric()
                gluSphere(quadric, BALL_RADIUS * 0.8, 8, 4)  # Slightly smaller shadow
                gluDeleteQuadric(quadric)
                glPopMatrix()
        
        # 💥 VISUAL EFFECT 6: Red shockwave on miss impact
        effects_to_remove = []
        for i, effect in enumerate(self.impact_effects):
            age = self.total_frames - effect['frame']
            if age > 30:  # Effect lasts 30 frames
                effects_to_remove.append(i)
                continue
            
            # Expanding ring
            progress = age / 30.0
            effect['radius'] = effect['max_radius'] * progress
            effect['intensity'] = 1.0 - progress
            
            # Larger effect if streak was broken
            streak_multiplier = 1.0 + 0.2 * min(effect.get('streak_broken', 0), 5)
            radius = effect['radius'] * streak_multiplier
            
            # Draw expanding red ring on sphere surface
            pos = effect['position']
            normal = _sphere_normalize(pos)
            
            up = (0, 1, 0)
            if abs(_sphere_dot(normal, up)) > 0.9:
                up = (1, 0, 0)
            tangent1 = _sphere_normalize(_sphere_cross(normal, up))
            tangent2 = _sphere_cross(normal, tangent1)
            
            # Red with fading intensity
            glColor4f(1.0, 0.2, 0.1, effect['intensity'] * 0.8)
            glLineWidth(2.0 + 3.0 * effect['intensity'])
            
            glBegin(GL_LINE_LOOP)
            for j in range(48):
                angle = 2 * math.pi * j / 48
                offset_x = radius * math.cos(angle)
                offset_y = radius * math.sin(angle)
                point = (
                    pos[0] + tangent1[0]*offset_x + tangent2[0]*offset_y,
                    pos[1] + tangent1[1]*offset_x + tangent2[1]*offset_y,
                    pos[2] + tangent1[2]*offset_x + tangent2[2]*offset_y
                )
                point = _sphere_normalize(point)
                point = (point[0]*SPHERE_RADIUS, point[1]*SPHERE_RADIUS, point[2]*SPHERE_RADIUS)
                glVertex3f(*point)
            glEnd()
            glLineWidth(1.0)
        
        for i in reversed(effects_to_remove):
            self.impact_effects.pop(i)
        
        # ✨ VISUAL EFFECT 7: Green ripple on catch
        effects_to_remove = []
        for i, effect in enumerate(self.catch_effects):
            age = self.total_frames - effect['frame']
            if age > 20:  # Catch effect lasts 20 frames
                effects_to_remove.append(i)
                continue
            
            progress = age / 20.0
            effect['radius'] = effect['max_radius'] * progress
            effect['intensity'] = 1.0 - progress
            
            # Draw expanding colored ring (uses catcher's color)
            pos = effect['position']
            # Project to sphere surface
            dist = math.sqrt(pos[0]**2 + pos[1]**2 + pos[2]**2)
            if dist > 0:
                pos = (pos[0]*SPHERE_RADIUS/dist, pos[1]*SPHERE_RADIUS/dist, pos[2]*SPHERE_RADIUS/dist)
            
            normal = _sphere_normalize(pos)
            
            up = (0, 1, 0)
            if abs(_sphere_dot(normal, up)) > 0.9:
                up = (1, 0, 0)
            tangent1 = _sphere_normalize(_sphere_cross(normal, up))
            tangent2 = _sphere_cross(normal, tangent1)
            
            # Catcher's color with green tint for success
            c = effect['color']
            glColor4f(c[0] * 0.5 + 0.5, c[1] * 0.5 + 0.5, c[2] * 0.3, effect['intensity'] * 0.7)
            glLineWidth(3.0 * effect['intensity'] + 1.0)
            
            glBegin(GL_LINE_LOOP)
            for j in range(32):
                angle = 2 * math.pi * j / 32
                offset_x = effect['radius'] * math.cos(angle)
                offset_y = effect['radius'] * math.sin(angle)
                point = (
                    pos[0] + tangent1[0]*offset_x + tangent2[0]*offset_y,
                    pos[1] + tangent1[1]*offset_x + tangent2[1]*offset_y,
                    pos[2] + tangent1[2]*offset_x + tangent2[2]*offset_y
                )
                point = _sphere_normalize(point)
                point = (point[0]*SPHERE_RADIUS, point[1]*SPHERE_RADIUS, point[2]*SPHERE_RADIUS)
                glVertex3f(*point)
            glEnd()
            glLineWidth(1.0)
        
        for i in reversed(effects_to_remove):
            self.catch_effects.pop(i)
        
        # Draw command target
        if self.active_command:
            glPushMatrix()
            glTranslatef(*self.active_command)
            glColor4f(1.0, 1.0, 0.0, 0.5)
            
            quadric = gluNewQuadric()
            gluSphere(quadric, BALL_RADIUS/2, 8, 8)
            gluDeleteQuadric(quadric)
            
            glPopMatrix()
        
        # Rotate camera slowly
        self.camera_angle += 0.2
        
        pygame.display.flip()
    
    def _render_2d_fallback(self):
        """2D fallback rendering when OpenGL not available."""
        self.screen.fill((20, 20, 40))
        
        cx, cy = 512, 384
        scale = 150
        
        # Draw sphere outline
        pygame.draw.circle(self.screen, (60, 60, 100), (cx, cy), int(SPHERE_RADIUS * scale), 2)
        
        # Project 3D to 2D (simple orthographic)
        def project(pos):
            return (int(cx + pos[0] * scale), int(cy - pos[1] * scale))
        
        # Draw paddle zones (as circles in 2D projection)
        for org in self.organisms:
            if not org.alive:
                continue
            
            pos = project(org.position)
            color = (int(org.color[0]*255), int(org.color[1]*255), int(org.color[2]*255))
            
            if org.is_commander:
                color = (255, 200, 0)  # Gold
            
            # Draw as circle (paddle zone)
            paddle_radius = int(PADDLE_ANGULAR_RADIUS * SPHERE_RADIUS * scale)
            pygame.draw.circle(self.screen, color, pos, paddle_radius)
            pygame.draw.circle(self.screen, (255, 255, 255), pos, paddle_radius, 2)
        
        # Draw balls (yellow like sphere_arena.py)
        ball_colors_2d = [(255, 255, 0), (255, 128, 0), (0, 255, 255), (255, 0, 255), (128, 255, 128)]
        for ball_idx, ball in enumerate(self.balls):
            if not ball.active:
                continue
            
            pos = project(ball.position)
            color = ball_colors_2d[ball_idx % len(ball_colors_2d)]
            pygame.draw.circle(self.screen, color, pos, int(BALL_RADIUS * scale))
        
        # Draw HUD
        if self.font:
            text = f"Catches: {self.collective_catches}  Misses: {self.collective_misses}/{self.max_misses}  Streak: {self.current_streak}"
            surf = self.font.render(text, True, (255, 255, 255))
            self.screen.blit(surf, (20, 20))
            
            if self.enable_training:
                train_text = f"Training: ON  Losses: {len(self.training_losses)}"
                train_surf = self.font.render(train_text, True, (100, 255, 100))
                self.screen.blit(train_surf, (20, 60))
        
        pygame.display.flip()
    
    def run(self) -> Dict[str, Any]:
        """Run the game loop."""
        running = True
        
        while running:
            # Handle events
            if PYGAME_AVAILABLE and not self.headless:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False
            
            # Step
            observations, rewards, done, info = self.step()
            
            # Collect experiences for training
            if self.enable_training:
                for org in self.organisms:
                    if org.idx in self.prev_observations and org.idx in rewards:
                        self._add_experience(
                            org.idx,
                            self.prev_observations[org.idx],
                            self.prev_actions.get(org.idx, 0),
                            rewards[org.idx],
                            observations.get(org.idx, np.zeros(OBSERVATION_SIZE)),
                            done
                        )
            
            # Render
            self.render()
            
            # FPS cap
            if self.clock:
                self.clock.tick(60)
            
            if done:
                running = False
        
        # Cleanup
        if PYGAME_AVAILABLE and not self.headless:
            pygame.quit()
        
        # Prompt to save trained weights
        if self.enable_training and len(self.training_losses) > 0:
            self._prompt_save_weights()
        
        # Build results
        results = {
            'collective_catches': self.collective_catches,
            'collective_misses': self.collective_misses,
            'best_streak': self.best_streak,
            'total_frames': self.total_frames,
            'command_chain_enabled': self.enable_command_chain,
            'total_commands': len(self.command_history),
            'training_losses': self.training_losses,
            'final_stats': {}
        }
        
        # Per-organism stats
        for org in self.organisms:
            results['final_stats'][org.idx] = {
                'catches': org.catches,
                'commands_issued': org.commands_issued,
                'commands_followed': org.commands_followed
            }
        
        # Best commander/follower
        if self.command_history:
            commander_counts = {}
            for cmd in self.command_history:
                nc = cmd['new_commander']
                commander_counts[nc] = commander_counts.get(nc, 0) + 1
            results['best_commander'] = max(commander_counts, key=commander_counts.get)
            results['best_follower'] = max(
                (o.idx for o in self.organisms),
                key=lambda i: results['final_stats'][i]['catches']
            )
        
        return results
    
    def _prompt_save_weights(self):
        """Prompt user to save trained weights."""
        print("\n" + "=" * 60)
        print("📈 TRAINING COMPLETE")
        print("=" * 60)
        print(f"   Training steps: {len(self.training_losses)}")
        if self.training_losses:
            print(f"   Final loss: {self.training_losses[-1]:.4f}")
        
        try:
            save = input("\nSave trained weights? (y/N): ").strip().lower()
            if save == 'y':
                self._save_trained_weights()
        except (EOFError, KeyboardInterrupt):
            pass
    
    def _save_trained_weights(self):
        """Save trained brain weights."""
        import os
        
        # Determine save directory
        save_dir = '.'
        if hasattr(self.agent, 'cocoon_dir'):
            save_dir = self.agent.cocoon_dir
        
        print(f"\n💾 Saving trained weights to: {save_dir}")
        
        for i, brain in enumerate(self.agent.brains):
            save_path = os.path.join(save_dir, f'brain_{i}_trained.pt')
            if hasattr(brain, 'state_dict'):
                torch.save(brain.state_dict(), save_path)
                print(f"   ✓ Saved brain_{i}_trained.pt")
        
        # Save ensemble if available
        if len(self.agent.brains) > 1:
            ensemble_path = os.path.join(save_dir, 'brain_ensemble_trained.pt')
            ensemble_state = {
                f'brain_{i}': brain.state_dict() 
                for i, brain in enumerate(self.agent.brains) 
                if hasattr(brain, 'state_dict')
            }
            torch.save(ensemble_state, ensemble_path)
            print(f"   ✓ Saved brain_ensemble_trained.pt")
        
        print("\n✅ Weights saved! Load with --export to create updated cocoon.")


def run_sphere_swarm_defense(
    agent,
    organism_indices: Optional[List[int]] = None,
    max_misses: int = 10,
    headless: bool = False,
    seed: Optional[int] = None,
    num_balls: int = 1,
    enable_training: bool = False,
    train_interval: int = SPHERE_TRAIN_INTERVAL,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Run swarm defense mode - the main 3D training game.
    
    Args:
        agent: CocoonAgent with organism brains
        organism_indices: Which organisms to include
        max_misses: Total misses before game over
        headless: Run without display
        seed: Random seed
        num_balls: Number of balls (1-5)
        enable_training: Enable post-snapshot learning
        train_interval: Frames between training steps
        verbose: Enable debug logging
    
    Returns:
        Results dict with catches, misses, streak, command history
    """
    arena = SphereArena(
        agent=agent,
        organism_indices=organism_indices,
        max_misses=max_misses,
        headless=headless,
        seed=seed,
        mode=SphereGameMode.SWARM_DEFENSE,
        enable_command_chain=True,
        num_balls=num_balls,
        enable_training=enable_training,
        train_interval=train_interval,
        verbose=verbose
    )
    
    return arena.run()


def run_sphere_demo(num_organisms: int = 6, max_misses: int = 10):
    """
    Run demo mode with dummy AI - preview visuals without trained organisms.
    """
    if not PYGAME_AVAILABLE:
        print("❌ pygame required for demo mode")
        print("   Install with: pip install pygame PyOpenGL")
        return None
    
    print("🎮 DEMO MODE - Preview with dummy AI")
    
    # Create dummy agent
    class DummyBrain:
        def __init__(self, idx):
            self.idx = idx
            self.input_dim = OBSERVATION_SIZE
            self.output_dim = 4
        
        def forward(self, x, **kwargs):
            return torch.randn(1, 4) * 0.5
        
        def eval(self):
            pass
        
        def __call__(self, x, **kwargs):
            return self.forward(x, **kwargs)
    
    class DummyAgent:
        def __init__(self, n):
            self.brains = [DummyBrain(i) for i in range(n)]
            self.device = 'cpu'
    
    dummy_agent = DummyAgent(num_organisms)
    
    arena = SphereArena(
        agent=dummy_agent,
        organism_indices=list(range(num_organisms)),
        max_misses=max_misses,
        headless=False,
        mode=SphereGameMode.SWARM_DEFENSE,
        enable_command_chain=True
    )
    
    return arena.run()


# =============================================================================
# INTERNAL TOURNAMENT RUNNER (when standalone_proton_tournament not available)
# =============================================================================

def _run_internal_tournament(agent: 'CocoonAgent', tournament_type: str, learn: bool = True):
    """
    Run an internal tournament between organisms in the ensemble.
    Fallback when standalone_proton_tournament.py is not available.
    
    Args:
        agent: CocoonAgent with multiple organisms
        tournament_type: 'round_robin', 'elimination', or 'ladder'
        learn: Whether to train during battles
    """
    import random
    import itertools
    
    num_organisms = len(agent.brains)
    if num_organisms < 2:
        print("❌ Tournament requires at least 2 organisms!")
        return
    
    # Default tournament games (built-in, no extra installs needed)
    TOURNAMENT_GAMES = [
        "CartPole-v1",
        "MountainCar-v0",
        "Acrobot-v1",
        "FrozenLake-v1",
    ]
    
    # Track wins
    wins = {i: 0 for i in range(num_organisms)}
    fitness = list(agent.organism_fitness) if hasattr(agent, 'organism_fitness') else [1.0] * num_organisms
    
    print(f"\n⚔️ INTERNAL TOURNAMENT: {tournament_type.upper()}")
    print(f"   Organisms: {num_organisms}")
    print(f"   Learning: {'ON' if learn else 'OFF'}")
    print("=" * 60)
    
    try:
        import gymnasium as gym
    except ImportError:
        print("❌ gymnasium not installed!")
        return
    
    def run_battle(org_a: int, org_b: int, game: str, episodes: int = 3) -> tuple:
        """Run a battle between two organisms, return (score_a, score_b)."""
        try:
            env = gym.make(game)
        except Exception as e:
            print(f"  ⚠️ Can't load {game}: {e}")
            return 0, 0
        
        scores = [0.0, 0.0]
        
        for org_idx, org_pos in enumerate([org_a, org_b]):
            brain = agent.brains[org_pos]
            total_reward = 0.0
            
            for ep in range(episodes):
                obs, _ = env.reset()
                obs = np.asarray(obs, dtype=np.float32).flatten()
                done = False
                ep_reward = 0.0
                
                while not done:
                    # Get action from this organism's brain
                    with torch.no_grad():
                        obs_tensor = torch.FloatTensor(obs).unsqueeze(0).to(agent.device)
                        if len(obs) < brain.input_dim:
                            pad = torch.zeros(1, brain.input_dim - len(obs), device=agent.device)
                            obs_tensor = torch.cat([obs_tensor, pad], dim=1)
                        outputs = brain(obs_tensor)
                        # Handle tuple output (action_probs, language_logits)
                        if isinstance(outputs, tuple):
                            action_probs = outputs[0]
                        else:
                            action_probs = outputs
                        action = action_probs.argmax(dim=-1).item()
                    
                    # Clamp action to valid range
                    if hasattr(env.action_space, 'n'):
                        action = action % env.action_space.n
                    
                    result = env.step(action)
                    if len(result) == 5:
                        next_obs, reward, terminated, truncated, _ = result
                        done = terminated or truncated
                    else:
                        next_obs, reward, done, _ = result
                    
                    next_obs = np.asarray(next_obs, dtype=np.float32).flatten()
                    
                    # Learn if enabled
                    if learn:
                        agent.add_experience(obs, action, reward, next_obs, done)
                    
                    obs = next_obs
                    ep_reward += reward
                
                total_reward += ep_reward
            
            scores[org_idx] = total_reward / episodes
        
        env.close()
        
        # Train if enough experiences
        if learn and len(agent.experience_buffers[0]) >= agent.batch_size:
            agent.train_step()
        
        return scores[0], scores[1]
    
    # Generate matchups based on tournament type
    if tournament_type == 'round_robin':
        matchups = list(itertools.combinations(range(num_organisms), 2))
        print(f"\n📋 Round Robin: {len(matchups)} matches")
        
        for match_num, (org_a, org_b) in enumerate(matchups, 1):
            game = random.choice(TOURNAMENT_GAMES)
            name_a = agent.organism_names[org_a] if hasattr(agent, 'organism_names') else f"Org-{org_a}"
            name_b = agent.organism_names[org_b] if hasattr(agent, 'organism_names') else f"Org-{org_b}"
            
            print(f"\n  Match {match_num}/{len(matchups)}: {name_a} vs {name_b} [{game}]")
            
            score_a, score_b = run_battle(org_a, org_b, game)
            
            if score_a > score_b:
                wins[org_a] += 1
                print(f"    🏆 {name_a} wins! ({score_a:.1f} vs {score_b:.1f})")
                # Fitness transfer
                transfer = 0.05 * fitness[org_b]
                fitness[org_a] += transfer
                fitness[org_b] -= transfer
            elif score_b > score_a:
                wins[org_b] += 1
                print(f"    🏆 {name_b} wins! ({score_b:.1f} vs {score_a:.1f})")
                transfer = 0.05 * fitness[org_a]
                fitness[org_b] += transfer
                fitness[org_a] -= transfer
            else:
                print(f"    🤝 Draw! ({score_a:.1f} vs {score_b:.1f})")
    
    elif tournament_type == 'elimination':
        # Single elimination bracket
        remaining = list(range(num_organisms))
        random.shuffle(remaining)
        round_num = 1
        
        print(f"\n🏆 Single Elimination: {num_organisms} organisms")
        
        while len(remaining) > 1:
            print(f"\n  === Round {round_num} ({len(remaining)} remaining) ===")
            next_round = []
            
            for i in range(0, len(remaining) - 1, 2):
                org_a, org_b = remaining[i], remaining[i + 1]
                game = random.choice(TOURNAMENT_GAMES)
                name_a = agent.organism_names[org_a] if hasattr(agent, 'organism_names') else f"Org-{org_a}"
                name_b = agent.organism_names[org_b] if hasattr(agent, 'organism_names') else f"Org-{org_b}"
                
                print(f"\n    {name_a} vs {name_b} [{game}]")
                score_a, score_b = run_battle(org_a, org_b, game, episodes=5)
                
                if score_a >= score_b:
                    next_round.append(org_a)
                    wins[org_a] += 1
                    print(f"      🏆 {name_a} advances! ({score_a:.1f} vs {score_b:.1f})")
                    # Elimination bonus
                    fitness[org_a] += 0.1 * fitness[org_b]
                    fitness[org_b] *= 0.8
                else:
                    next_round.append(org_b)
                    wins[org_b] += 1
                    print(f"      🏆 {name_b} advances! ({score_b:.1f} vs {score_a:.1f})")
                    fitness[org_b] += 0.1 * fitness[org_a]
                    fitness[org_a] *= 0.8
            
            # Odd organism gets bye
            if len(remaining) % 2 == 1:
                bye_org = remaining[-1]
                name_bye = agent.organism_names[bye_org] if hasattr(agent, 'organism_names') else f"Org-{bye_org}"
                print(f"    {name_bye} gets a bye")
                next_round.append(bye_org)
            
            remaining = next_round
            round_num += 1
        
        champion = remaining[0]
        champ_name = agent.organism_names[champion] if hasattr(agent, 'organism_names') else f"Org-{champion}"
        print(f"\n  👑 CHAMPION: {champ_name}!")
    
    elif tournament_type == 'ladder':
        # Continuous ladder matches
        num_matches = num_organisms * 3  # 3 matches per organism on average
        print(f"\n📊 Ladder: {num_matches} matches")
        
        for match_num in range(1, num_matches + 1):
            # Pick two different organisms
            org_a, org_b = random.sample(range(num_organisms), 2)
            game = random.choice(TOURNAMENT_GAMES)
            name_a = agent.organism_names[org_a] if hasattr(agent, 'organism_names') else f"Org-{org_a}"
            name_b = agent.organism_names[org_b] if hasattr(agent, 'organism_names') else f"Org-{org_b}"
            
            print(f"\n  [{match_num}/{num_matches}] {name_a} vs {name_b} [{game}]")
            score_a, score_b = run_battle(org_a, org_b, game)
            
            if score_a > score_b:
                wins[org_a] += 1
                print(f"    🏆 {name_a} ({score_a:.1f} vs {score_b:.1f})")
                transfer = 0.03 * fitness[org_b]
                fitness[org_a] += transfer
                fitness[org_b] -= transfer * 0.5  # Less punishment in ladder
            elif score_b > score_a:
                wins[org_b] += 1
                print(f"    🏆 {name_b} ({score_b:.1f} vs {score_a:.1f})")
                transfer = 0.03 * fitness[org_a]
                fitness[org_b] += transfer
                fitness[org_a] -= transfer * 0.5
    
    # Update agent fitness
    if hasattr(agent, 'organism_fitness'):
        agent.organism_fitness = fitness
    
    # Final standings
    print("\n" + "=" * 60)
    print("📊 FINAL STANDINGS")
    print("=" * 60)
    standings = sorted(range(num_organisms), key=lambda x: (wins[x], fitness[x]), reverse=True)
    for rank, org_idx in enumerate(standings, 1):
        name = agent.organism_names[org_idx] if hasattr(agent, 'organism_names') else f"Org-{org_idx}"
        medal = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else "  "))
        print(f"  {medal} #{rank}: {name} - {wins[org_idx]} wins, fitness={fitness[org_idx]:.3f}")
    
    if learn:
        print(f"\n📈 Training steps completed: {agent.training_step}")


# Optional Gym adapter
class GymRunner:
    def __init__(self, agent: CocoonAgent):
        self.agent = agent

    def run(self, env_name: str, episodes: int = 100, render: bool = False, learn: bool = True):
        try:
            import gymnasium as gym
            from gymnasium import spaces
        except ImportError:
            try:
                import gym
                from gym import spaces
            except ImportError:
                print("[!] Gymnasium not found. Install with: pip install gymnasium")
                return

        # Try to create the environment with helpful error messages
        try:
            env = gym.make(env_name, render_mode='human' if render else None)
        except gym.error.NameNotFound as e:
            print(f"\n❌ Environment '{env_name}' not found!")
            
            # Provide specific install hints
            if 'ALE/' in env_name or 'Atari' in env_name.lower():
                print("\n💡 Atari games require additional setup:")
                print("   pip install gymnasium[atari] ale-py")
                print("   ale-import-roms --yes")
            elif env_name in ['LunarLander-v3', 'BipedalWalker-v3', 'CarRacing-v2']:
                print("\n💡 Box2D games require additional setup:")
                print("   pip install gymnasium[box2d]")
                print("   (May also need: conda install swig)")
            elif '-PLE-' in env_name:
                print("\n❌ PLE (PyGame Learning Environment) is no longer maintained!")
                print("   These games don't work on modern Python. Try these instead:")
                print("   - CartPole-v1 (built-in)")
                print("   - ALE/Pong-v5 (Atari - need ale-py)")
            else:
                print("\n💡 Try: pip install gymnasium[all]")
                print("   Or check: https://gymnasium.farama.org/environments/")
            return
        except Exception as e:
            print(f"\n❌ Failed to create environment: {e}")
            return
        
        # Detect action space type
        is_continuous = isinstance(env.action_space, spaces.Box)
        action_space_size = None
        
        if is_continuous:
            action_dim = env.action_space.shape[0]
            action_low = env.action_space.low
            action_high = env.action_space.high
            print(f"[INFO] Continuous action space: dim={action_dim}, range=[{action_low[0]:.2f}, {action_high[0]:.2f}]")
        elif hasattr(env.action_space, 'n'):
            action_space_size = env.action_space.n
            print(f"[INFO] Discrete action space: {action_space_size} (brain has {self.agent.brains[0].output_dim})")
        
        all_rewards = []
        for ep in range(episodes):
            obs, _ = env.reset()
            if isinstance(obs, dict):
                obs = np.array(list(obs.values())).flatten()
            obs = np.asarray(obs, dtype=np.float32).flatten()
            done = False
            ep_reward = 0.0
            while not done:
                if is_continuous:
                    # For continuous action spaces, use brain output as continuous values
                    action = self.agent.get_continuous_action(obs, action_dim, action_low, action_high, explore=learn)
                else:
                    action = self.agent.get_action(obs, explore=learn, action_space_size=action_space_size)
                result = env.step(action)
                if len(result) == 5:
                    next_obs, reward, terminated, truncated, info = result
                    done = terminated or truncated
                else:
                    next_obs, reward, done, info = result
                if isinstance(next_obs, dict):
                    next_obs = np.array(list(next_obs.values())).flatten()
                next_obs = np.asarray(next_obs, dtype=np.float32).flatten()
                if learn:
                    self.agent.add_experience(obs, action, reward, next_obs, done)
                    if len(self.agent.experience_buffers[0]) >= self.agent.batch_size:
                        self.agent.train_step()
                obs = next_obs
                ep_reward += reward
            all_rewards.append(ep_reward)
            if (ep + 1) % 10 == 0:
                avg = np.mean(all_rewards[-10:])
                print(f"  Episode {ep+1:4d}: reward={ep_reward:7.1f}, avg10={avg:7.1f}, ε={self.agent.epsilon:.3f}")
        env.close()
        print(f"\n✅ Completed {episodes} episodes")
        print(f"   Mean reward: {np.mean(all_rewards):.2f}")
        print(f"   Best reward: {np.max(all_rewards):.2f}")


# Optional HTTP server
def run_http_server(agent: CocoonAgent, port: int = 8080):
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        print("[!] Flask not found. Install with: pip install flask")
        return

    app = Flask(__name__)

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok', 'organisms': len(agent.brains)})

    @app.route('/act', methods=['POST'])
    def act():
        data = request.json
        state = np.array(data.get('state', []), dtype=np.float32)
        explore = data.get('explore', False)
        action = agent.get_action(state, explore=explore)
        return jsonify({'action': action})

    @app.route('/learn', methods=['POST'])
    def learn():
        data = request.json
        agent.add_experience(
            np.array(data['state'], dtype=np.float32),
            data['action'],
            data['reward'],
            np.array(data['next_state'], dtype=np.float32),
            data['done']
        )
        loss = agent.train_step()
        return jsonify({'loss': loss, 'step': agent.training_step})

    @app.route('/chat', methods=['POST'])
    def chat():
        data = request.json
        prompt = data.get('prompt', '')
        learn = data.get('learn', True)
        
        # Get current VP value for reward calculation
        input_dim = agent.brains[0].input_dim if agent.brains else 25
        vp_info = agent.vp_runtime.compute_from_state(
            np.zeros(input_dim, dtype=np.float32),  # Dynamic input_dim from brain config
            agent.reward_history
        )
        current_vp = vp_info.get('violation_pressure', 0.0)
        
        # Get responses from all organisms with confidence and semantic reward
        responses = []
        for i, name in enumerate(agent.organism_names):
            response, confidence = agent.generate_response(prompt, organism_idx=i, vp_value=current_vp)
            fitness = agent.organism_fitness[i] if i < len(agent.organism_fitness) else 1.0
            
            # Calculate semantic reward (NEW - aligned with butterfly_chat.py)
            semantic_reward = agent._calculate_semantic_reward(
                user_message=prompt,
                organism_response=response,
                confidence=confidence,
                vp_value=current_vp
            )
            
            # Weight combines fitness, confidence, AND semantic quality
            weight = fitness * confidence * (0.5 + semantic_reward)
            
            responses.append({
                'organism': name,
                'response': response,
                'confidence': confidence,
                'fitness': fitness,
                'semantic_reward': semantic_reward,
                'weight': weight
            })
        
        # Select best response using decision matrix
        valid = [r for r in responses if r['response'].strip() and not r['response'].startswith('[')]
        if valid:
            best = max(valid, key=lambda r: r['weight'])
            final_response = best['response']
            best_reward = best['semantic_reward']
        else:
            final_response = responses[0]['response'] if responses else ''
            best_reward = 0.1
        
        # Learn from input with semantic reward if enabled
        if learn and prompt:
            agent.learn_from_text(prompt, reward=best_reward, vp_value=current_vp)
            if len(agent.experience_buffers[0]) >= agent.batch_size:
                agent.train_step()
        
        # Update conversation history
        agent.conversation.add_message('user', prompt)
        agent.conversation.add_message('assistant', final_response, {'semantic_reward': best_reward})
        
        return jsonify({
            'response': final_response,
            'all_responses': responses,
            'vocab_size': len(agent.vocabulary.get('word_to_id', {})),
            'semantic_reward': best_reward,
            'vp_value': current_vp
        })

    @app.route('/teach', methods=['POST'])
    def teach():
        """Teach the cocoon new words or concepts."""
        data = request.json
        text = data.get('text', '')
        reward = data.get('reward', 0.5)
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        tokens = agent.learn_from_text(text, reward=reward)
        
        # Train if we have enough experiences
        loss = 0.0
        if len(agent.experience_buffers[0]) >= agent.batch_size:
            loss = agent.train_step()
        
        return jsonify({
            'tokens': tokens,
            'vocab_size': len(agent.vocabulary.get('word_to_id', {})),
            'loss': loss
        })

    @app.route('/vocab', methods=['GET'])
    def get_vocab():
        """Get current vocabulary."""
        return jsonify({
            'vocab_size': len(agent.vocabulary.get('word_to_id', {})),
            'words': list(agent.vocabulary.get('word_to_id', {}).keys())
        })

    print(f"\n🌐 HTTP API Server starting on port {port}")
    print(f"   Endpoints: /health, /act, /learn, /chat, /teach, /vocab")
    app.run(host='0.0.0.0', port=port)


# =============================================================================
# COCOON LINK - P2P NETWORKING
# =============================================================================

async def run_cocoon_link(agent, display_name: str, hatch_url: str):
    """
    Run the cocoon in link mode - connect to a CocoonHatch server
    for P2P battles, trades, and chat with other cocoons.
    """
    import asyncio
    import json
    from dataclasses import dataclass, field
    from typing import Dict, Any, Optional, List
    from queue import Queue
    
    try:
        import websockets
    except ImportError:
        print("❌ websockets library required. Install with: pip install websockets")
        return
    
    @dataclass
    class RemoteUser:
        user_id: str
        display_name: str
        organism_count: int = 0
        total_fitness: float = 0.0
        battle_wins: int = 0
        battle_losses: int = 0
        status: str = "idle"
        
        def __str__(self):
            icon = "⚔️" if self.status == "battling" else "🟢"
            return f"{icon} {self.display_name} | 🧬{self.organism_count} | 🏆{self.battle_wins}/{self.battle_losses}"
    
    # Connection state
    websocket = None
    user_id = None
    users: Dict[str, RemoteUser] = {}
    current_battle = None
    pending_challenges: Dict[str, dict] = {}
    msg_queue: Queue = Queue()
    
    def get_cocoon_stats():
        return {
            'organism_count': len(getattr(agent, 'brains', [])),
            'total_fitness': sum(getattr(agent, 'organism_fitness', [0])),
            'battle_wins': getattr(agent, 'battle_wins', 0),
            'battle_losses': getattr(agent, 'battle_losses', 0),
            'vocab_size': len(agent.vocabulary.get('word_to_id', {})),
        }
    
    async def send(msg_type: str, data: dict):
        if websocket:
            await websocket.send(json.dumps({'type': msg_type, 'data': data}))
    
    async def handle_message(msg: dict):
        nonlocal user_id, current_battle
        msg_type = msg.get('type', '')
        data = msg.get('data', {})
        
        if msg_type == 'REGISTERED':
            user_id = data.get('user_id')
            print(f"✅ Connected as {display_name} ({user_id})")
            print(f"📊 {data.get('online_users', 0)} users online")
        
        elif msg_type == 'USER_LIST':
            users.clear()
            for u in data.get('users', []):
                if u.get('user_id') != user_id:
                    users[u['user_id']] = RemoteUser(**u)
        
        elif msg_type == 'USER_JOINED':
            u = data.get('user', {})
            if u.get('user_id') != user_id:
                users[u['user_id']] = RemoteUser(**u)
                print(f"➕ {u.get('display_name')} joined")
        
        elif msg_type == 'USER_LEFT':
            uid = data.get('user_id')
            name = data.get('display_name', 'Someone')
            if uid in users:
                del users[uid]
            print(f"➖ {name} left")
        
        elif msg_type == 'CHALLENGED':
            challenger = data.get('challenger', {})
            cid = data.get('challenge_id')
            pending_challenges[cid] = data
            print(f"\n⚔️ CHALLENGE from {challenger.get('display_name')}!")
            print(f"   Type /accept {cid[:8]} or /decline {cid[:8]}")
        
        elif msg_type == 'CHALLENGE_ACCEPTED':
            opponent = data.get('opponent', {})
            current_battle = {
                'battle_id': data.get('battle_id'),
                'opponent': opponent,
                'is_user1': data.get('you_are') == 'user1',
                'round': 0
            }
            print(f"\n🎮 BATTLE STARTING vs {opponent.get('display_name')}!")
            await run_battle()
        
        elif msg_type == 'BATTLE_START':
            opponent = data.get('opponent', {})
            current_battle = {
                'battle_id': data.get('battle_id'),
                'opponent': opponent,
                'is_user1': data.get('you_are') == 'user1',
                'round': 0
            }
            print(f"\n🎮 BATTLE STARTING vs {opponent.get('display_name')}!")
            await run_battle()
        
        elif msg_type == 'BATTLE_MSG':
            msg_queue.put(data.get('payload', {}))
        
        elif msg_type == 'BATTLE_END':
            winner = data.get('winner_name')
            if data.get('winner_id') == user_id:
                print(f"\n🏆 YOU WON!")
            elif data.get('winner_id'):
                print(f"\n💀 You lost to {winner}")
            else:
                print(f"\n🤝 Draw!")
            current_battle = None
        
        elif msg_type == 'CHAT':
            sender = data.get('from', 'Unknown')
            message = data.get('message', '')
            print(f"💬 {sender}: {message}")
        
        elif msg_type == 'ERROR':
            print(f"❌ {data.get('error')}")
    
    async def run_battle(rounds: int = 10):
        nonlocal current_battle
        if not current_battle:
            return
        
        print(f"\n⚔️ Battle: {rounds} rounds")
        my_score = 0
        opp_score = 0
        action_names = ['move', 'cooperate', 'compete', 'rest', 'reproduce', 'isolate']
        
        for r in range(1, rounds + 1):
            # Get my action
            state = [r/10.0, my_score/10.0, opp_score/10.0] + [0.0] * 21
            my_action = agent.get_action(np.array(state, dtype=np.float32), explore=True)
            my_conf = 0.7
            
            # Send action
            await send('BATTLE_MSG', {
                'round': r,
                'payload': {'action': int(my_action), 'confidence': my_conf}
            })
            
            # Wait for opponent
            opp_action = None
            for _ in range(300):  # 30 second timeout
                try:
                    opp_data = msg_queue.get_nowait()
                    opp_action = opp_data.get('action', 0)
                    break
                except Exception:
                    await asyncio.sleep(0.1)
            
            if opp_action is None:
                print("⏱️ Opponent timed out!")
                await send('BATTLE_END', {'winner_id': user_id, 'reason': 'timeout'})
                return
            
            # Resolve (simple: different actions = attacker wins)
            if my_action == opp_action:
                result = "🤝 Tie"
            elif (opp_action - my_action) % 6 in [1, 2]:
                my_score += 1
                result = "✅ You win"
            else:
                opp_score += 1
                result = "❌ Opponent wins"
            
            print(f"R{r}: {action_names[my_action]} vs {action_names[opp_action]} → {result} [{my_score}-{opp_score}]")
            await asyncio.sleep(0.3)
        
        # Determine winner
        if my_score > opp_score:
            await send('BATTLE_END', {'winner_id': user_id, 'reason': f'{my_score}-{opp_score}'})
        elif opp_score > my_score:
            opp_id = current_battle['opponent'].get('user_id')
            await send('BATTLE_END', {'winner_id': opp_id, 'reason': f'{my_score}-{opp_score}'})
        else:
            await send('BATTLE_END', {'winner_id': None, 'reason': 'Draw'})
    
    # Connect
    print(f"🔗 Connecting to {hatch_url}...")
    try:
        websocket = await websockets.connect(hatch_url)
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    # Register
    await send('REGISTER', {'display_name': display_name, **get_cocoon_stats()})
    
    print("\n📖 Commands: /users /challenge <name> /accept <id> /decline <id> /chat <msg> /quit")
    print("=" * 60)
    
    # Message receiver task
    async def receiver():
        try:
            async for message in websocket:
                await handle_message(json.loads(message))
        except websockets.exceptions.ConnectionClosed:
            print("⚠️ Connection lost")
    
    receiver_task = asyncio.create_task(receiver())
    
    # Input loop (simplified - blocking)
    import sys
    while True:
        try:
            await asyncio.sleep(0.1)
            # Simple input handling
            if sys.stdin in await asyncio.get_event_loop().run_in_executor(None, lambda: [sys.stdin] if sys.stdin.readable() else []):
                line = sys.stdin.readline().strip()
                if not line:
                    continue
                
                parts = line.split(maxsplit=2)
                cmd = parts[0].lower()
                
                if cmd == '/users':
                    await send('LIST_USERS', {})
                    await asyncio.sleep(0.2)
                    if users:
                        print("\n👥 Online Users:")
                        for u in users.values():
                            print(f"   {u}")
                    else:
                        print("No other users online")
                
                elif cmd == '/challenge' and len(parts) > 1:
                    await send('CHALLENGE', {'target': parts[1], 'message': parts[2] if len(parts) > 2 else ''})
                
                elif cmd == '/accept' and len(parts) > 1:
                    for cid in list(pending_challenges.keys()):
                        if cid.startswith(parts[1]):
                            await send('ACCEPT', {'challenge_id': cid})
                            del pending_challenges[cid]
                            break
                
                elif cmd == '/decline' and len(parts) > 1:
                    for cid in list(pending_challenges.keys()):
                        if cid.startswith(parts[1]):
                            await send('DECLINE', {'challenge_id': cid})
                            del pending_challenges[cid]
                            break
                
                elif cmd == '/chat' and len(parts) > 1:
                    await send('CHAT', {'message': ' '.join(parts[1:])})
                
                elif cmd == '/quit':
                    break
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            pass
    
    receiver_task.cancel()
    await websocket.close()
    print("👋 Disconnected")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="🦋 Butterfly Cocoon - Self-Contained Learning Agent",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog="""
Examples:
  python cocoon.py --mode chat
  python cocoon.py --mode gym --env CartPole-v1 --episodes 100
  python cocoon.py --mode serve --port 8080
  python cocoon.py --mode link --hatch ws://localhost:9000
  python cocoon.py --mode sphere --balls 2 --train
  python cocoon.py --export updated_cocoon.py
  python cocoon.py --export-onnx brain.onnx
  python cocoon.py --export-package ./my_model
    python cocoon.py --unpack ./ultimate_package
        """)
    parser.add_argument('--mode', choices=['chat', 'gym', 'serve', 'link', 'sphere', 'info'], default='info')
    parser.add_argument('--env', type=str, default='CartPole-v1')
    parser.add_argument('--episodes', type=int, default=100)
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--no-learn', action='store_true')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--export', type=str, help='Export cocoon Python file')
    parser.add_argument('--export-onnx', type=str, help='Export ONNX model (ensemble exports all brains combined)')
    parser.add_argument('--export-torchscript', type=str, help='Export TorchScript model (ensemble exports all brains combined)')
    parser.add_argument('--export-package', type=str, help='Export full package (ONNX + README + metadata)')
    parser.add_argument('--unpack', type=str, help='Unpack ultimate package assets to a directory (README/adapter/vocab/ensemble.onnx/ensemble_weights.pt)')
    parser.add_argument('--organism', type=int, default=0, help='Organism index for single-brain ONNX export (default: export all as ensemble)')
    parser.add_argument('--voting', choices=['majority', 'weighted', 'confidence'], default='confidence')
    parser.add_argument('--max-organisms', type=int, default=None, help='Limit number of organisms to load (saves VRAM)')
    parser.add_argument('--readme', action='store_true', help='Print the embedded README and exit')
    # Sphere arena arguments
    parser.add_argument('--balls', type=int, default=1, help='Number of balls in sphere arena (1-5)')
    parser.add_argument('--misses', type=int, default=10, help='Max collective misses before game over')
    parser.add_argument('--train', action='store_true', help='Enable post-snapshot training in sphere arena')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose debug logging')
    parser.add_argument('--demo', action='store_true', help='Run sphere arena with dummy AI')
    parser.add_argument('--headless', action='store_true', help='Run sphere arena without display')
    # Link mode arguments
    parser.add_argument('--hatch', type=str, default='ws://localhost:9000', help='CocoonHatch server URL')
    parser.add_argument('--name', type=str, default=None, help='Display name for link mode')
    args = parser.parse_args()

    if args.readme:
        _print_embedded_readme()
        return

    if args.unpack:
        _unpack_ultimate(args.unpack, voting=args.voting, max_organisms=args.max_organisms)
        return

    arch = _decode_data(_ARCHITECTURE_B64) or {}
    config = _decode_data(_TRAINING_CONFIG_B64) or {}
    vocab = _decode_data(_VOCABULARY_B64) or {'word_to_id': {}, 'id_to_word': {}}

    # Handle export commands FIRST - they work without loading the full agent
    if args.export or args.export_onnx or args.export_torchscript or args.export_package:
        if not TORCH_AVAILABLE:
            print("[!] PyTorch required for export")
            return
        agent = CocoonAgent(voting=args.voting, max_organisms=args.max_organisms)
        if args.export:
            agent.export_cocoon(args.export)
            return
        if args.export_onnx:
            # For ensembles, export ALL brains as combined ONNX unless specific organism requested
            if len(agent.brains) > 1 and args.organism == 0:
                agent.export_ensemble_onnx(args.export_onnx)
            else:
                agent.export_onnx(args.export_onnx, organism_idx=args.organism)
            return
        if args.export_torchscript:
            # For ensembles, export ALL brains as combined TorchScript unless specific organism requested
            if len(agent.brains) > 1 and args.organism == 0:
                agent.export_ensemble_torchscript(args.export_torchscript)
            else:
                agent.export_torchscript(args.export_torchscript, organism_idx=args.organism)
            return
        if args.export_package:
            agent.export_package(args.export_package)
            return

    if args.mode == 'info':
        print("\n🦋 BUTTERFLY COCOON")
        print("=" * 50)
        print(f"Mode:       {'ENSEMBLE' if arch.get('is_ensemble') else 'SOLO'}")
        print(f"Organisms:  {arch.get('ensemble_size', 1)}")
        print(f"Names:      {', '.join(arch.get('organism_names', []))}")
        print(f"Vocabulary: {len(vocab.get('word_to_id', {}))} words")
        print("\nTraining Config:")
        for k, v in config.items():
            print(f"  {k}: {v}")
        print("\nExport Options:")
        print("  --export <file.py>      Export updated cocoon")
        print("  --export-onnx <file>    Export ONNX for Netron")
        print("  --export-package <dir>  Export full package")
        print("  --unpack <dir>          Unpack ultimate package assets")
        print("\nUse --mode chat/gym/serve to run the agent")
        return

    if not TORCH_AVAILABLE:
        print("[!] PyTorch required for agent modes")
        return

    agent = CocoonAgent(voting=args.voting, max_organisms=args.max_organisms)

    if args.mode == 'chat':
        print("\n🦋 Butterfly Cocoon - Interactive Chat")
        print("=" * 60)
        print("╔═══════════════════════════════════════════════════════════╗")
        print("║ BUTTERFLY PIPELINE: Tokenomic Decision Matrix Active      ║")
        print("║ Commands: 'quit' to exit, 'export <file>' to save         ║")
        print("╚═══════════════════════════════════════════════════════════╝")
        print()
        initial_vocab = len(agent.vocabulary.get('word_to_id', {}))
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not user_input:
                continue
            if user_input.lower() == 'quit':
                break
            if user_input.lower().startswith('export '):
                agent.export_cocoon(user_input[7:].strip())
                continue
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 1: MESSAGE RECEIVED
            # ═══════════════════════════════════════════════════════════════
            print()
            print("┌─── STEP 1: MESSAGE ───────────────────────────────────────┐")
            print(f"│ Input: {user_input[:50]}{'...' if len(user_input) > 50 else ''}")
            print("└────────────────────────────────────────────────────────────┘")
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 2: TOKENIZATION
            # ═══════════════════════════════════════════════════════════════
            input_tokens = agent.tokenize(user_input)
            print("┌─── STEP 2: TOKENIZATION ────────────────────────────────────┐")
            print(f"│ Tokens: {len(input_tokens)} │ IDs: {input_tokens[:8]}{'...' if len(input_tokens) > 8 else ''}")
            print("└────────────────────────────────────────────────────────────┘")
            
            # Get VP value for semantic reward calculation (BEFORE generation)
            input_dim = agent.brains[0].input_dim if agent.brains else 25
            vp_info = agent.vp_runtime.compute_from_state(
                np.zeros(input_dim, dtype=np.float32),  # Dynamic input_dim from brain config
                agent.reward_history
            )
            current_vp = vp_info.get('violation_pressure', 0.0)
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 3: ORGANISM SELECTION
            # ═══════════════════════════════════════════════════════════════
            print("┌─── STEP 3: SELECTION ───────────────────────────────────────┐")
            num_orgs = len(agent.brains)
            print(f"│ Strategy: FITNESS_WEIGHTED │ Organisms: {num_orgs}")
            print(f"│ VP State: {vp_info.get('vp_class', 'VP0')} ({current_vp:.3f})")
            print("└────────────────────────────────────────────────────────────┘")
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 4: GENERATION (per-organism with detailed decision matrix)
            # ═══════════════════════════════════════════════════════════════
            print("┌─── STEP 4: GENERATION ──────────────────────────────────────┐")
            print("│ Decision Matrix: weight = fitness × confidence × gene_mod")
            print("├────────────────────────────────────────────────────────────┤")
            
            responses = []
            
            for i, name in enumerate(agent.organism_names):
                response, confidence = agent.generate_response(user_input, organism_idx=i, vp_value=current_vp)
                fitness = agent.organism_fitness[i] if i < len(agent.organism_fitness) else 1.0
                
                # NEW: Calculate semantic reward (aligned with butterfly_chat.py)
                semantic_reward = agent._calculate_semantic_reward(
                    user_message=user_input,
                    organism_response=response,
                    confidence=confidence,
                    vp_value=current_vp
                )
                
                # Granular decision matrix (matching main Butterfly Chat)
                # 1. Base weight from fitness × confidence
                base_weight = fitness * confidence
                
                # 2. Genetic diversity modifier (if available)
                gene_modifier = 1.0
                if hasattr(agent, 'organism_metadata') and i < len(agent.organism_metadata):
                    meta = agent.organism_metadata[i]
                    if 'gene_variance' in meta:
                        # More genetic diversity = slight weight bonus (max 20%)
                        gene_modifier = 1.0 + min(meta['gene_variance'] / 50000.0, 0.2)
                
                # 3. Semantic reward modifier (NEW - replaces basic response_modifier)
                # Scale semantic reward from [-0.3, 1.0] to [0.2, 1.5] multiplier
                semantic_modifier = 0.5 + semantic_reward
                
                # Final weight with all modifiers including semantic quality
                weight = base_weight * gene_modifier * semantic_modifier
                
                responses.append({
                    'idx': i,
                    'name': name,
                    'response': response,
                    'confidence': confidence,
                    'fitness': fitness,
                    'gene_mod': gene_modifier,
                    'semantic_reward': semantic_reward,
                    'semantic_mod': semantic_modifier,
                    'weight': weight
                })
                
                # Show individual organism response with granular breakdown
                print(f"│ [{name}]")
                print(f"│   conf={confidence:.3f} × fit={fitness:.2f} × gene={gene_modifier:.2f} × sem={semantic_modifier:.2f}")
                print(f"│   semantic_reward={semantic_reward:.3f} → weight {weight:.4f}")
                print(f"│   → {response[:80]}{'...' if len(response) > 80 else ''}")
            
            print("└────────────────────────────────────────────────────────────┘")
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 5: AGGREGATION (Granular Decision Matrix Summary)
            # ═══════════════════════════════════════════════════════════════
            print("┌─── STEP 5: AGGREGATION ─────────────────────────────────────┐")
            
            # Filter empty responses
            valid_responses = [r for r in responses if r['response'].strip() and not r['response'].startswith('[')]
            
            # Note: Diversity/repetition penalty is now handled by _calculate_semantic_reward()
            # which already penalizes low unique_ratio responses heavily
            
            total_weight = sum(r['weight'] for r in valid_responses)
            
            if valid_responses:
                # Sort by weight descending
                sorted_responses = sorted(valid_responses, key=lambda r: r['weight'], reverse=True)
                best = sorted_responses[0]
                final_response = best['response']
                best_reward = best.get('semantic_reward', 0.3)
                
                # Show granular decision matrix summary
                print(f"│ Aggregation: SEMANTIC_WEIGHTED_SELECTION")
                print(f"│ Total Weight Pool: {total_weight:.4f}")
                print(f"├────────────────────────────────────────────────────────────┤")
                print(f"│ 🏆 WINNER: [{best['name']}]")
                print(f"│    Weight: {best['weight']:.4f} ({best['weight']/total_weight*100:.1f}% of pool)")
                print(f"│    Breakdown: conf={best['confidence']:.3f} × fit={best['fitness']:.2f}")
                if 'gene_mod' in best:
                    print(f"│               × gene={best['gene_mod']:.2f} × sem={best.get('semantic_mod', 1.0):.2f}")
                print(f"│    Semantic Reward: {best.get('semantic_reward', 0):.3f}")
                print(f"├────────────────────────────────────────────────────────────┤")
                print(f"│ Runners-up:")
                for i, r in enumerate(sorted_responses[1:4], 2):  # Show top 3 runners-up
                    pct = r['weight']/total_weight*100 if total_weight > 0 else 0
                    print(f"│   #{i} [{r['name']}] weight={r['weight']:.4f} ({pct:.1f}%) sem_reward={r.get('semantic_reward', 0):.3f}")
            else:
                final_response = "[No valid response from organisms]"
                best_reward = 0.1
                best = None
                print(f"│ No valid responses to aggregate")
            
            print("└────────────────────────────────────────────────────────────┘")
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 6: CAUSATION (Event Tracking)
            # ═══════════════════════════════════════════════════════════════
            print("┌─── STEP 6: CAUSATION ───────────────────────────────────────┐")
            print(f"│ Event: CHAT_RESPONSE")
            print(f"│ Organisms Queried: {num_orgs}")
            print(f"│ Valid Responses: {len(valid_responses)}")
            print(f"│ Winner: {best['name'] if best else 'none'}")
            if best:
                print(f"│ Winner Weight: {best['weight']:.4f}")
            print("└────────────────────────────────────────────────────────────┘")
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 7: COMPLETE
            # ═══════════════════════════════════════════════════════════════
            print("┌─── STEP 7: COMPLETE ────────────────────────────────────────┐")
            print(f"│ Final Response:")
            print(f"└────────────────────────────────────────────────────────────┘")
            print()
            print(f"🦋 Cocoon: {final_response}")
            
            # Record conversation for context
            agent.conversation.add_message('user', user_input)
            agent.conversation.add_message('assistant', final_response, {'semantic_reward': best_reward})
            
            # Learn from user input WITH the semantic reward (not hardcoded 0.1)
            agent.learn_from_text(user_input, reward=best_reward, vp_value=current_vp)
            
            # Gap 3 Fix: Words USED in response get higher strength (rewarding active vocabulary use)
            # Use the winning organism's atomic language (Gap 5 Alignment)
            if best:
                winner_idx = best['idx']
                target_als = agent.atomic_language
                # Check for per-organism atomic languages
                if hasattr(agent, 'atomic_languages') and winner_idx < len(agent.atomic_languages):
                    target_als = agent.atomic_languages[winner_idx]
                
                for word in final_response.lower().split():
                    clean_word = ''.join(c for c in word if c.isalnum())
                    if len(clean_word) > 2:
                        # Strengthen if already known, acquire if new
                        if hasattr(target_als, 'atoms') and clean_word in target_als.atoms:
                            if hasattr(target_als, 'strengthen_concept'):
                                target_als.strengthen_concept(clean_word, 0.03, "chat_used")
                            else:
                                target_als.acquire_concept(clean_word, source='chat_used', initial_strength=0.3)
                        else:
                            target_als.acquire_concept(clean_word, source='chat_used', initial_strength=0.3)
            
            # Train on accumulated experiences
            if len(agent.experience_buffers[0]) >= agent.batch_size:
                loss = agent.train_step()
                if loss > 0:
                    print(f"\n  [📈 Training: loss={loss:.4f}, step={agent.training_step}]")
        
        # Show vocabulary growth
        final_vocab = len(agent.vocabulary.get('word_to_id', {}))
        if final_vocab > initial_vocab:
            print(f"\n📚 Vocabulary grew: {initial_vocab} → {final_vocab} words (+{final_vocab - initial_vocab})")
            print("   Export the cocoon to save learned words!")

    elif args.mode == 'gym':
        # Interactive menu if no env specified
        if args.env == 'CartPole-v1' and '--env' not in sys.argv:
            print("\n🎮 PROTON GAME ARENA - Training & Competition")
            print("=" * 70)
            print("Inspired by Piers Anthony's 'Apprentice Adept' game selection system")
            print("=" * 70)
            
            # ═══════════════════════════════════════════════════════════════════
            # PROTON-ALIGNED GAMES (All verified working!)
            # ═══════════════════════════════════════════════════════════════════
            
            # PHYSICAL CHALLENGES - Body, reflexes, coordination
            PHYSICAL_GAMES = [
                ("CartPole-v1", "🎯 Balance Beam - Keep pole balanced (reflexes)", "classic", "PHYSICAL/NAKED"),
                ("MountainCar-v0", "🏔️ Mountain Climb - Build momentum (persistence)", "classic", "PHYSICAL/NAKED"),
                ("Acrobot-v1", "🤸 Gymnast Swing - Double pendulum (coordination)", "classic", "PHYSICAL/NAKED"),
                ("Pendulum-v1", "🔄 Pendulum Control - Torque control (precision)", "classic", "PHYSICAL/TOOL"),
                ("LunarLander-v3", "🌙 Lunar Landing - Spacecraft landing (piloting)", "box2d", "PHYSICAL/MACHINE"),
                ("BipedalWalker-v3", "🚶 Biped Walk - Two-legged locomotion", "box2d", "PHYSICAL/MACHINE"),
                ("CarRacing-v3", "🏎️ Car Racing - Drive the track", "box2d", "PHYSICAL/MACHINE"),
            ]
            
            # MENTAL CHALLENGES - Strategy, planning, puzzle
            MENTAL_GAMES = [
                ("FrozenLake-v1", "🧊 Frozen Lake - Navigate slippery ice (planning)", "classic", "MENTAL/NAKED"),
                ("CliffWalking-v1", "🏔️ Cliff Walk - Don't fall off! (caution)", "classic", "MENTAL/NAKED"),
                ("Taxi-v3", "🚕 Taxi Driver - Pickup & delivery (efficiency)", "classic", "MENTAL/MACHINE"),
            ]
            
            # CHANCE CHALLENGES - Probability, luck
            CHANCE_GAMES = [
                ("Blackjack-v1", "🃏 Blackjack - Beat the dealer (probability)", "classic", "CHANCE/NAKED"),
            ]
            
            # ATARI ARCADE - Classic games (need ale-py)
            ATARI_GAMES = [
                ("ALE/Pong-v5", "🏓 Pong - Classic paddle game", "atari", "PHYSICAL/MACHINE"),
                ("ALE/Breakout-v5", "🧱 Breakout - Break the bricks", "atari", "PHYSICAL/TOOL"),
                ("ALE/SpaceInvaders-v5", "👾 Space Invaders - Defend Earth", "atari", "PHYSICAL/MACHINE"),
                ("ALE/MsPacman-v5", "👩 Ms. Pac-Man - Maze chase", "atari", "MENTAL/MACHINE"),
                ("ALE/Enduro-v5", "🚗 Enduro - Racing endurance", "atari", "PHYSICAL/MACHINE"),
            ]
            
            # MUJOCO PHYSICS (need gymnasium[mujoco])
            MUJOCO_GAMES = [
                ("Ant-v4", "🐜 Ant Walker - Quadruped locomotion", "mujoco", "PHYSICAL/ANIMAL"),
                ("HalfCheetah-v4", "🐆 Half Cheetah - Fast running", "mujoco", "PHYSICAL/ANIMAL"),
            ]
            
            # MULTIPLAYER TOURNAMENT - Uses multiple organisms!
            TOURNAMENT_MODES = [
                ("TOURNAMENT:round_robin", "⚔️ Round Robin - All organisms battle each other", "tournament", "VERSUS"),
                ("TOURNAMENT:elimination", "🏆 Elimination - Single elimination bracket", "tournament", "VERSUS"),
                ("TOURNAMENT:ladder", "📊 Ladder - Continuous ranked matches", "tournament", "VERSUS"),
            ]
            
            all_games = []
            idx = 1
            
            print("\n╔══════════════════════════════════════════════════════════════════╗")
            print("║  💪 PHYSICAL CHALLENGES - Reflexes, Coordination, Control        ║")
            print("╚══════════════════════════════════════════════════════════════════╝")
            for env, desc, cat, grid in PHYSICAL_GAMES:
                marker = "✅" if cat == "classic" else "📦"
                print(f"  {idx:2d}. {marker} {desc}")
                all_games.append((env, cat, grid, "solo"))
                idx += 1
            
            print("\n╔══════════════════════════════════════════════════════════════════╗")
            print("║  🧠 MENTAL CHALLENGES - Strategy, Planning, Puzzles              ║")
            print("╚══════════════════════════════════════════════════════════════════╝")
            for env, desc, cat, grid in MENTAL_GAMES:
                marker = "✅" if cat == "classic" else "📦"
                print(f"  {idx:2d}. {marker} {desc}")
                all_games.append((env, cat, grid, "solo"))
                idx += 1
            
            print("\n╔══════════════════════════════════════════════════════════════════╗")
            print("║  🎲 CHANCE CHALLENGES - Probability, Risk                        ║")
            print("╚══════════════════════════════════════════════════════════════════╝")
            for env, desc, cat, grid in CHANCE_GAMES:
                print(f"  {idx:2d}. ✅ {desc}")
                all_games.append((env, cat, grid, "solo"))
                idx += 1
            
            print("\n╔══════════════════════════════════════════════════════════════════╗")
            print("║  👾 ATARI ARCADE (pip install ale-py)                            ║")
            print("╚══════════════════════════════════════════════════════════════════╝")
            for env, desc, cat, grid in ATARI_GAMES:
                print(f"  {idx:2d}. 📦 {desc}")
                all_games.append((env, cat, grid, "solo"))
                idx += 1
            
            print("\n╔══════════════════════════════════════════════════════════════════╗")
            print("║  🤖 MUJOCO PHYSICS (pip install gymnasium[mujoco])               ║")
            print("╚══════════════════════════════════════════════════════════════════╝")
            for env, desc, cat, grid in MUJOCO_GAMES:
                print(f"  {idx:2d}. 📦 {desc}")
                all_games.append((env, cat, grid, "solo"))
                idx += 1
            
            # Only show tournament if we have multiple organisms
            num_organisms = len(agent.brains) if hasattr(agent, 'brains') else 1
            if num_organisms > 1:
                print("\n╔══════════════════════════════════════════════════════════════════╗")
                print(f"║  ⚔️ TOURNAMENT MODE - {num_organisms} Organisms Battle! (Highlander Style)      ║")
                print("╚══════════════════════════════════════════════════════════════════╝")
                for env, desc, cat, grid in TOURNAMENT_MODES:
                    print(f"  {idx:2d}. 🏟️ {desc}")
                    all_games.append((env, cat, grid, "tournament"))
                    idx += 1
            
            print(f"\n  {idx:2d}. [CUSTOM] Enter your own environment name")
            print("=" * 70)
            print("\n✅ = Built-in (always works)  📦 = Needs extra install  🏟️ = Multiplayer")
            
            # Selection
            try:
                choice = input(f"\nSelect game (1-{idx}): ").strip()
                if choice.isdigit():
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(all_games):
                        args.env, cat, grid, mode_type = all_games[choice_idx]
                        print(f"\n✅ Selected: {args.env} [{grid}]")
                        
                        # Handle tournament mode specially
                        if mode_type == "tournament":
                            tournament_type = args.env.replace("TOURNAMENT:", "")
                            print(f"\n⚔️ TOURNAMENT: {tournament_type.upper()}")
                            print(f"   {num_organisms} organisms will battle for supremacy!")
                            
                            # Run tournament instead of regular gym
                            try:
                                from standalone_proton_tournament import ProtonTournament
                            except ImportError:
                                # Use local tournament runner
                                print("\n🎮 Starting internal tournament...")
                                _run_internal_tournament(agent, tournament_type, learn=not args.no_learn)
                                return
                            
                            tournament = ProtonTournament(agent, learn_during_battle=not args.no_learn)
                            
                            if tournament_type == "round_robin":
                                tournament.round_robin()
                            elif tournament_type == "elimination":
                                tournament.elimination()
                            elif tournament_type == "ladder":
                                ep_input = input(f"Ladder episodes [{args.episodes}]: ").strip()
                                ladder_eps = int(ep_input) if ep_input else args.episodes
                                tournament.ladder(episodes=ladder_eps)
                            
                            # Save after tournament
                            if not args.no_learn:
                                save = input("\nSave tournament results? (y/N): ").strip().lower()
                                if save == 'y':
                                    agent.export_cocoon('cocoon_tournament.py')
                            return
                        
                        # Show install hints for different categories
                        if cat == 'box2d':
                            print("\n💡 Box2D install: pip install gymnasium[box2d]")
                        elif cat == 'atari':
                            print("\n💡 Atari install: pip install ale-py")
                        elif cat == 'mujoco':
                            print("\n💡 MuJoCo install: pip install gymnasium[mujoco]")
                    elif choice_idx == len(all_games):
                        args.env = input("Enter environment name: ").strip()
                    else:
                        print("Invalid choice, using CartPole-v1")
                        args.env = "CartPole-v1"
                else:
                    args.env = choice  # User typed env name directly
            except (EOFError, KeyboardInterrupt):
                print("\nCancelled.")
                return
            
            # Ask for episodes
            try:
                ep_input = input(f"Episodes [{args.episodes}]: ").strip()
                if ep_input:
                    args.episodes = int(ep_input)
            except Exception:
                pass
            
            # Ask for render
            try:
                render_input = input("Render visually? (Y/n): ").strip().lower()
                args.render = render_input != 'n'
            except Exception:
                args.render = True
            
            # Ask for training (default ON now)
            try:
                learn_input = input("Train while playing? (Y/n): ").strip().lower()
                args.no_learn = (learn_input == 'n')
            except Exception:
                args.no_learn = False
            
            print()
        
        runner = GymRunner(agent)
        runner.run(args.env, episodes=args.episodes, render=args.render, learn=not args.no_learn)
        
        if not args.no_learn:
            # Show training summary
            print(f"\n📊 Training Summary:")
            print(f"   Steps trained: {agent.training_step}")
            print(f"   Vocab size: {len(agent.vocabulary.get('word_to_id', {}))}")
            if hasattr(agent, 'organism_fitness'):
                print(f"   Organism fitness: {[f'{f:.2f}' for f in agent.organism_fitness]}")
            
            save = input("\nSave trained cocoon? (y/N): ").strip().lower()
            if save == 'y':
                agent.export_cocoon('cocoon_trained.py')
                print("✅ Saved to cocoon_trained.py")

    elif args.mode == 'serve':
        run_http_server(agent, port=args.port)

    elif args.mode == 'link':
        # Cocoon Link - P2P Networking
        print("\n🔗 COCOON LINK - P2P Networking")
        print("=" * 60)
        
        try:
            import asyncio
            import websockets
            LINK_AVAILABLE = True
        except ImportError:
            LINK_AVAILABLE = False
            print("❌ websockets library required for link mode")
            print("   Install with: pip install websockets")
            return
        
        # Get display name
        display_name = args.name
        if not display_name:
            # Generate from organism names
            if hasattr(agent, 'organism_names') and agent.organism_names:
                display_name = f"{agent.organism_names[0]}'s Cocoon"
            else:
                display_name = "Anonymous Cocoon"
        
        print(f"Display Name: {display_name}")
        print(f"Hatch Server: {args.hatch}")
        print()
        
        # Run the link client
        asyncio.run(run_cocoon_link(agent, display_name, args.hatch))

    elif args.mode == 'sphere':
        # Sphere Arena - 3D Swarm Defense Training
        print("\n🌐 SPHERE ARENA - 3D Swarm Defense")
        print("=" * 60)
        
        if args.demo:
            # Demo mode with dummy AI
            results = run_sphere_demo(num_organisms=6, max_misses=args.misses)
        else:
            # Full mode with cocoon brains
            num_organisms = args.max_organisms if args.max_organisms else len(agent.brains)
            num_balls = max(1, min(5, args.balls))
            max_misses = max(1, args.misses)
            
            print(f"Organisms: {num_organisms}")
            print(f"Balls: {num_balls}")
            print(f"Max Misses: {max_misses}")
            print(f"Training: {'ENABLED' if args.train else 'disabled'}")
            if args.verbose:
                print(f"Verbose: ENABLED")
            print()
            
            results = run_sphere_swarm_defense(
                agent,
                organism_indices=list(range(num_organisms)),
                max_misses=max_misses,
                headless=args.headless,
                num_balls=num_balls,
                enable_training=args.train,
                verbose=args.verbose
            )
        
        if results:
            print("\n" + "=" * 60)
            print("📊 SPHERE ARENA RESULTS")
            print("=" * 60)
            print(f"   Total Catches: {results.get('collective_catches', 0)}")
            print(f"   Total Misses:  {results.get('collective_misses', 0)}")
            print(f"   Best Streak:   {results.get('best_streak', 0)}")
            print(f"   Total Frames:  {results.get('total_frames', 0)}")
            
            if results.get('training_losses'):
                print(f"\n   Training Steps: {len(results['training_losses'])}")
                print(f"   Final Loss:     {results['training_losses'][-1]:.4f}")


if __name__ == "__main__":
    main()
''')

        # Embed TMRL adapter if available
        tmrl_adapter_b64 = ""
        tmrl_adapter_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cocoon_tmrl_adapter.py')
        if os.path.exists(tmrl_adapter_path):
            try:
                with open(tmrl_adapter_path, 'r', encoding='utf-8') as f:
                    tmrl_adapter_b64 = base64.b64encode(f.read().encode('utf-8')).decode('ascii')
            except Exception:
                pass
        
        # Embed Drone adapter if available
        drone_adapter_b64 = ""
        drone_adapter_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cocoon_drone_adapter.py')
        if os.path.exists(drone_adapter_path):
            try:
                with open(drone_adapter_path, 'r', encoding='utf-8') as f:
                    drone_adapter_b64 = base64.b64encode(f.read().encode('utf-8')).decode('ascii')
            except Exception:
                pass
        
        # Embed Drone arena (full 8-mode arena for --unpack)
        drone_arena_b64 = ""
        drone_arena_path = os.path.join(os.path.dirname(__file__), 'arena', 'cocoon_drone_arena.py')
        if os.path.exists(drone_arena_path):
            try:
                with open(drone_arena_path, 'r', encoding='utf-8') as f:
                    drone_arena_b64 = base64.b64encode(f.read().encode('utf-8')).decode('ascii')
            except Exception:
                pass
        
        # Embed JSBSim quadcopter physics (NASA-grade 6-DOF)
        drone_physics_b64 = ""
        drone_physics_path = os.path.join(os.path.dirname(__file__), 'arena', 'jsbsim_quadcopter.py')
        if os.path.exists(drone_physics_path):
            try:
                with open(drone_physics_path, 'r', encoding='utf-8') as f:
                    drone_physics_b64 = base64.b64encode(f.read().encode('utf-8')).decode('ascii')
            except Exception:
                pass
        
        source = template.substitute(
            MODE_COMMENT=mode_comment,
            ORGANISMS=", ".join(organism_names),
            GENERATED_TS=generated_timestamp,
            BRAIN_DATA=brain_data_py,
            ARCH_B64=arch_b64,
            VOCAB_B64=vocab_b64,
            KW_B64=kw_b64,
            CONFIG_B64=config_b64,
            ATOMIC_LANG_B64=atomic_lang_b64,
            CONVERSATION_B64=conversation_b64,
            ALLIANCE_B64=alliance_b64,
            DATA_COMPRESSED=str(compressed),
            README_B64=readme_b64 or "",
            TMRL_ADAPTER_B64=tmrl_adapter_b64,
            DRONE_ADAPTER_B64=drone_adapter_b64,
            DRONE_ARENA_B64=drone_arena_b64,
            DRONE_PHYSICS_B64=drone_physics_b64
        )
        return source

if __name__ == '__main__':
    # This block is for testing the AgentCompiler in isolation.
    # It requires a dummy OrganismCapsule and OrganismBrain setup.
    
    
    # Setup dummy brain and organism for testing
    dummy_brain_arch = {
        'input_dim': 25,
        'hidden_dim': 64,
        'output_dim': 6,
        'activation': 'relu',
        'dropout': 0.1,
        'use_attention': False,
        'num_attention_heads': 4,
        'attention_dim': 64,
        'vocab_size': 1000,
        'use_language_head': False
    }
    dummy_brain = OrganismBrain(**dummy_brain_arch)
    
    # Save dummy brain state_dict to BytesIO
    dummy_state_dict_buffer = BytesIO()
    torch.save(dummy_brain.state_dict(), dummy_state_dict_buffer)
    dummy_state_dict_buffer.seek(0)
    dummy_state_dict_b64 = base64.b64encode(dummy_state_dict_buffer.read()).decode('utf-8')
    
    dummy_capsule = OrganismCapsule(
        organism_id="test_org_001",
        capsule_id=f"cap_{uuid.uuid4()}",
        version="1.0",
        timestamp=datetime.datetime.now().isoformat(),
        neural_network_state={
            'architecture': dummy_brain_arch,
            'state_dict_b64': dummy_state_dict_b64,
            'device': 'cpu',
            'training_steps': 100,
            'avg_loss': 0.05
        },
        genotype_hash_state={'dna': 'ATGC...'}, 
        phenotype_summary={'size': 10, 'color': 'red'},
        fitness_trajectory=[{'fitness': 0.5, 'generation': 0}, {'fitness': 0.6, 'generation': 10}],
        age=10,
        atomic_language_state={'concept_count': 50, 'dialect_signature': [0.1, 0.2]},
        atomic_config_state={'neural': {'lr': 0.001}},
        highlander_metadata={'wins': 5, 'losses': 2},
        social_connections={'neighbors': 3},
        environment_context={'resource_density': 0.7},
        causation_digest={'events': [{'id': 'evt_1', 'type': 'born'}]},
        file_path="dummy_path.json"
    )
    
    compiler = AgentCompiler()
    
    # Test ONNX export
    try:
        onnx_archive = compiler.compile_capsule_to_agent(dummy_capsule, export_format='onnx')
        with open("test_agent_onnx.zip", "wb") as f:
            f.write(onnx_archive.read())
        print("Generated test_agent_onnx.zip")
    except Exception as e:
        print(f"ONNX compilation failed: {e}")
        
    # Test TorchScript export
    try:
        ts_archive = compiler.compile_capsule_to_agent(dummy_capsule, export_format='torchscript')
        with open("test_agent_torchscript.zip", "wb") as f:
            f.write(ts_archive.read())
        print("Generated test_agent_torchscript.zip")
    except Exception as e:
        print(f"TorchScript compilation failed: {e}")
        
    # Test StateDict export
    try:
        sd_archive = compiler.compile_capsule_to_agent(dummy_capsule, export_format='statedict')
        with open("test_agent_statedict.zip", "wb") as f:
            f.write(sd_archive.read())
        print("Generated test_agent_statedict.zip")
    except Exception as e:
        print(f"StateDict compilation failed: {e}")
