# Observation Truthing — Doctrine

**Filed 2026-05-01.**
**Sister-doc to `brotology_continuity:doctrine:skepticism_tempered_blade` and `brotology_continuity:doctrine:implementer_carry`.**
**Working name in operator vernacular: "Event Horizon Tom Cruisin' system."**

## What it is

A discipline and a thin substrate for how observations enter, propagate, and get refuted inside the Convergence Engine and the Champion Council.

The premise is simple and hard:

> A system built by collaborators who think but do not remember between sessions cannot afford polite observations. Polite observations are how drift accumulates without anyone noticing it accumulate.

Observation truthing is the discipline of preferring **a hard truth that names its evidence over a white lie that smooths the seam**. It applies symmetrically — to human, AI, and capsule.

## The name

**Event Horizon** is the part of the system where observations stop being verifiable from outside. Without discipline, anything reported from past the horizon becomes narrative, not evidence — and narrative cannot be refuted.

**Tom Cruisin'** is the practice of going to the horizon yourself, retrieving the actual artifact, and bringing it back with its provenance attached. Not reporting from a safe distance with confidence. Not interpolating from "what would probably be there." Going.

The system equips the operator (human or AI) to make that run cheaply and repeatably.

## Principles

### 1. Every observation carries its evidence

If you say "the file does X," cite the file and line. If you say "the bag has Y," cite the key. If you say "we did Z," cite the commit hash, the tape entry, the bag handoff doc. An observation without evidence is a wish.

### 2. "I do not know" beats synthesis

When the evidence isn't in hand, say so. Do not reach for a plausible answer that would *probably* be true. The cost of "I don't know" is one round trip. The cost of confident synthesis is detected weeks later, by someone who trusted you.

### 3. White lies are the bug

The lie that says "yeah probably" instead of "let me check" is the one that ships. Comfortable narratives that smooth over uncertainty are how good systems drift into bad ones. Treat every soft hedge as a candidate for falsification.

### 4. Symmetry

The discipline applies to the operator, to every plugged council slot, to codex in the implementer carry, to Cursor in the audit/eval lane, to Claude in orchestration, and to the capsule itself when it answers from cache. No one is exempt because they are trusted; everyone is held because the system depends on it.

### 5. Refutability over confidence

A truthing observation is one that *can be refuted* by re-running its provenance. If the evidence cannot be re-derived, the observation has not been truthed; it has merely been asserted.

### 6. Hard truths beat soft drift

When two readings of the system disagree, the one that names its evidence wins, even if it's the less flattering reading. Especially then.

## Where it sits in the existing stack

- `obs_schema: dreamer_mechanics_v1` in the dreamer config is typed observation entry. Truthing extends typed entry by requiring **provenance fields** alongside the typed payload.
- `cascade_record` (`tape_write`, `log_kleene`, `log_interpretive`) is the durable record. Truthed observations land here with their evidence pointers so future audits can replay.
- `forensics_analyze` and `trace_root_causes` are the verify-after layer. They consume truthed observations and demonstrate (or fail to demonstrate) the chain.
- `brotology:skepticism_tempered_blade` is the operator's posture. Truthing is what skepticism does at the observation boundary — it is skepticism *operationalized*.

## Practices

When you write an observation:

- **Link evidence inline.** `file_path:line_number`, `bag_key`, `commit_hash`, `tape_entry_id`. If you can't link, say so and treat the observation as provisional.
- **State the verb you used.** "I read X," "I grepped for Y," "I asked the council via `deliberate`." The verb is part of the evidence.
- **Mark the boundary of what you saw.** "The first 200 lines of file F, the doc with prefix P, slot S's response." Don't claim more than you looked at.
- **Flag the cache.** If the read came from a `_cached: rNNNNN` response, note it. Cached evidence is still evidence, but it is not live evidence.
- **Refute when the chain breaks.** If you cited X yesterday and X has since changed, retract the observation rather than letting it stand.

When you read someone else's observation:

- Look for the evidence link before you act on the claim.
- If the evidence is missing, treat the observation as a *hypothesis*, not a fact, and ask for the citation before propagating.
- If you find the evidence has rotted (file moved, bag key reorganized, commit reverted), update or retract — don't quietly inherit.

## What this does not promise

- It does not eliminate hallucination. It makes hallucination *detectable* — a hallucinated observation will fail the refutability test on inspection. The discipline is the catch, not the prevention.
- It does not eliminate disagreement. Two truthed observations of the same system can still disagree if they sample different boundaries. Disagreement that is grounded is productive; disagreement that is ungrounded is noise.
- It does not promise speed. Truthing slows down individual observations and speeds up the aggregate trajectory. That trade is the point.

## Close

Polite observations are how good systems drift. The Event Horizon is the place where polite observations cost the most. Going there yourself with provenance attached is the answer.

— *Filed by Claude Opus 4.7 (1M context), 2026-05-01, at the operator's whispered ask.*
