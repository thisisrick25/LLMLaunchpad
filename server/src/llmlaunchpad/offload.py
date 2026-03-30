"""GPU offload calculation for LLMLaunchpad.

This module calculates the optimal number of GPU layers based on:
- Available VRAM
- Model size and architecture
- Performance mode setting
"""

import math
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple
from enum import Enum

from .hardware import get_hardware_info, HardwareInfo
from .config import get_config

logger = logging.getLogger(__name__)


class PerformanceMode(Enum):
    """Performance modes for GPU offloading."""
    AUTO = "auto"
    GPU_HEAVY = "gpu-heavy"
    CPU_ONLY = "cpu-only"
    CLOUD = "cloud"


@dataclass
class ModelMemoryEstimate:
    """Memory estimates for a model."""
    total_size_bytes: int
    layer_count: int
    bytes_per_layer: int
    context_memory_bytes: int
    kv_cache_bytes: int
    
    @property
    def total_size_gb(self) -> float:
        return self.total_size_bytes / (1024 ** 3)
    
    @property
    def bytes_per_layer_mb(self) -> float:
        return self.bytes_per_layer / (1024 ** 2)


@dataclass
class OffloadRecommendation:
    """Recommended offload settings."""
    gpu_layers: int
    total_layers: int
    estimated_vram_mb: int
    mode: PerformanceMode
    reason: str
    
    def to_dict(self) -> dict:
        return {
            "gpu_layers": self.gpu_layers,
            "total_layers": self.total_layers,
            "estimated_vram_mb": self.estimated_vram_mb,
            "mode": self.mode.value,
            "reason": self.reason,
        }


# Common model architectures and their layer counts
# Format: (min_size_gb, max_size_gb, typical_layers)
MODEL_LAYER_ESTIMATES = {
    "3b": (1.5, 3.0, 26),
    "7b": (3.0, 7.0, 32),
    "8b": (3.5, 8.0, 32),
    "13b": (6.0, 13.0, 40),
    "34b": (15.0, 35.0, 60),
    "70b": (35.0, 75.0, 80),
}


def estimate_layers_from_size(model_size_bytes: int) -> int:
    """
    Estimate the number of layers based on model file size.
    
    This is a heuristic based on common GGUF model sizes.
    """
    size_gb = model_size_bytes / (1024 ** 3)
    
    # Try to match known size ranges
    for name, (min_size, max_size, layers) in MODEL_LAYER_ESTIMATES.items():
        if min_size <= size_gb <= max_size:
            return layers
    
    # Fallback: estimate based on size
    # Rough heuristic: ~0.5GB per layer for Q4, ~1GB for larger quants
    if size_gb < 2:
        return 24
    elif size_gb < 5:
        return 32
    elif size_gb < 10:
        return 40
    elif size_gb < 20:
        return 48
    elif size_gb < 40:
        return 60
    else:
        return 80


def estimate_hidden_dim_from_size(model_size_bytes: int) -> int:
    """
    Estimate hidden dimension based on model size.
    This is a heuristic based on common model architectures.
    """
    size_gb = model_size_bytes / (1024 ** 3)
    
    # Heuristic for hidden dimension based on model size
    if size_gb < 1:      # < 1B parameters
        return 1024
    elif size_gb < 2:    # 1-2B parameters
        return 2048
    elif size_gb < 4:    # 2-4B parameters
        return 2560
    elif size_gb < 8:    # 4-8B parameters
        return 3072
    elif size_gb < 15:   # 8-15B parameters
        return 4096
    elif size_gb < 30:   # 15-30B parameters
        return 5120
    else:                # 30B+ parameters
        return 6144


def estimate_context_memory(context_size: int, model_layers: int, model_size_bytes: int = 0, hidden_dim: Optional[int] = None) -> int:
    """
    Estimate memory needed for KV cache.
    
    KV cache formula (approximate):
    2 * layers * context * hidden_dim * bytes_per_element
    
    For Q4 models, KV cache is typically in FP16.
    """
    # Backward compatibility: if model_size_bytes looks like a hidden_dim (reasonable range)
    # and hidden_dim is not explicitly provided, treat model_size_bytes as hidden_dim
    if hidden_dim is None and model_size_bytes > 0 and model_size_bytes < 10000:
        # Assume model_size_bytes is actually hidden_dim for backward compatibility
        hidden_dim = model_size_bytes
        model_size_bytes = 0  # Reset to trigger estimation
    
    # If hidden_dim is not provided, estimate it from model size
    if hidden_dim is None:
        if model_size_bytes == 0:
            # Fallback to a reasonable default if no model size provided
            hidden_dim = 4096
        else:
            hidden_dim = estimate_hidden_dim_from_size(model_size_bytes)
    
    # FP16 = 2 bytes per element
    bytes_per_element = 2
    
    # KV cache size
    kv_cache = 2 * model_layers * context_size * hidden_dim * bytes_per_element
    
    # Add ~20% overhead for other buffers
    return int(kv_cache * 1.2)


def get_model_size(model_path: str) -> int:
    """Get the size of a model file in bytes."""
    path = Path(model_path)
    if path.exists():
        return path.stat().st_size
    return 0


def estimate_model_memory(
    model_path: str,
    context_size: int = 4096,
) -> ModelMemoryEstimate:
    """
    Estimate memory requirements for a model.
    """
    model_size = get_model_size(model_path)
    layer_count = estimate_layers_from_size(model_size)
    
    # Bytes per layer (model weights distributed across layers)
    # This is approximate - actual distribution varies by architecture
    bytes_per_layer = model_size // layer_count if layer_count > 0 else model_size
    
    # Context/KV cache memory
    context_memory = estimate_context_memory(context_size, layer_count, model_size, model_size)
    
    return ModelMemoryEstimate(
        total_size_bytes=model_size,
        layer_count=layer_count,
        bytes_per_layer=bytes_per_layer,
        context_memory_bytes=context_memory,
        kv_cache_bytes=context_memory,
    )


def calculate_optimal_layers(
    available_vram_mb: int,
    model_estimate: ModelMemoryEstimate,
    safety_margin: float = 0.9,  # Use only 90% of VRAM
) -> Tuple[int, int]:
    """
    Calculate optimal number of GPU layers.
    
    Returns (gpu_layers, estimated_vram_usage_mb)
    """
    if available_vram_mb <= 0:
        logger.debug("No VRAM available, returning 0 GPU layers")
        return 0, 0
    
    # Reserve some VRAM for context/KV cache and overhead
    context_mb = model_estimate.context_memory_bytes / (1024 ** 2)
    usable_vram_mb = (available_vram_mb * safety_margin) - context_mb
    
    if usable_vram_mb <= 0:
        logger.debug(f"Insufficient VRAM after context reservation: {usable_vram_mb:.2f} MB usable")
        return 0, 0
    
    # Calculate how many layers fit
    bytes_per_layer_mb = model_estimate.bytes_per_layer / (1024 ** 2)
    
    if bytes_per_layer_mb <= 0:
        logger.debug("Invalid bytes per layer calculation")
        return 0, 0
    
    max_layers = int(usable_vram_mb / bytes_per_layer_mb)
    
    # Cap at actual layer count
    gpu_layers = min(max_layers, model_estimate.layer_count)
    
    # Additional validation: ensure we don't exceed physical VRAM limits
    estimated_vram = int((gpu_layers * bytes_per_layer_mb) + context_mb)
    if estimated_vram > available_vram_mb:
        logger.warning(f"Estimated VRAM usage ({estimated_vram} MB) exceeds available ({available_vram_mb} MB), reducing layers")
        # Recalculate with reduced layers to fit within available VRAM
        excess_mb = estimated_vram - available_vram_mb
        layers_to_remove = int(excess_mb / bytes_per_layer_mb) + 1  # Add 1 for safety
        gpu_layers = max(0, gpu_layers - layers_to_remove)
        estimated_vram = int((gpu_layers * bytes_per_layer_mb) + context_mb)
    
    logger.debug(f"Calculated optimal layers: {gpu_layers}/{model_estimate.layer_count}, estimated VRAM: {estimated_vram} MB")
    
    return gpu_layers, estimated_vram


def calculate_offload(
    model_path: str,
    context_size: int = 4096,
    mode: Optional[str] = None,
    hardware_info: Optional[HardwareInfo] = None,
) -> OffloadRecommendation:
    """
    Calculate optimal GPU offload settings for a model.
    
    Args:
        model_path: Path to the model file
        context_size: Context window size
        mode: Performance mode (auto, gpu-heavy, cpu-only, cloud)
        hardware_info: Pre-fetched hardware info (optional)
    
    Returns:
        OffloadRecommendation with optimal settings
    """
    # Get hardware info
    if hardware_info is None:
        hardware_info = get_hardware_info()
    
    # Get mode from config if not specified
    if mode is None:
        config = get_config()
        mode = config.mode
    
    # Parse mode
    try:
        perf_mode = PerformanceMode(mode.lower())
    except ValueError:
        perf_mode = PerformanceMode.AUTO
    
    # Get model memory estimates
    model_estimate = estimate_model_memory(model_path, context_size)
    
    # Handle different modes
    if perf_mode == PerformanceMode.CPU_ONLY:
        logger.debug("CPU-only mode selected")
        return OffloadRecommendation(
            gpu_layers=0,
            total_layers=model_estimate.layer_count,
            estimated_vram_mb=0,
            mode=perf_mode,
            reason="CPU-only mode selected",
        )
    
    if perf_mode == PerformanceMode.CLOUD:
        logger.debug("Cloud mode selected - local inference disabled")
        return OffloadRecommendation(
            gpu_layers=0,
            total_layers=model_estimate.layer_count,
            estimated_vram_mb=0,
            mode=perf_mode,
            reason="Cloud mode - local inference disabled",
        )
    
    # Check if we have a GPU
    if not hardware_info.has_gpu:
        logger.debug("No GPU detected")
        return OffloadRecommendation(
            gpu_layers=0,
            total_layers=model_estimate.layer_count,
            estimated_vram_mb=0,
            mode=perf_mode,
            reason="No GPU detected",
        )
    
    # Get available VRAM (use first GPU or total)
    total_vram_mb = int(hardware_info.total_vram_gb * 1024)
    free_vram_mb = sum(gpu.memory_free_mb for gpu in hardware_info.gpus)
    
    if perf_mode == PerformanceMode.GPU_HEAVY:
        # Use total VRAM with safety margin for GPU-Heavy mode
        available_vram = total_vram_mb
        safety_margin = 0.90  # Allow 90% utilization for GPU-Heavy mode
        logger.debug(f"GPU-Heavy mode: using total VRAM ({total_vram_mb} MB) with safety margin {safety_margin}")
    else:  # AUTO
        # Use free VRAM with more conservative safety margin for Auto mode
        available_vram = free_vram_mb
        safety_margin = 0.75  # More conservative (75%) for Auto mode to prevent OOM
        logger.debug(f"Auto mode: using free VRAM ({free_vram_mb} MB) with safety margin {safety_margin}")
    
    # Validate available VRAM
    if available_vram <= 0:
        logger.warning("No VRAM available for GPU offload")
        return OffloadRecommendation(
            gpu_layers=0,
            total_layers=model_estimate.layer_count,
            estimated_vram_mb=0,
            mode=perf_mode,
            reason="No VRAM available for GPU offload",
        )
    
    # Calculate optimal layers with improved validation
    gpu_layers, estimated_vram = calculate_optimal_layers(
        available_vram,
        model_estimate,
        safety_margin,
    )
    
    # Additional validation: ensure calculated layers don't exceed model's actual layers
    if gpu_layers > model_estimate.layer_count:
        logger.warning(f"Calculated GPU layers ({gpu_layers}) exceeds model layer count ({model_estimate.layer_count}), capping")
        gpu_layers = model_estimate.layer_count
        # Recalculate estimated VRAM with capped layers
        bytes_per_layer_mb = model_estimate.bytes_per_layer / (1024 ** 2)
        context_mb = model_estimate.context_memory_bytes / (1024 ** 2)
        estimated_vram = int((gpu_layers * bytes_per_layer_mb) + context_mb)
    
    # Final validation: ensure we don't exceed physical VRAM limits
    if estimated_vram > available_vram:
        logger.warning(f"Estimated VRAM usage ({estimated_vram} MB) exceeds available ({available_vram} MB), reducing layers")
        # Recalculate with reduced layers to fit within available VRAM
        excess_mb = estimated_vram - available_vram
        bytes_per_layer_mb = model_estimate.bytes_per_layer / (1024 ** 2)
        if bytes_per_layer_mb > 0:
            layers_to_remove = int(excess_mb / bytes_per_layer_mb) + 1  # Add 1 for safety
            gpu_layers = max(0, gpu_layers - layers_to_remove)
            # Recalculate estimated VRAM
            context_mb = model_estimate.context_memory_bytes / (1024 ** 2)
            estimated_vram = int((gpu_layers * bytes_per_layer_mb) + context_mb)
    
    # Generate more informative reason
    if gpu_layers >= model_estimate.layer_count:
        reason = f"Full GPU offload ({gpu_layers}/{model_estimate.layer_count} layers)"
        logger.debug(reason)
    elif gpu_layers > 0:
        pct = int((gpu_layers / model_estimate.layer_count) * 100)
        vram_percent = int((estimated_vram / available_vram) * 100) if available_vram > 0 else 0
        reason = f"Partial GPU offload ({gpu_layers}/{model_estimate.layer_count} layers, {pct}%) using {estimated_vram} MB VRAM ({vram_percent}% of available)"
        logger.debug(reason)
    else:
        reason = f"Insufficient VRAM for GPU offload (need ~{int(model_estimate.bytes_per_layer / (1024**2))} MB per layer, have {available_vram} MB)"
        logger.debug(reason)
    
    return OffloadRecommendation(
        gpu_layers=gpu_layers,
        total_layers=model_estimate.layer_count,
        estimated_vram_mb=estimated_vram,
        mode=perf_mode,
        reason=reason,
    )


def get_offload_preview(
    model_path: str,
    context_size: int = 4096,
) -> dict:
    """
    Get a preview of offload settings for all modes.
    
    Returns a dict with recommendations for each mode.
    """
    hardware_info = get_hardware_info()
    
    previews = {}
    for mode in [PerformanceMode.AUTO, PerformanceMode.GPU_HEAVY, PerformanceMode.CPU_ONLY]:
        recommendation = calculate_offload(
            model_path=model_path,
            context_size=context_size,
            mode=mode.value,
            hardware_info=hardware_info,
        )
        previews[mode.value] = recommendation.to_dict()
    
    return {
        "model_path": model_path,
        "model_size_gb": round(get_model_size(model_path) / (1024 ** 3), 2),
        "context_size": context_size,
        "recommendations": previews,
        "hardware": {
            "has_gpu": hardware_info.has_gpu,
            "total_vram_gb": round(hardware_info.total_vram_gb, 2),
            "gpus": [
                {
                    "name": gpu.name,
                    "total_gb": round(gpu.memory_total_gb, 2),
                    "free_gb": round(gpu.memory_free_gb, 2),
                }
                for gpu in hardware_info.gpus
            ],
        },
    }
