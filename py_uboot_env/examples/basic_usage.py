#!/usr/bin/env python3
"""
Basic Usage Example for py_uboot_env

This example demonstrates how to load and read an environment file.
"""
import os
import sys
from pathlib import Path
from py_uboot_env import load_env

# Get the path to the sample environment file
SCRIPT_DIR = Path(__file__).parent.absolute()
SAMPLE_ENV = os.path.join(SCRIPT_DIR, "sample-uboot.env")

def main():
    print("=" * 60)
    print("Basic Usage Example for py_uboot_env".center(60))
    print("=" * 60)
    
    # Step 1: Load the environment file
    print("\n1. Loading the U-Boot environment file...")
    try:
        env = load_env(SAMPLE_ENV)
        print(f"✓ Successfully loaded environment with {len(env.content)} variables")
    except Exception as e:
        print(f"✗ Error loading environment: {e}", file=sys.stderr)
        return 1

    # Step 2: Get specific variables
    print("\n2. Reading environment variables...")
    
    # Example of getting variables with default values
    bootcmd = env.get("bootcmd", "Default boot command")
    bootdelay = env.get("bootdelay", "3")
    nonexistent = env.get("this_does_not_exist", "Default value")
    
    print(f"  • bootcmd = {bootcmd}")
    print(f"  • bootdelay = {bootdelay}")
    print(f"  • nonexistent variable = {nonexistent}")
    
    # Step 3: List all variables
    print("\n3. Listing the first 5 environment variables...")
    for i, (key, value) in enumerate(sorted(env.content.items())[:5]):
        print(f"  • {key} = {value}")
    
    if len(env.content) > 5:
        print(f"  ... and {len(env.content) - 5} more variables")
    
    # Step 4: Information about the environment
    print("\n4. Environment information...")
    print(f"  • Environment size: {env.env_size} bytes")
    print(f"  • Header size: {env.header_size} bytes")
    
    print("\nExample completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
