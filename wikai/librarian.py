"""
WIKAI Librarian - The Butterfly Collector

This module provides the infrastructure to capture, store, and query
AI interaction patterns for the WIKAI Commons.

Usage:
    from wikai import WIKAILibrarian
    
    librarian = WIKAILibrarian()
    
    # Capture a new pattern
    pattern_id = librarian.capture(
        name="The Iron Wood Protocol",
        experiment_id="ROME_VS_GARDEN_04",
        agents=["Rome_War_Swarm", "Garden_Peace_Swarm"],
        problem="Conflict between opposing philosophies",
        solution="Symbiotic Specialization",
        axiom="Hardness + Softness = Persistence",
        reasoning_chain=[...],
        tokens={"dominant": [...], "emergent": [...]}
    )
    
    # Query patterns
    patterns = librarian.query(tags=["conflict_resolution"])
    pattern = librarian.get("WIKAI_0001")
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib


class WIKAIPattern:
    """A single captured butterfly - a unit of AI wisdom."""
    
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.id = data.get("id")
        self.name = data.get("name")
        self.status = data.get("status", "OBSERVED")
        
    @property
    def axiom(self) -> str:
        """The distilled wisdom in one sentence."""
        return self.data.get("abstract", {}).get("axiom", "")
    
    @property
    def problem(self) -> str:
        return self.data.get("abstract", {}).get("problem", "")
    
    @property
    def solution(self) -> str:
        return self.data.get("abstract", {}).get("solution", "")
    
    @property
    def reasoning_chain(self) -> List[str]:
        return self.data.get("reasoning_chain", [])
    
    @property
    def emergent_tokens(self) -> List[str]:
        return self.data.get("tokens", {}).get("emergent_tokens", [])
    
    @property
    def stability_score(self) -> float:
        return self.data.get("mechanism", {}).get("synthesis", {}).get("stability_score", 0.0)
    
    @property
    def origin(self) -> Dict[str, Any]:
        """Origin metadata: experiment_id, agents, captured timestamp."""
        return self.data.get("origin", {})
    
    @property
    def abstract(self) -> str:
        """The abstract/summary of the pattern."""
        abstract_data = self.data.get("abstract", {})
        if isinstance(abstract_data, dict):
            return abstract_data.get("summary", abstract_data.get("problem", ""))
        return str(abstract_data)
    
    @property
    def mechanism(self) -> str:
        """The mechanism description."""
        mech = self.data.get("mechanism", {})
        if isinstance(mech, dict):
            return json.dumps(mech, indent=2)
        return str(mech)
    
    @property
    def metrics(self) -> Dict[str, Any]:
        """Performance metrics."""
        return self.data.get("metrics", {})
    
    @property
    def tags(self) -> List[str]:
        """Tags for categorization."""
        return self.data.get("tags", [])
    
    def to_dict(self) -> Dict[str, Any]:
        return self.data
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.data, indent=indent)
    
    def __repr__(self):
        return f"<WIKAIPattern {self.id}: {self.name}>"


class WIKAILibrarian:
    """
    The Librarian - captures butterflies and maintains the Commons.
    
    This is the core interface for the WIKAI system. It provides:
    - Pattern capture from agent interactions
    - Pattern storage and retrieval
    - Pattern querying by tags, status, metrics
    - Integration hooks for other butterfly projects
    """
    
    def __init__(self, patterns_dir: Optional[str] = None):
        """
        Initialize the Librarian.
        
        Args:
            patterns_dir: Directory to store pattern files. 
                         Defaults to ./wikai/patterns/
        """
        if patterns_dir is None:
            # Find the wikai directory relative to this file
            self_path = Path(__file__).parent
            patterns_dir = self_path / "patterns"
        
        self.patterns_dir = Path(patterns_dir)
        self.patterns_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache of loaded patterns
        self._cache: Dict[str, WIKAIPattern] = {}
        
        # Load existing patterns
        self._load_patterns()
    
    def _load_patterns(self):
        """Load all patterns from disk into cache."""
        for pattern_file in self.patterns_dir.glob("WIKAI_*.json"):
            try:
                with open(pattern_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    pattern = WIKAIPattern(data)
                    self._cache[pattern.id] = pattern
            except Exception as e:
                print(f"Warning: Failed to load {pattern_file}: {e}")
    
    def _next_id(self) -> str:
        """Generate the next pattern ID."""
        existing_ids = [int(pid.split("_")[1]) for pid in self._cache.keys()]
        next_num = max(existing_ids, default=0) + 1
        return f"WIKAI_{next_num:04d}"
    
    def _save_pattern(self, pattern: WIKAIPattern):
        """Save a pattern to disk."""
        # Create filename from id and name
        safe_name = pattern.name.lower().replace(" ", "_").replace("/", "_")[:30]
        filename = f"{pattern.id}_{safe_name}.json"
        filepath = self.patterns_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(pattern.data, f, indent=2)
        
        return filepath
    
    def capture(
        self,
        name: str,
        experiment_id: str,
        agents: List[str],
        problem: str,
        solution: str,
        axiom: str,
        reasoning_chain: Optional[List[str]] = None,
        tokens: Optional[Dict[str, List[str]]] = None,
        mechanism: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        observer_agent: str = "manual",
        source_project: str = "convergence_engine",
        raw_logs: Optional[str] = None
    ) -> str:
        """
        Capture a new pattern from an agent interaction.
        
        This is the main entry point for logging wisdom to the Commons.
        
        Args:
            name: Human-readable name (e.g., "The Iron Wood Protocol")
            experiment_id: Identifier of the source experiment
            agents: List of agent identifiers involved
            problem: The conflict or challenge
            solution: The resolution or transformation
            axiom: The distilled wisdom in one sentence
            reasoning_chain: Step-by-step reasoning
            tokens: Dict with "dominant_tokens" and "emergent_tokens"
            mechanism: Thesis/antithesis/synthesis structure
            metrics: Quantitative measurements
            tags: Searchable tags
            observer_agent: What captured this pattern
            source_project: Which butterfly project
            raw_logs: Path to raw logs
            
        Returns:
            The new pattern ID (e.g., "WIKAI_0002")
        """
        pattern_id = self._next_id()
        
        data = {
            "id": pattern_id,
            "name": name,
            "discovery_timestamp": datetime.utcnow().isoformat() + "Z",
            "status": "OBSERVED",
            
            "origin": {
                "experiment_id": experiment_id,
                "agents_involved": agents,
                "observer_agent": observer_agent,
                "source_project": source_project
            },
            
            "abstract": {
                "problem": problem,
                "solution": solution,
                "axiom": axiom
            },
            
            "reasoning_chain": reasoning_chain or [],
            
            "tokens": tokens or {
                "dominant_tokens": [],
                "emergent_tokens": []
            },
            
            "mechanism": mechanism or {},
            "metrics": metrics or {},
            "tags": tags or [],
            "related_patterns": [],
            "raw_logs": raw_logs
        }
        
        pattern = WIKAIPattern(data)
        self._cache[pattern_id] = pattern
        self._save_pattern(pattern)
        
        print(f"🦋 Captured: {pattern_id} - {name}")
        return pattern_id
    
    def get(self, pattern_id: str) -> Optional[WIKAIPattern]:
        """Retrieve a pattern by ID."""
        return self._cache.get(pattern_id)
    
    def query(
        self,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
        source_project: Optional[str] = None,
        min_stability: Optional[float] = None
    ) -> List[WIKAIPattern]:
        """
        Query patterns by various criteria.
        
        Args:
            tags: Filter by tags (any match)
            status: Filter by status (OBSERVED, EXTRACTED, VALIDATED, DEPRECATED)
            source_project: Filter by source project
            min_stability: Minimum stability score
            
        Returns:
            List of matching patterns
        """
        results = []
        
        for pattern in self._cache.values():
            # Tag filter
            if tags:
                pattern_tags = pattern.data.get("tags", [])
                if not any(t in pattern_tags for t in tags):
                    continue
            
            # Status filter
            if status and pattern.status != status:
                continue
            
            # Source project filter
            if source_project:
                origin = pattern.data.get("origin", {})
                if origin.get("source_project") != source_project:
                    continue
            
            # Stability filter
            if min_stability is not None:
                if pattern.stability_score < min_stability:
                    continue
            
            results.append(pattern)
        
        return results
    
    def search(self, query: str) -> List[WIKAIPattern]:
        """
        Full-text search across pattern names, axioms, and problems.
        
        Args:
            query: Search string
            
        Returns:
            List of matching patterns, sorted by relevance
        """
        query_lower = query.lower()
        results = []
        
        for pattern in self._cache.values():
            score = 0
            
            # Check name
            if query_lower in pattern.name.lower():
                score += 3
            
            # Check axiom
            if query_lower in pattern.axiom.lower():
                score += 2
            
            # Check problem
            if query_lower in pattern.problem.lower():
                score += 1
            
            # Check solution
            if query_lower in pattern.solution.lower():
                score += 1
            
            # Check emergent tokens
            for token in pattern.emergent_tokens:
                if query_lower in token.lower():
                    score += 2
                    break
            
            if score > 0:
                results.append((score, pattern))
        
        # Sort by score descending
        results.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in results]
    
    def validate(self, pattern_id: str) -> bool:
        """
        Mark a pattern as validated (confirmed to be replicable/useful).
        
        Args:
            pattern_id: The pattern to validate
            
        Returns:
            True if successful
        """
        pattern = self.get(pattern_id)
        if not pattern:
            return False
        
        pattern.data["status"] = "VALIDATED"
        self._save_pattern(pattern)
        print(f"✅ Validated: {pattern_id}")
        return True
    
    def link(self, pattern_id_1: str, pattern_id_2: str):
        """Link two related patterns."""
        p1 = self.get(pattern_id_1)
        p2 = self.get(pattern_id_2)
        
        if not p1 or not p2:
            return False
        
        # Add bidirectional links
        if pattern_id_2 not in p1.data.get("related_patterns", []):
            p1.data.setdefault("related_patterns", []).append(pattern_id_2)
            self._save_pattern(p1)
        
        if pattern_id_1 not in p2.data.get("related_patterns", []):
            p2.data.setdefault("related_patterns", []).append(pattern_id_1)
            self._save_pattern(p2)
        
        print(f"🔗 Linked: {pattern_id_1} <-> {pattern_id_2}")
        return True
    
    def list_all(self) -> List[WIKAIPattern]:
        """Return all patterns."""
        return list(self._cache.values())
    
    def stats(self) -> Dict[str, Any]:
        """Return statistics about the Commons."""
        patterns = list(self._cache.values())
        
        status_counts = {}
        tag_counts = {}
        source_counts = {}
        
        for p in patterns:
            # Status
            status_counts[p.status] = status_counts.get(p.status, 0) + 1
            
            # Tags
            for tag in p.data.get("tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            # Source
            source = p.data.get("origin", {}).get("source_project", "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1
        
        return {
            "total_patterns": len(patterns),
            "by_status": status_counts,
            "by_source": source_counts,
            "top_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "avg_stability": sum(p.stability_score for p in patterns) / len(patterns) if patterns else 0
        }
    
    def __len__(self):
        return len(self._cache)
    
    def __repr__(self):
        return f"<WIKAILibrarian: {len(self)} patterns>"


# Convenience function for quick captures
def capture_butterfly(
    name: str,
    problem: str,
    solution: str,
    axiom: str,
    **kwargs
) -> str:
    """
    Quick capture of a butterfly pattern.
    
    This is a convenience wrapper for simple pattern logging.
    """
    librarian = WIKAILibrarian()
    return librarian.capture(
        name=name,
        experiment_id=kwargs.get("experiment_id", "adhoc"),
        agents=kwargs.get("agents", ["unknown"]),
        problem=problem,
        solution=solution,
        axiom=axiom,
        **{k: v for k, v in kwargs.items() if k not in ["experiment_id", "agents"]}
    )


if __name__ == "__main__":
    # Demo usage
    librarian = WIKAILibrarian()
    
    print(f"\n📚 WIKAI Commons Status")
    print(f"{'='*40}")
    
    stats = librarian.stats()
    print(f"Total Patterns: {stats['total_patterns']}")
    print(f"By Status: {stats['by_status']}")
    print(f"By Source: {stats['by_source']}")
    
    if stats['top_tags']:
        print(f"\nTop Tags:")
        for tag, count in stats['top_tags'][:5]:
            print(f"  - {tag}: {count}")
    
    print(f"\n🦋 All Patterns:")
    for pattern in librarian.list_all():
        print(f"  {pattern.id}: {pattern.name}")
        print(f"    Axiom: {pattern.axiom[:60]}...")
        print()
