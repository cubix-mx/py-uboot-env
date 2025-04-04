#!/usr/bin/python3
"""
U-Boot environment file handling module.

Provides functionality to read, modify, and write U-Boot environment files.
"""

import io
import os
import binascii
import struct
from typing import Dict, Union, Optional, BinaryIO, TextIO, Tuple, Any, cast
from dataclasses import dataclass


@dataclass
class UBootEnv:
    """Class representing a U-Boot environment."""
    
    content: Dict[str, str]
    env_size: int
    header_size: int
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a value from the environment by key."""
        return self.content.get(key, default)
    
    def set(self, key: str, value: str) -> None:
        """Set a value in the environment."""
        self.content[key] = value
        
    def delete(self, key: str) -> None:
        """Delete a key from the environment."""
        if key in self.content:
            del self.content[key]
            
    def save(self, filename: Union[str, os.PathLike, BinaryIO]) -> None:
        """Save the environment to a file."""
        dump_env(self, filename)


def load_env(file_source: Union[str, os.PathLike, BinaryIO]) -> UBootEnv:
    """
    Load a U-Boot environment from a file.
    
    Args:
        file_source: Filename or file handle to load from
        
    Returns:
        UBootEnv: The loaded U-Boot environment
        
    Raises:
        ValueError: If the environment size is invalid or the CRC is incorrect
    """
    # Handle file path or file handle
    close_file = False
    if isinstance(file_source, (str, os.PathLike)):
        env_file = io.open(file_source, 'rb')
        close_file = True
    else:
        env_file = cast(BinaryIO, file_source)
    
    try:
        env = env_file.read()
    finally:
        if close_file:
            env_file.close()
    
    env_size = len(env)
    if env_size not in (0x1f000, 0x2000, 0x4000, 0x8000, 0x20000, 0x40000):
        raise ValueError(f"Invalid environment size: {env_size}")

    header_size = 4
    if binascii.crc32(env[header_size:]) != struct.unpack('<L', env[:4])[0]:
        header_size = 5
        if binascii.crc32(env[header_size:]) != struct.unpack('<L', env[:4])[0]:
            raise ValueError("Invalid CRC in environment header")

    content = {}
    raw_content = env[header_size:].rstrip(b'\xff').split(b'\x00')
    
    for entry in raw_content:
        if b'=' in entry:
            key, value = entry.decode('ascii').split('=', 1)
            content[key] = value
    
    return UBootEnv(content=content, env_size=env_size, header_size=header_size)


def dump_env(env: UBootEnv, file_dest: Union[str, os.PathLike, BinaryIO]) -> None:
    """
    Dump a U-Boot environment to a file.
    
    Args:
        env: UBootEnv object to dump
        file_dest: Filename or file handle to write to
    """
    # Create the binary content
    s = b'\x00' * env.header_size  # CRC + optional "redundand" count
    s += b''.join(
        f"{key}={value}".encode('ascii') + b'\x00'
        for key, value in sorted(env.content.items())
    )
    s += b'\x00'  # env terminator
    s += b'\xff' * (env.env_size - len(s))  # padding
    
    s = bytearray(s)
    s[:4] = struct.pack('<L', binascii.crc32(s[env.header_size:]))
    
    # Handle file path or file handle
    close_file = False
    if isinstance(file_dest, (str, os.PathLike)):
        env_file = io.open(file_dest, 'wb')
        close_file = True
    else:
        env_file = cast(BinaryIO, file_dest)
    
    try:
        env_file.write(s)
    finally:
        if close_file:
            env_file.close()


def format_env(env: UBootEnv) -> str:
    """
    Format a U-Boot environment as a string.
    
    Args:
        env: UBootEnv object to format
        
    Returns:
        str: Formatted environment as a string
    """
    return '\n'.join(
        f"{key}={value}"
        for key, value in sorted(env.content.items())
    )
