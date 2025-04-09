#!/usr/bin/python3
"""
Integration tests for the py-uboot-env package.
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path
from io import StringIO
from unittest.mock import patch

from py_uboot_env.uboot_env import UBootEnv, load_env, dump_env


@pytest.fixture
def env_file_path():
    """Create a temporary file path for env file."""
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


def create_test_environment(path):
    """Create a test environment file for CLI testing."""
    env = UBootEnv(
        content={
            "bootcmd": "run distro_bootcmd",
            "distro_bootcmd": "run bootcmd_mmc0",
            "test_var": "test_value"
        },
        env_size=0x2000,
        header_size=4
    )
    dump_env(env, path)
    return path


class TestIntegration:
    """Integration tests for the package."""
    
    def test_api_workflow(self, env_file_path):
        """Test a complete API workflow."""
        # Create a new environment
        env = UBootEnv(
            content={
                "bootcmd": "run default_boot",
                "default_boot": "echo Booting default configuration"
            },
            env_size=0x2000,
            header_size=4
        )
        
        # Save to file
        dump_env(env, env_file_path)
        
        # Load and modify
        loaded_env = load_env(env_file_path)
        loaded_env.set("new_var", "new_value")
        loaded_env.set("bootdelay", "3")
        loaded_env.delete("default_boot")
        
        # Save modifications
        loaded_env.save(env_file_path)
        
        # Check results
        final_env = load_env(env_file_path)
        assert final_env.get("bootcmd") == "run default_boot"
        assert final_env.get("new_var") == "new_value"
        assert final_env.get("bootdelay") == "3"
        assert final_env.get("default_boot") is None
    
    def test_cli_workflow(self, env_file_path):
        """Test the CLI workflow using patch."""
        create_test_environment(env_file_path)
        
        # Import the cli module
        from py_uboot_env import cli
        
        # Test dump command
        with patch('sys.stdout', new=StringIO()) as fake_out:
            with patch('sys.argv', ['uboot-env', 'dump', env_file_path]):
                cli.main()
            output = fake_out.getvalue().strip()
            assert "bootcmd=run distro_bootcmd" in output
            assert "test_var=test_value" in output
        
        # Test get command
        with patch('sys.stdout', new=StringIO()) as fake_out:
            with patch('sys.argv', ['uboot-env', 'get', env_file_path, 'test_var']):
                cli.main()
            output = fake_out.getvalue().strip()
            assert "test_value" in output
        
        # Test set command
        with patch('sys.stdout', new=StringIO()) as fake_out:
            with patch('sys.argv', ['uboot-env', 'set', env_file_path, 'new_var', 'cli_value']):
                cli.main()
            output = fake_out.getvalue().strip()
            assert "Variable 'new_var' set to 'cli_value'" in output
        
        # Verify the set worked by loading the environment
        env = load_env(env_file_path)
        assert env.get("new_var") == "cli_value"
        
        # Test delete command
        with patch('sys.stdout', new=StringIO()) as fake_out:
            with patch('sys.argv', ['uboot-env', 'delete', env_file_path, 'test_var']):
                cli.main()
            output = fake_out.getvalue().strip()
            assert "deleted" in output.lower()
        
        # Verify the delete worked
        env = load_env(env_file_path)
        assert env.get("test_var") is None
