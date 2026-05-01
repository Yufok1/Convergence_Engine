# Convergence Engine — Nervous System Rescue

**Date:** 2026-05-01
**Author:** Claude Opus 4.7 (1M context, max effort) — invoked from Claude Code at `C:\Users\Jeff Towers`
**Operator:** Jeff Towers (towers.jeff@gmail.com)
**Scope:** `D:\End-Game\Convergence_Engine`

## Symptom (operator report)

> "codex messed up my logging and play resume tape"
> "organisms can't get past lvl 169"
> "it's really a nervous system"

## Diagnosis

The Convergence Engine's neural-checkpoint pathway (the **play-resume tape**) was non-functional and the structured logging side of the **nervous system** was silent. Three independent root causes had compounded:

1. **Checkpoint target directory missing.** The runtime expects `data/neural_checkpoints/` but only `data/checkpoints/` (a different, empty dir) existed on disk. Any `save_checkpoint` call was either failing silently or writing nothing the restore path could read.

2. **Signal-clearing regression in commit `d1ffcbd` ("Handle neural checkpoint restore signals", CodexSandboxOffline lineage).** The pre-codex code unconditionally removed `data/.checkpoint_signal.json` after reading it. The codex rewrite moved the clear call into the `restore` branch and into the success path of `save_now`, so:
   - A `save_now` whose backing `save_checkpoint` returned `False` left the signal on disk → re-fired every simulation step (retry loop).
   - A corrupt or partial JSON signal hit the `except Exception` branch and stayed on disk forever → re-fired every step.
   - Any unknown action stayed on disk and re-fired every step.

3. **Stuck at `training_step_count = 169`.** Not a level cap. Per the operator-prompt comments in `causation_web_ui.py:3263-3267`, training only fires when `(step_count % update_frequency == 0) AND each organism has ≥ batch_size (default 32) experiences`. With (1) and (2) above, every restart wiped the experience buffer before training fired, so the counter never advanced past the last collection plateau. `application.log` shows the simulator restarted 5 times today (11:25, 12:18, 12:21, 12:28, 12:51) — each restart is a state amnesia event under the broken tape.

## Fix applied

Surgical changes only. Two files touched, no behavior added beyond restoring pre-codex semantics.

### 1. `data/neural_checkpoints/` created

```
mkdir -p D:/End-Game/Convergence_Engine/data/neural_checkpoints
```

The neural trainer's `checkpoint_dir` now has a real target. Subsequent `save_checkpoint` calls can land somewhere; `get_latest_checkpoint` can find them; auto-resume can hydrate organisms from disk across restarts.

### 2. `reality_simulator/main.py` — signal-clearing made unconditional

Two edits inside `RealitySimulator.run` (~line 1695–1744):

- **After the signal `if/elif` chain:** added an `else` for unknown actions and a `self._clear_checkpoint_signal()` inside the `except` so a corrupt or unknown signal cannot loop. Comment block at the top of the read explains the invariant.
- **After a forced save:** added an `else` clause that clears the signal when `save_checkpoint` returns falsy, so a failed save no longer retriggers every simulation step.

Net effect: once the simulator opens the signal file, that file is always gone before the next step — exactly the pre-codex invariant — regardless of action, JSON validity, or save success.

## What this does NOT change

- StateLogger silence (state.log, reality_sim.log at 0 bytes) is most likely an initialization-order issue in `unified_entry.py` (the async writer thread is started in `StateLogger.__init__` but may never receive log entries if the logger isn't being passed a state stream). Left for the next pass — this rescue prioritized the tape mechanism over the structured-log capture.
- The 2866-line uncommitted churn in `causation_web_ui.py` and 4611 lines in `templates/causation_explorer.html` are mostly LF→CRLF line-ending diffs (git noted this) plus today's edits. Not touched by this rescue.
- Codex's 24-commit lead over `origin/main` is untouched.

## Verification path

1. Start the simulator. Tail `data/logs/application.log`.
2. From the web UI, click **Save Checkpoint**. Confirm `data/neural_checkpoints/checkpoint_<timestamp>/` appears.
3. Stop and restart. Confirm `[NEURAL CHECKPOINT] Found latest checkpoint:` line appears in the boot log and brain count > 0 is reported by `_restore_neural_checkpoint`.
4. Once experience buffers carry across restarts, `training_step_count` should advance past 169.

## Watermark

> Opus 4.7 max-effort, 2026-05-01.
> The tape is on the floor and the player can hear itself again.
> Two edits, one mkdir, one continuity doc. Clean fight.
> — Claude Opus 4.7 (1M context)
