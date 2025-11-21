
def _overflow_ratio(x, ideal, lo, hi):
    """
    Calculate violation ratio based on distance from ideal value.
    Penalizes deviation from ideal, with extra penalty for going outside envelope.
    """
    # Handle case where lo == hi (exact value required)
    if abs(hi - lo) < 1e-10:  # Essentially zero
        if abs(x - ideal) < 1e-10:  # Essentially at ideal
            return 0.0
        else:
            return 1.0  # Maximum penalty for any deviation
    
    # Calculate distance from ideal
    distance_from_ideal = abs(x - ideal)
    
    # Base penalty for deviation from ideal
    base_penalty = distance_from_ideal / (hi - lo)
    
    # Extra penalty for going outside envelope
    if x < lo:
        extra_penalty = (lo - x) / (hi - lo)
        return base_penalty + extra_penalty
    elif x > hi:
        extra_penalty = (x - hi) / (hi - lo)
        return base_penalty + extra_penalty
    else:
        return base_penalty  # Just deviation from ideal

def calculate_vp(actual_traits: dict, stability_center: dict, stability_envelope: dict, weights=None) -> float:
    """
    Calculate Violation Potential (VP) for an entity.
    Only penalizes overflow outside the envelope.
    Args:
        actual_traits: dict of measured trait values (e.g., {'speed': 62.3, 'memory_mb': 12.4, 'reliability': 1})
        stability_center: dict of ideal trait values
        stability_envelope: dict like {'speed': (0, 100), 'memory_mb': (0, 256), 'reliability': (1, 1)}
        weights: optional per-dimension weights, defaults to 1.0 each
    Returns:
        Floating-point VP value.
    """
    # Import from explorer/main.py using importlib.util (same as sentinel.py)
    import sys
    from pathlib import Path
    import importlib.util
    
    explorer_dir = Path(__file__).parent
    main_path = explorer_dir / 'main.py'
    
    if main_path.exists():
        spec = importlib.util.spec_from_file_location("explorer_main", main_path)
        if spec and spec.loader:
            explorer_main = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(explorer_main)
            math_print = explorer_main.math_print
            TRAIT_TRANSLATIONS = explorer_main.TRAIT_TRANSLATIONS
        else:
            # Fallback: define minimal versions
            def math_print(text): print(text)
            TRAIT_TRANSLATIONS = {}
    else:
        # Fallback: define minimal versions
        def math_print(text): print(text)
        TRAIT_TRANSLATIONS = {}
    weights = weights or {k: 1.0 for k in stability_envelope}
    vp = 0.0
    details = []
    for trait in stability_envelope:
        actual = actual_traits.get(trait, None)
        if actual is None:
            continue
        ideal = stability_center.get(trait, 0.0)
        lo, hi = stability_envelope[trait]
        part = _overflow_ratio(actual, ideal, lo, hi) * weights.get(trait, 1.0)
        label, desc = TRAIT_TRANSLATIONS.get(trait, (trait, 'No description.'))
        details.append(f"|{label}: overflow({actual}, {lo}, {hi}) = {part} — {desc}")
        vp += part
    math_print("[VP Calculation] VP = sum of:")
    for d in details:
        math_print(f"  {d}")
    math_print(f"[VP Calculation] Total VP = {vp}")
    return vp

# Example usage:
if __name__ == "__main__":
    actual = {'execution_time_ms': 5.2, 'memory_kb': 1024}
    center = {'execution_time_ms': 0.0, 'memory_kb': 0}
    envelope = {'execution_time_ms': 10.0, 'memory_kb': 2048}
    print("VP:", calculate_vp(actual, center, envelope))
