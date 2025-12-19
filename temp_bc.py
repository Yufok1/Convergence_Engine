"""
Butterfly Chat Router - Direct communication with organism network

Routes user messages to organisms and aggregates their responses.
"""

from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import logging
import time
import numpy as np

try:
    from reality_simulator.language_system import LanguageVocabulary
except Exception:
    LanguageVocabulary = None

try:
    from reality_simulator.neural.neural_organism import NeuralOrganism
except Exception:
    NeuralOrganism = None

logger = logging.getLogger(__name__)


class ButterflyChatRouter:
    """
    Routes user messages to organisms and aggregates responses.

    Routing strategies:
    - "all": All organisms respond
    - "random": Random sample of organisms
    - "fittest": Top N organisms by fitness
    - "connected": Organisms with most connections (requires network_state)
    - "by_word": Organisms associated with words in message (requires network_state/context_memory)
    """

    def __init__(self, 
                 organisms: Dict[str, Any],
                 vocabulary: Optional[LanguageVocabulary] = None,
                 event_emitter: Optional[callable] = None,
                 trainer: Optional[Any] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize router.

        Args:
            organisms: Dictionary of organism_id -> NeuralOrganism-like objects
            vocabulary: LanguageVocabulary for tokenization (optional)
            event_emitter: Optional function to emit causation events
            trainer: Optional NeuralTrainer for chat-triggered training
            config: Optional configuration dictionary for settings like temperature
        """
        self.organisms = organisms or {}
        self.vocabulary = vocabulary
        self.event_emitter = event_emitter
        self.trainer = trainer  # For chat-triggered learning
        self.config = config or {}
        
        # Get language generation settings from config
        language_config = self.config.get('neural', {}).get('language_model', {}).get('generation', {})
        self.generation_temperature = language_config.get('temperature', 1.2)  # Default matches config.json
        self.conversation_history: List[Dict[str, Any]] = []
        # Debug logging system
        self.debug_logs: List[Dict[str, Any]] = []
        self.causation_trail: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        # Learning tracking
        self.total_chat_experiences = 0
        self.chat_training_triggered = 0
        
        # ═══════════════════════════════════════════════════════════════
        # MISSION 1: Language Metrics Tracking for CRA/AutoTune Integration
        # ═══════════════════════════════════════════════════════════════
        self.semantic_reward_totals = {
            'word_overlap': 0.0,
            'coherence': 0.0,
            'length_score': 0.0,
            'confidence': 0.0,
            'vp_adjustment': 0.0,
            'total_reward': 0.0,
            'calculation_count': 0
        }
        self.knowledge_transfer_stats = {
            'total_broadcasts': 0,
            'total_recipients': 0,
            'total_reward_transferred': 0.0,
            'successful_transfers': 0
        }
        self.creative_vocab_stats = {
            'expansions': 0,
            'phrases_generated': 0,
            'compounds_created': 0,
            'neologisms': 0
        }

    def route_message(self,
                     message: str,
                     routing_strategy: str = "all",
                     max_organisms: Optional[int] = None,
                     network_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Route message to organisms and aggregate responses.

        Returns: dict with response, organism_responses, tokens_used, routing_info, debug_logs, causation_trail, errors
        """
        # Initialize debug logging for this message
        self.debug_logs = []
        self.causation_trail = []
        self.errors = []
        start_time = time.time()
        
        self._log_debug("STEP_1", "Message Received", {
            "message": message,
            "routing_strategy": routing_strategy,
            "max_organisms": max_organisms,
            "vocabulary_available": self.vocabulary is not None,
            "organisms_count": len(self.organisms),
            "network_state_available": network_state is not None
        })

        # Extract context_memory early so tokenization and generation use the same instance
        context_memory = network_state.get('context_memory') if network_state else None

        def _vocab_word_count(v: Any) -> int:
            try:
                return len(getattr(v, 'word_to_id', {}) or {})
            except Exception:
                return 0

        # Make vocab state visible in the debug panel (logger output doesn't show there)
        router_vocab_words = _vocab_word_count(self.vocabulary) if self.vocabulary else 0
        cm_vocab = getattr(context_memory, 'vocabulary', None) if context_memory else None
        cm_vocab_words = _vocab_word_count(cm_vocab) if cm_vocab else 0
        self._log_debug("STEP_1", "Vocabulary Snapshot", {
            "router_vocab_words": router_vocab_words,
            "context_memory_vocab_words": cm_vocab_words,
            "context_memory_available": context_memory is not None
        })

        # CRITICAL: Bootstrap router/context_memory vocabulary when it's effectively empty
        # (fresh instances often only have the 5 special tokens)
        if context_memory and router_vocab_words <= 5:
            bootstrapped = False
            bootstrap_source = None
            try:
                from reality_simulator.language_system import create_vocabulary_from_context_memory
                candidate = create_vocabulary_from_context_memory(context_memory)
                candidate_words = _vocab_word_count(candidate)
                if candidate_words > 5:
                    self.vocabulary = candidate
                    router_vocab_words = candidate_words
                    bootstrapped = True
                    bootstrap_source = "context_memory"
            except Exception as e:
                self._log_error("VOCAB_BOOTSTRAP_ERROR", f"Failed to build vocab from context_memory: {e}", {
                    "error_type": type(e).__name__
                })

            if not bootstrapped:
                # Fall back to data/innate_vocab.json (ships with the repo)
                try:
                    import json
                    from pathlib import Path
                    from reality_simulator.language_system import LanguageVocabulary

                    repo_root = Path(__file__).resolve().parents[2]
                    innate_path = repo_root / 'data' / 'innate_vocab.json'
                    if innate_path.exists():
                        with innate_path.open('r', encoding='utf-8') as f:
                            innate_data = json.load(f)

                        words: List[str] = []
                        concepts = innate_data.get('concepts')
                        if isinstance(concepts, list):
                            for c in concepts:
                                if isinstance(c, dict):
                                    w = c.get('word') or c.get('concept')
                                    if w:
                                        words.append(str(w))
                                elif isinstance(c, str):
                                    words.append(c)
                        elif isinstance(innate_data, list):
                            words = [str(w) for w in innate_data]

                        vocab = LanguageVocabulary()
                        for w in words:
                            if w:
                                vocab.add_word(w.lower())

                        candidate_words = _vocab_word_count(vocab)
                        if candidate_words > 5:
                            self.vocabulary = vocab
                            router_vocab_words = candidate_words
                            bootstrapped = True
                            bootstrap_source = "innate_vocab.json"
                except Exception as e:
                    self._log_error("VOCAB_BOOTSTRAP_ERROR", f"Failed to bootstrap vocab from innate_vocab.json: {e}", {
                        "error_type": type(e).__name__
                    })

            if bootstrapped:
                # Ensure generation sees the same vocabulary
                try:
                    context_memory.vocabulary = self.vocabulary
                except Exception:
                    pass
                self._log_debug("STEP_1", "Vocabulary Bootstrapped", {
                    "source": bootstrap_source,
                    "router_vocab_words": router_vocab_words
                })
        
        # Tokenize user message
        words = message.lower().split()
        self._log_debug("STEP_2", "Tokenization", {
            "input_words": words,
            "word_count": len(words)
        })
        
        if self.vocabulary is not None:
            try:
                prompt_tokens = self.vocabulary.encode(words, add_special=True)
                self._log_debug("STEP_2", "Tokenization Success", {
                    "tokens": prompt_tokens,
                    "token_count": len(prompt_tokens),
                    "vocab_words": _vocab_word_count(self.vocabulary)
                })
            except Exception as e:
                prompt_tokens = []
                self._log_error("TOKENIZATION_ERROR", f"Failed to encode message: {e}", {
                    "words": words,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                })
        else:
            prompt_tokens = []
            self._log_error("TOKENIZATION_WARNING", "Vocabulary not available", {
                "words": words,
                "result": "Empty token list (no vocabulary to encode)"
            })

        # Select organisms based on strategy
        self._log_debug("STEP_3", "Organism Selection", {
            "strategy": routing_strategy,
            "max_organisms": max_organisms,
            "total_organisms": len(self.organisms)
        })
        
        selected_organisms = self._select_organisms(
            routing_strategy, max_organisms, words, network_state
        )
        
        self._log_debug("STEP_3", "Organism Selection Complete", {
            "selected_count": len(selected_organisms),
            "selected_ids": list(selected_organisms.keys())[:10]  # First 10 for brevity
        })

        # Generate responses from each organism
        organism_responses = []
        # vp_value from network_state for generate_tokens()
        vp_value = network_state.get('vp_value') if network_state else None
        
        # CRITICAL FIX: Ensure context_memory has vocabulary wired before generation
        if context_memory and self.vocabulary:
            cm_vocab = getattr(context_memory, 'vocabulary', None)
            cm_words = _vocab_word_count(cm_vocab) if cm_vocab else 0
            our_words = _vocab_word_count(self.vocabulary)
            if cm_words <= 5 and our_words > 5:
                context_memory.vocabulary = self.vocabulary
                self._log_debug("STEP_4", "Wired vocabulary to context_memory", {
                    "router_vocab_words": our_words,
                    "context_memory_vocab_words_before": cm_words
                })
        
        self._log_debug("STEP_4", "Response Generation Setup", {
            "context_memory_available": context_memory is not None,
            "vp_value": vp_value,
            "organisms_to_query": len(selected_organisms)
        })
        
        for org_id, organism in selected_organisms.items():
            org_start_time = time.time()
            try:
                # Prefer a generate_tokens method, otherwise try a 'respond' callable
                if hasattr(organism, 'generate_tokens'):
                    # Calculate adaptive max_length based on organism experience
                    experience_count = len(organism.experience_buffer) if hasattr(organism, 'experience_buffer') else 0
                    vocab_size = self.vocabulary.vocab_size if self.vocabulary else 100
                    
                    # Adaptive max_length: shorter sequences early, scale up as network learns
                    # NEURAL SYNAPSE MODE: Longer responses = more causation edges!
                    if experience_count < 10:
                        adaptive_max_length = min(8, max(5, vocab_size // 6))
                    elif experience_count < 50:
                        adaptive_max_length = min(24, max(12, vocab_size // 4))
                    elif experience_count < 100:
                        adaptive_max_length = min(64, max(32, vocab_size // 2))
                    else:
                        adaptive_max_length = 128  # Full neural synapse length when experienced
                    
                    self._log_debug("STEP_4", f"Generating tokens for organism {org_id}", {
                        "method": "generate_tokens",
                        "has_context_memory": context_memory is not None,
                        "vp_value": vp_value,
                        "organism_fitness": float(getattr(organism, 'fitness', 0.0)),
                        "experience_count": experience_count,
                        "adaptive_max_length": adaptive_max_length
                    })

                    # Prove which implementation is running (file + line)
                    try:
                        import inspect
                        fn = getattr(organism, 'generate_tokens')
                        src_file = inspect.getsourcefile(fn)
                        _, src_line = inspect.getsourcelines(fn)
                        self._log_debug("STEP_4", f"generate_tokens implementation for {org_id}", {
                            "module": getattr(fn, '__module__', None),
                            "file": src_file,
                            "line": src_line
                        })
                    except Exception as e:
                        self._log_debug("STEP_4", f"generate_tokens implementation for {org_id}", {
                            "inspect_error": str(e)
                        })

                    # FIXED: Pass context_memory as first argument (required), then optional params
                    response_tokens = organism.generate_tokens(
                        context_memory=context_memory,
                        max_length=adaptive_max_length,
                        vp_value=vp_value,
                        temperature=self.generation_temperature  # Use config value
                    )
                    self._log_debug("STEP_4", f"Tokens generated for {org_id}", {
                        "token_count": len(response_tokens),
                        "tokens": response_tokens[:10]  # First 10 tokens
                    })
                elif hasattr(organism, 'respond'):
                    self._log_debug("STEP_4", f"Using respond method for {org_id}", {
                        "method": "respond"
                    })
                    # respond may accept text
                    response_text = organism.respond(message)
                    response_tokens = self.vocabulary.encode(response_text.split(), add_special=True) if self.vocabulary else []
                else:
                    response_tokens = []
                    self._log_error("RESPONSE_GENERATION_WARNING", f"Organism {org_id} has no response method", {
                        "organism_id": org_id,
                        "has_generate_tokens": hasattr(organism, 'generate_tokens'),
                        "has_respond": hasattr(organism, 'respond')
                    })

                response_words = self.vocabulary.decode(response_tokens, skip_special=True) if self.vocabulary else [str(t) for t in response_tokens]
                response_text = ' '.join(response_words) if isinstance(response_words, list) else str(response_words)
                
                # Learn new words from user message (vocabulary expansion)
                # NO FALLBACKS - organisms must generate their own responses
                if self.vocabulary and words:
                    for word in words:
                        if word not in self.vocabulary.word_to_id:
                            self.vocabulary.add_word(word)
                            self._log_debug("STEP_4", f"Learned new word: {word}", {
                                "organism_id": org_id,
                                "word": word,
                                "vocab_size": self.vocabulary.vocab_size
                            })
                
                # If response is empty, that's fine - organism couldn't generate yet
                # NO FALLBACKS - we want real organism responses, not automated fake ones
                if not response_text or response_text.strip() == '':
                    self._log_debug("STEP_4", f"Empty response from {org_id} (organism learning)", {
                        "organism_id": org_id,
                        "token_count": len(response_tokens),
                        "note": "Organism will learn to generate responses as it gains experience"
                    })
                
                confidence = self._calculate_confidence(response_tokens, organism=organism)
                fitness = float(getattr(organism, 'fitness', 0.0))
                
                # ✅ FIX: Add genetic/trait-based weight modifier
                genetic_weight_modifier = 1.0
                if hasattr(organism, 'genotype') and hasattr(organism.genotype, 'genes'):
                    # Genetic diversity contributes to weight
                    gene_variance = np.var(organism.genotype.genes) if len(organism.genotype.genes) > 0 else 0.0
                    genetic_weight_modifier = 1.0 + min(gene_variance / 50000.0, 0.2)  # Max 20% bonus
                
                weight = fitness * confidence * genetic_weight_modifier
                
                self._log_debug("STEP_4", f"Response decoded for {org_id}", {
                    "response_text": response_text[:50],  # First 50 chars
                    "token_count": len(response_tokens),
                    "word_count": len(response_words) if isinstance(response_words, list) else 0,
                    "confidence": confidence,
                    "fitness": fitness,
                    "weight": weight,
                    "generation_time_ms": (time.time() - org_start_time) * 1000
                })
                
                # Add to causation trail (event_id will be added later when events are emitted)
                self._add_causation_step(org_id, {
                    "input_tokens": prompt_tokens,
                    "output_tokens": response_tokens,
                    "response_text": response_text,
                    "fitness": fitness,
                    "confidence": confidence,
                    "weight": weight,
                    "context_memory_used": context_memory is not None,
                    "vp_value": vp_value,
                    "event_id": None  # Will be set when event is emitted
                })

                organism_responses.append({
                    'organism_id': org_id,
                    'response': response_text,
                    'tokens': response_tokens,
                    'fitness': fitness,
                    'confidence': confidence
                })
                
                # ═══════════════════════════════════════════════════════════════════════════
                # 🧠 LEARNING FROM CHAT INTERACTIONS
                # ═══════════════════════════════════════════════════════════════════════════
                # Store this interaction as a learning experience for the organism
                self._store_chat_experience(
                    organism=organism,
                    user_message=message,
                    user_tokens=prompt_tokens,
                    organism_response=response_text,
                    organism_tokens=response_tokens,
                    confidence=confidence,
                    fitness=fitness,
                    network_state=network_state
                )
            except Exception as e:
                import traceback
                error_info = {
                    "organism_id": org_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "has_generate_tokens": hasattr(organism, 'generate_tokens'),
                    "has_respond": hasattr(organism, 'respond'),
                    "generation_time_ms": (time.time() - org_start_time) * 1000,
                    "traceback": traceback.format_exc(limit=50),
                    "router_vocab_words": len(getattr(getattr(self, 'vocabulary', None), 'word_to_id', {}) or {}) if getattr(self, 'vocabulary', None) else 0,
                    "context_memory_vocab_words": len(getattr(getattr(context_memory, 'vocabulary', None), 'word_to_id', {}) or {}) if context_memory else 0
                }
                self._log_error("RESPONSE_GENERATION_ERROR", f"Organism {org_id} failed: {e}", error_info)
                logger.warning(f"Organism {org_id} failed to generate response: {e}")
                continue

        # Aggregate responses
        self._log_debug("STEP_5", "Response Aggregation", {
            "response_count": len(organism_responses),
            "aggregation_method": "weighted_by_fitness_confidence"
        })
        
        aggregated_response = self._aggregate_responses(organism_responses)
        
        self._log_debug("STEP_5", "Response Aggregation Complete", {
            "aggregated_response": aggregated_response[:100],  # First 100 chars
            "selected_from": len(organism_responses)
        })
        
        # Emit causation events and capture event IDs
        emitted_event_ids = []
        if self.event_emitter:
            self._log_debug("STEP_6", "Emitting Causation Events", {
                "event_emitter_available": True
            })
            emitted_event_ids = self._emit_chat_events(message, prompt_tokens, organism_responses, aggregated_response)
            
            # Link event IDs to causation trail steps
            # emitted_event_ids[0] is the message event, [1:] are organism response events
            # Match response events to steps by organism_id to ensure correct pairing
            if len(emitted_event_ids) > 1:
                response_event_ids = emitted_event_ids[1:]  # Skip message event
                # Create mapping: organism_id -> event_id
                organism_to_event = {}
                for resp in organism_responses:
                    org_id = resp.get('organism_id')
                    # Find matching event ID (they should be in same order)
                    resp_idx = organism_responses.index(resp)
                    if resp_idx < len(response_event_ids):
                        organism_to_event[org_id] = response_event_ids[resp_idx]
                
                # Link event IDs to steps by organism_id
                for step in self.causation_trail:
                    org_id = step.get('organism_id')
                    if org_id and org_id in organism_to_event:
                        event_id = organism_to_event[org_id]
                        step['event_id'] = event_id
                        step['step_data']['event_id'] = event_id
        else:
            self._log_error("CAUSATION_EVENT_WARNING", "Event emitter not available", {
                "events_skipped": True
            })

        # Store in conversation history
        conversation_entry = {
            'timestamp': time.time(),
            'user_message': message,
            'routing_strategy': routing_strategy,
            'organism_responses': organism_responses,
            'aggregated_response': aggregated_response,
            'tokens_used': prompt_tokens
        }
        self.conversation_history.append(conversation_entry)
        
        total_time = (time.time() - start_time) * 1000
        self._log_debug("STEP_7", "Message Routing Complete", {
            "total_time_ms": total_time,
            "response_length": len(aggregated_response),
            "success": True
        })

        return {
            'response': aggregated_response,
            'organism_responses': organism_responses,
            'tokens_used': prompt_tokens,
            'routing_info': {
                'strategy': routing_strategy,
                'organisms_queried': len(selected_organisms),
                'organisms_responded': len(organism_responses)
            },
            'debug_logs': self.debug_logs,
            'causation_trail': self.causation_trail,
            'errors': self.errors,
            'performance': {
                'total_time_ms': total_time,
                'avg_response_time_ms': total_time / max(len(organism_responses), 1)
            }
        }

    def _select_organisms(self,
                         strategy: str,
                         max_organisms: Optional[int],
                         message_words: List[str],
                         network_state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        all_orgs = dict(self.organisms)
        if not all_orgs:
            return {}

        if strategy == 'all':
            # Even 'all' strategy should respect max_organisms limit for performance
            if max_organisms and len(all_orgs) > max_organisms:
                # Sort by fitness and take top max_organisms
                sorted_orgs = sorted(all_orgs.items(), key=lambda x: getattr(x[1], 'fitness', 0.0), reverse=True)
                selected = dict(sorted_orgs[:max_organisms])
                self._log_debug("STEP_3", "Strategy: All Organisms (Limited)", {
                    "total_organisms": len(all_orgs),
                    "max_organisms": max_organisms,
                    "selected_count": len(selected),
                    "limited_by_fitness": True
                })
            else:
                selected = all_orgs
                self._log_debug("STEP_3", "Strategy: All Organisms", {
                    "selected_count": len(selected)
                })
        elif strategy == 'random':
            # Pick a random sample of items
            keys = list(all_orgs.keys())
            k = min(max_organisms or len(keys), len(keys))
            chosen = list(np.random.choice(keys, size=k, replace=False)) if k > 0 else []
            selected = {k: all_orgs[k] for k in chosen}
            self._log_debug("STEP_3", "Strategy: Random Sample", {
                "selected_count": len(selected),
                "sample_size": k,
                "selected_ids": list(selected.keys())[:10]
            })
        elif strategy == 'fittest':
            sorted_orgs = sorted(all_orgs.items(), key=lambda x: getattr(x[1], 'fitness', 0.0), reverse=True)
            selected = dict(sorted_orgs[:(max_organisms or len(sorted_orgs))])
            fitnesses = [getattr(org, 'fitness', 0.0) for org in selected.values()]
            self._log_debug("STEP_3", "Strategy: Fittest Organisms", {
                "selected_count": len(selected),
                "fitness_range": f"{min(fitnesses):.3f} - {max(fitnesses):.3f}" if fitnesses else "N/A",
                "top_organisms": list(selected.keys())[:5]
            })
        elif strategy == 'connected':
            if network_state:
                connections = network_state.get('connections', {})
                org_connection_counts = defaultdict(int)
                for (a, b) in connections.keys():
                    org_connection_counts[a] += 1
                    org_connection_counts[b] += 1
                sorted_orgs = sorted(all_orgs.items(), key=lambda x: org_connection_counts.get(x[0], 0), reverse=True)
                selected = dict(sorted_orgs[:(max_organisms or len(sorted_orgs))])
                connection_counts = [org_connection_counts.get(oid, 0) for oid in selected.keys()]
                self._log_debug("STEP_3", "Strategy: Connected Organisms", {
                    "selected_count": len(selected),
                    "connection_range": f"{min(connection_counts)} - {max(connection_counts)}" if connection_counts else "N/A",
                    "total_connections": len(connections)
                })
            else:
                selected = all_orgs
                self._log_error("ORGANISM_SELECTION_WARNING", "Network state not available for 'connected' strategy", {
                    "fallback": "All organisms selected"
                })
        elif strategy == 'by_word':
            selected = {}
            # Best-effort: if network_state has language_anchors mapping words -> organism ids
            if network_state:
                anchors = network_state.get('language_anchors', {})
                matched_words = []
                for word in message_words:
                    if word in anchors:
                        matched_words.append(word)
                        for oid in anchors.get(word, []):
                            oid_str = str(oid)
                            if oid_str in all_orgs:
                                selected[oid_str] = all_orgs[oid_str]
                self._log_debug("STEP_3", "Strategy: By Word Match", {
                    "matched_words": matched_words,
                    "selected_count": len(selected),
                    "vocab_size": len(anchors)
                })
            else:
                self._log_error("ORGANISM_SELECTION_WARNING", "Network state not available for 'by_word' strategy", {
                    "fallback": "All organisms selected"
                })
            if not selected:
                selected = all_orgs
        else:
            selected = all_orgs
            self._log_error("ORGANISM_SELECTION_WARNING", f"Unknown strategy: {strategy}", {
                "fallback": "All organisms selected"
            })

        return selected

    def process_message_through_organism(self, 
                                          organism: Any, 
                                          message: str,
                                          context_memory: Any = None,
                                          vp_value: Optional[float] = None) -> Dict[str, Any]:
        """
        Process a message through a single specific organism.
        
        Used for direct 1:1 chat with an individual organism.
        
        Args:
            organism: The organism to chat with
            message: User's message text
            context_memory: ContextMemory instance with vocabulary (REQUIRED for token generation!)
            vp_value: Current VP value for adaptive response length
            
        Returns:
            Dict with response, word_associations, emotional_state, confidence, causation_trail
        """
        self.debug_logs = []
        self.causation_trail = []
        self.errors = []
        
        org_id = getattr(organism, 'id', 'unknown')
        
        self._log_debug("DIRECT_CHAT", "Single organism chat started", {
            "organism_id": org_id,
            "message": message[:100],
            "has_language_system": hasattr(organism, 'language_system'),
            "has_context_memory": context_memory is not None,
            "vp_value": vp_value
        })
        
        # Tokenize message
        words = message.lower().split()
        prompt_tokens = []
        
        if self.vocabulary:
            try:
                prompt_tokens = self.vocabulary.encode(words, add_special=True)
            except Exception as e:
                self._log_error("TOKENIZATION_ERROR", str(e), {"words": words})
        
        # Get organism's language system
        language_system = getattr(organism, 'language_system', None)
        
        # Generate response
        response_tokens = []
        response_text = ""
        confidence = 0.0
        
        # DIAGNOSTIC: Check brain's language head capacity
        brain = getattr(organism, 'brain', None)
        if brain:
            fc_lang = getattr(brain, 'fc_language', None)
            if fc_lang:
                self._log_debug("DIRECT_CHAT", "Brain fc_language check", {
                    "out_features": fc_lang.out_features,
                    "use_language_head": getattr(brain, 'use_language_head', False)
                })
            else:
                self._log_debug("DIRECT_CHAT", "Brain has no fc_language", {})
        else:
            self._log_debug("DIRECT_CHAT", "Organism has no brain", {})
        
        try:
            if hasattr(organism, 'generate_tokens'):
                # Calculate adaptive response length
                try:
                    experience_count = len(organism.experience_buffer) if hasattr(organism, 'experience_buffer') and organism.experience_buffer else 0
                except (TypeError, AttributeError):
                    experience_count = 0
                    
                vocab_size = self.vocabulary.vocab_size if self.vocabulary and hasattr(self.vocabulary, 'vocab_size') else 100
                
                # Adaptive max_length like route_message uses
                if experience_count < 10:
                    max_length = min(8, max(5, vocab_size // 6))
                elif experience_count < 50:
                    max_length = min(24, max(12, vocab_size // 4))
                elif experience_count < 100:
                    max_length = min(64, max(32, vocab_size // 2))
                else:
                    max_length = 128
                
                self._log_debug("DIRECT_CHAT", "Generating tokens", {
                    "organism_id": org_id,
                    "max_length": max_length,
                    "experience_count": experience_count,
                    "has_context_memory": context_memory is not None,
                    "vp_value": vp_value
                })
                
                # Check brain's language head output size
                brain = getattr(organism, 'brain', None)
                if brain and hasattr(brain, 'fc_language'):
                    fc_lang_out = brain.fc_language.out_features
                    self._log_debug("DIRECT_CHAT", "Brain language head info", {
                        "fc_language_out_features": fc_lang_out,
                        "use_language_head": getattr(brain, 'use_language_head', False)
                    })
                
                # DEBUG: Log what vocabulary is being passed to generate_tokens
                if context_memory and hasattr(context_memory, 'vocabulary') and context_memory.vocabulary:
                    cm_vocab = context_memory.vocabulary
                    word_to_id = getattr(cm_vocab, 'word_to_id', {})
                    sample_words = list(word_to_id.keys())[:10]
                    self._log_debug("VOCAB_CHECK", "Vocabulary being passed to generate_tokens", {
                        "word_to_id_len": len(word_to_id),
                        "vocab_size_attr": getattr(cm_vocab, 'vocab_size', 'N/A'),
                        "sample_words": sample_words
                    })
                else:
                    self._log_debug("VOCAB_CHECK", "NO VOCABULARY in context_memory!", {})
                
                # CRITICAL: Pass context_memory for vocabulary access!
                response_tokens = organism.generate_tokens(
                    context_memory=context_memory,
                    max_length=max_length,
                    vp_value=vp_value,
                    temperature=self.generation_temperature  # Use config value
                )
                
                self._log_debug("DIRECT_CHAT", "Tokens generated", {
                    "token_count": len(response_tokens),
                    "tokens": response_tokens[:10] if response_tokens else []
                })
                
                # Decode tokens
                if self.vocabulary:
                    response_words = self.vocabulary.decode(response_tokens, skip_special=True)
                    response_text = ' '.join(response_words) if isinstance(response_words, list) else str(response_words)
                else:
                    response_text = ' '.join(str(t) for t in response_tokens)
                
                confidence = self._calculate_confidence(response_tokens, organism=organism)
                
            elif hasattr(organism, 'respond'):
                response_text = organism.respond(message)
                confidence = 0.5  # Default confidence for simple respond
                
        except Exception as e:
            self._log_error("RESPONSE_ERROR", str(e), {"organism_id": org_id})
        
        # Get word associations from organism's vocabulary
        word_associations = []
        if language_system and hasattr(language_system, 'vocabulary'):
            vocab = language_system.vocabulary
            for word in words:
                if word in vocab:
                    # Find related words by looking at co-occurrence or associations
                    word_info = {
                        'word': word,
                        'known': True,
                        'word_id': vocab.get(word, -1) if isinstance(vocab, dict) else -1
                    }
                    word_associations.append(word_info)
                else:
                    word_associations.append({'word': word, 'known': False})
        
        # Get emotional state if available
        emotional_state = {}
        if hasattr(organism, 'emotional_state'):
            emotional_state = dict(organism.emotional_state)
        elif hasattr(organism, 'mood'):
            emotional_state = {'mood': organism.mood}
        
        # Store this interaction as learning experience
        if hasattr(organism, 'experience_buffer'):
            self._store_chat_experience(
                organism=organism,
                user_message=message,
                user_tokens=prompt_tokens,
                organism_response=response_text,
                organism_tokens=response_tokens,
                confidence=confidence,
                fitness=getattr(organism, 'fitness', 0.0),
                network_state=None
            )
        
        self._log_debug("DIRECT_CHAT", "Single organism chat complete", {
            "organism_id": org_id,
            "response_length": len(response_text),
            "confidence": confidence,
            "token_count": len(response_tokens)
        })
        
        return {
            'response': response_text,
            'word_associations': word_associations,
            'emotional_state': emotional_state,
            'confidence': confidence,
            'causation_trail': self.causation_trail,
            'debug_logs': self.debug_logs,
            'errors': self.errors
        }

    def _aggregate_responses(self, organism_responses: List[Dict[str, Any]]) -> str:
        if not organism_responses:
            self._log_error("AGGREGATION_ERROR", "No organism responses to aggregate", {})
            return ""  # Empty response - organisms couldn't generate yet

        weighted_responses = []
        total_weight = 0.0
        for resp in organism_responses:
            weight = max(resp.get('fitness', 0.0), 0.0) * max(resp.get('confidence', 0.0), 0.0)
            weighted_responses.append((weight, resp.get('response', ''), resp.get('organism_id', 'unknown')))
            total_weight += weight

        if total_weight == 0.0:
            self._log_debug("STEP_5", "Aggregation: Zero weights, using concatenation", {
                "response_count": len(organism_responses)
            })
            return ' '.join([r['response'] for r in organism_responses if r.get('response')])

        best_response = max(weighted_responses, key=lambda x: x[0])
        self._log_debug("STEP_5", "Aggregation: Weighted selection", {
            "selected_organism": best_response[2],
            "selected_weight": best_response[0],
            "total_weight": total_weight,
            "response_preview": best_response[1][:50]
        })
        return best_response[1]

    def _calculate_confidence(self, tokens: List[int], organism: Any = None) -> float:
        """
        Calculate confidence score for organism response.
        
        Now includes organism-specific factors:
        - Token statistics (diversity, length)
        - Genetic fitness contribution
        - Neural capability (if neural organism)
        - Trait-based quality indicators
        
        Args:
            tokens: Generated token sequence
            organism: Organism instance (optional, for organism-specific factors)
            
        Returns:
            Confidence score (0.0-1.0)
        """
        if not tokens:
            return 0.0
        
        # Token-based confidence (original method)
        unique_tokens = len(set(tokens))
        total_tokens = len(tokens)
        diversity = unique_tokens / max(total_tokens, 1)
        length_score = min(total_tokens / 20.0, 1.0)
        token_confidence = (diversity * 0.6 + length_score * 0.4)
        
        # ✅ FIX: Organism-specific confidence factors
        organism_confidence = 0.5  # Default neutral
        
        if organism is not None:
            organism_factors = []
            
            # 1. Genetic fitness contribution (0.0-0.2 weight)
            if hasattr(organism, 'fitness'):
                # Normalize fitness to confidence contribution
                # Higher fitness = higher confidence (but cap at 0.2)
                fitness_contribution = min(organism.fitness * 0.2, 0.2)
                organism_factors.append(fitness_contribution)
            
            # 2. Genetic diversity bonus (0.0-0.15 weight)
            if hasattr(organism, 'genotype') and hasattr(organism.genotype, 'genes'):
                gene_variance = np.var(organism.genotype.genes) if len(organism.genotype.genes) > 0 else 0.0
                # More diverse genes = slightly higher confidence (genetic richness)
                diversity_bonus = min(gene_variance / 20000.0, 0.15)
                organism_factors.append(diversity_bonus)
            
            # 3. Neural capability (if neural organism) (0.0-0.15 weight)
            if hasattr(organism, 'brain') and organism.brain is not None:
                # Neural organisms get confidence boost
                neural_bonus = 0.1
                # Additional bonus if brain has language head
                if hasattr(organism.brain, 'use_language_head') and organism.brain.use_language_head:
                    neural_bonus = 0.15
                organism_factors.append(neural_bonus)
            
            # 4. Experience/learning progress (0.0-0.1 weight)
            if hasattr(organism, 'experience_buffer') and organism.experience_buffer is not None:
                buffer_len = len(organism.experience_buffer)
                buffer_cap = getattr(organism.experience_buffer, 'capacity', 1000)
                # More experience = higher confidence
                experience_contribution = min((buffer_len / buffer_cap) * 0.1, 0.1) if buffer_cap > 0 else 0.0
                organism_factors.append(experience_contribution)
            
            # 5. Trait-based quality (0.0-0.1 weight)
            if hasattr(organism, 'phenotype') and hasattr(organism.phenotype, 'traits'):
                traits = organism.phenotype.traits
                if traits:
                    # Trait balance (low variance = more balanced = higher confidence)
                    trait_values = list(traits.values())
                    if len(trait_values) > 1:
                        trait_variance = np.var(trait_values)
                        trait_balance = (1.0 - min(trait_variance, 1.0)) * 0.1
                        organism_factors.append(trait_balance)
            
            # Sum organism-specific factors
            if organism_factors:
                organism_confidence = sum(organism_factors)
                # Cap organism contribution at 0.5 (50% of total confidence)
                organism_confidence = min(organism_confidence, 0.5)
        
        # Combined confidence: 50% token-based, 50% organism-based
        total_confidence = (token_confidence * 0.5) + (organism_confidence * 0.5)
        
        # Clamp to valid range
        return np.clip(total_confidence, 0.0, 1.0)
    
    def _log_debug(self, step: str, action: str, data: Dict[str, Any]):
        """Add debug log entry"""
        self.debug_logs.append({
            'timestamp': time.time(),
            'step': step,
            'action': action,
            'data': data,
            'level': 'debug'
        })
    
    def _log_error(self, error_type: str, message: str, data: Dict[str, Any]):
        """Add error log entry"""
        error_entry = {
            'timestamp': time.time(),
            'error_type': error_type,
            'message': message,
            'data': data,
            'level': 'error'
        }
        self.errors.append(error_entry)
        self.debug_logs.append(error_entry)
    
    def _add_causation_step(self, organism_id: str, step_data: Dict[str, Any]):
        """Add step to causation trail"""
        self.causation_trail.append({
            'timestamp': time.time(),
            'organism_id': organism_id,
            'step_data': step_data
        })
    
    def _store_chat_experience(self,
                               organism: Any,
                               user_message: str,
                               user_tokens: List[int],
                               organism_response: str,
                               organism_tokens: List[int],
                               confidence: float,
                               fitness: float,
                               network_state: Optional[Dict[str, Any]] = None):
        """
        Store chat interaction as a learning experience for neural organisms.
        
        This allows organisms to learn from user interactions and improve
        their language generation over time.
        """
        # Only store experiences for neural organisms
        if not hasattr(organism, 'record_experience'):
            return
        
        if not hasattr(organism, 'experience_buffer') or organism.experience_buffer is None:
            return
        
        try:
            # Calculate reward based on response quality with SEMANTIC AWARENESS
            # This replaces simple length-based reward with meaning-aware scoring
            reward = self._calculate_semantic_reward(
                user_message=user_message,
                user_tokens=user_tokens,
                organism_response=organism_response,
                organism_tokens=organism_tokens,
                confidence=confidence,
                network_state=network_state
            )
            
            # Defensive: Ensure reward is a valid float (prevent NoneType comparison errors)
            if reward is None:
                reward = 0.3
                self._log_debug("REWARD_NONE_FALLBACK", "Reward was None, using fallback", {"fallback": 0.3})
            elif reward == 0.0:
                reward = 0.2
                self._log_debug("REWARD_ZERO_ADJUST", "Reward was 0.0, adjusted to 0.2", {})
            
            # Get organism state features for experience storage
            if hasattr(organism, 'get_state_features'):
                try:
                    state = organism.get_state_features(
                        local_env=None,
                        network_state=network_state,
                        breath_state=None
                    )
                except Exception:
                    # Fallback: create minimal state
                    state = np.array([fitness, confidence, len(organism_tokens)])
            else:
                # Minimal state: [fitness, confidence, token_count]
                state = np.array([fitness, confidence, len(organism_tokens)])
            
            # Use previous state if available, otherwise use current state
            prev_state = getattr(organism, 'prev_state', None)
            if prev_state is None:
                prev_state = state.copy()
            
            # Store token sequence for language model training
            # Combine user tokens and organism tokens as a sequence
            full_token_sequence = user_tokens + organism_tokens
            
            # Get VP value if available
            vp_val = None
            if network_state:
                vp_val = network_state.get('vp_value')
            
            # Create experience with EXPLICIT input/target separation for proper seq2seq learning
            # This fixes the supervised learning gap where concatenated sequences caused echoing
            from reality_simulator.neural.experience import Experience
            experience = Experience(
                state=prev_state,
                action=0,  # Chat interaction doesn't map to action space
                reward=reward,
                next_state=state,
                done=False,
                input_tokens=user_tokens,       # User input (context)
                target_tokens=organism_tokens,  # Desired response (target)
                vp_value=vp_val
            )
            
            # Add to experience buffer with EXPLICIT input/target separation
            # This enables proper "given input X, generate response Y" learning
            organism.experience_buffer.add(
                state=prev_state,
                action=0,
                reward=reward,
                next_state=state,
                done=False,
                input_tokens=user_tokens,       # User input tokens
                target_tokens=organism_tokens,  # Organism response tokens
                vp_value=vp_val
            )
            
            # Also store token sequence in organism's token_sequence deque if available
            # Use both for backward compatibility with existing training code
            full_token_sequence = user_tokens + organism_tokens
            if hasattr(organism, 'token_sequence'):
                for token in full_token_sequence:
                    organism.token_sequence.append(token)
            
            # Update previous state
            organism.prev_state = state.copy()
            
            self._log_debug("STEP_4", f"Stored chat experience for {organism}", {
                "organism_id": getattr(organism, 'species_id', 'unknown'),
                "reward": reward,
                "response_length": len(organism_response),
                "input_tokens_length": len(user_tokens),
                "target_tokens_length": len(organism_tokens),
                "experience_buffer_size": len(organism.experience_buffer) if hasattr(organism.experience_buffer, '__len__') else 'unknown'
            })
            
            # Track chat experiences
            self.total_chat_experiences += 1
            
            # TOKEN TUMBLER - Generate tokens for chat interactions
            # This links conversation quality to language model token sequences
            if hasattr(organism, 'tumble_action_tokens'):
                # Map reward to action: higher reward = more "cooperative" action
                chat_action = min(5, max(0, int(reward * 5)))  # 0-5 based on reward
                organism.tumble_action_tokens(
                    action=chat_action, 
                    reward=reward, 
                    context='chat_response'
                )
            
            # ═══════════════════════════════════════════════════════════════════════════
            # 🆕 GAP 2 FIX: VOCABULARY LEARNING FROM CHAT
            # Organisms learn words from user messages (low initial strength, must reinforce)
            # ═══════════════════════════════════════════════════════════════════════════
            user_words = user_message.lower().split()
            words_learned = self._learn_words_from_chat(
                organism=organism,
                words=user_words,
                source='chat_heard',
                network_state=network_state,
                initial_strength=0.2  # Low strength - must be reinforced
            )
            
            # Strengthen words the organism successfully used in its response
            if organism_response and len(organism_response.strip()) > 0:
                response_words = organism_response.lower().split()
                self._learn_words_from_chat(
                    organism=organism,
                    words=response_words,
                    source='chat_used',
                    network_state=network_state,
                    initial_strength=0.3  # Slightly higher - organism actively used it
                )
            
            # Trigger training more frequently (every 5 experiences instead of waiting for buffer to fill)
            buffer_size = len(organism.experience_buffer) if hasattr(organism.experience_buffer, '__len__') else 0
            if buffer_size >= 5 and buffer_size % 5 == 0:
                self._trigger_chat_training(organism, network_state)
            
            # Trigger bootstrap learning for empty responses
            if (not organism_response or len(organism_response.strip()) == 0) and self.trainer:
                self._trigger_bootstrap_learning(organism, user_tokens, network_state)
            
            # Trigger periodic training from chat experiences (every 10 experiences)
            if self.total_chat_experiences % 10 == 0 and self.trainer:
                self._trigger_chat_training(organism, network_state)
            
            # KNOWLEDGE TRANSFER: Broadcast successful responses to connected organisms
            # Based on Grok-2's inter-organism knowledge transfer design
            # High-reward responses (reward > 0.6) are shared with network neighbors
            # GROK-3 FIX: Only broadcast if response has good variety (no repetition)
            response_words_for_broadcast = organism_response.lower().split() if organism_response else []
            broadcast_unique_ratio = len(set(response_words_for_broadcast)) / max(1, len(response_words_for_broadcast))
            
            # GROK REVIEW FIX: Separate broadcast and vocab expansion into isolated try blocks
            if reward > 0.6 and network_state and broadcast_unique_ratio > 0.5:
                try:
                    self._broadcast_successful_response(
                        source_organism=organism,
                        user_tokens=user_tokens,
                        response_tokens=organism_tokens,
                        reward=reward,
                        network_state=network_state
                    )
                except Exception as broadcast_err:
                    logger.debug(f"Broadcast failed (non-fatal): {broadcast_err}")
            
            # GROK REVIEW FIX: Vocabulary expansion moved OUTSIDE broadcast condition
            # Expand vocab for any moderately successful response (reward > 0.4)
            if reward > 0.4 and self.vocabulary and hasattr(self.vocabulary, 'expand_vocabulary_from_pattern'):
                try:
                    self.vocabulary.expand_vocabulary_from_pattern(organism_tokens, reward)
                except Exception as vocab_err:
                    logger.debug(f"Vocabulary expansion failed (non-fatal): {vocab_err}")
            
        except Exception as e:
            # Don't fail chat if experience storage fails
            self._log_error("EXPERIENCE_STORAGE_ERROR", f"Failed to store chat experience: {e}", {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "organism_id": getattr(organism, 'species_id', 'unknown')
            })
            logger.warning(f"Failed to store chat experience for organism: {e}")

    def _learn_words_from_chat(self,
                                organism: Any,
                                words: List[str],
                                source: str,
                                network_state: Optional[Dict[str, Any]] = None,
                                initial_strength: float = 0.2) -> int:
        """
        Have organism acquire concepts from chat words.
        
        This is the KEY FIX for vocabulary learning - organisms now learn words
        from user chat messages. Words must exist in knowledge_web to be valid concepts.
        
        Args:
            organism: Organism with atomic_language system
            words: List of words from user message
            source: Source of learning ('chat_heard', 'chat_used', etc.)
            network_state: Network state containing knowledge_web reference
            initial_strength: Starting strength for acquired concepts (low = must be reinforced)
            
        Returns:
            Number of words learned
        """
        # Need atomic_language to learn
        if not hasattr(organism, 'atomic_language') or organism.atomic_language is None:
            return 0
        
        # Get knowledge_web for semantic frame info
        knowledge_web = None
        if network_state:
            context_memory = network_state.get('context_memory')
            if context_memory and hasattr(context_memory, 'knowledge_web'):
                knowledge_web = context_memory.knowledge_web
        
        learned = 0
        for word in words:
            # Clean word
            word = word.lower().strip()
            if not word or len(word) < 2:
                continue
            
            # Skip if already known (but strengthen it)
            if word in organism.atomic_language.atoms:
                organism.atomic_language.strengthen_concept(
                    word, 0.03, f"{source}_reinforced"
                )
                continue
            
            # Get semantic frame from knowledge_web if available
            semantic_frame = 'unknown'
            if knowledge_web and hasattr(knowledge_web, 'concepts') and word in knowledge_web.concepts:
                concept = knowledge_web.concepts[word]
                semantic_frame = getattr(concept, 'semantic_frame', 'unknown')
            
            # Acquire the concept at low strength (must be reinforced through use)
            try:
                organism.atomic_language.acquire_concept(
                    concept_id=word,
                    source=source,
                    semantic_frame=semantic_frame,
                    initial_strength=initial_strength,
                    reason=f"heard_in_chat"
                )
                learned += 1
                
                self._log_debug("VOCAB_LEARNING", f"Organism learned word: {word}", {
                    "organism_id": getattr(organism, 'species_id', 'unknown'),
                    "word": word,
                    "source": source,
                    "strength": initial_strength,
                    "semantic_frame": semantic_frame
                })
            except Exception as e:
                logger.debug(f"Failed to acquire concept '{word}': {e}")
        
        return learned

    def _calculate_semantic_reward(self,
                                     user_message: str,
                                     user_tokens: List[int],
                                     organism_response: str,
                                     organism_tokens: List[int],
                                     confidence: float,
                                     network_state: Optional[Dict[str, Any]] = None) -> float:
        """
        Calculate reward with SEMANTIC AWARENESS based on Grok-1's reward shaping design.
        
        This replaces the naive length-based reward with meaning-aware scoring that
        teaches organisms semantic coherence rather than just rewarding any output.
        
        Components:
        1. Word overlap: Relevance to user message (0.0-0.25)
        2. Coherence: Structural quality indicators (0.0-0.25)
        3. Length appropriateness: Neither too short nor too long (0.0-0.2)
        4. Confidence scaling: Model confidence adjustment (0.0-0.2)
        5. VP awareness: Network vitality influence (±0.1)
        """
        try:
            # Base reward for generating any response (changed from 0.0 to ensure non-zero)
            reward = 0.3  # Baseline reward for participation
            
            # Handle empty response case
            if not organism_response or len(organism_response.strip()) == 0:
                self._log_debug("REWARD_CALC", "Empty response penalty", {"reward": -0.1})
                return -0.1  # Small penalty for empty responses
            
            # Normalize text for comparison
            user_words = set(user_message.lower().split())
            response_words = organism_response.lower().split()
            response_words_set = set(response_words)
            
            # 1. WORD OVERLAP SCORE (0.0 - 0.25)
            # Measures semantic relevance to user message
            # Filter out very common words for meaningful overlap
            stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                         'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                         'could', 'should', 'may', 'might', 'must', 'shall', 'can',
                         'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'who',
                         'this', 'that', 'to', 'of', 'in', 'for', 'on', 'with', 'at'}
            
            user_content_words = user_words - stopwords
            response_content_words = response_words_set - stopwords
            
            if user_content_words and response_content_words:
                overlap = len(user_content_words & response_content_words)
                max_possible = min(len(user_content_words), len(response_content_words))
                overlap_score = (overlap / max_possible) * 0.25 if max_possible > 0 else 0.0
            else:
                overlap_score = 0.1  # Increased base for having any response
            
            reward += overlap_score
            
            # 2. COHERENCE SCORE (0.0 - 0.25)
            # Measures structural quality of the response
            coherence_score = 0.0
            
            # Check for basic sentence structure (starts capital, has some length)
            if organism_response[0].isupper():
                coherence_score += 0.05
            
            # Check for sentence ending punctuation
            if organism_response.rstrip()[-1] in '.!?':
                coherence_score += 0.05
            
            # Penalize pure echoing (just repeating user input)
            if organism_response.strip().lower() == user_message.strip().lower():
                coherence_score -= 0.1  # Penalty for pure echoing
            
            # GROK-3 FIX: Stronger repetition penalty - not just variety bonus
            # GROK REVIEW FIX: Initialize unique_ratio before conditional so it's always defined
            unique_ratio = 1.0  # Default to 1.0 (no repetition) for single-word responses
            if len(response_words) > 1:
                unique_ratio = len(response_words_set) / len(response_words)
                # Bonus for variety
                coherence_score += unique_ratio * 0.15
                # PENALTY for repetition ("was was was" gets unique_ratio=0.2, penalty=-0.24)
                if unique_ratio < 0.5:
                    coherence_score -= (1.0 - unique_ratio) * 0.3  # Heavy penalty for repetition
                # Check for consecutive repetition (n-gram detection)
                consecutive_repeats = 0
                for i in range(1, len(response_words)):
                    if response_words[i] == response_words[i-1]:
                        consecutive_repeats += 1
                if consecutive_repeats > 0:
                    coherence_score -= consecutive_repeats * 0.15  # -0.15 per consecutive repeat
            
            # Check for multiple words (indicates more than just noise)
            if len(response_words) >= 2:
                coherence_score += 0.05
            
            reward += max(0.0, coherence_score)  # Don't let coherence go negative
            
            # 3. LENGTH APPROPRIATENESS (0.0 - 0.2)
            # Goldilocks zone: neither too short nor too long
            response_length = len(response_words)
            if response_length == 0:
                length_score = 0.0
            elif response_length <= 2:
                length_score = 0.05  # Very short
            elif response_length <= 10:
                length_score = 0.2   # Good range
            elif response_length <= 20:
                length_score = 0.15  # Slightly verbose
            else:
                length_score = 0.1   # Too long, slight penalty
            
            reward += length_score
            
            # 4. CONFIDENCE SCALING (0.0 - 0.2)
            # Model's own confidence in the response
            reward += confidence * 0.2
            
            # 5. VP-AWARE ADJUSTMENT (±0.1)
            # Higher VP = more resources = higher standards
            vp_adjustment = 0.0
            if network_state:
                vp_value = network_state.get('vp_value', 0.5)
                # Defensive: ensure vp_value is not None
                if vp_value is None:
                    vp_value = 0.5
                
                # High VP: reward quality more, penalize poor responses
                if vp_value > 0.7:
                    # At high VP, expect better responses
                    if reward > 0.5:
                        vp_adjustment = 0.1  # Bonus for quality at high VP
                        reward += vp_adjustment
                    elif reward < 0.2:
                        vp_adjustment = -0.05  # Slight penalty for poor at high VP
                        reward += vp_adjustment
                elif vp_value < 0.3:
                    # At low VP, be more forgiving
                    reward = max(reward, 0.0)  # No negative rewards when struggling
            
            # GROK-3 FIX: Allow negative rewards for severe repetition
            # Repetitive outputs should not get positive reinforcement
            # GROK REVIEW FIX: Reuse unique_ratio from earlier (line ~880) instead of recalculating
            # unique_ratio was already calculated in the coherence section above
            # GROK STABILIZE FIX: Allow rewards to go lower for proper learning signal
            if len(response_words) > 1 and unique_ratio < 0.3:  # Severe repetition
                final_reward = max(-0.3, min(1.0, reward))  # Allow more negative for severe cases
            elif len(response_words) > 1 and unique_ratio < 0.5:  # Moderate repetition
                final_reward = max(0.0, min(1.0, reward))  # Allow zero but not negative
            else:
                final_reward = max(0.05, min(1.0, reward))  # Very low floor for normal output
            
            # ═══════════════════════════════════════════════════════════════
            # MISSION 1: Track semantic reward components for CRA/AutoTune
            # ═══════════════════════════════════════════════════════════════
            self.semantic_reward_totals['word_overlap'] += overlap_score
            self.semantic_reward_totals['coherence'] += max(0.0, coherence_score)
            self.semantic_reward_totals['length_score'] += length_score
            self.semantic_reward_totals['confidence'] += confidence * 0.2
            self.semantic_reward_totals['vp_adjustment'] += vp_adjustment
            self.semantic_reward_totals['total_reward'] += final_reward
            self.semantic_reward_totals['calculation_count'] += 1
            
            # Log reward components for debugging
            self._log_debug("REWARD_CALC_COMPLETE", "Semantic reward calculated", {
                "components": {
                    "overlap": overlap_score,
                    "coherence": max(0.0, coherence_score),
                    "length": length_score,
                    "confidence": confidence * 0.2,
                    "vp_adjustment": vp_adjustment
                },
                "final_reward": final_reward,
                "response_preview": organism_response[:50] if organism_response else ""
            })
            
            return final_reward
            
        except Exception as e:
            # Fallback: Return safe default if reward calculation fails
            logger.warning(f"Semantic reward calculation failed: {e}, returning 0.3")
            self._log_debug("REWARD_CALC_ERROR", f"Exception in reward calculation: {e}", {"fallback_reward": 0.3})
            return 0.3  # Changed from 0.0 to 0.3 for safe non-zero fallback

    def _trigger_bootstrap_learning(self, organism: Any, user_tokens: List[int], 
                                      network_state: Optional[Dict[str, Any]] = None):
        """
        Trigger bootstrap learning for organisms that generated empty responses.
        Uses teacher forcing with user tokens to help organism learn.
        """
        if not self.trainer or not hasattr(self.trainer, 'bootstrap_language_learning'):
            # Fallback: manual bootstrap if trainer doesn't have the method
            try:
                if hasattr(organism, 'token_sequence') and user_tokens:
                    # Add user tokens to organism's sequence for learning
                    for token in user_tokens:
                        organism.token_sequence.append(token)
                    
                    self._log_debug("STEP_4", f"Bootstrap tokens added for {getattr(organism, 'species_id', 'unknown')}", {
                        "tokens_added": len(user_tokens),
                        "method": "direct_token_injection"
                    })
            except Exception as e:
                logger.debug(f"Bootstrap learning fallback failed: {e}")
            return
        
        try:
            # Use trainer's bootstrap method if available
            self.trainer.bootstrap_language_learning(organism, user_tokens, network_state)
            self.chat_training_triggered += 1
            
            self._log_debug("STEP_4", f"Bootstrap learning triggered for {getattr(organism, 'species_id', 'unknown')}", {
                "tokens_used": len(user_tokens),
                "method": "trainer_bootstrap"
            })
        except Exception as e:
            logger.debug(f"Bootstrap learning failed: {e}")
    
    def _trigger_chat_training(self, organism: Any, network_state: Optional[Dict[str, Any]] = None):
        """
        Trigger training from accumulated chat experiences.
        Called periodically to close the experience→training→generation loop.
        """
        if not self.trainer:
            return
        
        try:
            # Use trainer's chat training method if available
            if hasattr(self.trainer, 'train_from_chat_experiences'):
                loss = self.trainer.train_from_chat_experiences(organism, network_state)
                if loss is not None:
                    self.chat_training_triggered += 1
                    self._log_debug("STEP_4", f"Chat training completed for {getattr(organism, 'species_id', 'unknown')}", {
                        "loss": loss,
                        "total_experiences": self.total_chat_experiences
                    })
            else:
                # Fallback: use regular train_step if available
                if hasattr(self.trainer, 'train_step'):
                    organisms = {getattr(organism, 'species_id', 'unknown'): organism}
                    loss = self.trainer.train_step(organisms, network_state or {})
                    if loss is not None:
                        self.chat_training_triggered += 1
        except Exception as e:
            logger.debug(f"Chat training failed: {e}")
    
    def _broadcast_successful_response(self,
                                        source_organism: Any,
                                        user_tokens: List[int],
                                        response_tokens: List[int],
                                        reward: float,
                                        network_state: Dict[str, Any]):
        """
        Broadcast successful response to connected organisms for knowledge transfer.
        
        Based on Grok-2's inter-organism knowledge transfer design:
        - Successful responses (high reward) are shared with network neighbors
        - Connected organisms learn from the success without direct experience
        - This accelerates ecosystem-level language learning
        
        Args:
            source_organism: The organism that generated the successful response
            user_tokens: Input tokens (user message)
            response_tokens: Output tokens (successful response)
            reward: The reward score (should be > 0.6 to broadcast)
            network_state: Network state containing connection information
        """
        try:
            source_id = getattr(source_organism, 'species_id', str(id(source_organism)))
            
            # ═══════════════════════════════════════════════════════════════
            # MISSION 5: Use NetworkGraphAccessor for null-safe graph access
            # ═══════════════════════════════════════════════════════════════
            try:
                from reality_simulator.symbiotic_network import NetworkGraphAccessor
                graph_accessor = NetworkGraphAccessor(network_state)
            except ImportError:
                # Fallback: use direct access if accessor not available
                graph_accessor = None
            
            if graph_accessor is not None and graph_accessor.is_valid:
                # Use safe accessor
                if not graph_accessor.has_node(source_id):
                    return
                neighbors = graph_accessor.get_neighbors(source_id)
            else:
                # Fallback: direct access (legacy behavior)
                network_graph = network_state.get('network_graph')
                if network_graph is None:
                    return
                if source_id not in network_graph:
                    return
                neighbors = list(network_graph.neighbors(source_id))
            
            if not neighbors:
                return
            
            # Calculate distillation strength based on connection strength and reward
            transfer_count = 0
            for neighbor_id in neighbors:
                neighbor_organism = self.organisms.get(neighbor_id)
                if neighbor_organism is None:
                    continue
                
                if not hasattr(neighbor_organism, 'experience_buffer') or neighbor_organism.experience_buffer is None:
                    continue
                
                # Get connection strength from network graph (using accessor if available)
                if graph_accessor is not None and graph_accessor.is_valid:
                    edge_data = graph_accessor.get_edge_data(source_id, neighbor_id)
                else:
                    edge_data = network_graph.get_edge_data(source_id, neighbor_id, {})
                connection_strength = edge_data.get('strength', 0.5)
                
                # Calculate discounted reward for knowledge transfer
                # Neighbors learn from success but at reduced reward (avoid free-riding)
                transfer_reward = reward * connection_strength * 0.5  # 50% discount + strength scaling
                
                # Only transfer if reward is still meaningful
                if transfer_reward < 0.15:
                    continue
                
                # Get VP value
                vp_val = network_state.get('vp_value')
                
                # Create state for neighbor (use minimal state since we don't have their exact context)
                neighbor_state = np.array([
                    getattr(neighbor_organism, 'fitness', 0.5),
                    transfer_reward,
                    len(response_tokens)
                ])
                
                # Store transferred experience in neighbor's buffer
                # Mark with distillation_metadata to distinguish from direct experience
                neighbor_organism.experience_buffer.add(
                    state=neighbor_state,
                    action=0,
                    reward=transfer_reward,
                    next_state=neighbor_state,
                    done=False,
                    input_tokens=user_tokens,
                    target_tokens=response_tokens,
                    vp_value=vp_val
                )
                
                transfer_count += 1
            
            if transfer_count > 0:
                self._log_debug("STEP_4", f"Knowledge transfer from {source_id}", {
                    "source_organism": source_id,
                    "recipients": transfer_count,
                    "original_reward": reward,
                    "neighbor_ids": neighbors[:5]  # Log first 5
                })
                
                # ═══════════════════════════════════════════════════════════════
                # MISSION 1: Track knowledge transfer stats for CRA/AutoTune
                # ═══════════════════════════════════════════════════════════════
                self.knowledge_transfer_stats['total_broadcasts'] += 1
                self.knowledge_transfer_stats['total_recipients'] += transfer_count
                self.knowledge_transfer_stats['total_reward_transferred'] += reward * transfer_count * 0.25  # Approx
                self.knowledge_transfer_stats['successful_transfers'] += transfer_count
                
                # Emit knowledge transfer event
                if self.event_emitter:
                    try:
                        from causation_explorer import Event
                        event = Event(
                            timestamp=time.time(),
                            component='butterfly_chat',
                            event_type='knowledge_transfer',
                            data={
                                'source_organism': source_id,
                                'recipients': transfer_count,
                                'total_neighbors': len(neighbors),
                                'original_reward': reward,
                                'input_tokens_count': len(user_tokens),
                                'response_tokens_count': len(response_tokens)
                            }
                        )
                        self.event_emitter(event)
                    except Exception as e:
                        logger.debug(f"Knowledge transfer event emission failed: {e}")
        
        except Exception as e:
            logger.debug(f"Knowledge transfer failed: {e}")

    def _emit_chat_events(self,
                          user_message: str,
                          prompt_tokens: List[int],
                          organism_responses: List[Dict[str, Any]],
                          aggregated_response: str) -> List[str]:
        """
        Emit causation events and return list of event IDs.
        Uses adaptive thresholds based on population statistics.
        
        Returns:
            List of event IDs in order: [message_event_id, ...response_event_ids...]
        """
        event_ids = []
        if not self.event_emitter:
            return event_ids
        try:
            from causation_explorer import Event
            
            # Calculate population statistics for adaptive thresholds
            confidences = [r.get('confidence', 0.0) for r in organism_responses]
            fitnesses = [r.get('fitness', 0.0) for r in organism_responses]
            
            # Adaptive thresholds: use percentile-based (top 25%) or minimum floor
            if confidences:
                confidence_threshold = max(0.3, np.percentile(confidences, 75))
                fitness_threshold = max(0.3, np.percentile(fitnesses, 75))
            else:
                confidence_threshold = 0.3
                fitness_threshold = 0.3
            
            # Calculate diversity metrics
            fitness_variance = np.var(fitnesses) if fitnesses else 0.0
            confidence_variance = np.var(confidences) if confidences else 0.0
            unique_responses = len(set(r.get('response', '') for r in organism_responses))
            
            # User message event with diversity metrics
            message_event = Event(
                timestamp=time.time(),
                component='butterfly_chat',
                event_type='butterfly_chat_message',
                data={
                    'message': user_message, 
                    'tokens': prompt_tokens, 
                    'num_organisms_queried': len(organism_responses),
                    'fitness_variance': float(fitness_variance),
                    'confidence_variance': float(confidence_variance),
                    'unique_responses': unique_responses,
                    'adaptive_confidence_threshold': float(confidence_threshold),
                    'adaptive_fitness_threshold': float(fitness_threshold)
                }
            )
            self.event_emitter(message_event)
            event_ids.append(message_event.event_id)
            
            self._log_debug("STEP_6", "Message Event Emitted", {
                "event_id": message_event.event_id,
                "event_type": "butterfly_chat_message",
                "adaptive_thresholds": {
                    "confidence": confidence_threshold,
                    "fitness": fitness_threshold
                }
            })
            
            # Emit diversity analysis event if variance is low
            if fitness_variance < 0.01 and len(organism_responses) > 5:
                diversity_event = Event(
                    timestamp=time.time(),
                    component='butterfly_chat',
                    event_type='organism_diversity_analysis',
                    data={
                        'fitness_variance': float(fitness_variance),
                        'confidence_variance': float(confidence_variance),
                        'population_size': len(organism_responses),
                        'unique_responses': unique_responses,
                        'is_converged': fitness_variance < 0.001,
                        'recommendation': 'Population may need diversity injection' if fitness_variance < 0.001 else 'Low diversity detected'
                    }
                )
                self.event_emitter(diversity_event)
                event_ids.append(diversity_event.event_id)

            # Emit response events using ADAPTIVE thresholds (not hardcoded 0.7)
            responses_emitted = 0
            for resp in organism_responses:
                confidence = resp.get('confidence', 0.0)
                fitness = resp.get('fitness', 0.0)
                
                # Use adaptive thresholds based on population statistics
                if confidence >= confidence_threshold and fitness >= fitness_threshold:
                    response_event = Event(
                        timestamp=time.time(),
                        component='butterfly_chat',
                        event_type='butterfly_chat_response',
                        data={
                            'organism_id': resp.get('organism_id'), 
                            'response': resp.get('response'), 
                            'tokens': resp.get('tokens'), 
                            'confidence': confidence,
                            'fitness': fitness
                        }
                    )
                    self.event_emitter(response_event)
                    event_ids.append(response_event.event_id)
                    responses_emitted += 1
                    
                    self._log_debug("STEP_6", f"Response Event Emitted for {resp.get('organism_id')}", {
                        "event_id": response_event.event_id,
                        "event_type": "butterfly_chat_response",
                        "organism_id": resp.get('organism_id')
                    })
        except ImportError:
            logger.warning("CausationExplorer not available, skipping event emission")
        except Exception as e:
            logger.error(f"Error emitting chat events: {e}", exc_info=True)
            self._log_error("EVENT_EMISSION_ERROR", f"Failed to emit events: {e}", {
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
        
        return event_ids

    # =========================================================================
    # 🆕 ATOMIC LANGUAGE INTEGRATION
    # Query organisms' linguistic atoms for deeper understanding
    # =========================================================================
    
    def get_organism_concepts(self, organism_id: str, top_k: int = 10) -> Dict[str, Any]:
        """
        Get the top concepts for a specific organism.
        
        Args:
            organism_id: ID of the organism to query
            top_k: Number of top concepts to return
            
        Returns:
            Dictionary with concept information
        """
        if organism_id not in self.organisms:
            return {'error': f'Organism {organism_id} not found'}
        
        organism = self.organisms[organism_id]
        
        if not hasattr(organism, 'atomic_language') or organism.atomic_language is None:
            return {'error': f'Organism {organism_id} has no atomic language system'}
        
        # Get activated concepts with default VP state
        concepts = organism.get_activated_concepts((0.5, 0.5), top_k=top_k)
        
        return {
            'organism_id': organism_id,
            'total_concepts': len(organism.atomic_language.atoms),
            'top_concepts': [{'concept': c, 'activation': float(a)} for c, a in concepts],
            'dialect_signature': organism.get_dialect_signature().tolist()
        }
    
    def get_population_linguistic_stats(self) -> Dict[str, Any]:
        """
        Get linguistic statistics across the population.
        
        Returns:
            Dictionary with population-level language stats
        """
        stats = {
            'total_organisms': len(self.organisms),
            'organisms_with_atomic_language': 0,
            'avg_concepts_per_organism': 0,
            'total_unique_concepts': set(),
            'concept_frequency': defaultdict(int)
        }
        
        concept_counts = []
        
        for org_id, organism in self.organisms.items():
            if hasattr(organism, 'atomic_language') and organism.atomic_language is not None:
                stats['organisms_with_atomic_language'] += 1
                concept_counts.append(len(organism.atomic_language.atoms))
                
                for concept_id in organism.atomic_language.atoms.keys():
                    stats['total_unique_concepts'].add(concept_id)
                    stats['concept_frequency'][concept_id] += 1
        
        if concept_counts:
            stats['avg_concepts_per_organism'] = sum(concept_counts) / len(concept_counts)
        
        stats['total_unique_concepts'] = len(stats['total_unique_concepts'])
        
        # Convert defaultdict to regular dict and get top 20
        freq_sorted = sorted(stats['concept_frequency'].items(), key=lambda x: x[1], reverse=True)
        stats['top_concepts'] = freq_sorted[:20]
        del stats['concept_frequency']  # Too large
        
        return stats
    
    # =========================================================================
    # 🆕 MISSION 1: CRA DIAGNOSTIC STATS - Agent Swarm Learning Metrics
    # Exposes all language learning metrics for CRA and AutoTune integration
    # =========================================================================
    
    def get_agent_swarm_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive agent swarm statistics for CRA diagnostics.
        
        This method exposes all language learning metrics that the CRA
        needs to display and that AutoTune needs for closed-loop optimization.
        
        Returns:
            Dictionary with all swarm learning metrics including:
            - semantic_reward_stats: Breakdown of reward components
            - knowledge_transfer_stats: Broadcast/recipient counts
            - creative_vocab_stats: Vocabulary expansion metrics
            - population_stats: Overall organism language health
        """
        # Calculate averages from totals
        count = max(1, self.semantic_reward_totals.get('calculation_count', 1))
        
        semantic_stats = {
            'total_calculations': self.semantic_reward_totals.get('calculation_count', 0),
            'avg_word_overlap': self.semantic_reward_totals.get('word_overlap', 0) / count,
            'avg_coherence': self.semantic_reward_totals.get('coherence', 0) / count,
            'avg_length_score': self.semantic_reward_totals.get('length_score', 0) / count,
            'avg_confidence': self.semantic_reward_totals.get('confidence', 0) / count,
            'avg_vp_adjustment': self.semantic_reward_totals.get('vp_adjustment', 0) / count,
            'avg_total_reward': self.semantic_reward_totals.get('total_reward', 0) / count,
            'total_word_overlap': self.semantic_reward_totals.get('word_overlap', 0),
            'total_coherence': self.semantic_reward_totals.get('coherence', 0),
            'total_length_score': self.semantic_reward_totals.get('length_score', 0),
            'total_reward_sum': self.semantic_reward_totals.get('total_reward', 0)
        }
        
        # Calculate transfer efficiency
        broadcasts = max(1, self.knowledge_transfer_stats.get('total_broadcasts', 1))
        transfer_stats = {
            'total_broadcasts': self.knowledge_transfer_stats.get('total_broadcasts', 0),
            'total_recipients': self.knowledge_transfer_stats.get('total_recipients', 0),
            'total_reward_transferred': self.knowledge_transfer_stats.get('total_reward_transferred', 0),
            'successful_transfers': self.knowledge_transfer_stats.get('successful_transfers', 0),
            'avg_recipients_per_broadcast': self.knowledge_transfer_stats.get('total_recipients', 0) / broadcasts,
            'transfer_efficiency': self.knowledge_transfer_stats.get('successful_transfers', 0) / broadcasts
        }
        
        # Creative vocabulary stats
        vocab_stats = {
            'total_expansions': self.creative_vocab_stats.get('expansions', 0),
            'phrases_generated': self.creative_vocab_stats.get('phrases_generated', 0),
            'compounds_created': self.creative_vocab_stats.get('compounds_created', 0),
            'neologisms_minted': self.creative_vocab_stats.get('neologisms', 0)
        }
        
        # Population-level stats
        organisms_with_language = sum(
            1 for org in self.organisms.values()
            if hasattr(org, 'atomic_language') and org.atomic_language is not None
        )
        
        population_stats = {
            'total_organisms': len(self.organisms),
            'organisms_with_language': organisms_with_language,
            'language_adoption_rate': organisms_with_language / max(1, len(self.organisms)),
            'total_chat_experiences': self.total_chat_experiences,
            'chat_training_triggered': self.chat_training_triggered
        }
        
        return {
            'semantic_reward_stats': semantic_stats,
            'knowledge_transfer_stats': transfer_stats,
            'creative_vocab_stats': vocab_stats,
            'population_stats': population_stats,
            'timestamp': time.time(),
            'version': '1.0.0'  # For API versioning
        }
    
    def reset_swarm_stats(self) -> None:
        """Reset all tracking statistics. Useful for benchmarking."""
        self.semantic_reward_totals = {
            'word_overlap': 0.0,
            'coherence': 0.0,
            'length_score': 0.0,
            'confidence': 0.0,
            'vp_adjustment': 0.0,
            'total_reward': 0.0,
            'calculation_count': 0
        }
        self.knowledge_transfer_stats = {
            'total_broadcasts': 0,
            'total_recipients': 0,
            'total_reward_transferred': 0.0,
            'successful_transfers': 0
        }
        self.creative_vocab_stats = {
            'expansions': 0,
            'phrases_generated': 0,
            'compounds_created': 0,
            'neologisms': 0
        }
    
    def explain_organism_dialect(self, organism_id: str) -> Dict[str, Any]:
        """
        Get a detailed explanation of an organism's linguistic development.
        
        This is what Butterfly Chat uses to explain WHY an organism
        developed its particular "dialect".
        
        Args:
            organism_id: ID of the organism
            
        Returns:
            Detailed dialect explanation
        """
        if organism_id not in self.organisms:
            return {'error': f'Organism {organism_id} not found'}
        
        organism = self.organisms[organism_id]
        
        if not hasattr(organism, 'atomic_language') or organism.atomic_language is None:
            return {'error': f'Organism {organism_id} has no atomic language system'}
        
        als = organism.atomic_language
        
        # Get concept graph
        graph = organism.get_concept_graph()
        
        # Find strongest associations
        strongest_associations = []
        for edge in graph['edges']:
            strongest_associations.append({
                'from': edge['source'],
                'to': edge['target'],
                'strength': edge['strength'],
                'reason': edge['reason']
            })
        strongest_associations.sort(key=lambda x: abs(x['strength']), reverse=True)
        
        # Get concepts by source (innate vs learned)
        concepts_by_source = defaultdict(list)
        for concept_id, atom in als.atoms.items():
            concepts_by_source[atom.source].append({
                'concept': concept_id,
                'strength': atom.strength,
                'usage_count': atom.usage_count
            })
        
        # Get VP affinities
        vp_profile = {
            'high_vitality': [],
            'low_vitality': [],
            'high_pleasure': [],
            'low_pleasure': []
        }
        for concept_id, atom in als.atoms.items():
            if atom.vp_vitality_affinity > 0.7:
                vp_profile['high_vitality'].append(concept_id)
            elif atom.vp_vitality_affinity < 0.3:
                vp_profile['low_vitality'].append(concept_id)
            if atom.vp_pleasure_affinity > 0.7:
                vp_profile['high_pleasure'].append(concept_id)
            elif atom.vp_pleasure_affinity < 0.3:
                vp_profile['low_pleasure'].append(concept_id)
        
        return {
            'organism_id': organism_id,
            'total_concepts': len(als.atoms),
            'total_associations': len(graph['edges']),
            'concepts_by_source': dict(concepts_by_source),
            'strongest_associations': strongest_associations[:10],
            'vp_profile': vp_profile,
            'dialect_signature': organism.get_dialect_signature().tolist(),
            'creation_time': als.creation_time
        }

