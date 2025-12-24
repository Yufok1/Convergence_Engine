"""
🦠 Amoeba - HuggingFace Space Entry Point (ZeroGPU H200)

Uses ZeroGPU for FREE H200 access with dynamic allocation.
Training runs in bursts with state saved between GPU allocations.

Initialization Order:
1. Load state from HF Dataset (tostido/Amoeba)
2. Build vocabulary & knowledge systems (if needed)
3. Run training burst with @spaces.GPU decorator
4. Save state to HF Dataset
5. Repeat on user interaction or refresh
"""

import os
import sys
import time
import json
import shutil
import threading
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

import gradio as gr

# ZeroGPU support - provides FREE H200 access!
try:
    import spaces
    ZEROGPU_AVAILABLE = True
    print("✅ ZeroGPU available - H200 GPU enabled")
except ImportError:
    ZEROGPU_AVAILABLE = False
    print("⚠️ ZeroGPU not available - running in CPU mode")
    # Mock decorator for local testing
    class spaces:
        @staticmethod
        def GPU(duration=60):
            def decorator(fn):
                return fn
            return decorator

# HuggingFace imports
try:
    from huggingface_hub import HfApi, hf_hub_download, upload_folder, list_repo_files
    HF_HUB_AVAILABLE = True
except ImportError:
    HF_HUB_AVAILABLE = False
    print("⚠️ huggingface_hub not available")

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

DATASET_REPO = "tostido/Amoeba"
STATE_DIRS = [
    "data/logs",
    "data/checkpoints", 
    "data/neural_checkpoints",
    "data/capsules",
    "highlander_capsules",
]
HF_TOKEN = os.environ.get("HF_TOKEN")

# WIKAI API Configuration
WIKAI_SPACE_URL = "https://tostido-wikai.hf.space"

# ZeroGPU Training Configuration
TRAINING_BURST_DURATION = 60  # Seconds per GPU allocation
DEFAULT_TRAINING_STEPS = 50   # Steps per burst

# ═══════════════════════════════════════════════════════════════════════════════
# STATE SYNC WITH HF DATASET
# ═══════════════════════════════════════════════════════════════════════════════

def load_state_from_dataset():
    """Load all state from HuggingFace Dataset on startup"""
    if not HF_HUB_AVAILABLE or not HF_TOKEN:
        print("⚠️ No HF_TOKEN or huggingface_hub - running without persistent state")
        return False
    
    print("📥 Loading state from HuggingFace Dataset...")
    api = HfApi(token=HF_TOKEN)
    
    try:
        # List all files in dataset
        files = list_repo_files(DATASET_REPO, repo_type="dataset", token=HF_TOKEN)
        state_files = [f for f in files if f.startswith("state/")]
        
        print(f"   Found {len(state_files)} state files")
        
        # Download each state file
        for file_path in state_files:
            try:
                # Remove 'state/' prefix to get local path
                local_path = file_path.replace("state/", "", 1)
                local_full = Path(local_path)
                local_full.parent.mkdir(parents=True, exist_ok=True)
                
                # Download file
                downloaded = hf_hub_download(
                    repo_id=DATASET_REPO,
                    filename=file_path,
                    repo_type="dataset",
                    token=HF_TOKEN,
                    local_dir=".",
                    local_dir_use_symlinks=False
                )
                
                # Move from state/ to correct location
                if Path(f"state/{local_path}").exists():
                    shutil.copy2(f"state/{local_path}", local_path)
                    
            except Exception as e:
                print(f"   ⚠️ Failed to download {file_path}: {e}")
        
        print("   ✅ State loaded successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to load state: {e}")
        return False


def save_state_to_dataset():
    """Save all state to HuggingFace Dataset"""
    if not HF_HUB_AVAILABLE or not HF_TOKEN:
        print("⚠️ No HF_TOKEN - cannot save state")
        return False
    
    print(f"📤 Saving state... ({datetime.now().strftime('%H:%M:%S')})")
    api = HfApi(token=HF_TOKEN)
    
    try:
        # Create state directory structure
        state_dir = Path("state_upload")
        state_dir.mkdir(exist_ok=True)
        
        file_count = 0
        
        # Copy all state files to upload directory
        for dir_path in STATE_DIRS:
            src = Path(dir_path)
            if src.exists():
                dst = state_dir / "state" / dir_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                
                if src.is_dir():
                    for f in src.rglob("*"):
                        if f.is_file():
                            rel = f.relative_to(src)
                            dest_file = dst / rel
                            dest_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(f, dest_file)
                            file_count += 1
                else:
                    shutil.copy2(src, dst)
                    file_count += 1
        
        # Also save live_report.json if it exists
        if Path("live_report.json").exists():
            shutil.copy2("live_report.json", state_dir / "state" / "live_report.json")
            file_count += 1
        
        # Upload to dataset
        if file_count > 0:
            upload_folder(
                folder_path=str(state_dir),
                repo_id=DATASET_REPO,
                repo_type="dataset",
                token=HF_TOKEN,
                commit_message=f"Auto-save: {file_count} files at {datetime.now().isoformat()}"
            )
            print(f"   ✅ Saved {file_count} files")
        else:
            print("   ℹ️ No state files to save")
        
        # Cleanup
        shutil.rmtree(state_dir, ignore_errors=True)
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to save state: {e}")
        return False


def state_save_loop():
    """Background thread to save state periodically (not used with ZeroGPU)"""
    pass  # ZeroGPU saves after each burst instead


# ═══════════════════════════════════════════════════════════════════════════════
# ZEROGPU TRAINING SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

# Global state for the unified system
_unified_system = None
_system_initialized = False


def initialize_system():
    """Initialize the unified system (runs once, CPU only)"""
    global _unified_system, _system_initialized
    
    if _system_initialized:
        return _unified_system
    
    print("🔧 Initializing system...")
    
    # Run build scripts if needed (CPU)
    if not Path("data/seeded_knowledge_web_250k.json").exists():
        print("   Building vocabulary...")
        commands = [
            "python build_curated_dataset.py",
            "python merge_nuclear_vocab.py", 
            "python generate_innate_vocab.py",
        ]
        for cmd in commands:
            try:
                subprocess.run(cmd, shell=True, capture_output=True, timeout=300)
            except:
                pass
    
    # Import and create unified system
    try:
        from unified_entry import UnifiedSystem
        _unified_system = UnifiedSystem(config_path="config.json", no_viz=True)
        _system_initialized = True
        print("   ✅ System initialized")
    except Exception as e:
        print(f"   ❌ Failed to initialize: {e}")
        _unified_system = None
    
    return _unified_system


@spaces.GPU(duration=TRAINING_BURST_DURATION)
def run_training_burst(steps: int = DEFAULT_TRAINING_STEPS) -> str:
    """
    Run a training burst on ZeroGPU H200.
    
    This function is decorated with @spaces.GPU to request H200 allocation.
    It runs a fixed number of training steps then returns results.
    """
    global _unified_system
    
    start_time = time.time()
    gpu_name = "H200 (ZeroGPU)" if ZEROGPU_AVAILABLE else "CPU (local)"
    
    results = {
        "steps_completed": 0,
        "organisms_trained": 0,
        "avg_loss": 0.0,
        "duration_seconds": 0.0,
        "gpu": gpu_name,
        "status": "running"
    }
    
    try:
        system = initialize_system()
        if system is None:
            results["status"] = "error"
            results["error"] = "System not initialized"
            return json.dumps(results, indent=2)
        
        # Run training steps
        losses = []
        for step in range(steps):
            try:
                # One breath of the system (training step)
                system.breath()
                results["steps_completed"] += 1
                
                # Collect metrics
                if hasattr(system, 'evolution_engine'):
                    orgs = system.evolution_engine.get_active_organisms()
                    results["organisms_trained"] = len(orgs)
                    
                    for org in orgs:
                        if hasattr(org, 'trainer') and org.trainer:
                            buffer = getattr(org.trainer, 'autotune_metrics_buffer', {})
                            loss_history = buffer.get('loss_history', [])
                            if loss_history:
                                losses.append(loss_history[-1])
                
                # Check time limit (leave 5s buffer)
                elapsed = time.time() - start_time
                if elapsed > TRAINING_BURST_DURATION - 5:
                    break
                    
            except Exception as e:
                print(f"Step {step} error: {e}")
                break
        
        results["avg_loss"] = sum(losses) / len(losses) if losses else 0.0
        results["duration_seconds"] = round(time.time() - start_time, 2)
        results["status"] = "completed"
        
        # Save state after burst
        save_state_to_dataset()
        
        return json.dumps(results, indent=2)
        
    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
        return json.dumps(results, indent=2)


# ═══════════════════════════════════════════════════════════════════════════════
# REPORT GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def get_live_report():
    """Load and return the live report JSON"""
    report_path = Path("live_report.json")
    
    if report_path.exists():
        try:
            with open(report_path, 'r') as f:
                return f.read()
        except:
            pass
    
    return '{"status": "No data yet - run a training burst"}'


def get_formatted_report():
    """Get nicely formatted report text"""
    try:
        from system_report import SystemReporter
        reporter = SystemReporter(_unified_system)
        report = reporter.generate()
        
        gpu_label = "H200 (ZeroGPU)" if ZEROGPU_AVAILABLE else "CPU"
        
        lines = []
        lines.append("=" * 70)
        lines.append(f"📊 SYSTEM REPORT - {report.timestamp}")
        lines.append(f"   GPU: {gpu_label}")
        lines.append("=" * 70)
        lines.append("")
        
        pop = report.population
        lines.append("👥 POPULATION")
        lines.append(f"   Active: {pop.active_organisms} | Fallen: {pop.fallen_organisms}")
        lines.append(f"   Fitness: {pop.fitness_mean:.3f} ± {pop.fitness_std:.3f}")
        lines.append(f"   Age: {pop.age_mean:.1f} avg, {pop.age_max} max")
        lines.append("")
        
        hl = report.highlander
        lines.append(f"⚔️ HIGHLANDER ({hl.phase})")
        lines.append(f"   Round: {hl.round_number} | Battles: {hl.total_battles}")
        lines.append(f"   Eliminations: {hl.eliminations_total} | Champions: {hl.champions_crowned}")
        lines.append("")
        
        al = report.alliances
        lines.append("🤝 ALLIANCES")
        lines.append(f"   Active: {al.active_alliances} | Members: {al.total_members}")
        lines.append(f"   Largest: {al.largest_alliance_size} | Wars: {al.wars_in_progress}")
        lines.append("")
        
        nn = report.neural
        lines.append("🧠 NEURAL")
        lines.append(f"   Brains: {nn.organisms_with_brains} | Steps: {nn.total_training_steps}")
        lines.append(f"   Loss: {nn.avg_loss:.4f} | ε: {nn.avg_epsilon:.3f}")
        lines.append(f"   Experience: {nn.experience_buffer_total} total")
        lines.append("")
        
        lang = report.language
        lines.append("📚 LANGUAGE")
        lines.append(f"   Unique Words: {lang.unique_words_total}")
        lines.append(f"   Avg Vocab: {lang.avg_vocabulary_size:.1f} words/organism")
        lines.append("")
        
        res = report.resources
        lines.append(f"💻 RESOURCES ({gpu_label})")
        lines.append(f"   Breath: {res.breath_count} | Uptime: {res.uptime_seconds / 60:.1f}m")
        ray_status = "✅" if res.ray_enabled else "❌"
        lines.append(f"   Ray: {ray_status} | CPUs: {res.cpu_count} | GPUs: {res.gpu_count}")
        lines.append("")
        
        if report.warnings:
            lines.append("⚠️ WARNINGS")
            for w in report.warnings[:5]:
                lines.append(f"   ⚠️ {w}")
        
        lines.append("=" * 70)
        return "\n".join(lines)
        
    except Exception as e:
        return f"System initializing... Click 'Run Training Burst' to start.\n\nError: {e}"


def manual_save():
    """Manually trigger state save"""
    success = save_state_to_dataset()
    return "✅ State saved!" if success else "❌ Save failed (check HF_TOKEN)"


def run_burst_and_report(steps: int) -> tuple:
    """Run training burst and return updated report"""
    burst_result = run_training_burst(int(steps))
    report = get_formatted_report()
    return report, burst_result


# ═══════════════════════════════════════════════════════════════════════════════
# GRADIO INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

def create_interface():
    """Create the Gradio interface"""
    
    gpu_status = "🟢 H200 ZeroGPU (FREE)" if ZEROGPU_AVAILABLE else "🟡 CPU Mode (local)"
    
    with gr.Blocks(title="🦠 Amoeba - Convergence Engine", theme=gr.themes.Base()) as demo:
        gr.Markdown("# 🦠 Amoeba - Convergence Engine")
        gr.Markdown(f"**{gpu_status}** - Click 'Run Training Burst' to evolve organisms on the GPU.")
        
        with gr.Row():
            with gr.Column(scale=2):
                report_output = gr.Textbox(
                    label="📊 System Report",
                    value=get_formatted_report,
                    lines=28,
                    max_lines=35,
                    interactive=False,
                    show_copy_button=True
                )
                
                burst_output = gr.Textbox(
                    label="🚀 Training Burst Results",
                    lines=8,
                    interactive=False,
                    placeholder="Click 'Run Training Burst' to start..."
                )
            
            with gr.Column(scale=1):
                gr.Markdown("### 🎮 Controls")
                
                steps_slider = gr.Slider(
                    minimum=10,
                    maximum=200,
                    value=DEFAULT_TRAINING_STEPS,
                    step=10,
                    label="Training Steps per Burst"
                )
                
                train_btn = gr.Button("🚀 Run Training Burst", variant="primary", size="lg")
                refresh_btn = gr.Button("🔄 Refresh Report", variant="secondary")
                save_btn = gr.Button("💾 Save State", variant="secondary")
                
                save_status = gr.Textbox(label="Status", lines=1, interactive=False)
                
                gr.Markdown("### 🔗 Links")
                gr.Markdown("- [State Dataset](https://huggingface.co/datasets/tostido/Amoeba)")
                gr.Markdown("- [WIKAI Commons](https://huggingface.co/spaces/tostido/Wikai)")
                gr.Markdown("- [GitLab Source](https://gitlab.com/Toasteedo/Convergence_Engine)")
                
                gr.Markdown("### ℹ️ About ZeroGPU")
                gr.Markdown("""
**FREE H200 Access!**

ZeroGPU provides dynamic GPU allocation:
- ~60 second bursts of H200 compute
- State saved between bursts
- No rental costs required

Click 'Run Training Burst' to:
1. Allocate H200 GPU
2. Run training steps
3. Save state to dataset
4. Release GPU
""")
        
        # Event handlers
        train_btn.click(
            fn=run_burst_and_report,
            inputs=[steps_slider],
            outputs=[report_output, burst_output]
        )
        refresh_btn.click(fn=get_formatted_report, outputs=report_output)
        save_btn.click(fn=manual_save, outputs=save_status)
        
        with gr.Accordion("📜 Raw JSON Report", open=False):
            json_output = gr.Code(label="Live Report", language="json")
            json_btn = gr.Button("Load JSON")
            json_btn.click(fn=get_live_report, outputs=json_output)
        
        gr.Markdown("---")
        gr.Markdown("*Organisms evolve, learn language, form alliances, and fight for survival on H200 GPU.*")
    
    return demo


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

print("=" * 70)
print("🦠 AMOEBA - Convergence Engine (ZeroGPU H200)")
print("=" * 70)

# Load state on startup
load_state_from_dataset()

# Create interface (don't auto-start training - let user trigger it)
demo = create_interface()

if __name__ == "__main__":
    demo.launch()
