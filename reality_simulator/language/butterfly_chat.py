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

    def route_message(self,
                     message: str,
                     routing_strategy: str = "all",
                     max_organisms: Optional[int] = None,
                     network_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Route message to organisms and aggregate responses.

        Returns: dict with response, organism_responses, tokens_used, routing_info
        """
        # Tokenize user message
        words = message.lower().split()
        if self.vocabulary is not None:
            try:
                prompt_tokens = self.vocabulary.encode(words, add_special=True)
            except Exception:
                prompt_tokens = []
        else:
            prompt_tokens = []

        # Select organisms based on strategy
        selected_organisms = self._select_organisms(
            routing_strategy, max_organisms, words, network_state
        )

        # Generate responses from each organism
        organism_responses = []
        for org_id, organism in selected_organisms.items():
            try:
                # Prefer a generate_tokens method, otherwise try a 'respond' callable
                if hasattr(organism, 'generate_tokens'):
                    response_tokens = organism.generate_tokens(prompt_tokens, max_length=50)
                elif hasattr(organism, 'respond'):
                    # respond may accept text
                    response_text = organism.respond(message)
                    response_tokens = self.vocabulary.encode(response_text.split(), add_special=True) if self.vocabulary else []
                else:
                    response_tokens = []

                response_words = self.vocabulary.decode(response_tokens, skip_special=True) if self.vocabulary else [str(t) for t in response_tokens]
                response_text = ' '.join(response_words) if isinstance(response_words, list) else str(response_words)

                organism_responses.append({
                    'organism_id': org_id,
                    'response': response_text,
                    'tokens': response_tokens,
                    'fitness': float(getattr(organism, 'fitness', 0.0)),
                    'confidence': self._calculate_confidence(response_tokens)
                })
            except Exception as e:
                logger.warning(f"Organism {org_id} failed to generate response: {e}")
                continue

        # Aggregate responses
        aggregated_response = self._aggregate_responses(organism_responses)

        # Emit causation events
        if self.event_emitter:
            self._emit_chat_events(message, prompt_tokens, organism_responses, aggregated_response)

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

        return {
            'response': aggregated_response,
            'organism_responses': organism_responses,
            'tokens_used': prompt_tokens,
            'routing_info': {
                'strategy': routing_strategy,
                'organisms_queried': len(selected_organisms),
                'organisms_responded': len(organism_responses)
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
        elif strategy == 'random':
            # Pick a random sample of items
            keys = list(all_orgs.keys())
            k = min(max_organisms or len(keys), len(keys))
            chosen = list(np.random.choice(keys, size=k, replace=False)) if k > 0 else []
            selected = {k: all_orgs[k] for k in chosen}
        elif strategy == 'fittest':
            sorted_orgs = sorted(all_orgs.items(), key=lambda x: getattr(x[1], 'fitness', 0.0), reverse=True)
            selected = dict(sorted_orgs[:(max_organisms or len(sorted_orgs))])
        elif strategy == 'connected':
            if network_state:
                connections = network_state.get('connections', {})
                org_connection_counts = defaultdict(int)
                for (a, b) in connections.keys():
                    org_connection_counts[a] += 1
                    org_connection_counts[b] += 1
                sorted_orgs = sorted(all_orgs.items(), key=lambda x: org_connection_counts.get(x[0], 0), reverse=True)
                selected = dict(sorted_orgs[:(max_organisms or len(sorted_orgs))])
            else:
                selected = all_orgs
        elif strategy == 'by_word':
            selected = {}
            # Best-effort: if network_state has language_anchors mapping words -> organism ids
            if network_state:
                anchors = network_state.get('language_anchors', {})
                for word in message_words:
                    for oid in anchors.get(word, []):
                        oid_str = str(oid)
                        if oid_str in all_orgs:
                            selected[oid_str] = all_orgs[oid_str]
            if not selected:
                selected = all_orgs
        else:
            selected = all_orgs

        return selected

    def _aggregate_responses(self, organism_responses: List[Dict[str, Any]]) -> str:
        if not organism_responses:
            return "<no response>"

        weighted_responses = []
        total_weight = 0.0
        for resp in organism_responses:
            weight = max(resp.get('fitness', 0.0), 0.0) * max(resp.get('confidence', 0.0), 0.0)
            weighted_responses.append((weight, resp.get('response', '')))
            total_weight += weight

        if total_weight == 0.0:
            return ' '.join([r['response'] for r in organism_responses if r.get('response')])

        best_response = max(weighted_responses, key=lambda x: x[0])[1]
        return best_response

    def _calculate_confidence(self, tokens: List[int]) -> float:
        if not tokens:
            return 0.0
        unique_tokens = len(set(tokens))
        total_tokens = len(tokens)
        diversity = unique_tokens / max(total_tokens, 1)
        length_score = min(total_tokens / 20.0, 1.0)
        return (diversity * 0.6 + length_score * 0.4)

    def _emit_chat_events(self,
                          user_message: str,
                          prompt_tokens: List[int],
                          organism_responses: List[Dict[str, Any]],
                          aggregated_response: str):
        if not self.event_emitter:
            return
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

            # Response events
            for resp in organism_responses:
                response_event = Event(
                    timestamp=time.time(),
                    component='butterfly_chat',
                    event_type='butterfly_chat_response',
                    data={'organism_id': resp.get('organism_id'), 'response': resp.get('response'), 'tokens': resp.get('tokens'), 'confidence': resp.get('confidence'), 'fitness': resp.get('fitness')}
                )
                self.event_emitter(response_event)
        except ImportError:
            logger.warning("CausationExplorer not available, skipping event emission")
