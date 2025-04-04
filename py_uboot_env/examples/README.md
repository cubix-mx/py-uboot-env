# py_uboot_env Examples

This directory contains example code demonstrating how to use the `py_uboot_env` package.

## Available Examples

1. **basic_usage.py** - Demonstrates basic operations like loading and reading from a U-Boot environment file
2. **modify_and_revert.py** - Shows how to modify an environment, save changes, and then revert back to the original state
3. **advanced_usage.py** - Covers advanced topics like using file handles, batch operations, and error handling

## Sample Environment File

The examples use `sample-uboot.env`, which is a sample U-Boot environment file included in this directory.

## Running the Examples

You can run any example script directly:

```bash
# Basic usage example
python basic_usage.py

# Modifying and reverting example
python modify_and_revert.py

# Advanced usage example
python advanced_usage.py
```

All examples are designed to leave the sample environment file unchanged after execution, so you can run them multiple times without worry.

## What You'll Learn

- How to load and read U-Boot environment variables
- How to modify, add, and delete environment variables
- How to save changes to environment files
- Best practices for error handling
- Advanced usage with file handles and in-memory operations
