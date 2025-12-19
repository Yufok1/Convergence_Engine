"""
Hardware Governor - Sovereign Hardware Profile Management

This module provides hardware-aware configuration that SUPERSEDES CRA's self-tuning
for hardware-critical parameters. CRA can optimize within the envelope, but cannot
exceed hardware limits.

HIERARCHY:
1. Hardware Governor (SOVEREIGN) - sets hard limits based on detected hardware
2. CRA Self-Tuning (SUBORDINATE) - optimizes within governor's envelope
3. User Config (OVERRIDE) - can manually override if explicit

Hardware-locked parameters (CRA CANNOT modify):
- neural.training.batch_size (VRAM-bound)
- evolution.population_size (VRAM/RAM-bound)
- network.max_organisms (RAM-bound)
- ray.num_cpus (CPU-bound)
- neural.brain.hidden_dim (VRAM-bound)
- neural.training.memory_size (RAM-bound)

CRA-tunable parameters (within envelope):
- evolution.mutation_rate
- neural.training.learning_rate
- feedback.knobs.*
- All other non-hardware parameters
"""

import os
import platform
import psutil
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class HardwareProfile(Enum):
    """Hardware capability tiers"""
    BEAST = "beast"        # H100/H200/A100 - 40GB+ VRAM, 16+ cores
    HIGH_RAM_CPU = "high_ram_cpu"  # 500GB+ RAM servers running in CPU mode (Vast.ai, etc)
    WORKSTATION = "workstation"  # RTX 4090/3090 - 24GB VRAM, 8+ cores
    STANDARD = "standard"  # RTX 3080/4080 - 10-16GB VRAM, 6+ cores
    LAPTOP = "laptop"      # RTX 3060/4060 - 6-8GB VRAM, 4+ cores  
    POTATO = "potato"      # Integrated/old GPU - <6GB VRAM, limited
    CPU_ONLY = "cpu_only"  # No CUDA GPU


@dataclass
class HardwareCapabilities:
    """Detected hardware capabilities"""
    profile: HardwareProfile
    gpu_name: str
    vram_gb: float
    ram_gb: float
    cpu_cores: int
    cuda_available: bool
    compute_capability: Optional[Tuple[int, int]] = None


@dataclass
class HardwareEnvelope:
    """Hard limits that CRA cannot exceed"""
    max_batch_size: int
    max_population_size: int
    max_organisms: int
    max_hidden_dim: int
    max_memory_size: int
    max_ray_workers: int
    recommended_device: str
    enable_gpu_batching: bool
    enable_mixed_precision: bool


# Profile-specific envelopes
PROFILE_ENVELOPES: Dict[HardwareProfile, HardwareEnvelope] = {
    HardwareProfile.BEAST: HardwareEnvelope(
        max_batch_size=2048,       # B200 can handle massive batches
        max_population_size=10000, # Huge populations for evolution
        max_organisms=100000,      # Massive swarms (beastmode saturation)
        max_hidden_dim=1024,       # Deep networks
        max_memory_size=2000000,   # 2M experience buffer
        max_ray_workers=64,        # Many parallel workers
        recommended_device="cuda",
        enable_gpu_batching=True,
        enable_mixed_precision=True
    ),
    HardwareProfile.HIGH_RAM_CPU: HardwareEnvelope(
        # Vast.ai-style machines: 500GB-4TB RAM, weak/small GPU, running CPU mode
        # These are RAM monsters - let them use it!
        max_batch_size=512,         # CPU can handle large batches
        max_population_size=100000, # RAM is the limit, not VRAM
        max_organisms=200000,       # 2TB RAM = 200K organisms easy
        max_hidden_dim=256,         # Moderate network depth
        max_memory_size=5000000,    # 5M experience buffer (RAM is cheap here)
        max_ray_workers=128,        # Max out those CPU cores
        recommended_device="cpu",   # CPU mode - RAM > VRAM
        enable_gpu_batching=False,
        enable_mixed_precision=False
    ),
    HardwareProfile.WORKSTATION: HardwareEnvelope(
        max_batch_size=256,
        max_population_size=500,
        max_organisms=1000,
        max_hidden_dim=256,
        max_memory_size=200000,
        max_ray_workers=16,
        recommended_device="cuda",
        enable_gpu_batching=True,
        enable_mixed_precision=True
    ),
    HardwareProfile.STANDARD: HardwareEnvelope(
        max_batch_size=128,
        max_population_size=200,
        max_organisms=500,
        max_hidden_dim=128,
        max_memory_size=100000,
        max_ray_workers=8,
        recommended_device="cuda",
        enable_gpu_batching=True,
        enable_mixed_precision=True
    ),
    HardwareProfile.LAPTOP: HardwareEnvelope(
        max_batch_size=64,
        max_population_size=100,
        max_organisms=200,
        max_hidden_dim=64,
        max_memory_size=50000,
        max_ray_workers=4,
        recommended_device="cuda",
        enable_gpu_batching=False,
        enable_mixed_precision=True
    ),
    HardwareProfile.POTATO: HardwareEnvelope(
        max_batch_size=32,
        max_population_size=50,
        max_organisms=100,
        max_hidden_dim=64,
        max_memory_size=20000,
        max_ray_workers=2,
        recommended_device="cuda",
        enable_gpu_batching=False,
        enable_mixed_precision=False
    ),
    HardwareProfile.CPU_ONLY: HardwareEnvelope(
        # CPU_ONLY can still have massive RAM - check RAM to set limits
        # These are conservative defaults, apply_to_config will scale up based on actual RAM
        max_batch_size=256,
        max_population_size=100000,
        max_organisms=200000,
        max_hidden_dim=128,
        max_memory_size=2000000,
        max_ray_workers=128,
        recommended_device="cpu",
        enable_gpu_batching=False,
        enable_mixed_precision=False
    )
}

# Parameters that are HARDWARE-LOCKED (CRA cannot modify)
HARDWARE_LOCKED_PARAMS = frozenset([
    "neural.training.batch_size",
    "neural.brain.hidden_dim",
    "neural.training.memory_size",
    "evolution.population_size",
    "network.max_organisms",
    "network.max_connections",
    "ray.num_cpus",
    "ray.num_gpus",
    "rendering.mode",  # headless on servers
])


class HardwareGovernor:
    """
    Sovereign hardware profile manager.
    
    Detects hardware capabilities and enforces limits that CRA cannot exceed.
    """
    
    def __init__(self, force_profile: Optional[str] = None):
        """
        Initialize hardware governor.
        
        Args:
            force_profile: Override auto-detection with specific profile
                          ("beast", "workstation", "standard", "laptop", "potato", "cpu_only")
        """
        self.capabilities = self._detect_hardware()
        
        if force_profile:
            try:
                self.capabilities.profile = HardwareProfile(force_profile.lower())
                logger.info(f"[HARDWARE_GOV] Forced profile: {self.capabilities.profile.value}")
            except ValueError:
                logger.warning(f"[HARDWARE_GOV] Unknown profile '{force_profile}', using auto-detected")
        
        self.envelope = PROFILE_ENVELOPES[self.capabilities.profile]
        self._log_detection()
    
    def _detect_hardware(self) -> HardwareCapabilities:
        """Auto-detect hardware capabilities"""
        # CPU and RAM
        cpu_cores = psutil.cpu_count(logical=False) or psutil.cpu_count() or 4
        ram_gb = psutil.virtual_memory().total / (1024**3)
        
        # GPU detection
        cuda_available = False
        gpu_name = "None"
        vram_gb = 0.0
        compute_capability = None
        
        try:
            import torch
            cuda_available = torch.cuda.is_available()
            
            if cuda_available:
                gpu_name = torch.cuda.get_device_name(0)
                vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                cc = torch.cuda.get_device_properties(0)
                compute_capability = (cc.major, cc.minor)
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"[HARDWARE_GOV] GPU detection error: {e}")
        
        # Determine profile based on hardware
        profile = self._classify_hardware(vram_gb, ram_gb, cpu_cores, cuda_available, gpu_name)
        
        return HardwareCapabilities(
            profile=profile,
            gpu_name=gpu_name,
            vram_gb=vram_gb,
            ram_gb=ram_gb,
            cpu_cores=cpu_cores,
            cuda_available=cuda_available,
            compute_capability=compute_capability
        )
    
    def _classify_hardware(self, vram_gb: float, ram_gb: float, cpu_cores: int, 
                          cuda_available: bool, gpu_name: str) -> HardwareProfile:
        """Classify hardware into a profile tier"""
        if not cuda_available:
            # No GPU - but check if it's a high-RAM server
            if ram_gb >= 500:
                return HardwareProfile.HIGH_RAM_CPU
            return HardwareProfile.CPU_ONLY
        
        gpu_lower = gpu_name.lower()
        
        # HIGH_RAM_CPU: Massive RAM (500GB+) with small GPU - these are Vast.ai-style servers
        # where RAM is the real resource, not VRAM. Treat them as CPU workloads.
        if ram_gb >= 500 and vram_gb < 24:
            return HardwareProfile.HIGH_RAM_CPU
        
        # Beast tier: B200, B100, H100, H200, A100, or 40GB+ VRAM
        if any(x in gpu_lower for x in ['b200', 'b100', 'h100', 'h200', 'a100', 'a6000', 'gh200']) or vram_gb >= 40:
            return HardwareProfile.BEAST
        
        # Workstation tier: 4090, 3090, or 20GB+ VRAM
        if any(x in gpu_lower for x in ['4090', '3090', 'a5000', 'rtx 6000']) or vram_gb >= 20:
            return HardwareProfile.WORKSTATION
        
        # Standard tier: 3080, 4080, or 10GB+ VRAM
        if any(x in gpu_lower for x in ['4080', '3080', '3070 ti', 'a4000']) or vram_gb >= 10:
            return HardwareProfile.STANDARD
        
        # Laptop tier: 3060, 4060, or 6GB+ VRAM
        if any(x in gpu_lower for x in ['4060', '4070', '3060', '3070', '2080', '1660']) or vram_gb >= 6:
            return HardwareProfile.LAPTOP
        
        # Potato tier: everything else with CUDA
        return HardwareProfile.POTATO
    
    def _log_detection(self):
        """Log detected hardware info"""
        cap = self.capabilities
        env = self.envelope
        
        logger.info(f"[HARDWARE_GOV] ═══════════════════════════════════════════")
        logger.info(f"[HARDWARE_GOV] Hardware Detection Complete")
        logger.info(f"[HARDWARE_GOV] ───────────────────────────────────────────")
        logger.info(f"[HARDWARE_GOV] Profile: {cap.profile.value.upper()}")
        logger.info(f"[HARDWARE_GOV] GPU: {cap.gpu_name} ({cap.vram_gb:.1f} GB VRAM)")
        logger.info(f"[HARDWARE_GOV] RAM: {cap.ram_gb:.1f} GB")
        logger.info(f"[HARDWARE_GOV] CPU: {cap.cpu_cores} cores")
        logger.info(f"[HARDWARE_GOV] CUDA: {'Available' if cap.cuda_available else 'Not Available'}")
        logger.info(f"[HARDWARE_GOV] ───────────────────────────────────────────")
        logger.info(f"[HARDWARE_GOV] Envelope Limits:")
        logger.info(f"[HARDWARE_GOV]   max_batch_size: {env.max_batch_size}")
        logger.info(f"[HARDWARE_GOV]   max_population: {env.max_population_size}")
        logger.info(f"[HARDWARE_GOV]   max_organisms: {env.max_organisms}")
        logger.info(f"[HARDWARE_GOV]   max_hidden_dim: {env.max_hidden_dim}")
        logger.info(f"[HARDWARE_GOV]   max_ray_workers: {env.max_ray_workers}")
        logger.info(f"[HARDWARE_GOV]   gpu_batching: {env.enable_gpu_batching}")
        logger.info(f"[HARDWARE_GOV] ═══════════════════════════════════════════")
    
    def apply_to_config(self, config: Dict[str, Any], scale_up: bool = False) -> Dict[str, Any]:
        """
        Apply hardware envelope to config - CLAMP ONLY, no auto-scaling.
        
        Your config values are used as-is. Only clamps down if you exceed
        hardware limits.
        
        This is called AFTER loading config but BEFORE CRA gets access.
        
        Args:
            config: The configuration dictionary
            scale_up: Ignored (kept for API compatibility). Scaling removed by design.
        """
        env = self.envelope
        
        # Deep copy to avoid mutation
        import copy
        config = copy.deepcopy(config)
        
        # CLAMPING DISABLED - user's config is law
        # If you want safety rails back, uncomment the clamp_if_exceeded calls below
        
        # def clamp_if_exceeded(d: dict, path: str, max_val: Any):
        #     """Clamp config value if it exceeds hardware max"""
        #     keys = path.split('.')
        #     current = d
        #     for key in keys[:-1]:
        #         if key not in current:
        #             return
        #         current = current[key]
        #     
        #     final_key = keys[-1]
        #     original = current.get(final_key)
        #     
        #     if original is not None and isinstance(original, (int, float)) and original > max_val:
        #         logger.warning(f"[HARDWARE_GOV] Clamping {path}: {original} -> {max_val}")
        #         current[final_key] = int(max_val) if isinstance(original, int) else max_val
        
        # Clamping disabled - your config, your rules
        # clamp_if_exceeded(config, 'neural.training.batch_size', env.max_batch_size)
        # clamp_if_exceeded(config, 'neural.brain.hidden_dim', env.max_hidden_dim)
        # clamp_if_exceeded(config, 'neural.training.memory_size', env.max_memory_size)
        # clamp_if_exceeded(config, 'evolution.population_size', env.max_population_size)
        # clamp_if_exceeded(config, 'network.max_organisms', env.max_organisms)
        
        # Set Ray workers based on CPU cores (but respect envelope max)
        ray_workers = min(self.capabilities.cpu_cores, env.max_ray_workers)
        if 'ray' not in config:
            config['ray'] = {}
        config['ray']['num_cpus'] = ray_workers
        
        # Set device
        config['neural']['device'] = env.recommended_device
        
        # Enable/disable GPU optimizations
        if 'optimization' not in config.get('neural', {}):
            config['neural']['optimization'] = {}
        config['neural']['optimization']['gpu_batching'] = env.enable_gpu_batching
        config['neural']['optimization']['mixed_precision'] = env.enable_mixed_precision
        
        # Store governor metadata in config for CRA awareness
        config['hardware_governor'] = {
            'profile': self.capabilities.profile.value,
            'gpu_name': self.capabilities.gpu_name,
            'vram_gb': self.capabilities.vram_gb,
            'ram_gb': self.capabilities.ram_gb,
            'cpu_cores': self.capabilities.cpu_cores,
            'locked_params': list(HARDWARE_LOCKED_PARAMS),
            'envelope': {
                'max_batch_size': env.max_batch_size,
                'max_population_size': env.max_population_size,
                'max_organisms': env.max_organisms,
                'max_hidden_dim': env.max_hidden_dim,
                'max_memory_size': env.max_memory_size,
                'max_ray_workers': env.max_ray_workers,
            }
        }
        
        return config
    
    def validate_cra_request(self, param_path: str, proposed_value: Any) -> Tuple[bool, Any, str]:
        """
        Validate a CRA self-tuning request against hardware limits.
        
        Returns:
            (allowed, clamped_value, reason)
        """
        env = self.envelope
        
        # Check if parameter is hardware-locked
        if param_path in HARDWARE_LOCKED_PARAMS:
            return False, None, f"Parameter '{param_path}' is hardware-locked by Governor"
        
        # For non-locked params, allow but log
        return True, proposed_value, "Allowed"
    
    def get_cra_safe_params(self, current_safe_params: list) -> list:
        """
        Filter CRA's safe_parameters list to remove hardware-locked params.
        
        Call this when CRA initializes to ensure it doesn't try to tune locked params.
        """
        return [p for p in current_safe_params if p not in HARDWARE_LOCKED_PARAMS]


# Global singleton
_governor: Optional[HardwareGovernor] = None


def get_hardware_governor(force_profile: Optional[str] = None) -> HardwareGovernor:
    """Get or create the hardware governor singleton"""
    global _governor
    if _governor is None:
        _governor = HardwareGovernor(force_profile)
    return _governor


def apply_hardware_envelope(config: Dict[str, Any], force_profile: Optional[str] = None, 
                           scale_up: bool = True) -> Dict[str, Any]:
    """
    Convenience function to apply hardware envelope to config.
    
    Call this immediately after loading config.json:
    
        config = json.load(open('config.json'))
        config = apply_hardware_envelope(config)  # Hardware governor applied with scaling
        # Now safe to pass to CRA
    
    Args:
        config: Your config dictionary
        force_profile: Override auto-detection ("beast", "workstation", etc.)
        scale_up: If True, proportionally scale config values UP based on hardware tier.
                  A LAPTOP config scales ~32x on BEAST hardware.
                  If False, only clamps DOWN values that exceed hardware limits.
    """
    governor = get_hardware_governor(force_profile)
    return governor.apply_to_config(config, scale_up=scale_up)


def is_hardware_locked(param_path: str) -> bool:
    """Check if a parameter is hardware-locked"""
    return param_path in HARDWARE_LOCKED_PARAMS
