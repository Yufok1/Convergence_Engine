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
                 event_emitter: Optional[callable] = None):
        """
        Initialize router.

        Args:
            organisms: Dictionary of organism_id -> NeuralOrganism-like objects
            vocabulary: LanguageVocabulary for tokenization (optional)
            event_emitter: Optional function to emit causation events
        """
        self.organisms = organisms or {}
        self.vocabulary = vocabulary
        self.event_emitter = event_emitter
        self.conversation_history: List[Dict[str, Any]] = []
        # Debug logging system
        self.debug_logs: List[Dict[str, Any]] = []
        self.causation_trail: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []

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
                    "vocab_size": len(self.vocabulary) if hasattr(self.vocabulary, '__len__') else 'unknown'
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
                "fallback": "Empty token list"
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
        # Extract context_memory and vp_value from network_state for generate_tokens()
        context_memory = network_state.get('context_memory') if network_state else None
        vp_value = network_state.get('vp_value') if network_state else None
        
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
                    self._log_debug("STEP_4", f"Generating tokens for organism {org_id}", {
                        "method": "generate_tokens",
                        "has_context_memory": context_memory is not None,
                        "vp_value": vp_value,
                        "organism_fitness": float(getattr(organism, 'fitness', 0.0))
                    })
                    # FIXED: Pass context_memory as first argument (required), then optional params
                    response_tokens = organism.generate_tokens(
                        context_memory=context_memory,
                        max_length=50,
                        vp_value=vp_value,
                        temperature=1.0
                    )
                    self._log_debug("STEP_4", f"Tokens generated for {org_id}", {
                        "token_count": len(response_tokens),
                        "tokens": response_tokens[:10]  # First 10 tokens
                    })
                elif hasattr(organism, 'respond'):
                    self._log_debug("STEP_4", f"Using respond method for {org_id}", {
                        "method": "respond",
                        "fallback": True
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
                
                # If response is empty, try to learn from the interaction and use fallback words
                if not response_text or response_text.strip() == '':
                    # Extract words from user message to add to vocabulary
                    if self.vocabulary and words:
                        for word in words:
                            if word not in self.vocabulary.word_to_id:
                                self.vocabulary.add_word(word)
                                self._log_debug("STEP_4", f"Learned new word: {word}", {
                                    "organism_id": org_id,
                                    "word": word,
                                    "vocab_size": self.vocabulary.vocab_size
                                })
                    
                    # If still empty, use a fallback response based on organism state
                    if not response_text or response_text.strip() == '':
                        # Generate a simple fallback response using vocabulary words
                        fallback_words = []
                        if self.vocabulary:
                            # Try to use words that exist in vocabulary
                            available_words = [w for w in self.vocabulary.word_to_id.keys() 
                                             if w not in ['<PAD>', '<UNK>', '<START>', '<END>', '<VP_GATE>']]
                            if available_words:
                                # Use a few random words from vocabulary as fallback
                                import random
                                fallback_words = random.sample(available_words, min(3, len(available_words)))
                                response_text = ' '.join(fallback_words)
                                self._log_debug("STEP_4", f"Using fallback response for {org_id}", {
                                    "organism_id": org_id,
                                    "fallback_words": fallback_words,
                                    "vocab_size": self.vocabulary.vocab_size
                                })
                
                confidence = self._calculate_confidence(response_tokens)
                fitness = float(getattr(organism, 'fitness', 0.0))
                weight = fitness * confidence
                
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
                error_info = {
                    "organism_id": org_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "has_generate_tokens": hasattr(organism, 'generate_tokens'),
                    "has_respond": hasattr(organism, 'respond'),
                    "generation_time_ms": (time.time() - org_start_time) * 1000
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

    def _aggregate_responses(self, organism_responses: List[Dict[str, Any]]) -> str:
        if not organism_responses:
            self._log_error("AGGREGATION_ERROR", "No organism responses to aggregate", {})
            return "<no response>"

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

    def _calculate_confidence(self, tokens: List[int]) -> float:
        if not tokens:
            return 0.0
        unique_tokens = len(set(tokens))
        total_tokens = len(tokens)
        diversity = unique_tokens / max(total_tokens, 1)
        length_score = min(total_tokens / 20.0, 1.0)
        return (diversity * 0.6 + length_score * 0.4)
    
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
            # Calculate reward based on response quality
            # Positive reward for:
            # - Non-empty responses
            # - Higher confidence
            # - Responses that match user intent (simple heuristic: length > 0)
            reward = 0.0
            
            if organism_response and len(organism_response.strip()) > 0:
                # Base reward for generating a response
                reward += 0.5
                
                # Bonus for confidence
                reward += confidence * 0.3
                
                # Bonus for response length (encourages more complete responses)
                response_length = len(organism_response.split())
                reward += min(response_length / 10.0, 0.2)  # Max 0.2 for length
            else:
                # Small negative reward for empty responses
                reward -= 0.1
            
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
            
            # Create experience with language model extensions
            from reality_simulator.neural.experience import Experience
            experience = Experience(
                state=prev_state,
                action=0,  # Chat interaction doesn't map to action space
                reward=reward,
                next_state=state,
                done=False,
                token_sequence=full_token_sequence,
                vp_value=vp_val
            )
            
            # Add to experience buffer
            organism.experience_buffer.add(
                state=prev_state,
                action=0,
                reward=reward,
                next_state=state,
                done=False
            )
            
            # Also store token sequence in organism's token_sequence deque if available
            if hasattr(organism, 'token_sequence'):
                for token in full_token_sequence:
                    organism.token_sequence.append(token)
            
            # Update previous state
            organism.prev_state = state.copy()
            
            self._log_debug("STEP_4", f"Stored chat experience for {organism}", {
                "organism_id": getattr(organism, 'species_id', 'unknown'),
                "reward": reward,
                "response_length": len(organism_response),
                "token_sequence_length": len(full_token_sequence),
                "experience_buffer_size": len(organism.experience_buffer) if hasattr(organism.experience_buffer, '__len__') else 'unknown'
            })
            
        except Exception as e:
            # Don't fail chat if experience storage fails
            self._log_error("EXPERIENCE_STORAGE_ERROR", f"Failed to store chat experience: {e}", {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "organism_id": getattr(organism, 'species_id', 'unknown')
            })
            logger.warning(f"Failed to store chat experience for organism: {e}")

    def _emit_chat_events(self,
                          user_message: str,
                          prompt_tokens: List[int],
                          organism_responses: List[Dict[str, Any]],
                          aggregated_response: str) -> List[str]:
        """
        Emit causation events and return list of event IDs.
        
        Returns:
            List of event IDs in order: [message_event_id, ...response_event_ids...]
        """
        event_ids = []
        if not self.event_emitter:
            return event_ids
        try:
            from causation_explorer import Event
            # User message event
            message_event = Event(
                timestamp=time.time(),
                component='butterfly_chat',
                event_type='butterfly_chat_message',
                data={'message': user_message, 'tokens': prompt_tokens, 'num_organisms_queried': len(organism_responses)}
            )
            self.event_emitter(message_event)
            event_ids.append(message_event.event_id)
            
            self._log_debug("STEP_6", "Message Event Emitted", {
                "event_id": message_event.event_id,
                "event_type": "butterfly_chat_message"
            })

            # Response events
            for resp in organism_responses:
                response_event = Event(
                    timestamp=time.time(),
                    component='butterfly_chat',
                    event_type='butterfly_chat_response',
                    data={
                        'organism_id': resp.get('organism_id'), 
                        'response': resp.get('response'), 
                        'tokens': resp.get('tokens'), 
                        'confidence': resp.get('confidence'), 
                        'fitness': resp.get('fitness')
                    }
                )
                self.event_emitter(response_event)
                event_ids.append(response_event.event_id)
                
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
