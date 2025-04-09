#!/usr/bin/python3
"""
Tests for the UBootEnv class and utility functions.
"""

import os
import io
import tempfile
import binascii
import struct
import pytest
from py_uboot_env.uboot_env import UBootEnv, load_env, dump_env, format_env


@pytest.fixture
def sample_env_dict():
    """Return a sample environment dictionary."""
    return {
        "bootcmd": "run distro_bootcmd",
        "bootdelay": "2",
        "baudrate": "115200",
        "board_name": "cubix-mx",
        "bootargs": "console=ttyS0,115200n8 root=/dev/mmcblk0p2 rootwait",
        "loadaddr": "0x42000000",
    }


@pytest.fixture
def sample_env(sample_env_dict):
    """Return a sample UBootEnv instance."""
    return UBootEnv(
        content=sample_env_dict.copy(),
        env_size=0x2000,  # 8KB
        header_size=4
    )


@pytest.fixture
def env_file_path():
    """Create a temporary file path for env file."""
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


def create_test_env_file(path, content, env_size=0x2000, header_size=4):
    """Create a test environment file."""
    # Create binary content
    s = b'\x00' * header_size
    s += b''.join(
        f"{key}={value}".encode('ascii') + b'\x00'
        for key, value in sorted(content.items())
    )
    s += b'\x00'  # env terminator
    s += b'\xff' * (env_size - len(s))  # padding
    
    # Calculate and set CRC
    s = bytearray(s)
    s[:4] = struct.pack('<L', binascii.crc32(s[header_size:]))
    
    # Write to file
    with open(path, 'wb') as f:
        f.write(s)
    
    return path


class TestUBootEnv:
    """Tests for the UBootEnv class."""

    def test_get(self, sample_env):
        """Test the get method."""
        assert sample_env.get("bootcmd") == "run distro_bootcmd"
        assert sample_env.get("baudrate") == "115200"
        assert sample_env.get("nonexistent") is None
        assert sample_env.get("nonexistent", "default") == "default"

    def test_set(self, sample_env):
        """Test the set method."""
        sample_env.set("new_var", "new_value")
        assert sample_env.get("new_var") == "new_value"
        
        # Update existing
        sample_env.set("bootcmd", "updated_value")
        assert sample_env.get("bootcmd") == "updated_value"

    def test_delete(self, sample_env):
        """Test the delete method."""
        # Delete existing
        sample_env.delete("bootcmd")
        assert sample_env.get("bootcmd") is None
        
        # Delete non-existent (should not raise)
        sample_env.delete("nonexistent")

    def test_save(self, sample_env, env_file_path):
        """Test the save method."""
        sample_env.save(env_file_path)
        
        # Check file exists
        assert os.path.exists(env_file_path)
        
        # Load it back and verify contents
        loaded_env = load_env(env_file_path)
        assert loaded_env.content == sample_env.content
        assert loaded_env.env_size == sample_env.env_size
        assert loaded_env.header_size == sample_env.header_size


class TestLoadEnv:
    """Tests for the load_env function."""

    def test_load_from_path(self, sample_env_dict, env_file_path):
        """Test loading from a file path."""
        create_test_env_file(env_file_path, sample_env_dict)
        
        env = load_env(env_file_path)
        assert env.content == sample_env_dict
        assert env.env_size == 0x2000
        assert env.header_size == 4

    def test_load_from_file_handle(self, sample_env_dict, env_file_path):
        """Test loading from a file handle."""
        create_test_env_file(env_file_path, sample_env_dict)
        
        with open(env_file_path, 'rb') as f:
            env = load_env(f)
            assert env.content == sample_env_dict
            assert env.env_size == 0x2000
            assert env.header_size == 4

    def test_load_with_5_byte_header(self, sample_env_dict, env_file_path):
        """Test loading with a 5-byte header."""
        create_test_env_file(env_file_path, sample_env_dict, header_size=5)
        
        env = load_env(env_file_path)
        assert env.content == sample_env_dict
        assert env.env_size == 0x2000
        assert env.header_size == 5

    def test_invalid_env_size(self, sample_env_dict):
        """Test handling invalid environment size."""
        # Create an in-memory file with invalid size
        env_data = io.BytesIO()
        s = b'\x00' * 4  # header
        s += b''.join(
            f"{key}={value}".encode('ascii') + b'\x00'
            for key, value in sorted(sample_env_dict.items())
        )
        s += b'\x00'  # env terminator
        s += b'\xff' * (0x1000 - len(s))  # Invalid size
        
        s = bytearray(s)
        s[:4] = struct.pack('<L', binascii.crc32(s[4:]))
        env_data.write(s)
        env_data.seek(0)
        
        with pytest.raises(ValueError, match="Invalid environment size"):
            load_env(env_data)

    def test_invalid_crc(self, sample_env_dict, env_file_path):
        """Test handling invalid CRC."""
        create_test_env_file(env_file_path, sample_env_dict)
        
        # Corrupt the CRC
        with open(env_file_path, 'r+b') as f:
            data = bytearray(f.read(4))
            data[0] = (data[0] + 1) % 256  # Change the CRC
            f.seek(0)
            f.write(data)
        
        with pytest.raises(ValueError, match="Invalid CRC"):
            load_env(env_file_path)


class TestDumpEnv:
    """Tests for the dump_env function."""

    def test_dump_to_path(self, sample_env, env_file_path):
        """Test dumping to a file path."""
        dump_env(sample_env, env_file_path)
        
        # Verify the file exists
        assert os.path.exists(env_file_path)
        
        # Verify the contents
        loaded_env = load_env(env_file_path)
        assert loaded_env.content == sample_env.content

    def test_dump_to_file_handle(self, sample_env, env_file_path):
        """Test dumping to a file handle."""
        with open(env_file_path, 'wb') as f:
            dump_env(sample_env, f)
        
        # Verify the contents
        loaded_env = load_env(env_file_path)
        assert loaded_env.content == sample_env.content


class TestFormatEnv:
    """Tests for the format_env function."""

    def test_format_env(self, sample_env):
        """Test formatting an environment."""
        formatted = format_env(sample_env)
        
        # Check each variable is in the output
        for key, value in sample_env.content.items():
            assert f"{key}={value}" in formatted
        
        # Check the output is sorted
        lines = formatted.split('\n')
        sorted_lines = sorted(lines)
        assert lines == sorted_lines
