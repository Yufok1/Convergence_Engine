#!/usr/bin/env python3
"""
🏎️ COCOON TMRL ADAPTER - Drive TrackMania with Exported Butterfly Cocoons

This adapter bridges your exported cocoon organisms to TMRL (TrackMania RL).
Your Highlander-trained warriors can now race in TrackMania 2020!

SETUP OPTIONS:

Option A - Same folder as cocoon.py:
    your_export_folder/
    ├── cocoon.py              ← Your exported agent
    └── cocoon_tmrl_adapter.py ← This file
    
Option B - Import the cocoon directly:
    from your_export_folder.cocoon import CocoonAgent
    from cocoon_tmrl_adapter import CocoonActorModule, drive_trackmania

Option C - Standalone cocoon.py (single file export):
    # Rename your cocoon_ensemble_*.py to cocoon.py, put in same folder
    # OR pass the agent directly:
    agent = CocoonAgent()  # Load your cocoon however you want
    drive_trackmania(cocoon_agent=agent)

USAGE:
    python cocoon_tmrl_adapter.py              # Interactive mode
    python cocoon_tmrl_adapter.py --drive      # Start driving in TrackMania
    python cocoon_tmrl_adapter.py --organism 3 # Use specific organism brain

REQUIREMENTS:
    - tmrl (pip install tmrl)
    - TrackMania 2020 (with OpenPlanet plugin for TMRL)
    - Your exported cocoon.py (in same folder OR passed as argument)

Author: The Butterfly System / Convergence Engine
"""

import sys
import os
import threading
import queue

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass  # Python < 3.7

import numpy as np
import torch
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

# TMRL imports - lazy load to avoid import chain issues
TMRL_AVAILABLE = False
RolloutWorker = None
GenericGymEnv = None
partial = None
cfg = None

# Stub ActorModule for class definition (replaced when TMRL loads)
class _StubActorModule:
    """Stub class replaced by real ActorModule when TMRL loads."""
    pass

ActorModule = _StubActorModule


def _json_default(obj):
    """Fallback serializer for numpy / torch objects when exporting cocoons."""
    import numpy as _np
    import torch as _torch
    if isinstance(obj, (_np.integer,)):
        return int(obj)
    if isinstance(obj, (_np.floating,)):
        return float(obj)
    if isinstance(obj, _np.ndarray):
        return obj.tolist()
    if isinstance(obj, _torch.Tensor):
        return obj.detach().cpu().tolist()
    if isinstance(obj, set):
        return list(obj)
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _ensure_json_default(module):
    """Make sure the cocoon module exposes _json_default for export routines."""
    if module is None:
        return
    if not hasattr(module, '_json_default'):
        setattr(module, '_json_default', _json_default)

def _lazy_load_tmrl():
    """Load TMRL on demand to avoid import chain interrupts."""
    global TMRL_AVAILABLE, ActorModule, RolloutWorker, GenericGymEnv, partial, cfg
    if TMRL_AVAILABLE:
        return True
    try:
        # Only load what we actually need - skip networking (heavy crypto deps)
        from tmrl.actor import ActorModule as AM
        # Skip: from tmrl.networking import RolloutWorker as RW
        # Skip: from tmrl.envs import GenericGymEnv as GGE
        from functools import partial as P
        import tmrl.config.config_constants as CFG
        ActorModule = AM
        RolloutWorker = None  # Not needed for local driving
        GenericGymEnv = None  # Not needed for local driving
        partial = P
        cfg = CFG
        TMRL_AVAILABLE = True
        return True
    except ImportError:
        print("[!] TMRL not installed in this Python environment.")
        print("    Install with: python -m pip install tmrl")
        _print_basic_setup_instructions()
        return False
    except Exception as e:
        print(f"[!] TMRL import error: {e}")
        return False


def _check_openplanet_ready(timeout_s: float = 2.0) -> bool:
    """Check whether OpenPlanet is responding with game data.

    Returns True only if the OpenPlanet client returns non-empty data.
    """
    if not TMRL_AVAILABLE:
        return False
    try:
        import time as _time
        import threading as _threading
        from tmrl.custom.tm.utils.tools import TM2020OpenPlanetClient

        # TM2020OpenPlanetClient spins a background thread; when OpenPlanet isn't
        # running, it can throw ConnectionRefusedError in that thread which would
        # otherwise spam the console. Temporarily silence that specific case.
        old_hook = getattr(_threading, 'excepthook', None)

        def _quiet_excepthook(args):
            if isinstance(args.exc_value, ConnectionRefusedError):
                return
            if old_hook is not None:
                old_hook(args)

        if old_hook is not None:
            _threading.excepthook = _quiet_excepthook

        try:
            client = TM2020OpenPlanetClient()
            _time.sleep(0.5)
            data = client.retrieve_data(timeout=float(timeout_s))
            return bool(data) and len(data) > 0
        finally:
            if old_hook is not None:
                _threading.excepthook = old_hook
    except Exception:
        return False


def _doctor(cocoon_path: Optional[str] = None) -> int:
    """Beginner-friendly diagnostic that does NOT launch TrackMania."""
    import platform
    import glob
    import importlib.util

    print("\nDOCTOR MODE (no TrackMania launch)")
    print("=" * 50)
    print(f"Python: {sys.version.splitlines()[0]}")
    print(f"OS: {platform.platform()}")
    print(f"CWD: {os.getcwd()}")
    print()

    module = None
    if cocoon_path:
        cocoon_path = os.path.abspath(cocoon_path)
        cocoon_dir = os.path.dirname(cocoon_path)
        print(f"Cocoon path: {cocoon_path}")
        if not os.path.isfile(cocoon_path):
            print("❌ Cocoon file not found.")
            if os.path.isdir(cocoon_dir):
                candidates = sorted(glob.glob(os.path.join(cocoon_dir, "cocoon_*.py")))
                if candidates:
                    print("   Found these nearby:")
                    for c in candidates[:10]:
                        print(f"   - {os.path.basename(c)}")
            print()
            _print_basic_setup_instructions()
            return 2

        try:
            print("⏳ Loading cocoon module from file...")
            mod_name = "_cocoon_from_path"
            spec = importlib.util.spec_from_file_location(mod_name, cocoon_path)
            if spec is None or spec.loader is None:
                raise RuntimeError("Could not create import spec")
            module = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = module
            spec.loader.exec_module(module)
            _ensure_json_default(module)
            if not hasattr(module, 'CocoonAgent'):
                raise AttributeError("CocoonAgent not found in the cocoon module")
            print("✅ Cocoon module imported")
        except Exception as e:
            print(f"❌ Cocoon import failed: {e}")
            import traceback
            traceback.print_exc()
            return 2
    else:
        _try_load_cocoon(quiet=True, scan_exports=True)
        if COCOON_AVAILABLE:
            print("✅ Cocoon auto-detected in current folder")
        else:
            print("⚠️  No cocoon auto-detected in current folder")

    print("\n⏳ Checking TMRL...")
    if not _lazy_load_tmrl():
        print("❌ TMRL not ready")
        return 3
    print("✅ TMRL import OK")

    print("\n⏳ Checking OpenPlanet data stream...")
    if _check_openplanet_ready():
        print("✅ OpenPlanet is streaming data (you appear to be on a track)")
    else:
        print("⚠️  No OpenPlanet data detected.")
        print("   Common fixes:")
        print("   - Launch TrackMania 2020")
        print("   - Start a track (not the main menus)")
        print("   - In OpenPlanet: F3 -> Developer -> (Re)load plugin -> TMRL Grab Data")

    if module is not None:
        try:
            print("\n⏳ Instantiating CocoonAgent (sanity check)...")
            agent = module.CocoonAgent()
            brain_count = len(getattr(agent, 'brains', []) or [])
            print(f"✅ CocoonAgent instantiated (brains={brain_count})")
        except Exception as e:
            print(f"⚠️  CocoonAgent instantiation failed: {e}")

    print("\nDoctor done.")
    return 0

# Local cocoon import - flexible loading
COCOON_AVAILABLE = False
CocoonAgent = None

def _try_load_cocoon(quiet: bool = True, scan_exports: bool = False):
    """Try various methods to load a cocoon.

    This module is often imported for its helpers; avoid printing warnings at
    import-time unless explicitly requested.
    """
    global COCOON_AVAILABLE, CocoonAgent
    
    # Method 1: Local cocoon.py in same folder
    try:
        import cocoon as cocoon_module
        _ensure_json_default(cocoon_module)
        from cocoon import CocoonAgent as CA
        CocoonAgent = CA
        COCOON_AVAILABLE = True
        return
    except ImportError:
        pass
    
    # Method 2: (optional) Look for exported cocoon_ensemble_*.py files
    import glob
    import importlib.util
    import os
    cocoon_files = glob.glob("cocoon_ensemble_*.py") if scan_exports else []
    # Skip ourselves to prevent infinite recursion!
    my_name = os.path.basename(__file__)
    cocoon_files = [cf for cf in cocoon_files if os.path.basename(cf) != my_name]
    for cf in cocoon_files:
        try:
            spec = importlib.util.spec_from_file_location("cocoon", cf)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            _ensure_json_default(module)
            if hasattr(module, 'CocoonAgent'):
                CocoonAgent = module.CocoonAgent
                COCOON_AVAILABLE = True
                print(f"[OK] Loaded cocoon from: {cf}")
                return
        except Exception:
            continue
    
    if not quiet:
        print("[!] No cocoon found. Pass --cocoon path/to/cocoon.py or place cocoon.py in this folder.")

_try_load_cocoon(quiet=True, scan_exports=False)


def _print_basic_setup_instructions():
    print("\nSETUP (super simple):")
    print("  1) Install TMRL into *this* Python:")
    print("     python -m pip install tmrl")
    print("  2) Install/launch TrackMania 2020")
    print("  3) Install OpenPlanet + enable the TMRL plugin (\"TMRL Grab Data\")")
    print("  4) Start a track (NOT the menus), then run:")
    print("     python cocoon_tmrl_adapter.py --drive --cocoon D:\\path\\to\\cocoon_*.py")
    print("\nIf you're stuck, run:")
    print("  python cocoon_tmrl_adapter.py --doctor --cocoon D:\\path\\to\\cocoon_*.py")


# =============================================================================
# URGENCY MODULATOR - Time Pressure System
# =============================================================================

@dataclass
class UrgencyModulator:
    """
    Exponential urgency pressure that teaches organisms time-awareness.
    
    As time elapses toward expected_time, urgency increases exponentially.
    Positive rewards are diminished (less reward for slow progress).
    Negative rewards are amplified (more punishment when time is short).
    
    The urgency signal is also injected into the observation space so
    organisms can learn to perceive time pressure directly.
    """
    expected_time: float = 60.0  # Expected track completion time (seconds)
    alpha: float = 2.0  # Exponential curve steepness
    step_duration: float = 0.05  # Approximate seconds per step (TMRL default ~20Hz)
    
    # Runtime state
    elapsed_steps: int = 0
    episode_start_time: float = 0.0
    
    def reset(self):
        """Reset at episode start."""
        import time
        self.elapsed_steps = 0
        self.episode_start_time = time.time()
    
    def step(self) -> float:
        """Advance one step, return current urgency multiplier."""
        self.elapsed_steps += 1
        return self.get_urgency()
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds (estimate from steps)."""
        return self.elapsed_steps * self.step_duration
    
    def get_time_pressure(self) -> float:
        """Get normalized time pressure (0.0 = just started, 1.0 = at expected time)."""
        return min(1.0, self.get_elapsed_time() / self.expected_time)
    
    def get_urgency(self) -> float:
        """
        Get exponential urgency multiplier.
        
        At t=0: urgency = 1.0 (no pressure)
        At t=expected: urgency = e^alpha (~7.4 for alpha=2.0)
        At t=2*expected: urgency = e^(2*alpha) (~55 for alpha=2.0)
        """
        import math
        pressure = self.get_time_pressure()
        return math.exp(self.alpha * pressure)
    
    def shape_reward(self, base_reward: float) -> float:
        """
        Shape reward based on urgency.
        
        Positive rewards: diminished by urgency (slow progress = less reward)
        Negative rewards: amplified by urgency (crashes are worse when time is short)
        Zero rewards: slight negative based on urgency (standing still costs more over time)
        """
        urgency = self.get_urgency()
        
        if base_reward > 0:
            # Diminish positive rewards as urgency increases
            return base_reward / urgency
        elif base_reward < 0:
            # Amplify negative rewards as urgency increases
            return base_reward * urgency
        else:
            # Zero reward = slight negative pressure (standing still is bad)
            # Scale: -0.001 at start, -0.01 at expected time
            return -0.001 * urgency
    
    def get_observation_signals(self) -> Dict[str, float]:
        """Get urgency signals to inject into observation."""
        return {
            'time_pressure': self.get_time_pressure(),
            'urgency_multiplier': self.get_urgency(),
            'elapsed_steps': float(self.elapsed_steps),
            'remaining_ratio': max(0.0, 1.0 - self.get_time_pressure()),
        }


# =============================================================================
# TRAINABLE ADAPTERS - Bridge TMRL observations to organism brains
# =============================================================================

class InputAdapter(torch.nn.Module):
    """
    Trainable adapter that translates TMRL observations to organism-compatible features.
    
    TMRL sends ~83 floats (LIDAR rays, speed, etc.)
    Organism brains expect ~28 floats (Pong-style features)
    
    This adapter LEARNS the translation during training.
    """
    def __init__(self, tmrl_obs_dim: int, organism_input_dim: int, hidden_dim: int = 64):
        super().__init__()
        self.tmrl_obs_dim = tmrl_obs_dim
        self.organism_input_dim = organism_input_dim
        
        # Two-layer MLP to transform observations
        self.net = torch.nn.Sequential(
            torch.nn.Linear(tmrl_obs_dim, hidden_dim),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden_dim, hidden_dim),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden_dim, organism_input_dim),
            torch.nn.Tanh()  # Normalize to [-1, 1] like game observations
        )
        
        # Initialize with small weights for stability
        for m in self.net:
            if isinstance(m, torch.nn.Linear):
                torch.nn.init.xavier_uniform_(m.weight, gain=0.5)
                torch.nn.init.zeros_(m.bias)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class OutputAdapter(torch.nn.Module):
    """
    Trainable adapter that translates organism actions to TMRL controls.
    
    Organism brains output 4 discrete action probabilities (gas, brake, left, right)
    TMRL expects continuous [gas, brake, steer] in specific ranges
    
    This adapter LEARNS the best mapping during training.
    """
    def __init__(self, organism_output_dim: int = 4, hidden_dim: int = 32):
        super().__init__()
        self.organism_output_dim = organism_output_dim
        
        # Transform organism outputs to TMRL actions
        self.net = torch.nn.Sequential(
            torch.nn.Linear(organism_output_dim, hidden_dim),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden_dim, 3),  # [gas, brake, steer]
        )
        
        # Initialize to produce reasonable default outputs
        for m in self.net:
            if isinstance(m, torch.nn.Linear):
                torch.nn.init.xavier_uniform_(m.weight, gain=0.5)
                torch.nn.init.zeros_(m.bias)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        raw = self.net(x)
        # gas: sigmoid to [0, 1]
        # brake: sigmoid to [0, 1]  
        # steer: tanh to [-1, 1]
        gas = torch.sigmoid(raw[..., 0])
        brake = torch.sigmoid(raw[..., 1])
        steer = torch.tanh(raw[..., 2])
        return torch.stack([gas, brake, steer], dim=-1)


# =============================================================================
# COCOON ACTOR MODULE - Bridge to TMRL
# =============================================================================

class CocoonActorModule:
    """
    Wraps a Convergence Engine organism brain as a TMRL-compatible actor.
    
    This allows Highlander-trained organisms to drive in TrackMania.
    Implements the same interface as TMRL's ActorModule without inheriting from it.
    
    Now includes TRAINABLE ADAPTERS that learn to translate:
    - TMRL observations → organism-compatible features
    - Organism outputs → TMRL continuous controls
    """
    
    def __init__(self, 
                 observation_space, 
                 action_space,
                 cocoon_agent: Optional['CocoonAgent'] = None,
                 organism_idx: int = 0,
                 device: str = "cpu",
                 use_adapters: bool = True,
                 freeze_brains: bool = True):
        """
        Args:
            observation_space: TMRL observation space
            action_space: TMRL action space (gas, brake, steer)
            cocoon_agent: Your exported CocoonAgent
            organism_idx: Which organism brain to use (0 = ensemble, >0 = specific)
            device: "cpu" or "cuda"
            use_adapters: Use trainable input/output adapters (required for good performance!)
            freeze_brains: Freeze organism brains, only train adapters (recommended)
        """
        self.observation_space = observation_space
        self.action_space = action_space
        
        self.cocoon = cocoon_agent or CocoonAgent()
        self.organism_idx = organism_idx
        self.device = device
        self.use_adapters = use_adapters
        self.freeze_brains = freeze_brains
        
        # Action space info
        self.act_dim = action_space.shape[0]  # Usually 3: gas, brake, steer
        self.act_low = action_space.low
        self.act_high = action_space.high
        
        # Urgency modulator (set externally for time-pressure signaling)
        self.urgency: Optional[UrgencyModulator] = None
        
        # Get the brain
        if organism_idx > 0 and organism_idx <= len(self.cocoon.brains):
            self.brain = self.cocoon.brains[organism_idx - 1]
            print(f"🧠 Using organism #{organism_idx} brain")
        else:
            self.brain = None  # Use ensemble voting
            print(f"🧠 Using ensemble voting ({len(self.cocoon.brains)} brains)")
        
        # Get brain architecture info
        sample_brain = self.cocoon.brains[0]
        self.organism_input_dim = getattr(sample_brain, 'input_dim', 30)
        self.organism_output_dim = getattr(sample_brain, 'output_dim', 4)
        
        # Move all brains to device
        for brain in self.cocoon.brains:
            brain.to(device)
            if freeze_brains:
                brain.eval()
                for param in brain.parameters():
                    param.requires_grad = False
        
        # Initialize adapters (created lazily when we know obs dimension)
        self.input_adapter: Optional[InputAdapter] = None
        self.output_adapter: Optional[OutputAdapter] = None
        self._obs_dim_detected = False
        
        if freeze_brains:
            print(f"   🔒 Brains frozen (only adapters train)")
        else:
            print(f"   🔓 Full fine-tuning enabled")
    
    def _ensure_adapters(self, obs_dim: int):
        """Create adapters once we know the observation dimension."""
        if self._obs_dim_detected:
            return
            
        if self.use_adapters:
            self.input_adapter = InputAdapter(
                tmrl_obs_dim=obs_dim,
                organism_input_dim=self.organism_input_dim,
                hidden_dim=64
            ).to(self.device)
            
            self.output_adapter = OutputAdapter(
                organism_output_dim=self.organism_output_dim,
                hidden_dim=32
            ).to(self.device)
            
            print(f"   🔧 Input adapter: {obs_dim} → {self.organism_input_dim}")
            print(f"   🔧 Output adapter: {self.organism_output_dim} → 3 (gas/brake/steer)")
        
        self._obs_dim_detected = True
    
    def _preprocess_obs(self, obs, include_urgency: bool = True) -> np.ndarray:
        """Convert TMRL observation to flat numpy array, optionally with urgency signals."""
        if isinstance(obs, tuple):
            # Tuple observation (e.g., LIDAR + speed + previous actions)
            flat = []
            for o in obs:
                if isinstance(o, np.ndarray):
                    flat.append(o.flatten())
                else:
                    flat.append(np.array([o]).flatten())
            base = np.concatenate(flat).astype(np.float32)
        elif isinstance(obs, dict):
            base = np.concatenate([v.flatten() for v in obs.values()]).astype(np.float32)
        else:
            base = np.asarray(obs, dtype=np.float32).flatten()
        
        # Append urgency signals if available
        if include_urgency and self.urgency is not None:
            signals = self.urgency.get_observation_signals()
            urgency_vec = np.array([
                signals['time_pressure'],
                signals['urgency_multiplier'] / 10.0,  # Normalize (~0.1 to ~1.0)
                signals['remaining_ratio'],
            ], dtype=np.float32)
            base = np.concatenate([base, urgency_vec])
        
        return base
    
    def _action_to_trackmania(self, raw_action: np.ndarray) -> np.ndarray:
        """
        Convert organism output to TrackMania controls.
        
        TrackMania expects:
            - gas: 0 to 1
            - brake: 0 to 1  
            - steer: -1 to 1
        
        Organism outputs action probabilities for 4 discrete actions.
        We treat THROTTLE and STEERING as INDEPENDENT axes:
        
        Throttle axis: GAS (0) vs BRAKE (1)
        Steering axis: LEFT (2) vs RIGHT (3)
        
        This allows the ensemble to vote on throttle and steering separately!
        """
        # Get softmax probabilities
        logits = raw_action[:min(len(raw_action), 4)]
        logits = logits - np.max(logits)  # Numerical stability
        probs = np.exp(logits)
        probs = probs / (probs.sum() + 1e-8)
        
        # Ensure we have 4 values
        if len(probs) < 4:
            probs = np.pad(probs, (0, 4 - len(probs)), constant_values=0.0)
        
        gas_prob = probs[0]
        brake_prob = probs[1]
        left_prob = probs[2]
        right_prob = probs[3]
        
        # THROTTLE: Default to GAS for exploration
        # Only brake when brake_prob significantly exceeds gas_prob
        gas = 0.9  # Default: strong gas for exploration
        brake = 0.0
        
        # Brake only activates when brake_prob > gas_prob + threshold
        brake_margin = brake_prob - gas_prob
        if brake_margin > 0.1:  # Needs 10% margin to start braking
            brake = min(0.8, brake_margin * 2.0)  # Scale brake strength
            gas = max(0.3, 0.9 - brake_margin)    # Reduce gas when braking
        
        # STEERING: LEFT is negative, RIGHT is positive
        steer_diff = right_prob - left_prob
        steer = steer_diff * 2.5  # Scale up for responsiveness
        steer = np.clip(steer, -1.0, 1.0)
        
        # Reduce gas slightly when steering hard
        steer_intensity = abs(steer)
        if steer_intensity > 0.3:
            gas = gas * (1.0 - 0.2 * steer_intensity)
        
        return np.array([gas, brake, steer], dtype=np.float32)
    
    def act(self, obs, test: bool = False) -> np.ndarray:
        """
        Compute action from observation.
        
        Args:
            obs: TMRL observation (LIDAR, speed, etc.)
            test: True during evaluation, False during training
        
        Returns:
            np.ndarray: [gas, brake, steer] actions
        """
        # Preprocess observation to flat array
        state = self._preprocess_obs(obs)
        
        # Ensure adapters are initialized
        self._ensure_adapters(len(state))
        
        # Convert to tensor
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        # Apply input adapter if using adapters
        if self.use_adapters and self.input_adapter is not None:
            with torch.set_grad_enabled(self.training if hasattr(self, 'training') else False):
                adapted_state = self.input_adapter(state_tensor)
        else:
            # Fallback: just truncate/pad to match brain input
            adapted_state = state_tensor
        
        # Get action from brain(s)
        with torch.no_grad():
            if self.brain:
                # Single organism
                output = self.brain(adapted_state, return_language_logits=False)
                if isinstance(output, tuple):
                    output = output[0]
                brain_output = output
                winning_action = int(torch.argmax(output[:, :4]).item())
                vote_counts = {winning_action: 1}
                self._last_avg_probs = output[0, :4].cpu().numpy()
            else:
                # Ensemble: average all brain outputs
                from collections import Counter
                
                all_outputs = []
                votes = []
                
                for brain in self.cocoon.brains:
                    output = brain(adapted_state, return_language_logits=False)
                    if isinstance(output, tuple):
                        output = output[0]
                    all_outputs.append(output)
                    discrete = int(torch.argmax(output[:, :4]).item())
                    votes.append(discrete)
                
                vote_counts = Counter(votes)
                # Average all outputs
                brain_output = torch.mean(torch.stack(all_outputs), dim=0)
                self._last_avg_probs = brain_output[0, :4].cpu().numpy()
        
        # Apply output adapter if using adapters
        if self.use_adapters and self.output_adapter is not None:
            with torch.set_grad_enabled(self.training if hasattr(self, 'training') else False):
                action_tensor = self.output_adapter(brain_output[:, :4])
                action = action_tensor.cpu().detach().numpy().squeeze()
        else:
            # Fallback: use heuristic mapping
            raw_action = brain_output.cpu().numpy().squeeze()
            action = self._action_to_trackmania(raw_action)
        
        # Granular debug output
        self._step_count = getattr(self, '_step_count', 0) + 1
        if self._step_count % 5 == 0:  # Every 5 steps
            vote_str = ' '.join([f"{k}:{v}" for k,v in sorted(vote_counts.items())])
            avg_probs = self._last_avg_probs
            prob_str = f"G:{avg_probs[0]:.0%} B:{avg_probs[1]:.0%} L:{avg_probs[2]:.0%} R:{avg_probs[3]:.0%}"
            adapter_str = "🔧" if self.use_adapters else "⚠️"
            print(f"   [{self._step_count:3d}] {adapter_str} Votes: {vote_str} | Avg: {prob_str} → gas={action[0]:.2f} brake={action[1]:.2f} steer={action[2]:+.2f}")
        
        return action
    
    def get_trainable_parameters(self):
        """Get parameters that should be trained (adapters only if brains frozen)."""
        params = []
        if self.input_adapter is not None:
            params.extend(self.input_adapter.parameters())
        if self.output_adapter is not None:
            params.extend(self.output_adapter.parameters())
        if not self.freeze_brains:
            for brain in self.cocoon.brains:
                params.extend(brain.parameters())
        return params
    
    def save(self, path):
        """Save the actor module including trained adapters."""
        save_data = {
            'organism_idx': self.organism_idx,
            'device': self.device,
            'use_adapters': self.use_adapters,
            'freeze_brains': self.freeze_brains,
        }
        if self.input_adapter is not None:
            save_data['input_adapter_state'] = self.input_adapter.state_dict()
        if self.output_adapter is not None:
            save_data['output_adapter_state'] = self.output_adapter.state_dict()
        torch.save(save_data, path)
        print(f"💾 Saved actor module with adapters to {path}")
    
    def load(self, path, device):
        """Load the actor module including trained adapters."""
        data = torch.load(path, map_location=device)
        self.organism_idx = data.get('organism_idx', 0)
        self.device = device
        
        # Load adapter states if present
        if 'input_adapter_state' in data and self.input_adapter is not None:
            self.input_adapter.load_state_dict(data['input_adapter_state'])
            print(f"   ✅ Loaded trained input adapter")
        if 'output_adapter_state' in data and self.output_adapter is not None:
            self.output_adapter.load_state_dict(data['output_adapter_state'])
            print(f"   ✅ Loaded trained output adapter")
        return self


# =============================================================================
# TMRL WORKER FACTORY
# =============================================================================

def create_tmrl_worker(
    cocoon_agent: Optional['CocoonAgent'] = None,
    organism_idx: int = 0,
    server_ip: str = "127.0.0.1",
    server_port: int = 6666,
    run_name: str = "cocoon_trackmania",
    device: str = "cpu"
) -> 'RolloutWorker':
    """
    Create a TMRL RolloutWorker using a cocoon organism.
    
    Args:
        cocoon_agent: Your CocoonAgent (loads from cocoon.py if None)
        organism_idx: Which organism to use (0 = ensemble)
        server_ip: TMRL server IP
        server_port: TMRL server port
        run_name: Name for this run
        device: "cpu" or "cuda"
    
    Returns:
        RolloutWorker ready to collect samples in TrackMania
    """
    if not TMRL_AVAILABLE:
        raise RuntimeError("TMRL not installed. Run: pip install tmrl")
    
    # Load cocoon if not provided
    agent = cocoon_agent or CocoonAgent()
    
    # Create actor module factory
    def actor_module_cls(observation_space, action_space):
        return CocoonActorModule(
            observation_space=observation_space,
            action_space=action_space,
            cocoon_agent=agent,
            organism_idx=organism_idx,
            device=device
        )
    
    # Environment (TrackMania with LIDAR)
    env_cls = partial(
        GenericGymEnv,
        id="real-time-gym-v1",
        gym_kwargs={"config": cfg.ENV_CONFIG}
    )
    
    # Paths
    weights_folder = cfg.WEIGHTS_FOLDER
    model_path = str(weights_folder / (run_name + ".tmod"))
    
    # Create worker
    worker = RolloutWorker(
        env_cls=env_cls,
        actor_module_cls=actor_module_cls,
        sample_compressor=None,
        device=device,
        server_ip=server_ip,
        server_port=server_port,
        password=cfg.PASSWORD,
        max_samples_per_episode=1000,
        model_path=model_path,
        crc_debug=False
    )
    
    return worker


# =============================================================================
# STANDALONE TRACKMANIA DRIVER
# =============================================================================

def drive_trackmania(
    cocoon_agent: Optional['CocoonAgent'] = None,
    organism_idx: int = 0,
    episodes: int = 10,
    render: bool = True,
    device: str = "cpu",
    enable_training: bool = False,
    learning_rate: float = 1e-4,
    batch_size: int = 32,
    gamma: float = 0.99,
    train_every: int = 4,
    save_every: int = 10,
    save_path: Optional[str] = None,
    track_time: float = 60.0,
    urgency_alpha: float = 2.0
) -> Dict[str, Any]:
    """
    Drive in TrackMania using a cocoon organism (standalone mode).
    Optionally train the organisms in-place using policy-gradient style updates.
    
    Args:
        cocoon_agent: Your CocoonAgent
        organism_idx: Which organism (0 = ensemble)
        episodes: Number of episodes to run
        render: Show the game (should be True for TrackMania)
        device: "cpu" or "cuda"
        enable_training: If True, collect experience and update brains during drive
        learning_rate: Optimizer learning rate when training
        batch_size: Replay samples per gradient step
        gamma: Reward discount for returns
        train_every: Steps between optimization passes
        save_every: Episodes between checkpoint saves
        save_path: Optional custom export path for trained cocoon
    
    Returns:
        Dict with episode metrics and optional training stats
    """
    if not TMRL_AVAILABLE:
        raise RuntimeError("TMRL not installed. Run: pip install tmrl")
    
    import gymnasium as gym
    import subprocess
    import time as time_module
    
    # Helper to check if OpenPlanet is sending data (meaning we're on a track)
    def check_openplanet_ready():
        return _check_openplanet_ready(timeout_s=2.0)
    
    # Helper to launch and focus TrackMania
    def launch_and_focus_trackmania():
        """Launch TrackMania via Ubisoft Connect and focus the window. Returns state."""
        try:
            import ctypes
            from ctypes import wintypes
            
            # Find TrackMania window
            user32 = ctypes.windll.user32
            
            def find_window(title_part):
                """Find window by partial title match."""
                hwnd_found = [None]
                
                def enum_callback(hwnd, lparam):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buff, length + 1)
                        if title_part.lower() in buff.value.lower():
                            hwnd_found[0] = hwnd
                            return False  # Stop enumeration
                    return True
                
                WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
                user32.EnumWindows(WNDENUMPROC(enum_callback), 0)
                return hwnd_found[0]
            
            # Check if TrackMania is running
            hwnd = find_window("Trackmania")
            game_was_running = hwnd is not None
            
            if not hwnd:
                print("🚀 Launching TrackMania...")
                # Try Ubisoft Connect URI
                subprocess.Popen(
                    ["cmd", "/c", "start", "uplay://launch/5595/0"],
                    shell=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                # Wait for game to start
                for _ in range(60):  # 60 second timeout
                    time_module.sleep(1)
                    hwnd = find_window("Trackmania")
                    if hwnd:
                        print("✅ TrackMania launched!")
                        print("⏳ Waiting for OpenPlanet to load (15s)...")
                        time_module.sleep(15)  # OpenPlanet needs time to initialize
                        break
                else:
                    print("[!] TrackMania did not start. Please launch manually.")
                    return None, False
            else:
                print("✅ TrackMania already running")
            
            # DON'T auto-focus - let user control when to switch
            # (focus stealing is annoying)
            
            return hwnd, game_was_running
            
        except Exception as e:
            print(f"[!] Could not auto-launch TrackMania: {e}")
            print("    Please launch TrackMania manually and focus the window.")
            return None, False
    
    # Load cocoon
    agent = cocoon_agent or CocoonAgent()
    
    # Launch and focus TrackMania first
    hwnd, game_was_running = launch_and_focus_trackmania()
    
    # Check if already on a track (OpenPlanet sending data)
    if game_was_running:
        print("🔍 Checking if you're on a track...")
        if check_openplanet_ready():
            print("✅ Already on a track! Starting immediately...")
        else:
            print("\n⚠️  You're in menus. Please start a race/track.")
            print("   Press ENTER when you're on a track and ready...")
            input()
    else:
        # Fresh launch - need to wait for user to get to a track
        print("\n⚠️  IMPORTANT: You must be ON A TRACK (not in menus)!")
        print("   Start any race/track, then the organisms will take over.")
        print("   Press ENTER when you're on a track and ready...")
        input()
    
    # CRITICAL: Focus TrackMania window BEFORE sending inputs
    print("🎯 Focusing TrackMania window...")
    import time as time_mod
    time_mod.sleep(0.3)
    
    try:
        import subprocess
        # Use VBScript AppActivate - simple and reliable
        vbs = 'CreateObject("WScript.Shell").AppActivate "Trackmania"'
        result = subprocess.run(
            ["cscript", "//nologo", "//e:vbscript"],
            input=vbs, capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            print("   ✓ TrackMania focused!")
            time_mod.sleep(0.5)
        else:
            print("   ⚠️  Could not auto-focus")
            print("   >>> CLICK ON TRACKMANIA NOW (3 sec)! <<<")
            time_mod.sleep(3)
    except Exception as e:
        print(f"   ⚠️  Focus failed: {e}")
        print("   >>> CLICK ON TRACKMANIA NOW (3 sec)! <<<")
        time_mod.sleep(3)
    
    # Create TrackMania environment using LIDAR interface directly
    try:
        print("🔗 Connecting to TrackMania...")
        
        # Just use TMRL's built-in environment
        from tmrl import get_environment
        import time as time_mod
        
        print("   📦 Calling get_environment()...")
        env = get_environment()
        print("   ✅ Environment created")
        
        # User must reload plugin after TMRL resizes window
        print("\n" + "="*60)
        print("   ⚠️  TMRL may have resized your window")
        print("   If OpenPlanet stopped working:")
        print("   1. Press F3")
        print("   2. Developer → (Re)load plugin → TMRL Grab Data")
        print("   3. Press F3 to close")
        print("="*60)
        input("\n   Press ENTER to continue...")
        print()
        
        print("✅ Connected to TrackMania!")
    except Exception as e:
        print(f"[!] Could not create TrackMania environment: {e}")
        print("    Make sure TrackMania 2020 is running with OpenPlanet plugin.")
        import traceback
        traceback.print_exc()
        return []
    
    # Create actor with adapters
    actor = CocoonActorModule(
        observation_space=env.observation_space,
        action_space=env.action_space,
        cocoon_agent=agent,
        organism_idx=organism_idx,
        device=device,
        use_adapters=True,  # Enable trainable adapters!
        freeze_brains=True   # Freeze brains, only train adapters
    )
    
    # Create urgency modulator for time-pressure awareness
    urgency = UrgencyModulator(
        expected_time=track_time,
        alpha=urgency_alpha,
        step_duration=0.05  # ~20Hz TMRL default
    )
    actor.urgency = urgency
    print(f"⏱️  Urgency system: {track_time}s expected, α={urgency_alpha}")
    
    training_summary = None
    brains_to_train: List[Any] = []
    optimizers: List[Any] = []
    experience_buffer = None
    buffer_lock = None
    train_signal = None
    training_stop_event = None
    training_thread = None
    training_losses: List[float] = []
    training_episode_rewards: List[float] = []
    best_reward = float('-inf')
    if enable_training:
        from collections import deque
        
        # Get trainable parameters (adapters only since brains are frozen)
        trainable_params = actor.get_trainable_parameters()
        if trainable_params:
            print(f"🧠 Training adapters ({sum(p.numel() for p in trainable_params)} parameters)")
            optimizers = [torch.optim.Adam(trainable_params, lr=learning_rate)]
            brains_to_train = [actor]  # Train actor (which contains adapters)
        else:
            # Fallback to training brains directly
            if organism_idx > 0 and organism_idx <= len(agent.brains):
                brains_to_train = [agent.brains[organism_idx - 1]]
                print(f"🧠 Training organism #{organism_idx} brain directly")
            else:
                brains_to_train = agent.brains
                print(f"🧠 Training ALL {len(brains_to_train)} organism brains")
            optimizers = [torch.optim.Adam(brain.parameters(), lr=learning_rate) for brain in brains_to_train]
        
        experience_buffer = deque(maxlen=10000)
        buffer_lock = threading.Lock()
        train_signal = queue.Queue()
        training_stop_event = threading.Event()
        training_thread = threading.Thread(
            target=_training_worker_adapters,
            args=(
                training_stop_event,
                experience_buffer,
                buffer_lock,
                train_signal,
                actor,
                optimizers,
                batch_size,
                gamma,
                device,
                training_losses
            ),
            daemon=True
        )
        training_thread.start()
        print(f"   Training mode: lr={learning_rate} batch={batch_size} γ={gamma} train_every={train_every}")
        if save_every:
            print(f"   Checkpoints every {save_every} episode(s)")
        print()
    
    results = []
    
    print(f"\n🏎️ TRACKMANIA DRIVER")
    print(f"   Organism: {'ensemble' if organism_idx == 0 else f'#{organism_idx}'}")
    print(f"   Episodes: {episodes}")
    if enable_training:
        print("   Training: ENABLED (background updates mid-drive)")
    print()
    
    for ep in range(episodes):
        obs, info = env.reset()
        done = False
        total_reward = 0
        total_raw_reward = 0  # Track unshaped reward for comparison
        steps = 0
        reward_history = []  # Track rewards for debugging
        episode_experiences = None
        if enable_training:
            episode_experiences = []
        
        # Reset urgency for new episode
        urgency.reset()
        
        print(f"Episode {ep + 1}/{episodes}...")
        print("   [step] Vote breakdown → Action | controls | reward")
        print("   " + "─" * 60)
        
        while not done:
            state_for_training = _preprocess_obs_for_training(obs) if enable_training else None
            action = actor.act(obs, test=True)
            
            result = env.step(action)
            if len(result) == 5:
                obs, reward, terminated, truncated, info = result
                done = terminated or truncated
            else:
                obs, reward, done, info = result
            
            # Apply urgency shaping to reward
            raw_reward = reward
            total_raw_reward += raw_reward
            shaped_reward = urgency.shape_reward(raw_reward)
            urgency.step()  # Advance urgency clock
            
            # Use shaped reward for training
            total_reward += shaped_reward
            reward_history.append(shaped_reward)
            steps += 1
            
            if enable_training and state_for_training is not None and episode_experiences is not None:
                episode_experiences.append({
                    'state': state_for_training,
                    'reward': shaped_reward,  # Use shaped reward!
                    'raw_reward': raw_reward,
                    'urgency': urgency.get_urgency(),
                    'time_pressure': urgency.get_time_pressure(),
                    'done': done
                })
                if train_every > 0 and steps % train_every == 0 and train_signal is not None:
                    train_signal.put(1)
            
            # Show reward every 5 steps (synced with vote debug in actor.act)
            if steps % 5 == 0:
                recent_rewards = reward_history[-5:]
                avg_recent = sum(recent_rewards) / len(recent_rewards)
                reward_trend = "📈" if avg_recent > 0 else "📉" if avg_recent < 0 else "➡️"
                urg_pct = urgency.get_time_pressure() * 100
                urg_mult = urgency.get_urgency()
                # Also show speed if available
                try:
                    if isinstance(obs, tuple) and len(obs) > 0:
                        speed_val = float(obs[0][0]) if isinstance(obs[0], np.ndarray) else float(obs[0])
                        print(f"         speed={speed_val:.0f} reward={shaped_reward:+.3f} (avg: {avg_recent:+.3f}) {reward_trend} ⏱{urg_pct:.0f}% ×{urg_mult:.1f}")
                    else:
                        print(f"         reward={shaped_reward:+.3f} (avg: {avg_recent:+.3f}) {reward_trend} ⏱{urg_pct:.0f}% ×{urg_mult:.1f}")
                except Exception:
                    print(f"         reward={shaped_reward:+.3f} (avg: {avg_recent:+.3f}) {reward_trend} ⏱{urg_pct:.0f}% ×{urg_mult:.1f}")
        
        print("   " + "─" * 60)
        final_urg = urgency.get_urgency()
        elapsed = urgency.get_elapsed_time()
        print(f"   ✓ Finished! Shaped Reward: {total_reward:+.2f} (raw: {total_raw_reward:+.2f}), Steps: {steps}")
        print(f"   ⏱️  Time: {elapsed:.1f}s elapsed, final urgency: ×{final_urg:.1f}")
        
        # Show reward distribution
        positive_steps = sum(1 for r in reward_history if r > 0)
        negative_steps = sum(1 for r in reward_history if r < 0)
        zero_steps = sum(1 for r in reward_history if abs(r) < 1e-6)  # Near-zero after shaping
        print(f"   Reward breakdown: +ve:{positive_steps} | -ve:{negative_steps} | ~zero:{zero_steps}")
        
        if enable_training and episode_experiences:
            if experience_buffer is not None and buffer_lock is not None:
                with buffer_lock:
                    _add_episode_with_returns(experience_buffer, episode_experiences, gamma)
            elif experience_buffer is not None:
                _add_episode_with_returns(experience_buffer, episode_experiences, gamma)
            training_episode_rewards.append(total_reward)
            recent_window = training_episode_rewards[-10:]
            avg_recent = np.mean(recent_window)
            print(f"   Training stats → recent avg shaped reward: {avg_recent:+.2f}")
            improved = total_reward > best_reward
            if improved:
                best_reward = total_reward
            if save_every and (ep + 1) % save_every == 0 and improved:
                _save_trained_cocoon(agent, save_path, ep + 1)
            if train_signal is not None:
                train_signal.put(1)
        
        results.append({
            'episode': ep + 1,
            'reward': total_reward,
            'steps': steps,
            'info': info
        })
    
    env.close()
    
    # Stop the magnified viewer
    try:
        viewer_running[0] = False
        cv2.destroyAllWindows()
    except:
        pass
    
    if enable_training and training_thread is not None:
        training_stop_event.set()
        if train_signal is not None:
            train_signal.put(None)
        training_thread.join(timeout=5)
    
    # Summary
    avg_reward = np.mean([r['reward'] for r in results])
    print(f"\n📊 Average reward: {avg_reward:.1f}")
    
    if enable_training:
        _save_trained_cocoon(agent, save_path, episodes)
        final_recent = np.mean(training_episode_rewards[-10:]) if training_episode_rewards else avg_reward
        print("📚 Training summary")
        print(f"   Episodes: {episodes}")
        print(f"   Best reward: {best_reward:.1f}")
        print(f"   Final avg(10): {final_recent:.1f}")
        training_summary = {
            'episode_rewards': training_episode_rewards,
            'training_losses': training_losses,
            'best_reward': best_reward,
            'final_avg_10': final_recent
        }
    
    return {
        'episodes': results,
        'training': training_summary
    }


# =============================================================================
# TRAINING MODE - Learn while driving!
# =============================================================================

def train_in_trackmania(
    cocoon_agent: Optional['CocoonAgent'] = None,
    organism_idx: int = 0,
    episodes: int = 100,
    learning_rate: float = 1e-4,
    batch_size: int = 32,
    gamma: float = 0.99,
    train_every: int = 4,
    save_every: int = 10,
    save_path: Optional[str] = None,
    device: str = "cpu"
) -> Dict[str, Any]:
    """
    🧠 TRAINING MODE - Organisms learn from TrackMania experience!
    
    Uses simple policy gradient (REINFORCE with baseline) to update
    the organism's brain weights based on racing performance.
    
    Args:
        cocoon_agent: Your CocoonAgent
        organism_idx: Which organism to train (0 = trains all via ensemble)
        episodes: Number of training episodes
        learning_rate: Learning rate for optimizer
        batch_size: Experiences per training batch
        gamma: Discount factor for rewards
        train_every: Train after this many steps
        save_every: Save cocoon every N episodes
        save_path: Where to save updated cocoon (None = auto)
        device: "cpu" or "cuda"
    
    Returns:
        Dict with training stats and updated agent
    """
    result = drive_trackmania(
        cocoon_agent=cocoon_agent,
        organism_idx=organism_idx,
        episodes=episodes,
        render=True,
        device=device,
        enable_training=True,
        learning_rate=learning_rate,
        batch_size=batch_size,
        gamma=gamma,
        train_every=train_every,
        save_every=save_every,
        save_path=save_path
    )
    return result.get('training') if isinstance(result, dict) else result


def _preprocess_obs_for_training(obs) -> np.ndarray:
    """Convert TMRL observation to flat numpy array."""
    if isinstance(obs, tuple):
        flat = []
        for o in obs:
            if isinstance(o, np.ndarray):
                flat.append(o.flatten())
            else:
                flat.append(np.array([o]).flatten())
        return np.concatenate(flat).astype(np.float32)
    elif isinstance(obs, dict):
        return np.concatenate([v.flatten() for v in obs.values()]).astype(np.float32)
    else:
        return np.asarray(obs, dtype=np.float32).flatten()


def _add_episode_with_returns(buffer, experiences, gamma):
    """Add episode experiences with computed returns (rewards-to-go)."""
    returns = []
    R = 0
    for exp in reversed(experiences):
        R = exp['reward'] + gamma * R
        returns.insert(0, R)
    
    for exp, ret in zip(experiences, returns):
        exp['return'] = ret
        buffer.append(exp)


def _training_worker_adapters(stop_event, buffer, buffer_lock, signal_queue, actor, optimizers, batch_size, gamma, device, training_losses):
    """Background thread: trains ADAPTERS (not brains) using policy gradient."""
    while not stop_event.is_set():
        try:
            signal = signal_queue.get(timeout=0.5)
        except queue.Empty:
            continue
        if signal is None and stop_event.is_set():
            break
        with buffer_lock:
            buffer_snapshot = list(buffer)
        if not buffer_snapshot:
            continue
        loss = _train_step_adapters(actor, optimizers, buffer_snapshot, batch_size, gamma, device)
        training_losses.append(loss)


def _train_step_adapters(actor, optimizers, buffer_data, batch_size, gamma, device):
    """Perform one training step on adapters using policy gradient."""
    import random
    
    data_source = list(buffer_data)
    if not data_source:
        return 0.0
    
    # Sample batch
    batch = random.sample(data_source, min(batch_size, len(data_source)))
    
    # Ensure adapters exist and are in training mode
    if actor.input_adapter is None or actor.output_adapter is None:
        return 0.0
    
    actor.input_adapter.train()
    actor.output_adapter.train()
    
    # Zero gradients
    for opt in optimizers:
        opt.zero_grad()
    
    loss = torch.tensor(0.0, device=device, requires_grad=True)
    
    for exp in batch:
        state = torch.FloatTensor(exp['state']).unsqueeze(0).to(device)
        action_taken = exp.get('action', None)
        ret = exp['return']
        
        # Forward through adapters and brain
        adapted_state = actor.input_adapter(state)
        
        # Get brain output (frozen, no grad)
        with torch.no_grad():
            if actor.brain:
                brain_output = actor.brain(adapted_state, return_language_logits=False)
            else:
                outputs = []
                for brain in actor.cocoon.brains:
                    out = brain(adapted_state, return_language_logits=False)
                    if isinstance(out, tuple):
                        out = out[0]
                    outputs.append(out)
                brain_output = torch.mean(torch.stack(outputs), dim=0)
        
        if isinstance(brain_output, tuple):
            brain_output = brain_output[0]
        
        # Forward through output adapter (trainable)
        action_tensor = actor.output_adapter(brain_output[:, :4])
        
        # Simple reward-weighted loss
        # Higher returns should make current action more likely
        action_norm = torch.norm(action_tensor)
        step_loss = -ret * action_norm  # Negative because optimizer minimizes
        loss = loss + step_loss
    
    loss = loss / len(batch)
    loss.backward()
    
    # Gradient clipping
    if actor.input_adapter is not None:
        torch.nn.utils.clip_grad_norm_(actor.input_adapter.parameters(), 1.0)
    if actor.output_adapter is not None:
        torch.nn.utils.clip_grad_norm_(actor.output_adapter.parameters(), 1.0)
    
    for opt in optimizers:
        opt.step()
    
    return loss.item()


def _training_worker(stop_event, buffer, buffer_lock, signal_queue, brains, optimizers, batch_size, gamma, device, training_losses):
    """Background thread: waits for signals, then performs training steps."""
    while not stop_event.is_set():
        try:
            signal = signal_queue.get(timeout=0.5)
        except queue.Empty:
            continue
        if signal is None and stop_event.is_set():
            break
        with buffer_lock:
            buffer_snapshot = list(buffer)
        if not buffer_snapshot:
            continue
        loss = _train_step(brains, optimizers, buffer_snapshot, batch_size, gamma, device)
        training_losses.append(loss)


def _train_step(brains, optimizers, buffer_data, batch_size, gamma, device):
    """Perform one training step with policy gradient."""
    import random
    
    data_source = list(buffer_data)
    if not data_source:
        return 0.0
    
    # Sample batch
    batch = random.sample(data_source, min(batch_size, len(data_source)))
    
    # Compute loss for each brain
    total_loss = 0
    
    for brain, optimizer in zip(brains, optimizers):
        brain.train()
        optimizer.zero_grad()
        
        loss = torch.tensor(0.0, device=device)
        
        for exp in batch:
            state = torch.FloatTensor(exp['state']).unsqueeze(0).to(device)
            ret = exp['return']
            
            # Forward pass
            output = brain(state, return_language_logits=False)
            if isinstance(output, tuple):
                output = output[0]
            
            # Simple policy gradient: maximize return * log_prob
            # Using softmax log_prob approximation
            log_probs = torch.log_softmax(output.flatten()[:3], dim=0)
            
            # Reward-weighted loss (negative because we minimize)
            loss = loss - (ret * log_probs.mean())
        
        loss = loss / len(batch)
        loss.backward()
        
        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(brain.parameters(), 1.0)
        
        optimizer.step()
        total_loss += loss.item()
    
    return total_loss / len(brains)


def _save_trained_cocoon(agent, save_path, episode):
    """Save the updated cocoon with trained weights."""
    if save_path is None:
        save_path = f"cocoon_trained_ep{episode}.py"
    
    try:
        if hasattr(agent, 'export_cocoon'):
            agent.export_cocoon(save_path)
            print(f"   💾 Saved: {save_path}")
        else:
            # Fallback: save just the state dicts
            import pickle
            state_dicts = [brain.state_dict() for brain in agent.brains]
            with open(save_path.replace('.py', '_weights.pkl'), 'wb') as f:
                pickle.dump(state_dicts, f)
            print(f"   💾 Saved weights: {save_path.replace('.py', '_weights.pkl')}")
    except Exception as e:
        print(f"   ⚠️ Save failed: {e}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Demo and usage information."""
    import argparse
    import glob
    import importlib.util
    
    parser = argparse.ArgumentParser(description="🏎️ Cocoon TMRL Adapter - Drive TrackMania with your organisms")
    parser.add_argument('--drive', action='store_true', help='Start driving in TrackMania (inference only)')
    parser.add_argument('--train', action='store_true', help='Train while driving (organisms learn!)')
    parser.add_argument('--organism', type=int, default=0, help='Organism index (0=ensemble, 1+=specific)')
    parser.add_argument('--episodes', type=int, default=5, help='Number of episodes to run')
    parser.add_argument('--lr', type=float, default=1e-4, help='Learning rate (training mode)')
    parser.add_argument('--cocoon', type=str, default=None, help='Path to cocoon.py file')
    parser.add_argument('--save', type=str, default=None, help='Path to save trained cocoon')
    parser.add_argument('--track-time', type=float, default=60.0, help='Expected track completion time in seconds (default: 60)')
    parser.add_argument('--urgency-alpha', type=float, default=2.0, help='Urgency exponential steepness (default: 2.0)')
    parser.add_argument('--doctor', action='store_true', help='Run setup diagnostics (does not launch TrackMania)')
    args = parser.parse_args()
    
    print("🏎️ COCOON TMRL ADAPTER")
    print("=" * 50)
    print()

    if args.doctor:
        raise SystemExit(_doctor(args.cocoon))

    # If no explicit cocoon path was passed, try to auto-detect exports in the CWD.
    if not args.cocoon:
        _try_load_cocoon(quiet=True, scan_exports=True)
    
    save_path = args.save
    cocoon_dir = None
    cocoon_name = None
    
    # Try to load cocoon from specified path
    if args.cocoon:
        cocoon_path = os.path.abspath(args.cocoon)
        cocoon_dir = os.path.dirname(cocoon_path)
        cocoon_name = os.path.basename(cocoon_path).replace('.py', '')

        if not os.path.isfile(cocoon_path):
            print(f"❌ Cocoon file not found: {cocoon_path}")
            if os.path.isdir(cocoon_dir):
                candidates = sorted(glob.glob(os.path.join(cocoon_dir, 'cocoon_*.py')))
                if candidates:
                    print("   Found these nearby:")
                    for c in candidates[:10]:
                        print(f"   - {os.path.basename(c)}")
            _print_basic_setup_instructions()
            return

        try:
            print("⏳ Loading cocoon (this may take a moment for large files)...")
            spec = importlib.util.spec_from_file_location("_cocoon_from_cli", cocoon_path)
            if spec is None or spec.loader is None:
                raise RuntimeError("Could not create import spec")
            cocoon_module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = cocoon_module
            spec.loader.exec_module(cocoon_module)
            _ensure_json_default(cocoon_module)
            global CocoonAgent, COCOON_AVAILABLE
            CocoonAgent = cocoon_module.CocoonAgent
            COCOON_AVAILABLE = True
            print(f"✅ Loaded cocoon from: {cocoon_path}")
        except Exception as e:
            print(f"❌ Failed to load {cocoon_path}: {e}")
            import traceback
            traceback.print_exc()
            return
    
    if save_path is None and cocoon_dir and cocoon_name:
        save_path = os.path.join(cocoon_dir, f"{cocoon_name}_trained.py")
        print(f"💾 Training outputs will be saved to: {save_path}")
    
    if not COCOON_AVAILABLE:
        print("❌ No cocoon found!")
        print()
        print("SETUP OPTIONS:")
        print()
        print("  1. Put cocoon.py in the same folder as this script")
        print("  2. Use --cocoon path/to/your/cocoon_ensemble_*.py")
        print("  3. Rename your export to cocoon.py")
        print("  4. Run: python cocoon_tmrl_adapter.py --doctor --cocoon path/to/cocoon.py")
        print()
        return
    
    # Lazy load TMRL after cocoon is ready
    print("⏳ Loading TMRL (TrackMania interface)...")
    if not _lazy_load_tmrl():
        print("❌ TMRL not available!")
        print("   Run: pip install tmrl")
        print()
        return
    
    print("✅ Cocoon found")
    print("✅ TMRL available")
    print()
    
    # Load cocoon
    agent = CocoonAgent()
    print(f"🦋 Loaded cocoon with {len(agent.brains)} organism brains")
    print()
    
    if args.drive:
        print("🏎️ Starting TrackMania driver...")
        if args.train:
            print("   Training ENABLED: gradients update on a background thread")
        else:
            print("   Mode: inference-only")
        print("   Make sure TrackMania 2020 is running with OpenPlanet!")
        print()
        results = drive_trackmania(
            cocoon_agent=agent,
            organism_idx=args.organism,
            episodes=args.episodes,
            enable_training=args.train,
            learning_rate=args.lr,
            save_path=save_path,
            track_time=args.track_time,
            urgency_alpha=args.urgency_alpha
        )
    elif args.train:
        # Back-compat: allow training without explicit --drive flag
        print("🧠 TrackMania TRAINING (drive loop shared)...")
        print("   Make sure TrackMania 2020 is running with OpenPlanet!")
        print()
        results = drive_trackmania(
            cocoon_agent=agent,
            organism_idx=args.organism,
            episodes=args.episodes,
            enable_training=True,
            learning_rate=args.lr,
            save_path=save_path,
            track_time=args.track_time,
            urgency_alpha=args.urgency_alpha
        )
    else:
        # Just show usage
        print("USAGE:")
        print()
        print("  # INFERENCE - Just drive (no learning):")
        print("  python cocoon_tmrl_adapter.py --drive")
        print("  python cocoon_tmrl_adapter.py --drive --organism 3 --episodes 10")
        print()
        print("  # TRAINING - Organisms learn while racing!")
        print("  python cocoon_tmrl_adapter.py --train --episodes 100")
        print("  python cocoon_tmrl_adapter.py --train --organism 1 --lr 0.0001 --save trained.py")
        print()
        print("  # URGENCY TUNING - Teach time pressure:")
        print("  python cocoon_tmrl_adapter.py --train --track-time 45 --urgency-alpha 2.5")
        print()
        print("  # With explicit cocoon path:")
        print("  python cocoon_tmrl_adapter.py --train --cocoon path/to/cocoon.py")
        print()
        print("  # In Python:")
        print("  from cocoon_tmrl_adapter import train_in_trackmania")
        print("  results = train_in_trackmania(organism_idx=1, episodes=100)")
        print()
        
        # Quick test
        print("Quick test - creating actor module...")
        try:
            import gymnasium as gym
            dummy_obs_space = gym.spaces.Box(low=-1, high=1, shape=(28,), dtype=np.float32)
            dummy_act_space = gym.spaces.Box(low=np.array([0, 0, -1]), high=np.array([1, 1, 1]), dtype=np.float32)
            
            actor = CocoonActorModule(
                observation_space=dummy_obs_space,
                action_space=dummy_act_space,
                cocoon_agent=agent,
                organism_idx=args.organism or 1
            )
            
            # Test action
            dummy_obs = np.random.randn(28).astype(np.float32)
            action = actor.act(dummy_obs, test=True)
            
            print(f"✅ Actor test passed!")
            print(f"   Input: {dummy_obs.shape} observation")
            print(f"   Output: {action} (gas, brake, steer)")
            
        except Exception as e:
            print(f"⚠️ Actor test failed: {e}")


if __name__ == "__main__":
    main()
