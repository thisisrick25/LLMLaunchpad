"""Tests for GPU offload calculation functionality."""

import pytest
from unittest.mock import Mock, patch
from server.src.llmlaunchpad.offload import (
    calculate_offload,
    PerformanceMode,
    OffloadRecommendation,
    estimate_layers_from_size,
    estimate_context_memory,
    estimate_model_memory,
    calculate_optimal_layers
)
from server.src.llmlaunchpad.hardware import HardwareInfo, GPUInfo


def test_calculate_offload_returns_zero_layers_when_no_gpu():
    """Test that calculate_offload returns gpu_layers=0 when no GPU detected."""
    # Arrange
    mock_hardware = Mock(spec=HardwareInfo)
    mock_hardware.has_gpu = False
    mock_hardware.total_vram_gb = 0
    mock_hardware.gpus = []
    
    # Act
    result = calculate_offload(
        model_path="dummy/path/to/model.gguf",
        context_size=4096,
        mode="auto",
        hardware_info=mock_hardware
    )
    
    # Assert
    assert isinstance(result, OffloadRecommendation)
    assert result.gpu_layers == 0
    assert result.mode == PerformanceMode.AUTO
    assert "No GPU detected" in result.reason


def test_calculate_offload_respects_cpu_only_mode():
    """Test that calculate_offload respects CPU-only mode setting."""
    # Arrange
    mock_hardware = Mock(spec=HardwareInfo)
    mock_hardware.has_gpu = True
    mock_hardware.total_vram_gb = 8
    mock_hardware.gpus = [Mock(spec=GPUInfo)]
    mock_hardware.gpus[0].memory_free_mb = 8192
    
    # Act
    result = calculate_offload(
        model_path="dummy/path/to/model.gguf",
        context_size=4096,
        mode="cpu-only",
        hardware_info=mock_hardware
    )
    
    # Assert
    assert result.gpu_layers == 0
    assert result.mode == PerformanceMode.CPU_ONLY
    assert "CPU-only mode selected" in result.reason


def test_calculate_offload_respects_cloud_mode():
    """Test that calculate_offload respects Cloud mode setting."""
    # Arrange
    mock_hardware = Mock(spec=HardwareInfo)
    mock_hardware.has_gpu = True
    mock_hardware.total_vram_gb = 8
    mock_hardware.gpus = [Mock(spec=GPUInfo)]
    mock_hardware.gpus[0].memory_free_mb = 8192
    
    # Act
    result = calculate_offload(
        model_path="dummy/path/to/model.gguf",
        context_size=4096,
        mode="cloud",
        hardware_info=mock_hardware
    )
    
    # Assert
    assert result.gpu_layers == 0
    assert result.mode == PerformanceMode.CLOUD
    assert "Cloud mode - local inference disabled" in result.reason


def test_calculate_offload_applies_safety_margins():
    """Test that calculate_offload applies appropriate safety margins for Auto vs GPU-Heavy modes."""
    # Arrange
    mock_hardware = Mock(spec=HardwareInfo)
    mock_hardware.has_gpu = True
    mock_hardware.total_vram_gb = 8
    mock_hardware.gpus = [Mock(spec=GPUInfo)]
    mock_hardware.gpus[0].memory_free_mb = 8192  # 8 GB free
    
    # Act - Auto mode
    auto_result = calculate_offload(
        model_path="dummy/path/to/model.gguf",
        context_size=4096,
        mode="auto",
        hardware_info=mock_hardware
    )
    
    # Act - GPU-Heavy mode
    gpu_heavy_result = calculate_offload(
        model_path="dummy/path/to/model.gguf",
        context_size=4096,
        mode="gpu-heavy",
        hardware_info=mock_hardware
    )
    
    # Assert - GPU-Heavy should allow more layers than Auto (higher safety margin)
    assert gpu_heavy_result.gpu_layers >= auto_result.gpu_layers
    assert auto_result.mode == PerformanceMode.AUTO
    assert gpu_heavy_result.mode == PerformanceMode.GPU_HEAVY


def test_calculate_offload_prevents_oom_by_validating_vram():
    """Test that calculate_offload prevents OOM by validating against total available VRAM."""
    # Arrange
    mock_hardware = Mock(spec=HardwareInfo)
    mock_hardware.has_gpu = True
    mock_hardware.total_vram_gb = 4  # 4 GB total
    mock_hardware.gpus = [Mock(spec=GPUInfo)]
    mock_hardware.gpus[0].memory_free_mb = 4096  # 4 GB free
    
    # Act
    result = calculate_offload(
        model_path="dummy/path/to/model.gguf",
        context_size=4096,
        mode="auto",
        hardware_info=mock_hardware
    )
    
    # Assert - estimated VRAM usage should not exceed available VRAM
    assert result.estimated_vram_mb <= 4096  # 4 GB in MB
    assert result.mode == PerformanceMode.AUTO


def test_estimate_layers_from_size_handles_edge_cases():
    """Test that estimate_layers_from_size handles edge cases."""
    # Test very small model (< 1.5GB)
    assert estimate_layers_from_size(1_000_000_000) == 24  # < 1.5GB
    
    # Test small model (1.5-3.0GB range - 3b model)
    assert estimate_layers_from_size(2_000_000_000) == 26  # 1.5-3.0GB
    
    # Test small model (3.0-5.0GB range - 7b model starts at 3.0)
    assert estimate_layers_from_size(4_000_000_000) == 32  # 3.0-7.0GB
    
    # Test medium model (3.0-7.0GB range - 7b model)
    assert estimate_layers_from_size(5_000_000_000) == 32  # 3.0-7.0GB
    
    # Test large model (7.0-13.0GB range - 13b model)
    assert estimate_layers_from_size(10_000_000_000) == 40  # 6.0-13.0GB
    
    # Test very large model (13.0-35.0GB range - 34b model)
    assert estimate_layers_from_size(20_000_000_000) == 60  # 15.0-35.0GB
    
    # Test extremely large model (>35.0GB range - 70b model)
    assert estimate_layers_from_size(50_000_000_000) == 80  # 35.0-75.0GB


def test_estimate_context_memory_calculation():
    """Test that estimate_context_memory calculates KV cache correctly."""
    # Arrange
    context_size = 4096
    model_layers = 32
    hidden_dim = 4096
    
    # Act
    result = estimate_context_memory(context_size, model_layers, hidden_dim)
    
    # Assert
    # KV cache = 2 * layers * context * hidden_dim * 2 bytes (FP16)
    # With 20% overhead: result = 2 * 32 * 4096 * 4096 * 2 * 1.2
    expected = int(2 * 32 * 4096 * 4096 * 2 * 1.2)
    assert result == expected


def test_calculate_optimal_layers_respects_layer_cap():
    """Test that calculate_optimal_layers caps at actual layer count."""
    # Arrange
    from server.src.llmlaunchpad.offload import ModelMemoryEstimate
    
    model_estimate = ModelMemoryEstimate(
        total_size_bytes=10_000_000_000,  # 10GB
        layer_count=40,
        bytes_per_layer=250_000_000,  # 250MB per layer
        context_memory_bytes=1_000_000_000,  # 1GB
        kv_cache_bytes=1_000_000_000  # 1GB
    )
    
    # Act
    gpu_layers, estimated_vram = calculate_optimal_layers(
        available_vram_mb=12_000,  # 12GB available
        model_estimate=model_estimate,
        safety_margin=0.9
    )
    
    # Assert - should not exceed actual layer count
    assert gpu_layers <= model_estimate.layer_count
    assert gpu_layers == 40  # Should be capped at layer count