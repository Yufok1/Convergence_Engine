# Continuity: Agent Exporter Binder UI

Updated: 2026-04-29

Live task:
- Tighten the Convergence Engine web UI Agent Exporter surface.
- The Pokemon-style organism binder should be a metadata/filtering surface only.
- Clicking a card should drill directly into the Organism Microscope inspection surface.
- Export selection should use an explicit select control on the card, not card click.
- Single-organism chat should live inside the microscope/inspection surface, not in an intermediary card expansion window.

Patch applied:
- `templates/causation_explorer.html`
  - Removed inline card chat markup from `createOrganismCard(...)`.
  - Card click now calls `openMicroscope(org.id)`.
  - Added explicit `card-select-btn` for export selection.
  - Added microscope `Chat` tab and `renderMicroscopeChat()`.
  - Chat history is replayed into the microscope chat panel with `replayOrganismChatHistory(orgId)`.

Verification:
- `python -m py_compile causation_web_ui.py` passed.

Follow-up priority:
1. Browser-test Agent Exporter card click, explicit selection, and microscope chat.
2. If layout is good, remove or rename stale card-chat CSS comments/classes later.
3. Harden and publish `D:\End-Game\clipboard-relay` v0.2.0 after the UI flow is stable.
