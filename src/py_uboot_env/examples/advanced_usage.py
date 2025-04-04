#!/usr/bin/env python3
"""
Advanced Usage Example for py_uboot_env

This example demonstrates more advanced features:
- Using file handles instead of file paths
- Batch operations
- Error handling
"""
import os
import sys
import io
import tempfile
from pathlib import Path
from py_uboot_env import load_env, dump_env, format_env, UBootEnv

# Get the path to the sample environment file
SCRIPT_DIR = Path(__file__).parent.absolute()
SAMPLE_ENV = os.path.join(SCRIPT_DIR, "sample-uboot.env")

def main():
    print("=" * 70)
    print("Advanced Usage Example for py_uboot_env".center(70))
    print("=" * 70)
    
    # Step 1: Load environment using a file handle
    print("\n1. Loading environment using a file handle...")
    try:
        with open(SAMPLE_ENV, "rb") as env_file:
            env = load_env(env_file)
        print(f"✓ Successfully loaded environment with {len(env.content)} variables")
    except Exception as e:
        print(f"✗ Error loading environment: {e}", file=sys.stderr)
        return 1
    
    # Step 2: Using batch operations with a context manager
    print("\n2. Performing batch operations...")
    
    # Create a temporary file for our operations
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_env_path = temp_file.name
    
    try:
        # Copy environment to our temporary file
        with open(SAMPLE_ENV, "rb") as src, open(temp_env_path, "wb") as dst:
            dst.write(src.read())
        
        # Load the environment
        env = load_env(temp_env_path)
        
        # Track original values for reversion
        original_values = {}
        
        # Perform batch operations
        operations = [
            # (operation, key, value)
            ("set", "bootdelay", "1"),
            ("set", "example_var", "Example value"),
            ("set", "numeric_var", "42"),
            ("delete", "example_var", None),  # Delete immediately after setting
            ("set", "complex_var", "Value with spaces and special chars: !@#$%^&*()"),
        ]
        
        print("  Performing operations:")
        for op, key, value in operations:
            # Save original value for reversion
            if key not in original_values:
                original_values[key] = env.get(key)
                
            if op == "set":
                env.set(key, value)
                print(f"  • Set: {key} = {value}")
            elif op == "delete":
                env.delete(key)
                print(f"  • Deleted: {key}")
        
        # Save the modified environment
        env.save(temp_env_path)
        print("✓ Batch operations completed and saved")
        
        # Step 3: Writing to a file-like object
        print("\n3. Saving environment to a BytesIO object...")
        try:
            # Create an in-memory binary stream
            bytes_io = io.BytesIO()
            
            # Save the environment to the stream
            dump_env(env, bytes_io)
            
            # Get the size of the written data
            size = bytes_io.tell()
            print(f"✓ Successfully wrote {size} bytes to BytesIO object")
            
            # Reset the stream position to the beginning
            bytes_io.seek(0)
            
            # Reload the environment from the stream
            stream_env = load_env(bytes_io)
            print(f"✓ Successfully reloaded environment with {len(stream_env.content)} variables")
            
            # Verify the contents
            match = all(stream_env.get(k) == v for k, v in env.content.items())
            print(f"✓ Environment integrity check: {'Passed' if match else 'Failed'}")
            
        except Exception as e:
            print(f"✗ Error in BytesIO operations: {e}", file=sys.stderr)
        
        # Step 4: Format environment as a string
        print("\n4. Formatting environment as a string...")
        formatted = format_env(env)
        lines = formatted.split('\n')
        print(f"  Environment has {len(lines)} variables. First 3:")
        for line in lines[:3]:
            print(f"  • {line}")
        if len(lines) > 3:
            print(f"  ... and {len(lines) - 3} more variables")
        
        # Step 5: Error handling demonstration
        print("\n5. Demonstrating error handling...")
        try:
            print("  Attempting to load from a non-existent file...")
            load_env("/path/does/not/exist.env")
        except FileNotFoundError as e:
            print(f"  ✓ Caught expected error: {e}")
        
        try:
            print("  Attempting to set an invalid value type...")
            # This would normally be caught by type hints, but let's demonstrate runtime checking
            env.set("test_var", None)  # type: ignore
        except AttributeError as e:
            print(f"  ✓ Caught expected error: {e}")
        except Exception as e:
            print(f"  ✓ Caught error: {e}")
        
        # Step A: Restore the original environment
        print("\n6. Restoring original values...")
        for key, value in original_values.items():
            if value is None:
                env.delete(key)
                print(f"  • Deleted: {key}")
            else:
                env.set(key, value)
                print(f"  • Restored: {key} = {value}")
        
        # Save the reverted changes
        env.save(temp_env_path)
        print("✓ Original values restored and saved")
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_env_path):
            os.unlink(temp_env_path)
            print(f"✓ Removed temporary file: {temp_env_path}")
    
    print("\nExample completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
