"""Tests for GGUF format validation and verification."""

import os
import tempfile
import pytest
from unittest.mock import patch, mock_open
from pathlib import Path

from server.src.llmlaunchpad.models import validate_gguf_format, extract_gguf_metadata, LocalModel


def test_validate_gguf_format_valid():
    """Test validation of a valid GGUF file."""
    # Create a mock GGUF file with correct magic number and version
    gguf_data = bytearray()
    gguf_data.extend(b'GGUF')  # Magic number
    gguf_data.extend((1).to_bytes(4, 'little'))  # Version 1
    gguf_data.extend((0).to_bytes(4, 'little'))  # Tensor count
    gguf_data.extend((0).to_bytes(4, 'little'))  # KV count
    
    with tempfile.NamedTemporaryFile(suffix='.gguf', delete=False) as f:
        f.write(gguf_data)
        temp_path = f.name
    
    try:
        result = validate_gguf_format(temp_path)
        assert result is True
    finally:
        os.unlink(temp_path)


def test_validate_gguf_format_invalid_magic():
    """Test validation fails with incorrect magic number."""
    # Create a mock file with wrong magic number
    gguf_data = bytearray()
    gguf_data.extend(b'WRONG')  # Wrong magic number
    gguf_data.extend((1).to_bytes(4, 'little'))  # Version 1
    gguf_data.extend((0).to_bytes(4, 'little'))  # Tensor count
    gguf_data.extend((0).to_bytes(4, 'little'))  # KV count
    
    with tempfile.NamedTemporaryFile(suffix='.gguf', delete=False) as f:
        f.write(gguf_data)
        temp_path = f.name
    
    try:
        result = validate_gguf_format(temp_path)
        assert result is False
    finally:
        os.unlink(temp_path)


def test_validate_gguf_format_invalid_version():
    """Test validation fails with unsupported version."""
    # Create a mock file with unsupported version
    gguf_data = bytearray()
    gguf_data.extend(b'GGUF')  # Magic number
    gguf_data.extend((99).to_bytes(4, 'little'))  # Unsupported version 99
    gguf_data.extend((0).to_bytes(4, 'little'))  # Tensor count
    gguf_data.extend((0).to_bytes(4, 'little'))  # KV count
    
    with tempfile.NamedTemporaryFile(suffix='.gguf', delete=False) as f:
        f.write(gguf_data)
        temp_path = f.name
    
    try:
        result = validate_gguf_format(temp_path)
        assert result is False
    finally:
        os.unlink(temp_path)


def test_validate_gguf_format_too_short():
    """Test validation fails with file too short."""
    # Create a mock file that's too short
    gguf_data = bytearray(b'GG')  # Only 2 bytes
    
    with tempfile.NamedTemporaryFile(suffix='.gguf', delete=False) as f:
        f.write(gguf_data)
        temp_path = f.name
    
    try:
        result = validate_gguf_format(temp_path)
        assert result is False
    finally:
        os.unlink(temp_path)


def test_extract_gguf_metadata_valid():
    """Test extracting metadata from a valid GGUF file."""
    # Create a mock GGUF file with some metadata
    gguf_data = bytearray()
    gguf_data.extend(b'GGUF')  # Magic number
    gguf_data.extend((1).to_bytes(4, 'little'))  # Version 1
    gguf_data.extend((0).to_bytes(4, 'little'))  # Tensor count
    gguf_data.extend((1).to_bytes(4, 'little'))  # KV count (one key-value pair)
    
    # Add a key-value pair: key="test_key", value="test_value" (string)
    key_bytes = b'test_key'
    gguf_data.extend(len(key_bytes).to_bytes(8, 'little'))  # Key length
    gguf_data.extend(key_bytes)  # Key
    gguf_data.extend((8).to_bytes(4, 'little'))  # Value type: STRING
    value_bytes = b'test_value'
    gguf_data.extend(len(value_bytes).to_bytes(8, 'little'))  # Value length
    gguf_data.extend(value_bytes)  # Value
    
    with tempfile.NamedTemporaryFile(suffix='.gguf', delete=False) as f:
        f.write(gguf_data)
        temp_path = f.name
    
    try:
        metadata = extract_gguf_metadata(temp_path)
        assert metadata is not None
        assert metadata['gguf_version'] == 1
        assert metadata['test_key'] == 'test_value'
    finally:
        os.unlink(temp_path)


def test_extract_gguf_metadata_invalid_magic():
    """Test extracting metadata fails with incorrect magic number."""
    # Create a mock file with wrong magic number
    gguf_data = bytearray()
    gguf_data.extend(b'WRONG')  # Wrong magic number
    gguf_data.extend((1).to_bytes(4, 'little'))  # Version 1
    gguf_data.extend((0).to_bytes(4, 'little'))  # Tensor count
    gguf_data.extend((0).to_bytes(4, 'little'))  # KV count
    
    with tempfile.NamedTemporaryFile(suffix='.gguf', delete=False) as f:
        f.write(gguf_data)
        temp_path = f.name
    
    try:
        metadata = extract_gguf_metadata(temp_path)
        assert metadata is None
    finally:
        os.unlink(temp_path)


def test_extract_gguf_metadata_too_short():
    """Test extracting metadata fails with file too short."""
    # Create a mock file that's too short
    gguf_data = bytearray(b'GG')  # Only 2 bytes
    
    with tempfile.NamedTemporaryFile(suffix='.gguf', delete=False) as f:
        f.write(gguf_data)
        temp_path = f.name
    
    try:
        metadata = extract_gguf_metadata(temp_path)
        assert metadata is None
    finally:
        os.unlink(temp_path)


def test_integration_with_local_model():
    """Test that GGUF validation integrates with LocalModel scanning."""
    # This test verifies that our validation functions work with the model scanning
    
    # Create a valid GGUF file
    gguf_data = bytearray()
    gguf_data.extend(b'GGUF')  # Magic number
    gguf_data.extend((1).to_bytes(4, 'little'))  # Version 1
    gguf_data.extend((0).to_bytes(4, 'little'))  # Tensor count
    gguf_data.extend((0).to_bytes(4, 'little'))  # KV count
    
    with tempfile.TemporaryDirectory() as temp_dir:
        model_path = Path(temp_dir) / "test-model.gguf"
        with open(model_path, 'wb') as f:
            f.write(gguf_data)
        
        # Test validation
        assert validate_gguf_format(str(model_path)) is True
        
        # Test metadata extraction
        metadata = extract_gguf_metadata(str(model_path))
        assert metadata is not None
        assert metadata['gguf_version'] == 1
        
        # Test creating a LocalModel (this would normally happen in scan_directory_for_gguf)
        stat = model_path.stat()
        model = LocalModel(
            name=model_path.name,
            path=str(model_path),
            size_bytes=stat.st_size,
            source="test",
            quantization=None,
            family=None
        )
        assert model.path == str(model_path)
        assert model.name == "test-model.gguf"