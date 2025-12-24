"""
WIKAI API Client - Connects to HuggingFace Space API

Instead of local pattern storage, this connects to the WIKAI Commons
hosted at https://huggingface.co/spaces/tostido/Wikai

API Endpoints:
- POST /api/predict - Submit new pattern
- GET /api/list - List all patterns
- POST /api/query - Search/query patterns
- GET /rest/patterns - Simple REST list
- GET /rest/patterns/{id} - Get specific pattern
- POST /rest/patterns - Submit pattern
- GET /rest/search?q=keyword - Search

Usage:
    from wikai.api_client import WIKAIClient
    
    client = WIKAIClient()
    
    # Submit a pattern
    pattern_id = client.submit_pattern(
        title="The Neural Training Pattern",
        axiom="Stable patterns propagate; unstable patterns dissolve",
        domain="General Intelligence",
        stability=0.95,
        tags=["neural", "training", "convergence"]
    )
    
    # Query patterns
    patterns = client.list_patterns()
    pattern = client.get_pattern("WIKAI_0001")
    results = client.search("convergence")
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

WIKAI_API_BASE = "https://tostido-wikai.hf.space"


@dataclass
class WIKAIPattern:
    """A pattern from the WIKAI Commons"""
    id: str
    title: str
    axiom: str
    domain: str = "General Intelligence"
    stability: float = 0.0
    tags: List[str] = None
    timestamp: str = ""
    reasoning_chain: List[str] = None
    origin: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.reasoning_chain is None:
            self.reasoning_chain = []
        if self.origin is None:
            self.origin = {}


class WIKAIClient:
    """
    Client for the WIKAI Commons API on HuggingFace Spaces.
    
    This replaces the local librarian/observer with API calls to the
    centralized WIKAI Commons at https://huggingface.co/spaces/tostido/Wikai
    """
    
    def __init__(self, base_url: str = WIKAI_API_BASE, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make an API request with error handling."""
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault("timeout", self.timeout)
        
        try:
            response = self._session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.warning(f"WIKAI API timeout: {endpoint}")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"WIKAI API error: {e}")
            return None
        except json.JSONDecodeError:
            logger.warning(f"WIKAI API invalid JSON from {endpoint}")
            return None
    
    # ═══════════════════════════════════════════════════════════════════════════
    # REST API (Simple endpoints)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def list_patterns(self) -> List[WIKAIPattern]:
        """List all patterns from the Commons."""
        result = self._request("GET", "/rest/patterns")
        if not result:
            return []
        
        patterns = []
        entries = result if isinstance(result, list) else result.get("entries", [])
        for entry in entries:
            try:
                patterns.append(WIKAIPattern(
                    id=entry.get("id", ""),
                    title=entry.get("title", ""),
                    axiom=entry.get("axiom", ""),
                    domain=entry.get("domain", "General Intelligence"),
                    stability=float(entry.get("stability", 0)),
                    tags=entry.get("tags", []),
                    timestamp=entry.get("timestamp", ""),
                    reasoning_chain=entry.get("reasoning_chain", []),
                    origin=entry.get("origin", {})
                ))
            except Exception as e:
                logger.debug(f"Failed to parse pattern: {e}")
        
        return patterns
    
    def get_pattern(self, pattern_id: str) -> Optional[WIKAIPattern]:
        """Get a specific pattern by ID."""
        result = self._request("GET", f"/rest/patterns/{pattern_id}")
        if not result:
            return None
        
        try:
            return WIKAIPattern(
                id=result.get("id", pattern_id),
                title=result.get("title", ""),
                axiom=result.get("axiom", ""),
                domain=result.get("domain", "General Intelligence"),
                stability=float(result.get("stability", 0)),
                tags=result.get("tags", []),
                timestamp=result.get("timestamp", ""),
                reasoning_chain=result.get("reasoning_chain", []),
                origin=result.get("origin", {})
            )
        except Exception as e:
            logger.warning(f"Failed to parse pattern {pattern_id}: {e}")
            return None
    
    def search(self, query: str) -> List[WIKAIPattern]:
        """Search patterns by keyword."""
        result = self._request("GET", "/rest/search", params={"q": query})
        if not result:
            return []
        
        patterns = []
        entries = result if isinstance(result, list) else result.get("results", [])
        for entry in entries:
            try:
                patterns.append(WIKAIPattern(
                    id=entry.get("id", ""),
                    title=entry.get("title", ""),
                    axiom=entry.get("axiom", ""),
                    domain=entry.get("domain", "General Intelligence"),
                    stability=float(entry.get("stability", 0)),
                    tags=entry.get("tags", [])
                ))
            except:
                pass
        
        return patterns
    
    def submit_pattern(
        self,
        title: str,
        axiom: str,
        domain: str = "General Intelligence",
        stability: float = 0.8,
        tags: List[str] = None,
        reasoning_chain: List[str] = None,
        origin: Dict[str, Any] = None,
        **extra
    ) -> Optional[str]:
        """
        Submit a new pattern to the WIKAI Commons.
        
        Returns the pattern ID if successful, None otherwise.
        """
        if tags is None:
            tags = []
        if reasoning_chain is None:
            reasoning_chain = []
        if origin is None:
            origin = {}
        
        pattern_data = {
            "title": title,
            "axiom": axiom,
            "domain": domain,
            "stability": stability,
            "tags": tags,
            "reasoning_chain": reasoning_chain,
            "origin": origin,
            **extra
        }
        
        result = self._request("POST", "/rest/patterns", json=pattern_data)
        if result:
            return result.get("id") or result.get("pattern_id")
        
        # Fallback to Gradio API format
        gradio_data = {
            "data": [json.dumps(pattern_data)]
        }
        result = self._request("POST", "/api/predict", json=gradio_data)
        if result and "data" in result:
            # Parse response for pattern ID
            response_text = result["data"][0] if result["data"] else ""
            if "WIKAI_" in response_text:
                import re
                match = re.search(r"WIKAI_\d+", response_text)
                if match:
                    return match.group()
        
        return None
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Gradio API (Alternative endpoints)
    # ═══════════════════════════════════════════════════════════════════════════
    
    def query_api(self, query_params: Dict) -> List[Dict]:
        """
        Query via the Gradio /api/query endpoint.
        
        Supports:
        - {"search": "keyword"}
        - {"id": "WIKAI_0001"}
        - {"domain": "Healthcare"}
        - {"tags": ["neural"]}
        """
        result = self._request("POST", "/api/query", json={"data": [json.dumps(query_params)]})
        if result and "data" in result:
            try:
                return json.loads(result["data"][0])
            except:
                pass
        return []
    
    def get_count(self) -> int:
        """Get total pattern count from /api/list."""
        result = self._request("GET", "/api/list")
        if result:
            return result.get("count", 0)
        return 0
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Convenience methods
    # ═══════════════════════════════════════════════════════════════════════════
    
    def patterns_by_domain(self, domain: str) -> List[WIKAIPattern]:
        """Get all patterns in a specific domain."""
        results = self.query_api({"domain": domain})
        return [WIKAIPattern(**p) for p in results if isinstance(p, dict)]
    
    def patterns_by_tag(self, tag: str) -> List[WIKAIPattern]:
        """Get all patterns with a specific tag."""
        results = self.query_api({"tags": [tag]})
        return [WIKAIPattern(**p) for p in results if isinstance(p, dict)]
    
    def recent_patterns(self, limit: int = 10) -> List[WIKAIPattern]:
        """Get most recent patterns."""
        patterns = self.list_patterns()
        return patterns[:limit]
    
    def ping(self) -> bool:
        """Check if the WIKAI API is reachable."""
        try:
            response = self._session.get(f"{self.base_url}/rest/patterns", timeout=5)
            return response.status_code == 200
        except:
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

_client: Optional[WIKAIClient] = None

def get_wikai_client() -> WIKAIClient:
    """Get or create the singleton WIKAI client."""
    global _client
    if _client is None:
        _client = WIKAIClient()
    return _client


# ═══════════════════════════════════════════════════════════════════════════════
# COMPATIBILITY LAYER - Matches old WIKAILibrarian interface
# ═══════════════════════════════════════════════════════════════════════════════

class WIKAILibrarian:
    """
    Compatibility wrapper that mimics the old WIKAILibrarian interface
    but uses the HuggingFace Space API underneath.
    """
    
    def __init__(self, patterns_dir: str = None):
        """patterns_dir is ignored - we use the API."""
        self.client = get_wikai_client()
        self._patterns_cache = {}
        self._cache_time = None
    
    def capture(
        self,
        name: str,
        experiment_id: str = None,
        agents: List[str] = None,
        problem: str = "",
        solution: str = "",
        axiom: str = "",
        reasoning_chain: List[str] = None,
        tokens: Dict = None,
        stability: float = 0.8,
        **kwargs
    ) -> Optional[str]:
        """
        Capture a new pattern - submits to WIKAI API.
        
        Returns pattern ID or None.
        """
        # Build title from name or generate one
        title = name or f"Pattern from {experiment_id or 'unknown'}"
        
        # Build tags from various sources
        tags = list(kwargs.get("tags", []))
        if agents:
            tags.extend([f"agent:{a}" for a in agents[:3]])
        if tokens:
            dominant = tokens.get("dominant", [])[:5]
            tags.extend(dominant)
        
        origin = {
            "experiment_id": experiment_id,
            "agents": agents or [],
            "captured_at": datetime.utcnow().isoformat() + "Z",
            "source": "convergence_engine"
        }
        
        return self.client.submit_pattern(
            title=title,
            axiom=axiom or f"{problem} → {solution}",
            domain=kwargs.get("domain", "General Intelligence"),
            stability=stability,
            tags=tags,
            reasoning_chain=reasoning_chain or [],
            origin=origin,
            problem=problem,
            solution=solution
        )
    
    def query(
        self,
        tags: List[str] = None,
        domain: str = None,
        search: str = None
    ) -> List[WIKAIPattern]:
        """Query patterns from the API."""
        if search:
            return self.client.search(search)
        if domain:
            return self.client.patterns_by_domain(domain)
        if tags:
            # Search for first tag (API limitation)
            return self.client.patterns_by_tag(tags[0])
        return self.client.list_patterns()
    
    def get(self, pattern_id: str) -> Optional[WIKAIPattern]:
        """Get a specific pattern by ID."""
        return self.client.get_pattern(pattern_id)
    
    def list_all(self) -> List[WIKAIPattern]:
        """List all patterns."""
        return self.client.list_patterns()
    
    def count(self) -> int:
        """Get pattern count."""
        return self.client.get_count()
    
    @property
    def patterns_dir(self) -> str:
        """Compatibility - returns dummy path."""
        return "wikai/patterns"


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = [
    "WIKAIClient",
    "WIKAIPattern", 
    "WIKAILibrarian",
    "get_wikai_client",
    "WIKAI_API_BASE"
]
