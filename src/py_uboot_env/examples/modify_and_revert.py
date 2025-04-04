#!/usr/bin/env python3
"""
Environment Modification Example for py_uboot_env

This example demonstrates how to modify an environment and then revert changes,
leaving the original file unchanged.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from py_uboot_env import load_env

# Get the path to the sample environment file
SCRIPT_DIR = Path(__file__).parent.absolute()
SAMPLE_ENV = os.path.join(SCRIPT_DIR, "sample-uboot.env")

def main():
    print("=" * 70)
    print("Environment Modification Example for py_uboot_env".center(70))
    print("=" * 70)
    
    # Create a temporary copy of the sample environment
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_env_path = temp_file.name
    
    try:
        # Step 1: Make a temporary copy of the environment
        print("\n1. Creating a temporary copy of the environment file...")
        shutil.copy2(SAMPLE_ENV, temp_env_path)
        print(f"✓ Temporary copy created at: {temp_env_path}")
        
        # Step 2: Load the environment
        print("\n2. Loading the environment...")
        env = load_env(temp_env_path)
        print(f"✓ Successfully loaded environment with {len(env.content)} variables")
        
        # Step 3: Modify the environment
        print("\n3. Modifying environment variables...")
        
        # Save original values for later restoration
        original_values = {}
        test_vars = {
            "test_var1": "This is a test value",
            "test_var2": "Another test value",
            "bootdelay": "1"  # Change an existing variable
        }
        
        for key, value in test_vars.items():
            original_values[key] = env.get(key)
            env.set(key, value)
            status = "Modified" if original_values[key] is not None else "Created"
            print(f"  • {status}: {key} = {value}")
        
        # Step 4: Save the modified environment
        print("\n4. Saving the modified environment...")
        env.save(temp_env_path)
        print("✓ Environment saved successfully")
        
        # Step 5: Reload to verify changes
        print("\n5. Reloading the environment to verify changes...")
        modified_env = load_env(temp_env_path)
        for key, value in test_vars.items():
            actual = modified_env.get(key)
            if actual == value:
                print(f"  • Verified: {key} = {actual}")
            else:
                print(f"  ✗ Verification failed for {key}: expected '{value}', got '{actual}'")
        
        # Step 6: Revert changes
        print("\n6. Reverting changes...")
        for key, value in original_values.items():
            if value is None:
                modified_env.delete(key)
                print(f"  • Deleted: {key}")
            else:
                modified_env.set(key, value)
                print(f"  • Restored: {key} = {value}")
        
        # Step 7: Save the reverted environment
        print("\n7. Saving the reverted environment...")
        modified_env.save(temp_env_path)
        print("✓ Reverted environment saved successfully")
        
        # Step 8: Verify the reversion
        print("\n8. Verifying the reversion...")
        final_env = load_env(temp_env_path)
        all_reverted = True
        
        for key, original_value in original_values.items():
            final_value = final_env.get(key)
            if original_value != final_value:
                all_reverted = False
                print(f"  ✗ Reversion failed for {key}: expected '{original_value}', got '{final_value}'")
        
        if all_reverted:
            print("  ✓ All changes successfully reverted!")
            
        print("\nExample completed successfully!")
        
    finally:
        # Clean up the temporary file
        print("\nCleaning up...")
        if os.path.exists(temp_env_path):
            os.unlink(temp_env_path)
            print(f"✓ Removed temporary file: {temp_env_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
