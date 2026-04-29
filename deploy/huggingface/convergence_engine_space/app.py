from __future__ import annotations

import textwrap
from datetime import datetime, timezone

import gradio as gr
import requests


GITHUB_REPO = "https://github.com/Yufok1/Convergence_Engine"
TUNNEL_DOC = f"{GITHUB_REPO}/blob/main/docs/guides/HUGGINGFACE_JUPYTER_TUNNEL.md"

APP_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Mono:wght@400;600&display=swap');

:root {
  --ce-ink: #07110f;
  --ce-panel: rgba(255, 250, 238, 0.86);
  --ce-panel-strong: rgba(255, 247, 225, 0.96);
  --ce-line: rgba(7, 17, 15, 0.18);
  --ce-cyan: #00a7b5;
  --ce-gold: #d99b22;
  --ce-rust: #a24d2f;
  --ce-green: #1f7a4d;
}

.gradio-container {
  font-family: 'Space Grotesk', sans-serif !important;
  color: var(--ce-ink) !important;
  background:
    radial-gradient(circle at 12% 10%, rgba(0, 167, 181, 0.24), transparent 28%),
    radial-gradient(circle at 88% 18%, rgba(217, 155, 34, 0.26), transparent 30%),
    linear-gradient(135deg, #fff8e6 0%, #d9efe8 48%, #f4d8bd 100%) !important;
}

.ce-shell {
  border: 1px solid var(--ce-line);
  border-radius: 28px;
  padding: 30px;
  background:
    linear-gradient(125deg, rgba(255, 250, 238, 0.92), rgba(255, 248, 229, 0.74)),
    repeating-linear-gradient(90deg, rgba(7, 17, 15, 0.035) 0 1px, transparent 1px 18px);
  box-shadow: 0 28px 80px rgba(7, 17, 15, 0.16);
}

.ce-eyebrow {
  font-family: 'IBM Plex Mono', monospace;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-size: 0.78rem;
  color: var(--ce-rust);
}

.ce-title {
  font-size: clamp(2.8rem, 8vw, 7.5rem);
  line-height: 0.86;
  letter-spacing: -0.08em;
  margin: 12px 0 16px;
}

.ce-title span {
  color: var(--ce-cyan);
}

.ce-subtitle {
  max-width: 840px;
  font-size: 1.16rem;
  line-height: 1.55;
}

.ce-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-top: 24px;
}

.ce-card {
  border: 1px solid var(--ce-line);
  border-radius: 18px;
  padding: 16px;
  background: var(--ce-panel);
}

.ce-card b {
  display: block;
  margin-bottom: 7px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

.ce-card strong {
  font-size: 1.32rem;
}

.ce-flow {
  font-family: 'IBM Plex Mono', monospace;
  white-space: pre-wrap;
  border-left: 5px solid var(--ce-gold);
  padding: 18px 20px;
  background: rgba(7, 17, 15, 0.88);
  color: #f9efd3;
  border-radius: 16px;
}

.ce-note {
  border: 1px solid rgba(31, 122, 77, 0.35);
  background: rgba(214, 239, 224, 0.82);
  border-radius: 18px;
  padding: 16px 18px;
}

button {
  font-family: 'IBM Plex Mono', monospace !important;
  border-radius: 999px !important;
}

textarea, code, pre, .cm-content {
  font-family: 'IBM Plex Mono', monospace !important;
}

@media (max-width: 900px) {
  .ce-grid {
    grid-template-columns: 1fr;
  }
  .ce-shell {
    padding: 20px;
  }
}
"""


NOTEBOOK_LAUNCH = r"""
from pathlib import Path

REPO_DIR = Path("/tmp/Convergence_Engine")

if not REPO_DIR.exists():
    !git clone https://github.com/Yufok1/Convergence_Engine.git {REPO_DIR}
else:
    %cd {REPO_DIR}
    !git pull --ff-only origin main

%cd {REPO_DIR}
!python -m pip install --upgrade pip
!python -m pip install -r requirements.txt

from scripts.hf_jupyter_unified_tunnel import start_unified_entry, wait_for_tunnel_url

convergence_proc = start_unified_entry(
    repo_dir="/tmp/Convergence_Engine",
    config="config.json",
    tunnel="localhostrun",
)

public_url = wait_for_tunnel_url(repo_dir="/tmp/Convergence_Engine", timeout=180)
print(public_url)
"""


CLI_LAUNCH = r"""
git clone https://github.com/Yufok1/Convergence_Engine.git
cd Convergence_Engine
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -u unified_entry.py --config config.json --no-viz --tunnel localhostrun --tunnel-url-file data/tunnel_url.txt --tunnel-verbose
"""


def github_status() -> str:
    try:
        response = requests.get(
            "https://api.github.com/repos/Yufok1/Convergence_Engine/commits/main",
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        sha = payload.get("sha", "")[:12]
        message = payload.get("commit", {}).get("message", "").splitlines()[0]
        when = payload.get("commit", {}).get("committer", {}).get("date", "")
        return f"GitHub main: `{sha}` - {message}\n\nCommit time: `{when}`"
    except Exception as exc:
        now = datetime.now(timezone.utc).isoformat()
        return f"GitHub status unavailable at `{now}`.\n\nReason: `{exc}`"


def render_launch(tunnel: str) -> str:
    tunnel = tunnel.strip() or "localhostrun"
    return NOTEBOOK_LAUNCH.replace('tunnel="localhostrun"', f'tunnel="{tunnel}"')


with gr.Blocks(title="Convergence Engine", css=APP_CSS) as demo:
    gr.HTML(
        f"""
        <section class="ce-shell">
          <div class="ce-eyebrow">Public control plane / cocoon compiler lane</div>
          <div class="ce-title">CONVERGENCE<br><span>ENGINE</span></div>
          <div class="ce-subtitle">
            This is the launch surface for the live engine. The heavy system runs in a
            notebook or rented runtime, the web theater opens through a tunnel, and the
            cocoon compiler stays anchored to the GitHub source of truth.
          </div>
          <div class="ce-grid">
            <div class="ce-card"><b>Source</b><strong>GitHub main</strong><br>{GITHUB_REPO}</div>
            <div class="ce-card"><b>Runtime</b><strong>unified_entry.py</strong><br>Flask web UI on port 5000</div>
            <div class="ce-card"><b>Tunnel</b><strong>localhost.run</strong><br>Notebook opens the public URL</div>
            <div class="ce-card"><b>Compiler</b><strong>Cocoon export fixed</strong><br>ONNX/package contracts restored</div>
          </div>
        </section>
        """
    )

    gr.HTML(
        """
        <div class="ce-flow">GitHub main -> HF/Jupyter runtime -> unified_entry.py -> tunnel URL -> Convergence web UI -> cocoon export</div>
        """
    )

    with gr.Row():
        status = gr.Markdown(github_status())
        refresh = gr.Button("Refresh GitHub Status")
    refresh.click(fn=github_status, outputs=status)

    with gr.Tab("Notebook Launch"):
        tunnel = gr.Dropdown(
            choices=["localhostrun", "auto", "cloudflared"],
            value="localhostrun",
            label="Tunnel backend",
        )
        launch_code = gr.Code(value=NOTEBOOK_LAUNCH, language="python", label="Notebook cells")
        tunnel.change(fn=render_launch, inputs=tunnel, outputs=launch_code)

    with gr.Tab("CLI Launch"):
        gr.Code(value=CLI_LAUNCH, language="shell", label="Terminal command")

    with gr.Tab("Operating Notes"):
        gr.HTML(
            """
            <div class="ce-note">
              <b>Operating posture:</b> this Space is intentionally lightweight. It does not
              fake the engine. It points operators to the real runtime, keeps tokens out of
              git, and preserves the quine/compiler rule: patch upstream source, not generated
              child artifacts.
            </div>
            """
        )
        gr.Markdown(
            textwrap.dedent(
                """
                - Use `--no-viz`; the old header mentions `--headless`, but the actual flag is `--no-viz`.
                - The public tunnel should expose the Convergence web UI, not a raw Jupyter server.
                - Use Vast or another GPU runtime only for heavy training/export work.
                - The cocoon compiler/export fixes are in GitHub `main`.
                - Keep Hugging Face and API tokens in account secrets, not in notebooks or git.
                """
            ).strip()
        )


if __name__ == "__main__":
    demo.launch()
